# GeoWeaver

**GeoWeaver is an open-source spatial intelligence engine that fuses geospatial,
environmental, temporal, and observational data to reason about real-world locations.**

Its first application is **CastNetGPT**: an explainable decision-support experiment for
ranking shoreline candidates. The current v0.1 slice is completely offline.

> **Demo warning:** `data/catalogue/demo_segments.geojson` contains fictional synthetic
> records and coordinates only. Its output is not a real fishing recommendation and does not
> replace official weather, fisheries, access, health, navigation, or emergency advice.

## Vision

> Understand the world, not just map it.

GeoWeaver is designed as a reusable core rather than a fishing-specific application. The same spatial reasoning pipeline may later support flood analysis, property intelligence, kayaking, wildlife observation, environmental monitoring, and planetary or celestial mapping.

## Initial scope

The first study area covers:

- Ipswich
- Brisbane
- Logan

The first practical milestone is a usable weekend prototype that can rank a curated set of shoreline candidates for cast-net fishing.

## Working offline scoring foundation

The repository now provides a Python 3.12+ package that:

- validates the documented v0.1 GeoJSON contract;
- validates user-supplied trip, scoped-condition, and manual-travel JSON files;
- applies fail-closed activity, tidal, legal/advisory, access, weather, terrain/footing,
  casting-space, daylight, family, travel-time, freshness, and critical-information gates;
- ranks eligible demo segments with a deterministic, versioned rule set;
- reports score and evidence confidence separately; and
- emits explanation-first JSON and Markdown reports from a console command.

This foundation does **not** complete Issue #1 or the real-trip v0.1 vertical slice. It exercises
the contracts and deterministic rules with synthetic fixtures and now supports manually prepared
run files. The real-trip work still requires reviewed shoreline candidates, authoritative legal
and condition evidence, selected code/data licences, and a recorded field test.

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
geoweaver rank \
  --catalogue data/catalogue/demo_segments.geojson \
  --trip data/trips/demo_trip.json \
  --conditions data/conditions/demo_conditions.json \
  --travel data/travel/demo_travel.json \
  --format markdown
geoweaver demo --format json
```

`rank` requires all three run-input files and never substitutes favourable demonstration values.
An omitted travel estimate is reported as missing and fails that segment's travel gate. Missing,
unknown, or overlapping condition applicability is rejected because a location-specific snapshot
cannot safely be assigned by guesswork. `demo` is an explicit shortcut backed by packaged copies
of the committed fictional files, so it works independently of the current working directory.

## Input classes

The repository distinguishes three workflows:

- **Synthetic demonstration:** the committed files under `data/catalogue/`, `data/trips/`,
  `data/conditions/`, and `data/travel/` use fictional values and the `synthetic_demo`
  classification. They exist only for tests, examples, and regression checks.
- **Manually sourced real trip:** copy the documented JSON shapes, keep the files private unless
  deliberate review permits publication, use `manual_user_supplied`, and record real source and
  retrieval provenance. GeoWeaver validates and reports what was supplied but does not independently
  verify it. Inferred critical conditions fail their safety gates; legal, closure, health, and
  travel evidence must also be within the documented freshness limits.
- **Future live integrations:** weather, warning, tide, daylight, closure, and routing adapters
  remain future work. The current command performs no API calls, scraping, geocoding, or route
  calculation.

Format details and controlled values are documented in
[`data/trips/`](data/trips/README.md), [`data/conditions/`](data/conditions/README.md), and
[`data/travel/`](data/travel/README.md). Trip and retrieval timestamps must include timezones.

CLI exit codes are stable for automation: `0` means success, `2` means invalid usage or an
unreadable/invalid catalogue or run-input file, and `3` means validated inputs reached the ranking
stage but ranking could not be completed.

## Planned capabilities

- Shoreline segmentation and public-access modelling
- Weather, wind, rainfall, tide, and daylight integration
- Terrain and bank-slope analysis from DEM and LiDAR
- Aerial and satellite feature extraction
- Rule-based environmental scoring
- Field-observation logging and calibration
- Machine-learning ranking once sufficient outcome data exists

## Repository structure

```text
src/geoweaver/  Offline domain, validation, scoring, reports, and CLI package
docs/           Project vision, architecture, data, scoring, research notes, and ADRs
backend/        Reserved for later service-oriented boundaries
frontend/       Reserved for later application interfaces
data/           Schemas, small curated datasets, and data documentation
models/         Rule and learned-model documentation as the project evolves
scripts/        Data acquisition, transformation, and maintenance utilities
notebooks/      Exploration and geospatial research
tests/          Automated unit and CLI tests
```

## Current milestone

**Milestone 1 — User-supplied offline trip inputs**

The scorer can now reproduce a run entirely from catalogue, trip, condition, and travel files.
This is still not the real-trip vertical slice itself. The next milestone is authoritative source
research and deliberate curation. No demo record should be promoted into a real recommendation
without legal, safety, licence, provenance, and field review.

## Current limitations

- Committed conditions, preferences, origin, and travel estimates are fixed and synthetic; real
  values must be prepared manually outside the repository unless publication is deliberate.
- There are no live weather, tide, routing, closure, or advisory adapters.
- There is no frontend, API, authentication, database, scraping, terrain/imagery processing,
  machine learning, or production deployment.
- Scores express a transparent relative ranking, not catch probability or expected catch.
- Source licensing and the real catalogue governance process still require decisions.
- Tide-source location, distance, and assignment evidence are manually supplied and are not
  independently calculated or geographically verified.
- Interfaces and schemas may change before the first tagged release.
