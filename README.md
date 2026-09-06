# GeoWeaver

**GeoWeaver is an open-source spatial intelligence engine that fuses geospatial,
environmental, temporal, and observational data to reason about real-world locations.**

Its first application is **CastNetGPT**: an explainable decision-support experiment for
ranking shoreline candidates. The current implementation remains offline and demonstration-first.

> **Demo warning:** `data/catalogue/demo_segments.geojson` contains fictional synthetic
> records and coordinates only. Its output is not a real fishing recommendation and does not
> replace official weather, fisheries, access, health, navigation, or emergency advice.

## Vision

> Understand the world, not just map it.

GeoWeaver is designed as a reusable core rather than a fishing-specific application. The same
spatial reasoning pipeline may later support flood analysis, property intelligence, kayaking,
wildlife observation, environmental monitoring, and planetary or celestial mapping.

## Initial scope

The first study area covers:

- Ipswich
- Brisbane
- Logan

The first practical vertical slice is a reproducible workflow that can rank a curated set of
shoreline candidates for one real cast-net field trip while making legality, safety, evidence
quality, provenance, confidence, and limitations explicit.

## Working offline scoring foundation

The repository provides a Python 3.12+ package that:

- validates the documented v0.1 GeoJSON contract;
- applies fail-closed activity, tidal, legal/advisory, access, weather, terrain/footing,
  casting-space, daylight, family, travel-time, freshness, and critical-information gates;
- ranks eligible demo segments with a deterministic, versioned rule set;
- reports score and evidence confidence separately; and
- emits explanation-first JSON and Markdown reports from a console command.

This foundation does **not** complete Issue #1 or the real-trip v0.1 vertical slice. It exercises
the contracts and deterministic rules with synthetic fixtures. The real-trip work still requires
explicit user-supplied run inputs, reviewed shoreline candidates, authoritative legal and
condition evidence, selected code/data licensing strategy, and a recorded field test.

## Installation

[`uv`](https://docs.astral.sh/uv/) is the preferred dependency manager:

```sh
uv sync --extra dev
uv run geoweaver validate-catalogue --catalogue data/catalogue/demo_segments.geojson
```

If `uv` is unavailable, use a Python 3.12+ virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

## Development commands

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Without `uv`, replace `uv run` with `.venv/bin/python -m` for pytest and use
`.venv/bin/ruff` for Ruff.

## CLI examples

```sh
geoweaver validate-catalogue --catalogue data/catalogue/demo_segments.geojson
geoweaver rank --catalogue data/catalogue/demo_segments.geojson
geoweaver rank --catalogue data/catalogue/demo_segments.geojson --format json
geoweaver rank --catalogue data/catalogue/demo_segments.geojson --format markdown
```

The rank command currently uses a fixed, printed synthetic condition snapshot, fixed demo
preferences, and sourced manual travel estimates from a fictional origin. This keeps M0 results
reproducible while explicit user-supplied run inputs are implemented in M1.

## Continuing development

A contributor or AI agent starting with no prior context should **not** guess the next task from
this README, the roadmap, or an old issue checklist.

Read in this order:

1. `AGENTS.md` — mandatory repository workflow and safety/engineering rules;
2. `docs/09_status.md` — authoritative snapshot of what exists now;
3. `docs/11_progress.md` — authoritative task state and the single task marked **NEXT**;
4. `docs/10_implementation_plan.md` — detailed task prerequisites, scope, tests, acceptance
   criteria, and the staged path through later milestones;
5. `docs/01_architecture.md` and the task-specific domain documents/ADRs.

The implementation workflow is deliberately incremental: inspect existing code and tests, complete
one NEXT task, run the complete checks, update progress/status, and only then advance.

## Planned capabilities

- User-supplied reproducible recommendation runs
- Reviewed shoreline segmentation and public-access modelling
- Weather, wind, rainfall, tide, warning, and daylight integration
- Terrain and bank-slope analysis from DEM and LiDAR
- Aerial and satellite feature extraction with human review
- Rule-based environmental scoring as a transparent baseline
- Field-observation logging and calibration
- Machine-learning ranking once sufficient outcome data exists
- A reusable application/plugin platform after the first vertical slice is proven

## Repository structure

```text
src/geoweaver/  Implemented domain, data validation, scoring, reports, demo inputs, and CLI
docs/           Status, implementation plan, architecture, data/scoring research, roadmap, ADRs
backend/        Reserved for later service-oriented evolution; not the current Python core
frontend/       Reserved for the interactive-interface milestone
data/           Small redistributable schemas, templates, and curated/demo datasets
models/         Rule/learned-model documentation or artefacts as later milestones require
scripts/        Reproducible data acquisition, transformation, and maintenance utilities
notebooks/      Exploration and geospatial research; not production logic
tests/          Automated unit, regression, report, validation, scoring, and CLI tests
```

## Current milestone

**M1 — Real-trip CastNetGPT v0.1 vertical slice**

The M0 offline scoring foundation exists and is exercised against synthetic data. M1 turns those
contracts into a reproducible real-trip workflow, beginning with validated user-supplied run inputs
and then adding provenance, curation, authoritative evidence, and field validation.

See `docs/09_status.md` for the current capability snapshot and `docs/11_progress.md` for the
single next task.

## Current limitations

- Demo conditions, preferences, origin, and travel estimates are still fixed and synthetic in the
  current CLI workflow.
- There are no live weather, tide, routing, closure, or advisory adapters.
- There is no reviewed real shoreline catalogue ready for operational recommendations.
- There is no frontend, API, authentication, production database, scraping, terrain/imagery
  processing, machine learning, or production deployment.
- Scores express a transparent relative ranking, not catch probability or expected catch.
- Code licence and real-data licensing/governance decisions remain open.
- Interfaces and schemas may change before the first tagged production-oriented release.
