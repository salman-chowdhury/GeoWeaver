"""File-input recommendation orchestration with explicit condition scoping."""

import hashlib
from dataclasses import replace

from geoweaver.domain.enums import DataClassification
from geoweaver.domain.models import (
    ConditionSnapshot,
    RankedRecommendation,
    RecommendationRun,
    ShorelineSegment,
    TravelEstimate,
    TripRequest,
)
from geoweaver.scoring.scorer import DEMONSTRATION_NOTICE, MODEL_VERSION, rank_segments

MANUAL_INPUT_NOTICE = (
    "Offline decision support only: conditions and travel estimates were manually supplied and "
    "are not independently checked or refreshed by GeoWeaver. Confirm current official legal, "
    "weather, access, health, and safety information before a trip."
)
COMMON_LIMITATIONS = (
    "No live weather, warning, tide, closure, advisory, or routing service was queried.",
    "Manual provenance is reported as supplied and is not independently verified by GeoWeaver.",
    "Tide-source applicability and distance are manually supplied; GeoWeaver does not calculate "
    "or independently verify station assignment.",
    "Recommendation scores are relative suitability scores, not catch probabilities.",
)


def _condition_mapping(
    segments: tuple[ShorelineSegment, ...],
    conditions: tuple[ConditionSnapshot, ...],
    trip: TripRequest,
) -> dict[str, ConditionSnapshot]:
    if not conditions:
        raise ValueError("at least one condition snapshot is required")
    known_ids = {segment.segment_id for segment in segments}
    condition_by_segment: dict[str, ConditionSnapshot] = {}
    seen_snapshot_ids: set[str] = set()
    for condition in conditions:
        if condition.snapshot_id in seen_snapshot_ids:
            raise ValueError(f"duplicate condition snapshot ID {condition.snapshot_id!r}")
        seen_snapshot_ids.add(condition.snapshot_id)
        if condition.valid_at != trip.target_datetime:
            raise ValueError(
                f"condition snapshot {condition.snapshot_id!r} does not match the trip target time"
            )
        if condition.retrieved_at is None:
            raise ValueError(
                f"condition snapshot {condition.snapshot_id!r} is missing retrieval provenance"
            )
        if condition.retrieved_at > trip.target_datetime:
            raise ValueError(
                f"condition snapshot {condition.snapshot_id!r} was retrieved after the trip time"
            )
        unknown_ids = set(condition.applicable_segment_ids).difference(known_ids)
        if unknown_ids:
            raise ValueError(
                f"condition snapshot {condition.snapshot_id!r} references unknown segment IDs: "
                + ", ".join(sorted(unknown_ids))
            )
        for segment_id in condition.applicable_segment_ids:
            if segment_id in condition_by_segment:
                previous = condition_by_segment[segment_id]
                raise ValueError(
                    f"condition snapshots {previous.snapshot_id!r} and "
                    f"{condition.snapshot_id!r} both apply to segment {segment_id!r}"
                )
            condition_by_segment[segment_id] = condition
    missing_ids = known_ids.difference(condition_by_segment)
    if missing_ids:
        raise ValueError(
            "condition snapshots do not apply to segment IDs: " + ", ".join(sorted(missing_ids))
        )
    return condition_by_segment


def _travel_mapping(
    segments: tuple[ShorelineSegment, ...],
    estimates: tuple[TravelEstimate, ...],
    trip: TripRequest,
) -> dict[str, TravelEstimate]:
    known_ids = {segment.segment_id for segment in segments}
    travel_by_segment: dict[str, TravelEstimate] = {}
    for estimate in estimates:
        if estimate.segment_id in travel_by_segment:
            raise ValueError(f"duplicate travel estimate for {estimate.segment_id!r}")
        if estimate.segment_id not in known_ids:
            raise ValueError(
                f"travel estimate references unknown segment ID {estimate.segment_id!r}"
            )
        if estimate.origin_label != trip.origin_label:
            raise ValueError(
                f"travel estimate for {estimate.segment_id!r} does not use trip origin "
                f"{trip.origin_label!r}"
            )
        if estimate.retrieved_at is None:
            raise ValueError(
                f"travel estimate for {estimate.segment_id!r} is missing retrieval provenance"
            )
        if estimate.retrieved_at > trip.target_datetime:
            raise ValueError(
                f"travel estimate for {estimate.segment_id!r} was retrieved after the trip time"
            )
        travel_by_segment[estimate.segment_id] = estimate
    return travel_by_segment


def _deterministic_run_id(
    segments: tuple[ShorelineSegment, ...],
    trip: TripRequest,
    conditions: tuple[ConditionSnapshot, ...],
    travel_estimates: tuple[TravelEstimate, ...],
) -> str:
    payload = repr(
        (
            MODEL_VERSION,
            tuple(sorted(segments, key=lambda item: item.segment_id)),
            trip,
            tuple(
                (
                    item,
                    item.retrieved_at,
                    item.scope_type,
                    item.scope_id,
                )
                for item in sorted(conditions, key=lambda item: item.snapshot_id)
            ),
            tuple(
                (item, item.retrieved_at)
                for item in sorted(travel_estimates, key=lambda item: item.segment_id)
            ),
        )
    ).encode()
    return f"run-{hashlib.sha256(payload).hexdigest()[:16]}"


def _add_input_provenance(
    recommendation: RankedRecommendation,
    condition: ConditionSnapshot,
    travel: TravelEstimate | None,
    *,
    is_demo: bool,
) -> RankedRecommendation:
    if is_demo:
        missing = recommendation.missing_or_stale_information
        limitations = recommendation.strongest_limitations
    else:
        replacements = {
            "Condition snapshot is explicitly marked as inferred demonstration data.": (
                "Condition snapshot is explicitly marked as inferred data."
            ),
            "Travel time is an inferred manual demonstration estimate.": (
                "Travel time is an inferred manual estimate."
            ),
            "No material limitation is represented in the supplied demo inputs.": (
                "No material limitation is represented in the supplied inputs."
            ),
        }
        missing = tuple(
            replacements.get(item, item) for item in recommendation.missing_or_stale_information
        )
        limitations = tuple(
            replacements.get(item, item) for item in recommendation.strongest_limitations
        )
    return replace(
        recommendation,
        missing_or_stale_information=missing,
        strongest_limitations=limitations,
        condition_snapshot_id=condition.snapshot_id,
        travel_source_ref=travel.source_ref if travel else None,
        travel_retrieved_at=travel.retrieved_at if travel else None,
        travel_evidence_state=travel.evidence_state if travel else None,
    )


def rank_trip(
    segments: tuple[ShorelineSegment, ...],
    trip: TripRequest,
    conditions: tuple[ConditionSnapshot, ...],
    travel_estimates: tuple[TravelEstimate, ...],
) -> RecommendationRun:
    """Rank a complete file-supplied trip without inventing missing favourable values."""
    segment_ids = [segment.segment_id for segment in segments]
    if not segments:
        raise ValueError("at least one shoreline segment is required")
    if len(set(segment_ids)) != len(segment_ids):
        raise ValueError("segments must not contain duplicate segment IDs")
    condition_by_segment = _condition_mapping(segments, conditions, trip)
    travel_by_segment = _travel_mapping(segments, travel_estimates, trip)
    preferences = trip.preferences
    is_demo = trip.data_classification is DataClassification.SYNTHETIC_DEMO

    assessments: list[RankedRecommendation] = []
    for segment in segments:
        condition = condition_by_segment[segment.segment_id]
        travel = travel_by_segment.get(segment.segment_id)
        single_run = rank_segments(
            (segment,),
            condition,
            preferences,
            (travel,) if travel else (),
        )
        assessments.append(
            _add_input_provenance(
                single_run.recommendations[0],
                condition,
                travel,
                is_demo=is_demo,
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
    sorted_conditions = tuple(sorted(conditions, key=lambda item: item.snapshot_id))
    sorted_travel = tuple(sorted(travel_estimates, key=lambda item: item.segment_id))
    return RecommendationRun(
        run_id=(
            trip.run_id or _deterministic_run_id(segments, trip, sorted_conditions, sorted_travel)
        ),
        application="CastNetGPT v0.1",
        generated_at=trip.target_datetime,
        model_version=MODEL_VERSION,
        condition=sorted_conditions[0],
        preferences=preferences,
        travel_estimates=sorted_travel,
        recommendations=ranked,
        demonstration_notice=DEMONSTRATION_NOTICE if is_demo else MANUAL_INPUT_NOTICE,
        trip_request=trip,
        condition_snapshots=sorted_conditions,
        input_classification=trip.data_classification,
        limitations=COMMON_LIMITATIONS,
    )
