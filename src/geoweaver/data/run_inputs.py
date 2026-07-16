"""Strict file adapters for reproducible recommendation-run inputs."""

import json
import math
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import cast

from geoweaver.domain.enums import (
    ConditionScopeType,
    DataClassification,
    EvidenceState,
    IntendedActivity,
    SkillLevel,
    TideAssignmentMethod,
    TideStage,
)
from geoweaver.domain.models import (
    ConditionSnapshot,
    ShorelineSegment,
    TideSourceApplicability,
    TravelEstimate,
    TripRequest,
)

TRIP_SCHEMA_VERSION = "geoweaver-trip-v0.1"
CONDITIONS_SCHEMA_VERSION = "geoweaver-conditions-v0.1"
TRAVEL_SCHEMA_VERSION = "geoweaver-travel-v0.1"


class RunInputValidationError(ValueError):
    """Raised when a trip, condition, or travel file cannot be used safely."""


def _read_json(path: str | Path, input_name: str) -> object:
    input_path = Path(path)
    try:
        with input_path.open(encoding="utf-8") as input_file:
            return json.load(input_file)
    except OSError as error:
        raise RunInputValidationError(
            f"could not read {input_name} file {input_path}: {error.strerror or error}"
        ) from error
    except UnicodeError as error:
        raise RunInputValidationError(
            f"{input_name} file {input_path} is not valid UTF-8: {error}"
        ) from error
    except json.JSONDecodeError as error:
        raise RunInputValidationError(
            f"{input_name} file {input_path} is not valid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise RunInputValidationError(f"{context} must be an object")
    return cast("Mapping[str, object]", value)


def _list(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise RunInputValidationError(f"{context} must be an array")
    return cast("list[object]", value)


def _fields(
    value: Mapping[str, object],
    context: str,
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> None:
    missing = sorted(required.difference(value))
    if missing:
        raise RunInputValidationError(f"{context} is missing required fields: {', '.join(missing)}")
    unknown = sorted(set(value).difference(required | optional))
    if unknown:
        raise RunInputValidationError(f"{context} has unknown fields: {', '.join(unknown)}")


def _text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunInputValidationError(f"{context} must be a non-empty string")
    return value


def _optional_text(value: object, context: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RunInputValidationError(f"{context} must be a string or null")
    return value


def _boolean(value: object, context: str) -> bool:
    if not isinstance(value, bool):
        raise RunInputValidationError(f"{context} must be true or false")
    return value


def _integer(
    value: object,
    context: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RunInputValidationError(f"{context} must be an integer")
    if minimum is not None and value < minimum:
        raise RunInputValidationError(f"{context} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise RunInputValidationError(f"{context} must be at most {maximum}")
    return value


def _optional_number(value: object, context: str, *, minimum: float = 0.0) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RunInputValidationError(f"{context} must be a number or null")
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        raise RunInputValidationError(f"{context} must be finite and at least {minimum:g}, or null")
    return number


def _number(value: object, context: str, *, minimum: float = 0.0) -> float:
    number = _optional_number(value, context, minimum=minimum)
    if number is None:
        raise RunInputValidationError(f"{context} must be a number")
    return number


def _optional_integer(
    value: object,
    context: str,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int | None:
    if value is None:
        return None
    return _integer(value, context, minimum=minimum, maximum=maximum)


def _enum_value[EnumType: StrEnum](
    enum_type: type[EnumType], value: object, context: str
) -> EnumType:
    raw_value = _text(value, context)
    try:
        return enum_type(raw_value)
    except ValueError as error:
        allowed = ", ".join(item.value for item in enum_type)
        raise RunInputValidationError(
            f"{context} has unsupported value {raw_value!r}; expected one of: {allowed}"
        ) from error


def _timestamp(value: object, context: str) -> datetime:
    raw_value = _text(value, context)
    try:
        timestamp = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RunInputValidationError(f"{context} must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise RunInputValidationError(f"{context} must include a timezone")
    return timestamp


def _string_tuple(value: object, context: str, *, require_items: bool) -> tuple[str, ...]:
    values = _list(value, context)
    if require_items and not values:
        raise RunInputValidationError(f"{context} must contain at least one reference")
    result = tuple(_text(item, f"{context}[{index}]") for index, item in enumerate(values))
    if len(set(result)) != len(result):
        raise RunInputValidationError(f"{context} must not contain duplicate values")
    return result


def _classification(root: Mapping[str, object], context: str) -> DataClassification:
    return _enum_value(
        DataClassification,
        root.get("data_classification"),
        f"{context}.data_classification",
    )


def _require_matching_classification(
    actual: DataClassification,
    trip: TripRequest,
    context: str,
) -> None:
    if actual is not trip.data_classification:
        raise RunInputValidationError(
            f"{context}.data_classification must match the trip classification "
            f"{trip.data_classification.value!r}"
        )


def load_trip_request(path: str | Path) -> TripRequest:
    """Load one strictly validated trip request from JSON."""
    root = _mapping(_read_json(path, "trip"), "trip")
    required = frozenset(
        {
            "schema_version",
            "data_classification",
            "origin_label",
            "target_datetime",
            "maximum_travel_minutes",
            "skill_level",
            "family_suitability_required",
            "minimum_family_rating",
            "desired_privacy_rating",
            "minimum_casting_space_rating",
            "intended_activity",
            "minimum_usable_daylight_minutes",
        }
    )
    _fields(root, "trip", required=required, optional=frozenset({"run_id", "notes"}))
    schema_version = _text(root["schema_version"], "trip.schema_version")
    if schema_version != TRIP_SCHEMA_VERSION:
        raise RunInputValidationError(f"trip.schema_version must be {TRIP_SCHEMA_VERSION!r}")
    try:
        return TripRequest(
            run_id=(
                _text(root["run_id"], "trip.run_id") if root.get("run_id") is not None else None
            ),
            origin_label=_text(root["origin_label"], "trip.origin_label"),
            target_datetime=_timestamp(root["target_datetime"], "trip.target_datetime"),
            maximum_travel_minutes=_integer(
                root["maximum_travel_minutes"],
                "trip.maximum_travel_minutes",
                minimum=0,
                maximum=1440,
            ),
            skill_level=_enum_value(SkillLevel, root["skill_level"], "trip.skill_level"),
            family_suitability_required=_boolean(
                root["family_suitability_required"],
                "trip.family_suitability_required",
            ),
            minimum_family_rating=_integer(
                root["minimum_family_rating"],
                "trip.minimum_family_rating",
                minimum=0,
                maximum=5,
            ),
            desired_privacy_rating=_integer(
                root["desired_privacy_rating"],
                "trip.desired_privacy_rating",
                minimum=0,
                maximum=5,
            ),
            minimum_casting_space_rating=_integer(
                root["minimum_casting_space_rating"],
                "trip.minimum_casting_space_rating",
                minimum=0,
                maximum=5,
            ),
            intended_activity=_enum_value(
                IntendedActivity,
                root["intended_activity"],
                "trip.intended_activity",
            ),
            minimum_usable_daylight_minutes=_integer(
                root["minimum_usable_daylight_minutes"],
                "trip.minimum_usable_daylight_minutes",
                minimum=0,
                maximum=1440,
            ),
            notes=_optional_text(root.get("notes"), "trip.notes"),
            data_classification=_classification(root, "trip"),
        )
    except ValueError as error:
        if isinstance(error, RunInputValidationError):
            raise
        raise RunInputValidationError(f"trip: {error}") from error


def _condition_applicability(
    value: object,
    context: str,
    segments: tuple[ShorelineSegment, ...],
) -> tuple[ConditionScopeType, str, tuple[str, ...]]:
    applicability = _mapping(value, context)
    scope_type = _enum_value(
        ConditionScopeType,
        applicability.get("scope_type"),
        f"{context}.scope_type",
    )
    required = frozenset({"scope_type", "scope_id"})
    optional = (
        frozenset({"segment_ids"})
        if scope_type is ConditionScopeType.EXPLICIT_SEGMENT_GROUP
        else frozenset()
    )
    _fields(applicability, context, required=required, optional=optional)
    scope_id = _text(applicability["scope_id"], f"{context}.scope_id")
    segments_by_id = {segment.segment_id: segment for segment in segments}

    if scope_type is ConditionScopeType.SEGMENT:
        if scope_id not in segments_by_id:
            raise RunInputValidationError(
                f"{context}.scope_id references unknown segment ID {scope_id!r}"
            )
        return scope_type, scope_id, (scope_id,)

    if scope_type is ConditionScopeType.WATERWAY:
        applicable_ids = tuple(
            sorted(segment.segment_id for segment in segments if segment.waterway == scope_id)
        )
        if not applicable_ids:
            raise RunInputValidationError(
                f"{context}.scope_id references unknown waterway {scope_id!r}"
            )
        return scope_type, scope_id, applicable_ids

    if "segment_ids" not in applicability:
        raise RunInputValidationError(f"{context} is missing required fields: segment_ids")
    segment_ids = _string_tuple(
        applicability["segment_ids"],
        f"{context}.segment_ids",
        require_items=True,
    )
    unknown_ids = sorted(set(segment_ids).difference(segments_by_id))
    if unknown_ids:
        raise RunInputValidationError(
            f"{context}.segment_ids references unknown segment IDs: {', '.join(unknown_ids)}"
        )
    return scope_type, scope_id, tuple(sorted(segment_ids))


def _hazard_status(value: object, context: str) -> bool | None:
    status = _text(value, context)
    mapping = {"clear": False, "active": True, "unknown": None}
    if status not in mapping:
        raise RunInputValidationError(
            f"{context} has unsupported value {status!r}; expected one of: clear, active, unknown"
        )
    return mapping[status]


def _footing_status(value: object, context: str) -> bool | None:
    status = _text(value, context)
    mapping = {"safe": True, "unsafe": False, "unknown": None}
    if status not in mapping:
        raise RunInputValidationError(
            f"{context} has unsupported value {status!r}; expected one of: safe, unsafe, unknown"
        )
    return mapping[status]


def load_condition_snapshots(
    path: str | Path,
    segments: tuple[ShorelineSegment, ...],
    trip: TripRequest,
) -> tuple[ConditionSnapshot, ...]:
    """Load conditions and resolve every declared scope against the catalogue."""
    root = _mapping(_read_json(path, "conditions"), "conditions_file")
    _fields(
        root,
        "conditions_file",
        required=frozenset({"schema_version", "data_classification", "conditions"}),
    )
    schema_version = _text(root["schema_version"], "conditions_file.schema_version")
    if schema_version != CONDITIONS_SCHEMA_VERSION:
        raise RunInputValidationError(
            f"conditions_file.schema_version must be {CONDITIONS_SCHEMA_VERSION!r}"
        )
    _require_matching_classification(
        _classification(root, "conditions_file"), trip, "conditions_file"
    )
    raw_conditions = _list(root["conditions"], "conditions_file.conditions")
    if not raw_conditions:
        raise RunInputValidationError(
            "conditions_file.conditions must contain at least one snapshot"
        )

    snapshots: list[ConditionSnapshot] = []
    seen_snapshot_ids: set[str] = set()
    covered_by: dict[str, str] = {}
    required_fields = frozenset(
        {
            "snapshot_id",
            "applicability",
            "observed_or_predicted_at",
            "tide_stage",
            "weather_warning_status",
            "lightning_thunderstorm_status",
            "sustained_wind_kph",
            "gust_speed_kph",
            "footing_status",
            "usable_daylight_minutes",
            "source_refs",
            "tide_source",
            "retrieved_at",
            "evidence_state",
        }
    )
    for index, raw_condition in enumerate(raw_conditions):
        context = f"conditions_file.conditions[{index}]"
        condition = _mapping(raw_condition, context)
        _fields(condition, context, required=required_fields)
        snapshot_id = _text(condition["snapshot_id"], f"{context}.snapshot_id")
        if snapshot_id in seen_snapshot_ids:
            raise RunInputValidationError(f"duplicate condition snapshot_id: {snapshot_id!r}")
        seen_snapshot_ids.add(snapshot_id)
        scope_type, scope_id, applicable_segment_ids = _condition_applicability(
            condition["applicability"], f"{context}.applicability", segments
        )
        for segment_id in applicable_segment_ids:
            if segment_id in covered_by:
                raise RunInputValidationError(
                    f"condition snapshots {covered_by[segment_id]!r} and {snapshot_id!r} "
                    f"both apply to segment {segment_id!r}"
                )
            covered_by[segment_id] = snapshot_id

        valid_at = _timestamp(
            condition["observed_or_predicted_at"],
            f"{context}.observed_or_predicted_at",
        )
        if valid_at != trip.target_datetime:
            raise RunInputValidationError(
                f"{context}.observed_or_predicted_at must exactly match trip.target_datetime"
            )
        retrieved_at = _timestamp(condition["retrieved_at"], f"{context}.retrieved_at")
        if retrieved_at > trip.target_datetime:
            raise RunInputValidationError(
                f"{context}.retrieved_at must not be later than trip.target_datetime"
            )
        freshness_minutes = int((trip.target_datetime - retrieved_at).total_seconds() // 60)
        source_refs = _mapping(condition["source_refs"], f"{context}.source_refs")
        _fields(
            source_refs,
            f"{context}.source_refs",
            required=frozenset({"weather", "footing", "tide", "daylight"}),
        )
        evidence_state = _enum_value(
            EvidenceState,
            condition["evidence_state"],
            f"{context}.evidence_state",
        )
        tide_source = _mapping(condition["tide_source"], f"{context}.tide_source")
        _fields(
            tide_source,
            f"{context}.tide_source",
            required=frozenset(
                {
                    "source_location_id",
                    "source_location_label",
                    "distance_to_scope_km",
                    "assignment_method",
                    "applicability_source_ref",
                    "retrieved_at",
                    "evidence_state",
                }
            ),
        )
        tide_applicability_ref = _text(
            tide_source["applicability_source_ref"],
            f"{context}.tide_source.applicability_source_ref",
        )
        tide_refs = _string_tuple(
            source_refs["tide"],
            f"{context}.source_refs.tide",
            require_items=True,
        )
        if tide_applicability_ref not in tide_refs:
            raise RunInputValidationError(
                f"{context}.tide_source.applicability_source_ref must also appear in "
                f"{context}.source_refs.tide"
            )
        tide_source_retrieved_at = _timestamp(
            tide_source["retrieved_at"],
            f"{context}.tide_source.retrieved_at",
        )
        if tide_source_retrieved_at > trip.target_datetime:
            raise RunInputValidationError(
                f"{context}.tide_source.retrieved_at must not be later than trip.target_datetime"
            )
        verified = evidence_state is EvidenceState.VERIFIED
        try:
            snapshots.append(
                ConditionSnapshot(
                    snapshot_id=snapshot_id,
                    applicable_segment_ids=applicable_segment_ids,
                    valid_at=valid_at,
                    tide_stage=_enum_value(
                        TideStage,
                        condition["tide_stage"],
                        f"{context}.tide_stage",
                    ),
                    severe_weather_warning=_hazard_status(
                        condition["weather_warning_status"],
                        f"{context}.weather_warning_status",
                    ),
                    lightning_or_severe_thunderstorm_risk=_hazard_status(
                        condition["lightning_thunderstorm_status"],
                        f"{context}.lightning_thunderstorm_status",
                    ),
                    footing_safe=_footing_status(
                        condition["footing_status"], f"{context}.footing_status"
                    ),
                    usable_daylight_minutes=_optional_integer(
                        condition["usable_daylight_minutes"],
                        f"{context}.usable_daylight_minutes",
                        maximum=1440,
                    ),
                    wind_speed_kph=_optional_number(
                        condition["sustained_wind_kph"],
                        f"{context}.sustained_wind_kph",
                    ),
                    gust_speed_kph=_optional_number(
                        condition["gust_speed_kph"], f"{context}.gust_speed_kph"
                    ),
                    data_freshness_minutes=freshness_minutes,
                    inferred=evidence_state is EvidenceState.INFERRED,
                    weather_status_verified=verified,
                    footing_status_verified=verified,
                    tide_status_verified=verified,
                    daylight_status_verified=verified,
                    weather_source_refs=_string_tuple(
                        source_refs["weather"],
                        f"{context}.source_refs.weather",
                        require_items=True,
                    ),
                    footing_source_refs=_string_tuple(
                        source_refs["footing"],
                        f"{context}.source_refs.footing",
                        require_items=True,
                    ),
                    tide_source_refs=tide_refs,
                    daylight_source_refs=_string_tuple(
                        source_refs["daylight"],
                        f"{context}.source_refs.daylight",
                        require_items=True,
                    ),
                    retrieved_at=retrieved_at,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    tide_source_applicability=TideSourceApplicability(
                        source_location_id=_text(
                            tide_source["source_location_id"],
                            f"{context}.tide_source.source_location_id",
                        ),
                        source_location_label=_text(
                            tide_source["source_location_label"],
                            f"{context}.tide_source.source_location_label",
                        ),
                        distance_to_scope_km=_number(
                            tide_source["distance_to_scope_km"],
                            f"{context}.tide_source.distance_to_scope_km",
                        ),
                        assignment_method=_enum_value(
                            TideAssignmentMethod,
                            tide_source["assignment_method"],
                            f"{context}.tide_source.assignment_method",
                        ),
                        applicability_source_ref=tide_applicability_ref,
                        retrieved_at=tide_source_retrieved_at,
                        evidence_state=_enum_value(
                            EvidenceState,
                            tide_source["evidence_state"],
                            f"{context}.tide_source.evidence_state",
                        ),
                    ),
                )
            )
        except ValueError as error:
            if isinstance(error, RunInputValidationError):
                raise
            raise RunInputValidationError(f"{context}: {error}") from error

    missing_ids = sorted({segment.segment_id for segment in segments}.difference(covered_by))
    if missing_ids:
        raise RunInputValidationError(
            "condition snapshots do not apply to catalogue segment IDs: " + ", ".join(missing_ids)
        )
    return tuple(sorted(snapshots, key=lambda item: item.snapshot_id))


def load_travel_estimates(
    path: str | Path,
    segments: tuple[ShorelineSegment, ...],
    trip: TripRequest,
) -> tuple[TravelEstimate, ...]:
    """Load sourced manual travel estimates and reject ambiguous mappings."""
    root = _mapping(_read_json(path, "travel"), "travel_file")
    _fields(
        root,
        "travel_file",
        required=frozenset({"schema_version", "data_classification", "estimates"}),
    )
    schema_version = _text(root["schema_version"], "travel_file.schema_version")
    if schema_version != TRAVEL_SCHEMA_VERSION:
        raise RunInputValidationError(
            f"travel_file.schema_version must be {TRAVEL_SCHEMA_VERSION!r}"
        )
    _require_matching_classification(_classification(root, "travel_file"), trip, "travel_file")
    known_segment_ids = {segment.segment_id for segment in segments}
    estimates: list[TravelEstimate] = []
    seen_ids: set[str] = set()
    required_fields = frozenset(
        {
            "segment_id",
            "estimated_travel_minutes",
            "origin_label",
            "source_ref",
            "retrieved_at",
            "evidence_state",
        }
    )
    for index, raw_estimate in enumerate(_list(root["estimates"], "travel_file.estimates")):
        context = f"travel_file.estimates[{index}]"
        estimate = _mapping(raw_estimate, context)
        _fields(estimate, context, required=required_fields)
        segment_id = _text(estimate["segment_id"], f"{context}.segment_id")
        if segment_id in seen_ids:
            raise RunInputValidationError(f"duplicate travel estimate for {segment_id!r}")
        seen_ids.add(segment_id)
        if segment_id not in known_segment_ids:
            raise RunInputValidationError(
                f"{context}.segment_id references unknown segment ID {segment_id!r}"
            )
        origin_label = _text(estimate["origin_label"], f"{context}.origin_label")
        if origin_label != trip.origin_label:
            raise RunInputValidationError(
                f"{context}.origin_label must match trip.origin_label {trip.origin_label!r}"
            )
        retrieved_at = _timestamp(estimate["retrieved_at"], f"{context}.retrieved_at")
        if retrieved_at > trip.target_datetime:
            raise RunInputValidationError(
                f"{context}.retrieved_at must not be later than trip.target_datetime"
            )
        evidence_state = _enum_value(
            EvidenceState,
            estimate["evidence_state"],
            f"{context}.evidence_state",
        )
        try:
            estimates.append(
                TravelEstimate(
                    segment_id=segment_id,
                    origin_label=origin_label,
                    minutes=_integer(
                        estimate["estimated_travel_minutes"],
                        f"{context}.estimated_travel_minutes",
                        minimum=0,
                    ),
                    source_ref=_text(estimate["source_ref"], f"{context}.source_ref"),
                    inferred=evidence_state is EvidenceState.INFERRED,
                    retrieved_at=retrieved_at,
                )
            )
        except ValueError as error:
            if isinstance(error, RunInputValidationError):
                raise
            raise RunInputValidationError(f"{context}: {error}") from error
    return tuple(sorted(estimates, key=lambda item: item.segment_id))
