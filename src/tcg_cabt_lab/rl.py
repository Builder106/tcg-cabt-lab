"""Policy-gradient training from play against an opponent pool (REINFORCE)."""

import random
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import numpy as np

from tcg_cabt_lab.agent import sanitize_observation
from tcg_cabt_lab.battle import _normalize_agent
from tcg_cabt_lab.catalog import get_attack_by_id
from tcg_cabt_lab.deck import REFERENCE_DECK
from tcg_cabt_lab.features import extract_candidate_matrix
from tcg_cabt_lab.manifest import get_deck_family
from tcg_cabt_lab.policy import (
    CompactPolicy,
    create_checkpoint,
    load_checkpoint,
    save_checkpoint,
)
from tcg_cabt_lab.training import TRAINING_FAMILIES, training_opponent


@dataclass(frozen=True)
class RLConfig:
    """Budget and optimizer settings. Both opponent pools get the same values.

    `init_checkpoint` is a path template with `{seed}`. When set, every checkpoint starts from
    the saved weights of that seed instead of a random initialization, so both pools begin
    from the same policy.
    """

    games: int = 400
    games_per_update: int = 8
    learning_rate: float = 0.01
    init_checkpoint: str | None = None


DEFAULT_CONFIG = RLConfig()


@dataclass
class Decision:
    candidate_matrix: np.ndarray
    chosen: int


class SamplingAgent:
    """Plays by sampling each choice from the policy's softmax and records the decisions."""

    def __init__(
        self,
        policy: CompactPolicy,
        rng: np.random.Generator,
        deck: Sequence[int] | None = None,
        attacks: Mapping[int, Any] | None = None,
    ) -> None:
        self.policy = policy
        self.rng = rng
        self.deck = list(deck) if deck is not None else list(REFERENCE_DECK)
        self.attacks = attacks if attacks is not None else get_attack_by_id()
        self.decisions: list[Decision] = []

    def __call__(
        self,
        observation: Mapping[str, Any],
        configuration: Mapping[str, Any] | None = None,
    ) -> list[int]:
        obs = sanitize_observation(observation)
        sel = obs.get("select")
        if sel is None:
            return list(self.deck)
        options = sel.get("option") or []
        max_count = int(sel.get("maxCount") or 0)
        if not options or max_count <= 0:
            return []
        matrix = extract_candidate_matrix(obs, attacks=self.attacks)
        scores = self.policy.forward(matrix).astype(np.float64)
        probs = np.exp(scores - scores.max())
        probs /= probs.sum()
        first = int(self.rng.choice(len(probs), p=probs))
        if len(options) > 1:
            self.decisions.append(Decision(matrix, first))
        # Extra picks (selections that ask for several cards) follow the highest scores
        rest = [int(i) for i in np.argsort(-scores) if int(i) != first]
        return [first, *rest[: min(max_count, len(scores)) - 1]]


def play_episode(
    policy: CompactPolicy,
    opponent: Callable[..., list[int]],
    deck: Sequence[int],
    seat: int,
    rng: np.random.Generator,
) -> tuple[list[Decision], float]:
    """Play one game from `seat`. Returns the learner's decisions and +1, 0 or -1."""
    from kaggle_environments import make

    learner = SamplingAgent(policy, rng, deck=deck)
    agents = [_normalize_agent(learner), _normalize_agent(opponent)]
    if seat == 1:
        agents.reverse()
    steps = make("cabt", configuration={"bo": 1}).run(agents)
    mine = float(steps[-1][seat].reward or 0)
    theirs = float(steps[-1][1 - seat].reward or 0)
    return learner.decisions, float(np.sign(mine - theirs))


def reinforce_gradients(
    policy: CompactPolicy, episodes: Sequence[tuple[list[Decision], float]]
) -> list[np.ndarray] | None:
    """Policy-gradient step direction: loss is -(outcome - batch mean) * log p(choice).

    Returns gradients for (w1, b1, w2, b2), averaged over decisions, or None when every
    game had the same outcome and so carries no signal.
    """
    outcomes = np.array([o for _, o in episodes])
    advantages = outcomes - outcomes.mean()
    if not np.any(advantages):
        return None
    g_w1, g_b1 = np.zeros_like(policy.w1), np.zeros_like(policy.b1)
    g_w2, g_b2 = np.zeros_like(policy.w2), np.zeros_like(policy.b2)
    count = 0
    for (decisions, _), adv in zip(episodes, advantages, strict=True):
        for d in decisions:
            x = d.candidate_matrix
            h = np.maximum(0.0, np.dot(x, policy.w1) + policy.b1)
            out = (np.dot(h, policy.w2) + policy.b2).ravel()
            probs = np.exp(out - out.max())
            probs /= probs.sum()
            d_out = probs.copy()
            d_out[d.chosen] -= 1.0
            d_out = (adv * d_out).reshape(-1, 1)
            g_w2 += np.dot(h.T, d_out)
            g_b2 += d_out.sum(axis=0)
            d_pre = np.dot(d_out, policy.w2.T) * (h > 0)
            g_w1 += np.dot(x.T, d_pre)
            g_b1 += d_pre.sum(axis=0)
            count += 1
    if count == 0:
        return None
    return [g / count for g in (g_w1, g_b1, g_w2, g_b2)]


def train_rl_policy(
    variant: str,
    seed: int,
    config: RLConfig = DEFAULT_CONFIG,
    training_families: Sequence[str] = TRAINING_FAMILIES,
) -> tuple[CompactPolicy, dict[str, Any]]:
    """Train a CompactPolicy from play against the variant's opponent pool."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    policy = CompactPolicy(seed=seed)
    init_hash: str | None = None
    if config.init_checkpoint is not None:
        init = load_checkpoint(config.init_checkpoint.format(seed=seed))
        policy.set_weights_dict(init["weights"])
        init_hash = str(init["weights_sha256"])
    decks = [get_deck_family(fam)["deck"] for fam in training_families]
    params = [policy.w1, policy.b1, policy.w2, policy.b2]
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    beta1, beta2, eps = 0.9, 0.999, 1e-8

    outcomes: list[float] = []
    step = 0
    while len(outcomes) < config.games:
        episodes: list[tuple[list[Decision], float]] = []
        for _ in range(min(config.games_per_update, config.games - len(outcomes))):
            deck_learner, deck_opponent = rng.choice(decks), rng.choice(decks)
            opponent = training_opponent(variant, rng, deck_opponent)
            seat = rng.randint(0, 1)
            episode = play_episode(policy, opponent, deck_learner, seat, np_rng)
            episodes.append(episode)
            outcomes.append(episode[1])
        grads = reinforce_gradients(policy, episodes)
        if grads is None:
            continue
        step += 1
        for i, (p, g) in enumerate(zip(params, grads, strict=True)):
            m[i] = beta1 * m[i] + (1 - beta1) * g
            v[i] = beta2 * v[i] + (1 - beta2) * g * g
            m_hat = m[i] / (1 - beta1**step)
            v_hat = v[i] / (1 - beta2**step)
            # The gradient is of the loss, so subtracting it raises the winning choices
            p -= (config.learning_rate * m_hat / (np.sqrt(v_hat) + eps)).astype(p.dtype)

    quarter = max(1, len(outcomes) // 4)

    def score(games: list[float]) -> float | None:
        return round(float(np.mean(games) / 2 + 0.5), 4) if games else None

    meta = {
        "learner": "reinforce",
        "teacher": None,
        "rl": asdict(config),
        "init_weights_sha256": init_hash,
        "updates": step,
        "training_games": len(outcomes),
        "training_score_first_quarter": score(outcomes[:quarter]),
        "training_score_last_quarter": score(outcomes[-quarter:]),
    }
    return policy, meta


def train_rl_checkpoint(
    variant: str,
    seed: int,
    config: RLConfig,
    training_families: Sequence[str],
    output_dir: str,
) -> dict[str, Any]:
    """Train one checkpoint and save it; module-level so worker processes can run it."""
    policy, meta = train_rl_policy(variant, seed, config, training_families)
    ckpt = create_checkpoint(
        policy=policy,
        variant=variant,
        seed=seed,
        training_steps=int(meta["updates"]),
        training_deck_families=training_families,
        extra_metadata=meta,
    )
    path = Path(output_dir) / f"{variant}-seed-{seed}.json"
    save_checkpoint(ckpt, path)
    return {
        "checkpoint_path": str(path),
        "weights_sha256": ckpt["weights_sha256"],
        "training_metadata": meta,
    }


def run_rl_suite(
    output_dir: Path | str,
    training_seeds: Sequence[int],
    variants: Sequence[str] = ("fixed-opponent-pool", "diverse-opponent-pool"),
    config: RLConfig = DEFAULT_CONFIG,
    training_families: Sequence[str] = TRAINING_FAMILIES,
    workers: int = 1,
) -> dict[str, Any]:
    """Train one RL checkpoint per variant and seed, `workers` processes at a time."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(var, s) for var in variants for s in training_seeds]
    with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn")) as pool:
        futures = [
            pool.submit(train_rl_checkpoint, var, s, config, list(training_families), str(out))
            for var, s in jobs
        ]
        results = [f.result() for f in futures]
    suite: dict[str, Any] = {var: {} for var in variants}
    for (var, s), result in zip(jobs, results, strict=True):
        suite[var][str(s)] = result
    return suite
