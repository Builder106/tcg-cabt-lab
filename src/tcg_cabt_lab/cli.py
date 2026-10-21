"""TCG CABT Lab command-line interface."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from random import Random

from tcg_cabt_lab.baseline import choose_random_action
from tcg_cabt_lab.battle import run_battle
from tcg_cabt_lab.catalog import (
    EXPECTED_CARD_COUNT,
    EXPECTED_CATALOG_SHA256,
    get_catalog_sha256,
    load_card_catalog,
)
from tcg_cabt_lab.deck import REFERENCE_DECK, format_deck_summary, validate_deck
from tcg_cabt_lab.experiment import (
    DEFAULT_TRAINING_SEEDS,
    run_controlled_experiment,
    run_training_suite,
)
from tcg_cabt_lab.features import measure_representation_profile
from tcg_cabt_lab.manifest import SPLIT_ASSIGNMENTS, verify_split_disjointness
from tcg_cabt_lab.policy import create_checkpoint, save_checkpoint
from tcg_cabt_lab.tournament import run_pilot_tournament, run_tournament
from tcg_cabt_lab.training import TRAINING_FAMILIES, train_policy


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    # Subcommand: sample
    sample = subcommands.add_parser("sample", help="sample indices from an observation JSON file")
    sample.add_argument("observation", type=Path, help="path to observation JSON file")
    sample.add_argument("--seed", type=int, default=11, help="random seed (default: 11)")

    # Subcommand: battle
    battle = subcommands.add_parser("battle", help="simulate a complete CABT battle between agents")
    battle.add_argument("--seed-p0", type=int, default=11, help="seed for player 0 (default: 11)")
    battle.add_argument("--seed-p1", type=int, default=22, help="seed for player 1 (default: 22)")
    battle.add_argument(
        "--bo", type=int, default=1, choices=[1, 3], help="best of N matches (default: 1)"
    )
    battle.add_argument(
        "--deck-p0", type=Path, default=None, help="JSON file containing 60 card IDs for player 0"
    )
    battle.add_argument(
        "--deck-p1", type=Path, default=None, help="JSON file containing 60 card IDs for player 1"
    )
    battle.add_argument("--out", type=Path, default=None, help="output path for full JSON game log")

    # Subcommand: catalog
    catalog = subcommands.add_parser(
        "catalog", help="inspect and verify the pinned engine card catalog"
    )
    catalog.add_argument(
        "--export", type=Path, default=None, help="export full card catalog to a JSON file"
    )

    # Subcommand: deck
    deck = subcommands.add_parser("deck", help="validate and inspect a 60-card deck")
    deck.add_argument(
        "deck_file",
        type=Path,
        nargs="?",
        default=None,
        help="path to JSON file containing card IDs (defaults to reference deck)",
    )

    # Subcommand: splits
    splits = subcommands.add_parser("splits", help="inspect and verify deck family split manifests")
    splits.add_argument(
        "--export", type=Path, default=None, help="export verified splits to a JSON file"
    )

    # Subcommand: tournament
    tournament = subcommands.add_parser(
        "tournament", help="run evaluation tournament across agents and deck families"
    )
    tournament.add_argument(
        "--pilot",
        action="store_true",
        help="run standard baseline pilot between heuristic, first, and random",
    )
    tournament.add_argument(
        "--pairs",
        type=int,
        default=1,
        help="pairs of matched games per matchup (default: 1)",
    )
    tournament.add_argument(
        "--out", type=Path, default=None, help="output path for JSON tournament report"
    )

    # Subcommand: profile
    profile = subcommands.add_parser(
        "profile", help="measure compact representation sizes, memory, and inference latency"
    )
    profile.add_argument(
        "--trials", type=int, default=200, help="number of benchmark trials (default: 200)"
    )

    # Subcommand: train
    train = subcommands.add_parser("train", help="train a compact neural policy checkpoint")
    train.add_argument(
        "--variant",
        type=str,
        default="fixed-opponent-pool",
        choices=["fixed-opponent-pool", "diverse-opponent-pool"],
        help="opponent pool variant",
    )
    train.add_argument("--seed", type=int, default=11, help="training seed (default: 11)")
    train.add_argument(
        "--steps", type=int, default=400, help="training gradient steps (default: 400)"
    )
    train.add_argument(
        "--samples", type=int, default=2000, help="decision samples to collect (default: 2000)"
    )
    train.add_argument(
        "--out", type=Path, required=True, help="output path for JSON checkpoint file"
    )

    # Subcommand: experiment
    experiment = subcommands.add_parser(
        "experiment", help="run controlled ML experiment comparing fixed vs diverse opponent pools"
    )
    experiment.add_argument(
        "--checkpoints-dir",
        type=Path,
        default=Path("experiments/checkpoints"),
        help="directory to save/load checkpoints",
    )
    experiment.add_argument(
        "--report-out",
        type=Path,
        default=Path("experiments/ml-experiment-report.json"),
        help="output path for JSON experiment report",
    )
    experiment.add_argument(
        "--train-steps",
        type=int,
        default=400,
        help="training steps per checkpoint (default: 400)",
    )
    experiment.add_argument(
        "--samples-per-run",
        type=int,
        default=2000,
        help="decision samples per checkpoint (default: 2000)",
    )
    experiment.add_argument(
        "--skip-training",
        action="store_true",
        help="evaluate the existing checkpoints instead of training new ones",
    )
    experiment.add_argument(
        "--replays",
        type=Path,
        default=None,
        help="directory for one compact gzipped replay per evaluated game",
    )

    return parser


def _cmd_sample(args: argparse.Namespace) -> int:
    try:
        observation: object = json.loads(args.observation.read_text(encoding="utf-8"))
        action = choose_random_action(observation, Random(args.seed))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Invalid choice request: {error}", file=sys.stderr)
        return 2

    print(json.dumps(action))
    return 0


def _cmd_battle(args: argparse.Namespace) -> int:
    try:
        deck_p0 = None
        if args.deck_p0 is not None:
            deck_p0 = json.loads(args.deck_p0.read_text(encoding="utf-8"))

        deck_p1 = None
        if args.deck_p1 is not None:
            deck_p1 = json.loads(args.deck_p1.read_text(encoding="utf-8"))

        log = run_battle(
            deck_p0=deck_p0,
            deck_p1=deck_p1,
            seed_p0=args.seed_p0,
            seed_p1=args.seed_p1,
            best_of=args.bo,
        )
    except Exception as error:
        print(f"Battle simulation error: {error}", file=sys.stderr)
        return 2

    metadata = log["metadata"]
    outcome = log["outcome"]
    print(
        f"Battle completed in {metadata['total_steps']} steps: "
        f"Winner=Player {outcome['winner']}, "
        f"Rewards={outcome['rewards']}, "
        f"Statuses={outcome['statuses']}"
    )

    if args.out is not None:
        args.out.write_text(json.dumps(log, indent=2), encoding="utf-8")
        print(f"Saved battle log to {args.out}")

    return 0


def _cmd_catalog(args: argparse.Namespace) -> int:
    try:
        cards = load_card_catalog()
        catalog_sha = get_catalog_sha256()
    except Exception as error:
        print(f"Catalog error: {error}", file=sys.stderr)
        return 2

    verified = catalog_sha == EXPECTED_CATALOG_SHA256 and len(cards) == EXPECTED_CARD_COUNT
    print(f"Total cards: {len(cards)} (expected: {EXPECTED_CARD_COUNT})")
    print(f"SHA-256: {catalog_sha}")
    print(f"Verification: {'PASSED' if verified else 'FAILED'}")

    if args.export is not None:
        args.export.write_text(json.dumps(cards, indent=2), encoding="utf-8")
        print(f"Exported card catalog to {args.export}")

    return 0 if verified else 1


def _cmd_deck(args: argparse.Namespace) -> int:
    try:
        if args.deck_file is not None:
            raw_deck = json.loads(args.deck_file.read_text(encoding="utf-8"))
        else:
            raw_deck = list(REFERENCE_DECK)

        valid_deck = validate_deck(raw_deck)
        summary = format_deck_summary(valid_deck)
        print(summary)
    except Exception as error:
        print(f"Deck error: {error}", file=sys.stderr)
        return 2

    return 0


def _cmd_splits(args: argparse.Namespace) -> int:
    try:
        verified = verify_split_disjointness()
    except Exception as error:
        print(f"Split verification error: {error}", file=sys.stderr)
        return 2

    print("Deck Family Splits (Disjointness PASSED):")
    for split_name, families in verified.items():
        print(f"\n  [{split_name.upper()}] ({len(families)} families):")
        for fam in families:
            hash_abbr = fam["deck_sha256"][:16]
            print(f"    - {fam['family']:<20} | {fam['archetype']:<10} | SHA-256: {hash_abbr}...")

    if args.export is not None:
        args.export.write_text(json.dumps(verified, indent=2), encoding="utf-8")
        print(f"\nExported split manifests to {args.export}")

    return 0


def _cmd_tournament(args: argparse.Namespace) -> int:
    try:
        if args.pilot:
            print("Running baseline pilot tournament (Random vs First vs Heuristic)...")
            report = run_pilot_tournament()
        else:
            from tcg_cabt_lab.agent import FirstAgent, HeuristicAgent, RandomAgent

            competitors = {
                "heuristic": lambda deck=None: HeuristicAgent(deck=deck),
                "first": lambda deck=None: FirstAgent(deck=deck),
                "random": lambda deck=None: RandomAgent(seed=42, deck=deck),
            }
            # Use training split families
            families = SPLIT_ASSIGNMENTS["training"]
            print(
                f"Running tournament across {len(families)} training families "
                f"with {args.pairs} pairs/matchup..."
            )
            report = run_tournament(
                competitors=competitors,
                deck_family_names=families,
                pairs_per_matchup=args.pairs,
            )
    except Exception as error:
        print(f"Tournament error: {error}", file=sys.stderr)
        return 2

    leaderboard = report["leaderboard"]
    print("\nTournament Leaderboard:")
    hdr = f"{'Rank':<5} {'Agent':<12} {'Win Rate':<10} {'95% CI':<18} {'Points':<8} {'Games':<6}"
    print(hdr)
    print("-" * 65)
    for rank, entry in enumerate(leaderboard, start=1):
        ci = entry["confidence_interval_95"]
        ci_str = f"[{ci[0]:.3f}, {ci[1]:.3f}]"
        print(
            f"{rank:<5} {entry['name']:<12} {entry['win_rate']:<10.3f} "
            f"{ci_str:<18} {entry['points']:<8.1f} {entry['total_games']:<6}"
        )

    print("\nHead-to-Head Win Rate Grid:")
    grid = report["matchup_grid"]
    names = list(grid.keys())
    header = f"{'':<12} " + " ".join(f"{n:>10}" for n in names)
    print(header)
    for r_name in names:
        row = f"{r_name:<12} " + " ".join(f"{grid[r_name][c_name]:>10.3f}" for c_name in names)
        print(row)

    if args.out is not None:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nSaved tournament report to {args.out}")

    return 0


def _cmd_profile(args: argparse.Namespace) -> int:
    prof = measure_representation_profile(num_trials=args.trials)
    print("Representation Profile & Budget Verification:")
    print(f"  - State dimension: {prof['state_dimension']}")
    print(f"  - Option dimension: {prof['option_dimension']}")
    print(f"  - Total candidate feature dimension: {prof['total_feature_dimension']}")
    print(f"  - Memory footprint (5 options): {prof['matrix_bytes']} bytes (limit: 512 MiB)")
    print(f"  - Mean latency: {prof['mean_latency_ms']:.4f} ms (budget: 50.0 ms)")
    print(f"  - P95 latency: {prof['p95_latency_ms']:.4f} ms")
    print(f"  - Within resource budget: {'PASSED' if prof['within_budget'] else 'FAILED'}")
    return 0 if prof["within_budget"] else 1


def _cmd_train(args: argparse.Namespace) -> int:
    print(f"Training CompactPolicy [{args.variant}] (seed={args.seed}, steps={args.steps})...")
    policy, meta = train_policy(
        variant=args.variant,
        seed=args.seed,
        training_steps=args.steps,
        target_samples=args.samples,
        training_families=TRAINING_FAMILIES,
    )
    ckpt = create_checkpoint(
        policy=policy,
        variant=args.variant,
        seed=args.seed,
        training_steps=args.steps,
        training_deck_families=TRAINING_FAMILIES,
        extra_metadata=meta,
    )
    save_checkpoint(ckpt, args.out)
    print(f"Training completed in {meta['training_duration_seconds']}s")
    print(
        f"  - Samples: {meta['total_samples']} "
        f"(train: {meta['train_samples']}, val: {meta['val_samples']})"
    )
    print(f"  - Val Loss: {meta['initial_val_loss']} -> {meta['final_val_loss']}")
    print(
        f"  - Val Acc: {meta['initial_val_acc'] * 100:.1f}% -> {meta['final_val_acc'] * 100:.1f}%"
    )
    print(f"  - Weights SHA-256: {ckpt['weights_sha256']}")
    print(f"  - Saved checkpoint to: {args.out}")
    return 0


def _cmd_experiment(args: argparse.Namespace) -> int:
    print("Executing Milestone 3 Controlled ML Experiment...")
    if args.skip_training:
        print(f"Step 1: Reusing existing checkpoints in {args.checkpoints_dir}")
    else:
        print(f"Step 1: Training checkpoints in {args.checkpoints_dir}...")
        run_training_suite(
            output_dir=args.checkpoints_dir,
            training_seeds=DEFAULT_TRAINING_SEEDS,
            training_steps=args.train_steps,
            target_samples=args.samples_per_run,
        )
    print("Step 2: Evaluating checkpoints on held-out deck families...")
    report = run_controlled_experiment(
        checkpoints_dir=args.checkpoints_dir,
        output_report_path=args.report_out,
        training_seeds=DEFAULT_TRAINING_SEEDS,
        replay_dir=args.replays,
    )
    ablation = report["ablation_results"]
    summary = ablation["summary_by_variant"]
    print("\nExperiment Summary across 3 independent training seeds:")
    for var, s in summary.items():
        ci = s["pooled_wilson_ci_95"]
        print(
            f"  - {var:<24}: Mean Win Rate = {s['mean_win_rate'] * 100:.2f}% "
            f"(Pooled: {s['pooled_win_rate'] * 100:.2f}% [{ci[0] * 100:.2f}%, {ci[1] * 100:.2f}%])"
        )
    delta_pct = ablation["win_rate_delta_diverse_vs_fixed"] * 100
    print(f"\nWin Rate Delta (Diverse - Fixed): {delta_pct:+.2f}%")
    ci_delta = ablation["delta_confidence_interval_95"]
    print(f"95% CI on Delta: [{ci_delta[0] * 100:+.2f}%, {ci_delta[1] * 100:+.2f}%]")
    if args.replays is not None:
        print(f"Saved {len(report.get('games', []))} game replays to: {args.replays}")
    print(f"Saved complete experiment report to: {args.report_out}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "sample":
        return _cmd_sample(args)
    if args.command == "battle":
        return _cmd_battle(args)
    if args.command == "catalog":
        return _cmd_catalog(args)
    if args.command == "deck":
        return _cmd_deck(args)
    if args.command == "splits":
        return _cmd_splits(args)
    if args.command == "tournament":
        return _cmd_tournament(args)
    if args.command == "profile":
        return _cmd_profile(args)
    if args.command == "train":
        return _cmd_train(args)
    if args.command == "experiment":
        return _cmd_experiment(args)

    return 1
