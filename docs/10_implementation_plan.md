# GeoWeaver incremental implementation plan

> **Audience:** a developer or AI agent starting with no prior knowledge of the repository.
>
> **Purpose:** define the safe implementation order from the current offline foundation toward a
> reusable GeoWeaver platform. This document describes **what to implement and in what order**.
> Current completion state lives in `docs/11_progress.md`; the current repository snapshot lives
> in `docs/09_status.md`.

## How to use this plan

1. Read `README.md`, `AGENTS.md`, `docs/09_status.md`, and `docs/11_progress.md` first.
2. Find the single task marked **NEXT** in `docs/11_progress.md`.
3. Read that task here in full, including prerequisites, referenced files, non-goals, tests, and
   acceptance criteria.
4. Inspect the current implementation and relevant tests before writing code. Never assume a task
   is absent just because an old issue or roadmap says it is incomplete.
5. Implement only that task unless a tiny prerequisite fix is necessary to make it testable.
6. Run targeted tests, then the complete repository checks from `AGENTS.md`.
7. Update `docs/11_progress.md`. Update `docs/09_status.md` if capabilities or blockers changed.
8. Do not start the following task in the same change unless this plan explicitly says the tasks
   may be combined.

## Task-state vocabulary

- **DONE** — acceptance criteria are met and repository checks pass.
- **NEXT** — the one task an agent should implement now.
- **READY** — prerequisites are met, but another task is currently NEXT.
- **BLOCKED** — requires an owner decision, unavailable evidence, or another incomplete task.
- **LATER** — intentionally deferred to a later milestone.

Only `docs/11_progress.md` assigns these states.

## Global engineering invariants

These apply to every task unless an ADR deliberately changes them.

### Reproducibility

- The same versioned rules plus the same explicit inputs must produce the same ranking.
- Do not read hidden machine state, wall-clock time, network state, or user-specific files from the
  scoring core.
- Live external data must first become an explicit, timestamped snapshot before scoring.

### Safety and legality

- Unknown critical legal, access, health, weather, tide, footing, or daylight evidence must not be
  treated as safe.
- Keep hard eligibility gates separate from soft scoring.
- Never optimise a score around a failed hard gate.
- Do not turn absence of evidence into evidence of permission or safety.

### Explainability

- Score and confidence remain separate.
- Every recommendation must retain enough information to explain eligibility, strongest positives,
  strongest limitations, missing/stale evidence, provenance, and model version.
- Do not describe the deterministic score as catch probability.

### Data governance

- Never commit credentials, private trip history, sensitive exact locations, restricted imagery,
  bulk rasters/LiDAR, caches, or large model weights.
- External data needs publisher/source/licence/retrieval/provenance metadata appropriate to its
  use.
- Provider terms and redistribution rights must be checked before adding an adapter or derived
  dataset.

### Scope discipline

- Prefer the smallest vertical change that can be tested.
- Do not introduce a frontend, database, service framework, queue, cloud platform, or ML framework
  only as scaffolding for a later milestone.
- Do not replace the deterministic baseline when adding learned models.

---

# M0 — Offline deterministic foundation

**Goal:** prove the contracts, constraints, scorer, confidence, reports, and CLI against synthetic
fixtures before introducing real-world data complexity.

M0 is recorded here so a new agent knows what not to rebuild.

## M0.1 Package and developer tooling

**Expected state:** DONE.

Implemented surfaces include `pyproject.toml`, `uv.lock`, `src/geoweaver/`, pytest, Ruff, and the
`geoweaver` console entry point.

## M0.2 Typed domain and GeoJSON contract

**Expected state:** DONE.

Implemented surfaces include `src/geoweaver/domain/`, `src/geoweaver/data/`, and
`data/catalogue/README.md`.

## M0.3 Deterministic hard constraints

**Expected state:** DONE.

Implemented primarily in `src/geoweaver/scoring/constraints.py` with tests in
`tests/test_constraints.py`.

## M0.4 Deterministic scoring and confidence

**Expected state:** DONE.

Implemented primarily in `src/geoweaver/scoring/scorer.py` and
`src/geoweaver/scoring/explanations.py`, with tests in `tests/test_scorer.py`.

## M0.5 JSON/Markdown reports and demonstration CLI

**Expected state:** DONE.

Implemented in `src/geoweaver/reports/`, `src/geoweaver/cli.py`, and `src/geoweaver/demo.py`, with
report and CLI tests.

## M0.6 Synthetic catalogue and regression coverage

**Expected state:** DONE.

The repository includes fictional demo data and automated validation/loader/scorer/report/CLI
coverage. This does not imply real-world readiness.

---

# M1 — Real-trip CastNetGPT v0.1

**Goal:** produce one reproducible, explainable recommendation for a real trip from explicit user
inputs and reviewed evidence, then record the field outcome.

A real trip must not proceed from the fictional demo catalogue.

## D1 — Select code licence and data-licensing strategy

**Type:** owner decision / governance.

### Objective

Make repository redistribution terms explicit before publishing a real curated dataset.

### Prerequisites

- None.

### Read first

- `README.md`
- `docs/03_data_sources.md`
- `AGENTS.md`

### Work allowed without owner approval

An agent may prepare a short ADR comparing practical code-licence options and a separate data
licensing/provenance strategy, including implications for source data and derived coordinates.

### Work requiring owner approval

- selecting the actual code licence;
- adding the final licence file if the choice has not already been approved;
- declaring a redistribution policy for real source/derived data.

### Acceptance criteria

- chosen licence is explicit;
- real-data redistribution policy is documented;
- provenance obligations for curated catalogue entries are clear.

### Non-goals

Do not use this task to choose weather, tide, routing, or imagery providers.

---

## M1.1 — Add a validated user-supplied recommendation-run input document

**This is the first implementation task after M0.**

### Objective

Replace hidden demonstration-only run inputs with a serializable, validated input document while
reusing the existing `ConditionSnapshot`, `UserPreferences`, and `TravelEstimate` domain models.
The scorer itself must remain unchanged unless a genuine contract bug is discovered.

### Why this task exists

`geoweaver rank` currently receives only the catalogue path and output format. Conditions,
preferences, and travel estimates are supplied by `src/geoweaver/demo.py`. A real trip cannot be
reproduced from repository/user files until these run inputs are explicit.

### Prerequisites

- M0 complete.
- No external provider or licence decision is required because this task uses manually supplied
  input data only.

### Read first

- `src/geoweaver/domain/models.py`
- `src/geoweaver/domain/enums.py`
- `src/geoweaver/demo.py`
- `src/geoweaver/cli.py`
- `src/geoweaver/scoring/scorer.py`
- `tests/test_cli.py`
- `tests/conftest.py`
- `docs/04_scoring_engine.md`

### Expected files to add or change

Prefer the existing package boundaries. A reasonable implementation is:

- add one loader/validation module under `src/geoweaver/data/` for run-input JSON;
- add a synthetic example under `data/templates/` or `tests/fixtures/`;
- add focused loader tests;
- do **not** wire it into the CLI yet unless necessary for testability — M1.2 owns CLI integration.

If the existing code suggests a better filename, use it and document the choice.

### Required behaviour

The input document must be able to represent, without hidden defaults:

- a condition snapshot and its applicable segment IDs;
- target/valid time with timezone;
- tide stage;
- weather warning/lightning/wind/gust evidence values and verification flags;
- footing and daylight evidence values and verification flags;
- evidence source references and freshness;
- user skill/family/casting-space/daylight/privacy/travel constraints;
- one explicit origin label;
- per-segment travel estimates with source references and inference state.

The loader must produce the existing immutable domain models and surface useful validation errors.
Unknown enum values, malformed timestamps, invalid ratings, missing required fields, duplicate
travel estimates, and inconsistent segment references must fail rather than be silently repaired.

### Non-goals

- no network calls;
- no weather/tide/routing provider integration;
- no frontend;
- no database;
- no change to scoring weights;
- no real personal trip data committed as fixtures.

### Tests

Add tests for at least:

- valid synthetic input;
- malformed JSON or wrong top-level structure;
- missing required field;
- unsupported enum;
- timezone-naive timestamp;
- duplicate travel estimate for a segment;
- invalid source reference/blank source;
- invalid numeric/rating values;
- deterministic conversion to the existing domain objects.

### Validation commands

Run targeted tests first, then:

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

### Acceptance criteria

- one synthetic file can be loaded into existing `ConditionSnapshot`, `UserPreferences`, and
  `TravelEstimate` objects;
- no scoring behaviour changes;
- all invalid-input tests fail closed with understandable errors;
- no hidden live data or user-specific state is introduced;
- full repository checks pass.

### What becomes possible next

M1.2 can make the CLI consume the input document.

---

## M1.2 — Wire explicit run inputs into `geoweaver rank`

### Objective

Allow a user to rank a catalogue using a supplied run-input document rather than fixed demo inputs.

### Prerequisites

- M1.1 DONE.

### Read first

- M1.1 implementation and tests;
- `src/geoweaver/cli.py`;
- `src/geoweaver/demo.py`;
- `tests/test_cli.py`;
- `README.md`.

### Expected change

Add an explicit CLI option such as `--inputs <path>` for `rank`. Preserve a deliberate demo path
for synthetic regression/demo use; do not silently fall back to demo data when a real input file
is invalid.

### Required behaviour

- `rank --inputs ...` loads user-supplied run inputs and passes them to `rank_segments`;
- demonstration mode remains explicit and clearly labelled synthetic;
- invalid run inputs return a non-zero exit code and a useful error;
- JSON and Markdown output remain deterministic for identical inputs;
- the command prints/retains the evidence and demonstration distinctions correctly.

### Tests

Cover valid input, missing file, invalid input, demo mode, JSON output, Markdown output, and at least
one fail-closed case caused by supplied evidence.

### Non-goals

No live adapters and no real catalogue curation.

### Acceptance criteria

A complete offline recommendation run can be reproduced from a catalogue file plus a run-input
file without editing Python code.

---

## M1.3 — Implement a provenance/source registry contract

### Objective

Replace opaque source-reference strings as the only provenance surface with a small auditable
registry describing the sources those references identify.

### Prerequisites

- M1.2 DONE.
- D1 may remain unresolved if only synthetic/non-redistributed fixtures are used, but real data
  publication stays blocked until D1 is resolved.

### Read first

- `docs/03_data_sources.md`;
- `docs/02_database.md`;
- `data/catalogue/README.md`;
- domain models and loader code.

### Required minimum fields

For each external source record, support the relevant subset of:

- stable source ID;
- publisher;
- dataset/page title;
- source URL or catalogue identifier;
- licence/terms note;
- retrieved timestamp;
- source publication/update timestamp where available;
- CRS/resolution where spatially relevant;
- transformation note;
- limitations.

### Implementation guidance

Keep the first version small and file-based. Prefer a validated JSON/CSV/GeoJSON-adjacent registry
over a database. Existing `source_refs` may remain IDs that point into this registry.

### Tests

Validate unique IDs, required metadata, timestamps, blank values, and missing references from
catalogue/run inputs where practical.

### Acceptance criteria

A reviewer can follow important evidence references from a recommendation back to documented
source metadata.

---

## M1.4 — Define and test the real-candidate curation workflow

### Objective

Create a repeatable process for adding a real shoreline candidate without confusing remote review
with field verification.

### Prerequisites

- M1.3 DONE.
- D1 must be resolved before redistributable real records are committed.

### Read first

- `data/catalogue/README.md`;
- `docs/02_database.md`;
- `docs/03_data_sources.md`;
- `docs/04_scoring_engine.md`.

### Required deliverables

- curation checklist/template;
- required evidence for access, legality, tidal status, casting space, health/advisory state,
  facilities, substrate/footing, privacy/family ratings, and environmental features;
- verification-state rules;
- clear handling of unknowns;
- validation command for a proposed catalogue.

### Non-goals

Do not claim field verification based on imagery, maps, or web research alone.

### Acceptance criteria

A second contributor can curate a candidate using the documented workflow and produce a catalogue
record that passes validation with traceable provenance.

---

## M1.5 — Curate the first 20 reviewed candidates

### Objective

Build the first real candidate catalogue across the initial Ipswich, Brisbane, and Logan study
area.

### Prerequisites

- M1.4 DONE;
- D1 DONE;
- authoritative source access adequate for the claims stored.

### Required behaviour

- every segment has a stable ID;
- every material claim has appropriate provenance;
- remote review is labelled as remote review;
- unknown legal/safety/health/access evidence remains unknown and fails closed;
- synthetic demo records remain separate and unmistakable.

### Acceptance criteria

At least 20 reviewed candidate records pass catalogue validation and the provenance audit required
by M1.3/M1.4.

---

## M1.6 — Make legal, closure, and health-advisory evidence operational

### Objective

Ensure a real run can document and enforce activity permission, active restrictions, and relevant
health/advisory state at the requested time.

### Prerequisites

- M1.3 DONE;
- authoritative sources identified;
- M1.5 may proceed in parallel only if records remain fail-closed until evidence is complete.

### Required work

- document authoritative source hierarchy;
- represent effective periods and retrieval timestamps;
- ensure active restrictions are evaluated against the run time;
- add regression tests for active, expired, future, unknown, and contradictory evidence.

### Acceptance criteria

A high habitat score can never override a legal/closure/advisory failure, and the report names the
relevant evidence.

---

## M1.7a — Research the authoritative v0.1 tide source

### Objective

Establish whether the M1.7 prerequisite ("authoritative tide source researched") is
satisfied by identifying and documenting one authoritative tide source suitable for the
initial Ipswich/Brisbane/Logan scope. Research only; no implementation.

### Prerequisites

- M1.3 source registry available (so the note can state how the source will be cited).
- Public documentation only; no credentials, bulk data, or private trip details.

### Required research

For the candidate source, record:

- publisher;
- specific product/dataset;
- geographic/tidal-reach coverage for the study area;
- station availability and relevance to the study area's tidal reaches;
- access method;
- update/publication frequency;
- licence/terms/attribution;
- redistribution constraints;
- known limitations relevant to station assignment (e.g. distant stations,
  hydraulically separated inland reaches, offsets).

### Deliverable

A short research/design note (or ADR proposal) sufficient to establish whether the M1.7
prerequisite is satisfied: either it names the researched v0.1 tide source with the
details above, or it records that no suitable authoritative source was found and what
that implies for M1.7.

### Non-goals

- Do not select or implement a live provider adapter.
- Automated tide retrieval belongs to M2.
- No ranking, scoring, or adapter code; no live network calls in tests.

### Acceptance criteria

A reviewer can read the note and determine, without further research, which authoritative
tide source M1.7 station-selection work must be based on (or that none is available).

---

## M1.7 — Document and implement manual tide-station assignment evidence

### Objective

Avoid silently applying a distant or inappropriate tide prediction to a shoreline candidate.

### Prerequisites

- M1.7a DONE (authoritative tide source researched and recorded);
- M1.3 source registry available.

### Required work

- write an ADR or focused design note defining station-selection/offset rules for v0.1;
- record station/source/assignment rationale in run evidence;
- fail closed where no defensible assignment exists;
- add edge-case tests.

### Non-goals

This task may still use manually entered tide values. Automated tide retrieval belongs to M2.

### Acceptance criteria

Every real candidate used in a run has an explicit, reviewable tide evidence path or is excluded.

---

## M1.8 — Complete the manual real-condition snapshot workflow

### Objective

Create a documented way to assemble authoritative weather, warning, wind/gust, footing, tide, and
daylight evidence for one requested trip time without live adapters.

### Prerequisites

- M1.2 input files;
- M1.3 provenance;
- M1.6 legal/advisory evidence;
- M1.7 tide assignment.

### Required work

- document evidence collection steps;
- define freshness expectations for each evidence class;
- make missing/expired evidence visibly fail or reduce confidence according to existing rules;
- add one fully synthetic end-to-end fixture demonstrating the workflow without exposing private
  trip details.

### Acceptance criteria

A reviewer can reconstruct exactly which condition evidence drove a recommendation run.

---

## M1.9 — Produce the first reproducible real-trip shortlist

### Objective

Run the complete v0.1 workflow against the reviewed catalogue for one actual planned trip.

### Prerequisites

- M1.5 through M1.8 DONE;
- D1 DONE.

### Required output

- explicit run input;
- catalogue version/commit reference;
- ranked Markdown and/or JSON report;
- model version;
- source timestamps;
- no hidden manual edits to ranking output.

### Safety rule

A recommendation report remains decision support, not a guarantee of access, safety, legality, or
catch. Recheck time-sensitive official evidence before the field visit.

### Acceptance criteria

Another contributor can reproduce the same ranking from the recorded repository version and
explicit run inputs.

---

## M1.10 — Record field observation and v0.1 retrospective

### Objective

Close the loop between prediction, field reality, and future model improvement.

### Prerequisites

- M1.9 DONE;
- actual field visit completed safely and lawfully.

### Required work

- record observation using the repository field-observation contract;
- record access reality, footing, crowding, water state, effort, outcome, and important mismatches;
- do not rewrite the pre-trip recommendation after seeing the result;
- write a short retrospective identifying model/data errors and follow-up tasks.

### Acceptance criteria

The recommendation and subsequent observation are independently preserved and comparable.

---

# M2 — Live conditions

**Goal:** automate time-dependent evidence while preserving explicit snapshots, provenance, and
reproducibility.

## M2.1 — Define source-adapter interfaces

### Objective

Introduce narrow interfaces for retrieving external evidence without coupling the scoring core to
HTTP/provider details.

### Prerequisites

- M1 complete enough that manual evidence contracts are stable.

### Guidance

Add adapters/services inside `src/geoweaver/` only when needed. Keep provider calls outside domain
and scoring modules. Convert provider responses into explicit internal snapshots.

### Acceptance criteria

The scorer can still be tested completely offline with fixtures.

## M2.2 — Weather/warning provider decision ADR

Research authoritative machine-readable weather/warning options, terms, attribution, geographic
coverage, update frequency, rate limits, and caching. Record the selected approach before coding
an adapter.

## M2.3 — Implement weather/warning adapter

Retrieve only the fields required by the current condition contract, retain raw provenance needed
for audit, handle network/provider failures explicitly, and add fixture-based tests.

## M2.4 — Implement daylight calculation/adapter

Derive or retrieve usable daylight with explicit timezone/location handling and tests around
sunrise/sunset and date boundaries. Do not infer safe night access merely from civil twilight.

## M2.5 — Tide provider and station-assignment ADR

Turn the manual M1.7 method into an automated, documented mapping strategy. Address inland tidal
reaches, station distance, offsets, validity, and unknown cases.

## M2.6 — Implement tide adapter and assignment

Produce explicit tide evidence/snapshots with provider metadata and station assignment. Test
missing stations, stale predictions, boundary times, and unsupported reaches.

## M2.7 — Condition snapshot orchestration and cache

Create a service that gathers provider evidence and writes a reproducible snapshot before scoring.
Cache policy must respect provider terms. A historical run must point to the snapshot it used.

## M2.8 — Live-condition integration tests

Use recorded/provider fixtures, not live network calls in the normal test suite. Prove that
provider failure and missing critical evidence fail closed.

---

# M3 — Interactive map and field workflow

**Goal:** provide a useful interface without moving core decision logic into the frontend.

## M3.1 — Interface/API architecture ADR

Choose the smallest service/UI architecture justified by M1/M2. Decide boundaries, deployment
shape, and whether a web framework/API is actually needed. Do not choose a framework solely from
preference.

## M3.2 — Read-only recommendation service boundary

Expose validated catalogue/run/recommendation operations through a service boundary while keeping
scoring calls in the existing core. Add contract/integration tests.

## M3.3 — Candidate map

Render candidate geometry and recommendation state with clear eligible/ineligible/confidence
visual treatment. Do not hide hard-gate reasons behind a score colour.

## M3.4 — Filters and recommendation detail

Add practical filters and an explanation panel covering score, confidence, evidence freshness,
constraints, provenance, and travel context.

## M3.5 — Field-observation form

Allow observations to be recorded against stable segment/run IDs. Validate fields and preserve
pre-trip recommendation data unchanged.

## M3.6 — Mobile field view and usability pass

Make the trip view usable on a phone, including important safety/evidence warnings without relying
on hover-only UI.

---

# M4 — Terrain intelligence

**Goal:** derive useful access/morphology features from authoritative elevation data without
premature bulk infrastructure.

## M4.1 — DEM/LiDAR coverage and licensing research

Inventory coverage, resolution, vertical datum, licences, download/API mechanisms, and study-area
limitations. Record the source decision.

## M4.2 — Reproducible terrain ingestion utility

Add a small script/pipeline that records source metadata and transformations. Do not commit bulk
raw rasters to Git.

## M4.3 — Shoreline slope/bank feature extraction

Derive bounded, documented features relevant to access and casting. Include CRS/unit tests and
synthetic geometry fixtures.

## M4.4 — Terrain evidence integration

Attach derived features and confidence/provenance to candidate records or a versioned derived
feature layer. Unknown/low-resolution terrain must not masquerade as verified safe footing.

## M4.5 — Terrain validation

Compare a sample of derived features against remote/manual or field review and document failure
modes before using terrain for hard rejection.

---

# M5 — Imagery intelligence

**Goal:** experiment with imagery-derived environmental features under explicit licensing and human
review.

## M5.1 — Imagery governance ADR

Select only imagery whose access terms permit the intended processing and derivative use. Document
attribution, retention, redistribution, resolution, and update limitations.

## M5.2 — Annotation vocabulary and dataset contract

Define labels for water, sand, mud, vegetation, built access, drains/creek mouths, and other
features needed by the application. Include ambiguous/unknown labels and reviewer metadata.

## M5.3 — Human annotation workflow

Create a reproducible small annotation set with train/evaluation separation. Never label imagery
as field verification.

## M5.4 — Baseline imagery feature extractor

Start with the simplest defensible method. Preserve model/version/source metadata and produce
confidence rather than binary truth where appropriate.

## M5.5 — Human review gate

Imagery detections may propose candidates/features, but must not independently establish legal
access, safety, or health status.

## M5.6 — Evaluation and integration

Measure useful detection metrics on held-out data and compare against manual review before feeding
imagery-derived features into ranking.

---

# M6 — Learning-to-rank

**Goal:** learn from accumulated observations only when there is enough trustworthy data to beat or
complement the deterministic baseline.

## M6.1 — Observation dataset builder

Create a versioned training table from field observations plus contemporaneous features. Preserve
run IDs, effort, time, region, source versions, and missingness.

## M6.2 — Learning objective and evaluation protocol

Define target/outcome normalization, metrics, temporal/geographic splits, leakage controls, and the
minimum evidence needed before claiming improvement.

## M6.3 — Deterministic baseline evaluation

Measure the existing rule model using the same evaluation protocol. This is the comparison floor.

## M6.4 — First learned ranking model

Use a simple interpretable baseline before complex models. Pin dependencies, random seeds, feature
versions, and training data snapshot.

## M6.5 — Calibration and uncertainty

Separate ranking quality from calibrated probability. Do not expose catch probabilities unless
calibration evidence supports that interpretation.

## M6.6 — Bias, drift, and regional robustness

Check performance by region, season, user/effort characteristics, and data quality. Detect when the
model is operating outside its evidence base.

## M6.7 — Shadow-mode integration

Run the learned model beside the deterministic baseline and compare outputs before allowing it to
influence user recommendations.

## M6.8 — Promotion decision ADR

Document whether, where, and under what safeguards the learned model may affect ranking. The
rule-based model remains available as a transparent baseline/fallback.

---

# M7 — Reusable GeoWeaver v1 platform

**Goal:** generalise the proven CastNetGPT pipeline into a stable spatial-intelligence platform
without erasing application-specific objectives.

## M7.1 — Stable application/core contracts

Separate reusable location/evidence/condition/recommendation concepts from CastNetGPT-specific
objective profiles and vocabulary.

## M7.2 — Persistence decision and PostGIS ADR

Adopt PostGIS only when data size, spatial joins, history, concurrent updates, or API use justify
it. Define migration and local-development strategy before implementation.

## M7.3 — Canonical persistent store

Persist sources, locations/segments, condition snapshots, restrictions, observations, model
versions, and recommendation runs with auditable relationships.

## M7.4 — Versioned objective-profile/plugin interface

Allow additional applications to define constraints/features/weights or model adapters without
copying the whole engine. Protect core provenance, snapshot, and explanation contracts.

## M7.5 — Public/stable application API

Stabilise request/result schemas, version them, document error semantics, and add contract tests.

## M7.6 — Operational security and privacy review

Threat-model authentication if introduced, private locations, trip history, credentials, source
terms, logging, retention, and abuse cases. Minimise stored personal data.

## M7.7 — Reproducible deployment

Add the minimum deployment/CI/CD infrastructure required by the proven service architecture, with
health checks, migrations, rollback, and pinned environments.

## M7.8 — Second application proof

Implement one non-fishing objective profile using the reusable core. This is the test that
GeoWeaver has actually become a platform rather than a renamed CastNetGPT codebase.

## M7.9 — v1 release audit

Before v1.0, verify documentation, licences, data governance, API compatibility, migration paths,
security/privacy, reproducibility, field evidence, and model limitations.

---

# Rules for changing this plan

This plan is intentionally conservative. Change it when new evidence makes the sequence wrong, not
merely because a different implementation sounds interesting.

When changing task order or architecture:

1. explain why in the commit/PR;
2. add or update an ADR for material architecture/provider/governance decisions;
3. update `docs/11_progress.md` so there is still exactly one NEXT task;
4. update `docs/09_status.md` if the current milestone, capability, or blocker changed;
5. ensure old roadmap/backlog text cannot be mistaken for the authoritative task state.
