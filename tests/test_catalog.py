from tcg_cabt_lab.catalog import (
    EXPECTED_CARD_COUNT,
    EXPECTED_CATALOG_SHA256,
    get_catalog_by_id,
    get_catalog_sha256,
    load_card_catalog,
)


def test_card_catalog_sha256_matches_pinned_checksum() -> None:
    digest = get_catalog_sha256()
    assert digest == EXPECTED_CATALOG_SHA256


def test_card_catalog_contains_expected_card_count() -> None:
    cards = load_card_catalog()
    assert len(cards) == EXPECTED_CARD_COUNT


def test_card_catalog_by_id_indexing() -> None:
    by_id = get_catalog_by_id()
    assert len(by_id) == EXPECTED_CARD_COUNT

    # Spot check card 1 (Basic {G} Energy)
    card1 = by_id[1]
    assert card1["cardId"] == 1
    assert card1["name"] == "Basic {G} Energy"
    assert card1["cardType"] == 5

    # Spot check card 721 (Kyogre)
    card721 = by_id[721]
    assert card721["cardId"] == 721
    assert card721["name"] == "Kyogre"
    assert card721["basic"] is True
