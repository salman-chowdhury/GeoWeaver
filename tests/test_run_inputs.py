"""Validation and orchestration tests for file-supplied recommendation inputs."""

import json
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from geoweaver.data.run_inputs import (
    RunInputValidationError,
    load_condition_snapshots,
    load_travel_estimates,
    load_trip_request,
)
from geoweaver.domain.enums import DataClassification, IntendedActivity, SkillLevel
from geoweaver.domain.models import ShorelineSegment
from geoweaver.reports.json_report import render_json, report_document
from geoweaver.reports.markdown_report import render_markdown
from geoweaver.services.recommendation import rank_trip

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_TRIP = PROJECT_ROOT / "data" / "trips" / "demo_trip.json"
DEMO_CONDITIONS = PROJECT_ROOT / "data" / "conditions" / "demo_conditions.json"
DEMO_TRAVEL = PROJECT_ROOT / "data" / "travel" / "demo_travel.json"


def _document(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(tmp_path: Path, name: str, document: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_valid_trip_configuration() -> None:
    trip = load_trip_request(DEMO_TRIP)

    assert trip.origin_label == "Fictional Demo Origin"
    assert trip.target_datetime.utcoffset() is not None
    assert trip.skill_level is SkillLevel.NOVICE
    assert trip.intended_activity is IntendedActivity.CAST_NET_FISHING
    assert trip.data_classification is DataClassification.SYNTHETIC_DEMO
    assert trip.preferences.maximum_travel_minutes == 45


def test_trip_rejects_timezone_naive_target(tmp_path: Path) -> None:
    document = _document(DEMO_TRIP)
    document["target_datetime"] = "2026-01-15T06:00:00"

    with pytest.raises(RunInputValidationError, match="must include a timezone"):
        load_trip_request(_write_json(tmp_path, "trip.json", document))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("minimum_family_rating", 6),
        ("desired_privacy_rating", -1),
        ("minimum_casting_space_rating", 6),
        ("maximum_travel_minutes", 1441),
        ("minimum_usable_daylight_minutes", -1),
    ),
)
def test_trip_rejects_invalid_preference_ranges(tmp_path: Path, field: str, value: int) -> None:
    document = _document(DEMO_TRIP)
    document[field] = value

    with pytest.raises(RunInputValidationError, match=field):
        load_trip_request(_write_json(tmp_path, "trip.json", document))


def test_conditions_require_applicability(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_CONDITIONS)
    condition = document["conditions"][0]
    del condition["applicability"]

    with pytest.raises(RunInputValidationError, match="applicability"):
        load_condition_snapshots(
            _write_json(tmp_path, "conditions.json", document), demo_segments, trip
        )


def test_conditions_reject_overlapping_location_scopes(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_CONDITIONS)
    duplicate = deepcopy(document["conditions"][0])
    duplicate["snapshot_id"] = "overlapping-snapshot"
    document["conditions"].append(duplicate)

    with pytest.raises(RunInputValidationError, match="both apply to segment"):
        load_condition_snapshots(
            _write_json(tmp_path, "conditions.json", document), demo_segments, trip
        )


def test_condition_waterway_and_segment_scopes_resolve_exactly(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_CONDITIONS)
    base = document["conditions"][0]
    estuary = deepcopy(base)
    estuary["snapshot_id"] = "imaginary-estuary-conditions"
    estuary["applicability"] = {
        "scope_type": "waterway",
        "scope_id": "Imaginary Estuary",
    }
    creek = deepcopy(base)
    creek["snapshot_id"] = "model-creek-conditions"
    creek["applicability"] = {
        "scope_type": "waterway",
        "scope_id": "Model Creek",
    }
    inlet = deepcopy(base)
    inlet["snapshot_id"] = "narrow-segment-conditions"
    inlet["applicability"] = {
        "scope_type": "segment",
        "scope_id": "demo-narrow-mud-edge",
    }
    document["conditions"] = [estuary, creek, inlet]

    conditions = load_condition_snapshots(
        _write_json(tmp_path, "conditions.json", document), demo_segments, trip
    )

    resolved = {item.snapshot_id: item.applicable_segment_ids for item in conditions}
    assert resolved == {
        "imaginary-estuary-conditions": (
            "demo-alpha-gutter",
            "demo-beta-sandbar",
        ),
        "model-creek-conditions": (
            "demo-closed-reach",
            "demo-unknown-access",
        ),
        "narrow-segment-conditions": ("demo-narrow-mud-edge",),
    }
    run = rank_trip(
        demo_segments,
        trip,
        conditions,
        load_travel_estimates(DEMO_TRAVEL, demo_segments, trip),
    )
    report = report_document(run)

    assert report["condition_snapshot"] is None
    assert len(report["condition_snapshots"]) == 3
    assert {item["condition_snapshot_id"] for item in report["recommendations"]} == set(resolved)


def test_blank_condition_provenance_is_rejected(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_CONDITIONS)
    document["conditions"][0]["source_refs"]["weather"] = [""]

    with pytest.raises(RunInputValidationError, match="non-empty string"):
        load_condition_snapshots(
            _write_json(tmp_path, "conditions.json", document), demo_segments, trip
        )


def test_inferred_tide_source_applicability_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_CONDITIONS)
    document["conditions"][0]["tide_source"]["evidence_state"] = "inferred"
    conditions = load_condition_snapshots(
        _write_json(tmp_path, "conditions.json", document), demo_segments, trip
    )
    travel = load_travel_estimates(DEMO_TRAVEL, demo_segments, trip)

    run = rank_trip(demo_segments, trip, conditions, travel)

    assert all(
        "tide_condition" in {failure.gate for failure in item.constraints.failures}
        for item in run.recommendations
    )


def test_unknown_travel_segment_id_is_rejected(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_TRAVEL)
    document["estimates"][0]["segment_id"] = "unknown-segment"

    with pytest.raises(RunInputValidationError, match="unknown segment ID"):
        load_travel_estimates(_write_json(tmp_path, "travel.json", document), demo_segments, trip)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("source_ref", "", "non-empty string"),
        ("estimated_travel_minutes", -1, "at least 0"),
    ),
)
def test_invalid_travel_values_are_rejected(
    demo_segments: tuple[ShorelineSegment, ...],
    tmp_path: Path,
    field: str,
    value: str | int,
    message: str,
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_TRAVEL)
    document["estimates"][0][field] = value

    with pytest.raises(RunInputValidationError, match=message):
        load_travel_estimates(_write_json(tmp_path, "travel.json", document), demo_segments, trip)


def test_duplicate_travel_entries_are_rejected(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_TRAVEL)
    document["estimates"].append(deepcopy(document["estimates"][0]))

    with pytest.raises(RunInputValidationError, match="duplicate travel estimate"):
        load_travel_estimates(_write_json(tmp_path, "travel.json", document), demo_segments, trip)


def test_file_inputs_produce_deterministic_results(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip_document = _document(DEMO_TRIP)
    del trip_document["run_id"]
    trip = load_trip_request(_write_json(tmp_path, "trip.json", trip_document))
    conditions = load_condition_snapshots(DEMO_CONDITIONS, demo_segments, trip)
    travel = load_travel_estimates(DEMO_TRAVEL, demo_segments, trip)

    first = rank_trip(demo_segments, trip, conditions, travel)
    second = rank_trip(
        tuple(reversed(demo_segments)),
        trip,
        tuple(reversed(conditions)),
        tuple(reversed(travel)),
    )

    assert first.run_id == second.run_id
    assert render_json(first) == render_json(second)

    changed_condition = replace(
        conditions[0],
        retrieved_at=conditions[0].retrieved_at - timedelta(minutes=1),
        data_freshness_minutes=conditions[0].data_freshness_minutes + 1,
    )
    changed = rank_trip(demo_segments, trip, (changed_condition,), travel)
    assert changed.run_id != first.run_id


def test_file_reports_include_trip_and_input_provenance(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    conditions = load_condition_snapshots(DEMO_CONDITIONS, demo_segments, trip)
    travel = load_travel_estimates(DEMO_TRAVEL, demo_segments, trip)
    run = rank_trip(demo_segments, trip, conditions, travel)

    document = report_document(run)
    markdown = render_markdown(run)

    assert document["trip_request"] == {
        "run_id": "demo-weekend-run-v0.1",
        "origin_label": "Fictional Demo Origin",
        "target_datetime": "2026-01-15T06:00:00+00:00",
        "maximum_travel_minutes": 45,
        "skill_level": "novice",
        "family_suitability_required": True,
        "minimum_family_rating": 3,
        "desired_privacy_rating": 3,
        "minimum_casting_space_rating": 3,
        "intended_activity": "cast_net_fishing",
        "minimum_usable_daylight_minutes": 60,
        "notes": "Fictional values for deterministic tests and documentation only.",
        "data_classification": "synthetic_demo",
    }
    condition = document["condition_snapshots"][0]
    assert condition["retrieved_at"] == "2026-01-15T05:00:00+00:00"
    assert condition["source_refs"]
    assert condition["tide_source_applicability"] == {
        "source_location_id": "demo-tide-station-v0.1",
        "source_location_label": "Fictional station for the synthetic catalogue",
        "distance_to_scope_km": 0.0,
        "assignment_method": "manually_reviewed",
        "applicability_source_ref": "demo://synthetic/tide/v0.1",
        "retrieved_at": "2026-01-15T05:00:00+00:00",
        "evidence_state": "verified",
    }
    assert document["travel_estimates"][0]["source_ref"]
    assert document["travel_estimates"][0]["retrieved_at"]
    assert document["recommendations"][0]["eligible"] is True
    assert "missing_or_stale_information" in document["recommendations"][0]
    assert "## Trip request" in markdown
    assert "## Condition snapshots" in markdown
    assert "## Manual travel estimates" in markdown
    assert "## Run limitations" in markdown


def test_manual_input_classification_is_not_reported_as_demonstration(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip_document = _document(DEMO_TRIP)
    condition_document = _document(DEMO_CONDITIONS)
    travel_document = _document(DEMO_TRAVEL)
    for document in (trip_document, condition_document, travel_document):
        document["data_classification"] = "manual_user_supplied"
    trip_document["run_id"] = "manual-test-run"
    trip = load_trip_request(_write_json(tmp_path, "trip.json", trip_document))
    conditions = load_condition_snapshots(
        _write_json(tmp_path, "conditions.json", condition_document), demo_segments, trip
    )
    travel = load_travel_estimates(
        _write_json(tmp_path, "travel.json", travel_document), demo_segments, trip
    )

    run = rank_trip(demo_segments, trip, conditions, travel)
    markdown = render_markdown(run)

    assert markdown.startswith("# CastNetGPT v0.1 Ranking")
    assert "manually supplied" in run.demonstration_notice
    assert all(
        "demonstration" not in item.lower()
        for recommendation in run.recommendations
        for item in recommendation.missing_or_stale_information
    )


def test_inferred_manual_conditions_fail_critical_gates(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip_document = _document(DEMO_TRIP)
    condition_document = _document(DEMO_CONDITIONS)
    travel_document = _document(DEMO_TRAVEL)
    for document in (trip_document, condition_document, travel_document):
        document["data_classification"] = "manual_user_supplied"
    condition_document["conditions"][0]["evidence_state"] = "inferred"
    trip = load_trip_request(_write_json(tmp_path, "trip.json", trip_document))
    conditions = load_condition_snapshots(
        _write_json(tmp_path, "conditions.json", condition_document), demo_segments, trip
    )
    travel = load_travel_estimates(
        _write_json(tmp_path, "travel.json", travel_document), demo_segments, trip
    )

    run = rank_trip(demo_segments, trip, conditions, travel)

    assert not any(item.eligibility for item in run.recommendations)
    assert all(
        {"severe_weather", "tide_condition", "safe_footing", "usable_daylight"}
        <= {failure.gate for failure in item.constraints.failures}
        for item in run.recommendations
    )
    assert all(
        not condition.weather_status_verified
        and not condition.footing_status_verified
        and not condition.tide_status_verified
        and not condition.daylight_status_verified
        for condition in conditions
    )


def test_explicit_unknown_condition_does_not_use_synthetic_fallback(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    document = _document(DEMO_CONDITIONS)
    document["conditions"][0]["sustained_wind_kph"] = None
    conditions = load_condition_snapshots(
        _write_json(tmp_path, "conditions.json", document), demo_segments, trip
    )
    travel = load_travel_estimates(DEMO_TRAVEL, demo_segments, trip)

    run = rank_trip(demo_segments, trip, conditions, travel)

    assert all(not recommendation.eligibility for recommendation in run.recommendations)
    assert all(
        "severe_weather" in {failure.gate for failure in recommendation.constraints.failures}
        for recommendation in run.recommendations
    )
    assert all(
        "Wind speed is missing." in recommendation.missing_or_stale_information
        for recommendation in run.recommendations
    )


def test_omitted_travel_estimate_fails_only_that_segment_closed(
    demo_segments: tuple[ShorelineSegment, ...], tmp_path: Path
) -> None:
    trip = load_trip_request(DEMO_TRIP)
    conditions = load_condition_snapshots(DEMO_CONDITIONS, demo_segments, trip)
    document = _document(DEMO_TRAVEL)
    omitted_id = document["estimates"][0]["segment_id"]
    document["estimates"] = document["estimates"][1:]
    travel = load_travel_estimates(
        _write_json(tmp_path, "travel.json", document), demo_segments, trip
    )

    run = rank_trip(demo_segments, trip, conditions, travel)
    result = next(item for item in run.recommendations if item.segment_id == omitted_id)

    assert not result.eligibility
    assert "Travel time is missing." in result.missing_or_stale_information
    assert result.travel_time_minutes is None
