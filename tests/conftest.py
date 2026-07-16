"""Shared fixtures for the offline v0.1 test suite."""

import json
from pathlib import Path

import pytest

from geoweaver.data.loader import load_catalogue
from geoweaver.domain.models import ShorelineSegment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_CATALOGUE = PROJECT_ROOT / "data" / "catalogue" / "demo_segments.geojson"


@pytest.fixture
def demo_catalogue_path() -> Path:
    return DEMO_CATALOGUE


@pytest.fixture
def demo_document() -> dict[str, object]:
    return json.loads(DEMO_CATALOGUE.read_text(encoding="utf-8"))


@pytest.fixture
def demo_segments() -> tuple[ShorelineSegment, ...]:
    return load_catalogue(DEMO_CATALOGUE)


def write_catalogue(tmp_path: Path, document: object) -> Path:
    path = tmp_path / "catalogue.geojson"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path
