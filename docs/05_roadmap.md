# Roadmap

## Weekend prototype — CastNetGPT v0.1

Goal: produce a repeatable ranked report that is useful for one real field trip.

### Deliverables

- 20 manually reviewed shoreline candidates across Ipswich, Brisbane, and Logan;
- one GeoJSON catalogue with stable IDs and basic access attributes;
- a field-observation CSV template;
- deterministic Python scoring function;
- command-line input for origin, drive limit, date/time, skill, privacy, and family requirements;
- ranked JSON and Markdown output;
- one documented field test and post-trip review.

### Explicit shortcuts

- manual travel-time entry or cached estimates;
- manual weather and tide inputs when an authoritative adapter is not ready;
- no authentication;
- no production database;
- no machine learning;
- no automated satellite classification.

## v0.2 — Live conditions

- weather and warning adapter;
- tide station mapping and predictions;
- sunset/daylight calculation;
- freshness tracking;
- cached condition snapshots.

## v0.3 — Interactive map

- map-based candidate browsing;
- score and confidence overlays;
- access/facility filters;
- field-observation form;
- mobile-friendly trip view.

## v0.4 — Terrain intelligence

- DEM/LiDAR ingestion;
- shoreline slope and bank-access features;
- tidal-flat morphology experiments;
- automated candidate rejection for steep or inaccessible banks.

## v0.5 — Imagery intelligence

- imagery-source governance;
- manual annotation set;
- segmentation of water, sand, mud, vegetation, and built access;
- candidate drain, gutter, and creek-mouth detection;
- human review workflow.

## v0.6 — Learning-to-rank

- observation-quality weighting;
- outcome normalisation by effort;
- temporal train/test splits;
- calibrated ranking model;
- comparison with the deterministic baseline;
- drift and regional-bias monitoring.

## v1.0 — Reusable spatial intelligence platform

- stable application API;
- PostGIS-backed canonical store;
- reproducible source pipelines;
- versioned objective profiles;
- auditable recommendations;
- plugin architecture for additional environmental applications.

## Release principle

A simpler model that is field-tested, transparent, and reproducible is preferable to a complex model that produces convincing but unverified recommendations.
