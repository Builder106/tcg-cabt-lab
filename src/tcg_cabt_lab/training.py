"""Training pipeline for supervised imitation and controlled opponent-pool experiments."""

import random
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import TypedDict

import numpy as np

from tcg_cabt_lab.agent import FirstAgent, HeuristicAgent, RandomAgent, sanitize_observation
from tcg_cabt_lab.battle import _normalize_agent
from tcg_cabt_lab.catalog import get_attack_by_id
from tcg_cabt_lab.features import extract_candidate_matrix
from tcg_cabt_lab.manifest import get_deck_family
from tcg_cabt_lab.policy import CompactPolicy

TRAINING_FAMILIES = ["water-kyogre", "grass-bulbasaur", "lightning-pikachu"]
TUNING_FAMILIES = ["fire-ponyta"]
FINAL_TEST_FAMILIES = ["psychic-mewtwo", "colorless-snorlax"]


@dataclass
class DecisionExample:
    """A single state-action decision training pair."""

    candidate_matrix: np.ndarray  # Shape (N, 88)
    target_index: int  # Chosen index in [0, N-1]
    num_candidates: int


class TrainingMetadata(TypedDict):
    variant: str
    seed: int
    training_steps: int
    batch_size: int
    learning_rate: float
    l2_reg: float
    total_samples: int
    train_samples: int
    val_samples: int
    initial_val_loss: float
    initial_val_acc: float
    final_val_loss: float
    final_val_acc: float
    training_duration_seconds: float
    loss_history_start: float | None
    loss_history_end: float | None


def collect_game_decisions(
    agent_p0: Callable[..., list[int]],
    agent_p1: Callable[..., list[int]],
    deck_p0: Sequence[int],
    deck_p1: Sequence[int],
    attacks: Mapping[int, object] | None = None,
) -> list[DecisionExample]:
    """Play a game and collect (candidate_matrix, target_index) for player 0 decisions."""
    from kaggle_environments import make

    if attacks is None:
        try:
            attacks = get_attack_by_id()
        except Exception:
            attacks = {}

    p0 = _normalize_agent(agent_p0)
    p1 = _normalize_agent(agent_p1)

    examples: list[DecisionExample] = []

    # Custom wrapper for player 0 to capture observation and choice
    def recording_agent(
        obs: Mapping[str, object], conf: Mapping[str, object] | None = None
    ) -> list[int]:
        clean_obs = sanitize_observation(obs)
        sel = clean_obs.get("select")
        chosen = p0(clean_obs, conf)

        if sel is not None and isinstance(sel, Mapping):
            options = sel.get("option", [])
            if isinstance(options, list) and len(options) > 1 and len(chosen) > 0:
                target_idx = int(chosen[0])
                if 0 <= target_idx < len(options):
                    mat = extract_candidate_matrix(clean_obs, attacks=attacks)
                    if mat.shape[0] == len(options):
                        examples.append(
                            DecisionExample(
                                candidate_matrix=mat,
                                target_index=target_idx,
                                num_candidates=len(options),
                            )
                        )
        return chosen

    env = make("cabt", configuration={"bo": 1})
    env.run([recording_agent, p1])
    return examples


def collect_training_dataset(
    variant: str,
    seed: int,
    target_samples: int = 2500,
    training_families: Sequence[str] = TRAINING_FAMILIES,
) -> list[DecisionExample]:
    """Collect decision examples under the specified opponent pool variant.

    Args:
        variant: Either 'fixed-opponent-pool' (train against FirstAgent)
                 or 'diverse-opponent-pool' (train against HeuristicAgent, FirstAgent, RandomAgent).
        seed: Random seed governing opponent selection and deck pairings.
        target_samples: Target count of decision examples.
        training_families: Deck families available for training.

    Returns:
        List of collected DecisionExample instances.
    """
    rng = random.Random(seed)
    attacks = get_attack_by_id()
    dataset: list[DecisionExample] = []

    decks = [get_deck_family(fam)["deck"] for fam in training_families]
    teacher = HeuristicAgent()

    while len(dataset) < target_samples:
        deck_p0 = rng.choice(decks)
        deck_p1 = rng.choice(decks)

        opp: Callable[..., list[int]]
        if variant == "fixed-opponent-pool":
            opp = FirstAgent(deck=deck_p1)
        elif variant == "diverse-opponent-pool":
            opp_choice = rng.choice(["heuristic", "first", "random"])
            if opp_choice == "heuristic":
                opp = HeuristicAgent(deck=deck_p1)
            elif opp_choice == "first":
                opp = FirstAgent(deck=deck_p1)
            else:
                opp = RandomAgent(seed=rng.randint(1, 100000), deck=deck_p1)
        else:
            raise ValueError(f"Unknown variant: {variant}")

        game_examples = collect_game_decisions(
            agent_p0=teacher,
            agent_p1=opp,
            deck_p0=deck_p0,
            deck_p1=deck_p1,
            attacks=attacks,
        )
        dataset.extend(game_examples)

    return dataset[:target_samples]


def train_policy(
    variant: str,
    seed: int,
    training_steps: int = 500,
    batch_size: int = 64,
    learning_rate: float = 0.005,
    l2_reg: float = 1e-4,
    target_samples: int = 2500,
    training_families: Sequence[str] = TRAINING_FAMILIES,
    dataset: list[DecisionExample] | None = None,
) -> tuple[CompactPolicy, TrainingMetadata]:
    """Train a CompactPolicy on collected decisions using Adam gradient descent.

    Args:
        variant: Training variant ('fixed-opponent-pool' or 'diverse-opponent-pool').
        seed: Training seed for reproducibility.
        training_steps: Number of mini-batch gradient updates.
        batch_size: Mini-batch size.
        learning_rate: Initial Adam learning rate.
        l2_reg: Weight decay regularization strength.
        target_samples: Number of training decisions to collect.
        training_families: Permitted deck family names.

    Returns:
        Tuple of (trained_policy, training_metadata).
    """
    t_start = time.perf_counter()
    rng = np.random.default_rng(seed)

    # 1. Dataset collection or provision
    if dataset is None:
        dataset = collect_training_dataset(
            variant=variant,
            seed=seed,
            target_samples=target_samples,
            training_families=training_families,
        )

    # 2. Split into train and validation (80/20)
    indices = rng.permutation(len(dataset))
    split_pt = int(0.8 * len(dataset))
    train_idx = indices[:split_pt]
    val_idx = indices[split_pt:]

    train_data = [dataset[i] for i in train_idx]
    val_data = [dataset[i] for i in val_idx]

    policy = CompactPolicy(seed=seed)

    def evaluate_loss_acc(data: list[DecisionExample]) -> tuple[float, float]:
        if not data:
            return 0.0, 0.0
        total_loss = 0.0
        correct = 0
        for ex in data:
            scores = policy.forward(ex.candidate_matrix)
            # Softmax
            max_s = np.max(scores)
            exp_s = np.exp(scores - max_s)
            probs = exp_s / np.sum(exp_s)

            target = ex.target_index
            total_loss += float(-np.log(max(probs[target], 1e-12)))
            if int(np.argmax(scores)) == target:
                correct += 1

        return total_loss / len(data), float(correct) / len(data)

    initial_loss, initial_acc = evaluate_loss_acc(val_data)

    # Adam optimizer state
    w1 = policy.w1
    b1 = policy.b1
    w2 = policy.w2
    b2 = policy.b2

    m_w1, v_w1 = np.zeros_like(w1), np.zeros_like(w1)
    m_b1, v_b1 = np.zeros_like(b1), np.zeros_like(b1)
    m_w2, v_w2 = np.zeros_like(w2), np.zeros_like(w2)
    m_b2, v_b2 = np.zeros_like(b2), np.zeros_like(b2)

    beta1 = 0.9
    beta2 = 0.999
    eps = 1e-8

    loss_history: list[float] = []

    for step in range(1, training_steps + 1):
        cur_batch_size = min(batch_size, len(train_data))
        batch_indices = rng.choice(len(train_data), size=cur_batch_size, replace=False)
        grad_w1 = np.zeros_like(w1)
        grad_b1 = np.zeros_like(b1)
        grad_w2 = np.zeros_like(w2)
        grad_b2 = np.zeros_like(b2)
        batch_loss = 0.0

        for b_idx in batch_indices:
            ex = train_data[b_idx]
            x = ex.candidate_matrix
            target = ex.target_index

            # Forward
            pre1 = np.dot(x, w1) + b1
            h = np.maximum(0.0, pre1)
            out = (np.dot(h, w2) + b2).ravel()

            # Softmax
            exp_s = np.exp(out - np.max(out))
            probs = exp_s / np.sum(exp_s)
            batch_loss += -float(np.log(max(probs[target], 1e-12)))

            # Gradient of loss w.r.t logits: (N,)
            d_out = probs.copy()
            d_out[target] -= 1.0

            # Gradient w.r.t w2, b2
            d_out_2d = d_out.reshape(-1, 1)  # (N, 1)
            grad_w2 += np.dot(h.T, d_out_2d)
            grad_b2 += np.sum(d_out_2d, axis=0)

            # Gradient w.r.t h
            d_h = np.dot(d_out_2d, w2.T)  # (N, hidden)
            # Gradient w.r.t pre1 (ReLU derivative)
            d_pre1 = d_h * (pre1 > 0.0)

            # Gradient w.r.t w1, b1
            grad_w1 += np.dot(x.T, d_pre1)
            grad_b1 += np.sum(d_pre1, axis=0)

        n_batch = len(batch_indices)
        grad_w1 = np.asarray((grad_w1 / n_batch) + l2_reg * w1, dtype=np.float32)
        grad_b1 = np.asarray(grad_b1 / n_batch, dtype=np.float32)
        grad_w2 = np.asarray((grad_w2 / n_batch) + l2_reg * w2, dtype=np.float32)
        grad_b2 = np.asarray(grad_b2 / n_batch, dtype=np.float32)

        # Adam updates
        for p, grad, m, v in [
            (w1, grad_w1, m_w1, v_w1),
            (b1, grad_b1, m_b1, v_b1),
            (w2, grad_w2, m_w2, v_w2),
            (b2, grad_b2, m_b2, v_b2),
        ]:
            m[:] = beta1 * m + (1.0 - beta1) * grad
            v[:] = beta2 * v + (1.0 - beta2) * (grad**2)
            m_hat = m / (1.0 - beta1**step)
            v_hat = v / (1.0 - beta2**step)
            step_update = (learning_rate / (np.sqrt(v_hat) + eps)) * m_hat
            p -= np.asarray(step_update, dtype=np.float32)

        loss_history.append(batch_loss / n_batch)

    final_loss, final_acc = evaluate_loss_acc(val_data)
    training_duration = time.perf_counter() - t_start

    metadata: TrainingMetadata = {
        "variant": variant,
        "seed": seed,
        "training_steps": training_steps,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "l2_reg": l2_reg,
        "total_samples": len(dataset),
        "train_samples": len(train_data),
        "val_samples": len(val_data),
        "initial_val_loss": round(float(initial_loss), 4),
        "initial_val_acc": round(float(initial_acc), 4),
        "final_val_loss": round(float(final_loss), 4),
        "final_val_acc": round(float(final_acc), 4),
        "training_duration_seconds": round(float(training_duration), 2),
        "loss_history_start": round(loss_history[0], 4) if loss_history else None,
        "loss_history_end": round(loss_history[-1], 4) if loss_history else None,
    }

    return policy, metadata
