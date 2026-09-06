"""Strict validation and loading for user-supplied recommendation-run inputs."""

import json
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import cast

from geoweaver.domain.enums import SkillLevel, TideStage
from geoweaver.domain.models import ConditionSnapshot, TravelEstimate, UserPreferences


class RunInputValidationError(ValueError):
    """Raised when a run-input document cannot safely produce domain objects."""


REQUIRED_CONDITION_FIELDS = frozenset(
    {
        "snapshot_id",
        "applicable_segment_ids",
        "valid_at",
        "tide_stage",
        "severe_weather_warning",
        "lightning_or_severe_thunderstorm_risk",
        "footing_safe",
        "usable_daylight_minutes",
        "wind_speed_kph",
        "gust_speed_kph",
        "data_freshness_minutes",
        "inferred",
        "weather_status_verified",
        "footing_status_verified",
        "tide_status_verified",
        "daylight_status_verified",
        "weather_source_refs",
        "footing_source_refs",
        "tide_source_refs",
        "daylight_source_refs",
    }
)

REQUIRED_PREFERENCES_FIELDS = frozenset(
    {
        "skill_level",
        "require_family_suitable",
        "minimum_family_suitability",
        "minimum_casting_space_rating",
        "minimum_usable_daylight_minutes",
        "desired_privacy_rating",
        "maximum_travel_minutes",
    }
)

REQUIRED_TRAVEL_ESTIMATE_FIELDS = frozenset(
    {"segment_id", "origin_label", "minutes", "source_ref", "inferred"}
)


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise RunInputValidationError(f"{context} must be an object")
    return cast("Mapping[str, object]", value)


def _list(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise RunInputValidationError(f"{context} must be an array")
    return cast("list[object]", value)


def _text(value: object, context: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        qualifier = "a string" if allow_empty else "a non-empty string"
        raise RunInputValidationError(f"{context} must be {qualifier}")
    return value


def _integer(value: object, context: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RunInputValidationError(f"{context} must be an integer")
    if minimum is not None and value < minimum:
        raise RunInputValidationError(f"{context} must be at least {minimum}")
    return value


def _optional_integer(value: object, context: str, *, minimum: int = 0) -> int | None:
    if value is None:
        return None
    return _integer(value, context, minimum=minimum)


def _number(value: object, context: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RunInputValidationError(f"{context} must be a number")
    val_float = float(value)
    if minimum is not None and val_float < minimum:
        raise RunInputValidationError(f"{context} must be at least {minimum}")
    return val_float


def _optional_number(value: object, context: str, *, minimum: float = 0.0) -> float | None:
    if value is None:
        return None
    return _number(value, context, minimum=minimum)


def _boolean(value: object, context: str) -> bool:
    if not isinstance(value, bool):
        raise RunInputValidationError(f"{context} must be true or false")
    return value


def _optional_boolean(value: object, context: str) -> bool | None:
    if value is None:
        return None
    return _boolean(value, context)


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


def _string_tuple(value: object, context: str, *, require_items: bool) -> tuple[str, ...]:
    items = _list(value, context)
    if require_items and not items:
        raise RunInputValidationError(f"{context} must contain at least one item")
    return tuple(_text(item, f"{context}[{index}]") for index, item in enumerate(items))


def _timestamp(value: object, context: str) -> datetime:
    raw_value = _text(value, context)
    try:
        timestamp = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RunInputValidationError(f"{context} must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise RunInputValidationError(f"{context} must include a timezone")
    return timestamp


def _condition_snapshot(value: object, context: str) -> ConditionSnapshot:
    condition_obj = _mapping(value, context)
    missing = sorted(REQUIRED_CONDITION_FIELDS.difference(condition_obj))
    if missing:
        raise RunInputValidationError(f"{context} is missing required fields: {', '.join(missing)}")

    try:
        return ConditionSnapshot(
            snapshot_id=_text(condition_obj["snapshot_id"], f"{context}.snapshot_id"),
            applicable_segment_ids=_string_tuple(
                condition_obj["applicable_segment_ids"],
                f"{context}.applicable_segment_ids",
                require_items=True,
            ),
            valid_at=_timestamp(condition_obj["valid_at"], f"{context}.valid_at"),
            tide_stage=_enum_value(TideStage, condition_obj["tide_stage"], f"{context}.tide_stage"),
            severe_weather_warning=_optional_boolean(
                condition_obj["severe_weather_warning"], f"{context}.severe_weather_warning"
            ),
            lightning_or_severe_thunderstorm_risk=_optional_boolean(
                condition_obj["lightning_or_severe_thunderstorm_risk"],
                f"{context}.lightning_or_severe_thunderstorm_risk",
            ),
            footing_safe=_optional_boolean(
                condition_obj["footing_safe"], f"{context}.footing_safe"
            ),
            usable_daylight_minutes=_optional_integer(
                condition_obj["usable_daylight_minutes"], f"{context}.usable_daylight_minutes"
            ),
            wind_speed_kph=_optional_number(
                condition_obj["wind_speed_kph"], f"{context}.wind_speed_kph"
            ),
            gust_speed_kph=_optional_number(
                condition_obj["gust_speed_kph"], f"{context}.gust_speed_kph"
            ),
            data_freshness_minutes=_optional_integer(
                condition_obj["data_freshness_minutes"], f"{context}.data_freshness_minutes"
            ),
            inferred=_boolean(condition_obj["inferred"], f"{context}.inferred"),
            weather_status_verified=_boolean(
                condition_obj["weather_status_verified"], f"{context}.weather_status_verified"
            ),
            footing_status_verified=_boolean(
                condition_obj["footing_status_verified"], f"{context}.footing_status_verified"
            ),
            tide_status_verified=_boolean(
                condition_obj["tide_status_verified"], f"{context}.tide_status_verified"
            ),
            daylight_status_verified=_boolean(
                condition_obj["daylight_status_verified"], f"{context}.daylight_status_verified"
            ),
            weather_source_refs=_string_tuple(
                condition_obj["weather_source_refs"],
                f"{context}.weather_source_refs",
                require_items=False,
            ),
            footing_source_refs=_string_tuple(
                condition_obj["footing_source_refs"],
                f"{context}.footing_source_refs",
                require_items=False,
            ),
            tide_source_refs=_string_tuple(
                condition_obj["tide_source_refs"],
                f"{context}.tide_source_refs",
                require_items=False,
            ),
            daylight_source_refs=_string_tuple(
                condition_obj["daylight_source_refs"],
                f"{context}.daylight_source_refs",
                require_items=False,
            ),
        )
    except ValueError as error:
        raise RunInputValidationError(f"{context}: {error}") from error


def _user_preferences(value: object, context: str) -> UserPreferences:
    prefs_obj = _mapping(value, context)
    missing = sorted(REQUIRED_PREFERENCES_FIELDS.difference(prefs_obj))
    if missing:
        raise RunInputValidationError(f"{context} is missing required fields: {', '.join(missing)}")

    try:
        return UserPreferences(
            skill_level=_enum_value(SkillLevel, prefs_obj["skill_level"], f"{context}.skill_level"),
            require_family_suitable=_boolean(
                prefs_obj["require_family_suitable"], f"{context}.require_family_suitable"
            ),
            minimum_family_suitability=_integer(
                prefs_obj["minimum_family_suitability"],
                f"{context}.minimum_family_suitability",
            ),
            minimum_casting_space_rating=_integer(
                prefs_obj["minimum_casting_space_rating"],
                f"{context}.minimum_casting_space_rating",
            ),
            minimum_usable_daylight_minutes=_integer(
                prefs_obj["minimum_usable_daylight_minutes"],
                f"{context}.minimum_usable_daylight_minutes",
                minimum=0,
            ),
            desired_privacy_rating=_integer(
                prefs_obj["desired_privacy_rating"], f"{context}.desired_privacy_rating"
            ),
            maximum_travel_minutes=_integer(
                prefs_obj["maximum_travel_minutes"],
                f"{context}.maximum_travel_minutes",
                minimum=0,
            ),
        )
    except ValueError as error:
        raise RunInputValidationError(f"{context}: {error}") from error


def _travel_estimate(value: object, context: str) -> TravelEstimate:
    estimate_obj = _mapping(value, context)
    missing = sorted(REQUIRED_TRAVEL_ESTIMATE_FIELDS.difference(estimate_obj))
    if missing:
        raise RunInputValidationError(f"{context} is missing required fields: {', '.join(missing)}")

    try:
        return TravelEstimate(
            segment_id=_text(estimate_obj["segment_id"], f"{context}.segment_id"),
            origin_label=_text(estimate_obj["origin_label"], f"{context}.origin_label"),
            minutes=_integer(estimate_obj["minutes"], f"{context}.minutes", minimum=0),
            source_ref=_text(estimate_obj["source_ref"], f"{context}.source_ref"),
            inferred=_boolean(estimate_obj["inferred"], f"{context}.inferred"),
        )
    except ValueError as error:
        raise RunInputValidationError(f"{context}: {error}") from error


def _travel_estimates(value: object, context: str) -> tuple[TravelEstimate, ...]:
    raw_estimates = _list(value, context)
    if not raw_estimates:
        raise RunInputValidationError(f"{context} must contain at least one travel estimate")

    estimates: list[TravelEstimate] = []
    seen_segment_ids: set[str] = set()
    for index, raw_estimate in enumerate(raw_estimates):
        item_context = f"{context}[{index}]"
        estimate = _travel_estimate(raw_estimate, item_context)
        if estimate.segment_id in seen_segment_ids:
            raise RunInputValidationError(
                f"{item_context}.segment_id duplicates travel estimate for {estimate.segment_id!r}"
            )
        seen_segment_ids.add(estimate.segment_id)
        estimates.append(estimate)
    return tuple(estimates)


def validate_run_input_document(
    document: object,
) -> tuple[ConditionSnapshot, UserPreferences, tuple[TravelEstimate, ...]]:
    """Validate a decoded JSON object into condition, preferences, and travel estimates."""
    root = _mapping(document, "run_input")
    for key in ("condition", "preferences", "travel_estimates"):
        if key not in root:
            raise RunInputValidationError(f"run_input is missing required top-level section: {key}")

    condition = _condition_snapshot(root["condition"], "run_input.condition")
    preferences = _user_preferences(root["preferences"], "run_input.preferences")
    travel_estimates = _travel_estimates(root["travel_estimates"], "run_input.travel_estimates")

    # Enforce cross-field consistency
    origins = {estimate.origin_label for estimate in travel_estimates}
    if len(origins) > 1:
        raise RunInputValidationError(
            "run_input.travel_estimates must all use the same origin_label"
        )

    applicable_ids = set(condition.applicable_segment_ids)
    unknown_travel_ids = {
        estimate.segment_id
        for estimate in travel_estimates
        if estimate.segment_id not in applicable_ids
    }
    if unknown_travel_ids:
        unknown_str = ", ".join(sorted(unknown_travel_ids))
        raise RunInputValidationError(
            "run_input.travel_estimates reference segment IDs not in condition "
            f"applicable_segment_ids: {unknown_str}"
        )

    return condition, preferences, travel_estimates


def load_run_input(
    path: str | Path,
) -> tuple[ConditionSnapshot, UserPreferences, tuple[TravelEstimate, ...]]:
    """Read and validate a run-input JSON document with actionable error messages."""
    input_path = Path(path)
    try:
        with input_path.open(encoding="utf-8") as input_file:
            document = json.load(input_file)
    except OSError as error:
        raise RunInputValidationError(
            f"could not read run input {input_path}: {error.strerror or error}"
        ) from error
    except UnicodeError as error:
        raise RunInputValidationError(
            f"run input {input_path} is not valid UTF-8: {error}"
        ) from error
    except json.JSONDecodeError as error:
        raise RunInputValidationError(
            f"run input {input_path} is not valid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    return validate_run_input_document(document)
