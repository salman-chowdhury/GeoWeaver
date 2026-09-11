"""CLI provenance audit for `geoweaver rank --sources` (M1.3 stabilization).

When ``--sources`` is supplied, ranking must verify that important source
references from BOTH the catalogue and the run-input document resolve to
registry entries before ranking, failing closed otherwise.
"""

import json
from copy import deepcopy
from pathlib import Path

from geoweaver.cli import main

DEMO_CATALOGUE = Path("data/catalogue/demo_segments.geojson")
RUN_INPUT_TEMPLATE = Path("data/templates/run_input.template.json")
SOURCE_REGISTRY_TEMPLATE = Path("data/templates/source_registry.template.json")


def test_rank_with_sources_valid_registry(demo_catalogue_path: Path, capsys) -> None:
    exit_code = main(
        [
            "rank",
            "--catalogue",
            str(demo_catalogue_path),
            "--inputs",
            str(RUN_INPUT_TEMPLATE),
            "--sources",
            str(SOURCE_REGISTRY_TEMPLATE),
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    report = json.loads(output.out)
    assert report["demonstration_notice"] == ""
    assert len(report["recommendations"]) == 5


def test_rank_with_sources_is_deterministic(demo_catalogue_path: Path, capsys) -> None:
    arguments = [
        "rank",
        "--catalogue",
        str(demo_catalogue_path),
        "--inputs",
        str(RUN_INPUT_TEMPLATE),
        "--sources",
        str(SOURCE_REGISTRY_TEMPLATE),
        "--format",
        "json",
    ]
    assert main(arguments) == 0
    first = capsys.readouterr().out
    assert main(arguments) == 0
    second = capsys.readouterr().out

    assert first == second


def test_rank_with_sources_demo_mode_valid_registry(demo_catalogue_path: Path, capsys) -> None:
    exit_code = main(
        [
            "rank",
            "--catalogue",
            str(demo_catalogue_path),
            "--sources",
            str(SOURCE_REGISTRY_TEMPLATE),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    assert output.out.startswith("# CastNetGPT v0.1 Demonstration Ranking")


def test_rank_with_sources_missing_catalogue_reference(
    demo_document: dict, tmp_path: Path, capsys
) -> None:
    document = deepcopy(demo_document)
    properties = document["features"][0]["properties"]
    properties["source_refs"] = [*properties["source_refs"], "demo://unknown/catalogue-source"]

    catalogue = tmp_path / "catalogue-unknown-ref.geojson"
    catalogue.write_text(json.dumps(document), encoding="utf-8")

    exit_code = main(
        [
            "rank",
            "--catalogue",
            str(catalogue),
            "--inputs",
            str(RUN_INPUT_TEMPLATE),
            "--sources",
            str(SOURCE_REGISTRY_TEMPLATE),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 2
    assert "Catalogue error" in output.err
    assert "catalogue references" in output.err
    assert "demo://unknown/catalogue-source" in output.err
    assert output.out == ""


def test_rank_with_sources_missing_run_input_reference(
    demo_catalogue_path: Path, tmp_path: Path, capsys
) -> None:
    document = json.loads(RUN_INPUT_TEMPLATE.read_text(encoding="utf-8"))
    document["condition"]["tide_source_refs"] = ["demo://unknown/tide-source"]

    inputs = tmp_path / "run-input-unknown-ref.json"
    inputs.write_text(json.dumps(document), encoding="utf-8")

    exit_code = main(
        [
            "rank",
            "--catalogue",
            str(demo_catalogue_path),
            "--inputs",
            str(inputs),
            "--sources",
            str(SOURCE_REGISTRY_TEMPLATE),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 2
    assert "Catalogue error" in output.err
    assert "run inputs reference" in output.err
    assert "demo://unknown/tide-source" in output.err
    assert output.out == ""


def test_rank_with_sources_missing_registry_file(
    demo_catalogue_path: Path, tmp_path: Path, capsys
) -> None:
    exit_code = main(
        [
            "rank",
            "--catalogue",
            str(demo_catalogue_path),
            "--inputs",
            str(RUN_INPUT_TEMPLATE),
            "--sources",
            str(tmp_path / "missing-registry.json"),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 3
    assert "Source registry error" in output.err
    assert output.out == ""


def test_rank_with_sources_malformed_registry(
    demo_catalogue_path: Path, tmp_path: Path, capsys
) -> None:
    bad_registry = tmp_path / "bad-registry.json"
    bad_registry.write_text("{invalid json", encoding="utf-8")

    exit_code = main(
        [
            "rank",
            "--catalogue",
            str(demo_catalogue_path),
            "--inputs",
            str(RUN_INPUT_TEMPLATE),
            "--sources",
            str(bad_registry),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 3
    assert "Source registry error" in output.err
    assert output.out == ""


def test_rank_without_sources_preserves_offline_behaviour(
    demo_catalogue_path: Path, capsys
) -> None:
    # Backwards compatibility: omitting --sources must not audit provenance.
    exit_code = main(
        [
            "rank",
            "--catalogue",
            str(demo_catalogue_path),
            "--inputs",
            str(RUN_INPUT_TEMPLATE),
            "--format",
            "json",
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(output.out)["demonstration_notice"] == ""
