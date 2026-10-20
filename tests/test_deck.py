import pytest

from tcg_cabt_lab.deck import (
    DECK_SIZE,
    REFERENCE_DECK,
    format_deck_summary,
    validate_deck,
)


def test_reference_deck_satisfies_invariants() -> None:
    assert len(REFERENCE_DECK) == DECK_SIZE
    valid = validate_deck(REFERENCE_DECK)
    assert valid == list(REFERENCE_DECK)


def test_deck_validation_rejects_wrong_size() -> None:
    with pytest.raises(ValueError, match="must contain exactly 60 cards"):
        validate_deck(list(REFERENCE_DECK[:59]))

    with pytest.raises(ValueError, match="must contain exactly 60 cards"):
        validate_deck([*list(REFERENCE_DECK), 3])


def test_deck_validation_rejects_non_integers() -> None:
    bad_deck = list(REFERENCE_DECK)
    bad_deck[0] = "721"  # type: ignore[call-overload]
    with pytest.raises(TypeError, match="must be an integer"):
        validate_deck(bad_deck)

    bad_bool_deck = list(REFERENCE_DECK)
    bad_bool_deck[0] = True
    with pytest.raises(TypeError, match="must be an integer"):
        validate_deck(bad_bool_deck)


def test_deck_validation_rejects_excess_copies() -> None:
    mock_catalog = {
        100: {"cardId": 100, "name": "Pikachu", "basic": True, "cardType": 0, "energyType": 0},
        1: {"cardId": 1, "name": "Basic Lightning Energy", "cardType": 5, "energyType": 1},
    }
    # 5 copies of Pikachu (max allowed is 4)
    deck = [100] * 5 + [1] * 55
    with pytest.raises(ValueError, match="maximum permitted is 4"):
        validate_deck(deck, catalog=mock_catalog)


def test_deck_validation_rejects_no_basic_pokemon() -> None:
    mock_catalog = {
        1: {"cardId": 1, "name": "Basic Energy", "cardType": 5, "energyType": 1, "basic": False},
    }
    deck = [1] * 60
    with pytest.raises(ValueError, match="at least one Basic Pokemon"):
        validate_deck(deck, catalog=mock_catalog)


def test_deck_validation_rejects_unknown_card() -> None:
    mock_catalog = {
        100: {"cardId": 100, "name": "Pikachu", "basic": True, "cardType": 0, "energyType": 0},
        1: {"cardId": 1, "name": "Basic Energy", "cardType": 5, "energyType": 1, "basic": False},
    }
    deck = [100] + [1] * 58 + [99999]
    with pytest.raises(ValueError, match="does not exist in the CABT card catalog"):
        validate_deck(deck, catalog=mock_catalog)


def test_format_deck_summary() -> None:
    summary = format_deck_summary(REFERENCE_DECK)
    assert "Deck (60 cards" in summary
    assert "Card    3" in summary
    assert "Basic {W} Energy" in summary
