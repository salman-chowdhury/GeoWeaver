"""Readable Markdown report with evidence and gate explanations."""

from geoweaver.domain.models import RankedRecommendation, RecommendationRun, Restriction


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
        f"retrieved: {restriction.retrieved_at.isoformat()}; reason: {restriction.reason}"
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
            empty_message="None in the supplied demonstration inputs.",
        )
    )
    lines.extend(["", "### Missing or stale information", ""])
    lines.extend(
        _bullet_list(
            recommendation.missing_or_stale_information,
            empty_message="None identified in the supplied demonstration inputs.",
        )
    )
    lines.extend(["", "### Legal and health evidence", ""])
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
    lines = [
        "# CastNetGPT v0.1 Demonstration Ranking",
        "",
        f"> **Warning:** {run.demonstration_notice}",
        "",
        f"- **Run ID:** `{run.run_id}`",
        f"- **Model version:** `{run.model_version}`",
        f"- **Synthetic condition time:** {condition.valid_at.isoformat()}",
        f"- **Tide stage:** `{condition.tide_stage.value}`",
        f"- **Wind:** {condition.wind_speed_kph} km/h",
        f"- **Gusts:** {condition.gust_speed_kph} km/h",
        f"- **Usable daylight:** {condition.usable_daylight_minutes} minutes",
        f"- **Severe-weather warning:** {condition.severe_weather_warning}",
        (
            "- **Lightning/severe-thunderstorm risk:** "
            f"{condition.lightning_or_severe_thunderstorm_risk}"
        ),
        f"- **Footing marked safe:** {condition.footing_safe}",
        f"- **Conditions inferred:** {condition.inferred}",
        f"- **Weather status verified:** {condition.weather_status_verified}",
        f"- **Footing status verified:** {condition.footing_status_verified}",
        f"- **Tide status verified:** {condition.tide_status_verified}",
        f"- **Daylight status verified:** {condition.daylight_status_verified}",
        f"- **Applicable segments:** {', '.join(condition.applicable_segment_ids)}",
        f"- **Weather evidence:** {', '.join(condition.weather_source_refs) or 'Missing'}",
        f"- **Footing evidence:** {', '.join(condition.footing_source_refs) or 'Missing'}",
        f"- **Tide evidence:** {', '.join(condition.tide_source_refs) or 'Missing'}",
        f"- **Daylight evidence:** {', '.join(condition.daylight_source_refs) or 'Missing'}",
        "",
        "## Demonstration preferences",
        "",
        f"- Skill level: `{preferences.skill_level.value}`",
        f"- Family suitability required: {preferences.require_family_suitable}",
        f"- Minimum family rating: {preferences.minimum_family_suitability}/5",
        f"- Minimum casting-space rating: {preferences.minimum_casting_space_rating}/5",
        f"- Minimum usable daylight: {preferences.minimum_usable_daylight_minutes} minutes",
        f"- Desired privacy rating: {preferences.desired_privacy_rating}/5",
        f"- Maximum travel time: {preferences.maximum_travel_minutes} minutes",
        "",
    ]
    for recommendation in run.recommendations:
        lines.extend(_recommendation_section(recommendation))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
