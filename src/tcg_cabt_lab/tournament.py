"""Tournament evaluation, matched pairings, failure accounting, and statistics."""

import math
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from tcg_cabt_lab.agent import FirstAgent, HeuristicAgent, RandomAgent
from tcg_cabt_lab.battle import run_battle
from tcg_cabt_lab.manifest import get_deck_family


def compute_wilson_interval(
    successes: float, total: int, confidence: float = 0.95
) -> tuple[float, float]:
    """Compute the Wilson score confidence interval for a binomial proportion.

    Args:
        successes: Number of successful outcomes (wins + 0.5 * draws).
        total: Total number of trials.
        confidence: Desired confidence level (default 0.95).

    Returns:
        Tuple of (lower_bound, upper_bound) clamped to [0.0, 1.0].
    """
    if total <= 0:
        return (0.0, 0.0)

    # z value for two-tailed normal distribution
    # 0.95 -> 1.95996, 0.99 -> 2.57583, 0.90 -> 1.64485
    z = 1.959963984540054
    if math.isclose(confidence, 0.90):
        z = 1.6448536269514722
    elif math.isclose(confidence, 0.99):
        z = 2.5758293035489004

    p = successes / total
    denom = 1.0 + (z**2) / total
    centre = (p + (z**2) / (2.0 * total)) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))

    lower = max(0.0, centre - spread)
    upper = min(1.0, centre + spread)
    return (round(lower, 4), round(upper, 4))


def run_paired_match(
    agent_a_factory: Callable[..., Any],
    agent_b_factory: Callable[..., Any],
    deck_a: Sequence[int],
    deck_b: Sequence[int],
    seed_a: int,
    seed_b: int,
    best_of: int = 1,
) -> dict[str, Any]:
    """Run two matched games between two agents with reversed player assignments.

    Game 1: Player 0 = Agent A (Deck A), Player 1 = Agent B (Deck B)
    Game 2: Player 0 = Agent B (Deck B), Player 1 = Agent A (Deck A)
    """
    # Game 1: Normal assignments
    t0 = time.perf_counter()
    p0_g1 = agent_a_factory(deck=deck_a)
    p1_g1 = agent_b_factory(deck=deck_b)
    log_g1 = run_battle(
        agent_p0=p0_g1,
        agent_p1=p1_g1,
        deck_p0=deck_a,
        deck_p1=deck_b,
        seed_p0=seed_a,
        seed_p1=seed_b,
        best_of=best_of,
    )
    duration_g1 = time.perf_counter() - t0

    # Game 2: Reversed assignments
    t1 = time.perf_counter()
    p0_g2 = agent_b_factory(deck=deck_b)
    p1_g2 = agent_a_factory(deck=deck_a)
    log_g2 = run_battle(
        agent_p0=p0_g2,
        agent_p1=p1_g2,
        deck_p0=deck_b,
        deck_p1=deck_a,
        seed_p0=seed_b,
        seed_p1=seed_a,
        best_of=best_of,
    )
    duration_g2 = time.perf_counter() - t1

    # In Game 1: Agent A is player 0, Agent B is player 1
    w_g1 = log_g1["outcome"]["winner"]
    st_a_g1 = log_g1["players"][0]["final_status"]
    st_b_g1 = log_g1["players"][1]["final_status"]

    # In Game 2: Agent A is player 1, Agent B is player 0
    w_g2 = log_g2["outcome"]["winner"]
    st_a_g2 = log_g2["players"][1]["final_status"]
    st_b_g2 = log_g2["players"][0]["final_status"]

    # Calculate points for Agent A
    score_a = 0.0
    if w_g1 == 0:
        score_a += 1.0
    elif w_g1 == "draw":
        score_a += 0.5

    if w_g2 == 1:
        score_a += 1.0
    elif w_g2 == "draw":
        score_a += 0.5

    return {
        "games": [
            {
                "game": 1,
                "agent_p0": "A",
                "agent_p1": "B",
                "winner": "A" if w_g1 == 0 else ("B" if w_g1 == 1 else "draw"),
                "statuses": {"A": st_a_g1, "B": st_b_g1},
                "total_steps": log_g1["metadata"]["total_steps"],
                "duration_seconds": round(duration_g1, 4),
            },
            {
                "game": 2,
                "agent_p0": "B",
                "agent_p1": "A",
                "winner": "B" if w_g2 == 0 else ("A" if w_g2 == 1 else "draw"),
                "statuses": {"A": st_a_g2, "B": st_b_g2},
                "total_steps": log_g2["metadata"]["total_steps"],
                "duration_seconds": round(duration_g2, 4),
            },
        ],
        "score_a": score_a,
        "score_b": 2.0 - score_a,
    }


def run_tournament(
    competitors: Mapping[str, Callable[..., Any]],
    deck_family_names: Sequence[str],
    pairs_per_matchup: int = 1,
    base_seed: int = 100,
) -> dict[str, Any]:
    """Run a round-robin tournament across multiple competitors and deck families.

    Args:
        competitors: Dict mapping agent name to constructor callable.
        deck_family_names: List of deck family names to include.
        pairs_per_matchup: Number of paired matches (each pair is 2 games) per matchup.
        base_seed: Base seed for deterministic random generation.

    Returns:
        Structured tournament report with win rates, failure accounts,
        confidence intervals, and matchup matrix.
    """
    comp_names = list(competitors.keys())
    results: dict[str, dict[str, Any]] = {
        name: {
            "name": name,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "invalids": 0,
            "total_games": 0,
            "points": 0.0,
            "total_duration_seconds": 0.0,
            "total_steps": 0,
        }
        for name in comp_names
    }

    matchup_grid: dict[str, dict[str, float]] = {
        name: {opp: 0.0 for opp in comp_names} for name in comp_names
    }

    decks: dict[str, list[int]] = {}
    for fam_name in deck_family_names:
        decks[fam_name] = get_deck_family(fam_name)["deck"]

    pair_index = 0
    # Head to head between every pair of agents across deck families
    for i, name_a in enumerate(comp_names):
        for j, name_b in enumerate(comp_names):
            if i >= j:
                continue

            factory_a = competitors[name_a]
            factory_b = competitors[name_b]

            h2h_points_a = 0.0
            h2h_games = 0

            for fam_name in deck_family_names:
                deck = decks[fam_name]
                for _p in range(pairs_per_matchup):
                    pair_index += 1
                    seed_a = base_seed + pair_index * 13
                    seed_b = base_seed + pair_index * 17

                    paired_res = run_paired_match(
                        factory_a,
                        factory_b,
                        deck_a=deck,
                        deck_b=deck,
                        seed_a=seed_a,
                        seed_b=seed_b,
                    )

                    h2h_points_a += paired_res["score_a"]
                    h2h_games += 2

                    for g in paired_res["games"]:
                        dur = g["duration_seconds"]
                        steps = g["total_steps"]
                        results[name_a]["total_duration_seconds"] += dur
                        results[name_b]["total_duration_seconds"] += dur
                        results[name_a]["total_steps"] += steps
                        results[name_b]["total_steps"] += steps

                        # Record failure statuses
                        if g["statuses"]["A"] == "INVALID":
                            results[name_a]["invalids"] += 1
                        if g["statuses"]["B"] == "INVALID":
                            results[name_b]["invalids"] += 1

                        if g["winner"] == "A":
                            results[name_a]["wins"] += 1
                            results[name_b]["losses"] += 1
                            results[name_a]["points"] += 1.0
                        elif g["winner"] == "B":
                            results[name_b]["wins"] += 1
                            results[name_a]["losses"] += 1
                            results[name_b]["points"] += 1.0
                        else:
                            results[name_a]["draws"] += 1
                            results[name_b]["draws"] += 1
                            results[name_a]["points"] += 0.5
                            results[name_b]["points"] += 0.5

                        results[name_a]["total_games"] += 1
                        results[name_b]["total_games"] += 1

            win_rate_a = round(h2h_points_a / h2h_games, 4) if h2h_games > 0 else 0.0
            matchup_grid[name_a][name_b] = win_rate_a
            matchup_grid[name_b][name_a] = round(1.0 - win_rate_a, 4)

    # Compute aggregate win rates and Wilson confidence intervals
    leaderboard: list[dict[str, Any]] = []
    for name, stats in results.items():
        total = stats["total_games"]
        pts = stats["points"]
        win_rate = round(pts / total, 4) if total > 0 else 0.0
        ci_lower, ci_upper = compute_wilson_interval(pts, total)
        avg_steps = round(stats["total_steps"] / total, 1) if total > 0 else 0.0
        avg_time = round(stats["total_duration_seconds"] / total, 3) if total > 0 else 0.0

        leaderboard.append(
            {
                "name": name,
                "win_rate": win_rate,
                "confidence_interval_95": [ci_lower, ci_upper],
                "points": pts,
                "total_games": total,
                "wins": stats["wins"],
                "losses": stats["losses"],
                "draws": stats["draws"],
                "invalids": stats["invalids"],
                "avg_steps_per_game": avg_steps,
                "avg_seconds_per_game": avg_time,
            }
        )

    leaderboard.sort(key=lambda item: item["win_rate"], reverse=True)

    return {
        "metadata": {
            "competitors": comp_names,
            "deck_families": list(deck_family_names),
            "pairs_per_matchup": pairs_per_matchup,
            "total_games": sum(s["total_games"] for s in results.values()) // 2,
            "confidence_level": 0.95,
        },
        "leaderboard": leaderboard,
        "matchup_grid": matchup_grid,
    }


def run_pilot_tournament() -> dict[str, Any]:
    """Execute the baseline pilot tournament among Random, First, and Heuristic agents."""
    competitors = {
        "heuristic": lambda deck=None: HeuristicAgent(deck=deck),
        "first": lambda deck=None: FirstAgent(deck=deck),
        "random": lambda deck=None: RandomAgent(seed=42, deck=deck),
    }

    # Pilot across 2 distinct deck families
    pilot_families = ["water-kyogre", "grass-bulbasaur"]
    return run_tournament(
        competitors=competitors,
        deck_family_names=pilot_families,
        pairs_per_matchup=2,  # 2 pairs = 4 games per matchup per deck family
        base_seed=500,
    )
