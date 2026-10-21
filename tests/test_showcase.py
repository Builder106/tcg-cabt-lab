"""Tests for compact showcase replays and per-game records."""

import gzip
import json
from pathlib import Path
from typing import Any

from tcg_cabt_lab.agent import FirstAgent
from tcg_cabt_lab.battle import run_battle
from tcg_cabt_lab.catalog import get_attack_by_id, get_catalog_by_id
from tcg_cabt_lab.experiment import evaluate_checkpoint_on_heldout
from tcg_cabt_lab.manifest import get_deck_family
from tcg_cabt_lab.policy import CompactPolicy, PolicyAgent, create_checkpoint, save_checkpoint
from tcg_cabt_lab.showcase import compact_replay, end_reason, option_label, summarize_game

CATALOG = {
    3: {"name": "Basic {W} Energy"},
    304: {"name": "Hop's Snorlax"},
    1072: {"name": "Snorlax"},
}
ATTACKS = {1547: {"name": "Collapse", "damage": 170}}


def _frame(context: str = "Main") -> dict[str, Any]:
    snorlax = {"id": 1072, "energyCards": [{"id": 3}], "preEvolution": []}
    return {
        "select": {"context": context},
        "current": {
            "yourIndex": 0,
            "players": [
                {"active": [snorlax], "bench": [{"id": 304}], "hand": [{"id": 3}]},
                {"active": [{"id": 304}], "bench": [], "hand": None},
            ],
        },
    }


def _label(option: dict[str, Any], context: str = "Main") -> str:
    return option_label(option, _frame(context), CATALOG, ATTACKS)


def test_option_labels_use_card_and_attack_names() -> None:
    assert _label({"type": "End"}) == "End turn"
    assert _label({"type": "Retreat"}) == "Retreat Snorlax"
    assert _label({"type": "Attack", "attackId": 1547}) == "Attack: Collapse for 170"
    assert _label({"type": "Play", "index": 0}) == "Play Basic {W} Energy"
    attach = {"type": "Attach", "index": 0, "inPlayArea": 5, "inPlayIndex": 0}
    assert _label(attach) == "Attach Basic {W} Energy to Hop's Snorlax"
    switch = {"type": "Card", "area": 4, "index": 0, "playerIndex": 1}
    assert _label(switch, "Switch") == "Hop's Snorlax (opponent's active)"
    energy = {"type": "Energy", "area": 4, "index": 0, "playerIndex": 0, "energyIndex": 0}
    assert _label(energy, "DiscardEnergy") == "Basic {W} Energy on Snorlax"
    assert _label({"type": "Yes"}, "IsFirst") == "Go first"
    assert _label({"type": "Number", "number": 2}, "DrawCount") == "2"


def test_option_label_tolerates_out_of_range_indices() -> None:
    assert _label({"type": "Play", "index": 9}) == "Play a card"
    assert _label({"type": "Mystery"}) == "Mystery"
    assert _label({"type": "EnergyCard"}, "DiscardEnergyCard") == "Energy card"


def test_end_reason_classification() -> None:
    def frames(reason: int) -> list[dict[str, Any]]:
        return [{"logs": [{"type": "Result", "result": 0, "reason": reason}]}]

    assert end_reason(frames(1), ["DONE", "DONE"]) == ("prizes", 1)
    assert end_reason(frames(2), ["DONE", "DONE"]) == ("deck-out", 2)
    assert end_reason(frames(3), ["DONE", "DONE"]) == ("no-pokemon", 3)
    assert end_reason(frames(9), ["DONE", "DONE"]) == ("unknown", 9)
    assert end_reason([], ["INVALID", "DONE"]) == ("invalid", None)


def _checkpoint(tmp_path: Path) -> Path:
    ckpt = create_checkpoint(
        policy=CompactPolicy(input_dim=88, hidden_dim=32, seed=11),
        variant="fixed-opponent-pool",
        seed=11,
        training_steps=10,
        training_deck_families=["water-kyogre"],
    )
    path = tmp_path / "ckpt.json"
    save_checkpoint(ckpt, path)
    return path


def test_compact_replay_aligns_decisions_and_scores(tmp_path: Path) -> None:
    deck = get_deck_family("colorless-snorlax")["deck"]
    log = run_battle(
        agent_p0=PolicyAgent(_checkpoint(tmp_path), deck=deck),
        agent_p1=FirstAgent(deck=deck),
        deck_p0=deck,
        deck_p1=deck,
        record_replay=True,
    )
    game = {"game_id": "test", **summarize_game(log, policy_seat=0)}
    replay = compact_replay(log, game, get_catalog_by_id(), get_attack_by_id())

    frames = replay["frames"]
    assert len(frames) == len(log["replay"]["decisions"]) + 1
    policy_frames = [f for f in frames if f["actor"] == 0 and f["options"]]
    assert policy_frames
    for frame in policy_frames:
        assert len(frame["scores"]) == len(frame["options"])
        assert all(0 <= i < len(frame["options"]) for i in frame["chosen"])
    assert all(f["scores"] is None for f in frames if f["actor"] == 1)
    assert all(len(f["players"]) == 2 for f in frames)
    shown = {m["id"] for f in frames for p in f["players"] for m in p["active"] + p["bench"]}
    assert shown <= set(replay["cards"])
    assert all(card["name"] for card in replay["cards"].values())

    expected = {0: "win", 1: "loss", "draw": "draw"}[log["outcome"]["winner"]]
    assert game["result"] == expected
    assert game["end_reason"] in ("prizes", "deck-out", "no-pokemon")


def test_heldout_evaluation_writes_replays(tmp_path: Path) -> None:
    replay_dir = tmp_path / "replays"
    result = evaluate_checkpoint_on_heldout(
        checkpoint_path=_checkpoint(tmp_path),
        test_families=["colorless-snorlax"],
        opponents=["first"],
        eval_seeds=[11],
        replay_dir=replay_dir,
    )

    games = result["games"]
    assert [g["policy_seat"] for g in games] == [0, 1]
    for g in games:
        with gzip.open(replay_dir / f"{g['game_id']}.json.gz", "rt") as f:
            replay = json.load(f)
        assert replay["game"]["game_id"] == g["game_id"]
        assert replay["frames"]
    points = sum({"win": 1.0, "draw": 0.5, "loss": 0.0}[g["result"]] for g in games)
    assert points == result["total_points"]
