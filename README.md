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
the contracts and deterministic rules with synthetic fixtures. Explicit user-supplied run inputs
(M1.1/M1.2), a file-based provenance/source registry with CLI auditing (M1.3), a curation
workflow with a synthetic worked example (M1.4), and an operational legal/closure/advisory
evidence workflow with synthetic regression coverage (M1.6) now exist. The real-trip work still
requires reviewed shoreline candidates, authoritative real evidence, selected code/data licensing
strategy, and a recorded field test.

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
geoweaver validate-catalogue \
  --catalogue data/catalogue/demo_segments.geojson \
  --sources data/templates/source_registry.template.json
geoweaver rank --catalogue data/catalogue/demo_segments.geojson
geoweaver rank --catalogue data/catalogue/demo_segments.geojson --format json
geoweaver rank --catalogue data/catalogue/demo_segments.geojson --format markdown
geoweaver rank \
  --catalogue data/catalogue/demo_segments.geojson \
  --inputs data/templates/run_input.template.json \
  --format markdown
geoweaver rank \
  --catalogue data/catalogue/demo_segments.geojson \
  --inputs data/templates/run_input.template.json \
  --sources data/templates/source_registry.template.json \
  --format json
```

Three modes matter; do not confuse them:

- **Synthetic demo mode** (`rank` without `--inputs`): uses the fixed synthetic condition
  snapshot, demo preferences, and fictional travel estimates from `src/geoweaver/demo.py`.
  Reports are labelled as demonstration output. This keeps results reproducible for
  regression testing but is not a real recommendation.
- **Explicit offline recommendation inputs** (`rank --inputs <run-input>`): loads
  user-supplied conditions, preferences, and travel estimates from a validated JSON
  document (`data/templates/run_input.template.json` shows the shape). Demonstration
  labelling is omitted. No Python edits are needed; invalid inputs exit non-zero.
- **Provenance-registry validation** (`--sources <registry>` on either `validate-catalogue`
  or `rank`): checks that important `source_ref` values resolve to entries in a validated
  file-based source registry (`data/templates/source_registry.template.json`). On `rank`,
  both catalogue references and run-input evidence references are audited before ranking,
  and dangling references fail closed with a non-zero exit. Omitting `--sources` skips
  the audit and preserves the plain offline behaviour.

Genuinely unimplemented: reviewed real shoreline candidates, authoritative live adapters
(weather, tide, routing, daylight, closures/advisories), a production database, frontend/API,
terrain/imagery processing, machine learning, and production deployment.

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

- Without `--inputs`, the `rank` command still uses fixed synthetic demo conditions,
  preferences, origin, and travel estimates. With `--inputs`, it uses explicit offline
  user-supplied run inputs instead — but those inputs are still manually authored, not live.
- There are no live weather, tide, routing, closure, or advisory adapters.
- There is no reviewed real shoreline catalogue ready for operational recommendations
  (curation workflow exists; real publication is blocked on the D1 licence decision).
- Provenance auditing (`--sources`) verifies that references resolve to documented registry
  entries; it does not verify real-world truth of the underlying claims.
- There is no frontend, API, authentication, production database, scraping, terrain/imagery
  processing, machine learning, or production deployment.
- Scores express a transparent relative ranking, not catch probability or expected catch.
- Code licence and real-data licensing/governance decisions remain open.
- Interfaces and schemas may change before the first tagged production-oriented release.
