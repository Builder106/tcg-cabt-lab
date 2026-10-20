"""Observation sanitization and agent interfaces for CABT."""

import copy
from collections.abc import Mapping, Sequence
from random import Random
from typing import Any

from tcg_cabt_lab.baseline import choose_random_action
from tcg_cabt_lab.deck import REFERENCE_DECK, validate_deck

DISALLOWED_OBSERVATION_KEYS = frozenset({"search_begin_input"})


def sanitize_observation(raw_obs: Mapping[str, Any]) -> dict[str, Any]:
    """Sanitize observation to enforce an observation-only agent boundary.

    Strips C++ internal engine states (such as search_begin_input) and ensures
    opponent hidden information (such as hidden hand cards) is masked.

    Args:
        raw_obs: Raw observation dictionary from kaggle-environments.

    Returns:
        Deep-copied, sanitized observation dictionary suitable for agent input.
    """
    clean: dict[str, Any] = {}
    for key, value in raw_obs.items():
        if key in DISALLOWED_OBSERVATION_KEYS:
            continue
        clean[key] = copy.deepcopy(value)

    current = clean.get("current")
    if isinstance(current, dict):
        your_index = current.get("yourIndex")
        players = current.get("players")
        if isinstance(your_index, int) and isinstance(players, list):
            opponent_index = 1 - your_index
            if 0 <= opponent_index < len(players):
                opponent = players[opponent_index]
                if isinstance(opponent, dict):
                    # Opponent's hand must be private/masked
                    opponent["hand"] = None

    return clean


class Agent:
    """Base protocol for a CABT agent."""

    def __call__(self, observation: Mapping[str, Any]) -> list[int]:
        raise NotImplementedError


class RandomAgent:
    """Random choice agent satisfying CABT's step 0 deck and in-game selection."""

    def __init__(
        self,
        seed: int = 11,
        deck: Sequence[int] | None = None,
    ) -> None:
        self.rng = Random(seed)
        self.deck = validate_deck(deck) if deck is not None else list(REFERENCE_DECK)

    def __call__(
        self,
        observation: Mapping[str, Any],
        configuration: Mapping[str, Any] | None = None,
    ) -> list[int]:
        clean_obs = sanitize_observation(observation)
        return choose_random_action(
            clean_obs,
            self.rng,
            allow_deck_selection=True,
            default_deck=self.deck,
        )
