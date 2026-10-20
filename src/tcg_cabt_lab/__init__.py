"""CABT engine integration and evaluation framework for 60-card Pokemon TCG agents."""

from tcg_cabt_lab.agent import FirstAgent, HeuristicAgent, RandomAgent, sanitize_observation
from tcg_cabt_lab.baseline import choose_random_action
from tcg_cabt_lab.battle import run_battle
from tcg_cabt_lab.catalog import (
    get_attack_by_id,
    get_attack_sha256,
    get_catalog_by_id,
    get_catalog_sha256,
    load_attack_catalog,
    load_card_catalog,
)
from tcg_cabt_lab.deck import REFERENCE_DECK, format_deck_summary, validate_deck
from tcg_cabt_lab.manifest import (
    DECK_FAMILIES,
    SPLIT_ASSIGNMENTS,
    compute_deck_hash,
    get_deck_family,
    verify_split_disjointness,
)
from tcg_cabt_lab.tournament import (
    compute_wilson_interval,
    run_paired_match,
    run_pilot_tournament,
    run_tournament,
)

__all__ = [
    "DECK_FAMILIES",
    "REFERENCE_DECK",
    "SPLIT_ASSIGNMENTS",
    "FirstAgent",
    "HeuristicAgent",
    "RandomAgent",
    "choose_random_action",
    "compute_deck_hash",
    "compute_wilson_interval",
    "format_deck_summary",
    "get_attack_by_id",
    "get_attack_sha256",
    "get_catalog_by_id",
    "get_catalog_sha256",
    "get_deck_family",
    "load_attack_catalog",
    "load_card_catalog",
    "run_battle",
    "run_paired_match",
    "run_pilot_tournament",
    "run_tournament",
    "sanitize_observation",
    "validate_deck",
    "verify_split_disjointness",
]
