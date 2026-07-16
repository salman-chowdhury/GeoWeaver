"""Basic command-line behavior tests."""

import json
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest

from geoweaver.cli import main


def test_validate_catalogue_command(
    demo_catalogue_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["validate-catalogue", "--catalogue", str(demo_catalogue_path)])
    output = capsys.readouterr()

    assert exit_code == 0
    assert "Catalogue valid: 5 segment(s)" in output.out
    assert "synthetic" in output.out.lower()


def test_rank_json_command(demo_catalogue_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rank", "--catalogue", str(demo_catalogue_path), "--format", "json"])
    output = capsys.readouterr()
    report = json.loads(output.out)

    assert exit_code == 0
    assert report["application"] == "CastNetGPT v0.1"
    assert report["condition_snapshot"]["inferred"] is True


def test_rank_markdown_is_default(
    demo_catalogue_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["rank", "--catalogue", str(demo_catalogue_path)])
    output = capsys.readouterr()

    assert exit_code == 0
    assert output.out.startswith("# CastNetGPT v0.1 Demonstration Ranking")


def test_invalid_catalogue_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = tmp_path / "broken.geojson"
    broken.write_text("{}", encoding="utf-8")

    exit_code = main(["validate-catalogue", "--catalogue", str(broken)])
    output = capsys.readouterr()

    assert exit_code == 2
    assert "Catalogue error" in output.err


def test_rank_filters_demo_travel_estimates_to_present_segments(
    demo_document: dict[str, object],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    document = deepcopy(demo_document)
    features = cast("list[object]", document["features"])
    document["features"] = features[:1]
    catalogue = tmp_path / "demo-subset.geojson"
    catalogue.write_text(json.dumps(document), encoding="utf-8")

    exit_code = main(["rank", "--catalogue", str(catalogue), "--format", "json"])
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [item["segment_id"] for item in report["travel_estimates"]] == ["demo-alpha-gutter"]


def test_rank_accepts_valid_non_demo_catalogue_without_inventing_inputs(
    demo_document: dict[str, object],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    document = deepcopy(demo_document)
    features = cast("list[dict[str, object]]", document["features"])
    document["features"] = features[:1]
    properties = cast("dict[str, object]", features[0]["properties"])
    properties["segment_id"] = "custom-valid-segment"
    catalogue = tmp_path / "custom.geojson"
    catalogue.write_text(json.dumps(document), encoding="utf-8")

    exit_code = main(["rank", "--catalogue", str(catalogue), "--format", "json"])
    report = json.loads(capsys.readouterr().out)
    recommendation = report["recommendations"][0]

    assert exit_code == 0
    assert report["travel_estimates"] == []
    assert recommendation["segment_id"] == "custom-valid-segment"
    assert recommendation["eligible"] is False
    assert {failure["gate"] for failure in recommendation["hard_gate_failures"]} >= {
        "severe_weather",
        "tide_condition",
        "safe_footing",
        "usable_daylight",
        "travel_time",
    }


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

    monkeypatch.setattr("geoweaver.cli.rank_segments", fail_ranking)

    exit_code = main(["rank", "--catalogue", str(demo_catalogue_path)])
    output = capsys.readouterr()

    assert exit_code == 3
    assert output.out == ""
    assert "Ranking error: synthetic ranking failure" in output.err
