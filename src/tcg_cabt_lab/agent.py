"""Observation sanitization and agent interfaces for CABT."""

import copy
from collections.abc import Mapping, Sequence
from random import Random
from typing import Any

from tcg_cabt_lab.baseline import choose_random_action
from tcg_cabt_lab.catalog import get_attack_by_id
from tcg_cabt_lab.deck import REFERENCE_DECK, validate_deck

DISALLOWED_OBSERVATION_KEYS = frozenset({"search_begin_input"})


def sanitize_observation(
    raw_obs: Mapping[str, Any],
) -> dict[str, Any]:
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


class FirstAgent:
    """Greedy choice agent matching CABT's documented first_agent baseline."""

    def __init__(self, deck: Sequence[int] | None = None) -> None:
        self.deck = validate_deck(deck) if deck is not None else list(REFERENCE_DECK)

    def __call__(
        self,
        observation: Mapping[str, Any],
        configuration: Mapping[str, Any] | None = None,
    ) -> list[int]:
        clean_obs = sanitize_observation(observation)
        sel = clean_obs.get("select")
        if sel is None:
            return list(self.deck)
        max_count = sel.get("maxCount", 0)
        options = sel.get("option", [])
        return list(range(min(max_count, len(options))))


class HeuristicAgent:
    """Transparent rule-based heuristic agent prioritizing attacks and board development."""

    def __init__(self, deck: Sequence[int] | None = None) -> None:
        self.deck = validate_deck(deck) if deck is not None else list(REFERENCE_DECK)
        try:
            self.attacks = get_attack_by_id()
        except Exception:
            self.attacks = {}

    def score_option(self, option: Mapping[str, Any]) -> int:
        """Assign an explainable priority score to a selection option."""
        opt_type = option.get("type", -1)

        # Priority 1: Attacks (type 13), ranked by damage
        if opt_type == 13:
            attack_id = option.get("attackId")
            damage = 0
            if isinstance(attack_id, int):
                damage = int(self.attacks.get(attack_id, {}).get("damage", 0))
            return 10000 + damage

        # Priority 2: Bench or evolve Pokemon (type 8)
        if opt_type == 8:
            return 5000

        # Priority 3: Attach Energy (type 9)
        if opt_type == 9:
            in_play_area = option.get("inPlayArea", 0)
            # Prefer active Pokemon (inPlayArea == 4, inPlayIndex == 0)
            in_play_index = option.get("inPlayIndex", 0)
            return 4500 if (in_play_area == 4 and in_play_index == 0) else 4000

        # Priority 4: Play Trainers (type 7)
        if opt_type == 7:
            return 3000

        # Priority 5: Specific in-game selections (targeting, switching, retrieval)
        if opt_type in (1, 2, 3, 10, 12):
            return 2000

        # Priority 6: Pass or End Turn (type 14)
        if opt_type == 14:
            return 10

        return 100

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
        max_count = int(sel.get("maxCount", 0))
        min_count = int(sel.get("minCount", 0))

        if not options or max_count <= 0:
            return []

        scored_options: list[tuple[int, int]] = []
        for index, opt in enumerate(options):
            score = self.score_option(opt) if isinstance(opt, Mapping) else 0
            scored_options.append((score, index))

        # Sort by score descending; break ties by option index
        scored_options.sort(key=lambda pair: (-pair[0], pair[1]))

        # Select top max_count choices
        chosen = [idx for _, idx in scored_options[:max_count]]

        # If min_count is 0, only pass if pass is the only option or options are exhausted
        if min_count == 0 and len(chosen) > 0:
            top_score = scored_options[0][0]
            # If the only options available are pass (score == 10)
            if top_score == 10 and max_count == 1:
                return chosen

        return chosen
