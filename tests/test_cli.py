import json
from pathlib import Path

import pytest

from tcg_cabt_lab.cli import main


def test_cli_sample_outputs_an_action(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request = tmp_path / "selection.json"
    request.write_text(
        json.dumps({"select": {"option": [{}], "minCount": 1, "maxCount": 1}}),
        encoding="utf-8",
    )
    assert main(["sample", str(request), "--seed", "11"]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out) == [0]
    assert output.err == ""


@pytest.mark.parametrize("contents", ["not json", '{"select": null}'])
def test_cli_sample_rejects_bad_input(
    contents: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = tmp_path / "selection.json"
    request.write_text(contents, encoding="utf-8")
    assert main(["sample", str(request)]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.startswith("Invalid choice request:")


def test_cli_sample_reports_missing_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["sample", str(tmp_path / "missing.json")]) == 2
    assert capsys.readouterr().err.startswith("Invalid choice request:")


def test_cli_catalog_verification(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["catalog"]) == 0
    output = capsys.readouterr()
    assert "Verification: PASSED" in output.out
    assert "Total cards: 1431" in output.out


def test_cli_deck_inspection(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["deck"]) == 0
    output = capsys.readouterr()
    assert "Deck (60 cards" in output.out
    assert "Basic {W} Energy" in output.out


def test_cli_deck_custom_file_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad_deck = tmp_path / "bad_deck.json"
    bad_deck.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert main(["deck", str(bad_deck)]) == 2
    output = capsys.readouterr()
    assert "Deck error: Deck must contain exactly 60 cards" in output.err


def test_cli_battle_simulation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_log = tmp_path / "battle_log.json"
    assert (
        main(
            [
                "battle",
                "--seed-p0",
                "11",
                "--seed-p1",
                "22",
                "--bo",
                "1",
                "--out",
                str(out_log),
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert "Battle completed in" in output.out
    assert out_log.exists()
    data = json.loads(out_log.read_text(encoding="utf-8"))
    assert data["metadata"]["engine"] == "cabt"
    assert data["metadata"]["total_steps"] > 0


def test_cli_splits_verification(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_splits = tmp_path / "splits.json"
    assert main(["splits", "--export", str(out_splits)]) == 0
    output = capsys.readouterr()
    assert "Disjointness PASSED" in output.out
    assert "[TRAINING]" in output.out
    assert out_splits.exists()


def test_cli_tournament_execution(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_report = tmp_path / "tournament_report.json"
    assert main(["tournament", "--pairs", "1", "--out", str(out_report)]) == 0
    output = capsys.readouterr()
    assert "Tournament Leaderboard:" in output.out
    assert "Head-to-Head Win Rate Grid:" in output.out
    assert out_report.exists()
    data = json.loads(out_report.read_text(encoding="utf-8"))
    assert len(data["leaderboard"]) == 3


def test_cli_profile_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["profile", "--trials", "20"]) == 0
    output = capsys.readouterr()
    assert "Representation Profile & Budget Verification:" in output.out
    assert "Total candidate feature dimension: 88" in output.out
    assert "Within resource budget: PASSED" in output.out


def test_cli_train_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out_ckpt = tmp_path / "ckpt.json"
    assert (
        main(
            [
                "train",
                "--variant",
                "fixed-opponent-pool",
                "--seed",
                "11",
                "--steps",
                "10",
                "--samples",
                "30",
                "--out",
                str(out_ckpt),
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert "Training completed in" in output.out
    assert out_ckpt.exists()


def test_cli_experiment_refuses_unfrozen_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"status": "draft"}), encoding="utf-8")
    assert main(["experiment", "--config", str(plan)]) == 2
    assert "not frozen" in capsys.readouterr().err


def test_cli_analyze_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def evaluation(wins: float) -> dict[str, object]:
        return {
            "family_breakdown": {
                "psychic-mewtwo": {"wins": wins, "total_games": 10},
                "colorless-snorlax": {"wins": wins, "total_games": 10},
            }
        }

    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "checkpoint_evaluations": {
                    "fixed-opponent-pool": [evaluation(5), evaluation(6)],
                    "diverse-opponent-pool": [evaluation(5), evaluation(6)],
                }
            }
        ),
        encoding="utf-8",
    )
    assert main(["analyze", str(report), "--margin", "0.05", "--resamples", "500"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["comparison"] == "diverse-opponent-pool minus fixed-opponent-pool"
    assert result["delta"] == 0.0
    assert result["means"] == [0.55, 0.55]


def test_cli_experiment_runs_frozen_plan(tmp_path: Path) -> None:
    plan = json.loads(Path("experiments/opponent-pool-scaled.json").read_text(encoding="utf-8"))
    plan["status"] = "frozen"
    plan["design"].update(
        training_seeds=[1, 2],
        training_steps=5,
        samples_per_checkpoint=20,
        training_families=["water-kyogre"],
        test_families=["psychic-mewtwo"],
        opponents=["first"],
        eval_seeds=[11],
        pairs_per_seed=1,
        baselines=["first"],
    )
    plan["analysis"]["bootstrap_resamples"] = 100
    plan["outputs"] = {
        "checkpoints_dir": str(tmp_path / "checkpoints"),
        "report": str(tmp_path / "report.json"),
        "replays": None,
    }
    config = tmp_path / "plan.json"
    config.write_text(json.dumps(plan), encoding="utf-8")

    assert main(["experiment", "--config", str(config)]) == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["study_configuration"]["training_seeds"] == [1, 2]
    assert report["seed_level_analysis"]["equivalence_margin"] == 0.05
    assert report["seed_level_analysis"]["bootstrap"] == {"resamples": 100, "seed": 20261114}
    assert set(report["baseline_evaluations"]) == {"first"}
    assert len(list((tmp_path / "checkpoints").glob("*.json"))) == 4


def test_cli_experiment_trains_from_play(tmp_path: Path) -> None:
    plan = json.loads(Path("experiments/opponent-pool-scaled.json").read_text(encoding="utf-8"))
    plan["status"] = "frozen"
    plan["design"].update(
        training_seeds=[1, 2],
        rl={"games": 2, "games_per_update": 2, "learning_rate": 0.003},
        workers=1,
        training_families=["water-kyogre"],
        test_families=["psychic-mewtwo"],
        opponents=["first"],
        eval_seeds=[11],
        pairs_per_seed=1,
        baselines=[],
    )
    plan["analysis"]["bootstrap_resamples"] = 100
    plan["outputs"] = {
        "checkpoints_dir": str(tmp_path / "checkpoints"),
        "report": str(tmp_path / "report.json"),
        "replays": None,
    }
    config = tmp_path / "plan.json"
    config.write_text(json.dumps(plan), encoding="utf-8")

    assert main(["experiment", "--config", str(config)]) == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    study = report["study_configuration"]
    assert study["learners"] == ["reinforce"]
    assert study["teachers"] == []
    summary = report["ablation_results"]["summary_by_variant"]
    assert all("teacher_agreement_by_seed" not in s for s in summary.values())
