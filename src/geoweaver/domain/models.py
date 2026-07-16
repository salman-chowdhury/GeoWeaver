"""Immutable, validated domain models for the GeoWeaver v0.1 slice."""

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from geoweaver.domain.enums import (
    ActivityPermissionStatus,
    BankSlopeClass,
    ConfidenceBand,
    GeometryType,
    HabitatFeature,
    PublicAccessState,
    RestrictionStatus,
    ShorelineType,
    SkillLevel,
    Substrate,
    TidalStatus,
    TideStage,
    VerificationState,
)

type Position = tuple[float, float]
type GeometryCoordinates = Position | tuple[Position, ...]


def _require_text(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_rating(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
        raise ValueError(f"{field_name} must be an integer from 0 to 5")


def _require_score(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise ValueError(f"{field_name} must be an integer from 0 to 100")


def _require_bool(value: bool, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be true or false")


def _require_optional_bool(value: bool | None, field_name: str) -> None:
    if value is not None:
        _require_bool(value, field_name)


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")


def _coerce_enum[EnumType: StrEnum](
    value: object, enum_type: type[EnumType], field_name: str
) -> EnumType:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as error:
        allowed = ", ".join(item.value for item in enum_type)
        raise ValueError(
            f"{field_name} has unsupported value {value!r}; expected one of: {allowed}"
        ) from error


def _require_source_refs(
    source_refs: tuple[str, ...], field_name: str, *, require_items: bool
) -> None:
    if require_items and not source_refs:
        raise ValueError(f"{field_name} must contain at least one reference")
    if any(not isinstance(source, str) or not source.strip() for source in source_refs):
        raise ValueError(f"{field_name} must not contain blank values")
    if len(set(source_refs)) != len(source_refs):
        raise ValueError(f"{field_name} must not contain duplicate values")


@dataclass(frozen=True, slots=True)
class Geometry:
    """A validated WGS 84 Point or LineString."""

    geometry_type: GeometryType
    coordinates: GeometryCoordinates

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "geometry_type",
            _coerce_enum(self.geometry_type, GeometryType, "geometry_type"),
        )


@dataclass(frozen=True, slots=True)
class AccessProfile:
    """Stable access and usability attributes for a segment."""

    public_access_status: PublicAccessState
    casting_space_rating: int
    parking_available: bool | None
    parking_spaces_estimate: int | None
    parking_notes: str
    toilets: bool | None
    family_suitability: int
    privacy_rating: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_access_status",
            _coerce_enum(self.public_access_status, PublicAccessState, "public_access_status"),
        )
        _require_rating(self.casting_space_rating, "casting_space_rating")
        _require_rating(self.family_suitability, "family_suitability")
        _require_rating(self.privacy_rating, "privacy_rating")
        _require_optional_bool(self.parking_available, "parking_available")
        _require_optional_bool(self.toilets, "toilets")
        if self.parking_spaces_estimate is not None:
            if isinstance(self.parking_spaces_estimate, bool) or not isinstance(
                self.parking_spaces_estimate, int
            ):
                raise ValueError("parking_spaces_estimate must be an integer")
            if self.parking_spaces_estimate < 0:
                raise ValueError("parking_spaces_estimate must be zero or greater")


@dataclass(frozen=True, slots=True)
class EnvironmentalProfile:
    """Stable environmental characteristics used by the baseline rules."""

    mud_risk: int
    snag_risk: int
    boat_traffic_rating: int
    wind_shelter_rating: int
    habitat_features: tuple[HabitatFeature, ...]
    preferred_tide_stages: tuple[TideStage, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "habitat_features",
            tuple(
                _coerce_enum(value, HabitatFeature, "habitat_features")
                for value in self.habitat_features
            ),
        )
        object.__setattr__(
            self,
            "preferred_tide_stages",
            tuple(
                _coerce_enum(value, TideStage, "preferred_tide_stages")
                for value in self.preferred_tide_stages
            ),
        )
        _require_rating(self.mud_risk, "mud_risk")
        _require_rating(self.snag_risk, "snag_risk")
        _require_rating(self.boat_traffic_rating, "boat_traffic_rating")
        _require_rating(self.wind_shelter_rating, "wind_shelter_rating")
        if len(set(self.habitat_features)) != len(self.habitat_features):
            raise ValueError("habitat_features must not contain duplicate values")
        if len(set(self.preferred_tide_stages)) != len(self.preferred_tide_stages):
            raise ValueError("preferred_tide_stages must not contain duplicate values")


@dataclass(frozen=True, slots=True)
class Restriction:
    """A legal, health, or access restriction associated with a segment."""

    restriction_id: str
    restriction_type: str
    status: RestrictionStatus
    authority: str
    source_ref: str
    reason: str
    effective_from: datetime | None
    effective_to: datetime | None
    retrieved_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            _coerce_enum(self.status, RestrictionStatus, "restriction status"),
        )
        for field_name in (
            "restriction_id",
            "restriction_type",
            "authority",
            "source_ref",
            "reason",
        ):
            _require_text(getattr(self, field_name), field_name)
        if self.effective_from is not None:
            _require_aware_datetime(self.effective_from, "effective_from")
        if self.effective_to is not None:
            _require_aware_datetime(self.effective_to, "effective_to")
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_from > self.effective_to
        ):
            raise ValueError("effective_from must not be later than effective_to")
        _require_aware_datetime(self.retrieved_at, "retrieved_at")

    def is_effective_at(self, when: datetime) -> bool:
        """Return whether the restriction's declared effective window includes ``when``."""
        _require_aware_datetime(when, "restriction comparison time")
        return not (
            (self.effective_from is not None and when < self.effective_from)
            or (self.effective_to is not None and when > self.effective_to)
        )


@dataclass(frozen=True, slots=True)
class ShorelineSegment:
    """Canonical stable record loaded from the v0.1 GeoJSON catalogue."""

    segment_id: str
    name: str
    region: str
    waterway: str
    geometry: Geometry
    shoreline_type: ShorelineType
    substrate: Substrate
    bank_slope_class: BankSlopeClass
    access: AccessProfile
    environmental: EnvironmentalProfile
    verification_status: VerificationState
    activity_permission_status: ActivityPermissionStatus
    tidal_status: TidalStatus
    health_advisory_status: RestrictionStatus
    health_advisory_evidence: Restriction
    legal_status_known: bool
    safety_information_complete: bool
    restrictions: tuple[Restriction, ...]
    source_refs: tuple[str, ...]
    last_updated: datetime

    def __post_init__(self) -> None:
        enum_fields = (
            ("shoreline_type", ShorelineType),
            ("substrate", Substrate),
            ("bank_slope_class", BankSlopeClass),
            ("verification_status", VerificationState),
            ("activity_permission_status", ActivityPermissionStatus),
            ("tidal_status", TidalStatus),
            ("health_advisory_status", RestrictionStatus),
        )
        for field_name, enum_type in enum_fields:
            object.__setattr__(
                self,
                field_name,
                _coerce_enum(getattr(self, field_name), enum_type, field_name),
            )
        for field_name in ("segment_id", "name", "region", "waterway"):
            _require_text(getattr(self, field_name), field_name)
        _require_source_refs(self.source_refs, "source_refs", require_items=True)
        if self.health_advisory_evidence.status is not self.health_advisory_status:
            raise ValueError("health_advisory_evidence.status must match health_advisory_status")
        _require_bool(self.legal_status_known, "legal_status_known")
        _require_bool(self.safety_information_complete, "safety_information_complete")
        _require_aware_datetime(self.last_updated, "last_updated")


@dataclass(frozen=True, slots=True)
class ConditionSnapshot:
    """Explicit time-dependent inputs used for one recommendation run."""

    snapshot_id: str
    applicable_segment_ids: tuple[str, ...]
    valid_at: datetime
    tide_stage: TideStage
    severe_weather_warning: bool | None
    lightning_or_severe_thunderstorm_risk: bool | None
    footing_safe: bool | None
    usable_daylight_minutes: int | None
    wind_speed_kph: float | None
    gust_speed_kph: float | None
    data_freshness_minutes: int | None
    inferred: bool
    weather_status_verified: bool
    footing_status_verified: bool
    tide_status_verified: bool
    daylight_status_verified: bool
    weather_source_refs: tuple[str, ...]
    footing_source_refs: tuple[str, ...]
    tide_source_refs: tuple[str, ...]
    daylight_source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.snapshot_id, "snapshot_id")
        _require_source_refs(
            self.applicable_segment_ids,
            "applicable_segment_ids",
            require_items=True,
        )
        _require_aware_datetime(self.valid_at, "valid_at")
        object.__setattr__(
            self,
            "tide_stage",
            _coerce_enum(self.tide_stage, TideStage, "tide_stage"),
        )
        _require_optional_bool(self.severe_weather_warning, "severe_weather_warning")
        _require_optional_bool(
            self.lightning_or_severe_thunderstorm_risk,
            "lightning_or_severe_thunderstorm_risk",
        )
        _require_optional_bool(self.footing_safe, "footing_safe")
        _require_bool(self.inferred, "inferred")
        _require_bool(self.weather_status_verified, "weather_status_verified")
        _require_bool(self.footing_status_verified, "footing_status_verified")
        _require_bool(self.tide_status_verified, "tide_status_verified")
        _require_bool(self.daylight_status_verified, "daylight_status_verified")
        for field_name in (
            "weather_source_refs",
            "footing_source_refs",
            "tide_source_refs",
            "daylight_source_refs",
        ):
            _require_source_refs(getattr(self, field_name), field_name, require_items=False)
        if self.usable_daylight_minutes is not None:
            if isinstance(self.usable_daylight_minutes, bool) or not isinstance(
                self.usable_daylight_minutes, int
            ):
                raise ValueError("usable_daylight_minutes must be an integer")
            if self.usable_daylight_minutes < 0:
                raise ValueError("usable_daylight_minutes must be zero or greater")
        if self.wind_speed_kph is not None:
            if isinstance(self.wind_speed_kph, bool) or not isinstance(
                self.wind_speed_kph, (int, float)
            ):
                raise ValueError("wind_speed_kph must be a number")
            if not math.isfinite(self.wind_speed_kph) or self.wind_speed_kph < 0:
                raise ValueError("wind_speed_kph must be finite and zero or greater")
        if self.gust_speed_kph is not None:
            if isinstance(self.gust_speed_kph, bool) or not isinstance(
                self.gust_speed_kph, (int, float)
            ):
                raise ValueError("gust_speed_kph must be a number")
            if not math.isfinite(self.gust_speed_kph) or self.gust_speed_kph < 0:
                raise ValueError("gust_speed_kph must be finite and zero or greater")
        if self.data_freshness_minutes is not None:
            if isinstance(self.data_freshness_minutes, bool) or not isinstance(
                self.data_freshness_minutes, int
            ):
                raise ValueError("data_freshness_minutes must be an integer")
            if self.data_freshness_minutes < 0:
                raise ValueError("data_freshness_minutes must be zero or greater")

    @property
    def source_refs(self) -> tuple[str, ...]:
        """Return all condition evidence references in deterministic field order."""
        combined = (
            *self.weather_source_refs,
            *self.footing_source_refs,
            *self.tide_source_refs,
            *self.daylight_source_refs,
        )
        return tuple(dict.fromkeys(combined))


@dataclass(frozen=True, slots=True)
class UserPreferences:
    """Practical user constraints supplied to the recommendation service."""

    skill_level: SkillLevel
    require_family_suitable: bool
    minimum_family_suitability: int
    minimum_casting_space_rating: int
    minimum_usable_daylight_minutes: int
    desired_privacy_rating: int
    maximum_travel_minutes: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "skill_level",
            _coerce_enum(self.skill_level, SkillLevel, "skill_level"),
        )
        _require_rating(self.minimum_family_suitability, "minimum_family_suitability")
        _require_rating(self.minimum_casting_space_rating, "minimum_casting_space_rating")
        _require_rating(self.desired_privacy_rating, "desired_privacy_rating")
        _require_bool(self.require_family_suitable, "require_family_suitable")
        if isinstance(self.minimum_usable_daylight_minutes, bool) or not isinstance(
            self.minimum_usable_daylight_minutes, int
        ):
            raise ValueError("minimum_usable_daylight_minutes must be an integer")
        if self.minimum_usable_daylight_minutes < 0:
            raise ValueError("minimum_usable_daylight_minutes must be zero or greater")
        if isinstance(self.maximum_travel_minutes, bool) or not isinstance(
            self.maximum_travel_minutes, int
        ):
            raise ValueError("maximum_travel_minutes must be an integer")
        if self.maximum_travel_minutes < 0:
            raise ValueError("maximum_travel_minutes must be zero or greater")


@dataclass(frozen=True, slots=True)
class TravelEstimate:
    """Sourced, deterministic travel input for one segment and origin."""

    segment_id: str
    origin_label: str
    minutes: int
    source_ref: str
    inferred: bool

    def __post_init__(self) -> None:
        for field_name in ("segment_id", "origin_label", "source_ref"):
            _require_text(getattr(self, field_name), field_name)
        if isinstance(self.minutes, bool) or not isinstance(self.minutes, int):
            raise ValueError("travel minutes must be an integer")
        if self.minutes < 0:
            raise ValueError("travel minutes must be zero or greater")
        _require_bool(self.inferred, "inferred")


@dataclass(frozen=True, slots=True)
class GateCheck:
    """Result of one named hard-gate check."""

    gate: str
    passed: bool
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.gate, "gate")
        _require_bool(self.passed, "passed")
        _require_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class ConstraintResult:
    """Complete hard-gate outcome for a segment."""

    checks: tuple[GateCheck, ...]

    @property
    def eligible(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failures(self) -> tuple[GateCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    """Auditable scoring components; all values are bounded independently."""

    habitat_opportunity: int
    environmental_condition_match: int
    access_and_usability: int
    privacy: int
    family_suitability: int
    safety_and_risk: int
    travel_efficiency: int
    data_quality: int
    final_score: int

    def __post_init__(self) -> None:
        for field_name in self.component_scores():
            _require_score(getattr(self, field_name), field_name)
        _require_score(self.final_score, "final_score")

    def component_scores(self) -> dict[str, int]:
        """Return component values without conflating them with final score."""
        return {
            "habitat_opportunity": self.habitat_opportunity,
            "environmental_condition_match": self.environmental_condition_match,
            "access_and_usability": self.access_and_usability,
            "privacy": self.privacy,
            "family_suitability": self.family_suitability,
            "safety_and_risk": self.safety_and_risk,
            "travel_efficiency": self.travel_efficiency,
            "data_quality": self.data_quality,
        }

    def suitability_component_scores(self) -> dict[str, int]:
        """Return only components that contribute to recommendation suitability."""
        return {
            name: value for name, value in self.component_scores().items() if name != "data_quality"
        }


@dataclass(frozen=True, slots=True)
class RankedRecommendation:
    """A fully explained recommendation for one segment."""

    rank: int
    segment_id: str
    name: str
    region: str
    waterway: str
    eligibility: bool
    score: ScoreBreakdown
    confidence_score: int
    confidence_band: ConfidenceBand
    strongest_positive_factors: tuple[str, ...]
    highest_scoring_components: tuple[str, ...]
    strongest_limitations: tuple[str, ...]
    constraints: ConstraintResult
    missing_or_stale_information: tuple[str, ...]
    applicable_restrictions: tuple[Restriction, ...]
    health_advisory_evidence: Restriction
    verification_status: VerificationState
    source_refs: tuple[str, ...]
    data_last_updated: datetime
    travel_time_minutes: int | None
    travel_origin: str | None
    model_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "confidence_band",
            _coerce_enum(self.confidence_band, ConfidenceBand, "confidence_band"),
        )
        object.__setattr__(
            self,
            "verification_status",
            _coerce_enum(self.verification_status, VerificationState, "verification_status"),
        )
        if self.rank < 1:
            raise ValueError("rank must be one or greater")
        _require_bool(self.eligibility, "eligibility")
        _require_score(self.confidence_score, "confidence_score")
        for field_name in ("segment_id", "name", "region", "waterway", "model_version"):
            _require_text(getattr(self, field_name), field_name)
        if not self.source_refs or any(not source.strip() for source in self.source_refs):
            raise ValueError("source_refs must contain non-empty references")
        _require_aware_datetime(self.data_last_updated, "data_last_updated")
        if self.travel_time_minutes is not None:
            if isinstance(self.travel_time_minutes, bool) or not isinstance(
                self.travel_time_minutes, int
            ):
                raise ValueError("travel_time_minutes must be an integer")
            if self.travel_time_minutes < 0:
                raise ValueError("travel_time_minutes must be zero or greater")
        if self.travel_origin is not None:
            _require_text(self.travel_origin, "travel_origin")


@dataclass(frozen=True, slots=True)
class RecommendationRun:
    """Reproducible result set for one catalogue, preference, and condition input."""

    run_id: str
    application: str
    generated_at: datetime
    model_version: str
    condition: ConditionSnapshot
    preferences: UserPreferences
    travel_estimates: tuple[TravelEstimate, ...]
    recommendations: tuple[RankedRecommendation, ...]
    demonstration_notice: str

    def __post_init__(self) -> None:
        for field_name in ("run_id", "application", "model_version", "demonstration_notice"):
            _require_text(getattr(self, field_name), field_name)
        _require_aware_datetime(self.generated_at, "generated_at")
