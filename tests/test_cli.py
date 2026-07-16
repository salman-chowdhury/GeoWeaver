"""Basic command-line behavior tests."""

import json
from pathlib import Path

import pytest

from geoweaver.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_TRIP = PROJECT_ROOT / "data" / "trips" / "demo_trip.json"
DEMO_CONDITIONS = PROJECT_ROOT / "data" / "conditions" / "demo_conditions.json"
DEMO_TRAVEL = PROJECT_ROOT / "data" / "travel" / "demo_travel.json"


def _rank_arguments(catalogue: Path, *, report_format: str = "markdown") -> list[str]:
    return [
        "rank",
        "--catalogue",
        str(catalogue),
        "--trip",
        str(DEMO_TRIP),
        "--conditions",
        str(DEMO_CONDITIONS),
        "--travel",
        str(DEMO_TRAVEL),
        "--format",
        report_format,
    ]


def test_validate_catalogue_command(
    demo_catalogue_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["validate-catalogue", "--catalogue", str(demo_catalogue_path)])
    output = capsys.readouterr()

    assert exit_code == 0
    assert "Catalogue valid: 5 segment(s)" in output.out


def test_rank_json_command(demo_catalogue_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(_rank_arguments(demo_catalogue_path, report_format="json"))
    output = capsys.readouterr()
    report = json.loads(output.out)

    assert exit_code == 0
    assert report["application"] == "CastNetGPT v0.1"
    assert report["condition_snapshot"]["inferred"] is False
    assert report["trip_request"]["origin_label"] == "Fictional Demo Origin"
    assert report["travel_estimates"][0]["retrieved_at"]


def test_rank_markdown_is_default(
    demo_catalogue_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["demo", "--catalogue", str(demo_catalogue_path)])
    output = capsys.readouterr()

    assert exit_code == 0
    assert output.out.startswith("# CastNetGPT v0.1 Demonstration Ranking")


def test_demo_uses_packaged_inputs_outside_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["demo", "--format", "json"])
    output = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(output.out)["input_classification"] == "synthetic_demo"
    assert output.err == ""


def test_invalid_catalogue_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = tmp_path / "broken.geojson"
    broken.write_text("{}", encoding="utf-8")

    exit_code = main(["validate-catalogue", "--catalogue", str(broken)])
    output = capsys.readouterr()

    assert exit_code == 2
    assert "Catalogue error" in output.err


def test_demo_rejects_condition_scope_that_references_catalogue_subset(
    demo_document: dict[str, object],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    document = dict(demo_document)
    document["features"] = list(document["features"])[:1]
    catalogue = tmp_path / "demo-subset.geojson"
    catalogue.write_text(json.dumps(document), encoding="utf-8")

    exit_code = main(["demo", "--catalogue", str(catalogue), "--format", "json"])
    output = capsys.readouterr()

    assert exit_code == 2
    assert output.out == ""
    assert "unknown segment IDs" in output.err


def test_missing_trip_file_returns_controlled_exit(
    demo_catalogue_path: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = _rank_arguments(demo_catalogue_path, report_format="json")
    arguments[arguments.index(str(DEMO_TRIP))] = str(tmp_path / "missing-trip.json")

    exit_code = main(arguments)
    output = capsys.readouterr()

    assert exit_code == 2
    assert output.out == ""
    assert "Input error" in output.err
    assert "could not read trip file" in output.err


def test_missing_rank_arguments_return_usage_exit(
    demo_catalogue_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["rank", "--catalogue", str(demo_catalogue_path)])

    assert exit_code == 2
    assert "--trip" in capsys.readouterr().err


def test_cli_normalizes_invalid_utf8(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    catalogue = tmp_path / "invalid-utf8.geojson"
    catalogue.write_bytes(b"\xff\xfe")

    exit_code = main(["validate-catalogue", "--catalogue", str(catalogue)])
    output = capsys.readouterr()

    assert exit_code == 2
    assert "Catalogue error" in output.err
    assert "UTF-8" in output.err


def test_cli_converts_ranking_errors_to_controlled_exit(
    demo_catalogue_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_ranking(*args: object, **kwargs: object) -> None:
        raise ValueError("synthetic ranking failure")

    monkeypatch.setattr("geoweaver.cli.rank_trip", fail_ranking)

    exit_code = main(_rank_arguments(demo_catalogue_path))
    output = capsys.readouterr()

    assert exit_code == 3
    assert output.out == ""
    assert "Ranking error: synthetic ranking failure" in output.err
