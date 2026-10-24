"""60-card deck validation and reference deck definitions for CABT."""

from collections import Counter
from collections.abc import Mapping, Sequence

from tcg_cabt_lab.catalog import get_catalog_by_id

REFERENCE_DECK: tuple[int, ...] = (
    721,
    721,
    722,
    722,
    722,
    722,
    723,
    723,
    723,
    723,
    1092,
    1121,
    1121,
    1145,
    1145,
    1163,
    1163,
    1219,
    1219,
    1219,
    1219,
    1227,
    1227,
    1227,
    1227,
    1262,
    1262,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
)

DECK_SIZE = 60
MAX_COPIES_NON_BASIC_ENERGY = 4


def validate_deck(
    deck: Sequence[int],
    catalog: Mapping[int, Mapping[str, object]] | None = None,
) -> list[int]:
    """Validate a 60-card Pokemon TCG deck against standard deck invariants.

    Args:
        deck: Sequence of integer card IDs.
        catalog: Optional mapping from card ID to card attributes. If None,
            the catalog will be queried from the engine catalog helper.

    Returns:
        List of 60 validated card IDs.

    Raises:
        ValueError: If card count is not 60, card IDs are unknown, non-basic
            energy cards exceed 4 copies, or no Basic Pokemon exists.
        TypeError: If card IDs are not integer types.
    """
    if len(deck) != DECK_SIZE:
        raise ValueError(f"Deck must contain exactly {DECK_SIZE} cards, got {len(deck)}")

    normalized_deck: list[int] = []
    for index, card_id in enumerate(deck):
        if not isinstance(card_id, int) or isinstance(card_id, bool):
            raise TypeError(
                f"Card at index {index} must be an integer, got {type(card_id).__name__}"
            )
        normalized_deck.append(card_id)

    if catalog is None:
        try:
            catalog = get_catalog_by_id()
        except Exception:
            catalog = None

    if catalog is not None:
        counts = Counter(normalized_deck)
        name_counts: Counter[str] = Counter()
        has_basic_pokemon = False

        for cid, count in counts.items():
            card = catalog.get(cid)
            if card is None:
                raise ValueError(f"Card ID {cid} does not exist in the CABT card catalog")

            card_name_value = card.get("name", f"Card-{cid}")
            card_name = card_name_value if isinstance(card_name_value, str) else f"Card-{cid}"
            is_basic_energy = card.get("energyType") == 1 or (
                card.get("cardType") == 5 and card_name.startswith("Basic")
            )
            if not is_basic_energy:
                name_counts[card_name] += count
                if name_counts[card_name] > MAX_COPIES_NON_BASIC_ENERGY:
                    raise ValueError(
                        f"Deck has {name_counts[card_name]} copies of '{card_name}'; "
                        f"maximum permitted is {MAX_COPIES_NON_BASIC_ENERGY}"
                    )

            if card.get("basic") is True:
                has_basic_pokemon = True

        if not has_basic_pokemon:
            raise ValueError("Deck must contain at least one Basic Pokemon to be playable")

    return normalized_deck


def format_deck_summary(
    deck: Sequence[int],
    catalog: Mapping[int, Mapping[str, object]] | None = None,
) -> str:
    """Format a human-readable summary of deck contents."""
    if catalog is None:
        try:
            catalog = get_catalog_by_id()
        except Exception:
            catalog = None

    counts = Counter(deck)
    lines: list[str] = [f"Deck ({len(deck)} cards, {len(counts)} unique):"]
    for cid, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
        name = catalog.get(cid, {}).get("name", "Unknown") if catalog else "Unknown"
        lines.append(f"  {count:2d}x Card {cid:4d}: {name}")
    return "\n".join(lines)
