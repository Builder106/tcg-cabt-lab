"""Compact neural policy model, checkpoint provenance, and agent interface."""

import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from tcg_cabt_lab.agent import sanitize_observation
from tcg_cabt_lab.catalog import EXPECTED_CATALOG_SHA256, get_attack_by_id
from tcg_cabt_lab.deck import REFERENCE_DECK, validate_deck
from tcg_cabt_lab.features import (
    OPTION_DIM,
    STATE_DIM,
    TOTAL_FEATURE_DIM,
    extract_candidate_matrix,
)

DEFAULT_HIDDEN_DIM = 32


class CompactPolicy:
    """Two-layer MLP option-scoring policy implemented with NumPy."""

    def __init__(
        self,
        input_dim: int = TOTAL_FEATURE_DIM,
        hidden_dim: int = DEFAULT_HIDDEN_DIM,
        seed: int = 42,
    ) -> None:
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        rng = np.random.default_rng(seed)

        # He (Kaiming) normal initialization
        w1_scale = np.sqrt(2.0 / input_dim)
        self.w1 = (rng.normal(0.0, w1_scale, size=(input_dim, hidden_dim))).astype(np.float32)
        self.b1 = np.zeros(hidden_dim, dtype=np.float32)

        w2_scale = np.sqrt(2.0 / hidden_dim)
        self.w2 = (rng.normal(0.0, w2_scale, size=(hidden_dim, 1))).astype(np.float32)
        self.b2 = np.zeros(1, dtype=np.float32)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Compute scalar logits for an (N, input_dim) candidate option matrix.

        Returns:
            1D array of shape (N,) containing option scores.
        """
        if x.shape[0] == 0:
            return np.empty(0, dtype=np.float32)

        # Layer 1: Linear + ReLU
        h = np.maximum(0.0, np.dot(x, self.w1) + self.b1)
        # Layer 2: Linear -> (N, 1) -> (N,)
        out = np.dot(h, self.w2) + self.b2
        res: np.ndarray = np.asarray(out.ravel(), dtype=np.float32)
        return res

    def get_weights_dict(self) -> dict[str, list[Any]]:
        return {
            "w1": self.w1.tolist(),
            "b1": self.b1.tolist(),
            "w2": self.w2.tolist(),
            "b2": self.b2.tolist(),
        }

    def set_weights_dict(self, weights: Mapping[str, Any]) -> None:
        self.w1 = np.array(weights["w1"], dtype=np.float32)
        self.b1 = np.array(weights["b1"], dtype=np.float32)
        self.w2 = np.array(weights["w2"], dtype=np.float32)
        self.b2 = np.array(weights["b2"], dtype=np.float32)

        assert self.w1.shape == (self.input_dim, self.hidden_dim)
        assert self.b1.shape == (self.hidden_dim,)
        assert self.w2.shape == (self.hidden_dim, 1)
        assert self.b2.shape == (1,)

    def compute_weights_hash(self) -> str:
        """Compute canonical SHA-256 hash of policy weights."""
        serialized = json.dumps(self.get_weights_dict(), sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_checkpoint(
    policy: CompactPolicy,
    variant: str,
    seed: int,
    training_steps: int,
    training_deck_families: Sequence[str],
    extra_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Package a policy into a validated checkpoint dictionary with provenance."""
    weights = policy.get_weights_dict()
    weights_hash = policy.compute_weights_hash()

    payload: dict[str, Any] = {
        "model_type": "compact-mlp-policy",
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "architecture": {
            "input_dim": policy.input_dim,
            "hidden_dim": policy.hidden_dim,
            "state_dim": STATE_DIM,
            "option_dim": OPTION_DIM,
        },
        "weights_sha256": weights_hash,
        "provenance": {
            "variant": variant,
            "seed": seed,
            "training_steps": training_steps,
            "training_deck_families": list(training_deck_families),
            "card_catalog_sha256": EXPECTED_CATALOG_SHA256,
        },
        "weights": weights,
    }
    if extra_metadata:
        payload["provenance"].update(extra_metadata)

    return payload


def save_checkpoint(checkpoint: Mapping[str, Any], path: Path | str) -> str:
    """Save checkpoint to JSON file and return its weights SHA-256 hash."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
    return str(checkpoint["weights_sha256"])


def load_checkpoint(path: Path | str) -> dict[str, Any]:
    """Load and verify a policy checkpoint from disk."""
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Checkpoint not found at: {target}")

    with target.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    if data.get("model_type") != "compact-mlp-policy":
        raise ValueError(f"Unsupported model_type: {data.get('model_type')}")

    stored_hash = data.get("weights_sha256")
    weights = data.get("weights", {})
    calc_hash = hashlib.sha256(json.dumps(weights, sort_keys=True).encode("utf-8")).hexdigest()

    if stored_hash != calc_hash:
        raise ValueError(
            f"Checkpoint weights checksum mismatch: stored {stored_hash}, calculated {calc_hash}"
        )

    return data


class PolicyAgent:
    """Kaggle-environments compatible agent driven by a learned CompactPolicy."""

    def __init__(
        self,
        checkpoint: Mapping[str, Any] | Path | str,
        deck: Sequence[int] | None = None,
    ) -> None:
        if isinstance(checkpoint, (Path, str)):
            ckpt_dict = load_checkpoint(checkpoint)
        else:
            ckpt_dict = dict(checkpoint)

        arch = ckpt_dict["architecture"]
        self.policy = CompactPolicy(
            input_dim=int(arch["input_dim"]),
            hidden_dim=int(arch["hidden_dim"]),
        )
        self.policy.set_weights_dict(ckpt_dict["weights"])
        self.provenance = copy.deepcopy(ckpt_dict.get("provenance", {}))
        self.weights_hash = str(ckpt_dict.get("weights_sha256", ""))
        self.deck = validate_deck(deck) if deck is not None else list(REFERENCE_DECK)

        try:
            self.attacks = get_attack_by_id()
        except Exception:
            self.attacks = {}

    def __call__(
        self,
        observation: Mapping[str, Any],
        configuration: Mapping[str, Any] | None = None,
    ) -> list[int]:
        clean_obs = sanitize_observation(observation)
        sel = clean_obs.get("select")
        if sel is None:
            return list(self.deck)

        options = sel.get("option", [])
        if not options:
            return []

        max_count = int(sel.get("maxCount", 1) or 1)
        if max_count <= 0:
            return []

        # Extract candidates matrix: (N, 88)
        cand_matrix = extract_candidate_matrix(clean_obs, attacks=self.attacks)
        if cand_matrix.shape[0] == 0:
            return []

        # Forward pass: (N,)
        scores = self.policy.forward(cand_matrix)

        # Select top max_count candidate indices
        sorted_indices = np.argsort(-scores)
        chosen = [int(idx) for idx in sorted_indices[: min(max_count, len(scores))]]

        return chosen
