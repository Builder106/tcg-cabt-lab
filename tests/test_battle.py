from collections.abc import Mapping
from typing import Any

from tcg_cabt_lab.agent import RandomAgent
from tcg_cabt_lab.battle import run_battle


def test_full_battle_execution_and_schema() -> None:
    log = run_battle(seed_p0=11, seed_p1=22, best_of=1)

    metadata = log["metadata"]
    assert metadata["engine"] == "cabt"
    assert metadata["spec_version"] == "1.0.0"
    assert metadata["package_version"] == "1.33.0"
    assert metadata["best_of"] == 1
    assert metadata["total_steps"] > 10

    outcome = log["outcome"]
    assert outcome["winner"] in (0, 1, "draw")
    assert outcome["statuses"] == ["DONE", "DONE"]
    assert outcome["rewards"] in ([-1, 1], [1, -1], [0, 0])

    players = log["players"]
    assert len(players) == 2
    assert len(players[0]["deck"]) == 60
    assert len(players[1]["deck"]) == 60

    # Verify every recorded observation respects the information boundary
    for step_record in log["steps"]:
        obs = step_record["observation"]
        if obs is not None:
            assert "search_begin_input" not in obs


def test_battle_outcome_structure() -> None:
    log = run_battle(seed_p0=101, seed_p1=202, best_of=1)

    assert "metadata" in log
    assert "players" in log
    assert "outcome" in log
    assert "steps" in log
    assert len(log["steps"]) == log["metadata"]["total_steps"]

    final_step = log["steps"][-1]
    assert final_step["status"] == ["DONE", "DONE"]


def test_invalid_action_handling() -> None:
    # Player 0 plays an out-of-bounds action during in-game choices
    def faulty_agent(
        obs: Mapping[str, Any], config: Any = None  # noqa: ANN401
    ) -> list[int]:
        if obs.get("select") is None:
            from tcg_cabt_lab.deck import REFERENCE_DECK

            return list(REFERENCE_DECK)
        return [99999]

    log = run_battle(
        agent_p0=faulty_agent,
        agent_p1=RandomAgent(seed=7),
        best_of=1,
    )

    p0_status = log["players"][0]["final_status"]
    assert p0_status == "INVALID"
    assert log["outcome"]["winner"] == 1
