"""Tests for provenance source registry validation, loading, and verification."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from geoweaver.data.provenance import (
    ProvenanceValidationError,
    load_source_registry,
    validate_source_registry_document,
    verify_source_references,
)
from geoweaver.domain.models import SourceRecord, SourceRegistry


def test_source_record_valid() -> None:
    now = datetime.now(UTC)
    record = SourceRecord(
        source_id="src-001",
        publisher="Test Authority",
        title="Test Dataset",
        url_or_identifier="https://example.com/data",
        licence="CC-BY-4.0",
        retrieved_at=now,
        publication_updated_at=now,
        crs_or_resolution="EPSG:4326",
        transformation_note="None",
        limitations="Testing only",
    )
    assert record.source_id == "src-001"
    assert record.publisher == "Test Authority"
    assert record.retrieved_at == now


def test_source_record_invalid_blank_or_type() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="source_id must not be empty"):
        SourceRecord(
            source_id="   ",
            publisher="Test Authority",
            title="Test Dataset",
            url_or_identifier="https://example.com/data",
            licence="CC-BY-4.0",
            retrieved_at=now,
        )

    naive = datetime.now()
    with pytest.raises(ValueError, match="retrieved_at must include a timezone"):
        SourceRecord(
            source_id="src-001",
            publisher="Test Authority",
            title="Test Dataset",
            url_or_identifier="https://example.com/data",
            licence="CC-BY-4.0",
            retrieved_at=naive,
        )


def test_source_registry_methods() -> None:
    now = datetime.now(UTC)
    r1 = SourceRecord(
        source_id="src-1",
        publisher="P1",
        title="T1",
        url_or_identifier="U1",
        licence="L1",
        retrieved_at=now,
    )
    r2 = SourceRecord(
        source_id="src-2",
        publisher="P2",
        title="T2",
        url_or_identifier="U2",
        licence="L2",
        retrieved_at=now,
    )
    registry = SourceRegistry(sources=(r1, r2))

    assert "src-1" in registry
    assert "src-2" in registry
    assert "src-3" not in registry
    assert 123 not in registry
    assert registry.get("src-1") == r1
    assert registry.get("src-3") is None


def test_source_registry_duplicate_ids() -> None:
    now = datetime.now(UTC)
    r1 = SourceRecord(
        source_id="src-1",
        publisher="P1",
        title="T1",
        url_or_identifier="U1",
        licence="L1",
        retrieved_at=now,
    )
    r2 = SourceRecord(
        source_id="src-1",
        publisher="P2",
        title="T2",
        url_or_identifier="U2",
        licence="L2",
        retrieved_at=now,
    )
    with pytest.raises(ValueError, match="duplicate source_id in registry: 'src-1'"):
        SourceRegistry(sources=(r1, r2))


def test_load_template_source_registry() -> None:
    template_path = Path("data/templates/source_registry.template.json")
    registry = load_source_registry(template_path)
    assert len(registry.sources) == 16
    assert "demo://synthetic/weather/v0.1" in registry
    record = registry.get("demo://synthetic/weather/v0.1")
    assert record is not None
    assert record.publisher == "Bureau of Meteorology (Synthetic)"


def test_validate_source_registry_document_errors() -> None:
    with pytest.raises(ProvenanceValidationError, match="source_registry must be an object"):
        validate_source_registry_document("not a dict")

    with pytest.raises(
        ProvenanceValidationError,
        match="source_registry is missing required section: sources",
    ):
        validate_source_registry_document({"source_registry": {}})

    with pytest.raises(
        ProvenanceValidationError,
        match="source_registry is missing required section: sources",
    ):
        validate_source_registry_document({})

    with pytest.raises(
        ProvenanceValidationError, match="source_registry.sources must contain at least one source"
    ):
        validate_source_registry_document({"source_registry": {"sources": []}})

    valid_record_dict = {
        "source_id": "src-1",
        "publisher": "Pub",
        "title": "Title",
        "url_or_identifier": "URL",
        "licence": "Licence",
        "retrieved_at": "2026-01-01T00:00:00Z",
    }

    # Missing required field
    incomplete = dict(valid_record_dict)
    incomplete.pop("publisher")
    with pytest.raises(
        ProvenanceValidationError,
        match="source_registry.sources\\[0\\] is missing required fields: publisher",
    ):
        validate_source_registry_document({"source_registry": {"sources": [incomplete]}})

    # Naive timestamp
    naive_ts = dict(valid_record_dict, retrieved_at="2026-01-01T00:00:00")
    with pytest.raises(
        ProvenanceValidationError,
        match="source_registry.sources\\[0\\].retrieved_at must include a timezone",
    ):
        validate_source_registry_document({"source_registry": {"sources": [naive_ts]}})

    # Duplicate IDs
    with pytest.raises(
        ProvenanceValidationError,
        match="source_registry.sources\\[1\\].source_id duplicates 'src-1'",
    ):
        validate_source_registry_document(
            {"source_registry": {"sources": [valid_record_dict, valid_record_dict]}}
        )


def test_load_source_registry_file_errors(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist.json"
    with pytest.raises(ProvenanceValidationError, match="could not read source registry"):
        load_source_registry(non_existent)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{bad json", encoding="utf-8")
    with pytest.raises(ProvenanceValidationError, match="is not valid JSON"):
        load_source_registry(invalid_json)


def test_verify_source_references() -> None:
    now = datetime.now(UTC)
    r1 = SourceRecord(
        source_id="src-1",
        publisher="P1",
        title="T1",
        url_or_identifier="U1",
        licence="L1",
        retrieved_at=now,
    )
    registry = SourceRegistry(sources=(r1,))

    missing = verify_source_references(registry, ["src-1", "src-1", "src-2", "src-3"])
    assert missing == ("src-2", "src-3")

    missing_none = verify_source_references(registry, ["src-1"])
    assert missing_none == ()


def test_demo_catalogue_and_run_input_provenance_resolution() -> None:
    from geoweaver.data.loader import load_catalogue
    from geoweaver.data.run_input import load_run_input

    catalogue = load_catalogue("data/catalogue/demo_segments.geojson")
    condition, _, travel_estimates = load_run_input("data/templates/run_input.template.json")
    registry = load_source_registry("data/templates/source_registry.template.json")

    collected_refs: list[str] = []

    # Catalogue source refs
    for segment in catalogue:
        collected_refs.extend(segment.source_refs)
        collected_refs.append(segment.health_advisory_evidence.source_ref)
        for restriction in segment.restrictions:
            collected_refs.append(restriction.source_ref)

    # Condition & travel input source refs
    collected_refs.extend(condition.source_refs)
    for estimate in travel_estimates:
        collected_refs.append(estimate.source_ref)

    missing = verify_source_references(registry, collected_refs)
    assert missing == (), f"Found unresolved source references in demo data: {missing}"


def test_verify_source_references_detects_unresolved_ref() -> None:
    from geoweaver.data.loader import load_catalogue

    catalogue = load_catalogue("data/catalogue/demo_segments.geojson")
    registry = load_source_registry("data/templates/source_registry.template.json")

    collected_refs = list(catalogue[0].source_refs) + ["demo://missing-source-ref/v1.0"]

    missing = verify_source_references(registry, collected_refs)
    assert missing == ("demo://missing-source-ref/v1.0",)
