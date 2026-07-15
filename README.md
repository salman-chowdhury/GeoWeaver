# GeoWeaver

**GeoWeaver is an open-source spatial intelligence engine that fuses geospatial, environmental, temporal, and observational data to reason about real-world locations.**

Its first application is **CastNetGPT**: a decision-support tool that ranks publicly accessible shoreline locations using tides, weather, terrain, access, safety, and field observations.

## Vision

> Understand the world, not just map it.

GeoWeaver is designed as a reusable core rather than a fishing-specific application. The same spatial reasoning pipeline may later support flood analysis, property intelligence, kayaking, wildlife observation, environmental monitoring, and planetary or celestial mapping.

## Initial scope

The first study area covers:

- Ipswich
- Brisbane
- Logan

The first practical milestone is a usable weekend prototype that can rank a curated set of shoreline candidates for cast-net fishing.

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
docs/       Project vision, architecture, data, scoring, and research notes
backend/    APIs, domain services, ingestion, and ranking logic
frontend/   Interactive map and application interfaces
data/       Schemas, small curated datasets, and data documentation
models/     Rule-based and learned models
scripts/    Data acquisition, transformation, and maintenance utilities
notebooks/  Exploration and geospatial research
tests/      Automated tests and validation fixtures
```

## Current milestone

**Milestone 0 — Foundation**

1. Define the architecture and data contracts.
2. Catalogue authoritative public data sources.
3. Create a small, manually verified shoreline dataset.
4. Implement a transparent scoring baseline.
5. Produce CastNetGPT v0.1 for field testing.

## Project status

Early research and design. Interfaces and schemas may change rapidly before the first tagged release.
