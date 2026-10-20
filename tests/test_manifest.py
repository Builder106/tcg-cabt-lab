import pytest

from tcg_cabt_lab.manifest import (
    DECK_FAMILIES,
    compute_deck_hash,
    get_deck_family,
    verify_split_disjointness,
)


def test_canonical_deck_families_are_valid() -> None:
    assert len(DECK_FAMILIES) == 6
    for name, record in DECK_FAMILIES.items():
        assert record["family"] == name
        assert len(record["deck"]) == 60
        assert len(record["signature_pokemon"]) >= 2
        d_hash = compute_deck_hash(record["deck"])
        assert len(d_hash) == 64


def test_get_deck_family_unknown_raises_key_error() -> None:
    with pytest.raises(KeyError, match="Unknown deck family 'unknown-deck'"):
        get_deck_family("unknown-deck")


def test_split_disjointness_passes_for_canonical_splits() -> None:
    verified = verify_split_disjointness()
    assert set(verified.keys()) == {"training", "tuning", "final_test"}
    assert len(verified["training"]) == 3
    assert len(verified["tuning"]) == 1
    assert len(verified["final_test"]) == 2

    # Check all decks in verified split are valid
    for families in verified.values():
        for fam in families:
            assert len(fam["deck"]) == 60
            assert len(fam["deck_sha256"]) == 64


def test_split_disjointness_rejects_family_overlap() -> None:
    bad_splits = {
        "training": ["water-kyogre", "grass-bulbasaur"],
        "tuning": ["water-kyogre"],  # Overlaps with training!
        "final_test": ["psychic-mewtwo"],
    }
    with pytest.raises(ValueError, match="appears in both 'training' and 'tuning'"):
        verify_split_disjointness(bad_splits)


def test_split_disjointness_rejects_signature_pokemon_leak() -> None:
    # If a custom split definition attempts to reuse a signature Pokemon
    mock_splits = {
        "split_a": ["water-kyogre"],
        "split_b": ["water-kyogre"],
    }
    with pytest.raises(ValueError, match="appears in both"):
        verify_split_disjointness(mock_splits)
