"""Strict validation for the file-first v0.1 GeoJSON contract."""

import math
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import cast

from geoweaver.domain.enums import (
    ActivityPermissionStatus,
    BankSlopeClass,
    EvidenceState,
    GeometryType,
    HabitatFeature,
    PublicAccessState,
    RestrictionStatus,
    ShorelineType,
    Substrate,
    TidalStatus,
    TideStage,
    VerificationState,
)
from geoweaver.domain.models import (
    AccessProfile,
    EnvironmentalProfile,
    Geometry,
    Position,
    Restriction,
    ShorelineSegment,
    SourceProvenance,
)


class CatalogueValidationError(ValueError):
    """Raised when a catalogue cannot safely produce domain objects."""


REQUIRED_PROPERTIES = frozenset(
    {
        "segment_id",
        "name",
        "region",
        "waterway",
        "shoreline_type",
        "substrate",
        "bank_slope_class",
        "public_access_status",
        "verification_status",
        "activity_permission_status",
        "activity_permission_evidence",
        "tidal_status",
        "health_advisory_status",
        "health_advisory_evidence",
        "casting_space_rating",
        "parking",
        "toilets",
        "family_suitability",
        "privacy_rating",
        "mud_risk",
        "snag_risk",
        "boat_traffic_rating",
        "wind_shelter_rating",
        "habitat_features",
        "preferred_tide_stages",
        "legal_status_known",
        "legal_status_evidence",
        "safety_information_complete",
        "restrictions",
        "restriction_review_evidence",
        "source_refs",
        "last_updated",
    }
)


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise CatalogueValidationError(f"{context} must be an object")
    return cast("Mapping[str, object]", value)


def _list(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise CatalogueValidationError(f"{context} must be an array")
    return cast("list[object]", value)


def _text(value: object, context: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        qualifier = "a string" if allow_empty else "a non-empty string"
        raise CatalogueValidationError(f"{context} must be {qualifier}")
    return value


def _integer(value: object, context: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CatalogueValidationError(f"{context} must be an integer")
    if minimum is not None and value < minimum:
        raise CatalogueValidationError(f"{context} must be at least {minimum}")
    return value


def _optional_integer(value: object, context: str, *, minimum: int = 0) -> int | None:
    if value is None:
        return None
    return _integer(value, context, minimum=minimum)


def _boolean(value: object, context: str) -> bool:
    if not isinstance(value, bool):
        raise CatalogueValidationError(f"{context} must be true or false")
    return value


def _optional_boolean(value: object, context: str) -> bool | None:
    if value is None:
        return None
    return _boolean(value, context)


def _enum_value[EnumType: StrEnum](
    enum_type: type[EnumType], value: object, context: str
) -> EnumType:
    raw_value = _text(value, context)
    try:
        return enum_type(raw_value)
    except ValueError as error:
        allowed = ", ".join(item.value for item in enum_type)
        raise CatalogueValidationError(
            f"{context} has unsupported value {raw_value!r}; expected one of: {allowed}"
        ) from error


def _string_tuple(value: object, context: str, *, require_items: bool) -> tuple[str, ...]:
    items = _list(value, context)
    if require_items and not items:
        raise CatalogueValidationError(f"{context} must contain at least one item")
    return tuple(_text(item, f"{context}[{index}]") for index, item in enumerate(items))


def _timestamp(value: object, context: str) -> datetime:
    raw_value = _text(value, context)
    try:
        timestamp = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CatalogueValidationError(f"{context} must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise CatalogueValidationError(f"{context} must include a timezone")
    return timestamp


def _optional_timestamp(value: object, context: str) -> datetime | None:
    if value is None:
        return None
    return _timestamp(value, context)


def _position(value: object, context: str) -> Position:
    coordinates = _list(value, context)
    if len(coordinates) != 2:
        raise CatalogueValidationError(f"{context} must contain longitude and latitude")
    longitude, latitude = coordinates
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in coordinates):
        raise CatalogueValidationError(f"{context} coordinates must be numbers")
    longitude_float = float(cast("float", longitude))
    latitude_float = float(cast("float", latitude))
    if not math.isfinite(longitude_float) or not math.isfinite(latitude_float):
        raise CatalogueValidationError(f"{context} coordinates must be finite")
    if not -180 <= longitude_float <= 180 or not -90 <= latitude_float <= 90:
        raise CatalogueValidationError(f"{context} is outside WGS 84 coordinate bounds")
    return longitude_float, latitude_float


def _geometry(value: object, context: str) -> Geometry:
    geometry = _mapping(value, context)
    geometry_type = _enum_value(GeometryType, geometry.get("type"), f"{context}.type")
    raw_coordinates = geometry.get("coordinates")
    if geometry_type is GeometryType.POINT:
        return Geometry(
            geometry_type=geometry_type, coordinates=_position(raw_coordinates, context)
        )

    positions = _list(raw_coordinates, f"{context}.coordinates")
    if len(positions) < 2:
        raise CatalogueValidationError(f"{context}.coordinates must contain at least two positions")
    return Geometry(
        geometry_type=geometry_type,
        coordinates=tuple(
            _position(position, f"{context}.coordinates[{index}]")
            for index, position in enumerate(positions)
        ),
    )


def _restriction(value: object, context: str) -> Restriction:
    restriction = _mapping(value, context)
    required = frozenset(
        {
            "restriction_id",
            "restriction_type",
            "status",
            "authority",
            "source_ref",
            "reason",
            "effective_from",
            "effective_to",
            "retrieved_at",
            "evidence_state",
        }
    )
    missing = sorted(required.difference(restriction))
    if missing:
        raise CatalogueValidationError(
            f"{context} is missing required fields: {', '.join(missing)}"
        )
    unknown = sorted(set(restriction).difference(required))
    if unknown:
        raise CatalogueValidationError(f"{context} has unknown fields: {', '.join(unknown)}")
    return Restriction(
        restriction_id=_text(restriction.get("restriction_id"), f"{context}.restriction_id"),
        restriction_type=_text(restriction.get("restriction_type"), f"{context}.restriction_type"),
        status=_enum_value(RestrictionStatus, restriction.get("status"), f"{context}.status"),
        authority=_text(restriction.get("authority"), f"{context}.authority"),
        source_ref=_text(restriction.get("source_ref"), f"{context}.source_ref"),
        reason=_text(restriction.get("reason"), f"{context}.reason"),
        effective_from=_optional_timestamp(
            restriction.get("effective_from"), f"{context}.effective_from"
        ),
        effective_to=_optional_timestamp(
            restriction.get("effective_to"), f"{context}.effective_to"
        ),
        retrieved_at=_timestamp(restriction.get("retrieved_at"), f"{context}.retrieved_at"),
        evidence_state=_enum_value(
            EvidenceState,
            restriction.get("evidence_state"),
            f"{context}.evidence_state",
        ),
    )


def _source_provenance(value: object, context: str) -> SourceProvenance:
    provenance = _mapping(value, context)
    required = frozenset({"authority", "source_ref", "retrieved_at", "evidence_state"})
    missing = sorted(required.difference(provenance))
    if missing:
        raise CatalogueValidationError(
            f"{context} is missing required fields: {', '.join(missing)}"
        )
    unknown = sorted(set(provenance).difference(required))
    if unknown:
        raise CatalogueValidationError(f"{context} has unknown fields: {', '.join(unknown)}")
    return SourceProvenance(
        authority=_text(provenance["authority"], f"{context}.authority"),
        source_ref=_text(provenance["source_ref"], f"{context}.source_ref"),
        retrieved_at=_timestamp(provenance["retrieved_at"], f"{context}.retrieved_at"),
        evidence_state=_enum_value(
            EvidenceState,
            provenance["evidence_state"],
            f"{context}.evidence_state",
        ),
    )


def _restrictions(value: object, context: str) -> tuple[Restriction, ...]:
    raw_restrictions = _list(value, context)
    restrictions: list[Restriction] = []
    seen_ids: set[str] = set()
    for index, raw_restriction in enumerate(raw_restrictions):
        item_context = f"{context}[{index}]"
        restriction = _restriction(raw_restriction, item_context)
        if restriction.restriction_id in seen_ids:
            raise CatalogueValidationError(
                f"{item_context}.restriction_id duplicates {restriction.restriction_id!r}"
            )
        seen_ids.add(restriction.restriction_id)
        restrictions.append(restriction)
    return tuple(restrictions)


def _segment(feature: object, index: int) -> ShorelineSegment:
    context = f"features[{index}]"
    feature_object = _mapping(feature, context)
    if feature_object.get("type") != "Feature":
        raise CatalogueValidationError(f"{context}.type must be 'Feature'")
    properties = _mapping(feature_object.get("properties"), f"{context}.properties")
    missing = sorted(REQUIRED_PROPERTIES.difference(properties))
    if missing:
        raise CatalogueValidationError(
            f"{context}.properties is missing required fields: {', '.join(missing)}"
        )

    parking = _mapping(properties["parking"], f"{context}.properties.parking")
    for parking_field in ("available", "spaces_estimate", "notes"):
        if parking_field not in parking:
            raise CatalogueValidationError(
                f"{context}.properties.parking is missing required field: {parking_field}"
            )

    preferred_tide_values = _list(
        properties["preferred_tide_stages"], f"{context}.properties.preferred_tide_stages"
    )
    preferred_tides = tuple(
        _enum_value(TideStage, value, f"{context}.properties.preferred_tide_stages[{item_index}]")
        for item_index, value in enumerate(preferred_tide_values)
    )

    try:
        return ShorelineSegment(
            segment_id=_text(properties["segment_id"], f"{context}.properties.segment_id"),
            name=_text(properties["name"], f"{context}.properties.name"),
            region=_text(properties["region"], f"{context}.properties.region"),
            waterway=_text(properties["waterway"], f"{context}.properties.waterway"),
            geometry=_geometry(feature_object.get("geometry"), f"{context}.geometry"),
            shoreline_type=_enum_value(
                ShorelineType, properties["shoreline_type"], f"{context}.properties.shoreline_type"
            ),
            substrate=_enum_value(
                Substrate, properties["substrate"], f"{context}.properties.substrate"
            ),
            bank_slope_class=_enum_value(
                BankSlopeClass,
                properties["bank_slope_class"],
                f"{context}.properties.bank_slope_class",
            ),
            access=AccessProfile(
                public_access_status=_enum_value(
                    PublicAccessState,
                    properties["public_access_status"],
                    f"{context}.properties.public_access_status",
                ),
                casting_space_rating=_integer(
                    properties["casting_space_rating"],
                    f"{context}.properties.casting_space_rating",
                ),
                parking_available=_optional_boolean(
                    parking["available"], f"{context}.properties.parking.available"
                ),
                parking_spaces_estimate=_optional_integer(
                    parking["spaces_estimate"], f"{context}.properties.parking.spaces_estimate"
                ),
                parking_notes=_text(
                    parking["notes"], f"{context}.properties.parking.notes", allow_empty=True
                ),
                toilets=_optional_boolean(properties["toilets"], f"{context}.properties.toilets"),
                family_suitability=_integer(
                    properties["family_suitability"],
                    f"{context}.properties.family_suitability",
                ),
                privacy_rating=_integer(
                    properties["privacy_rating"], f"{context}.properties.privacy_rating"
                ),
            ),
            environmental=EnvironmentalProfile(
                mud_risk=_integer(properties["mud_risk"], f"{context}.properties.mud_risk"),
                snag_risk=_integer(properties["snag_risk"], f"{context}.properties.snag_risk"),
                boat_traffic_rating=_integer(
                    properties["boat_traffic_rating"],
                    f"{context}.properties.boat_traffic_rating",
                ),
                wind_shelter_rating=_integer(
                    properties["wind_shelter_rating"],
                    f"{context}.properties.wind_shelter_rating",
                ),
                habitat_features=tuple(
                    _enum_value(
                        HabitatFeature,
                        value,
                        f"{context}.properties.habitat_features[{item_index}]",
                    )
                    for item_index, value in enumerate(
                        _list(
                            properties["habitat_features"],
                            f"{context}.properties.habitat_features",
                        )
                    )
                ),
                preferred_tide_stages=preferred_tides,
            ),
            verification_status=_enum_value(
                VerificationState,
                properties["verification_status"],
                f"{context}.properties.verification_status",
            ),
            activity_permission_status=_enum_value(
                ActivityPermissionStatus,
                properties["activity_permission_status"],
                f"{context}.properties.activity_permission_status",
            ),
            activity_permission_evidence=_source_provenance(
                properties["activity_permission_evidence"],
                f"{context}.properties.activity_permission_evidence",
            ),
            tidal_status=_enum_value(
                TidalStatus,
                properties["tidal_status"],
                f"{context}.properties.tidal_status",
            ),
            health_advisory_status=_enum_value(
                RestrictionStatus,
                properties["health_advisory_status"],
                f"{context}.properties.health_advisory_status",
            ),
            health_advisory_evidence=_restriction(
                properties["health_advisory_evidence"],
                f"{context}.properties.health_advisory_evidence",
            ),
            legal_status_known=_boolean(
                properties["legal_status_known"], f"{context}.properties.legal_status_known"
            ),
            legal_status_evidence=_source_provenance(
                properties["legal_status_evidence"],
                f"{context}.properties.legal_status_evidence",
            ),
            safety_information_complete=_boolean(
                properties["safety_information_complete"],
                f"{context}.properties.safety_information_complete",
            ),
            restrictions=_restrictions(
                properties["restrictions"], f"{context}.properties.restrictions"
            ),
            restriction_review_evidence=_source_provenance(
                properties["restriction_review_evidence"],
                f"{context}.properties.restriction_review_evidence",
            ),
            source_refs=_string_tuple(
                properties["source_refs"],
                f"{context}.properties.source_refs",
                require_items=True,
            ),
            last_updated=_timestamp(
                properties["last_updated"], f"{context}.properties.last_updated"
            ),
        )
    except ValueError as error:
        raise CatalogueValidationError(f"{context}: {error}") from error


def validate_catalogue_document(document: object) -> tuple[ShorelineSegment, ...]:
    """Validate a decoded GeoJSON FeatureCollection into domain objects."""
    root = _mapping(document, "catalogue")
    if root.get("type") != "FeatureCollection":
        raise CatalogueValidationError("catalogue.type must be 'FeatureCollection'")
    if "crs" in root:
        raise CatalogueValidationError(
            "catalogue.crs is not supported; v0.1 GeoJSON coordinates must already be WGS 84"
        )
    features = _list(root.get("features"), "catalogue.features")
    if not features:
        raise CatalogueValidationError("catalogue.features must contain at least one feature")

    segments: list[ShorelineSegment] = []
    seen_ids: set[str] = set()
    for index, feature in enumerate(features):
        segment = _segment(feature, index)
        if segment.segment_id in seen_ids:
            raise CatalogueValidationError(f"duplicate segment_id: {segment.segment_id!r}")
        seen_ids.add(segment.segment_id)
        segments.append(segment)
    return tuple(segments)
