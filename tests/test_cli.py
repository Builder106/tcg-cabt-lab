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
