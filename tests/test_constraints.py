"""Tests for every CastNetGPT v0.1 hard gate."""

from dataclasses import replace
from datetime import timedelta

import pytest

from geoweaver.demo import (
    demonstration_condition,
    demonstration_preferences,
    demonstration_travel_estimates,
)
from geoweaver.domain.enums import (
    ActivityPermissionStatus,
    BankSlopeClass,
    PublicAccessState,
    RestrictionStatus,
    TidalStatus,
)
from geoweaver.domain.models import ShorelineSegment, TravelEstimate
from geoweaver.scoring.constraints import (
    MAX_CRITICAL_SEGMENT_AGE,
    MAX_SAFE_GUST_KPH,
    MAX_SAFE_SUSTAINED_WIND_KPH,
    evaluate_constraints,
)


def _segment_by_id(segments: tuple[ShorelineSegment, ...], segment_id: str) -> ShorelineSegment:
    return next(segment for segment in segments if segment.segment_id == segment_id)


def _travel_for(segment_id: str) -> TravelEstimate:
    return next(
        estimate
        for estimate in demonstration_travel_estimates()
        if estimate.segment_id == segment_id
    )


def test_complete_public_segment_is_eligible(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = _segment_by_id(demo_segments, "demo-alpha-gutter")

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert result.eligible
    assert not result.failures


@pytest.mark.parametrize(
    "status",
    [PublicAccessState.UNKNOWN, PublicAccessState.PROHIBITED, PublicAccessState.RESTRICTED],
)
def test_unknown_or_prohibited_access_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...], status: PublicAccessState
) -> None:
    segment = _segment_by_id(demo_segments, "demo-alpha-gutter")
    segment = replace(segment, access=replace(segment.access, public_access_status=status))

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert not result.eligible
    assert "public_access" in {failure.gate for failure in result.failures}


def test_active_legal_closure_is_a_hard_gate(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = _segment_by_id(demo_segments, "demo-closed-reach")

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert not result.eligible
    assert "active_legal_closure" in {failure.gate for failure in result.failures}


def test_unknown_restriction_status_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = _segment_by_id(demo_segments, "demo-alpha-gutter")
    restriction = replace(segment.restrictions[0], status=RestrictionStatus.UNKNOWN)
    segment = replace(segment, restrictions=(restriction,))

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert not result.eligible
    assert "active_legal_closure" in {failure.gate for failure in result.failures}


@pytest.mark.parametrize(
    ("condition_changes", "expected_gate"),
    [
        ({"severe_weather_warning": True}, "severe_weather"),
        ({"severe_weather_warning": None}, "severe_weather"),
        ({"footing_safe": False}, "safe_footing"),
        ({"footing_safe": None}, "safe_footing"),
        ({"weather_status_verified": False}, "severe_weather"),
        ({"footing_status_verified": False}, "safe_footing"),
        ({"data_freshness_minutes": 121}, "severe_weather"),
        ({"weather_source_refs": ()}, "severe_weather"),
        ({"usable_daylight_minutes": 30}, "usable_daylight"),
        ({"usable_daylight_minutes": None}, "usable_daylight"),
        ({"tide_status_verified": False}, "tide_condition"),
        ({"tide_source_refs": ()}, "tide_condition"),
        ({"daylight_status_verified": False}, "usable_daylight"),
        ({"daylight_source_refs": ()}, "usable_daylight"),
    ],
)
def test_condition_hard_gates(
    demo_segments: tuple[ShorelineSegment, ...],
    condition_changes: dict[str, object],
    expected_gate: str,
) -> None:
    segment = _segment_by_id(demo_segments, "demo-alpha-gutter")
    condition = replace(demonstration_condition(), **condition_changes)

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )

    assert not result.eligible
    assert expected_gate in {failure.gate for failure in result.failures}


def test_casting_space_and_family_requirements_are_hard_gates(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = _segment_by_id(demo_segments, "demo-narrow-mud-edge")

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )
    failed_gates = {failure.gate for failure in result.failures}

    assert "casting_space" in failed_gates
    assert "family_suitability" in failed_gates


def test_missing_critical_safety_and_legal_information_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = _segment_by_id(demo_segments, "demo-narrow-mud-edge")

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )
    failed_gates = {failure.gate for failure in result.failures}

    assert "legal_information" in failed_gates
    assert "critical_safety_information" in failed_gates


@pytest.mark.parametrize(
    ("changes", "expected_gate"),
    [
        (
            {"activity_permission_status": ActivityPermissionStatus.PROHIBITED},
            "activity_permission",
        ),
        ({"activity_permission_status": ActivityPermissionStatus.UNKNOWN}, "activity_permission"),
        ({"tidal_status": TidalStatus.NON_TIDAL}, "tidal_eligibility"),
        ({"tidal_status": TidalStatus.UNKNOWN}, "tidal_eligibility"),
        ({"health_advisory_status": RestrictionStatus.ACTIVE}, "health_advisory"),
        ({"health_advisory_status": RestrictionStatus.UNKNOWN}, "health_advisory"),
    ],
)
def test_activity_tidal_and_health_statuses_fail_closed(
    demo_segments: tuple[ShorelineSegment, ...],
    changes: dict[str, object],
    expected_gate: str,
) -> None:
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    if "health_advisory_status" in changes:
        changes = {
            **changes,
            "health_advisory_evidence": replace(
                original.health_advisory_evidence,
                status=changes["health_advisory_status"],
            ),
        }
    segment = replace(original, **changes)

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert not result.eligible
    assert expected_gate in {failure.gate for failure in result.failures}


@pytest.mark.parametrize(
    "segment_changes",
    [
        {"bank_slope_class": BankSlopeClass.STEEP},
        {"bank_slope_class": BankSlopeClass.UNKNOWN},
    ],
)
def test_unsafe_or_unknown_terrain_fails_footing_gate(
    demo_segments: tuple[ShorelineSegment, ...], segment_changes: dict[str, object]
) -> None:
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    segment = replace(original, **segment_changes)

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert "safe_footing" in {failure.gate for failure in result.failures}


def test_excessive_mud_fails_footing_gate(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    segment = replace(original, environmental=replace(original.environmental, mud_risk=4))

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert "safe_footing" in {failure.gate for failure in result.failures}


def test_missing_or_over_limit_travel_time_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = _segment_by_id(demo_segments, "demo-alpha-gutter")
    preferences = demonstration_preferences()
    over_limit = replace(
        _travel_for(segment.segment_id), minutes=preferences.maximum_travel_minutes + 1
    )

    missing = evaluate_constraints(segment, demonstration_condition(), preferences, None)
    excessive = evaluate_constraints(segment, demonstration_condition(), preferences, over_limit)

    assert "travel_time" in {failure.gate for failure in missing.failures}
    assert "travel_time" in {failure.gate for failure in excessive.failures}


def test_string_active_restriction_is_coerced_and_cannot_bypass_gate(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = _segment_by_id(demo_segments, "demo-alpha-gutter")
    restriction = replace(segment.restrictions[0], status="active")
    segment = replace(segment, restrictions=(restriction,))

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert restriction.status is RestrictionStatus.ACTIVE
    assert "active_legal_closure" in {failure.gate for failure in result.failures}


def test_string_steep_slope_is_coerced_and_cannot_bypass_gate(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    segment = replace(original, bank_slope_class="steep")

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert segment.bank_slope_class is BankSlopeClass.STEEP
    assert "safe_footing" in {failure.gate for failure in result.failures}


@pytest.mark.parametrize(
    "condition_changes",
    [
        {"wind_speed_kph": MAX_SAFE_SUSTAINED_WIND_KPH + 0.1},
        {"gust_speed_kph": MAX_SAFE_GUST_KPH + 0.1},
        {"lightning_or_severe_thunderstorm_risk": True},
        {"lightning_or_severe_thunderstorm_risk": None},
        {"wind_speed_kph": None},
        {"gust_speed_kph": None},
    ],
)
def test_dangerous_or_unknown_weather_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...], condition_changes: dict[str, object]
) -> None:
    segment = _segment_by_id(demo_segments, "demo-alpha-gutter")
    condition = replace(demonstration_condition(), **condition_changes)

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )

    assert "severe_weather" in {failure.gate for failure in result.failures}


def test_weather_threshold_boundaries_are_eligible(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = _segment_by_id(demo_segments, "demo-alpha-gutter")
    condition = replace(
        demonstration_condition(),
        wind_speed_kph=MAX_SAFE_SUSTAINED_WIND_KPH,
        gust_speed_kph=MAX_SAFE_GUST_KPH,
    )

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )

    assert result.eligible


def test_zero_casting_space_fails_even_when_user_minimum_is_zero(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    segment = replace(
        original,
        access=replace(original.access, casting_space_rating=0),
    )
    preferences = replace(demonstration_preferences(), minimum_casting_space_rating=0)

    result = evaluate_constraints(
        segment, demonstration_condition(), preferences, _travel_for(segment.segment_id)
    )

    assert "casting_space" in {failure.gate for failure in result.failures}


def test_expired_active_restriction_does_not_gate_current_run(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    restriction = replace(
        original.restrictions[0],
        status=RestrictionStatus.ACTIVE,
        effective_from=condition.valid_at - timedelta(hours=2),
        effective_to=condition.valid_at - timedelta(hours=1),
    )
    segment = replace(original, restrictions=(restriction,))

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )

    assert result.eligible


def test_future_dated_restriction_evidence_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    restriction = replace(
        original.restrictions[0],
        retrieved_at=condition.valid_at + timedelta(microseconds=1),
    )
    segment = replace(original, restrictions=(restriction,))

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )

    assert "active_legal_closure" in {failure.gate for failure in result.failures}


def test_health_advisory_evidence_must_apply_at_run_time(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    health_evidence = replace(
        original.health_advisory_evidence,
        effective_from=condition.valid_at - timedelta(hours=2),
        effective_to=condition.valid_at - timedelta(hours=1),
    )
    segment = replace(original, health_advisory_evidence=health_evidence)

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )

    assert "health_advisory" in {failure.gate for failure in result.failures}


@pytest.mark.parametrize(
    ("age", "expected_eligible"),
    [
        (MAX_CRITICAL_SEGMENT_AGE - timedelta(microseconds=1), True),
        (MAX_CRITICAL_SEGMENT_AGE, True),
        (MAX_CRITICAL_SEGMENT_AGE + timedelta(microseconds=1), False),
    ],
)
def test_record_freshness_uses_complete_timedelta_boundary(
    demo_segments: tuple[ShorelineSegment, ...],
    age: timedelta,
    expected_eligible: bool,
) -> None:
    condition = demonstration_condition()
    original = _segment_by_id(demo_segments, "demo-alpha-gutter")
    segment = replace(original, last_updated=condition.valid_at - age)

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )

    failed_gates = {failure.gate for failure in result.failures}
    assert result.eligible is expected_eligible
    assert ("critical_record_freshness" in failed_gates) is (not expected_eligible)
