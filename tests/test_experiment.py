"""Tests for controlled experiment runner and ablation report synthesis."""

from pathlib import Path

from tcg_cabt_lab.deck import REFERENCE_DECK
from tcg_cabt_lab.experiment import (
    evaluate_checkpoint_on_heldout,
    get_opponent_factory,
    run_controlled_experiment,
)
from tcg_cabt_lab.policy import CompactPolicy, create_checkpoint, save_checkpoint


def test_get_opponent_factory() -> None:
    for name in ["heuristic", "first", "random"]:
        factory = get_opponent_factory(name)
        agent = factory(list(REFERENCE_DECK))
        assert callable(agent)


def test_evaluate_checkpoint_heldout(tmp_path: Path) -> None:
    policy = CompactPolicy(input_dim=88, hidden_dim=32, seed=11)
    ckpt = create_checkpoint(
        policy=policy,
        variant="fixed-opponent-pool",
        seed=11,
        training_steps=10,
        training_deck_families=["water-kyogre"],
    )
    ckpt_path = tmp_path / "test-eval-ckpt.json"
    save_checkpoint(ckpt, ckpt_path)

    # Fast evaluation with 1 held-out family and 1 opponent
    eval_res = evaluate_checkpoint_on_heldout(
        checkpoint_path=ckpt_path,
        test_families=["psychic-mewtwo"],
        opponents=["first"],
        eval_seeds=[11],
        pairs_per_seed=1,
    )

    assert eval_res["total_games"] == 2  # 1 matched pair = 2 games
    assert 0.0 <= eval_res["overall_win_rate"] <= 1.0
    assert "psychic-mewtwo" in eval_res["family_breakdown"]
    assert "first" in eval_res["opponent_breakdown"]


def test_run_controlled_experiment_report(tmp_path: Path) -> None:
    ckpt_dir = tmp_path / "checkpoints"
    ckpt_dir.mkdir()
    report_file = tmp_path / "report.json"

    # Create dummy checkpoints for two variants across 2 seeds
    variants = ["fixed-opponent-pool", "diverse-opponent-pool"]
    seeds = [11, 29]
    for var in variants:
        for s in seeds:
            pol = CompactPolicy(input_dim=88, hidden_dim=32, seed=s)
            ckpt = create_checkpoint(
                policy=pol,
                variant=var,
                seed=s,
                training_steps=10,
                training_deck_families=["water-kyogre"],
            )
            save_checkpoint(ckpt, ckpt_dir / f"{var}-seed-{s}.json")

    report = run_controlled_experiment(
        checkpoints_dir=ckpt_dir,
        output_report_path=report_file,
        training_seeds=seeds,
        variants=variants,
        test_families=["psychic-mewtwo"],
        opponents=["first"],
        eval_seeds=[11],
    )

    assert report_file.exists()
    assert report["schema_version"] == 1
    assert "ablation_results" in report
    ablation = report["ablation_results"]
    assert "summary_by_variant" in ablation
    assert "win_rate_delta_diverse_vs_fixed" in ablation
    assert "delta_confidence_interval_95" in ablation
