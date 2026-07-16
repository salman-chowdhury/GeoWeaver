"""Stable JSON serialization for recommendation runs."""

import json

from geoweaver.domain.models import (
    ConditionSnapshot,
    RankedRecommendation,
    RecommendationRun,
    Restriction,
    SourceProvenance,
)


def _restriction_document(restriction: Restriction) -> dict[str, object]:
    return {
        "restriction_id": restriction.restriction_id,
        "restriction_type": restriction.restriction_type,
        "status": restriction.status.value,
        "authority": restriction.authority,
        "source_ref": restriction.source_ref,
        "reason": restriction.reason,
        "effective_from": (
            restriction.effective_from.isoformat() if restriction.effective_from else None
        ),
        "effective_to": restriction.effective_to.isoformat() if restriction.effective_to else None,
        "retrieved_at": restriction.retrieved_at.isoformat(),
        "evidence_state": restriction.evidence_state.value,
    }


def _provenance_document(provenance: SourceProvenance) -> dict[str, object]:
    return {
        "authority": provenance.authority,
        "source_ref": provenance.source_ref,
        "retrieved_at": provenance.retrieved_at.isoformat(),
        "evidence_state": provenance.evidence_state.value,
    }


def _recommendation_document(recommendation: RankedRecommendation) -> dict[str, object]:
    return {
        "rank": recommendation.rank,
        "segment_id": recommendation.segment_id,
        "name": recommendation.name,
        "region": recommendation.region,
        "waterway": recommendation.waterway,
        "eligible": recommendation.eligibility,
        "final_score": recommendation.score.final_score,
        "confidence_score": recommendation.confidence_score,
        "confidence_band": recommendation.confidence_band.value,
        "component_scores": recommendation.score.suitability_component_scores(),
        "diagnostic_components": {"data_quality": recommendation.score.data_quality},
        "strongest_positive_factors": list(recommendation.strongest_positive_factors),
        "highest_scoring_components": list(recommendation.highest_scoring_components),
        "strongest_limitations": list(recommendation.strongest_limitations),
        "hard_gate_failures": [
            {"gate": failure.gate, "reason": failure.reason}
            for failure in recommendation.constraints.failures
        ],
        "missing_or_stale_information": list(recommendation.missing_or_stale_information),
        "applicable_restrictions": [
            _restriction_document(restriction)
            for restriction in recommendation.applicable_restrictions
        ],
        "health_advisory_evidence": _restriction_document(recommendation.health_advisory_evidence),
        "legal_status_evidence": _provenance_document(recommendation.legal_status_evidence),
        "activity_permission_evidence": _provenance_document(
            recommendation.activity_permission_evidence
        ),
        "restriction_review_evidence": _provenance_document(
            recommendation.restriction_review_evidence
        ),
        "verification_status": recommendation.verification_status.value,
        "source_refs": list(recommendation.source_refs),
        "data_last_updated": recommendation.data_last_updated.isoformat(),
        "travel_time_minutes": recommendation.travel_time_minutes,
        "travel_origin": recommendation.travel_origin,
        "condition_snapshot_id": recommendation.condition_snapshot_id,
        "travel_provenance": (
            {
                "source_ref": recommendation.travel_source_ref,
                "retrieved_at": recommendation.travel_retrieved_at.isoformat(),
                "evidence_state": recommendation.travel_evidence_state.value,
            }
            if recommendation.travel_source_ref
            and recommendation.travel_retrieved_at
            and recommendation.travel_evidence_state
            else None
        ),
        "model_version": recommendation.model_version,
    }


def _condition_document(condition: ConditionSnapshot) -> dict[str, object]:
    weather_warning_status = (
        "active"
        if condition.severe_weather_warning is True
        else "clear"
        if condition.severe_weather_warning is False
        else "unknown"
    )
    lightning_status = (
        "active"
        if condition.lightning_or_severe_thunderstorm_risk is True
        else "clear"
        if condition.lightning_or_severe_thunderstorm_risk is False
        else "unknown"
    )
    footing_status = (
        "safe"
        if condition.footing_safe is True
        else "unsafe"
        if condition.footing_safe is False
        else "unknown"
    )
    return {
        "snapshot_id": condition.snapshot_id,
        "applicability": {
            "scope_type": condition.scope_type.value,
            "scope_id": condition.scope_id,
            "resolved_segment_ids": list(condition.applicable_segment_ids),
        },
        "applicable_segment_ids": list(condition.applicable_segment_ids),
        "observed_or_predicted_at": condition.valid_at.isoformat(),
        "valid_at": condition.valid_at.isoformat(),
        "retrieved_at": condition.retrieved_at.isoformat() if condition.retrieved_at else None,
        "tide_stage": condition.tide_stage.value,
        "weather_warning_status": weather_warning_status,
        "lightning_thunderstorm_status": lightning_status,
        "footing_status": footing_status,
        "severe_weather_warning": condition.severe_weather_warning,
        "lightning_or_severe_thunderstorm_risk": (condition.lightning_or_severe_thunderstorm_risk),
        "footing_safe": condition.footing_safe,
        "usable_daylight_minutes": condition.usable_daylight_minutes,
        "wind_speed_kph": condition.wind_speed_kph,
        "gust_speed_kph": condition.gust_speed_kph,
        "data_freshness_minutes": condition.data_freshness_minutes,
        "evidence_state": condition.evidence_state.value,
        "inferred": condition.inferred,
        "weather_status_verified": condition.weather_status_verified,
        "footing_status_verified": condition.footing_status_verified,
        "tide_status_verified": condition.tide_status_verified,
        "daylight_status_verified": condition.daylight_status_verified,
        "weather_source_refs": list(condition.weather_source_refs),
        "footing_source_refs": list(condition.footing_source_refs),
        "tide_source_refs": list(condition.tide_source_refs),
        "daylight_source_refs": list(condition.daylight_source_refs),
        "source_refs": list(condition.source_refs),
        "tide_source_applicability": (
            {
                "source_location_id": condition.tide_source_applicability.source_location_id,
                "source_location_label": (
                    condition.tide_source_applicability.source_location_label
                ),
                "distance_to_scope_km": (condition.tide_source_applicability.distance_to_scope_km),
                "assignment_method": (condition.tide_source_applicability.assignment_method.value),
                "applicability_source_ref": (
                    condition.tide_source_applicability.applicability_source_ref
                ),
                "retrieved_at": condition.tide_source_applicability.retrieved_at.isoformat(),
                "evidence_state": condition.tide_source_applicability.evidence_state.value,
            }
            if condition.tide_source_applicability
            else None
        ),
    }


def report_document(run: RecommendationRun) -> dict[str, object]:
    """Build the versioned, machine-readable report document."""
    condition = run.condition
    preferences = run.preferences
    trip = run.trip_request
    trip_document = (
        {
            "run_id": trip.run_id,
            "origin_label": trip.origin_label,
            "target_datetime": trip.target_datetime.isoformat(),
            "maximum_travel_minutes": trip.maximum_travel_minutes,
            "skill_level": trip.skill_level.value,
            "family_suitability_required": trip.family_suitability_required,
            "minimum_family_rating": trip.minimum_family_rating,
            "desired_privacy_rating": trip.desired_privacy_rating,
            "minimum_casting_space_rating": trip.minimum_casting_space_rating,
            "intended_activity": trip.intended_activity.value,
            "minimum_usable_daylight_minutes": trip.minimum_usable_daylight_minutes,
            "notes": trip.notes,
            "data_classification": trip.data_classification.value,
        }
        if trip
        else {
            "run_id": None,
            "origin_label": (
                run.travel_estimates[0].origin_label if run.travel_estimates else None
            ),
            "target_datetime": condition.valid_at.isoformat(),
            "maximum_travel_minutes": preferences.maximum_travel_minutes,
            "skill_level": preferences.skill_level.value,
            "family_suitability_required": preferences.require_family_suitable,
            "minimum_family_rating": preferences.minimum_family_suitability,
            "desired_privacy_rating": preferences.desired_privacy_rating,
            "minimum_casting_space_rating": preferences.minimum_casting_space_rating,
            "intended_activity": "cast_net_fishing",
            "minimum_usable_daylight_minutes": preferences.minimum_usable_daylight_minutes,
            "notes": None,
            "data_classification": run.input_classification.value,
        }
    )
    return {
        "schema_version": "geoweaver-report-v0.1",
        "application": run.application,
        "run_id": run.run_id,
        "generated_at": run.generated_at.isoformat(),
        "model_version": run.model_version,
        "input_classification": run.input_classification.value,
        "notice": run.demonstration_notice,
        "demonstration_notice": run.demonstration_notice,
        "trip_request": trip_document,
        "condition_snapshot": (
            _condition_document(condition) if len(run.condition_snapshots) == 1 else None
        ),
        "condition_snapshots": [
            _condition_document(snapshot) for snapshot in run.condition_snapshots
        ],
        "preferences": {
            "skill_level": preferences.skill_level.value,
            "require_family_suitable": preferences.require_family_suitable,
            "minimum_family_suitability": preferences.minimum_family_suitability,
            "minimum_casting_space_rating": preferences.minimum_casting_space_rating,
            "minimum_usable_daylight_minutes": preferences.minimum_usable_daylight_minutes,
            "desired_privacy_rating": preferences.desired_privacy_rating,
            "maximum_travel_minutes": preferences.maximum_travel_minutes,
        },
        "travel_estimates": [
            {
                "segment_id": estimate.segment_id,
                "origin_label": estimate.origin_label,
                "minutes": estimate.minutes,
                "source_ref": estimate.source_ref,
                "retrieved_at": (
                    estimate.retrieved_at.isoformat() if estimate.retrieved_at else None
                ),
                "evidence_state": estimate.evidence_state.value,
                "inferred": estimate.inferred,
            }
            for estimate in run.travel_estimates
        ],
        "recommendations": [
            _recommendation_document(recommendation) for recommendation in run.recommendations
        ],
        "limitations": list(run.limitations),
    }


def render_json(run: RecommendationRun) -> str:
    """Render a deterministic, pretty-printed JSON report."""
    return json.dumps(report_document(run), indent=2, sort_keys=True) + "\n"
