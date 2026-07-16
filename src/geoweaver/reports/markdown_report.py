"""Readable Markdown report with evidence and gate explanations."""

from geoweaver.domain.models import (
    RankedRecommendation,
    RecommendationRun,
    Restriction,
    SourceProvenance,
)


def _bullet_list(items: tuple[str, ...], *, empty_message: str) -> list[str]:
    if not items:
        return [f"- {empty_message}"]
    return [f"- {item}" for item in items]


def _restriction_bullet(restriction: Restriction) -> str:
    effective_from = (
        restriction.effective_from.isoformat() if restriction.effective_from else "open"
    )
    effective_to = restriction.effective_to.isoformat() if restriction.effective_to else "open"
    return (
        f"`{restriction.restriction_id}` — status `{restriction.status.value}`; "
        f"authority: {restriction.authority}; source: {restriction.source_ref}; "
        f"effective: {effective_from} to {effective_to}; "
        f"retrieved: {restriction.retrieved_at.isoformat()}; "
        f"state: `{restriction.evidence_state.value}`; reason: {restriction.reason}"
    )


def _provenance_bullet(provenance: SourceProvenance) -> str:
    return (
        f"authority: {provenance.authority}; source: {provenance.source_ref}; "
        f"retrieved: {provenance.retrieved_at.isoformat()}; "
        f"state: `{provenance.evidence_state.value}`"
    )


def _recommendation_section(recommendation: RankedRecommendation) -> list[str]:
    eligibility = "Eligible" if recommendation.eligibility else "Ineligible (hard-gated)"
    lines = [
        f"## {recommendation.rank}. {recommendation.name}",
        "",
        f"- **Segment:** `{recommendation.segment_id}`",
        f"- **Context:** {recommendation.region} — {recommendation.waterway}",
        f"- **Eligibility:** {eligibility}",
        f"- **Recommendation score:** {recommendation.score.final_score}/100",
        (
            f"- **Confidence:** {recommendation.confidence_band.value} "
            f"({recommendation.confidence_score}/100)"
        ),
        f"- **Verification:** `{recommendation.verification_status.value}`",
        f"- **Data last updated:** {recommendation.data_last_updated.isoformat()}",
        f"- **Source references:** {', '.join(recommendation.source_refs)}",
        (
            f"- **Travel:** {recommendation.travel_time_minutes} minutes from "
            f"{recommendation.travel_origin}"
            if recommendation.travel_time_minutes is not None
            else "- **Travel:** Missing"
        ),
        f"- **Condition snapshot:** `{recommendation.condition_snapshot_id or 'unspecified'}`",
        (
            f"- **Travel provenance:** {recommendation.travel_source_ref}; retrieved "
            f"{recommendation.travel_retrieved_at.isoformat()}; state "
            f"`{recommendation.travel_evidence_state.value}`"
            if recommendation.travel_source_ref
            and recommendation.travel_retrieved_at
            and recommendation.travel_evidence_state
            else "- **Travel provenance:** Missing"
        ),
        f"- **Model:** `{recommendation.model_version}`",
        "",
        "### Suitability component scores",
        "",
        "| Component | Score |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {name.replace('_', ' ').title()} | {value}/100 |"
        for name, value in recommendation.score.suitability_component_scores().items()
    )
    lines.extend(
        [
            "",
            "### Unweighted diagnostics",
            "",
            f"- Data quality: {recommendation.score.data_quality}/100 "
            "(diagnostic only; its evidence inputs affect confidence, not recommendation score)",
        ]
    )
    lines.extend(["", "### Meaningful positive factors", ""])
    lines.extend(
        _bullet_list(
            recommendation.strongest_positive_factors,
            empty_message="No positive factor was identified.",
        )
    )
    if recommendation.highest_scoring_components:
        lines.extend(["", "### Highest-scoring components", ""])
        lines.extend(
            _bullet_list(
                recommendation.highest_scoring_components,
                empty_message="No component score was available.",
            )
        )
    lines.extend(["", "### Strongest limitations", ""])
    lines.extend(
        _bullet_list(
            recommendation.strongest_limitations,
            empty_message="No material limitation was represented.",
        )
    )
    lines.extend(["", "### Hard-gate failures", ""])
    lines.extend(
        _bullet_list(
            tuple(
                f"`{failure.gate}`: {failure.reason}"
                for failure in recommendation.constraints.failures
            ),
            empty_message="None in the supplied inputs.",
        )
    )
    lines.extend(["", "### Missing or stale information", ""])
    lines.extend(
        _bullet_list(
            recommendation.missing_or_stale_information,
            empty_message="None identified in the supplied inputs.",
        )
    )
    lines.extend(["", "### Legal and health evidence", ""])
    lines.append(f"- Legal status: {_provenance_bullet(recommendation.legal_status_evidence)}")
    lines.append(
        f"- Activity permission: {_provenance_bullet(recommendation.activity_permission_evidence)}"
    )
    lines.append(
        f"- Closure review: {_provenance_bullet(recommendation.restriction_review_evidence)}"
    )
    lines.append(
        f"- Health advisory: {_restriction_bullet(recommendation.health_advisory_evidence)}"
    )
    lines.extend(
        _bullet_list(
            tuple(
                _restriction_bullet(restriction)
                for restriction in recommendation.applicable_restrictions
            ),
            empty_message="No additional restriction applies at the recommendation time.",
        )
    )
    return lines


def render_markdown(run: RecommendationRun) -> str:
    """Render an explanation-first Markdown report."""
    condition = run.condition
    preferences = run.preferences
    trip = run.trip_request
    is_demo = run.input_classification.value == "synthetic_demo"
    origin_label = (
        trip.origin_label
        if trip
        else run.travel_estimates[0].origin_label
        if run.travel_estimates
        else "Missing"
    )
    target_datetime = trip.target_datetime if trip else condition.valid_at
    lines = [
        ("# CastNetGPT v0.1 Demonstration Ranking" if is_demo else "# CastNetGPT v0.1 Ranking"),
        "",
        f"> **Warning:** {run.demonstration_notice}",
        "",
        f"- **Run ID:** `{run.run_id}`",
        f"- **Model version:** `{run.model_version}`",
        f"- **Input classification:** `{run.input_classification.value}`",
        "",
        "## Trip request",
        "",
        f"- Origin: {origin_label}",
        f"- Target date and time: {target_datetime.isoformat()}",
        f"- Skill level: `{preferences.skill_level.value}`",
        f"- Family suitability required: {preferences.require_family_suitable}",
        f"- Minimum family rating: {preferences.minimum_family_suitability}/5",
        f"- Minimum casting-space rating: {preferences.minimum_casting_space_rating}/5",
        f"- Minimum usable daylight: {preferences.minimum_usable_daylight_minutes} minutes",
        f"- Desired privacy rating: {preferences.desired_privacy_rating}/5",
        f"- Maximum travel time: {preferences.maximum_travel_minutes} minutes",
        f"- Intended activity: `{trip.intended_activity.value if trip else 'cast_net_fishing'}`",
        f"- Notes: {(trip.notes if trip and trip.notes else 'None supplied')}",
        "",
    ]
    lines.extend(["## Condition snapshots", ""])
    for snapshot in run.condition_snapshots:
        retrieved_at = snapshot.retrieved_at.isoformat() if snapshot.retrieved_at else "Missing"
        lines.extend(
            [
                f"### `{snapshot.snapshot_id}`",
                "",
                f"- Scope: `{snapshot.scope_type.value}` / `{snapshot.scope_id}`",
                f"- Resolved segments: {', '.join(snapshot.applicable_segment_ids)}",
                f"- Observed or predicted at: {snapshot.valid_at.isoformat()}",
                f"- Retrieved at: {retrieved_at}",
                f"- Evidence state: `{snapshot.evidence_state.value}`",
                f"- Tide stage: `{snapshot.tide_stage.value}`",
                f"- Wind / gusts: {snapshot.wind_speed_kph} / {snapshot.gust_speed_kph} km/h",
                f"- Severe-weather warning: {snapshot.severe_weather_warning}",
                "- Lightning/severe-thunderstorm risk: "
                f"{snapshot.lightning_or_severe_thunderstorm_risk}",
                f"- Footing marked safe: {snapshot.footing_safe}",
                f"- Usable daylight: {snapshot.usable_daylight_minutes} minutes",
                f"- Weather evidence: {', '.join(snapshot.weather_source_refs) or 'Missing'}",
                f"- Footing evidence: {', '.join(snapshot.footing_source_refs) or 'Missing'}",
                f"- Tide evidence: {', '.join(snapshot.tide_source_refs) or 'Missing'}",
                (
                    "- Tide-source applicability: "
                    f"`{snapshot.tide_source_applicability.source_location_id}` "
                    f"({snapshot.tide_source_applicability.source_location_label}), "
                    f"{snapshot.tide_source_applicability.distance_to_scope_km:g} km from scope; "
                    f"assignment `{snapshot.tide_source_applicability.assignment_method.value}`; "
                    f"source {snapshot.tide_source_applicability.applicability_source_ref}; "
                    f"retrieved {snapshot.tide_source_applicability.retrieved_at.isoformat()}; "
                    f"state `{snapshot.tide_source_applicability.evidence_state.value}`"
                    if snapshot.tide_source_applicability
                    else "- Tide-source applicability: Missing"
                ),
                f"- Daylight evidence: {', '.join(snapshot.daylight_source_refs) or 'Missing'}",
                "",
            ]
        )
    lines.extend(["## Manual travel estimates", ""])
    if run.travel_estimates:
        lines.extend(
            [
                "| Segment | Minutes | Origin | Source | Retrieved | State |",
                "|---|---:|---|---|---|---|",
            ]
        )
        lines.extend(
            f"| `{estimate.segment_id}` | {estimate.minutes} | {estimate.origin_label} | "
            f"{estimate.source_ref} | "
            f"{estimate.retrieved_at.isoformat() if estimate.retrieved_at else 'Missing'} | "
            f"`{estimate.evidence_state.value}` |"
            for estimate in run.travel_estimates
        )
    else:
        lines.append("- No travel estimates were supplied; travel gates fail closed.")
    lines.extend(["", "## Run limitations", ""])
    lines.extend(_bullet_list(run.limitations, empty_message="No run-level limitation supplied."))
    lines.append("")
    for recommendation in run.recommendations:
        lines.extend(_recommendation_section(recommendation))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
