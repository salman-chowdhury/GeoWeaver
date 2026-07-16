"""Deterministic, plain-language explanations for auditable scores."""

from geoweaver.domain.models import ConstraintResult, ScoreBreakdown

COMPONENT_LABELS = {
    "habitat_opportunity": "Habitat opportunity",
    "environmental_condition_match": "Environmental-condition match",
    "access_and_usability": "Access and usability",
    "privacy": "Privacy",
    "family_suitability": "Family suitability",
    "safety_and_risk": "Safety and risk",
    "travel_efficiency": "Travel efficiency",
    "data_quality": "Data quality",
}

POSITIVE_FACTOR_THRESHOLD = 60


def build_explanations(
    score: ScoreBreakdown,
    constraints: ConstraintResult,
    missing_or_stale_information: tuple[str, ...],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Select the strongest components and most decision-relevant limitations."""
    component_scores = score.suitability_component_scores()
    strongest = sorted(component_scores.items(), key=lambda item: (-item[1], item[0]))[:3]
    if constraints.eligible:
        positive_factors = tuple(
            f"{COMPONENT_LABELS[name]} is a meaningful positive factor ({value}/100)."
            for name, value in strongest
            if value > POSITIVE_FACTOR_THRESHOLD
        )
        highest_scoring_components = (
            ()
            if positive_factors
            else tuple(
                f"Highest-scoring component: {COMPONENT_LABELS[name]} ({value}/100); "
                f"no component exceeds {POSITIVE_FACTOR_THRESHOLD}/100."
                for name, value in strongest
            )
        )
    else:
        positive_factors = ()
        highest_scoring_components = tuple(
            f"Pre-gate component only — {COMPONENT_LABELS[name]} scores {value}/100; "
            "hard-gate failures still make this segment ineligible."
            for name, value in strongest
        )

    limitations: list[str] = [f"Hard gate — {failure.reason}" for failure in constraints.failures]
    limitations.extend(missing_or_stale_information)
    weakest = sorted(component_scores.items(), key=lambda item: (item[1], item[0]))
    limitations.extend(
        f"{COMPONENT_LABELS[name]} is comparatively weak ({value}/100)."
        for name, value in weakest
        if value < 60
    )

    unique_limitations: list[str] = []
    for limitation in limitations:
        if limitation not in unique_limitations:
            unique_limitations.append(limitation)
        if len(unique_limitations) == 3:
            break
    if not unique_limitations:
        unique_limitations.append(
            "No material limitation is represented in the supplied demo inputs."
        )
    return positive_factors, highest_scoring_components, tuple(unique_limitations)
