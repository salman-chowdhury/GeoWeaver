"""Tests for run-input JSON document loading and validation."""

from pathlib import Path

import pytest

from geoweaver.data import RunInputValidationError, load_run_input, validate_run_input_document
from geoweaver.demo import (
    demonstration_condition,
    demonstration_preferences,
    demonstration_travel_estimates,
)
from geoweaver.domain.enums import SkillLevel, TideStage


@pytest.fixture
def valid_run_input_document() -> dict:
    """Return a valid synthetic run-input dictionary."""
    return {
        "condition": {
            "snapshot_id": "demo-conditions-v0.1",
            "applicable_segment_ids": [
                "demo-alpha-gutter",
                "demo-beta-sandbar",
                "demo-closed-reach",
                "demo-unknown-access",
                "demo-narrow-mud-edge",
            ],
            "valid_at": "2026-01-15T06:00:00Z",
            "tide_stage": "rising",
            "severe_weather_warning": False,
            "lightning_or_severe_thunderstorm_risk": False,
            "footing_safe": True,
            "usable_daylight_minutes": 120,
            "wind_speed_kph": 14.0,
            "gust_speed_kph": 22.0,
            "data_freshness_minutes": 60,
            "inferred": True,
            "weather_status_verified": True,
            "footing_status_verified": True,
            "tide_status_verified": True,
            "daylight_status_verified": True,
            "weather_source_refs": ["demo://synthetic/weather/v0.1"],
            "footing_source_refs": ["demo://synthetic/footing/v0.1"],
            "tide_source_refs": ["demo://synthetic/tide/v0.1"],
            "daylight_source_refs": ["demo://synthetic/daylight/v0.1"],
        },
        "preferences": {
            "skill_level": "novice",
            "require_family_suitable": True,
            "minimum_family_suitability": 3,
            "minimum_casting_space_rating": 3,
            "minimum_usable_daylight_minutes": 60,
            "desired_privacy_rating": 3,
            "maximum_travel_minutes": 45,
        },
        "travel_estimates": [
            {
                "segment_id": "demo-alpha-gutter",
                "origin_label": "Fictional Demo Origin",
                "minutes": 20,
                "source_ref": "demo://synthetic/travel-times/v0.1",
                "inferred": True,
            },
            {
                "segment_id": "demo-beta-sandbar",
                "origin_label": "Fictional Demo Origin",
                "minutes": 35,
                "source_ref": "demo://synthetic/travel-times/v0.1",
                "inferred": True,
            },
            {
                "segment_id": "demo-closed-reach",
                "origin_label": "Fictional Demo Origin",
                "minutes": 15,
                "source_ref": "demo://synthetic/travel-times/v0.1",
                "inferred": True,
            },
            {
                "segment_id": "demo-unknown-access",
                "origin_label": "Fictional Demo Origin",
                "minutes": 25,
                "source_ref": "demo://synthetic/travel-times/v0.1",
                "inferred": True,
            },
            {
                "segment_id": "demo-narrow-mud-edge",
                "origin_label": "Fictional Demo Origin",
                "minutes": 50,
                "source_ref": "demo://synthetic/travel-times/v0.1",
                "inferred": True,
            },
        ],
    }


def test_validate_valid_run_input_document(valid_run_input_document: dict) -> None:
    condition, preferences, travel = validate_run_input_document(valid_run_input_document)

    assert condition == demonstration_condition()
    assert preferences == demonstration_preferences()
    assert travel == demonstration_travel_estimates()


def test_load_template_run_input_file() -> None:
    template_path = Path("data/templates/run_input.template.json")
    condition, preferences, travel = load_run_input(template_path)

    assert condition.snapshot_id == "template-conditions-v0.1"
    assert condition.tide_stage == TideStage.RISING
    assert preferences.skill_level == SkillLevel.NOVICE
    assert len(travel) == 5


def test_load_nonexistent_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "nonexistent.json"
    with pytest.raises(RunInputValidationError, match="could not read run input"):
        load_run_input(missing_path)


def test_load_invalid_json(tmp_path: Path) -> None:
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(RunInputValidationError, match="not valid JSON"):
        load_run_input(bad_json)


def test_load_invalid_utf8(tmp_path: Path) -> None:
    bad_utf8 = tmp_path / "bad_utf8.json"
    bad_utf8.write_bytes(b"\x80\x81")
    with pytest.raises(RunInputValidationError, match="not valid UTF-8"):
        load_run_input(bad_utf8)


def test_not_a_mapping() -> None:
    with pytest.raises(RunInputValidationError, match="run_input must be an object"):
        validate_run_input_document([])


def test_missing_top_level_section(valid_run_input_document: dict) -> None:
    del valid_run_input_document["preferences"]
    with pytest.raises(
        RunInputValidationError,
        match="run_input is missing required top-level section: preferences",
    ):
        validate_run_input_document(valid_run_input_document)


def test_missing_condition_field(valid_run_input_document: dict) -> None:
    del valid_run_input_document["condition"]["tide_stage"]
    with pytest.raises(
        RunInputValidationError,
        match="run_input.condition is missing required fields: tide_stage",
    ):
        validate_run_input_document(valid_run_input_document)


def test_invalid_enum_value(valid_run_input_document: dict) -> None:
    valid_run_input_document["condition"]["tide_stage"] = "tsunami"
    with pytest.raises(
        RunInputValidationError, match="run_input.condition.tide_stage has unsupported value"
    ):
        validate_run_input_document(valid_run_input_document)


def test_naive_timestamp(valid_run_input_document: dict) -> None:
    valid_run_input_document["condition"]["valid_at"] = "2026-01-15T06:00:00"
    with pytest.raises(
        RunInputValidationError, match="run_input.condition.valid_at must include a timezone"
    ):
        validate_run_input_document(valid_run_input_document)


def test_invalid_timestamp_string(valid_run_input_document: dict) -> None:
    valid_run_input_document["condition"]["valid_at"] = "not-a-timestamp"
    with pytest.raises(
        RunInputValidationError, match="run_input.condition.valid_at must be an ISO 8601 timestamp"
    ):
        validate_run_input_document(valid_run_input_document)


def test_duplicate_travel_estimates(valid_run_input_document: dict) -> None:
    valid_run_input_document["travel_estimates"].append(
        valid_run_input_document["travel_estimates"][0]
    )
    with pytest.raises(
        RunInputValidationError, match="duplicates travel estimate for 'demo-alpha-gutter'"
    ):
        validate_run_input_document(valid_run_input_document)


def test_empty_travel_estimates(valid_run_input_document: dict) -> None:
    valid_run_input_document["travel_estimates"] = []
    with pytest.raises(
        RunInputValidationError, match="run_input.travel_estimates must contain at least one"
    ):
        validate_run_input_document(valid_run_input_document)


def test_blank_string_field(valid_run_input_document: dict) -> None:
    valid_run_input_document["condition"]["snapshot_id"] = "   "
    with pytest.raises(
        RunInputValidationError, match="run_input.condition.snapshot_id must be a non-empty string"
    ):
        validate_run_input_document(valid_run_input_document)


def test_negative_numeric_field(valid_run_input_document: dict) -> None:
    valid_run_input_document["preferences"]["maximum_travel_minutes"] = -10
    with pytest.raises(
        RunInputValidationError,
        match="run_input.preferences.maximum_travel_minutes must be at least 0",
    ):
        validate_run_input_document(valid_run_input_document)


def test_invalid_type_field(valid_run_input_document: dict) -> None:
    valid_run_input_document["preferences"]["require_family_suitable"] = "yes"
    with pytest.raises(
        RunInputValidationError,
        match="run_input.preferences.require_family_suitable must be true or false",
    ):
        validate_run_input_document(valid_run_input_document)


def test_inconsistent_origin_labels(valid_run_input_document: dict) -> None:
    valid_run_input_document["travel_estimates"][1]["origin_label"] = "Different Origin"
    with pytest.raises(
        RunInputValidationError,
        match="run_input.travel_estimates must all use the same origin_label",
    ):
        validate_run_input_document(valid_run_input_document)


def test_travel_estimate_unknown_segment_id(valid_run_input_document: dict) -> None:
    valid_run_input_document["travel_estimates"][0]["segment_id"] = "unknown-segment"
    with pytest.raises(
        RunInputValidationError,
        match="reference segment IDs not in condition applicable_segment_ids: unknown-segment",
    ):
        validate_run_input_document(valid_run_input_document)


def test_blank_source_reference_in_condition(valid_run_input_document: dict) -> None:
    valid_run_input_document["condition"]["weather_source_refs"] = ["  "]
    with pytest.raises(
        RunInputValidationError,
        match="run_input.condition.weather_source_refs\\[0\\] must be a non-empty string",
    ):
        validate_run_input_document(valid_run_input_document)


def test_blank_source_reference_in_travel_estimate(valid_run_input_document: dict) -> None:
    valid_run_input_document["travel_estimates"][0]["source_ref"] = ""
    with pytest.raises(
        RunInputValidationError,
        match="run_input.travel_estimates\\[0\\].source_ref must be a non-empty string",
    ):
        validate_run_input_document(valid_run_input_document)


def test_invalid_source_reference_type(valid_run_input_document: dict) -> None:
    valid_run_input_document["condition"]["weather_source_refs"] = [123]
    with pytest.raises(
        RunInputValidationError,
        match="run_input.condition.weather_source_refs\\[0\\] must be a non-empty string",
    ):
        validate_run_input_document(valid_run_input_document)
