"""Tests for the strict v0.1 GeoJSON contract."""

from copy import deepcopy
from dataclasses import replace
from typing import cast

import pytest

from geoweaver.data.validation import CatalogueValidationError, validate_catalogue_document
from geoweaver.demo import demonstration_condition
from geoweaver.domain.models import ScoreBreakdown, ShorelineSegment


def _features(document: dict[str, object]) -> list[dict[str, object]]:
    return cast("list[dict[str, object]]", document["features"])


def _properties(document: dict[str, object], index: int = 0) -> dict[str, object]:
    return cast("dict[str, object]", _features(document)[index]["properties"])


def test_missing_required_field_is_rejected(demo_document: dict[str, object]) -> None:
    document = deepcopy(demo_document)
    del _properties(document)["legal_status_known"]

    with pytest.raises(CatalogueValidationError, match=r"legal_status_known"):
        validate_catalogue_document(document)


def test_duplicate_segment_ids_are_rejected(demo_document: dict[str, object]) -> None:
    document = deepcopy(demo_document)
    _properties(document, 1)["segment_id"] = _properties(document, 0)["segment_id"]

    with pytest.raises(CatalogueValidationError, match=r"duplicate segment_id"):
        validate_catalogue_document(document)


@pytest.mark.parametrize(
    ("geometry", "message"),
    [
        ({"type": "Polygon", "coordinates": []}, "unsupported value"),
        ({"type": "Point", "coordinates": [181, 0]}, "outside WGS 84"),
        ({"type": "LineString", "coordinates": [[0, 0]]}, "at least two positions"),
    ],
)
def test_invalid_geometries_are_rejected(
    demo_document: dict[str, object], geometry: dict[str, object], message: str
) -> None:
    document = deepcopy(demo_document)
    _features(document)[0]["geometry"] = geometry

    with pytest.raises(CatalogueValidationError, match=message):
        validate_catalogue_document(document)


def test_unsupported_controlled_value_is_rejected(demo_document: dict[str, object]) -> None:
    document = deepcopy(demo_document)
    _properties(document)["substrate"] = "wishful_thinking"

    with pytest.raises(CatalogueValidationError, match=r"substrate.*unsupported value"):
        validate_catalogue_document(document)


def test_unsupported_habitat_feature_is_rejected(demo_document: dict[str, object]) -> None:
    document = deepcopy(demo_document)
    _properties(document)["habitat_features"] = ["creek_mout"]

    with pytest.raises(
        CatalogueValidationError,
        match=r"habitat_features\[0\].*unsupported value.*creek_mout",
    ):
        validate_catalogue_document(document)


def test_health_advisory_status_must_match_its_evidence(
    demo_document: dict[str, object],
) -> None:
    document = deepcopy(demo_document)
    _properties(document)["health_advisory_status"] = "active"

    with pytest.raises(CatalogueValidationError, match=r"health_advisory_evidence.status"):
        validate_catalogue_document(document)


def test_missing_parking_evidence_is_not_defaulted(demo_document: dict[str, object]) -> None:
    document = deepcopy(demo_document)
    parking = _properties(document)["parking"]
    assert isinstance(parking, dict)
    del parking["available"]

    with pytest.raises(CatalogueValidationError, match=r"parking.*available"):
        validate_catalogue_document(document)


def test_rating_outside_contract_is_rejected(demo_document: dict[str, object]) -> None:
    document = deepcopy(demo_document)
    _properties(document)["mud_risk"] = 6

    with pytest.raises(CatalogueValidationError, match=r"mud_risk.*0 to 5"):
        validate_catalogue_document(document)


def test_timestamp_requires_timezone(demo_document: dict[str, object]) -> None:
    document = deepcopy(demo_document)
    _properties(document)["last_updated"] = "2026-01-15T10:00:00"

    with pytest.raises(CatalogueValidationError, match=r"timezone"):
        validate_catalogue_document(document)


@pytest.mark.parametrize("field_name", ["habitat_features", "source_refs"])
def test_duplicate_evidence_values_are_rejected(
    demo_document: dict[str, object], field_name: str
) -> None:
    document = deepcopy(demo_document)
    values = _properties(document)[field_name]
    assert isinstance(values, list)
    values.append(values[0])

    with pytest.raises(CatalogueValidationError, match=r"duplicate"):
        validate_catalogue_document(document)


def test_foreign_crs_declaration_is_rejected(demo_document: dict[str, object]) -> None:
    document = deepcopy(demo_document)
    document["crs"] = {"type": "name", "properties": {"name": "EPSG:3857"}}

    with pytest.raises(CatalogueValidationError, match=r"WGS 84"):
        validate_catalogue_document(document)


def test_domain_rating_rejects_fractional_value(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    with pytest.raises(ValueError, match=r"integer from 0 to 5"):
        replace(demo_segments[0].access, privacy_rating=2.5)


def test_score_breakdown_rejects_fractional_value() -> None:
    with pytest.raises(ValueError, match=r"integer from 0 to 100"):
        ScoreBreakdown(
            habitat_opportunity=50,
            environmental_condition_match=50,
            access_and_usability=50,
            privacy=50,
            family_suitability=50,
            safety_and_risk=50,
            travel_efficiency=50,
            data_quality=50,
            final_score=50.5,
        )


def test_domain_model_rejects_unsupported_enum_value(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    with pytest.raises(ValueError, match=r"bank_slope_class.*unsupported value.*cliff"):
        replace(demo_segments[0], bank_slope_class="cliff")


@pytest.mark.parametrize(
    "field_name",
    [
        "weather_source_refs",
        "footing_source_refs",
        "tide_source_refs",
        "daylight_source_refs",
    ],
)
def test_condition_evidence_rejects_blank_source_reference(field_name: str) -> None:
    with pytest.raises(ValueError, match=rf"{field_name}.*blank"):
        replace(demonstration_condition(), **{field_name: ("   ",)})
