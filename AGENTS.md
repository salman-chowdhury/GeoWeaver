# Repository Guidelines

## Project Structure & Module Organization

GeoWeaver is in its research and design phase. Project decisions live in `docs/`; begin with `docs/01_architecture.md` and `docs/05_roadmap.md`. Planned Python domain logic and adapters belong under `backend/`. Interface work belongs in `frontend/`, versioned scoring rules in `models/`, and reproducible utilities in `scripts/`. Keep exploration in `notebooks/`, automated checks and fixtures in `tests/`, and only small, redistributable datasets or schemas in `data/`. The field-observation schema starts at `data/templates/field_observation.csv`.

## Build, Test, and Development Commands

No package manifest, dependency manager, or build pipeline is configured yet. For documentation-only changes, run:

```sh
git diff --check
git status --short
```

The first implementation is expected to be a small Python package. Document environment setup in `README.md`, place tool configuration in `pyproject.toml`, and make `python -m pytest` the repository-wide test command. Do not introduce a frontend framework or database solely for scaffolding; v0.1 is a CLI producing ranked JSON and Markdown from GeoJSON/CSV inputs.

## Coding Style & Naming Conventions

Use four-space indentation and standard Python naming: `snake_case` for modules, functions, and fields; `PascalCase` for classes; and `UPPER_CASE` for constants. Match canonical fields such as `segment_id` and `source_refs`; identifiers must be independent of display names. Keep production transformations and scoring in tested modules rather than notebooks. No formatter or linter is configured; document one before enforcing it in CI.

## Testing Guidelines

Use pytest for planned Python tests, named `tests/test_<area>.py`, with fixtures kept small and redistributable. Prioritize schema and coordinate validation, deterministic scoring, hard gates, missing-data penalties, adapter fixtures, and temporal/spatial edge cases. Regression tests should pin model versions and input snapshots so recommendation runs remain reproducible.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Add project foundation and design blueprints`; follow that style and keep each commit focused. Pull requests must complete the repository template: explain the problem and change, cite evidence or datasets, list reproduction steps, link issues, and describe validation. Review data provenance plus safety, legal, ethical, and licensing impacts where relevant. Include screenshots for visible interface changes.

## Data, Security & Provenance

Never commit credentials, private trip history, exact sensitive locations, restricted imagery, bulk rasters/LiDAR, generated caches, or large model weights. Record publisher, licence, source URL, retrieval time, CRS, resolution, transformations, and limitations for imported data. Treat unknown legal or safety status as unknown—not safe.
