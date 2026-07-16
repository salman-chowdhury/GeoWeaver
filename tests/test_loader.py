"""Tests for catalogue file loading."""

from pathlib import Path

import pytest

from geoweaver.data.loader import load_catalogue
from geoweaver.data.validation import CatalogueValidationError
from geoweaver.domain.enums import GeometryType


def test_load_valid_catalogue(demo_catalogue_path: Path) -> None:
    segments = load_catalogue(demo_catalogue_path)

    assert len(segments) == 5
    assert segments[0].segment_id == "demo-alpha-gutter"
    assert segments[0].geometry.geometry_type is GeometryType.LINE_STRING
    assert segments[1].geometry.geometry_type is GeometryType.POINT


def test_malformed_geojson_reports_location(tmp_path: Path) -> None:
    catalogue = tmp_path / "broken.geojson"
    catalogue.write_text('{"type": "FeatureCollection",', encoding="utf-8")

    with pytest.raises(CatalogueValidationError, match=r"line 1, column"):
        load_catalogue(catalogue)


def test_missing_file_reports_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.geojson"

    with pytest.raises(CatalogueValidationError, match=r"could not read catalogue"):
        load_catalogue(missing)


def test_invalid_utf8_is_normalized_as_catalogue_validation_error(tmp_path: Path) -> None:
    catalogue = tmp_path / "invalid-utf8.geojson"
    catalogue.write_bytes(b'\xff\xfe{"type":"FeatureCollection"}')

    with pytest.raises(CatalogueValidationError, match=r"not valid UTF-8"):
        load_catalogue(catalogue)
