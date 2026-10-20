"""Deck family manifests, split definitions, and disjointness verification."""

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from tcg_cabt_lab.deck import REFERENCE_DECK, validate_deck

# 6 canonical deck families representing distinct elemental archetypes:
DECK_FAMILIES: dict[str, dict[str, Any]] = {
    "water-kyogre": {
        "family": "water-kyogre",
        "archetype": "Water",
        "description": "Kyogre and Mega Abomasnow ex baseline deck",
        "signature_pokemon": [721, 722, 723],
        "energy_type": "Water",
        "deck": list(REFERENCE_DECK),
    },
    "lightning-pikachu": {
        "family": "lightning-pikachu",
        "archetype": "Lightning",
        "description": "Pikachu ex high-tempo aggressive lightning deck",
        "signature_pokemon": [210, 948],
        "energy_type": "Lightning",
        "deck": [210] * 4 + [948] * 4 + [1121] * 4 + [1227] * 4 + [4] * 44,
    },
    "grass-bulbasaur": {
        "family": "grass-bulbasaur",
        "archetype": "Grass",
        "description": "Bulbasaur and Pinsir grass control deck",
        "signature_pokemon": [650, 25],
        "energy_type": "Grass",
        "deck": [650] * 4 + [25] * 4 + [1121] * 4 + [1227] * 4 + [1] * 44,
    },
    "fire-ponyta": {
        "family": "fire-ponyta",
        "archetype": "Fire",
        "description": "Charmander and Ponyta fire burn deck",
        "signature_pokemon": [788, 350],
        "energy_type": "Fire",
        "deck": [788] * 4 + [350] * 4 + [1121] * 4 + [1227] * 4 + [2] * 44,
    },
    "psychic-mewtwo": {
        "family": "psychic-mewtwo",
        "archetype": "Psychic",
        "description": "Team Rocket's Mewtwo ex high-HP psychic deck",
        "signature_pokemon": [431, 249],
        "energy_type": "Psychic",
        "deck": [431] * 4 + [249] * 4 + [1121] * 4 + [1227] * 4 + [5] * 44,
    },
    "colorless-snorlax": {
        "family": "colorless-snorlax",
        "archetype": "Colorless",
        "description": "Snorlax wall and heavy attack deck",
        "signature_pokemon": [1072, 304],
        "energy_type": "Colorless",
        "deck": [1072] * 4 + [304] * 4 + [1121] * 4 + [1227] * 4 + [3] * 44,
    },
}

SPLIT_ASSIGNMENTS: dict[str, list[str]] = {
    "training": ["water-kyogre", "grass-bulbasaur", "lightning-pikachu"],
    "tuning": ["fire-ponyta"],
    "final_test": ["psychic-mewtwo", "colorless-snorlax"],
}


def compute_deck_hash(deck: Sequence[int]) -> str:
    """Compute deterministic SHA-256 hash of a 60-card deck list."""
    payload = json.dumps(list(deck), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_deck_family(name: str) -> dict[str, Any]:
    """Retrieve verified deck family record by name."""
    if name not in DECK_FAMILIES:
        raise KeyError(f"Unknown deck family '{name}'. Available: {list(DECK_FAMILIES.keys())}")
    return DECK_FAMILIES[name]


def verify_split_disjointness(
    splits: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Verify that deck families and signature Pokémon are strictly disjoint across splits.

    Args:
        splits: Mapping from split name ('training', 'tuning', 'final_test')
            to list of deck family names. If None, uses canonical SPLIT_ASSIGNMENTS.

    Returns:
        Structured dictionary mapping split names to verified family records
        with validated 60-card decks and computed SHA-256 hashes.

    Raises:
        ValueError: If families overlap between splits or signature Pokemon leak.
    """
    target_splits = splits if splits is not None else SPLIT_ASSIGNMENTS
    seen_families: dict[str, str] = {}
    seen_pokemon: dict[int, str] = {}
    verified_splits: dict[str, list[dict[str, Any]]] = {}

    for split_name, family_names in target_splits.items():
        verified_splits[split_name] = []
        for fam_name in family_names:
            if fam_name in seen_families:
                raise ValueError(
                    f"Deck family '{fam_name}' appears in both '{seen_families[fam_name]}' "
                    f"and '{split_name}'"
                )
            seen_families[fam_name] = split_name

            record = get_deck_family(fam_name)
            valid_deck = validate_deck(record["deck"])
            deck_hash = compute_deck_hash(valid_deck)

            # Check that signature Pokemon do not appear in other splits
            for pid in record["signature_pokemon"]:
                if pid in seen_pokemon:
                    prev_split = seen_pokemon[pid]
                    raise ValueError(
                        f"Signature Pokemon ID {pid} in family '{fam_name}' ({split_name}) "
                        f"was already allocated to '{prev_split}'"
                    )
                seen_pokemon[pid] = split_name

            verified_splits[split_name].append(
                {
                    "family": fam_name,
                    "archetype": record["archetype"],
                    "description": record["description"],
                    "signature_pokemon": list(record["signature_pokemon"]),
                    "deck_sha256": deck_hash,
                    "deck": valid_deck,
                }
            )

    return verified_splits
