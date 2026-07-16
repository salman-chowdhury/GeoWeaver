"""Fixed synthetic inputs for the offline CastNetGPT demonstration."""

from datetime import UTC, datetime

from geoweaver.domain.enums import SkillLevel, TideStage
from geoweaver.domain.models import ConditionSnapshot, TravelEstimate, UserPreferences


def demonstration_condition() -> ConditionSnapshot:
    """Return deterministic, explicitly inferred conditions for the v0.1 demo."""
    return ConditionSnapshot(
        snapshot_id="demo-conditions-v0.1",
        applicable_segment_ids=(
            "demo-alpha-gutter",
            "demo-beta-sandbar",
            "demo-closed-reach",
            "demo-unknown-access",
            "demo-narrow-mud-edge",
        ),
        valid_at=datetime(2026, 1, 15, 6, 0, tzinfo=UTC),
        tide_stage=TideStage.RISING,
        severe_weather_warning=False,
        lightning_or_severe_thunderstorm_risk=False,
        footing_safe=True,
        usable_daylight_minutes=120,
        wind_speed_kph=14.0,
        gust_speed_kph=22.0,
        data_freshness_minutes=60,
        inferred=True,
        weather_status_verified=True,
        footing_status_verified=True,
        tide_status_verified=True,
        daylight_status_verified=True,
        weather_source_refs=("demo://synthetic/weather/v0.1",),
        footing_source_refs=("demo://synthetic/footing/v0.1",),
        tide_source_refs=("demo://synthetic/tide/v0.1",),
        daylight_source_refs=("demo://synthetic/daylight/v0.1",),
    )


def demonstration_preferences() -> UserPreferences:
    """Return deterministic practical constraints for the v0.1 demo."""
    return UserPreferences(
        skill_level=SkillLevel.NOVICE,
        require_family_suitable=True,
        minimum_family_suitability=3,
        minimum_casting_space_rating=3,
        minimum_usable_daylight_minutes=60,
        desired_privacy_rating=3,
        maximum_travel_minutes=45,
    )


def demonstration_travel_estimates() -> tuple[TravelEstimate, ...]:
    """Return fixed manual travel estimates from a fictional demonstration origin."""
    origin = "Fictional Demo Origin"
    source = "demo://synthetic/travel-times/v0.1"
    return tuple(
        TravelEstimate(
            segment_id=segment_id,
            origin_label=origin,
            minutes=minutes,
            source_ref=source,
            inferred=True,
        )
        for segment_id, minutes in (
            ("demo-alpha-gutter", 20),
            ("demo-beta-sandbar", 35),
            ("demo-closed-reach", 15),
            ("demo-unknown-access", 25),
            ("demo-narrow-mud-edge", 50),
        )
    )
