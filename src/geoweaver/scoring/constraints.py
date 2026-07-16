"""Fail-closed hard gates for the CastNetGPT v0.1 demonstration."""

from datetime import timedelta

from geoweaver.domain.enums import (
    ActivityPermissionStatus,
    BankSlopeClass,
    PublicAccessState,
    RestrictionStatus,
    TidalStatus,
    TideStage,
    VerificationState,
)
from geoweaver.domain.models import (
    ConditionSnapshot,
    ConstraintResult,
    GateCheck,
    ShorelineSegment,
    TravelEstimate,
    UserPreferences,
)

MAX_CRITICAL_CONDITION_AGE_MINUTES = 120
MAX_CRITICAL_SEGMENT_AGE_DAYS = 180
MAX_CRITICAL_SEGMENT_AGE = timedelta(days=MAX_CRITICAL_SEGMENT_AGE_DAYS)
MAX_SAFE_MUD_RISK = 3
MAX_SAFE_SUSTAINED_WIND_KPH = 40.0
MAX_SAFE_GUST_KPH = 60.0
MIN_SAFE_CASTING_SPACE_RATING = 1


def _access_check(segment: ShorelineSegment) -> GateCheck:
    status = segment.access.public_access_status
    if status is PublicAccessState.VERIFIED_PUBLIC:
        return GateCheck("public_access", True, "Public access is explicitly marked as verified.")
    if status is PublicAccessState.UNKNOWN:
        reason = "Critical access status is unknown; v0.1 fails closed."
    elif status is PublicAccessState.PROHIBITED:
        reason = "Public access is prohibited."
    else:
        reason = "Access is restricted and no permission workflow exists in v0.1."
    return GateCheck("public_access", False, reason)


def _legal_information_check(segment: ShorelineSegment) -> GateCheck:
    if segment.legal_status_known:
        return GateCheck("legal_information", True, "Legal status is explicitly recorded.")
    return GateCheck(
        "legal_information",
        False,
        "Critical legal status is unknown; absence of a known closure is not evidence of legality.",
    )


def _activity_permission_check(segment: ShorelineSegment) -> GateCheck:
    status = segment.activity_permission_status
    if status is ActivityPermissionStatus.PERMITTED:
        return GateCheck(
            "activity_permission", True, "The intended activity is explicitly marked permitted."
        )
    if status is ActivityPermissionStatus.PROHIBITED:
        reason = "The intended activity is explicitly prohibited."
    else:
        reason = "Permission for the intended activity is unknown; v0.1 fails closed."
    return GateCheck("activity_permission", False, reason)


def _tidal_eligibility_check(segment: ShorelineSegment) -> GateCheck:
    if segment.tidal_status is TidalStatus.TIDAL:
        return GateCheck("tidal_eligibility", True, "The segment is explicitly marked tidal.")
    if segment.tidal_status is TidalStatus.NON_TIDAL:
        reason = "The segment is non-tidal and is ineligible for this activity profile."
    else:
        reason = "Tidal eligibility is unknown; v0.1 fails closed."
    return GateCheck("tidal_eligibility", False, reason)


def _health_advisory_check(segment: ShorelineSegment, condition: ConditionSnapshot) -> GateCheck:
    evidence = segment.health_advisory_evidence
    if evidence.retrieved_at > condition.valid_at:
        return GateCheck(
            "health_advisory",
            False,
            "Health-advisory evidence was retrieved after the recommendation time.",
        )
    if not evidence.is_effective_at(condition.valid_at):
        return GateCheck(
            "health_advisory",
            False,
            "Health-advisory evidence does not apply at the recommendation time.",
        )
    if segment.health_advisory_status is RestrictionStatus.INACTIVE:
        return GateCheck("health_advisory", True, "No active health advisory is recorded.")
    if segment.health_advisory_status is RestrictionStatus.ACTIVE:
        reason = "An active health advisory applies."
    else:
        reason = "Health-advisory status is unknown; v0.1 fails closed."
    return GateCheck("health_advisory", False, reason)


def _closure_check(segment: ShorelineSegment, condition: ConditionSnapshot) -> GateCheck:
    applicable = [item for item in segment.restrictions if item.is_effective_at(condition.valid_at)]
    if any(item.retrieved_at > condition.valid_at for item in applicable):
        return GateCheck(
            "active_legal_closure",
            False,
            "Applicable restriction evidence was retrieved after the recommendation time.",
        )
    active = [item for item in applicable if item.status is RestrictionStatus.ACTIVE]
    unknown = [item for item in applicable if item.status is RestrictionStatus.UNKNOWN]
    if active:
        reasons = "; ".join(item.reason for item in active)
        return GateCheck("active_legal_closure", False, f"An active restriction applies: {reasons}")
    if unknown:
        return GateCheck(
            "active_legal_closure",
            False,
            "At least one applicable restriction has unknown status; v0.1 fails closed.",
        )
    return GateCheck(
        "active_legal_closure",
        True,
        "No applicable supplied restriction is active or unknown.",
    )


def _critical_condition_evidence_reason(
    condition: ConditionSnapshot,
    *,
    status_verified: bool,
    source_refs: tuple[str, ...],
    evidence_name: str,
) -> str | None:
    if not status_verified:
        return f"{evidence_name} status is not verified; v0.1 fails closed."
    if not source_refs:
        return f"{evidence_name} status has no source reference; v0.1 fails closed."
    if condition.data_freshness_minutes is None:
        return f"{evidence_name} freshness is missing; v0.1 fails closed."
    if condition.data_freshness_minutes > MAX_CRITICAL_CONDITION_AGE_MINUTES:
        return (
            f"{evidence_name} status is stale ({condition.data_freshness_minutes} minutes old); "
            "v0.1 fails closed."
        )
    return None


def _weather_check(condition: ConditionSnapshot) -> GateCheck:
    evidence_problem = _critical_condition_evidence_reason(
        condition,
        status_verified=condition.weather_status_verified,
        source_refs=condition.weather_source_refs,
        evidence_name="Severe-weather",
    )
    if evidence_problem is not None:
        return GateCheck("severe_weather", False, evidence_problem)
    if condition.severe_weather_warning is True:
        return GateCheck("severe_weather", False, "A severe-weather warning is active.")
    if condition.severe_weather_warning is None:
        return GateCheck(
            "severe_weather",
            False,
            "Severe-weather status is missing; v0.1 fails closed.",
        )
    if condition.lightning_or_severe_thunderstorm_risk is True:
        return GateCheck(
            "severe_weather",
            False,
            "Verified lightning or severe-thunderstorm risk is active.",
        )
    if condition.lightning_or_severe_thunderstorm_risk is None:
        return GateCheck(
            "severe_weather",
            False,
            "Lightning and severe-thunderstorm status is missing; v0.1 fails closed.",
        )
    if condition.wind_speed_kph is None:
        return GateCheck(
            "severe_weather", False, "Sustained wind speed is missing; v0.1 fails closed."
        )
    if condition.wind_speed_kph > MAX_SAFE_SUSTAINED_WIND_KPH:
        return GateCheck(
            "severe_weather",
            False,
            f"Sustained wind ({condition.wind_speed_kph:g} km/h) exceeds the safe v0.1 "
            f"threshold ({MAX_SAFE_SUSTAINED_WIND_KPH:g} km/h).",
        )
    if condition.gust_speed_kph is None:
        return GateCheck("severe_weather", False, "Gust speed is missing; v0.1 fails closed.")
    if condition.gust_speed_kph > MAX_SAFE_GUST_KPH:
        return GateCheck(
            "severe_weather",
            False,
            f"Gust speed ({condition.gust_speed_kph:g} km/h) exceeds the safe v0.1 "
            f"threshold ({MAX_SAFE_GUST_KPH:g} km/h).",
        )
    return GateCheck(
        "severe_weather",
        True,
        "Verified warning, lightning, sustained-wind, and gust checks are within thresholds.",
    )


def _tide_condition_check(condition: ConditionSnapshot) -> GateCheck:
    evidence_problem = _critical_condition_evidence_reason(
        condition,
        status_verified=condition.tide_status_verified,
        source_refs=condition.tide_source_refs,
        evidence_name="Tide",
    )
    if evidence_problem is not None:
        return GateCheck("tide_condition", False, evidence_problem)
    if condition.tide_stage is TideStage.UNKNOWN:
        return GateCheck("tide_condition", False, "Tide stage is missing; v0.1 fails closed.")
    return GateCheck("tide_condition", True, "Tide stage is verified and sourced.")


def _footing_check(segment: ShorelineSegment, condition: ConditionSnapshot) -> GateCheck:
    evidence_problem = _critical_condition_evidence_reason(
        condition,
        status_verified=condition.footing_status_verified,
        source_refs=condition.footing_source_refs,
        evidence_name="Footing",
    )
    if evidence_problem is not None:
        return GateCheck("safe_footing", False, evidence_problem)
    if segment.bank_slope_class is BankSlopeClass.UNKNOWN:
        return GateCheck("safe_footing", False, "Bank slope is unknown; v0.1 fails closed.")
    if segment.bank_slope_class is BankSlopeClass.STEEP:
        return GateCheck("safe_footing", False, "The bank slope is classified as steep.")
    if segment.environmental.mud_risk > MAX_SAFE_MUD_RISK:
        return GateCheck(
            "safe_footing",
            False,
            f"Mud-risk rating exceeds the safe v0.1 threshold ({MAX_SAFE_MUD_RISK}/5).",
        )
    if condition.footing_safe is True:
        return GateCheck(
            "safe_footing", True, "Current footing and stable terrain checks are safe."
        )
    if condition.footing_safe is False:
        reason = "The supplied footing condition is unsafe."
    else:
        reason = "Footing safety is missing; v0.1 fails closed."
    return GateCheck("safe_footing", False, reason)


def _casting_space_check(segment: ShorelineSegment, preferences: UserPreferences) -> GateCheck:
    actual = segment.access.casting_space_rating
    required = preferences.minimum_casting_space_rating
    if actual < MIN_SAFE_CASTING_SPACE_RATING:
        return GateCheck(
            "casting_space",
            False,
            "No usable casting footprint is recorded; the absolute safety minimum is 1/5.",
        )
    if actual >= required:
        return GateCheck(
            "casting_space",
            True,
            f"Casting-space rating {actual}/5 meets the required {required}/5.",
        )
    return GateCheck(
        "casting_space",
        False,
        f"Casting-space rating {actual}/5 is below the required {required}/5.",
    )


def _daylight_check(condition: ConditionSnapshot, preferences: UserPreferences) -> GateCheck:
    evidence_problem = _critical_condition_evidence_reason(
        condition,
        status_verified=condition.daylight_status_verified,
        source_refs=condition.daylight_source_refs,
        evidence_name="Daylight",
    )
    if evidence_problem is not None:
        return GateCheck("usable_daylight", False, evidence_problem)
    available = condition.usable_daylight_minutes
    required = preferences.minimum_usable_daylight_minutes
    if available is None:
        return GateCheck(
            "usable_daylight",
            False,
            "Usable daylight is missing; v0.1 fails closed.",
        )
    if available >= required:
        return GateCheck(
            "usable_daylight",
            True,
            f"Usable daylight ({available} minutes) meets the required {required} minutes.",
        )
    return GateCheck(
        "usable_daylight",
        False,
        f"Usable daylight ({available} minutes) is below the required {required} minutes.",
    )


def _family_check(segment: ShorelineSegment, preferences: UserPreferences) -> GateCheck:
    if not preferences.require_family_suitable:
        return GateCheck(
            "family_suitability", True, "Family suitability is not a hard requirement."
        )
    actual = segment.access.family_suitability
    required = preferences.minimum_family_suitability
    if actual >= required:
        return GateCheck(
            "family_suitability",
            True,
            f"Family-suitability rating {actual}/5 meets the required {required}/5.",
        )
    return GateCheck(
        "family_suitability",
        False,
        f"Family-suitability rating {actual}/5 is below the required {required}/5.",
    )


def _safety_information_check(segment: ShorelineSegment) -> GateCheck:
    if segment.safety_information_complete:
        return GateCheck(
            "critical_safety_information",
            True,
            "Critical stable safety fields are explicitly populated.",
        )
    return GateCheck(
        "critical_safety_information",
        False,
        "Critical stable safety information is incomplete; v0.1 fails closed.",
    )


def _availability_check(segment: ShorelineSegment) -> GateCheck:
    if segment.verification_status not in {
        VerificationState.TEMPORARILY_UNAVAILABLE,
        VerificationState.REJECTED,
    }:
        return GateCheck("record_availability", True, "The segment record is available for review.")
    return GateCheck(
        "record_availability",
        False,
        f"Verification state is {segment.verification_status.value!r}.",
    )


def _critical_record_freshness_check(
    segment: ShorelineSegment, condition: ConditionSnapshot
) -> GateCheck:
    age = condition.valid_at - segment.last_updated
    if age.total_seconds() < 0:
        return GateCheck(
            "critical_record_freshness",
            False,
            "Segment evidence timestamp is later than the recommendation time.",
        )
    if age > MAX_CRITICAL_SEGMENT_AGE:
        return GateCheck(
            "critical_record_freshness",
            False,
            f"Segment evidence is stale ({age.days} days old); v0.1 fails closed.",
        )
    return GateCheck(
        "critical_record_freshness",
        True,
        f"Segment evidence age ({age.days} days) is within the v0.1 threshold.",
    )


def _travel_time_check(
    segment: ShorelineSegment,
    preferences: UserPreferences,
    travel_estimate: TravelEstimate | None,
) -> GateCheck:
    if travel_estimate is None:
        return GateCheck(
            "travel_time",
            False,
            "Travel time is missing for this segment; v0.1 fails closed.",
        )
    if travel_estimate.segment_id != segment.segment_id:
        return GateCheck(
            "travel_time",
            False,
            "Travel estimate does not refer to this segment; v0.1 fails closed.",
        )
    if travel_estimate.minutes > preferences.maximum_travel_minutes:
        return GateCheck(
            "travel_time",
            False,
            f"Travel time ({travel_estimate.minutes} minutes) exceeds the "
            f"{preferences.maximum_travel_minutes}-minute limit.",
        )
    return GateCheck(
        "travel_time",
        True,
        f"Travel time ({travel_estimate.minutes} minutes) is within the "
        f"{preferences.maximum_travel_minutes}-minute limit.",
    )


def evaluate_constraints(
    segment: ShorelineSegment,
    condition: ConditionSnapshot,
    preferences: UserPreferences,
    travel_estimate: TravelEstimate | None,
) -> ConstraintResult:
    """Evaluate all v0.1 gates; unknown critical inputs are failures, never defaults."""
    return ConstraintResult(
        checks=(
            _access_check(segment),
            _legal_information_check(segment),
            _activity_permission_check(segment),
            _tidal_eligibility_check(segment),
            _health_advisory_check(segment, condition),
            _closure_check(segment, condition),
            _weather_check(condition),
            _tide_condition_check(condition),
            _footing_check(segment, condition),
            _casting_space_check(segment, preferences),
            _daylight_check(condition, preferences),
            _family_check(segment, preferences),
            _travel_time_check(segment, preferences, travel_estimate),
            _safety_information_check(segment),
            _availability_check(segment),
            _critical_record_freshness_check(segment, condition),
        )
    )
