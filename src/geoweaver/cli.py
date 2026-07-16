"""Command-line interface for the offline GeoWeaver v0.1 slice."""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from geoweaver.data.loader import load_catalogue
from geoweaver.data.validation import CatalogueValidationError
from geoweaver.demo import (
    demonstration_condition,
    demonstration_preferences,
    demonstration_travel_estimates,
)
from geoweaver.reports.json_report import render_json
from geoweaver.reports.markdown_report import render_markdown
from geoweaver.scoring.scorer import DEMONSTRATION_NOTICE, rank_segments


def _demonstration_inputs_for_catalogue(segments):
    segment_ids = tuple(segment.segment_id for segment in segments)
    present_ids = set(segment_ids)
    travel_estimates = tuple(
        estimate
        for estimate in demonstration_travel_estimates()
        if estimate.segment_id in present_ids
    )
    condition = demonstration_condition()
    if present_ids.issubset(condition.applicable_segment_ids):
        condition = replace(condition, applicable_segment_ids=segment_ids)
    else:
        condition = replace(
            condition,
            snapshot_id="demo-conditions-unavailable-v0.1",
            applicable_segment_ids=segment_ids,
            tide_stage="unknown",
            severe_weather_warning=None,
            lightning_or_severe_thunderstorm_risk=None,
            footing_safe=None,
            usable_daylight_minutes=None,
            wind_speed_kph=None,
            gust_speed_kph=None,
            data_freshness_minutes=None,
            weather_status_verified=False,
            footing_status_verified=False,
            tide_status_verified=False,
            daylight_status_verified=False,
            weather_source_refs=(),
            footing_source_refs=(),
            tide_source_refs=(),
            daylight_source_refs=(),
        )
    return condition, travel_estimates


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geoweaver",
        description="Validate and rank an offline GeoWeaver v0.1 demonstration catalogue.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate-catalogue", help="Validate a v0.1 GeoJSON catalogue."
    )
    validate_parser.add_argument("--catalogue", required=True, type=Path)

    rank_parser = subparsers.add_parser(
        "rank", help="Rank a catalogue with fixed synthetic conditions and preferences."
    )
    rank_parser.add_argument("--catalogue", required=True, type=Path)
    rank_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Report format (default: markdown).",
    )
    return parser


def _validate(catalogue: Path) -> int:
    segments = load_catalogue(catalogue)
    print(f"Catalogue valid: {len(segments)} segment(s) loaded from {catalogue}.")
    print(DEMONSTRATION_NOTICE)
    return 0


def _rank(catalogue: Path, report_format: str) -> int:
    segments = load_catalogue(catalogue)
    condition, travel_estimates = _demonstration_inputs_for_catalogue(segments)
    run = rank_segments(
        segments,
        condition,
        demonstration_preferences(),
        travel_estimates,
    )
    report = render_json(run) if report_format == "json" else render_markdown(run)
    sys.stdout.write(report)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process-compatible exit code."""
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "validate-catalogue":
            return _validate(arguments.catalogue)
        return _rank(arguments.catalogue, arguments.format)
    except CatalogueValidationError as error:
        print(f"Catalogue error: {error}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"Ranking error: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
