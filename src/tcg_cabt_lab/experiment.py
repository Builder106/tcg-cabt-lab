"""Controlled ML experiment runner, held-out evaluation, and ablation report."""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from tcg_cabt_lab.agent import FirstAgent, HeuristicAgent, RandomAgent
from tcg_cabt_lab.catalog import EXPECTED_ATTACK_SHA256, EXPECTED_CATALOG_SHA256
from tcg_cabt_lab.manifest import get_deck_family
from tcg_cabt_lab.policy import (
    PolicyAgent,
    create_checkpoint,
    load_checkpoint,
    save_checkpoint,
)
from tcg_cabt_lab.tournament import compute_wilson_interval, run_paired_match
from tcg_cabt_lab.training import (
    FINAL_TEST_FAMILIES,
    TRAINING_FAMILIES,
    train_policy,
)

DEFAULT_TRAINING_SEEDS = [11, 29, 47]
DEFAULT_EVAL_SEEDS = [11, 29, 47, 101, 202]
DEFAULT_OPPONENT_TYPES = ["heuristic", "first", "random"]


def get_opponent_factory(opponent_type: str) -> Any:
    """Return an agent factory for the specified baseline opponent type."""
    if opponent_type == "heuristic":
        return lambda deck: HeuristicAgent(deck=deck)
    elif opponent_type == "first":
        return lambda deck: FirstAgent(deck=deck)
    elif opponent_type == "random":
        return lambda deck: RandomAgent(seed=42, deck=deck)
    raise ValueError(f"Unknown opponent type: {opponent_type}")


def run_training_suite(
    output_dir: Path | str,
    training_seeds: Sequence[int] = DEFAULT_TRAINING_SEEDS,
    variants: Sequence[str] = ("fixed-opponent-pool", "diverse-opponent-pool"),
    training_steps: int = 400,
    target_samples: int = 2000,
) -> dict[str, Any]:
    """Train checkpoints across variants and seeds, saving them to output_dir."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    suite_results: dict[str, Any] = {}

    for var in variants:
        suite_results[var] = {}
        for s in training_seeds:
            policy, meta = train_policy(
                variant=var,
                seed=s,
                training_steps=training_steps,
                target_samples=target_samples,
                training_families=TRAINING_FAMILIES,
            )
            ckpt = create_checkpoint(
                policy=policy,
                variant=var,
                seed=s,
                training_steps=training_steps,
                training_deck_families=TRAINING_FAMILIES,
                extra_metadata=meta,
            )
            ckpt_filename = f"{var}-seed-{s}.json"
            ckpt_path = out_path / ckpt_filename
            save_checkpoint(ckpt, ckpt_path)

            suite_results[var][str(s)] = {
                "checkpoint_path": str(ckpt_path),
                "weights_sha256": ckpt["weights_sha256"],
                "training_metadata": meta,
            }

    return suite_results


def evaluate_checkpoint_on_heldout(
    checkpoint_path: Path | str,
    test_families: Sequence[str] = FINAL_TEST_FAMILIES,
    opponents: Sequence[str] = DEFAULT_OPPONENT_TYPES,
    eval_seeds: Sequence[int] = DEFAULT_EVAL_SEEDS,
    pairs_per_seed: int = 1,
) -> dict[str, Any]:
    """Evaluate a policy checkpoint on frozen held-out deck families.

    Runs matched pairs with reversed seats against each opponent type.
    """
    ckpt_dict = load_checkpoint(checkpoint_path)

    def policy_factory(deck: Sequence[int] | None = None) -> PolicyAgent:
        return PolicyAgent(ckpt_dict, deck=deck)

    matchup_records: list[dict[str, Any]] = []
    family_stats: dict[str, dict[str, Any]] = {}
    opponent_stats: dict[str, dict[str, float]] = {
        opp: {"wins": 0, "draws": 0, "total": 0} for opp in opponents
    }

    total_wins = 0.0
    total_games = 0

    for fam in test_families:
        deck = get_deck_family(fam)["deck"]
        fam_wins = 0.0
        fam_games = 0

        for opp_name in opponents:
            opp_factory = get_opponent_factory(opp_name)

            for seed_val in eval_seeds:
                for p_idx in range(pairs_per_seed):
                    pair_result = run_paired_match(
                        agent_a_factory=policy_factory,
                        agent_b_factory=opp_factory,
                        deck_a=deck,
                        deck_b=deck,
                        seed_a=seed_val + p_idx * 1000,
                        seed_b=seed_val + 500 + p_idx * 1000,
                        best_of=1,
                    )

                    pts = float(pair_result["score_a"])
                    tot = len(pair_result["games"])
                    fam_wins += pts
                    fam_games += tot
                    opponent_stats[opp_name]["wins"] += pts
                    opponent_stats[opp_name]["total"] += tot
                    total_wins += pts
                    total_games += tot

                    matchup_records.append(
                        {
                            "family": fam,
                            "opponent": opp_name,
                            "seed": seed_val,
                            "pair_index": p_idx,
                            "agent_a_points": pts,
                            "total_games": tot,
                            "outcomes": [g["winner"] for g in pair_result["games"]],
                        }
                    )

        fam_rate = (fam_wins / fam_games) if fam_games > 0 else 0.0
        fam_ci = compute_wilson_interval(fam_wins, fam_games, confidence=0.95)
        family_stats[fam] = {
            "wins": fam_wins,
            "total_games": fam_games,
            "win_rate": round(fam_rate, 4),
            "wilson_ci_95": [fam_ci[0], fam_ci[1]],
        }

    overall_win_rate = (total_wins / total_games) if total_games > 0 else 0.0
    overall_ci = compute_wilson_interval(total_wins, total_games, confidence=0.95)

    # Summarize per opponent type
    opp_summary: dict[str, dict[str, Any]] = {}
    for opp_name, stats in opponent_stats.items():
        o_tot = int(stats["total"])
        o_win = float(stats["wins"])
        o_rate = (o_win / o_tot) if o_tot > 0 else 0.0
        o_ci = compute_wilson_interval(o_win, o_tot, confidence=0.95)
        opp_summary[opp_name] = {
            "wins": o_win,
            "total_games": o_tot,
            "win_rate": round(o_rate, 4),
            "wilson_ci_95": [o_ci[0], o_ci[1]],
        }

    return {
        "checkpoint_path": str(checkpoint_path),
        "weights_sha256": ckpt_dict["weights_sha256"],
        "provenance": ckpt_dict.get("provenance", {}),
        "total_games": total_games,
        "total_points": total_wins,
        "overall_win_rate": round(overall_win_rate, 4),
        "overall_wilson_ci_95": [overall_ci[0], overall_ci[1]],
        "family_breakdown": family_stats,
        "opponent_breakdown": opp_summary,
        "matchup_records_count": len(matchup_records),
    }


def run_controlled_experiment(
    checkpoints_dir: Path | str,
    output_report_path: Path | str,
    training_seeds: Sequence[int] = DEFAULT_TRAINING_SEEDS,
    variants: Sequence[str] = ("fixed-opponent-pool", "diverse-opponent-pool"),
    test_families: Sequence[str] = FINAL_TEST_FAMILIES,
    opponents: Sequence[str] = DEFAULT_OPPONENT_TYPES,
    eval_seeds: Sequence[int] = DEFAULT_EVAL_SEEDS,
) -> dict[str, Any]:
    """Execute evaluation for all checkpoints across variants and synthesize comparative report."""
    ckpt_dir = Path(checkpoints_dir)
    report_file = Path(output_report_path)

    variant_evals: dict[str, list[dict[str, Any]]] = {var: [] for var in variants}

    for var in variants:
        for s in training_seeds:
            ckpt_path = ckpt_dir / f"{var}-seed-{s}.json"
            eval_res = evaluate_checkpoint_on_heldout(
                checkpoint_path=ckpt_path,
                test_families=test_families,
                opponents=opponents,
                eval_seeds=eval_seeds,
            )
            variant_evals[var].append(eval_res)

    # Comparative analysis and aggregation across seeds
    summary_by_variant: dict[str, Any] = {}
    for var, evals in variant_evals.items():
        rates = [e["overall_win_rate"] for e in evals]
        tot_points = sum(e["total_points"] for e in evals)
        tot_games = sum(e["total_games"] for e in evals)
        pooled_ci = compute_wilson_interval(tot_points, tot_games, confidence=0.95)

        # Average win rate across deck families
        fam_avgs: dict[str, float] = {}
        for fam in test_families:
            fam_rates = [e["family_breakdown"][fam]["win_rate"] for e in evals]
            fam_avgs[fam] = round(float(np.mean(fam_rates)), 4)

        # Average win rate across opponent types
        opp_avgs: dict[str, float] = {}
        for opp in opponents:
            opp_rates = [e["opponent_breakdown"][opp]["win_rate"] for e in evals]
            opp_avgs[opp] = round(float(np.mean(opp_rates)), 4)

        summary_by_variant[var] = {
            "num_seeds": len(evals),
            "seed_win_rates": rates,
            "mean_win_rate": round(float(np.mean(rates)), 4),
            "std_win_rate": round(float(np.std(rates)), 4),
            "pooled_points": tot_points,
            "pooled_games": tot_games,
            "pooled_win_rate": round(tot_points / tot_games, 4) if tot_games > 0 else 0.0,
            "pooled_wilson_ci_95": [pooled_ci[0], pooled_ci[1]],
            "deck_family_means": fam_avgs,
            "opponent_means": opp_avgs,
        }

    # Hypothesis test delta: diverse - fixed
    fixed_mean = summary_by_variant.get("fixed-opponent-pool", {}).get("mean_win_rate", 0.0)
    diverse_mean = summary_by_variant.get("diverse-opponent-pool", {}).get("mean_win_rate", 0.0)
    delta_mean = round(diverse_mean - fixed_mean, 4)

    fixed_pooled_points = float(
        summary_by_variant.get("fixed-opponent-pool", {}).get("pooled_points", 0.0)
    )
    fixed_pooled_games = int(
        summary_by_variant.get("fixed-opponent-pool", {}).get("pooled_games", 1)
    )
    diverse_pooled_points = float(
        summary_by_variant.get("diverse-opponent-pool", {}).get("pooled_points", 0.0)
    )
    diverse_pooled_games = int(
        summary_by_variant.get("diverse-opponent-pool", {}).get("pooled_games", 1)
    )

    # Standard error of difference between two independent proportions
    p1 = diverse_pooled_points / diverse_pooled_games
    p2 = fixed_pooled_points / fixed_pooled_games
    var1 = p1 * (1.0 - p1) / diverse_pooled_games
    var2 = p2 * (1.0 - p2) / fixed_pooled_games
    se_diff = float(np.sqrt(var1 + var2))
    delta_ci_95 = [round(delta_mean - 1.96 * se_diff, 4), round(delta_mean + 1.96 * se_diff, 4)]

    report = {
        "schema_version": 1,
        "completed_at": datetime.now(UTC).isoformat(),
        "hypothesis": (
            "Does training against a diverse opponent pool improve a compact "
            "CABT policy's win rate on held-out deck families?"
        ),
        "environment": {
            "card_catalog_sha256": EXPECTED_CATALOG_SHA256,
            "attack_catalog_sha256": EXPECTED_ATTACK_SHA256,
        },
        "study_configuration": {
            "training_variants": list(variants),
            "training_seeds": list(training_seeds),
            "training_deck_families": list(TRAINING_FAMILIES),
            "heldout_test_deck_families": list(test_families),
            "eval_opponents": list(opponents),
            "eval_seeds": list(eval_seeds),
            "pairing": "matched deck pair and seed with reversed player assignments",
            "confidence_level": 0.95,
        },
        "ablation_results": {
            "summary_by_variant": summary_by_variant,
            "win_rate_delta_diverse_vs_fixed": delta_mean,
            "delta_confidence_interval_95": delta_ci_95,
            "statistical_significance": delta_ci_95[0] > 0.0 or delta_ci_95[1] < 0.0,
        },
        "checkpoint_evaluations": variant_evals,
    }

    report_file.parent.mkdir(parents=True, exist_ok=True)
    with report_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report
