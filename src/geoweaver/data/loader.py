"""File adapter for the v0.1 GeoJSON catalogue."""

import json
from pathlib import Path

from geoweaver.data.validation import CatalogueValidationError, validate_catalogue_document
from geoweaver.domain.models import ShorelineSegment


def load_catalogue(path: str | Path) -> tuple[ShorelineSegment, ...]:
    """Read and validate a GeoJSON catalogue with actionable error messages."""
    catalogue_path = Path(path)
    try:
        with catalogue_path.open(encoding="utf-8") as catalogue_file:
            document = json.load(catalogue_file)
    except OSError as error:
        raise CatalogueValidationError(
            f"could not read catalogue {catalogue_path}: {error.strerror or error}"
        ) from error
    except UnicodeError as error:
        raise CatalogueValidationError(
            f"catalogue {catalogue_path} is not valid UTF-8: {error}"
        ) from error
    except json.JSONDecodeError as error:
        raise CatalogueValidationError(
            f"catalogue {catalogue_path} is not valid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    return validate_catalogue_document(document)
