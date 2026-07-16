"""Command-line interface for the offline GeoWeaver v0.1 slice."""

import argparse
import sys
from collections.abc import Sequence
from contextlib import ExitStack
from importlib.resources import as_file, files
from pathlib import Path

from geoweaver.data.loader import load_catalogue
from geoweaver.data.run_inputs import (
    RunInputValidationError,
    load_condition_snapshots,
    load_travel_estimates,
    load_trip_request,
)
from geoweaver.data.validation import CatalogueValidationError
from geoweaver.reports.json_report import render_json
from geoweaver.reports.markdown_report import render_markdown
from geoweaver.services.recommendation import rank_trip

DEMO_RESOURCE_PACKAGE = "geoweaver.demo_data"
DEMO_CATALOGUE_RESOURCE = "demo_segments.geojson"
DEMO_TRIP_RESOURCE = "demo_trip.json"
DEMO_CONDITIONS_RESOURCE = "demo_conditions.json"
DEMO_TRAVEL_RESOURCE = "demo_travel.json"
EXIT_SUCCESS = 0
EXIT_INPUT_ERROR = 2
EXIT_RANKING_ERROR = 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geoweaver",
        description="Validate catalogues and rank reproducible offline GeoWeaver inputs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate-catalogue", help="Validate a v0.1 GeoJSON catalogue."
    )
    validate_parser.add_argument("--catalogue", required=True, type=Path)

    rank_parser = subparsers.add_parser(
        "rank", help="Rank a catalogue using explicit trip, condition, and travel JSON files."
    )
    rank_parser.add_argument("--catalogue", required=True, type=Path)
    rank_parser.add_argument("--trip", required=True, type=Path)
    rank_parser.add_argument("--conditions", required=True, type=Path)
    rank_parser.add_argument("--travel", required=True, type=Path)
    rank_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Report format (default: markdown).",
    )

    demo_parser = subparsers.add_parser(
        "demo", help="Run the committed fictional demonstration files."
    )
    demo_parser.add_argument(
        "--catalogue",
        type=Path,
        help="Optional catalogue override; the packaged synthetic catalogue is the default.",
    )
    demo_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Report format (default: markdown).",
    )
    return parser


def _validate(catalogue: Path) -> int:
    segments = load_catalogue(catalogue)
    print(f"Catalogue valid: {len(segments)} segment(s) loaded from {catalogue}.")
    return EXIT_SUCCESS


def _rank(
    catalogue: Path,
    trip_path: Path,
    conditions_path: Path,
    travel_path: Path,
    report_format: str,
) -> int:
    segments = load_catalogue(catalogue)
    trip = load_trip_request(trip_path)
    conditions = load_condition_snapshots(conditions_path, segments, trip)
    travel_estimates = load_travel_estimates(travel_path, segments, trip)
    run = rank_trip(segments, trip, conditions, travel_estimates)
    report = render_json(run) if report_format == "json" else render_markdown(run)
    sys.stdout.write(report)
    return EXIT_SUCCESS


def _demo(catalogue_override: Path | None, report_format: str) -> int:
    resources = files(DEMO_RESOURCE_PACKAGE)
    with ExitStack() as stack:
        catalogue = catalogue_override or stack.enter_context(
            as_file(resources.joinpath(DEMO_CATALOGUE_RESOURCE))
        )
        trip = stack.enter_context(as_file(resources.joinpath(DEMO_TRIP_RESOURCE)))
        conditions = stack.enter_context(as_file(resources.joinpath(DEMO_CONDITIONS_RESOURCE)))
        travel = stack.enter_context(as_file(resources.joinpath(DEMO_TRAVEL_RESOURCE)))
        return _rank(catalogue, trip, conditions, travel, report_format)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process-compatible exit code."""
    try:
        arguments = _parser().parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    try:
        if arguments.command == "validate-catalogue":
            return _validate(arguments.catalogue)
        if arguments.command == "demo":
            return _demo(arguments.catalogue, arguments.format)
        return _rank(
            arguments.catalogue,
            arguments.trip,
            arguments.conditions,
            arguments.travel,
            arguments.format,
        )
    except CatalogueValidationError as error:
        print(f"Catalogue error: {error}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except RunInputValidationError as error:
        print(f"Input error: {error}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except ValueError as error:
        print(f"Ranking error: {error}", file=sys.stderr)
        return EXIT_RANKING_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
