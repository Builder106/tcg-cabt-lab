"""Tests for compact policy model, checkpoint serialization, and PolicyAgent."""

import json
from pathlib import Path

import numpy as np
import pytest

from tcg_cabt_lab.policy import (
    CompactPolicy,
    PolicyAgent,
    create_checkpoint,
    load_checkpoint,
    save_checkpoint,
)


def test_compact_policy_forward_shape() -> None:
    policy = CompactPolicy(input_dim=88, hidden_dim=32, seed=42)
    x = np.random.randn(5, 88).astype(np.float32)
    scores = policy.forward(x)

    assert scores.shape == (5,)
    assert scores.dtype == np.float32


def test_checkpoint_roundtrip_and_provenance(tmp_path: Path) -> None:
    policy = CompactPolicy(input_dim=88, hidden_dim=32, seed=123)
    ckpt = create_checkpoint(
        policy=policy,
        variant="fixed-opponent-pool",
        seed=123,
        training_steps=50,
        training_deck_families=["water-kyogre"],
    )

    ckpt_file = tmp_path / "test-checkpoint.json"
    w_hash = save_checkpoint(ckpt, ckpt_file)

    assert ckpt_file.exists()
    assert w_hash == ckpt["weights_sha256"]

    loaded = load_checkpoint(ckpt_file)
    assert loaded["weights_sha256"] == w_hash
    assert loaded["provenance"]["variant"] == "fixed-opponent-pool"
    assert loaded["provenance"]["seed"] == 123


def test_checkpoint_tamper_detection(tmp_path: Path) -> None:
    policy = CompactPolicy(input_dim=88, hidden_dim=32, seed=456)
    ckpt = create_checkpoint(
        policy=policy,
        variant="diverse-opponent-pool",
        seed=456,
        training_steps=10,
        training_deck_families=["water-kyogre"],
    )
    ckpt_file = tmp_path / "tampered.json"
    save_checkpoint(ckpt, ckpt_file)

    # Tamper with weights
    data = json.loads(ckpt_file.read_text(encoding="utf-8"))
    data["weights"]["b2"] = [999.0]
    ckpt_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="checksum mismatch"):
        load_checkpoint(ckpt_file)


def test_policy_agent_step_decisions(tmp_path: Path) -> None:
    policy = CompactPolicy(input_dim=88, hidden_dim=32, seed=789)
    ckpt = create_checkpoint(
        policy=policy,
        variant="fixed-opponent-pool",
        seed=789,
        training_steps=10,
        training_deck_families=["water-kyogre"],
    )
    ckpt_file = tmp_path / "agent-ckpt.json"
    save_checkpoint(ckpt, ckpt_file)

    agent = PolicyAgent(checkpoint=ckpt_file)

    # Step 0: deck selection (select is None)
    step0_action = agent({"current": {"turn": 0}})
    assert isinstance(step0_action, list)
    assert len(step0_action) == 60

    # In-game choice: select from 4 options
    obs = {
        "current": {"turn": 2, "yourIndex": 0, "players": [{}, {}]},
        "select": {
            "minCount": 1,
            "maxCount": 1,
            "option": [{"type": 13}, {"type": 8}, {"type": 9}, {"type": 14}],
        },
    }
    action = agent(obs)
    assert isinstance(action, list)
    assert len(action) == 1
    assert action[0] in [0, 1, 2, 3]
