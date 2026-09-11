# Current project status

> **Purpose:** this is the authoritative snapshot of what exists in the repository **now**.
> For task order, use `docs/11_progress.md` and `docs/10_implementation_plan.md`.
> Do not infer current completion state from the roadmap or historical issue checklists.

Last reconciled: **2026-09-11**

## Current milestone

**M1 — Real-trip CastNetGPT v0.1 vertical slice**

Milestone 0, the offline deterministic scoring foundation, is substantially implemented. Task M1.1
added a validated user-supplied run input document format, Task M1.2 wired explicit run inputs into
the CLI `rank` command (`--inputs <path>`), Task M1.3 added a validated file-based
provenance/source registry contract, Task M1.4 defined the real-candidate curation
workflow with a synthetic worked example, and Task M1.6 made legal, closure, and
health-advisory evidence operational with a documented source hierarchy and regression
coverage (all synthetic fixtures).

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
- provenance/source registry loading, validation, and audit helpers under
  `src/geoweaver/data/sources.py` and `data/templates/source_registry.template.json`;
- real-candidate curation checklist under `data/catalogue/CURATION.md` with a synthetic
  candidate template (`data/templates/curated_candidate.template.geojson`), a matching
  registry template (`data/templates/curation_registry.template.json`), and a `--sources`
  provenance audit on `validate-catalogue`;
- legal, closure, and health-advisory evidence workflow documented in
  `docs/12_legal_advisory_evidence.md` (authoritative source hierarchy, effective
  periods, retrieval timestamps, fail-closed unknown/contradictory handling) with
  regression tests in `tests/test_legal_advisory.py` pinning that a high habitat
  score never overrides a legal/advisory failure and reports name the evidence;
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
`TravelEstimate`, `RankedRecommendation`, `RecommendationRun`, and `SourceRecord`.

## Demonstration workflow that exists today

A developer can install the package and run the synthetic offline workflow:

```sh
uv sync --extra dev
uv run geoweaver validate-catalogue --catalogue data/catalogue/demo_segments.geojson
uv run geoweaver rank --catalogue data/catalogue/demo_segments.geojson --format markdown
uv run geoweaver rank \
  --catalogue data/catalogue/demo_segments.geojson \
  --inputs data/templates/run_input.template.json \
  --sources data/templates/source_registry.template.json \
  --format markdown
```

The `rank` command accepts a catalogue, an output format, an optional `--inputs`
run-input document, and an optional `--sources` source registry. Without `--inputs` it
uses fixed synthetic demonstration helpers; with `--inputs` it loads explicit
user-supplied conditions, preferences, and travel estimates and omits demonstration
labelling. When `--sources` is supplied, `rank` audits important source references from
both the catalogue and the run-input evidence against the registry before ranking and
fails closed on dangling references; omitting it preserves the plain offline behaviour.

## Implemented but not yet complete for a real trip

### CLI integration of explicit run inputs

The CLI `rank` command accepts `--inputs <path>` to load explicit user-supplied recommendation-run inputs,
omitting demonstration notices and labelling for custom inputs while preserving demo defaults when omitted.

### Provenance/source registry

A validated file-based registry (`SourceRecord` + `load_source_registry`) describes each stable
source ID with publisher, title, URL/catalogue identifier, licence/terms, retrieved and
publication timestamps, CRS/resolution where relevant, transformation, and limitations. The
synthetic template covers all demo catalogue and run-input references.
`find_missing_source_refs`/`collect_*_source_refs` audit helpers verify coverage, and the
CLI enforces it: `validate-catalogue --sources` audits catalogue references, while
`rank --sources` audits both catalogue and run-input evidence references before ranking.
Existing `source_refs` remain IDs pointing into this registry.

### Curation workflow

`data/catalogue/CURATION.md` defines the repeatable process for proposing a real shoreline
candidate: stable IDs, WGS 84 geometry, required evidence per field, `remote_reviewed`
ceiling for desk research, explicit fail-closed unknowns, and a registry entry for every
source reference. `validate-catalogue --catalogue <file> --sources <registry>` checks
structure plus provenance. No real redistributable records are committed until D1 is
resolved; the checked-in templates are synthetic.

### Shoreline catalogue contract

The GeoJSON contract is implemented and documented, but the checked-in catalogue is synthetic.
There is not yet a reviewed set of 20 real Ipswich/Brisbane/Logan shoreline candidates suitable
for operational use.

### Provenance and evidence concepts

The project documents provenance requirements and the current domain models retain source
references, verification state, restrictions, condition source references, and timestamps.
The file-based registry contract and curation workflow exist; populating them with real
redistributable data is blocked on D1.

### Scoring and confidence

The deterministic scorer, hard gates, explanations, and separate confidence signal exist. They
must remain the baseline when later live adapters and ML experiments are added.

## Not implemented yet

The following capabilities must not be assumed to exist:

- reviewed real shoreline catalogue;
- selected repository code licence and explicit data-licensing strategy;
- authoritative real-trip legal/closure/advisory evidence populated with real sources
  (the M1.6 workflow, hierarchy documentation, and synthetic regression coverage exist;
  real publication still needs D1);
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

**M1.7 — Document and implement manual tide-station assignment evidence.**

Its tide-source prerequisite is satisfied by M1.7a
(`docs/13_tide_source_research.md` names the MSQ Queensland Tide Tables as the v0.1
source). See `docs/10_implementation_plan.md` for its exact contract and
`docs/11_progress.md` for the authoritative task state.

## How to update this file

Update this document only when repository capabilities or material blockers change. Keep it a
snapshot, not a changelog. Historical detail belongs in Git history, issues, PRs, ADRs, or field
reports.
