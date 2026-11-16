from pathlib import Path

import numpy as np

from tcg_cabt_lab.agent import FirstAgent
from tcg_cabt_lab.manifest import get_deck_family
from tcg_cabt_lab.policy import CompactPolicy, create_checkpoint, load_checkpoint, save_checkpoint
from tcg_cabt_lab.rl import (
    Decision,
    RLConfig,
    SamplingAgent,
    play_episode,
    reinforce_gradients,
    run_rl_suite,
    train_rl_policy,
)


def softmax_prob(policy: CompactPolicy, matrix: np.ndarray, index: int) -> float:
    scores = policy.forward(matrix).astype(np.float64)
    probs = np.exp(scores - scores.max())
    return float(probs[index] / probs.sum())


def test_gradient_step_raises_the_choice_made_in_won_games() -> None:
    rng = np.random.default_rng(0)
    policy = CompactPolicy(seed=1)
    matrix = rng.normal(size=(4, 88)).astype(np.float32)
    won = [Decision(matrix, 2)]
    lost = [Decision(matrix, 0)]
    grads = reinforce_gradients(policy, [(won, 1.0), (lost, -1.0)])
    assert grads is not None
    before = softmax_prob(policy, matrix, 2)
    for p, g in zip([policy.w1, policy.b1, policy.w2, policy.b2], grads, strict=True):
        p -= 0.05 * g
    assert softmax_prob(policy, matrix, 2) > before


def test_games_with_one_outcome_carry_no_signal() -> None:
    policy = CompactPolicy(seed=1)
    matrix = np.ones((3, 88), dtype=np.float32)
    episodes = [([Decision(matrix, 1)], 1.0), ([Decision(matrix, 0)], 1.0)]
    assert reinforce_gradients(policy, episodes) is None


def test_sampling_agent_returns_legal_choices_and_records_them() -> None:
    agent = SamplingAgent(CompactPolicy(seed=3), np.random.default_rng(3))
    obs = {
        "select": {
            "context": 0,
            "minCount": 1,
            "maxCount": 2,
            "option": [{"type": 14}, {"type": 13, "attackId": 1}, {"type": 7, "index": 0}],
        },
        "current": {"yourIndex": 0, "players": [{}, {}]},
    }
    choice = agent(obs)
    assert len(choice) == 2 and len(set(choice)) == 2
    assert all(0 <= i < 3 for i in choice)
    assert len(agent.decisions) == 1 and agent.decisions[0].chosen == choice[0]
    assert agent({"select": None}) == agent.deck


def test_play_episode_scores_the_learner_from_either_seat() -> None:
    deck = get_deck_family("water-kyogre")["deck"]
    for seat in (0, 1):
        decisions, outcome = play_episode(
            CompactPolicy(seed=2), FirstAgent(deck=deck), deck, seat, np.random.default_rng(seat)
        )
        assert decisions
        assert outcome in (-1.0, 0.0, 1.0)


def test_train_and_save_rl_checkpoints(tmp_path: Path) -> None:
    config = RLConfig(games=2, games_per_update=2)
    policy, meta = train_rl_policy("diverse-opponent-pool", 5, config)
    assert meta["learner"] == "reinforce" and meta["teacher"] is None
    assert meta["training_games"] == 2
    assert policy.w1.shape == (88, 32)

    suite = run_rl_suite(tmp_path, [5], variants=("fixed-opponent-pool",), config=config, workers=1)
    result = suite["fixed-opponent-pool"]["5"]
    ckpt = load_checkpoint(result["checkpoint_path"])
    assert ckpt["provenance"]["learner"] == "reinforce"
    assert ckpt["provenance"]["variant"] == "fixed-opponent-pool"


def test_training_can_start_from_a_saved_checkpoint(tmp_path: Path) -> None:
    start = CompactPolicy(seed=99)
    ckpt = create_checkpoint(
        policy=start,
        variant="fixed-opponent-pool",
        seed=7,
        training_steps=1,
        training_deck_families=["water-kyogre"],
    )
    save_checkpoint(ckpt, tmp_path / "start-seed-7.json")
    config = RLConfig(games=0, init_checkpoint=str(tmp_path / "start-seed-{seed}.json"))
    policy, meta = train_rl_policy("fixed-opponent-pool", 7, config)
    assert np.array_equal(policy.w1, start.w1)
    assert meta["init_weights_sha256"] == ckpt["weights_sha256"]
