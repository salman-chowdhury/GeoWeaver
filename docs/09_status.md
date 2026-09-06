# Current project status

> **Purpose:** this is the authoritative snapshot of what exists in the repository **now**.
> For task order, use `docs/11_progress.md` and `docs/10_implementation_plan.md`.
> Do not infer current completion state from the roadmap or historical issue checklists.

Last reconciled: **2026-09-07**

## Current milestone

**M1 — Real-trip CastNetGPT v0.1 vertical slice**

Milestone 0, the offline deterministic scoring foundation, is substantially implemented. Tasks M1.1
and M1.2 added a validated user-supplied run input document format and wired `--inputs <path>` into
`geoweaver rank`.

## What GeoWeaver is

GeoWeaver is intended to become a reusable spatial-intelligence engine. CastNetGPT is its first
application and is deliberately narrow: rank shoreline candidates for a specified trip while
keeping legality, safety, evidence quality, provenance, uncertainty, and explanation visible.

The current implementation is **not** a live recommendation system. It is an offline Python
foundation exercised with fictional synthetic fixtures or explicit user-supplied inputs.

## Implemented foundation

The repository currently contains the following working implementation surfaces:

- Python 3.12+ package under `src/geoweaver/`;
- packaging and tool configuration in `pyproject.toml`;
- `uv.lock`, with `uv` as the preferred dependency workflow;
- typed domain models and controlled enums under `src/geoweaver/domain/`;
- a documented and validated v0.1 shoreline GeoJSON contract;
- catalogue loading and validation under `src/geoweaver/data/`;
- run input JSON loading and validation under `src/geoweaver/data/run_input.py` and
  `data/templates/run_input.template.json`;
- deterministic hard constraints under `src/geoweaver/scoring/constraints.py`;
- deterministic scoring, confidence calculation, and ranking under
  `src/geoweaver/scoring/scorer.py`;
- explanation helpers under `src/geoweaver/scoring/explanations.py`;
- JSON and Markdown report renderers under `src/geoweaver/reports/`;
- a console entry point in `src/geoweaver/cli.py` with `validate-catalogue` and `rank`
  (supporting `--inputs <path>`);
- fictional demonstration inputs in `src/geoweaver/demo.py` and
  `data/catalogue/demo_segments.geojson`;
- automated tests covering catalogue validation, run-input validation, loading, constraints,
  scoring, reports, and CLI behaviour under `tests/`;
- pytest and Ruff development configuration.

The typed run-time concepts include `ConditionSnapshot`, `UserPreferences`, `TravelEstimate`,
`RankedRecommendation`, and `RecommendationRun`.

## Demonstration and user-input workflow that exists today

A developer can install the package and run either the synthetic demo workflow or a user-input workflow:

```sh
uv sync --extra dev
uv run geoweaver validate-catalogue --catalogue data/catalogue/demo_segments.geojson
uv run geoweaver rank --catalogue data/catalogue/demo_segments.geojson --format markdown
uv run geoweaver rank --catalogue data/catalogue/demo_segments.geojson --inputs data/templates/run_input.template.json --format markdown
```

The `rank` command accepts `--inputs <path>` to load user-supplied condition snapshots, preferences,
and travel estimates. Omitting `--inputs` continues to use reproducible synthetic demonstration inputs.

## Implemented but not yet complete for a real trip

### Shoreline catalogue contract

The GeoJSON contract is implemented and documented, but the checked-in catalogue is synthetic.
There is not yet a reviewed set of 20 real Ipswich/Brisbane/Logan shoreline candidates suitable
for operational use.

### Provenance and evidence concepts

The project documents provenance requirements and the current domain models retain source
references, verification state, restrictions, condition source references, and timestamps.
A complete real-data source registry/governance workflow has not yet been implemented (Task M1.3).

### Scoring and confidence

The deterministic scorer, hard gates, explanations, and separate confidence signal exist. They
must remain the baseline when later live adapters and ML experiments are added.

## Not implemented yet

The following capabilities must not be assumed to exist:

- provenance source registry contract;
- reviewed real shoreline catalogue;
- selected repository code licence and explicit data-licensing strategy;
- authoritative real-trip legal/closure/advisory evidence workflow;
- production weather or warning adapter;
- production tide adapter or documented station-assignment implementation;
- routing/travel-time provider;
- daylight adapter;
- persistent condition-snapshot cache;
- field-observation ingestion command or form;
- real field test and retrospective;
- API/service layer;
- frontend or interactive map;
- authentication;
- production database or PostGIS store;
- DEM/LiDAR processing;
- imagery processing or annotation pipeline;
- machine-learning ranking;
- production deployment.

## Owner decisions still required

These are decisions an autonomous coding agent must **not invent**:

1. **Code licence.** The README describes GeoWeaver as open source, but a licence must be
   deliberately selected and added.
2. **Data-licensing strategy.** The project needs rules for what source data, derived data, and
   exact coordinates may be redistributed.
3. **External provider choices** where terms, cost, caching, or redistribution materially affect
   architecture, including routing and some live-data sources.

An agent may research options and write an ADR proposal, but it must leave the decision marked as
blocked when owner approval is required.

## Architecture decisions already made

Do not reopen these merely because older documentation once listed them as undecided:

- implementation language: Python 3.12+ for the current core;
- package root: `src/geoweaver/`;
- package/build metadata: `pyproject.toml` with setuptools;
- preferred environment/dependency workflow: `uv`;
- test framework: pytest;
- formatter/linter: Ruff;
- v0.1 persistence: small version-controlled GeoJSON/CSV/JSON-style inputs rather than a
  production database;
- scoring approach: deterministic rules before machine learning;
- score and confidence are separate signals;
- unknown critical legal/safety evidence fails closed.

See `docs/adr/` and `docs/01_architecture.md` for the reasoning and architecture context.

## Current blockers

- Real-data publication is blocked on licence/data-governance decisions.
- A real recommendation run is blocked on user-supplied run inputs and authoritative evidence.
- Field validation is blocked until a real catalogue and complete trip evidence are available.

These blockers do **not** prevent implementation of the next ready coding task.

## Next task

The single next implementation task is:

**M1.3 — Implement a provenance/source registry contract.**

See `docs/10_implementation_plan.md` for the complete task contract and
`docs/11_progress.md` for the authoritative task state.

## How to update this file

Update this document only when repository capabilities or material blockers change. Keep it a
snapshot, not a changelog. Historical detail belongs in Git history, issues, PRs, ADRs, or field
reports.
