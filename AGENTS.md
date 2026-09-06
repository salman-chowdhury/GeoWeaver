# Repository guidelines for human and AI contributors

GeoWeaver is an evolving spatial-intelligence project with an implemented offline Python
foundation. These instructions exist so a contributor starting with zero prior context can make
small, safe, reproducible changes without rebuilding completed work or jumping ahead in the
roadmap.

## Mandatory read order

Before changing code or data, read these files in order:

1. `README.md` — project purpose, installation, current public-facing capabilities and limits.
2. `docs/09_status.md` — authoritative snapshot of what is implemented **now**.
3. `docs/11_progress.md` — authoritative task state and the single task marked **NEXT**.
4. `docs/10_implementation_plan.md` — exact contract for that task and later milestones.
5. `docs/01_architecture.md` — current architecture and stable boundaries.
6. Only then read the domain-specific design files referenced by the current task, such as
   `docs/02_database.md`, `docs/03_data_sources.md`, or `docs/04_scoring_engine.md`.
7. Inspect the existing implementation and tests relevant to the task before writing anything.

Do not begin from `docs/05_roadmap.md`, `docs/08_backlog.md`, or an old GitHub issue checklist.
Those may explain direction or history, but they are not the authoritative current task state.

## Source-of-truth precedence

When documentation appears to disagree, use this order:

1. executable code and passing tests for **current behaviour**;
2. `docs/09_status.md` for **current capability/blocker state**;
3. `docs/11_progress.md` for **what should be worked on next**;
4. `docs/10_implementation_plan.md` for **intended implementation sequence and acceptance criteria**;
5. architecture/ADR/domain documents for **design intent and constraints**;
6. roadmap/issues for **broad direction and historical planning**.

If code/tests contradict an intended contract, do not silently choose one. Identify the mismatch,
fix it within the current task if clearly in scope, or document/block it for owner review.

## Current repository structure

The implemented Python package lives under `src/geoweaver/`:

```text
src/geoweaver/
├── cli.py          console interface
├── demo.py         fictional deterministic demonstration inputs
├── data/           catalogue/run-data loading and validation
├── domain/         immutable domain models and enums
├── reports/        JSON and Markdown rendering
└── scoring/        hard constraints, explanations, confidence and deterministic ranking
```

Other important locations:

```text
data/               small redistributable schemas/templates/catalogues only
docs/               status, implementation plan, architecture, source/scoring research and ADRs
tests/              automated unit/CLI/regression tests
scripts/            reproducible acquisition/transformation/maintenance utilities when needed
notebooks/          exploration only; production logic must move into tested modules
backend/            reserved; do not move the existing core here merely to match historical docs
frontend/           reserved until the interactive-interface milestone
models/             model/rule documentation or artefacts when justified by later milestones
```

Do not create duplicate `backend/domain` or `backend/services` implementations of code that
already belongs to `src/geoweaver/`.

## Current tooling

GeoWeaver uses:

- Python 3.12+;
- `pyproject.toml` with setuptools;
- `uv` as the preferred environment/dependency workflow;
- pytest;
- Ruff;
- the `geoweaver` console entry point.

Install and establish a baseline before coding:

```sh
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

If `uv` is unavailable, follow the virtual-environment fallback in `README.md`.

## Incremental working rule

Work on the **single task marked NEXT** in `docs/11_progress.md`.

Before implementation:

1. read that task in `docs/10_implementation_plan.md`;
2. confirm its prerequisites are satisfied;
3. inspect every existing file/test named by the task;
4. search for equivalent functionality so it is not reimplemented under a new name;
5. run the relevant baseline tests where practical.

During implementation:

- keep the change limited to the current task;
- prefer extending existing domain models and package boundaries over creating parallel concepts;
- add or update tests with the behaviour change;
- keep external/network/provider behaviour behind adapters and outside the scoring core;
- do not opportunistically start later roadmap tasks;
- do not make owner/governance decisions that the plan marks as requiring approval.

After implementation:

1. run targeted tests;
2. run the full repository checks:

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

3. verify the current task's acceptance criteria explicitly;
4. update `docs/11_progress.md` from NEXT to DONE only if the criteria and checks pass;
5. promote exactly one eligible following task to NEXT;
6. update `docs/09_status.md` when capabilities, current milestone, or blockers changed;
7. update README/domain docs/ADRs only when the task materially changes their public contract or
   design decision.

Never mark work complete merely because code was written.

## Architecture invariants

Unless a deliberate ADR changes them:

- the current core remains a Python package under `src/geoweaver/`;
- v0.1 stays file-based and offline-capable rather than requiring a production database;
- scoring is deterministic and versioned;
- identical explicit inputs and rule versions should produce identical rankings;
- live data must be converted to an explicit timestamped snapshot before scoring;
- hard eligibility constraints remain separate from soft scoring;
- score and evidence confidence remain separate;
- the deterministic scorer remains the baseline when ML is introduced later;
- provider/network code must not be embedded inside domain or scoring modules;
- frontend code must not become the source of truth for recommendation rules.

## Safety, legality, and uncertainty

GeoWeaver can influence real-world location decisions. Fail closed on critical uncertainty.

- Unknown legal permission is not permission.
- Unknown public access is not public access.
- Missing critical health/advisory evidence is not evidence of safety.
- Missing/unknown severe-weather, lightning, footing, tide, or daylight evidence must not be
  silently treated favourably.
- A failed hard gate cannot be overridden by a high suitability score.
- Do not describe a score as catch probability or fabricate expected catches.
- Do not silently use a distant tide station or unsupported geographic proxy.
- Demonstration fixtures must remain unmistakably fictional and must not be promoted into real
  recommendations.

## Data, privacy, licensing, and provenance

Never commit:

- credentials, API keys or secrets;
- private trip history or personal location traces;
- sensitive exact locations without deliberate review;
- restricted/licence-incompatible imagery or datasets;
- bulk rasters/LiDAR, generated caches, or large model weights.

For external data, retain appropriate publisher, source identifier/URL, licence/terms,
retrieval/publication timestamps, CRS/resolution where relevant, transformations, and known
limitations. Use the source-quality/provenance rules in `docs/03_data_sources.md`.

Provider choice, code licence, and data-redistribution policy may require owner approval. An agent
may research and prepare an ADR, but must not invent approval.

## Coding conventions

- four-space Python indentation;
- `snake_case` for modules/functions/fields;
- `PascalCase` for classes;
- `UPPER_CASE` for constants;
- stable identifiers such as `segment_id` must remain independent of display names;
- keep transformations/scoring in tested modules, not notebooks;
- prefer immutable/validated domain values consistent with the existing models;
- preserve deterministic ordering where it affects reproducible reports or tests.

Use Ruff rather than introducing a competing formatter/linter without an ADR-level reason.

## Testing expectations

Use pytest and keep fixtures small, synthetic, and redistributable. Prioritise tests for:

- schema and coordinate validation;
- domain validation and controlled enums;
- deterministic ranking;
- hard-gate behaviour;
- unknown/missing evidence;
- confidence/freshness handling;
- provenance/reference integrity;
- adapter fixtures rather than live-network tests;
- temporal/spatial boundary cases;
- report/CLI contracts.

Regression tests should pin rule/model versions and explicit snapshots where reproducibility
matters.

## Commits and pull requests

Use short imperative commit summaries and keep commits focused. A PR should explain the problem,
change, evidence/datasets, reproduction/validation steps, issue/task reference, and any safety,
legal, privacy, provenance, or licensing impact. Include screenshots for visible interface changes.

The task ID from `docs/10_implementation_plan.md` should appear in the PR/issue/commit context when
practical so progress remains traceable.
