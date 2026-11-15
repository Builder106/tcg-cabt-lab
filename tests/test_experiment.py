"""Tests for controlled experiment runner and ablation report synthesis."""

from pathlib import Path
from typing import Any

import pytest

from tcg_cabt_lab import training
from tcg_cabt_lab.board import BoardAgent
from tcg_cabt_lab.deck import REFERENCE_DECK
from tcg_cabt_lab.experiment import (
    evaluate_checkpoint_on_heldout,
    get_opponent_factory,
    run_controlled_experiment,
)
from tcg_cabt_lab.policy import CompactPolicy, create_checkpoint, save_checkpoint


def test_get_opponent_factory() -> None:
    for name in ["heuristic", "board", "first", "random"]:
        factory = get_opponent_factory(name)
        agent = factory(list(REFERENCE_DECK))
        assert callable(agent)
    assert isinstance(get_opponent_factory("board")(None), BoardAgent)


def test_agreement_reference_is_the_checkpoint_teacher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    built: list[BoardAgent] = []

    class CountingBoard(BoardAgent):
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
            super().__init__(*args, **kwargs)
            built.append(self)

    monkeypatch.setitem(training.TEACHERS, "board", CountingBoard)
    ckpt = create_checkpoint(
        policy=CompactPolicy(input_dim=88, hidden_dim=32, seed=5),
        variant="fixed-opponent-pool",
        seed=5,
        training_steps=10,
        training_deck_families=["water-kyogre"],
        extra_metadata={"teacher": "board"},
    )
    ckpt_path = tmp_path / "board-ckpt.json"
    save_checkpoint(ckpt, ckpt_path)
    evaluate_checkpoint_on_heldout(
        checkpoint_path=ckpt_path,
        test_families=["psychic-mewtwo"],
        opponents=["first"],
        eval_seeds=[11],
    )
    assert len(built) == 2  # one reference per game in the seat-reversed pair


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

    # Per-game records exist without replays, with seats reversed within the pair
    games = eval_res["games"]
    assert [g["policy_seat"] for g in games] == [0, 1]
    assert all(g["result"] in {"win", "loss", "draw"} for g in games)
    points = sum({"win": 1.0, "draw": 0.5, "loss": 0.0}[g["result"]] for g in games)
    assert points == eval_res["total_points"]

    agreement = eval_res["teacher_agreement"]
    assert agreement["decisions"] == sum(g["teacher_agreement"]["decisions"] for g in games)
    assert 0 <= agreement["matches"] <= agreement["decisions"]


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
        baselines=["first"],
        equivalence_margin=0.05,
        bootstrap_resamples=200,
    )

    assert report_file.exists()
    sla = report["seed_level_analysis"]
    assert sla["n_seeds"] == [2, 2]
    assert sla["comparison"] == "diverse-opponent-pool minus fixed-opponent-pool"
    assert sla["equivalent"] in {True, False}
    assert report["baseline_evaluations"]["first"]["total_games"] == 2
    assert len(report["games"]) == 8  # 4 checkpoints x 1 pair
    assert report["schema_version"] == 1
    assert "ablation_results" in report
    ablation = report["ablation_results"]
    assert "summary_by_variant" in ablation
    assert "win_rate_delta_diverse_vs_fixed" in ablation
    assert "delta_confidence_interval_95" in ablation
