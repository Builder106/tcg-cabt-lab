from tcg_cabt_lab.agent import RandomAgent, sanitize_observation
from tcg_cabt_lab.deck import REFERENCE_DECK


def test_sanitize_observation_strips_disallowed_keys() -> None:
    raw_obs = {
        "step": 4,
        "remainingOverageTime": 595.0,
        "search_begin_input": "SECRET_TREE_SEARCH_STATE",
        "select": {"minCount": 1, "maxCount": 1, "option": [{}]},
        "current": {
            "yourIndex": 0,
            "players": [
                {"hand": [{"cardId": 721}], "deckCount": 45},
                {"hand": [{"cardId": 1219}], "deckCount": 46},
            ],
        },
        "logs": ["Turn 1 started"],
    }

    clean = sanitize_observation(raw_obs)

    # Private C++ state must be removed
    assert "search_begin_input" not in clean
    assert clean["step"] == 4
    assert clean["remainingOverageTime"] == 595.0
    assert clean["select"] == raw_obs["select"]
    assert clean["logs"] == raw_obs["logs"]

    # Player 0 (acting) hand preserved
    assert clean["current"]["players"][0]["hand"] == [{"cardId": 721}]
    # Opponent (player 1) hand must be masked to None
    assert clean["current"]["players"][1]["hand"] is None


def test_random_agent_selects_deck_on_step_zero() -> None:
    agent = RandomAgent(seed=42)
    step0_obs: dict[str, object] = {
        "step": 0,
        "select": None,
        "remainingOverageTime": 600,
        "logs": [],
        "current": None,
    }
    action = agent(step0_obs)
    assert action == list(REFERENCE_DECK)
    assert len(action) == 60


def test_random_agent_selects_in_game_options() -> None:
    agent = RandomAgent(seed=42)
    obs = {
        "step": 1,
        "select": {
            "minCount": 1,
            "maxCount": 2,
            "option": [{"type": 1}, {"type": 2}, {"type": 3}],
        },
        "current": {"yourIndex": 0, "players": [{"hand": []}, {"hand": None}]},
        "logs": [],
    }
    action = agent(obs)
    assert len(action) == 2
    assert len(set(action)) == 2
    assert all(0 <= idx < 3 for idx in action)


def test_random_agent_seed_reproducibility() -> None:
    agent1 = RandomAgent(seed=123)
    agent2 = RandomAgent(seed=123)
    obs = {
        "step": 2,
        "select": {
            "minCount": 0,
            "maxCount": 3,
            "option": [{"id": i} for i in range(10)],
        },
        "current": {"yourIndex": 0, "players": []},
    }
    assert agent1(obs) == agent2(obs)
