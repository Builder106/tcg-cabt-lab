"""Sample distinct choice indices using CABT's documented selection fields."""

from collections.abc import Sequence
from random import Random


def choose_random_action(
    observation: object,
    rng: Random,
    allow_deck_selection: bool = False,
    default_deck: Sequence[int] | None = None,
) -> list[int]:
    """Select maxCount choices, matching the documented random baseline.

    Args:
        observation: Observation dictionary.
        rng: Random number generator.
        allow_deck_selection: When True, returns a 60-card deck list if select is None.
            When False, raises ValueError for unsupported deck selection.
        default_deck: 60-card deck to return on step 0 if allow_deck_selection is True.

    Returns:
        List of selected option indices (or card IDs if selecting deck).
    """
    if not isinstance(observation, dict):
        raise ValueError("observation must be a JSON object")

    selection: object = observation.get("select")
    if selection is None and allow_deck_selection:
        if default_deck is not None:
            return list(default_deck)
        from tcg_cabt_lab.deck import REFERENCE_DECK

        return list(REFERENCE_DECK)

    if not isinstance(selection, dict):
        raise ValueError("select must be an object; deck selection is not supported")

    options: object = selection.get("option")
    if not isinstance(options, list):
        raise ValueError("select.option must be an array")

    max_count: object = selection.get("maxCount")
    if not isinstance(max_count, int) or isinstance(max_count, bool):
        raise ValueError("select.maxCount must be an integer")

    min_count: object = selection.get("minCount", 0)
    if not isinstance(min_count, int) or isinstance(min_count, bool):
        raise ValueError("select.minCount must be an integer")
    if not 0 <= min_count <= max_count <= len(options):
        raise ValueError("selection counts must satisfy 0 <= minCount <= maxCount <= option count")

    return rng.sample(range(len(options)), max_count)
