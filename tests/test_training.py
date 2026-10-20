"""Tests for training pipeline and supervised baseline optimization."""

import numpy as np

from tcg_cabt_lab.training import DecisionExample, train_policy


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
