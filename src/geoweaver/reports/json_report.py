"""Stable JSON serialization for recommendation runs."""

import json

from geoweaver.domain.models import RankedRecommendation, RecommendationRun, Restriction


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
        "verification_status": recommendation.verification_status.value,
        "source_refs": list(recommendation.source_refs),
        "data_last_updated": recommendation.data_last_updated.isoformat(),
        "travel_time_minutes": recommendation.travel_time_minutes,
        "travel_origin": recommendation.travel_origin,
        "model_version": recommendation.model_version,
    }


def report_document(run: RecommendationRun) -> dict[str, object]:
    """Build the versioned, machine-readable report document."""
    condition = run.condition
    preferences = run.preferences
    return {
        "schema_version": "geoweaver-report-v0.1",
        "application": run.application,
        "run_id": run.run_id,
        "generated_at": run.generated_at.isoformat(),
        "model_version": run.model_version,
        "demonstration_notice": run.demonstration_notice,
        "condition_snapshot": {
            "snapshot_id": condition.snapshot_id,
            "applicable_segment_ids": list(condition.applicable_segment_ids),
            "valid_at": condition.valid_at.isoformat(),
            "tide_stage": condition.tide_stage.value,
            "severe_weather_warning": condition.severe_weather_warning,
            "lightning_or_severe_thunderstorm_risk": (
                condition.lightning_or_severe_thunderstorm_risk
            ),
            "footing_safe": condition.footing_safe,
            "usable_daylight_minutes": condition.usable_daylight_minutes,
            "wind_speed_kph": condition.wind_speed_kph,
            "gust_speed_kph": condition.gust_speed_kph,
            "data_freshness_minutes": condition.data_freshness_minutes,
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
        },
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
                "inferred": estimate.inferred,
            }
            for estimate in run.travel_estimates
        ],
        "recommendations": [
            _recommendation_document(recommendation) for recommendation in run.recommendations
        ],
    }


def render_json(run: RecommendationRun) -> str:
    """Render a deterministic, pretty-printed JSON report."""
    return json.dumps(report_document(run), indent=2, sort_keys=True) + "\n"
