"""Tests for the M1.4 real-candidate curation workflow."""

import json
from copy import deepcopy
from pathlib import Path

from geoweaver.cli import main
from geoweaver.data.loader import load_catalogue
from geoweaver.data.sources import (
    collect_catalogue_source_refs,
    find_missing_source_refs,
    load_source_registry,
)
from geoweaver.domain.enums import VerificationState

CURATED_CATALOGUE = Path("data/templates/curated_candidate.template.geojson")
CURATION_REGISTRY = Path("data/templates/curation_registry.template.json")
DEMO_REGISTRY = Path("data/templates/source_registry.template.json")


def test_curated_template_loads_as_remote_reviewed() -> None:
    segments = load_catalogue(CURATED_CATALOGUE)

    assert len(segments) == 1
    segment = segments[0]
    assert segment.segment_id == "curated-example-001"
    assert segment.verification_status is VerificationState.REMOTE_REVIEWED
    # Unknowns stay explicit: nullable parking/toilets model unverified facilities.
    assert segment.access.parking_available is None
    assert segment.access.toilets is None


def test_curated_template_provenance_resolves() -> None:
    segments = load_catalogue(CURATED_CATALOGUE)
    registry = load_source_registry(CURATION_REGISTRY)
    references = collect_catalogue_source_refs(segments)

    assert len(references) == 4
    assert find_missing_source_refs(registry, references) == ()


def test_curated_template_uses_separate_provenance() -> None:
    segments = load_catalogue(CURATED_CATALOGUE)
    demo_registry = load_source_registry(DEMO_REGISTRY)
    references = collect_catalogue_source_refs(segments)

    # Curated proposals must not silently reuse demo provenance.
    assert find_missing_source_refs(demo_registry, references) == references


def test_validate_catalogue_with_sources_passes(
    capsys,
) -> None:
    exit_code = main(
        [
            "validate-catalogue",
            "--catalogue",
            str(CURATED_CATALOGUE),
            "--sources",
            str(CURATION_REGISTRY),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 0
    assert "Catalogue valid: 1 segment(s)" in output.out
    assert "Provenance audit passed: 4 source reference(s)" in output.out


def test_validate_catalogue_without_sources_still_passes(
    capsys,
) -> None:
    exit_code = main(["validate-catalogue", "--catalogue", str(CURATED_CATALOGUE)])
    output = capsys.readouterr()

    assert exit_code == 0
    assert "Catalogue valid: 1 segment(s)" in output.out


def test_validate_catalogue_with_wrong_registry_reports_missing(
    capsys,
) -> None:
    exit_code = main(
        [
            "validate-catalogue",
            "--catalogue",
            str(CURATED_CATALOGUE),
            "--sources",
            str(DEMO_REGISTRY),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 2
    assert "Catalogue error" in output.err
    assert "missing from registry" in output.err
    assert "curation-example://" in output.err


def test_validate_catalogue_with_missing_registry_file(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "validate-catalogue",
            "--catalogue",
            str(CURATED_CATALOGUE),
            "--sources",
            str(tmp_path / "missing.json"),
        ]
    )
    output = capsys.readouterr()

    assert exit_code == 3
    assert "Source registry error" in output.err


def test_second_contributor_can_copy_template_and_revalidate(tmp_path: Path, capsys) -> None:
    document = json.loads(CURATED_CATALOGUE.read_text(encoding="utf-8"))
    proposed = deepcopy(document)
    properties = proposed["features"][0]["properties"]
    properties["segment_id"] = "second-contributor-example-002"
    properties["name"] = "Second Contributor Example 002 (synthetic)"
    catalogue = tmp_path / "candidate.geojson"
    catalogue.write_text(json.dumps(proposed), encoding="utf-8")

    exit_code = main(["validate-catalogue", "--catalogue", str(catalogue)])
    output = capsys.readouterr()

    assert exit_code == 0
    assert "Catalogue valid: 1 segment(s)" in output.out
