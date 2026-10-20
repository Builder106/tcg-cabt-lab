"""Research scaffolding and CABT engine integration for 60-card Pokemon TCG agents."""

from tcg_cabt_lab.agent import RandomAgent, sanitize_observation
from tcg_cabt_lab.baseline import choose_random_action
from tcg_cabt_lab.battle import run_battle
from tcg_cabt_lab.catalog import get_catalog_sha256, load_card_catalog
from tcg_cabt_lab.deck import REFERENCE_DECK, format_deck_summary, validate_deck

__all__ = [
    "REFERENCE_DECK",
    "RandomAgent",
    "choose_random_action",
    "format_deck_summary",
    "get_catalog_sha256",
    "load_card_catalog",
    "run_battle",
    "sanitize_observation",
    "validate_deck",
]
