"""Tests for training pipeline and supervised baseline optimization."""

from collections.abc import Callable, Mapping

import numpy as np
import pytest

from tcg_cabt_lab import training
from tcg_cabt_lab.agent import HeuristicAgent
from tcg_cabt_lab.manifest import get_deck_family
from tcg_cabt_lab.training import DecisionExample, collect_training_dataset, train_policy


def test_teacher_plays_every_training_deck(monkeypatch: pytest.MonkeyPatch) -> None:
    teacher_decks: list[list[int]] = []

    def fake_collect(
        agent_p0: Callable[..., list[int]],
        agent_p1: Callable[..., list[int]],
        attacks: Mapping[int, object] | None = None,
    ) -> list[DecisionExample]:
        assert isinstance(agent_p0, HeuristicAgent)
        teacher_decks.append(list(agent_p0.deck))
        return [
            DecisionExample(
                candidate_matrix=np.zeros((2, 88), dtype=np.float32),
                target_index=0,
                num_candidates=2,
            )
        ]

    monkeypatch.setattr(training, "collect_game_decisions", fake_collect)

    families = ["water-kyogre", "grass-bulbasaur", "lightning-pikachu"]
    collect_training_dataset(
        variant="fixed-opponent-pool",
        seed=11,
        target_samples=30,
        training_families=families,
    )

    expected = {tuple(get_deck_family(fam)["deck"]) for fam in families}
    assert {tuple(deck) for deck in teacher_decks} == expected


def test_training_loss_reduction() -> None:
    # Fast test of training
    _policy, meta = train_policy(
        variant="fixed-opponent-pool",
        seed=42,
        training_steps=30,
        batch_size=16,
        learning_rate=0.01,
        target_samples=50,
        training_families=["water-kyogre"],
    )

    assert meta["final_val_loss"] < meta["initial_val_loss"]
    assert meta["final_val_acc"] >= meta["initial_val_acc"]
    assert meta["total_samples"] == 50


def test_training_seed_reproducibility() -> None:
    rng = np.random.default_rng(12345)
    fixed_data = [
        DecisionExample(
            candidate_matrix=rng.normal(0.0, 1.0, size=(4, 88)).astype(np.float32),
            target_index=i % 4,
            num_candidates=4,
        )
        for i in range(20)
    ]

    p1, _m1 = train_policy(
        variant="fixed-opponent-pool",
        seed=99,
        training_steps=10,
        dataset=fixed_data,
    )
    p2, _m2 = train_policy(
        variant="fixed-opponent-pool",
        seed=99,
        training_steps=10,
        dataset=fixed_data,
    )

    assert np.allclose(p1.w1, p2.w1)
    assert np.allclose(p1.b1, p2.b1)
    assert np.allclose(p1.w2, p2.w2)
    assert np.allclose(p1.b2, p2.b2)
    assert p1.compute_weights_hash() == p2.compute_weights_hash()
