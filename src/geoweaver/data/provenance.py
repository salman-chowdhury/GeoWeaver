"""Strict validation and loading for provenance source registries."""

import json
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import cast

from geoweaver.domain.models import SourceRecord, SourceRegistry


class ProvenanceValidationError(ValueError):
    """Raised when a provenance document or reference check fails validation."""


REQUIRED_SOURCE_RECORD_FIELDS = frozenset(
    {
        "source_id",
        "publisher",
        "title",
        "url_or_identifier",
        "licence",
        "retrieved_at",
    }
)


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ProvenanceValidationError(f"{context} must be an object")
    return cast("Mapping[str, object]", value)


def _list(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise ProvenanceValidationError(f"{context} must be an array")
    return cast("list[object]", value)


def _text(value: object, context: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        qualifier = "a string" if allow_empty else "a non-empty string"
        raise ProvenanceValidationError(f"{context} must be {qualifier}")
    return value


def _optional_text(value: object, context: str) -> str | None:
    if value is None:
        return None
    return _text(value, context)


def _timestamp(value: object, context: str) -> datetime:
    raw_value = _text(value, context)
    try:
        timestamp = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProvenanceValidationError(f"{context} must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ProvenanceValidationError(f"{context} must include a timezone")
    return timestamp


def _optional_timestamp(value: object, context: str) -> datetime | None:
    if value is None:
        return None
    return _timestamp(value, context)


def _source_record(value: object, context: str) -> SourceRecord:
    record_obj = _mapping(value, context)
    missing = sorted(REQUIRED_SOURCE_RECORD_FIELDS.difference(record_obj))
    if missing:
        raise ProvenanceValidationError(
            f"{context} is missing required fields: {', '.join(missing)}"
        )

    try:
        return SourceRecord(
            source_id=_text(record_obj["source_id"], f"{context}.source_id"),
            publisher=_text(record_obj["publisher"], f"{context}.publisher"),
            title=_text(record_obj["title"], f"{context}.title"),
            url_or_identifier=_text(
                record_obj["url_or_identifier"], f"{context}.url_or_identifier"
            ),
            licence=_text(record_obj["licence"], f"{context}.licence"),
            retrieved_at=_timestamp(record_obj["retrieved_at"], f"{context}.retrieved_at"),
            publication_updated_at=_optional_timestamp(
                record_obj.get("publication_updated_at"),
                f"{context}.publication_updated_at",
            ),
            crs_or_resolution=_optional_text(
                record_obj.get("crs_or_resolution"), f"{context}.crs_or_resolution"
            ),
            transformation_note=_optional_text(
                record_obj.get("transformation_note"), f"{context}.transformation_note"
            ),
            limitations=_optional_text(record_obj.get("limitations"), f"{context}.limitations"),
        )
    except ValueError as error:
        raise ProvenanceValidationError(f"{context}: {error}") from error


def validate_source_registry_document(document: object) -> SourceRegistry:
    """Validate a decoded JSON object into a SourceRegistry domain object."""
    root = _mapping(document, "source_registry")
    if "source_registry" in root:
        registry_obj = _mapping(root["source_registry"], "source_registry")
    else:
        registry_obj = root

    if "sources" not in registry_obj:
        raise ProvenanceValidationError("source_registry is missing required section: sources")

    raw_sources = _list(registry_obj["sources"], "source_registry.sources")
    if not raw_sources:
        raise ProvenanceValidationError("source_registry.sources must contain at least one source")

    sources: list[SourceRecord] = []
    seen_ids: set[str] = set()
    for index, raw_source in enumerate(raw_sources):
        item_context = f"source_registry.sources[{index}]"
        record = _source_record(raw_source, item_context)
        if record.source_id in seen_ids:
            raise ProvenanceValidationError(
                f"{item_context}.source_id duplicates {record.source_id!r}"
            )
        seen_ids.add(record.source_id)
        sources.append(record)

    return SourceRegistry(sources=tuple(sources))


def load_source_registry(path: str | Path) -> SourceRegistry:
    """Read and validate a source registry JSON document with actionable error messages."""
    registry_path = Path(path)
    try:
        with registry_path.open(encoding="utf-8") as registry_file:
            document = json.load(registry_file)
    except OSError as error:
        raise ProvenanceValidationError(
            f"could not read source registry {registry_path}: {error.strerror or error}"
        ) from error
    except UnicodeError as error:
        raise ProvenanceValidationError(
            f"source registry {registry_path} is not valid UTF-8: {error}"
        ) from error
    except json.JSONDecodeError as error:
        raise ProvenanceValidationError(
            f"source registry {registry_path} is not valid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    return validate_source_registry_document(document)


def verify_source_references(
    registry: SourceRegistry, source_refs: Iterable[str]
) -> tuple[str, ...]:
    """Verify that all referenced source IDs exist in the registry, returning any missing IDs."""
    missing: list[str] = []
    seen: set[str] = set()
    for ref in source_refs:
        if ref not in seen:
            seen.add(ref)
            if ref not in registry:
                missing.append(ref)
    return tuple(missing)
