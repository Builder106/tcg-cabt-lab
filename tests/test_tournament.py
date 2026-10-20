from tcg_cabt_lab.agent import FirstAgent, RandomAgent
from tcg_cabt_lab.deck import REFERENCE_DECK
from tcg_cabt_lab.tournament import (
    compute_wilson_interval,
    run_paired_match,
    run_tournament,
)


def test_compute_wilson_interval() -> None:
    # Edge case 0/0
    assert compute_wilson_interval(0, 0) == (0.0, 0.0)

    # 50 wins out of 100
    low, high = compute_wilson_interval(50, 100)
    assert 0.40 <= low <= 0.41
    assert 0.59 <= high <= 0.60

    # 10 wins out of 10 (perfect score)
    low_perf, high_perf = compute_wilson_interval(10, 10)
    assert 0.72 <= low_perf <= 0.75
    assert high_perf == 1.0


def test_run_paired_match_reverses_player_assignments() -> None:
    res = run_paired_match(
        agent_a_factory=lambda deck=None: RandomAgent(seed=10, deck=deck),
        agent_b_factory=lambda deck=None: RandomAgent(seed=20, deck=deck),
        deck_a=list(REFERENCE_DECK),
        deck_b=list(REFERENCE_DECK),
        seed_a=100,
        seed_b=200,
    )

    assert len(res["games"]) == 2
    g1, g2 = res["games"][0], res["games"][1]

    # Game 1: P0 is A, P1 is B
    assert g1["agent_p0"] == "A"
    assert g1["agent_p1"] == "B"

    # Game 2: P0 is B, P1 is A (reversed)
    assert g2["agent_p0"] == "B"
    assert g2["agent_p1"] == "A"

    # Score sum must equal total game count (2.0)
    assert res["score_a"] + res["score_b"] == 2.0


def test_run_tournament_structure() -> None:
    competitors = {
        "first": lambda deck=None: FirstAgent(deck=deck),
        "random": lambda deck=None: RandomAgent(seed=42, deck=deck),
    }

    report = run_tournament(
        competitors=competitors,
        deck_family_names=["water-kyogre"],
        pairs_per_matchup=1,  # 1 pair = 2 games
        base_seed=300,
    )

    assert report["metadata"]["total_games"] == 2
    assert len(report["leaderboard"]) == 2

    # Check leaderboard schema
    for entry in report["leaderboard"]:
        assert "name" in entry
        assert "win_rate" in entry
        assert "confidence_interval_95" in entry
        assert len(entry["confidence_interval_95"]) == 2
        assert entry["total_games"] == 2

    # Check matchup grid
    grid = report["matchup_grid"]
    assert "first" in grid and "random" in grid
    # Diagonal is 0.0, off-diagonal sums to 1.0
    assert grid["first"]["random"] + grid["random"]["first"] == 1.0
