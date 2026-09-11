# GeoWeaver progress tracker

> **Purpose:** this is the authoritative task-state file. It answers one question for a developer
> or AI agent: **what should be worked on next?**
>
> Detailed task requirements live in `docs/10_implementation_plan.md`. Current capabilities and
> blockers live in `docs/09_status.md`.

Last reconciled: **2026-09-11**

## Agent rule

There must be **exactly one** implementation task marked **NEXT**.

An agent should:

1. read the NEXT task in `docs/10_implementation_plan.md`;
2. verify its prerequisites and inspect the existing implementation/tests;
3. implement only that task;
4. run targeted tests and the full repository checks;
5. mark it DONE only when its acceptance criteria are met;
6. promote the next eligible task to NEXT;
7. update `docs/09_status.md` if repository capabilities or blockers changed.

Owner/governance decisions may remain BLOCKED while independent coding tasks proceed.

## Current milestone

**M1 — Real-trip CastNetGPT v0.1 vertical slice**

The task carrying the single NEXT marker below is the current implementation focus. Do not skip
directly to live APIs, map UI, terrain, imagery, or ML.

## M0 — Offline deterministic foundation

- [x] **DONE — M0.1 Package and developer tooling**
- [x] **DONE — M0.2 Typed domain and GeoJSON contract**
- [x] **DONE — M0.3 Deterministic hard constraints**
- [x] **DONE — M0.4 Deterministic scoring and confidence**
- [x] **DONE — M0.5 JSON/Markdown reports and demonstration CLI**
- [x] **DONE — M0.6 Synthetic catalogue and regression coverage**

These entries mean the implementation surfaces exist. A new working session should still run the
baseline checks before editing code; this file is not a substitute for test execution.

## M1 — Real-trip CastNetGPT v0.1

- [ ] **BLOCKED — D1 Select code licence and data-licensing strategy**
  - Owner decision required for final selection.
  - Does not block M1.1/M1.2 because they can use synthetic/manual private inputs.
  - Blocks publication of a real curated catalogue.
- [x] **DONE — M1.1 Add a validated user-supplied recommendation-run input document**
- [x] **DONE — M1.2 Wire explicit run inputs into `geoweaver rank`**
- [x] **DONE — M1.3 Implement a provenance/source registry contract**
- [x] **DONE — M1.4 Define and test the real-candidate curation workflow**
- [ ] **BLOCKED — M1.5 Curate the first 20 reviewed candidates**
  - Blocked by D1 (M1.4 workflow is done; real publication still needs the licence decision).
- [x] **DONE — M1.6 Make legal, closure, and health-advisory evidence operational**
- [ ] **NEXT — Tide-source research note (M1.7 prerequisite, research only)**
  - No ranking/scoring/adapter code; no live network calls in tests.
  - Identify the authoritative v0.1 tide source for the Ipswich/Brisbane/Logan study
    area: specific product/dataset, publisher, tidal-reach coverage, access terms,
    attribution, update frequency, and redistribution limits. Record the basis in a
    short note or ADR proposal using public documentation only.
  - Successor: M1.7 becomes eligible once this note exists (M1.3 registry is available;
    real publication still needs D1).
- [ ] **BLOCKED — M1.7 Document and implement manual tide-station assignment evidence**
  - Blocked on the research note above. Its prerequisite ("authoritative tide source
    researched") is not yet met: `docs/03_data_sources.md` lists only candidate source
    classes ("authoritative Queensland/Australian tide products", "Maritime Safety
    Queensland tide tables") plus an open "determine the best tide source and local
    station offsets" research task. No ADR or design note records a researched v0.1
    tide source, so station-selection implementation must not proceed yet.
  - Use synthetic fixtures when unblocked; real publication still needs D1.
- [ ] **BLOCKED — M1.8 Complete the manual real-condition snapshot workflow**
  - Blocked by M1.7 (M1.2, M1.3, and M1.6 are done).
- [ ] **BLOCKED — M1.9 Produce the first reproducible real-trip shortlist**
  - Blocked by D1 and M1.5–M1.8.
- [ ] **BLOCKED — M1.10 Record field observation and v0.1 retrospective**
  - Blocked by M1.9 and the actual field visit.

## M2 — Live conditions

- [ ] **LATER — M2.1 Define source-adapter interfaces**
- [ ] **LATER — M2.2 Weather/warning provider decision ADR**
- [ ] **LATER — M2.3 Implement weather/warning adapter**
- [ ] **LATER — M2.4 Implement daylight calculation/adapter**
- [ ] **LATER — M2.5 Tide provider and station-assignment ADR**
- [ ] **LATER — M2.6 Implement tide adapter and assignment**
- [ ] **LATER — M2.7 Condition snapshot orchestration and cache**
- [ ] **LATER — M2.8 Live-condition integration tests**

## M3 — Interactive map and field workflow

- [ ] **LATER — M3.1 Interface/API architecture ADR**
- [ ] **LATER — M3.2 Read-only recommendation service boundary**
- [ ] **LATER — M3.3 Candidate map**
- [ ] **LATER — M3.4 Filters and recommendation detail**
- [ ] **LATER — M3.5 Field-observation form**
- [ ] **LATER — M3.6 Mobile field view and usability pass**

## M4 — Terrain intelligence

- [ ] **LATER — M4.1 DEM/LiDAR coverage and licensing research**
- [ ] **LATER — M4.2 Reproducible terrain ingestion utility**
- [ ] **LATER — M4.3 Shoreline slope/bank feature extraction**
- [ ] **LATER — M4.4 Terrain evidence integration**
- [ ] **LATER — M4.5 Terrain validation**

## M5 — Imagery intelligence

- [ ] **LATER — M5.1 Imagery governance ADR**
- [ ] **LATER — M5.2 Annotation vocabulary and dataset contract**
- [ ] **LATER — M5.3 Human annotation workflow**
- [ ] **LATER — M5.4 Baseline imagery feature extractor**
- [ ] **LATER — M5.5 Human review gate**
- [ ] **LATER — M5.6 Evaluation and integration**

## M6 — Learning-to-rank

- [ ] **LATER — M6.1 Observation dataset builder**
- [ ] **LATER — M6.2 Learning objective and evaluation protocol**
- [ ] **LATER — M6.3 Deterministic baseline evaluation**
- [ ] **LATER — M6.4 First learned ranking model**
- [ ] **LATER — M6.5 Calibration and uncertainty**
- [ ] **LATER — M6.6 Bias, drift, and regional robustness**
- [ ] **LATER — M6.7 Shadow-mode integration**
- [ ] **LATER — M6.8 Promotion decision ADR**

## M7 — Reusable GeoWeaver v1 platform

- [ ] **LATER — M7.1 Stable application/core contracts**
- [ ] **LATER — M7.2 Persistence decision and PostGIS ADR**
- [ ] **LATER — M7.3 Canonical persistent store**
- [ ] **LATER — M7.4 Versioned objective-profile/plugin interface**
- [ ] **LATER — M7.5 Public/stable application API**
- [ ] **LATER — M7.6 Operational security and privacy review**
- [ ] **LATER — M7.7 Reproducible deployment**
- [ ] **LATER — M7.8 Second application proof**
- [ ] **LATER — M7.9 v1 release audit**

## Completion log

Keep this deliberately short. Git history and PRs/issues are the detailed history.

| Date | Task | Evidence |
|---|---|---|
| 2026-09-07 | M0 foundation reconciled as implemented | Existing package, tests, CLI, scoring and docs reviewed during documentation reconciliation |
| 2026-09-07 | M1.1 Add a validated user-supplied recommendation-run input document | Implemented run_input loader/validator and tests in src/geoweaver/data/run_input.py |
| 2026-09-07 | M1.2 Wire explicit run inputs into `geoweaver rank` | Added --inputs option to CLI rank command, verified with automated unit and report tests |
| 2026-09-11 | M1.3 Implement a provenance/source registry contract | Implemented SourceRecord domain model, file-based registry loader/validator and audit helpers in src/geoweaver/data/sources.py with synthetic template coverage |
| 2026-09-11 | M1.4 Define and test the real-candidate curation workflow | Added data/catalogue/CURATION.md checklist, synthetic candidate + registry templates, and --sources provenance audit on validate-catalogue with tests |
| 2026-09-11 | M1.6 Make legal, closure, and health-advisory evidence operational | Documented source hierarchy and evaluation rules in docs/12_legal_advisory_evidence.md with regression tests for active/expired/future/unknown/contradictory evidence in tests/test_legal_advisory.py |

## When a task is completed

For a normal coding task, make the smallest update needed:

1. change its state here from NEXT to DONE;
2. choose the first task whose prerequisites are now satisfied and mark exactly that one NEXT;
3. update dependent entries from BLOCKED to READY only when their prerequisites are genuinely met;
4. add one row to the completion log with the date, task ID, and commit/PR/issue reference if
   available;
5. update `docs/09_status.md` if the project's capabilities or current blockers changed.

Do not mark an item DONE because code was drafted. Its tests and acceptance criteria must pass.
