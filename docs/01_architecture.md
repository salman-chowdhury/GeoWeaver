# Architecture

## Status and scope

This document describes GeoWeaver's **current architectural direction**. For what is implemented
right now, read `docs/09_status.md`. For implementation order, read
`docs/10_implementation_plan.md` and `docs/11_progress.md`.

The original design proposed several package boundaries before implementation began. The working
M0 foundation now lives under `src/geoweaver/`; new work must extend that implementation rather
than recreating historical `backend/domain` or `backend/services` scaffolding.

## System context

GeoWeaver is a reusable spatial reasoning core with application-specific objectives layered on top.

```text
Authoritative data + curated observations
                  |
          ingestion and validation
                  |
       canonical spatial data model
                  |
       feature and condition engine
                  |
        constraints and scoring
                  |
   explanation and uncertainty layer
                  |
        application interfaces
```

A key reproducibility boundary is that external/live evidence must be converted into an explicit,
timestamped internal snapshot before it reaches the deterministic scoring core.

## Core layers

### 1. Source adapters and ingestion

Adapters retrieve or import weather, tide, terrain, imagery metadata, access, zoning,
restriction/advisory, routing, and field-observation data. Every material external record should
retain enough metadata to audit its publisher/source, retrieval time, licence/terms, relevant
spatial/temporal resolution, and transformations.

M0 contains file loaders/validation but no live provider adapters. Future provider adapters should
live inside the Python package under a clear adapter/source boundary and must not be embedded in
`domain` or `scoring` modules.

### 2. Canonical domain model and storage

The current canonical domain is implemented as immutable/validated Python models in
`src/geoweaver/domain/`. The current v0.1 workflow uses small version-controlled files rather than
a production database.

The long-term canonical store may represent locations/segments, access points, environmental
features, condition snapshots, restrictions, source/provenance records, observations, model
versions, and recommendation runs.

PostgreSQL with PostGIS remains a likely long-term option, but it is **not** a current dependency.
Adopt it only when spatial joins, data volume, history, concurrent updates, or service requirements
justify the operational cost. That decision belongs to a later ADR.

### 3. Feature and condition engine

The feature/condition layer derives application-neutral variables such as:

- shoreline slope and orientation;
- distance to drains, creek mouths, mangroves, parking, and toilets;
- tide stage and rate of change;
- wind exposure relative to shoreline orientation;
- daylight remaining;
- travel estimates;
- data freshness and evidence coverage.

Stable spatial attributes and time-varying condition evidence should remain distinct.

### 4. Constraint engine

Constraints exclude locations when critical requirements fail. CastNetGPT examples include legal
permission, tidal eligibility, closures/advisories, public access, severe weather/lightning,
footing/casting space, travel limit, daylight, and user-specific family/access requirements.

Hard constraints must remain separate from the soft score. Critical unknowns fail closed according
to the documented rule profile.

The current implementation is in `src/geoweaver/scoring/constraints.py`.

### 5. Scoring engine

Each application supplies an objective profile. CastNetGPT currently uses a deterministic,
versioned rule set combining habitat opportunity, environmental condition match, access/usability,
privacy, family suitability, safety/risk, and travel efficiency.

The current implementation is in `src/geoweaver/scoring/scorer.py`. It remains the transparent
baseline even if learned ranking is introduced later.

### 6. Confidence and explanation layer

A recommendation must preserve:

- eligibility and hard-gate results;
- final suitability score;
- confidence as a separate signal;
- strongest positive factors;
- strongest limitations;
- missing or stale evidence;
- applicable restrictions/advisories;
- provenance/source references;
- relevant timestamps;
- model/rule version.

The current explanation helpers are under `src/geoweaver/scoring/` and report renderers under
`src/geoweaver/reports/`.

### 7. Application interfaces

Planned interface order remains deliberately incremental:

1. command-line report;
2. explicit file-based recommendation-run inputs;
3. live-condition orchestration behind adapters;
4. lightweight service/UI boundary;
5. interactive map and field-observation workflow;
6. stable API/plugin surface for additional applications.

Do not introduce a frontend or production API merely as scaffolding before the corresponding
milestone.

## Implemented M0 architecture

```text
GeoJSON catalogue + explicit synthetic demo inputs
                  |
         data loading/validation
                  |
          immutable domain models
                  |
         hard constraint evaluation
                  |
      deterministic score + confidence
                  |
        explanations and ranking
                  |
          JSON/Markdown reports
                  |
                CLI
```

Implemented package shape:

```text
src/geoweaver/
├── cli.py
├── demo.py
├── data/
├── domain/
├── reports/
└── scoring/
```

The `backend/` and `frontend/` directories are reserved for later evolution and currently contain
no alternative implementation of the core.

## M1 target architecture

The real-trip v0.1 milestone should remain file-based and offline-capable:

```text
reviewed GeoJSON catalogue
        +
validated recommendation-run input
        +
source/provenance registry
        |
existing domain + constraints + scorer
        |
reproducible ranked JSON/Markdown report
        |
field observation + retrospective
```

Manual authoritative condition/travel evidence is acceptable for M1. Live acquisition belongs to
M2.

## Planned live-data boundary

From M2 onward, preserve this direction:

```text
external provider
      |
provider-specific adapter
      |
validation / provenance capture
      |
explicit internal snapshot
      |
existing recommendation core
```

Normal scorer tests must remain offline and deterministic. Network failures or incomplete provider
data must become explicit unavailable/unknown evidence rather than hidden fallbacks.

## Architecture decisions already made

These are no longer open questions:

- Python 3.12+ for the current core;
- package root `src/geoweaver/`;
- `pyproject.toml` with setuptools;
- `uv` as preferred dependency/environment workflow;
- pytest for tests;
- Ruff for lint/format checks;
- file-based v0.1 rather than early PostGIS;
- deterministic rule-based scoring before machine learning;
- GeoJSON for the MVP catalogue;
- score and confidence are separate signals;
- unknown critical legal/safety evidence fails closed.

See `docs/adr/` for recorded decisions.

## Decisions still required

- code licence;
- data redistribution/licensing strategy;
- routing provider and cache policy;
- authoritative machine-readable weather/warning approach;
- automated tide source and station-assignment method;
- permitted imagery sources and derivative-use rules;
- terrain source/processing strategy;
- service/frontend framework and deployment shape, when M3 justifies them;
- PostGIS adoption, when M7 or scale justifies it;
- learned-model promotion criteria, after sufficient observations exist.

Material provider, governance, persistence, interface, and ML promotion decisions should be
recorded as ADRs rather than silently embedded in implementation code.
