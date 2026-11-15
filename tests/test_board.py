from collections.abc import Callable, Mapping
from typing import Any

import pytest

from tcg_cabt_lab.agent import FirstAgent
from tcg_cabt_lab.battle import run_battle
from tcg_cabt_lab.board import Area, BoardAgent, OptionType, missing_energy
from tcg_cabt_lab.manifest import get_deck_family
from tcg_cabt_lab.training import FINAL_TEST_FAMILIES, TRAINING_FAMILIES

KYOGRE, WATER_ENERGY, LILLIE, SNORLAX = 721, 3, 1227, 304
WATER = 3


@pytest.fixture(scope="module")
def agent() -> BoardAgent:
    return BoardAgent()


def kyogre(energies: list[int], hp: int = 150) -> dict[str, Any]:
    return {"id": KYOGRE, "hp": hp, "maxHp": 150, "energies": energies}


def strongest_attack(agent: BoardAgent) -> Mapping[str, Any]:
    return max(agent._attacks_of({"id": KYOGRE}), key=lambda a: int(a["damage"]))


def paid(attack: Mapping[str, Any]) -> list[int]:
    """Energy types that pay the attack's cost with Water energy."""
    return [WATER for _ in attack["energies"]]


def observation(
    options: list[dict[str, Any]],
    me: dict[str, Any],
    opponent: dict[str, Any],
    context: int = 0,
    min_count: int = 1,
    max_count: int = 1,
) -> dict[str, Any]:
    return {
        "select": {
            "type": 0,
            "context": context,
            "minCount": min_count,
            "maxCount": max_count,
            "option": options,
        },
        "current": {"yourIndex": 0, "players": [me, opponent]},
    }


def player(
    active: dict[str, Any] | None, bench: list[dict[str, Any]], hand: list[int]
) -> dict[str, Any]:
    return {
        "active": [active] if active else [],
        "bench": bench,
        "hand": [{"id": c} for c in hand],
    }


def test_missing_energy_counts_typed_and_colorless_costs() -> None:
    assert missing_energy([3], [3, 0]) == 1
    assert missing_energy([3, 3], [3, 0]) == 0
    assert missing_energy([10], [5]) == 0
    assert missing_energy([1], [3]) == 1
    assert missing_energy([], [0, 0]) == 2


def test_returns_deck_at_deck_selection(agent: BoardAgent) -> None:
    assert agent({"select": None}) == agent.deck


def test_takes_a_knockout_before_setting_up(agent: BoardAgent) -> None:
    attack = strongest_attack(agent)
    attacker = kyogre(paid(attack))
    damage = agent._damage(attack, attacker, {"id": SNORLAX})
    options: list[dict[str, Any]] = [
        {"type": OptionType.END},
        {"type": OptionType.EVOLVE, "inPlayArea": Area.ACTIVE, "inPlayIndex": 0},
        {"type": OptionType.ATTACK, "attackId": attack["attackId"]},
    ]
    opponent = player({"id": SNORLAX, "hp": damage, "energies": []}, [], [])
    obs = observation(options, player(attacker, [], []), opponent)
    assert agent(obs) == [2]


def test_sets_up_before_an_attack_that_does_not_knock_out(agent: BoardAgent) -> None:
    attack = strongest_attack(agent)
    attacker = kyogre(paid(attack))
    damage = agent._damage(attack, attacker, {"id": SNORLAX})
    options: list[dict[str, Any]] = [
        {"type": OptionType.END},
        {"type": OptionType.EVOLVE, "inPlayArea": Area.ACTIVE, "inPlayIndex": 0},
        {"type": OptionType.ATTACK, "attackId": attack["attackId"]},
    ]
    opponent = player({"id": SNORLAX, "hp": damage + 50, "energies": []}, [], [])
    obs = observation(options, player(attacker, [], []), opponent)
    assert agent(obs) == [1]


def test_benches_a_basic_pokemon_before_a_supporter_when_the_bench_is_short(
    agent: BoardAgent,
) -> None:
    options: list[dict[str, Any]] = [
        {"type": OptionType.END},
        {"type": OptionType.PLAY, "index": 1},
        {"type": OptionType.PLAY, "index": 0},
    ]
    me = player(kyogre([]), [], [KYOGRE, LILLIE])
    obs = observation(options, me, player({"id": SNORLAX, "hp": 150}, [], []))
    assert agent(obs) == [2]


def test_attaches_energy_where_it_brings_an_attack_closest(agent: BoardAgent) -> None:
    attack = strongest_attack(agent)
    ready = kyogre(paid(attack))
    empty = kyogre([])
    options: list[dict[str, Any]] = [
        {"type": OptionType.ATTACH, "area": Area.HAND, "index": 0, "inPlayArea": Area.ACTIVE},
        {
            "type": OptionType.ATTACH,
            "area": Area.HAND,
            "index": 0,
            "inPlayArea": Area.BENCH,
            "inPlayIndex": 0,
        },
    ]
    me = player(ready, [empty], [WATER_ENERGY])
    obs = observation(options, me, player({"id": SNORLAX, "hp": 150}, [], []))
    assert agent(obs) == [1]


def test_retreats_only_when_the_bench_offers_an_attacker(agent: BoardAgent) -> None:
    attack = strongest_attack(agent)
    options = [{"type": OptionType.END}, {"type": OptionType.RETREAT}]
    opponent = player({"id": SNORLAX, "hp": 150, "energies": []}, [], [])

    stuck = player(kyogre([]), [kyogre(paid(attack))], [])
    assert agent(observation(options, stuck, opponent)) == [1]

    nobody_ready = player(kyogre([]), [kyogre([])], [])
    assert agent(observation(options, nobody_ready, opponent)) == [0]


def test_discards_the_least_valuable_card_and_no_more(agent: BoardAgent) -> None:
    attack = strongest_attack(agent)
    me = player(kyogre(paid(attack)), [], [WATER_ENERGY, KYOGRE])
    options: list[dict[str, Any]] = [
        {"type": OptionType.CARD, "area": Area.HAND, "index": 1, "playerIndex": 0},
        {"type": OptionType.CARD, "area": Area.HAND, "index": 0, "playerIndex": 0},
    ]
    obs = observation(
        options, me, player({"id": SNORLAX, "hp": 150}, [], []), context=8, max_count=2
    )
    assert agent(obs) == [1]


@pytest.mark.parametrize("family", [*TRAINING_FAMILIES, *FINAL_TEST_FAMILIES])
def test_plays_full_games_without_invalid_moves(family: str) -> None:
    deck = get_deck_family(family)["deck"]
    for seat in (0, 1):
        board = BoardAgent(deck=deck)
        first = FirstAgent(deck=deck)
        agents: list[Callable[..., list[int]]] = [board, first] if seat == 0 else [first, board]
        log = run_battle(agent_p0=agents[0], agent_p1=agents[1], best_of=1)
        assert log["players"][seat]["final_status"] != "INVALID"
        assert log["outcome"]["winner"] in (0, 1, None)
