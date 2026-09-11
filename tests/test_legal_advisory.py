"""M1.6 regression tests: legal, closure, and health-advisory evidence is operational.

Covers the behaviours documented in ``docs/12_legal_advisory_evidence.md``:
active / expired / future / unknown / contradictory evidence, effective-period
boundaries, retrieval-timestamp direction, the score-never-overrides rule, and
report naming of the relevant evidence. All fixtures are synthetic.
"""

from dataclasses import replace
from datetime import timedelta

from geoweaver.demo import (
    demonstration_condition,
    demonstration_preferences,
    demonstration_travel_estimates,
)
from geoweaver.domain.enums import RestrictionStatus
from geoweaver.domain.models import ShorelineSegment
from geoweaver.reports.json_report import report_document
from geoweaver.reports.markdown_report import render_markdown
from geoweaver.scoring.constraints import evaluate_constraints
from geoweaver.scoring.scorer import rank_segments


def _alpha(segments: tuple[ShorelineSegment, ...]) -> ShorelineSegment:
    return next(segment for segment in segments if segment.segment_id == "demo-alpha-gutter")


def _travel_for(segment_id: str):
    return next(
        estimate
        for estimate in demonstration_travel_estimates()
        if estimate.segment_id == segment_id
    )


def test_active_applicable_restriction_gates_and_names_reason(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _alpha(demo_segments)
    restriction = replace(
        original.restrictions[0],
        restriction_id="synthetic-active-closure-01",
        status=RestrictionStatus.ACTIVE,
        reason="Synthetic closure instrument C-01 applies at the run time.",
        effective_from=condition.valid_at - timedelta(hours=2),
        effective_to=condition.valid_at + timedelta(hours=2),
    )
    segment = replace(original, restrictions=(restriction,))

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )
    failures = {failure.gate: failure.reason for failure in result.failures}

    assert not result.eligible
    assert "active_legal_closure" in failures
    assert "Synthetic closure instrument C-01" in failures["active_legal_closure"]


def test_future_active_restriction_is_not_yet_in_force(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _alpha(demo_segments)
    restriction = replace(
        original.restrictions[0],
        status=RestrictionStatus.ACTIVE,
        effective_from=condition.valid_at + timedelta(hours=1),
        effective_to=condition.valid_at + timedelta(hours=3),
    )
    segment = replace(original, restrictions=(restriction,))

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )

    assert result.eligible


def test_open_ended_active_restriction_gates(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _alpha(demo_segments)
    restriction = replace(
        original.restrictions[0],
        status=RestrictionStatus.ACTIVE,
        reason="Synthetic open-ended closure with no stated bounds.",
        effective_from=None,
        effective_to=None,
    )
    segment = replace(original, restrictions=(restriction,))

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert not result.eligible
    assert "active_legal_closure" in {failure.gate for failure in result.failures}


def test_effective_window_boundaries_are_inclusive(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _alpha(demo_segments)

    at_start = replace(
        original.restrictions[0],
        status=RestrictionStatus.ACTIVE,
        effective_from=condition.valid_at,
        effective_to=condition.valid_at + timedelta(hours=1),
    )
    at_end = replace(
        original.restrictions[0],
        status=RestrictionStatus.ACTIVE,
        effective_from=condition.valid_at - timedelta(hours=1),
        effective_to=condition.valid_at,
    )
    just_expired = replace(
        original.restrictions[0],
        status=RestrictionStatus.ACTIVE,
        effective_from=condition.valid_at - timedelta(hours=2),
        effective_to=condition.valid_at - timedelta(microseconds=1),
    )
    not_yet = replace(
        original.restrictions[0],
        status=RestrictionStatus.ACTIVE,
        effective_from=condition.valid_at + timedelta(microseconds=1),
        effective_to=condition.valid_at + timedelta(hours=1),
    )

    preferences = demonstration_preferences()
    travel = _travel_for(original.segment_id)
    assert not evaluate_constraints(
        replace(original, restrictions=(at_start,)), condition, preferences, travel
    ).eligible
    assert not evaluate_constraints(
        replace(original, restrictions=(at_end,)), condition, preferences, travel
    ).eligible
    assert evaluate_constraints(
        replace(original, restrictions=(just_expired,)), condition, preferences, travel
    ).eligible
    assert evaluate_constraints(
        replace(original, restrictions=(not_yet,)), condition, preferences, travel
    ).eligible


def test_unknown_applicable_restriction_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _alpha(demo_segments)
    restriction = replace(original.restrictions[0], status=RestrictionStatus.UNKNOWN)
    segment = replace(original, restrictions=(restriction,))

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert not result.eligible
    assert "active_legal_closure" in {failure.gate for failure in result.failures}


def test_contradictory_active_and_inactive_pair_fails_naming_active(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _alpha(demo_segments)
    active = replace(
        original.restrictions[0],
        restriction_id="synthetic-active-closure-02",
        status=RestrictionStatus.ACTIVE,
        reason="Synthetic authoritative closure instrument C-02.",
    )
    inactive = replace(
        active,
        restriction_id="synthetic-inactive-note-02",
        status=RestrictionStatus.INACTIVE,
        reason="Synthetic secondary page claims the reach is open.",
    )
    segment = replace(original, restrictions=(active, inactive))

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )
    failures = {failure.gate: failure.reason for failure in result.failures}

    assert not result.eligible
    assert "Synthetic authoritative closure instrument C-02" in failures["active_legal_closure"]


def test_contradictory_unknown_and_inactive_pair_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _alpha(demo_segments)
    unknown = replace(original.restrictions[0], status=RestrictionStatus.UNKNOWN)
    inactive = replace(
        original.restrictions[0],
        restriction_id="synthetic-inactive-note-03",
        status=RestrictionStatus.INACTIVE,
    )
    segment = replace(original, restrictions=(unknown, inactive))

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert not result.eligible
    assert "active_legal_closure" in {failure.gate for failure in result.failures}


def test_postdated_restriction_retrieval_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _alpha(demo_segments)
    restriction = replace(
        original.restrictions[0],
        status=RestrictionStatus.INACTIVE,
        retrieved_at=condition.valid_at + timedelta(microseconds=1),
    )
    segment = replace(original, restrictions=(restriction,))

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )
    failures = {failure.gate: failure.reason for failure in result.failures}

    assert not result.eligible
    assert "retrieved after the recommendation time" in failures["active_legal_closure"]


def test_active_health_advisory_gates(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _alpha(demo_segments)
    evidence = replace(
        original.health_advisory_evidence,
        status=RestrictionStatus.ACTIVE,
        reason="Synthetic health authority advisory H-01 applies.",
    )
    segment = replace(
        original,
        health_advisory_status=RestrictionStatus.ACTIVE,
        health_advisory_evidence=evidence,
    )

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )
    failures = {failure.gate: failure.reason for failure in result.failures}

    assert not result.eligible
    assert failures["health_advisory"] == "An active health advisory applies."


def test_unknown_health_advisory_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _alpha(demo_segments)
    evidence = replace(original.health_advisory_evidence, status=RestrictionStatus.UNKNOWN)
    segment = replace(
        original,
        health_advisory_status=RestrictionStatus.UNKNOWN,
        health_advisory_evidence=evidence,
    )

    result = evaluate_constraints(
        segment,
        demonstration_condition(),
        demonstration_preferences(),
        _travel_for(segment.segment_id),
    )

    assert not result.eligible
    assert "health_advisory" in {failure.gate for failure in result.failures}


def test_health_evidence_outside_run_window_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _alpha(demo_segments)
    expired = replace(
        original.health_advisory_evidence,
        effective_from=condition.valid_at - timedelta(days=2),
        effective_to=condition.valid_at - timedelta(days=1),
    )
    future = replace(
        original.health_advisory_evidence,
        effective_from=condition.valid_at + timedelta(days=1),
        effective_to=condition.valid_at + timedelta(days=2),
    )
    preferences = demonstration_preferences()
    travel = _travel_for(original.segment_id)

    for evidence in (expired, future):
        result = evaluate_constraints(
            replace(original, health_advisory_evidence=evidence),
            condition,
            preferences,
            travel,
        )
        assert not result.eligible
        assert "health_advisory" in {failure.gate for failure in result.failures}


def test_postdated_health_retrieval_fails_closed(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    original = _alpha(demo_segments)
    evidence = replace(
        original.health_advisory_evidence,
        retrieved_at=condition.valid_at + timedelta(microseconds=1),
    )
    segment = replace(original, health_advisory_evidence=evidence)

    result = evaluate_constraints(
        segment, condition, demonstration_preferences(), _travel_for(segment.segment_id)
    )
    failures = {failure.gate: failure.reason for failure in result.failures}

    assert not result.eligible
    assert "retrieved after the recommendation time" in failures["health_advisory"]


def test_high_habitat_score_cannot_override_active_closure(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = demonstration_condition()
    preferences = demonstration_preferences()
    original = _alpha(demo_segments)
    active = replace(
        original.restrictions[0],
        restriction_id="synthetic-active-closure-04",
        status=RestrictionStatus.ACTIVE,
        reason="Synthetic closure instrument C-04 applies at the run time.",
    )
    gated = replace(
        original,
        segment_id="synthetic-high-habitat-gated",
        name="Synthetic High Habitat Gated (fictional)",
        restrictions=(active,),
    )
    gated_condition = replace(
        condition, applicable_segment_ids=(*condition.applicable_segment_ids, gated.segment_id)
    )
    gated_travel = replace(_travel_for(original.segment_id), segment_id=gated.segment_id)

    run = rank_segments(
        (original, gated),
        gated_condition,
        preferences,
        (_travel_for(original.segment_id), gated_travel),
    )
    results = {item.segment_id: item for item in run.recommendations}
    gated_result = results[gated.segment_id]

    # Pre-gate habitat quality is preserved, but the final score is forced to zero.
    assert (
        gated_result.score.habitat_opportunity
        == results[original.segment_id].score.habitat_opportunity
    )
    assert gated_result.score.habitat_opportunity > 0
    assert not gated_result.eligibility
    assert gated_result.score.final_score == 0
    # Eligible records always rank first regardless of gated habitat quality.
    assert run.recommendations[0].segment_id == original.segment_id


def test_reports_name_closure_evidence_for_gated_segment(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _alpha(demo_segments)
    active = replace(
        original.restrictions[0],
        restriction_id="synthetic-active-closure-05",
        status=RestrictionStatus.ACTIVE,
        reason="Synthetic closure instrument C-05 applies at the run time.",
    )
    gated = replace(
        original,
        segment_id="synthetic-gated-report-copy",
        name="Synthetic Gated Report Copy (fictional)",
        restrictions=(active,),
    )
    condition = replace(demonstration_condition(), applicable_segment_ids=(gated.segment_id,))
    travel = replace(_travel_for(original.segment_id), segment_id=gated.segment_id)

    run = rank_segments((gated,), condition, demonstration_preferences(), (travel,))
    document = report_document(run)
    recommendation = document["recommendations"][0]
    markdown = render_markdown(run)

    assert recommendation["eligible"] is False
    assert any(
        failure["gate"] == "active_legal_closure"
        and "Synthetic closure instrument C-05" in failure["reason"]
        for failure in recommendation["hard_gate_failures"]
    )
    assert any(
        item["restriction_id"] == "synthetic-active-closure-05"
        for item in recommendation["applicable_restrictions"]
    )
    assert "synthetic-active-closure-05" in markdown
    assert "Synthetic closure instrument C-05" in markdown


def test_reports_name_health_evidence_for_gated_segment(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    original = _alpha(demo_segments)
    evidence = replace(
        original.health_advisory_evidence,
        restriction_id="synthetic-health-advisory-06",
        status=RestrictionStatus.ACTIVE,
        reason="Synthetic health authority advisory H-06 applies.",
    )
    gated = replace(
        original,
        segment_id="synthetic-health-gated-copy",
        name="Synthetic Health Gated Copy (fictional)",
        health_advisory_status=RestrictionStatus.ACTIVE,
        health_advisory_evidence=evidence,
    )
    condition = replace(demonstration_condition(), applicable_segment_ids=(gated.segment_id,))
    travel = replace(_travel_for(original.segment_id), segment_id=gated.segment_id)

    run = rank_segments((gated,), condition, demonstration_preferences(), (travel,))
    document = report_document(run)
    recommendation = document["recommendations"][0]
    markdown = render_markdown(run)

    assert recommendation["eligible"] is False
    assert any(
        failure["gate"] == "health_advisory" for failure in recommendation["hard_gate_failures"]
    )
    assert recommendation["health_advisory_evidence"]["restriction_id"] == (
        "synthetic-health-advisory-06"
    )
    assert "synthetic-health-advisory-06" in markdown
