import json
from pathlib import Path

import pytest

from tcg_cabt_lab.cli import main


def test_cli_outputs_an_action(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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
def test_cli_rejects_bad_input(
    contents: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = tmp_path / "selection.json"
    request.write_text(contents, encoding="utf-8")
    assert main(["sample", str(request)]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.startswith("Invalid choice request:")


def test_cli_reports_missing_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["sample", str(tmp_path / "missing.json")]) == 2
    assert capsys.readouterr().err.startswith("Invalid choice request:")
