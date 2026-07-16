"""Tests for JSON and Markdown report contracts."""

import json

from geoweaver.demo import (
    demonstration_condition,
    demonstration_preferences,
    demonstration_travel_estimates,
)
from geoweaver.domain.models import ShorelineSegment
from geoweaver.reports.json_report import render_json
from geoweaver.reports.markdown_report import render_markdown
from geoweaver.scoring.scorer import rank_segments


def test_json_report_structure(demo_segments: tuple[ShorelineSegment, ...]) -> None:
    run = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )
    report = json.loads(render_json(run))

    assert report["schema_version"] == "geoweaver-report-v0.1"
    assert report["condition_snapshot"]["inferred"] is False
    assert report["demonstration_notice"]
    assert len(report["recommendations"]) == len(demo_segments)
    first = report["recommendations"][0]
    assert {
        "eligible",
        "final_score",
        "confidence_band",
        "component_scores",
        "diagnostic_components",
        "strongest_positive_factors",
        "highest_scoring_components",
        "strongest_limitations",
        "hard_gate_failures",
        "missing_or_stale_information",
        "verification_status",
        "source_refs",
        "data_last_updated",
        "travel_time_minutes",
        "travel_origin",
        "model_version",
        "applicable_restrictions",
        "health_advisory_evidence",
        "legal_status_evidence",
        "activity_permission_evidence",
        "restriction_review_evidence",
        "condition_snapshot_id",
        "travel_provenance",
    } <= first.keys()
    assert "data_quality" not in first["component_scores"]
    assert first["diagnostic_components"] == {
        "data_quality": run.recommendations[0].score.data_quality
    }


def test_json_report_exposes_restriction_provenance(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    run = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )
    report = json.loads(render_json(run))
    closed = next(
        item for item in report["recommendations"] if item["segment_id"] == "demo-closed-reach"
    )
    restriction = closed["applicable_restrictions"][0]

    assert restriction == {
        "authority": "GeoWeaver synthetic fixture",
        "effective_from": "2026-01-01T00:00:00+00:00",
        "effective_to": "2026-12-31T23:59:59+00:00",
        "evidence_state": "verified",
        "reason": "A fictional active closure exists to exercise the legal hard gate.",
        "restriction_id": "demo-closure-001",
        "restriction_type": "synthetic_closure",
        "retrieved_at": "2026-01-15T00:00:00+00:00",
        "source_ref": "demo://synthetic/restrictions/closed-reach",
        "status": "active",
    }
    health_evidence = closed["health_advisory_evidence"]
    assert health_evidence["authority"] == "GeoWeaver synthetic fixture"
    assert health_evidence["evidence_state"] == "verified"
    assert health_evidence["source_ref"] == "demo://synthetic/health/closed-reach"
    assert health_evidence["status"] == "inactive"
    assert health_evidence["effective_from"] == "2026-01-01T00:00:00+00:00"
    assert health_evidence["effective_to"] == "2026-12-31T23:59:59+00:00"
    assert health_evidence["retrieved_at"] == "2026-01-15T00:00:00+00:00"
    assert closed["legal_status_evidence"]["source_ref"]
    assert closed["activity_permission_evidence"]["source_ref"]
    assert closed["restriction_review_evidence"]["source_ref"]


def test_rank_segments_populates_condition_and_travel_provenance(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    run = rank_segments(
        (demo_segments[0],),
        demonstration_condition(),
        demonstration_preferences(),
        (demonstration_travel_estimates()[0],),
    )
    recommendation = json.loads(render_json(run))["recommendations"][0]

    assert recommendation["condition_snapshot_id"] == "demo-conditions-v0.1"
    assert recommendation["travel_provenance"] == {
        "evidence_state": "inferred",
        "retrieved_at": "2026-01-14T12:00:00+00:00",
        "source_ref": "demo://synthetic/travel-times/v0.1",
    }


def test_markdown_report_explains_rankings(
    demo_segments: tuple[ShorelineSegment, ...],
) -> None:
    run = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )
    report = render_markdown(run)

    assert "# CastNetGPT v0.1 Demonstration Ranking" in report
    assert "fictional" in report.lower()
    assert "## 1. Fictional Demo Alpha Gutter" in report
    assert "### Suitability component scores" in report
    assert "### Unweighted diagnostics" in report
    assert "evidence inputs affect confidence, not recommendation score" in report
    assert "### Meaningful positive factors" in report
    assert "### Strongest limitations" in report
    assert "### Hard-gate failures" in report
    assert "active_legal_closure" in report
    assert "Data last updated" in report
    assert "Source references" in report
    assert "### Legal and health evidence" in report
    assert "demo://synthetic/restrictions/closed-reach" in report
    assert "Fictional Demo Origin" in report
    assert "catch probability" not in report.lower()


def test_json_render_is_deterministic(demo_segments: tuple[ShorelineSegment, ...]) -> None:
    first_run = rank_segments(
        demo_segments,
        demonstration_condition(),
        demonstration_preferences(),
        demonstration_travel_estimates(),
    )
    second_run = rank_segments(
        tuple(reversed(demo_segments)),
        demonstration_condition(),
        demonstration_preferences(),
        tuple(reversed(demonstration_travel_estimates())),
    )

    assert render_json(first_run) == render_json(second_run)
