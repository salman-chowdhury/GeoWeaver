"""Tests for deterministic scores, ranking, and confidence."""

import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from geoweaver.demo import (
    demonstration_condition,
    demonstration_preferences,
    demonstration_travel_estimates,
)
from geoweaver.domain.enums import (
    BankSlopeClass,
    ConfidenceBand,
    PublicAccessState,
    RestrictionStatus,
    SkillLevel,
    Substrate,
    VerificationState,
)
from geoweaver.domain.models import (
    ConstraintResult,
    GateCheck,
    ScoreBreakdown,
    ShorelineSegment,
)
from geoweaver.scoring.explanations import build_explanations
from geoweaver.scoring.scorer import COMPONENT_WEIGHTS, rank_segments

FIXTURES = Path(__file__).parent / "fixtures"


def test_component_weights_sum_to_one() -> None:
    assert sum(COMPONENT_WEIGHTS.values()) == 1.0


def test_all_scores_are_bounded(demo_segments: tuple[ShorelineSegment, ...]) -> None:
    run = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )

    for recommendation in run.recommendations:
        assert 0 <= recommendation.score.final_score <= 100
        assert all(0 <= value <= 100 for value in recommendation.score.component_scores().values())
        assert 0 <= recommendation.confidence_score <= 100


def test_ranking_is_deterministic(demo_segments: tuple[ShorelineSegment, ...]) -> None:
    first = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )
    second = rank_segments(
        tuple(reversed(demo_segments)),
        demonstration_condition(),
        demonstration_preferences(),
        tuple(reversed(demonstration_travel_estimates())),
    )

    assert first == second
    assert first.run_id == second.run_id


def test_rank_segments_run_id_includes_condition_and_travel_provenance(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = (demo_segments[0],)
    condition = demonstration_condition()
    travel = (demonstration_travel_estimates()[0],)
    baseline = rank_segments(segment, condition, demonstration_preferences(), travel)

    changed_scope = rank_segments(
        segment,
        replace(condition, scope_id="different-reviewed-scope"),
        demonstration_preferences(),
        travel,
    )
    changed_condition_retrieval = rank_segments(
        segment,
        replace(condition, retrieved_at=condition.retrieved_at - timedelta(minutes=1)),
        demonstration_preferences(),
        travel,
    )
    changed_travel_retrieval = rank_segments(
        segment,
        condition,
        demonstration_preferences(),
        (replace(travel[0], retrieved_at=travel[0].retrieved_at - timedelta(minutes=1)),),
    )

    assert (
        len(
            {
                baseline.run_id,
                changed_scope.run_id,
                changed_condition_retrieval.run_id,
                changed_travel_retrieval.run_id,
            }
        )
        == 4
    )


def test_equal_suitability_scores_do_not_use_confidence_as_a_tiebreaker(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    first = demo_segments[0]
    second = replace(
        first,
        segment_id="aaa-lower-confidence",
        verification_status=VerificationState.UNREVIEWED,
        source_refs=(first.source_refs[0],),
    )
    condition = replace(
        demonstration_condition(),
        applicable_segment_ids=(first.segment_id, second.segment_id),
    )
    travel = demonstration_travel_estimates()[0]
    second_travel = replace(travel, segment_id=second.segment_id)

    run = rank_segments(
        (first, second),
        condition,
        demonstration_preferences(),
        (travel, second_travel),
    )

    assert run.recommendations[0].segment_id == second.segment_id
    assert run.recommendations[0].score.final_score == run.recommendations[1].score.final_score
    assert run.recommendations[0].confidence_score < run.recommendations[1].confidence_score


def test_eligible_segments_always_rank_before_ineligible(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    run = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )
    eligibility = [item.eligibility for item in run.recommendations]

    assert eligibility == sorted(eligibility, reverse=True)
    assert all(item.score.final_score == 0 for item in run.recommendations if not item.eligibility)


def test_confidence_reduces_for_weak_or_missing_evidence(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    strong = demo_segments[0]
    weak = replace(
        strong,
        segment_id="demo-weak-copy",
        verification_status=VerificationState.UNREVIEWED,
        access=replace(strong.access, parking_available=None, toilets=None),
    )
    strong_travel = demonstration_travel_estimates()[0]
    weak_travel = replace(strong_travel, segment_id=weak.segment_id)
    condition = demonstration_condition()
    condition = replace(
        condition,
        applicable_segment_ids=(*condition.applicable_segment_ids, weak.segment_id),
    )
    run = rank_segments(
        (strong, weak),
        condition,
        demonstration_preferences(),
        (strong_travel, weak_travel),
    )
    strong_result = next(
        item for item in run.recommendations if item.segment_id == strong.segment_id
    )
    weak_result = next(item for item in run.recommendations if item.segment_id == weak.segment_id)

    assert weak_result.confidence_score < strong_result.confidence_score
    assert "Parking availability is unknown." in weak_result.missing_or_stale_information
    assert weak_result.score.data_quality < strong_result.score.data_quality


def test_stale_and_inferred_conditions_reduce_confidence(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = demo_segments[0]
    baseline_condition = replace(
        demonstration_condition(), inferred=False, data_freshness_minutes=30
    )
    weak_condition = replace(
        demonstration_condition(),
        inferred=True,
        data_freshness_minutes=500,
        weather_status_verified=False,
        footing_status_verified=False,
        tide_status_verified=False,
        daylight_status_verified=False,
    )
    travel = (demonstration_travel_estimates()[0],)
    baseline = rank_segments((segment,), baseline_condition, demonstration_preferences(), travel)
    weak = rank_segments((segment,), weak_condition, demonstration_preferences(), travel)

    assert weak.recommendations[0].confidence_score < baseline.recommendations[0].confidence_score
    assert any("stale" in item for item in weak.recommendations[0].missing_or_stale_information)


def test_score_and_confidence_are_reported_separately(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    run = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )
    result = run.recommendations[0]

    assert result.score.final_score != result.confidence_score
    assert result.model_version == run.model_version


def test_inferred_conditions_cannot_receive_high_confidence(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = replace(
        demonstration_condition(),
        inferred=True,
        weather_status_verified=False,
        footing_status_verified=False,
        tide_status_verified=False,
        daylight_status_verified=False,
    )
    run = rank_segments(
        (demo_segments[0],),
        condition,
        demonstration_preferences(),
        (demonstration_travel_estimates()[0],),
    )

    assert run.recommendations[0].confidence_score <= 79
    assert run.recommendations[0].confidence_band is not ConfidenceBand.HIGH


def test_missing_morphology_and_environmental_evidence_reduce_confidence(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    strong = demo_segments[0]
    weak = replace(
        strong,
        segment_id="demo-incomplete-copy",
        substrate=Substrate.UNKNOWN,
        bank_slope_class=BankSlopeClass.UNKNOWN,
        environmental=replace(
            strong.environmental,
            habitat_features=(),
            preferred_tide_stages=(),
        ),
    )
    strong_travel = demonstration_travel_estimates()[0]
    weak_travel = replace(strong_travel, segment_id=weak.segment_id)
    condition = demonstration_condition()
    condition = replace(
        condition,
        applicable_segment_ids=(*condition.applicable_segment_ids, weak.segment_id),
    )

    run = rank_segments(
        (strong, weak),
        condition,
        demonstration_preferences(),
        (strong_travel, weak_travel),
    )
    results = {item.segment_id: item for item in run.recommendations}

    assert results[weak.segment_id].confidence_score < results[strong.segment_id].confidence_score
    assert results[weak.segment_id].confidence_band is ConfidenceBand.LOW


def test_privacy_preference_changes_privacy_fit_and_final_score(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = replace(
        demo_segments[0],
        access=replace(demo_segments[0].access, privacy_rating=1),
    )
    travel = (demonstration_travel_estimates()[0],)
    low_requirement = replace(demonstration_preferences(), desired_privacy_rating=1)
    high_requirement = replace(demonstration_preferences(), desired_privacy_rating=5)

    low_run = rank_segments((segment,), demonstration_condition(), low_requirement, travel)
    high_run = rank_segments((segment,), demonstration_condition(), high_requirement, travel)

    assert low_run.recommendations[0].score.privacy == 100
    assert high_run.recommendations[0].score.privacy == 20
    assert (
        low_run.recommendations[0].score.final_score > high_run.recommendations[0].score.final_score
    )


def test_skill_level_changes_wind_condition_match(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = demo_segments[0]
    condition = replace(demonstration_condition(), wind_speed_kph=30.0)
    novice = replace(demonstration_preferences(), skill_level=SkillLevel.NOVICE)
    experienced = replace(demonstration_preferences(), skill_level=SkillLevel.EXPERIENCED)
    travel = (demonstration_travel_estimates()[0],)

    novice_run = rank_segments((segment,), condition, novice, travel)
    experienced_run = rank_segments((segment,), condition, experienced, travel)

    assert (
        experienced_run.recommendations[0].score.environmental_condition_match
        > novice_run.recommendations[0].score.environmental_condition_match
    )


def test_duplicate_travel_estimates_are_rejected(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    estimate = demonstration_travel_estimates()[0]

    with pytest.raises(ValueError, match="duplicate travel estimate"):
        rank_segments(
            (demo_segments[0],),
            demonstration_condition(),
            demonstration_preferences(),
            (estimate, estimate),
        )


def test_evidence_diagnostics_affect_confidence_not_suitability(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = demo_segments[0]
    strong_condition = replace(demonstration_condition(), inferred=False)
    inferred_condition = replace(
        strong_condition,
        inferred=True,
        weather_status_verified=False,
        footing_status_verified=False,
        tide_status_verified=False,
        daylight_status_verified=False,
    )
    travel = replace(demonstration_travel_estimates()[0], inferred=False)

    strong = rank_segments(
        (segment,), strong_condition, demonstration_preferences(), (travel,)
    ).recommendations[0]
    inferred = rank_segments(
        (segment,), inferred_condition, demonstration_preferences(), (travel,)
    ).recommendations[0]

    assert inferred.score.data_quality < strong.score.data_quality
    assert (
        inferred.score.suitability_component_scores() == strong.score.suitability_component_scores()
    )
    assert inferred.score.final_score == 0
    assert inferred.confidence_score < strong.confidence_score


def test_source_count_affects_confidence_not_suitability(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    strong = demo_segments[0]
    single_source = replace(strong, source_refs=(strong.source_refs[0],))
    condition = replace(demonstration_condition(), inferred=False)
    travel = replace(demonstration_travel_estimates()[0], inferred=False)

    strong_result = rank_segments(
        (strong,), condition, demonstration_preferences(), (travel,)
    ).recommendations[0]
    single_source_result = rank_segments(
        (single_source,), condition, demonstration_preferences(), (travel,)
    ).recommendations[0]

    assert single_source_result.score.data_quality < strong_result.score.data_quality
    assert single_source_result.score.final_score == strong_result.score.final_score
    assert single_source_result.confidence_score < strong_result.confidence_score


def test_travel_efficiency_changes_eligible_ranking(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    near = demo_segments[0]
    far = replace(near, segment_id="demo-alpha-far-copy")
    condition = demonstration_condition()
    condition = replace(
        condition,
        applicable_segment_ids=(*condition.applicable_segment_ids, far.segment_id),
    )
    base_travel = replace(demonstration_travel_estimates()[0], inferred=False)
    near_travel = replace(base_travel, minutes=5)
    far_travel = replace(base_travel, segment_id=far.segment_id, minutes=40)

    run = rank_segments(
        (far, near),
        condition,
        demonstration_preferences(),
        (far_travel, near_travel),
    )
    results = {item.segment_id: item for item in run.recommendations}

    assert all(item.eligibility for item in run.recommendations)
    assert run.recommendations[0].segment_id == near.segment_id
    assert (
        results[near.segment_id].score.travel_efficiency
        > results[far.segment_id].score.travel_efficiency
    )
    assert results[near.segment_id].score.final_score > results[far.segment_id].score.final_score


def test_low_components_are_not_labelled_positive_factors() -> None:
    score = ScoreBreakdown(
        habitat_opportunity=24,
        environmental_condition_match=23,
        access_and_usability=22,
        privacy=21,
        family_suitability=20,
        safety_and_risk=19,
        travel_efficiency=18,
        data_quality=39,
        final_score=24,
    )

    positives, highest, _ = build_explanations(score, ConstraintResult(()), ())

    assert positives == ()
    assert highest
    assert all("Highest-scoring component" in item for item in highest)
    assert all("positive" not in item.lower() for item in highest)


def test_hard_gated_components_are_explicitly_pre_gate_not_positive() -> None:
    score = ScoreBreakdown(
        habitat_opportunity=100,
        environmental_condition_match=90,
        access_and_usability=80,
        privacy=70,
        family_suitability=60,
        safety_and_risk=50,
        travel_efficiency=40,
        data_quality=100,
        final_score=0,
    )
    constraints = ConstraintResult((GateCheck("closure", False, "An active closure applies."),))

    positives, highest, _ = build_explanations(score, constraints, ())

    assert positives == ()
    assert highest
    assert all("Pre-gate component only" in item for item in highest)
    assert all("ineligible" in item for item in highest)


def test_condition_snapshot_must_explicitly_apply_to_every_ranked_segment(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    segment = demo_segments[0]
    condition = replace(
        demonstration_condition(),
        applicable_segment_ids=(demo_segments[1].segment_id,),
    )

    with pytest.raises(ValueError, match=rf"not applicable.*{segment.segment_id}"):
        rank_segments(
            (segment,),
            condition,
            demonstration_preferences(),
            (demonstration_travel_estimates()[0],),
        )


@pytest.mark.parametrize(
    ("segment_change", "expected_missing"),
    [
        ("public_access", "Public access status is unknown."),
        ("restriction", "At least one applicable restriction has unknown status."),
        ("legal", "Legal status is unknown."),
    ],
)
def test_missing_critical_segment_information_cannot_receive_high_confidence(
    demo_segments: tuple[ShorelineSegment, ...],
    segment_change: str,
    expected_missing: str,
) -> None:
    segment = demo_segments[0]
    if segment_change == "public_access":
        segment = replace(
            segment,
            access=replace(segment.access, public_access_status=PublicAccessState.UNKNOWN),
        )
    elif segment_change == "restriction":
        restriction = replace(segment.restrictions[0], status=RestrictionStatus.UNKNOWN)
        segment = replace(segment, restrictions=(restriction,))
    else:
        segment = replace(segment, legal_status_known=False)
    condition = replace(demonstration_condition(), inferred=False)
    travel = replace(demonstration_travel_estimates()[0], inferred=False)

    recommendation = rank_segments(
        (segment,), condition, demonstration_preferences(), (travel,)
    ).recommendations[0]

    assert not recommendation.eligibility
    assert expected_missing in recommendation.missing_or_stale_information
    assert recommendation.confidence_band is ConfidenceBand.LOW


def test_postdated_legal_evidence_is_missing_information_and_low_confidence(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    condition = replace(demonstration_condition(), inferred=False)
    original = demo_segments[0]
    restriction = replace(
        original.restrictions[0],
        retrieved_at=condition.valid_at + timedelta(microseconds=1),
    )
    segment = replace(original, restrictions=(restriction,))
    travel = replace(demonstration_travel_estimates()[0], inferred=False)

    recommendation = rank_segments(
        (segment,), condition, demonstration_preferences(), (travel,)
    ).recommendations[0]

    assert not recommendation.eligibility
    assert (
        "Applicable restriction evidence postdates the recommendation time."
        in recommendation.missing_or_stale_information
    )
    assert recommendation.confidence_band is ConfidenceBand.LOW


@pytest.mark.parametrize(
    ("condition_changes", "expected_missing"),
    [
        ({"severe_weather_warning": None}, "Severe-weather status is missing."),
        (
            {"lightning_or_severe_thunderstorm_risk": None},
            "Lightning and severe-thunderstorm status is missing.",
        ),
        ({"wind_speed_kph": None}, "Wind speed is missing."),
        ({"gust_speed_kph": None}, "Gust speed is missing."),
        ({"footing_safe": None}, "Footing safety is missing."),
        ({"usable_daylight_minutes": None}, "Usable daylight is missing."),
        ({"weather_source_refs": ()}, "Weather status has no source references."),
        ({"footing_source_refs": ()}, "Footing status has no source references."),
        ({"tide_source_refs": ()}, "Tide status has no source references."),
        ({"daylight_source_refs": ()}, "Daylight status has no source references."),
    ],
)
def test_missing_critical_condition_information_cannot_receive_high_confidence(
    demo_segments: tuple[ShorelineSegment, ...],
    condition_changes: dict[str, object],
    expected_missing: str,
) -> None:
    segment = demo_segments[0]
    condition = replace(
        demonstration_condition(),
        inferred=False,
        **condition_changes,
    )
    travel = replace(demonstration_travel_estimates()[0], inferred=False)

    recommendation = rank_segments(
        (segment,), condition, demonstration_preferences(), (travel,)
    ).recommendations[0]

    assert not recommendation.eligibility
    assert expected_missing in recommendation.missing_or_stale_information
    assert recommendation.confidence_band is ConfidenceBand.LOW


def test_castnet_v0_1_4_demo_ranking_matches_versioned_golden(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    run = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )
    actual = {
        "model_version": run.model_version,
        "run_id": run.run_id,
        "eligible_order": [item.segment_id for item in run.recommendations if item.eligibility],
        "results": sorted(
            (
                {
                    "segment_id": item.segment_id,
                    "eligible": item.eligibility,
                    "score": item.score.final_score,
                    "confidence": item.confidence_score,
                    "hard_gate_failures": [gate.gate for gate in item.constraints.failures],
                    "positive_factors": list(item.strongest_positive_factors),
                    "highest_scoring_components": list(item.highest_scoring_components),
                    "limitations": list(item.strongest_limitations),
                }
                for item in run.recommendations
            ),
            key=lambda result: result["segment_id"],
        ),
    }
    expected = json.loads((FIXTURES / "castnet_v0_1_4_golden.json").read_text(encoding="utf-8"))
    expected["results"] = sorted(expected["results"], key=lambda result: result["segment_id"])

    assert actual == expected
