# Current project status

> **Purpose:** this is the authoritative snapshot of what exists in the repository **now**.
> For task order, use `docs/11_progress.md` and `docs/10_implementation_plan.md`.
> Do not infer current completion state from the roadmap or historical issue checklists.

Last reconciled: **2026-09-07**

## Current milestone

**M1 — Real-trip CastNetGPT v0.1 vertical slice**

Milestone 0, the offline deterministic scoring foundation, is substantially implemented. Task M1.1
added a validated user-supplied run input document format, and Task M1.2 wired explicit run inputs into
the CLI `rank` command (`--inputs <path>`).

## What GeoWeaver is

GeoWeaver is intended to become a reusable spatial-intelligence engine. CastNetGPT is its first
application and is deliberately narrow: rank shoreline candidates for a specified trip while
keeping legality, safety, evidence quality, provenance, uncertainty, and explanation visible.

The current implementation is **not** a live recommendation system. It is an offline Python
foundation exercised with fictional synthetic fixtures.

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
- source registry JSON loading and validation under `src/geoweaver/data/provenance.py` and
  `data/templates/source_registry.template.json`;
- deterministic hard constraints under `src/geoweaver/scoring/constraints.py`;
- deterministic scoring, confidence calculation, and ranking under
  `src/geoweaver/scoring/scorer.py`;
- explanation helpers under `src/geoweaver/scoring/explanations.py`;
- JSON and Markdown report renderers under `src/geoweaver/reports/`;
- a console entry point in `src/geoweaver/cli.py`;
- fictional demonstration inputs in `src/geoweaver/demo.py` and
  `data/catalogue/demo_segments.geojson`;
- automated tests covering catalogue validation, run-input validation, loading, constraints,
  scoring, reports, and CLI behaviour under `tests/`;
- pytest and Ruff development configuration.

The typed run-time concepts already include `ConditionSnapshot`, `UserPreferences`,
`TravelEstimate`, `RankedRecommendation`, and `RecommendationRun`.

## Demonstration workflow that exists today

A developer can install the package and run the synthetic offline workflow:

```sh
uv sync --extra dev
uv run geoweaver validate-catalogue --catalogue data/catalogue/demo_segments.geojson
uv run geoweaver rank --catalogue data/catalogue/demo_segments.geojson --format markdown
```

The `rank` command currently takes a catalogue and output format, but it obtains conditions,
preferences, origin/travel estimates, and related run inputs from fixed synthetic demonstration
helpers. Task M1.1 introduced `load_run_input` for loading user-supplied input files, and M1.2 will
wire this into `geoweaver rank`.

## Implemented but not yet complete for a real trip

### CLI integration of explicit run inputs

The CLI `rank` command accepts `--inputs <path>` to load explicit user-supplied recommendation-run inputs,
omitting demonstration notices and labelling for custom inputs while preserving demo defaults when omitted.

### Shoreline catalogue contract

The GeoJSON contract is implemented and documented, but the checked-in catalogue is synthetic.
There is not yet a reviewed set of 20 real Ipswich/Brisbane/Logan shoreline candidates suitable
for operational use.

### Provenance and evidence concepts

The project documents provenance requirements and the domain models retain source
references, verification state, restrictions, condition source references, and timestamps.
Task M1.3 introduced `SourceRecord`, `SourceRegistry`, and `load_source_registry` for validating file-based source registries.

### Scoring and confidence

The deterministic scorer, hard gates, explanations, and separate confidence signal exist. They
must remain the baseline when later live adapters and ML experiments are added.

## Not implemented yet

The following capabilities must not be assumed to exist:

- user-supplied end-to-end run input via CLI;
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

**M1.4 — Define and test the real-candidate curation workflow.**

See `docs/10_implementation_plan.md` for the complete task contract and
`docs/11_progress.md` for the authoritative task state.

## How to update this file

Update this document only when repository capabilities or material blockers change. Keep it a
snapshot, not a changelog. Historical detail belongs in Git history, issues, PRs, ADRs, or field
reports.
