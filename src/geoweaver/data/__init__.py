"""Offline data loading and validation for catalogues and run inputs."""

from geoweaver.data.loader import load_catalogue
from geoweaver.data.run_input import (
    RunInputValidationError,
    load_run_input,
    validate_run_input_document,
)
from geoweaver.data.sources import (
    SourceRegistryValidationError,
    collect_catalogue_source_refs,
    collect_run_input_source_refs,
    find_missing_source_refs,
    index_sources_by_id,
    load_source_registry,
    validate_source_registry_document,
)
from geoweaver.data.validation import CatalogueValidationError, validate_catalogue_document

__all__ = [
    "CatalogueValidationError",
    "RunInputValidationError",
    "SourceRegistryValidationError",
    "collect_catalogue_source_refs",
    "collect_run_input_source_refs",
    "find_missing_source_refs",
    "index_sources_by_id",
    "load_catalogue",
    "load_run_input",
    "load_source_registry",
    "validate_catalogue_document",
    "validate_run_input_document",
    "validate_source_registry_document",
]
