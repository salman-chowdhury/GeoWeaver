"""Controlled vocabularies for the v0.1 domain model."""

from enum import StrEnum


class VerificationState(StrEnum):
    """Degree to which stable segment attributes have been checked."""

    UNREVIEWED = "unreviewed"
    REMOTE_REVIEWED = "remote_reviewed"
    FIELD_VERIFIED = "field_verified"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    REJECTED = "rejected"


class PublicAccessState(StrEnum):
    """Known public-access status for a shoreline segment."""

    VERIFIED_PUBLIC = "verified_public"
    RESTRICTED = "restricted"
    PROHIBITED = "prohibited"
    UNKNOWN = "unknown"


class ActivityPermissionStatus(StrEnum):
    """Whether the intended activity is explicitly permitted at a segment."""

    PERMITTED = "permitted"
    PROHIBITED = "prohibited"
    UNKNOWN = "unknown"


class TidalStatus(StrEnum):
    """Whether a segment is known to be tidal for the v0.1 activity profile."""

    TIDAL = "tidal"
    NON_TIDAL = "non_tidal"
    UNKNOWN = "unknown"


class ShorelineType(StrEnum):
    """Coarse, deliberately small shoreline classification."""

    ESTUARY_BANK = "estuary_bank"
    CREEK_EDGE = "creek_edge"
    MANGROVE_EDGE = "mangrove_edge"
    SANDY_BANK = "sandy_bank"
    BUILT_EDGE = "built_edge"
    ROCKY_BANK = "rocky_bank"


class Substrate(StrEnum):
    """Dominant shoreline substrate."""

    FIRM_EARTH = "firm_earth"
    SAND = "sand"
    MUD = "mud"
    ROCK = "rock"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class BankSlopeClass(StrEnum):
    """Coarse bank gradient used by the offline access scorer."""

    GENTLE = "gentle"
    MODERATE = "moderate"
    STEEP = "steep"
    UNKNOWN = "unknown"


class TideStage(StrEnum):
    """Simplified tide stage supplied by an offline condition snapshot."""

    LOW = "low"
    RISING = "rising"
    HIGH = "high"
    FALLING = "falling"
    UNKNOWN = "unknown"


class HabitatFeature(StrEnum):
    """Habitat tags consumed by the versioned CastNetGPT v0.1 rules."""

    CREEK_MOUTH = "creek_mouth"
    DRAIN_OUTFALL = "drain_outfall"
    SHALLOW_GUTTER = "shallow_gutter"
    MANGROVE_EDGE = "mangrove_edge"
    SAND_BAR = "sand_bar"
    BUILT_STRUCTURE = "built_structure"
    ESTUARINE_CONNECTION = "estuarine_connection"


class RestrictionStatus(StrEnum):
    """Whether a legal, health, or access restriction currently applies."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class ConfidenceBand(StrEnum):
    """Coarse evidence confidence, kept separate from recommendation score."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GeometryType(StrEnum):
    """Geometry types supported by the v0.1 catalogue."""

    POINT = "Point"
    LINE_STRING = "LineString"


class SkillLevel(StrEnum):
    """User experience level used to describe the demo preferences."""

    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"
