"""Validated, file-based provenance/source registry for M1.3.

The registry is a small JSON document of the form::

    {"sources": [<source record>, ...]}

Each record describes one stable ``source_id`` referenced by catalogue
``source_refs``, restriction ``source_ref`` values, condition evidence refs,
and travel-estimate ``source_ref`` values. Existing ``source_refs`` strings
remain the IDs that point into this registry.
"""

import json
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import cast

from geoweaver.domain.models import (
    ConditionSnapshot,
    ShorelineSegment,
    SourceRecord,
    TravelEstimate,
)


class SourceRegistryValidationError(ValueError):
    """Raised when a source registry cannot safely produce domain objects."""


REQUIRED_SOURCE_FIELDS = frozenset(
    {
        "source_id",
        "publisher",
        "title",
        "licence",
        "retrieved_at",
    }
)

OPTIONAL_SOURCE_FIELDS = frozenset(
    {
        "source_url",
        "catalogue_identifier",
        "published_at",
        "crs",
        "spatial_resolution",
        "temporal_resolution",
        "transformation",
        "limitations",
    }
)


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise SourceRegistryValidationError(f"{context} must be an object")
    return cast("Mapping[str, object]", value)


def _list(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise SourceRegistryValidationError(f"{context} must be an array")
    return cast("list[object]", value)


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceRegistryValidationError(f"{context} must be a non-empty string")
    return value


def _optional_text(value: object, context: str) -> str | None:
    if value is None:
        return None
    return _text(value, context)


def _optional_free_text(value: object, context: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SourceRegistryValidationError(f"{context} must be a string")
    return value


def _timestamp(value: object, context: str) -> datetime:
    raw_value = _text(value, context)
    try:
        timestamp = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SourceRegistryValidationError(f"{context} must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise SourceRegistryValidationError(f"{context} must include a timezone")
    return timestamp


def _optional_timestamp(value: object, context: str) -> datetime | None:
    if value is None:
        return None
    return _timestamp(value, context)


def _source_record(value: object, context: str) -> SourceRecord:
    record = _mapping(value, context)
    missing = sorted(REQUIRED_SOURCE_FIELDS.difference(record))
    if missing:
        raise SourceRegistryValidationError(
            f"{context} is missing required fields: {', '.join(missing)}"
        )
    try:
        return SourceRecord(
            source_id=_text(record["source_id"], f"{context}.source_id"),
            publisher=_text(record["publisher"], f"{context}.publisher"),
            title=_text(record["title"], f"{context}.title"),
            licence=_text(record["licence"], f"{context}.licence"),
            retrieved_at=_timestamp(record["retrieved_at"], f"{context}.retrieved_at"),
            source_url=_optional_text(record.get("source_url"), f"{context}.source_url"),
            catalogue_identifier=_optional_text(
                record.get("catalogue_identifier"), f"{context}.catalogue_identifier"
            ),
            published_at=_optional_timestamp(record.get("published_at"), f"{context}.published_at"),
            crs=_optional_text(record.get("crs"), f"{context}.crs"),
            spatial_resolution=_optional_text(
                record.get("spatial_resolution"), f"{context}.spatial_resolution"
            ),
            temporal_resolution=_optional_text(
                record.get("temporal_resolution"), f"{context}.temporal_resolution"
            ),
            transformation=_optional_free_text(
                record.get("transformation"), f"{context}.transformation"
            ),
            limitations=_optional_free_text(record.get("limitations"), f"{context}.limitations"),
        )
    except ValueError as error:
        raise SourceRegistryValidationError(f"{context}: {error}") from error


def validate_source_registry_document(document: object) -> tuple[SourceRecord, ...]:
    """Validate a decoded JSON registry into immutable source records."""
    root = _mapping(document, "source_registry")
    if "sources" not in root:
        raise SourceRegistryValidationError(
            "source_registry is missing required top-level section: sources"
        )
    raw_sources = _list(root["sources"], "source_registry.sources")
    if not raw_sources:
        raise SourceRegistryValidationError(
            "source_registry.sources must contain at least one source"
        )
    sources: list[SourceRecord] = []
    seen_ids: set[str] = set()
    for index, raw_source in enumerate(raw_sources):
        item_context = f"source_registry.sources[{index}]"
        record = _source_record(raw_source, item_context)
        if record.source_id in seen_ids:
            raise SourceRegistryValidationError(
                f"{item_context}.source_id duplicates source {record.source_id!r}"
            )
        seen_ids.add(record.source_id)
        sources.append(record)
    return tuple(sources)


def load_source_registry(path: str | Path) -> tuple[SourceRecord, ...]:
    """Read and validate a source-registry JSON document."""
    registry_path = Path(path)
    try:
        with registry_path.open(encoding="utf-8") as registry_file:
            document = json.load(registry_file)
    except OSError as error:
        raise SourceRegistryValidationError(
            f"could not read source registry {registry_path}: {error.strerror or error}"
        ) from error
    except UnicodeError as error:
        raise SourceRegistryValidationError(
            f"source registry {registry_path} is not valid UTF-8: {error}"
        ) from error
    except json.JSONDecodeError as error:
        raise SourceRegistryValidationError(
            f"source registry {registry_path} is not valid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    return validate_source_registry_document(document)


def index_sources_by_id(
    sources: Iterable[SourceRecord],
) -> dict[str, SourceRecord]:
    """Index registry records by stable source ID."""
    return {source.source_id: source for source in sources}


def find_missing_source_refs(
    sources: Iterable[SourceRecord],
    references: Iterable[str],
) -> tuple[str, ...]:
    """Return sorted registry IDs missing for the given evidence references."""
    known = {source.source_id for source in sources}
    missing = {ref for ref in references if ref not in known}
    return tuple(sorted(missing))


def collect_catalogue_source_refs(
    segments: Iterable[ShorelineSegment],
) -> tuple[str, ...]:
    """Collect every source reference used by catalogue segments."""
    collected: set[str] = set()
    for segment in segments:
        collected.update(segment.source_refs)
        collected.add(segment.health_advisory_evidence.source_ref)
        for restriction in segment.restrictions:
            collected.add(restriction.source_ref)
    return tuple(sorted(collected))


def collect_run_input_source_refs(
    condition: ConditionSnapshot,
    travel_estimates: Iterable[TravelEstimate],
) -> tuple[str, ...]:
    """Collect every source reference used by a recommendation-run input."""
    collected = set(condition.source_refs)
    for estimate in travel_estimates:
        collected.add(estimate.source_ref)
    return tuple(sorted(collected))
