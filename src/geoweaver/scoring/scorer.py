"""Transparent deterministic scorer for the CastNetGPT v0.1 profile."""

import hashlib
from dataclasses import replace
from types import MappingProxyType
from typing import Final

from geoweaver.domain.enums import (
    ActivityPermissionStatus,
    BankSlopeClass,
    ConfidenceBand,
    EvidenceState,
    HabitatFeature,
    PublicAccessState,
    RestrictionStatus,
    SkillLevel,
    Substrate,
    TidalStatus,
    TideAssignmentMethod,
    TideStage,
    VerificationState,
)
from geoweaver.domain.models import (
    ConditionSnapshot,
    ConstraintResult,
    RankedRecommendation,
    RecommendationRun,
    ScoreBreakdown,
    ShorelineSegment,
    TravelEstimate,
    UserPreferences,
)
from geoweaver.scoring.constraints import (
    MAX_CRITICAL_SEGMENT_AGE,
    MAX_TRAVEL_ESTIMATE_AGE,
    evaluate_constraints,
)
from geoweaver.scoring.explanations import build_explanations

MODEL_VERSION: Final = "castnet-v0.1.4"
DEMONSTRATION_NOTICE: Final = (
    "Demonstration only: catalogue locations and conditions are synthetic and are not real "
    "fishing recommendations or substitutes for official safety and legal advice."
)
STALE_AFTER_MINUTES: Final = 120

# Any weight change requires a MODEL_VERSION bump and updated regression fixtures.
COMPONENT_WEIGHTS = MappingProxyType(
    {
        "habitat_opportunity": 0.30,
        "environmental_condition_match": 0.32,
        "access_and_usability": 0.12,
        "privacy": 0.08,
        "family_suitability": 0.08,
        "safety_and_risk": 0.05,
        "travel_efficiency": 0.05,
    }
)

HABITAT_FEATURE_POINTS = MappingProxyType(
    {
        HabitatFeature.CREEK_MOUTH: 25,
        HabitatFeature.DRAIN_OUTFALL: 22,
        HabitatFeature.SHALLOW_GUTTER: 25,
        HabitatFeature.MANGROVE_EDGE: 18,
        HabitatFeature.SAND_BAR: 15,
        HabitatFeature.BUILT_STRUCTURE: 12,
        HabitatFeature.ESTUARINE_CONNECTION: 18,
    }
)

VERIFICATION_CONFIDENCE = MappingProxyType(
    {
        VerificationState.FIELD_VERIFIED: 95,
        VerificationState.REMOTE_REVIEWED: 72,
        VerificationState.UNREVIEWED: 42,
        VerificationState.TEMPORARILY_UNAVAILABLE: 25,
        VerificationState.REJECTED: 10,
    }
)


def _habitat_score(segment: ShorelineSegment) -> int:
    return min(
        100,
        sum(
            HABITAT_FEATURE_POINTS[feature]
            for feature in set(segment.environmental.habitat_features)
        ),
    )


def _wind_match_score(
    segment: ShorelineSegment,
    condition: ConditionSnapshot,
    preferences: UserPreferences,
) -> int:
    if condition.wind_speed_kph is None:
        return 0
    skill_adjustment = {
        SkillLevel.NOVICE: 0.0,
        SkillLevel.INTERMEDIATE: 5.0,
        SkillLevel.EXPERIENCED: 10.0,
    }[preferences.skill_level]
    sheltered_speed = max(
        0.0,
        condition.wind_speed_kph
        - (segment.environmental.wind_shelter_rating * 2.0)
        - skill_adjustment,
    )
    if sheltered_speed <= 10:
        return 100
    if sheltered_speed <= 20:
        return 70
    if sheltered_speed <= 30:
        return 40
    return 10


def _condition_match_score(
    segment: ShorelineSegment,
    condition: ConditionSnapshot,
    preferences: UserPreferences,
) -> int:
    if condition.tide_stage is TideStage.UNKNOWN or not segment.environmental.preferred_tide_stages:
        tide_match = 0
    elif condition.tide_stage in segment.environmental.preferred_tide_stages:
        tide_match = 100
    else:
        tide_match = 45
    return round((0.65 * tide_match) + (0.35 * _wind_match_score(segment, condition, preferences)))


def _access_score(segment: ShorelineSegment) -> int:
    access = segment.access
    parking_score = (
        20 if access.parking_available is True else 5 if access.parking_available is False else 0
    )
    toilet_score = 10 if access.toilets is True else 0
    slope_score = {
        BankSlopeClass.GENTLE: 20,
        BankSlopeClass.MODERATE: 10,
        BankSlopeClass.STEEP: 0,
        BankSlopeClass.UNKNOWN: 0,
    }[segment.bank_slope_class]
    return min(100, (access.casting_space_rating * 10) + parking_score + toilet_score + slope_score)


def _safety_score(segment: ShorelineSegment) -> int:
    profile = segment.environmental
    risk_penalty = (
        (profile.mud_risk * 7) + (profile.snag_risk * 7) + (profile.boat_traffic_rating * 6)
    )
    return max(0, 100 - risk_penalty)


def _condition_evidence_score(condition: ConditionSnapshot) -> int:
    score = 100
    if condition.inferred:
        score -= 40
    if condition.data_freshness_minutes is None:
        score -= 35
    elif condition.data_freshness_minutes > STALE_AFTER_MINUTES:
        score -= 30
    missing_source_groups = sum(
        not source_refs
        for source_refs in (
            condition.weather_source_refs,
            condition.footing_source_refs,
            condition.tide_source_refs,
            condition.daylight_source_refs,
        )
    )
    score -= missing_source_groups * 10
    return max(0, score)


def _data_quality_score(segment: ShorelineSegment, condition: ConditionSnapshot) -> int:
    verification_score = {
        VerificationState.FIELD_VERIFIED: 100,
        VerificationState.REMOTE_REVIEWED: 70,
        VerificationState.UNREVIEWED: 35,
        VerificationState.TEMPORARILY_UNAVAILABLE: 20,
        VerificationState.REJECTED: 0,
    }[segment.verification_status]
    source_score = min(100, len(set(segment.source_refs)) * 25)
    return round(
        (verification_score * 0.55)
        + (source_score * 0.20)
        + (_condition_evidence_score(condition) * 0.25)
    )


def _privacy_fit_score(segment: ShorelineSegment, preferences: UserPreferences) -> int:
    desired = preferences.desired_privacy_rating
    actual = segment.access.privacy_rating
    if desired == 0 or actual >= desired:
        return 100
    return round((actual / desired) * 100)


def _travel_efficiency_score(
    preferences: UserPreferences, travel_estimate: TravelEstimate | None
) -> int:
    if travel_estimate is None:
        return 0
    maximum = preferences.maximum_travel_minutes
    if maximum == 0:
        return 100 if travel_estimate.minutes == 0 else 0
    return max(0, round(((maximum - travel_estimate.minutes) / maximum) * 100))


def score_segment(
    segment: ShorelineSegment,
    condition: ConditionSnapshot,
    constraints: ConstraintResult,
    preferences: UserPreferences,
    travel_estimate: TravelEstimate | None,
) -> ScoreBreakdown:
    """Calculate bounded components and a final score for an eligible segment."""
    component_scores = {
        "habitat_opportunity": _habitat_score(segment),
        "environmental_condition_match": _condition_match_score(segment, condition, preferences),
        "access_and_usability": _access_score(segment),
        "privacy": _privacy_fit_score(segment, preferences),
        "family_suitability": segment.access.family_suitability * 20,
        "safety_and_risk": _safety_score(segment),
        "travel_efficiency": _travel_efficiency_score(preferences, travel_estimate),
        "data_quality": _data_quality_score(segment, condition),
    }
    weighted_score = round(
        sum(component_scores[name] * weight for name, weight in COMPONENT_WEIGHTS.items())
    )
    final_score = max(0, min(100, weighted_score)) if constraints.eligible else 0
    return ScoreBreakdown(**component_scores, final_score=final_score)


def _missing_or_stale_information(
    segment: ShorelineSegment,
    condition: ConditionSnapshot,
    travel_estimate: TravelEstimate | None,
) -> tuple[str, ...]:
    missing: list[str] = []
    if segment.verification_status is VerificationState.REMOTE_REVIEWED:
        missing.append("Segment attributes are remotely reviewed, not field verified.")
    elif segment.verification_status is VerificationState.UNREVIEWED:
        missing.append("Segment attributes have not been reviewed.")
    if segment.access.parking_available is None:
        missing.append("Parking availability is unknown.")
    if segment.access.toilets is None:
        missing.append("Toilet availability is unknown.")
    if segment.access.public_access_status is PublicAccessState.UNKNOWN:
        missing.append("Public access status is unknown.")
    if segment.substrate is Substrate.UNKNOWN:
        missing.append("Shoreline substrate is unknown.")
    if segment.bank_slope_class is BankSlopeClass.UNKNOWN:
        missing.append("Bank slope is unknown.")
    if not segment.environmental.habitat_features:
        missing.append("No habitat features are recorded.")
    if not segment.environmental.preferred_tide_stages:
        missing.append("No preferred tide stages are recorded.")
    if not segment.legal_status_known:
        missing.append("Legal status is unknown.")
    for label, provenance in (
        ("Legal-status", segment.legal_status_evidence),
        ("Activity-permission", segment.activity_permission_evidence),
        ("Closure-review", segment.restriction_review_evidence),
    ):
        age = condition.valid_at - provenance.retrieved_at
        if provenance.evidence_state is EvidenceState.INFERRED:
            missing.append(f"{label} provenance is inferred.")
        if age.total_seconds() < 0:
            missing.append(f"{label} provenance postdates the recommendation time.")
        elif age > MAX_CRITICAL_SEGMENT_AGE:
            missing.append(f"{label} provenance is stale ({age.days} days old).")
    if segment.activity_permission_status is ActivityPermissionStatus.UNKNOWN:
        missing.append("Permission for the intended activity is unknown.")
    if segment.tidal_status is TidalStatus.UNKNOWN:
        missing.append("Tidal eligibility is unknown.")
    if segment.health_advisory_status is RestrictionStatus.UNKNOWN:
        missing.append("Health-advisory status is unknown.")
    if segment.health_advisory_evidence.evidence_state is EvidenceState.INFERRED:
        missing.append("Health-advisory evidence is inferred.")
    applicable_restrictions = tuple(
        restriction
        for restriction in segment.restrictions
        if restriction.is_effective_at(condition.valid_at)
    )
    if any(
        restriction.status is RestrictionStatus.UNKNOWN for restriction in applicable_restrictions
    ):
        missing.append("At least one applicable restriction has unknown status.")
    if any(
        restriction.evidence_state is EvidenceState.INFERRED
        for restriction in applicable_restrictions
    ):
        missing.append("Applicable restriction evidence is inferred.")
    if segment.health_advisory_evidence.retrieved_at > condition.valid_at:
        missing.append("Health-advisory evidence postdates the recommendation time.")
    elif not segment.health_advisory_evidence.is_effective_at(condition.valid_at):
        missing.append("Health-advisory evidence is not applicable at the recommendation time.")
    elif (
        condition.valid_at - segment.health_advisory_evidence.retrieved_at
        > MAX_CRITICAL_SEGMENT_AGE
    ):
        age = condition.valid_at - segment.health_advisory_evidence.retrieved_at
        missing.append(f"Health-advisory evidence is stale ({age.days} days old).")
    if any(
        restriction.retrieved_at > condition.valid_at for restriction in applicable_restrictions
    ):
        missing.append("Applicable restriction evidence postdates the recommendation time.")
    if any(
        condition.valid_at - restriction.retrieved_at > MAX_CRITICAL_SEGMENT_AGE
        for restriction in applicable_restrictions
    ):
        missing.append("Applicable restriction evidence is stale.")
    if not segment.safety_information_complete:
        missing.append("Critical stable safety information is incomplete.")
    if condition.tide_stage is TideStage.UNKNOWN:
        missing.append("Tide stage is missing.")
    if condition.wind_speed_kph is None:
        missing.append("Wind speed is missing.")
    if condition.gust_speed_kph is None:
        missing.append("Gust speed is missing.")
    if condition.severe_weather_warning is None:
        missing.append("Severe-weather status is missing.")
    if condition.lightning_or_severe_thunderstorm_risk is None:
        missing.append("Lightning and severe-thunderstorm status is missing.")
    if condition.footing_safe is None:
        missing.append("Footing safety is missing.")
    if condition.usable_daylight_minutes is None:
        missing.append("Usable daylight is missing.")
    if condition.data_freshness_minutes is None:
        missing.append("Condition freshness is missing.")
    elif condition.data_freshness_minutes > STALE_AFTER_MINUTES:
        missing.append(
            f"Condition snapshot is stale ({condition.data_freshness_minutes} minutes old)."
        )
    if condition.retrieved_at is None:
        missing.append("Condition retrieval timestamp is missing.")
    else:
        actual_condition_age = condition.valid_at - condition.retrieved_at
        if actual_condition_age.total_seconds() < 0:
            missing.append("Condition retrieval timestamp postdates the recommendation time.")
        elif (
            condition.data_freshness_minutes is not None
            and int(actual_condition_age.total_seconds() // 60) != condition.data_freshness_minutes
        ):
            missing.append("Condition freshness conflicts with its retrieval timestamp.")
    if condition.inferred:
        missing.append("Condition snapshot is explicitly marked as inferred demonstration data.")
    if not condition.weather_status_verified:
        missing.append("Severe-weather status is not verified.")
    if not condition.footing_status_verified:
        missing.append("Footing status is not verified.")
    if not condition.tide_status_verified:
        missing.append("Tide status is not verified.")
    if not condition.daylight_status_verified:
        missing.append("Daylight status is not verified.")
    if not condition.weather_source_refs:
        missing.append("Weather status has no source references.")
    if not condition.footing_source_refs:
        missing.append("Footing status has no source references.")
    if not condition.tide_source_refs:
        missing.append("Tide status has no source references.")
    tide_applicability = condition.tide_source_applicability
    if tide_applicability is None:
        missing.append("Tide-source applicability provenance is missing.")
    else:
        applicability_age = condition.valid_at - tide_applicability.retrieved_at
        if (
            tide_applicability.evidence_state is EvidenceState.INFERRED
            or tide_applicability.assignment_method is TideAssignmentMethod.INFERRED
        ):
            missing.append("Tide-source applicability is inferred.")
        if tide_applicability.applicability_source_ref not in condition.tide_source_refs:
            missing.append("Tide-source applicability is not linked to tide evidence.")
        if applicability_age.total_seconds() < 0:
            missing.append("Tide-source applicability postdates the recommendation time.")
        elif applicability_age.total_seconds() / 60 > STALE_AFTER_MINUTES:
            missing.append("Tide-source applicability is stale.")
    if not condition.daylight_source_refs:
        missing.append("Daylight status has no source references.")
    segment_age = condition.valid_at - segment.last_updated
    if segment_age.total_seconds() < 0:
        missing.append("Segment evidence timestamp postdates the recommendation time.")
    elif segment_age > MAX_CRITICAL_SEGMENT_AGE:
        missing.append(f"Segment evidence is stale ({segment_age.days} days old).")
    if travel_estimate is None:
        missing.append("Travel time is missing.")
    else:
        if travel_estimate.inferred:
            missing.append("Travel time is an inferred manual demonstration estimate.")
        if travel_estimate.retrieved_at is None:
            missing.append("Travel estimate retrieval time is missing.")
        else:
            travel_age = condition.valid_at - travel_estimate.retrieved_at
            if travel_age.total_seconds() < 0:
                missing.append("Travel estimate postdates the recommendation time.")
            elif travel_age > MAX_TRAVEL_ESTIMATE_AGE:
                missing.append(f"Travel estimate is stale ({travel_age.days} days old).")
    return tuple(missing)


def _confidence(
    segment: ShorelineSegment,
    condition: ConditionSnapshot,
    missing_or_stale_information: tuple[str, ...],
    travel_estimate: TravelEstimate | None,
) -> tuple[int, ConfidenceBand]:
    confidence = VERIFICATION_CONFIDENCE[segment.verification_status]
    if len(set(segment.source_refs)) < 2:
        confidence -= 5
    if condition.inferred:
        confidence -= 10
    if condition.data_freshness_minutes is None:
        confidence -= 15
    elif condition.data_freshness_minutes > STALE_AFTER_MINUTES:
        confidence -= 20
    if condition.tide_stage is TideStage.UNKNOWN:
        confidence -= 10
    if condition.wind_speed_kph is None:
        confidence -= 10
    confidence -= 10 * sum(
        not source_refs
        for source_refs in (
            condition.weather_source_refs,
            condition.footing_source_refs,
            condition.tide_source_refs,
            condition.daylight_source_refs,
        )
    )
    if not condition.weather_status_verified:
        confidence -= 20
    if not condition.footing_status_verified:
        confidence -= 20
    if not condition.tide_status_verified:
        confidence -= 20
    if not condition.daylight_status_verified:
        confidence -= 20
    segment_penalties = {
        "Parking availability is unknown.": 5,
        "Toilet availability is unknown.": 5,
        "Public access status is unknown.": 25,
        "Shoreline substrate is unknown.": 10,
        "Bank slope is unknown.": 15,
        "No habitat features are recorded.": 10,
        "No preferred tide stages are recorded.": 10,
        "Legal status is unknown.": 20,
        "Permission for the intended activity is unknown.": 20,
        "Tidal eligibility is unknown.": 20,
        "Health-advisory status is unknown.": 20,
        "At least one applicable restriction has unknown status.": 25,
        "Health-advisory evidence postdates the recommendation time.": 25,
        "Health-advisory evidence is not applicable at the recommendation time.": 25,
        "Applicable restriction evidence postdates the recommendation time.": 25,
        "Critical stable safety information is incomplete.": 20,
        "Severe-weather status is missing.": 25,
        "Lightning and severe-thunderstorm status is missing.": 25,
        "Footing safety is missing.": 25,
        "Usable daylight is missing.": 20,
        "Gust speed is missing.": 20,
    }
    confidence -= sum(
        penalty
        for limitation, penalty in segment_penalties.items()
        if limitation in missing_or_stale_information
    )
    if any(
        item.startswith("Segment evidence is stale")
        or item == "Segment evidence timestamp postdates the recommendation time."
        for item in missing_or_stale_information
    ):
        confidence -= 20
    if travel_estimate is None:
        confidence -= 15
    elif travel_estimate.inferred:
        confidence -= 5
    if any(
        "provenance is inferred" in item
        or "evidence is inferred" in item
        or "provenance postdates" in item
        or "provenance is stale" in item
        or "evidence is stale" in item
        or item.startswith("Tide-source applicability")
        or item.startswith("Travel estimate")
        for item in missing_or_stale_information
    ):
        confidence -= 20
    confidence = max(0, min(100, confidence))
    critical_information_missing = (
        segment.access.public_access_status is PublicAccessState.UNKNOWN
        or not segment.legal_status_known
        or segment.activity_permission_status is ActivityPermissionStatus.UNKNOWN
        or segment.tidal_status is TidalStatus.UNKNOWN
        or segment.health_advisory_status is RestrictionStatus.UNKNOWN
        or any(
            restriction.status is RestrictionStatus.UNKNOWN
            for restriction in segment.restrictions
            if restriction.is_effective_at(condition.valid_at)
        )
        or segment.health_advisory_evidence.retrieved_at > condition.valid_at
        or not segment.health_advisory_evidence.is_effective_at(condition.valid_at)
        or any(
            restriction.retrieved_at > condition.valid_at
            for restriction in segment.restrictions
            if restriction.is_effective_at(condition.valid_at)
        )
        or not segment.safety_information_complete
        or segment.bank_slope_class is BankSlopeClass.UNKNOWN
        or condition.severe_weather_warning is None
        or condition.lightning_or_severe_thunderstorm_risk is None
        or condition.wind_speed_kph is None
        or condition.gust_speed_kph is None
        or condition.footing_safe is None
        or condition.usable_daylight_minutes is None
        or condition.tide_stage is TideStage.UNKNOWN
        or condition.data_freshness_minutes is None
        or condition.data_freshness_minutes > STALE_AFTER_MINUTES
        or condition.retrieved_at is None
        or (condition.retrieved_at is not None and condition.retrieved_at > condition.valid_at)
        or (
            condition.retrieved_at is not None
            and condition.data_freshness_minutes is not None
            and int((condition.valid_at - condition.retrieved_at).total_seconds() // 60)
            != condition.data_freshness_minutes
        )
        or not condition.weather_status_verified
        or not condition.footing_status_verified
        or not condition.tide_status_verified
        or not condition.daylight_status_verified
        or not condition.weather_source_refs
        or not condition.footing_source_refs
        or not condition.tide_source_refs
        or not condition.daylight_source_refs
        or travel_estimate is None
        or any(
            "provenance is inferred" in item
            or "evidence is inferred" in item
            or "provenance postdates" in item
            or "provenance is stale" in item
            or "evidence is stale" in item
            or item.startswith("Tide-source applicability")
            or item.startswith("Travel estimate")
            for item in missing_or_stale_information
        )
    )
    if critical_information_missing:
        confidence = min(confidence, 54)
    if condition.inferred:
        confidence = min(confidence, 79)
    if confidence >= 80:
        band = ConfidenceBand.HIGH
    elif confidence >= 55:
        band = ConfidenceBand.MEDIUM
    else:
        band = ConfidenceBand.LOW
    return confidence, band


def _run_id(
    segments: tuple[ShorelineSegment, ...],
    condition: ConditionSnapshot,
    preferences: UserPreferences,
    travel_estimates: tuple[TravelEstimate, ...],
) -> str:
    canonical_segments = tuple(sorted(segments, key=lambda item: item.segment_id))
    canonical_travel = tuple(sorted(travel_estimates, key=lambda item: item.segment_id))
    payload = repr(
        (
            MODEL_VERSION,
            canonical_segments,
            (
                condition,
                condition.retrieved_at,
                condition.scope_type,
                condition.scope_id,
                condition.tide_source_applicability,
            ),
            preferences,
            tuple((item, item.retrieved_at) for item in canonical_travel),
        )
    ).encode()
    return f"run-{hashlib.sha256(payload).hexdigest()[:16]}"


def rank_segments(
    segments: tuple[ShorelineSegment, ...],
    condition: ConditionSnapshot,
    preferences: UserPreferences,
    travel_estimates: tuple[TravelEstimate, ...],
) -> RecommendationRun:
    """Rank all segments deterministically, always placing eligible records first."""
    segment_ids = [segment.segment_id for segment in segments]
    if len(set(segment_ids)) != len(segment_ids):
        raise ValueError("segments must not contain duplicate segment IDs")
    inapplicable_segment_ids = set(segment_ids).difference(condition.applicable_segment_ids)
    if inapplicable_segment_ids:
        inapplicable = ", ".join(sorted(inapplicable_segment_ids))
        raise ValueError(
            f"condition snapshot {condition.snapshot_id!r} is not applicable to segment IDs: "
            f"{inapplicable}"
        )
    travel_by_segment: dict[str, TravelEstimate] = {}
    for estimate in travel_estimates:
        if estimate.segment_id in travel_by_segment:
            raise ValueError(f"duplicate travel estimate for {estimate.segment_id!r}")
        travel_by_segment[estimate.segment_id] = estimate
    unknown_travel_ids = set(travel_by_segment).difference(segment_ids)
    if unknown_travel_ids:
        unknown = ", ".join(sorted(unknown_travel_ids))
        raise ValueError(f"travel estimates reference unknown segment IDs: {unknown}")
    origins = {estimate.origin_label for estimate in travel_estimates}
    if len(origins) > 1:
        raise ValueError("all travel estimates in a run must use the same origin")

    assessments: list[RankedRecommendation] = []
    for segment in segments:
        travel_estimate = travel_by_segment.get(segment.segment_id)
        constraints = evaluate_constraints(segment, condition, preferences, travel_estimate)
        score = score_segment(
            segment,
            condition,
            constraints,
            preferences,
            travel_estimate,
        )
        missing = _missing_or_stale_information(segment, condition, travel_estimate)
        confidence_score, confidence_band = _confidence(
            segment, condition, missing, travel_estimate
        )
        positives, highest_components, limitations = build_explanations(score, constraints, missing)
        applicable_restrictions = tuple(
            restriction
            for restriction in segment.restrictions
            if restriction.is_effective_at(condition.valid_at)
        )
        assessments.append(
            RankedRecommendation(
                rank=1,
                segment_id=segment.segment_id,
                name=segment.name,
                region=segment.region,
                waterway=segment.waterway,
                eligibility=constraints.eligible,
                score=score,
                confidence_score=confidence_score,
                confidence_band=confidence_band,
                strongest_positive_factors=positives,
                highest_scoring_components=highest_components,
                strongest_limitations=limitations,
                constraints=constraints,
                missing_or_stale_information=missing,
                applicable_restrictions=applicable_restrictions,
                health_advisory_evidence=segment.health_advisory_evidence,
                legal_status_evidence=segment.legal_status_evidence,
                activity_permission_evidence=segment.activity_permission_evidence,
                restriction_review_evidence=segment.restriction_review_evidence,
                verification_status=segment.verification_status,
                source_refs=segment.source_refs,
                data_last_updated=segment.last_updated,
                travel_time_minutes=(travel_estimate.minutes if travel_estimate else None),
                travel_origin=(travel_estimate.origin_label if travel_estimate else None),
                model_version=MODEL_VERSION,
                condition_snapshot_id=condition.snapshot_id,
                travel_source_ref=(travel_estimate.source_ref if travel_estimate else None),
                travel_retrieved_at=(travel_estimate.retrieved_at if travel_estimate else None),
                travel_evidence_state=(travel_estimate.evidence_state if travel_estimate else None),
            )
        )

    assessments.sort(
        key=lambda item: (
            not item.eligibility,
            -item.score.final_score,
            item.segment_id,
        )
    )
    ranked = tuple(replace(item, rank=index) for index, item in enumerate(assessments, start=1))
    return RecommendationRun(
        run_id=_run_id(segments, condition, preferences, travel_estimates),
        application="CastNetGPT v0.1",
        generated_at=condition.valid_at,
        model_version=MODEL_VERSION,
        condition=condition,
        preferences=preferences,
        travel_estimates=tuple(sorted(travel_estimates, key=lambda item: item.segment_id)),
        recommendations=ranked,
        demonstration_notice=DEMONSTRATION_NOTICE,
        condition_snapshots=(condition,),
    )
