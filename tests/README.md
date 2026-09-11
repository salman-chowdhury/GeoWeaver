# Tests

Current coverage by file (all fixtures are small, synthetic, and redistributable):

- `test_validation.py` — strict v0.1 GeoJSON catalogue contract (schema, coordinates,
  enums, integrity rules);
- `test_loader.py` — catalogue file loading;
- `test_run_input.py` — run-input JSON document loading and validation, including
  fail-closed invalid inputs and deterministic domain conversion;
- `test_sources.py` — provenance/source registry contract (required metadata, timestamps,
  blank/duplicate values, missing-reference auditing);
- `test_rank_sources.py` — `rank --sources` provenance audit (valid registry, missing
  catalogue reference, missing run-input reference, malformed/missing registry,
  deterministic ranking with validation);
- `test_curation.py` — real-candidate curation workflow (synthetic template, provenance
  resolution, `validate-catalogue --sources`, second-contributor revalidation);
- `test_legal_advisory.py` — legal/closure/health-advisory evidence (active, expired,
  future, unknown, and contradictory evidence; score never overrides a gate; reports name
  the evidence);
- `test_constraints.py` — deterministic hard-gate behaviour, including unknown/missing
  evidence failing closed;
- `test_scorer.py` — deterministic scoring, confidence/freshness handling, and ranking;
- `test_reports.py` — JSON and Markdown report contracts;
- `test_cli.py` — CLI behaviour for `validate-catalogue` and `rank`, including explicit
  `--inputs` runs and fail-closed invalid inputs;
- `conftest.py` — shared fixtures (demo catalogue path/document/segments).

Run the suite with `uv run pytest` (or `.venv/bin/python -m pytest` without `uv`).
