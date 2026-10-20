"""Access and verify the CABT card catalog from the pinned engine."""

import ctypes
import hashlib
import json
from functools import lru_cache
from typing import Any

from kaggle_environments.envs.cabt.cg.sim import lib

EXPECTED_CATALOG_SHA256 = "7fd6c45fcdc2913a1fe19ddb67c01aa9b204718cb760be7582cf4fcc3513de9c"
EXPECTED_CARD_COUNT = 1431

EXPECTED_ATTACK_SHA256 = "1b584ac7e19f85d565c2902d04831bf9b30e5107b51a4ab3bc956db2051a12ce"
EXPECTED_ATTACK_COUNT = 1755


def get_catalog_raw_bytes() -> bytes:
    """Retrieve raw card catalog JSON bytes directly from the C++ engine."""
    lib.AllCard.restype = ctypes.c_char_p
    raw: bytes | None = lib.AllCard()
    if raw is None:
        raise RuntimeError("libcg AllCard returned null pointer")
    return raw


def get_attack_raw_bytes() -> bytes:
    """Retrieve raw attack catalog JSON bytes directly from the C++ engine."""
    lib.AllAttack.restype = ctypes.c_char_p
    raw: bytes | None = lib.AllAttack()
    if raw is None:
        raise RuntimeError("libcg AllAttack returned null pointer")
    return raw


def get_catalog_sha256() -> str:
    """Compute the SHA-256 hex digest of the raw card catalog."""
    return hashlib.sha256(get_catalog_raw_bytes()).hexdigest()


def get_attack_sha256() -> str:
    """Compute the SHA-256 hex digest of the raw attack catalog."""
    return hashlib.sha256(get_attack_raw_bytes()).hexdigest()


@lru_cache(maxsize=1)
def load_card_catalog() -> list[dict[str, Any]]:
    """Load and parse the full CABT card catalog."""
    raw = get_catalog_raw_bytes()
    catalog_hash = hashlib.sha256(raw).hexdigest()
    if catalog_hash != EXPECTED_CATALOG_SHA256:
        raise ValueError(
            f"Card catalog checksum mismatch: got {catalog_hash}, "
            f"expected {EXPECTED_CATALOG_SHA256}"
        )
    parsed: Any = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, list):
        raise TypeError("Card catalog root must be a JSON array")
    return parsed


@lru_cache(maxsize=1)
def load_attack_catalog() -> list[dict[str, Any]]:
    """Load and parse the full CABT attack catalog."""
    raw = get_attack_raw_bytes()
    attack_hash = hashlib.sha256(raw).hexdigest()
    if attack_hash != EXPECTED_ATTACK_SHA256:
        raise ValueError(
            f"Attack catalog checksum mismatch: got {attack_hash}, "
            f"expected {EXPECTED_ATTACK_SHA256}"
        )
    parsed: Any = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, list):
        raise TypeError("Attack catalog root must be a JSON array")
    return parsed


@lru_cache(maxsize=1)
def get_catalog_by_id() -> dict[int, dict[str, Any]]:
    """Return a mapping from integer card ID to card attributes."""
    cards = load_card_catalog()
    return {int(card["cardId"]): card for card in cards if "cardId" in card}


@lru_cache(maxsize=1)
def get_attack_by_id() -> dict[int, dict[str, Any]]:
    """Return a mapping from integer attack ID to attack attributes."""
    attacks = load_attack_catalog()
    return {int(attack["attackId"]): attack for attack in attacks if "attackId" in attack}
