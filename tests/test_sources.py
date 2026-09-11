"""Tests for the provenance/source registry contract."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from geoweaver.data import (
    SourceRegistryValidationError,
    collect_catalogue_source_refs,
    collect_run_input_source_refs,
    find_missing_source_refs,
    index_sources_by_id,
    load_run_input,
    load_source_registry,
    validate_source_registry_document,
)
from geoweaver.data.loader import load_catalogue


@pytest.fixture
def valid_registry_document() -> dict:
    return {
        "sources": [
            {
                "source_id": "demo://synthetic/catalogue/v0.1",
                "publisher": "GeoWeaver synthetic demo",
                "title": "Synthetic catalogue",
                "source_url": "demo://synthetic/catalogue/v0.1",
                "licence": "Synthetic demonstration only.",
                "retrieved_at": "2026-01-15T06:00:00Z",
            },
            {
                "source_id": "demo://synthetic/weather/v0.1",
                "publisher": "GeoWeaver synthetic demo",
                "title": "Synthetic weather",
                "catalogue_identifier": "synthetic-weather-v0.1",
                "licence": "Synthetic demonstration only.",
                "retrieved_at": "2026-01-15T05:30:00Z",
                "published_at": "2026-01-15T05:00:00Z",
                "temporal_resolution": "Single snapshot.",
                "transformation": "None.",
                "limitations": "Not authoritative.",
            },
        ]
    }


def test_validate_valid_registry(valid_registry_document: dict) -> None:
    sources = validate_source_registry_document(valid_registry_document)

    assert len(sources) == 2
    assert sources[0].source_id == "demo://synthetic/catalogue/v0.1"
    assert sources[1].catalogue_identifier == "synthetic-weather-v0.1"
    assert sources[1].transformation == "None."


def test_load_template_registry_covers_demo_fixtures() -> None:
    template_path = Path("data/templates/source_registry.template.json")
    sources = load_source_registry(template_path)

    assert len(sources) == 16
    indexed = index_sources_by_id(sources)
    assert indexed["demo://synthetic/weather/v0.1"].publisher == ("GeoWeaver synthetic demo")

    segments = load_catalogue("data/catalogue/demo_segments.geojson")
    condition, _, travel = load_run_input("data/templates/run_input.template.json")
    catalogue_refs = collect_catalogue_source_refs(segments)
    run_refs = collect_run_input_source_refs(condition, travel)

    assert find_missing_source_refs(sources, catalogue_refs) == ()
    assert find_missing_source_refs(sources, run_refs) == ()


def test_load_nonexistent_file(tmp_path: Path) -> None:
    with pytest.raises(SourceRegistryValidationError, match="could not read source registry"):
        load_source_registry(tmp_path / "missing.json")


def test_load_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(SourceRegistryValidationError, match="not valid JSON"):
        load_source_registry(bad)


def test_load_invalid_utf8(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"\x80\x81")
    with pytest.raises(SourceRegistryValidationError, match="not valid UTF-8"):
        load_source_registry(bad)


def test_not_a_mapping() -> None:
    with pytest.raises(SourceRegistryValidationError, match="source_registry must be an object"):
        validate_source_registry_document([])


def test_missing_top_level_section() -> None:
    with pytest.raises(
        SourceRegistryValidationError, match="missing required top-level section: sources"
    ):
        validate_source_registry_document({})


def test_empty_sources_rejected() -> None:
    with pytest.raises(SourceRegistryValidationError, match="must contain at least one source"):
        validate_source_registry_document({"sources": []})


def test_missing_required_field(valid_registry_document: dict) -> None:
    document = deepcopy(valid_registry_document)
    del document["sources"][0]["publisher"]
    with pytest.raises(
        SourceRegistryValidationError, match="is missing required fields: publisher"
    ):
        validate_source_registry_document(document)


def test_blank_source_id_rejected(valid_registry_document: dict) -> None:
    document = deepcopy(valid_registry_document)
    document["sources"][0]["source_id"] = "   "
    with pytest.raises(SourceRegistryValidationError, match="source_id must be a non-empty string"):
        validate_source_registry_document(document)


def test_blank_publisher_rejected(valid_registry_document: dict) -> None:
    document = deepcopy(valid_registry_document)
    document["sources"][1]["publisher"] = ""
    with pytest.raises(SourceRegistryValidationError, match="publisher must be a non-empty string"):
        validate_source_registry_document(document)


def test_missing_url_and_identifier_rejected(
    valid_registry_document: dict,
) -> None:
    document = deepcopy(valid_registry_document)
    del document["sources"][0]["source_url"]
    with pytest.raises(
        SourceRegistryValidationError,
        match="at least one of source_url or catalogue_identifier is required",
    ):
        validate_source_registry_document(document)


def test_naive_retrieved_timestamp_rejected(valid_registry_document: dict) -> None:
    document = deepcopy(valid_registry_document)
    document["sources"][0]["retrieved_at"] = "2026-01-15T06:00:00"
    with pytest.raises(SourceRegistryValidationError, match="retrieved_at must include a timezone"):
        validate_source_registry_document(document)


def test_invalid_timestamp_string_rejected(valid_registry_document: dict) -> None:
    document = deepcopy(valid_registry_document)
    document["sources"][0]["retrieved_at"] = "not-a-timestamp"
    with pytest.raises(
        SourceRegistryValidationError, match="retrieved_at must be an ISO 8601 timestamp"
    ):
        validate_source_registry_document(document)


def test_duplicate_source_ids_rejected(valid_registry_document: dict) -> None:
    document = deepcopy(valid_registry_document)
    document["sources"].append(deepcopy(document["sources"][0]))
    with pytest.raises(SourceRegistryValidationError, match="duplicates source"):
        validate_source_registry_document(document)


def test_find_missing_refs_reports_sorted_unknowns(
    valid_registry_document: dict,
) -> None:
    sources = validate_source_registry_document(valid_registry_document)
    missing = find_missing_source_refs(sources, ["zzz", "demo://synthetic/catalogue/v0.1", "aaa"])
    assert missing == ("aaa", "zzz")


def test_audit_demo_catalogue_refs_against_template() -> None:
    sources = load_source_registry("data/templates/source_registry.template.json")
    segments = load_catalogue("data/catalogue/demo_segments.geojson")
    refs = collect_catalogue_source_refs(segments)

    # Spot-check that restriction and segment refs are collected.
    assert "demo://synthetic/catalogue/v0.1" in refs
    assert "demo://synthetic/restrictions/closed-reach" in refs
    assert find_missing_source_refs(sources, refs) == ()


def test_audit_detects_unknown_catalogue_ref(
    demo_document: dict[str, object],
) -> None:
    sources = load_source_registry("data/templates/source_registry.template.json")
    segments = load_catalogue("data/catalogue/demo_segments.geojson")
    refs = collect_catalogue_source_refs(segments)
    assert find_missing_source_refs(sources, [*refs, "demo://unknown/source"]) == (
        "demo://unknown/source",
    )
    assert isinstance(demo_document, dict)


def test_template_is_deterministic_json() -> None:
    path = Path("data/templates/source_registry.template.json")
    document = json.loads(path.read_text(encoding="utf-8"))
    first = validate_source_registry_document(document)
    second = validate_source_registry_document(json.loads(json.dumps(document)))
    assert first == second
