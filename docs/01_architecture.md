# Architecture

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

## Core layers

### 1. Source adapters

Adapters retrieve or import weather, tide, terrain, imagery metadata, access, zoning, and field-observation data. Every record should retain source, retrieval time, licence notes, and spatial/temporal resolution.

### 2. Canonical data store

The canonical store represents locations, shoreline segments, access points, environmental features, condition snapshots, restrictions, observations, and recommendation runs.

The likely long-term database is PostgreSQL with PostGIS. The weekend prototype may use version-controlled GeoJSON and CSV files to minimise setup cost.

### 3. Feature engine

The feature engine derives application-neutral variables such as:

- shoreline slope and orientation;
- distance to drains, creek mouths, mangroves, parking, and toilets;
- tide stage and rate of change;
- wind exposure relative to shoreline orientation;
- daylight remaining;
- data freshness and coverage.

### 4. Constraint engine

Constraints exclude or penalise locations based on legal closure, unsafe access, severe weather, darkness, excessive mud or slope, and user-specific requirements.

### 5. Scoring engine

Each application provides an objective profile. CastNetGPT weights habitat opportunity, condition match, access, privacy, family suitability, and risk.

### 6. Explanation layer

Every recommendation returns:

- final score;
- confidence band;
- hard-gate results;
- top positive factors;
- top negative factors;
- missing data;
- best time window;
- source timestamps.

### 7. Interfaces

Initial interface order:

1. command-line report;
2. lightweight web interface;
3. interactive map;
4. field-observation form;
5. API for additional applications.

## Weekend MVP

```text
GeoJSON/CSV spot catalogue
          +
manual condition inputs
          |
Python scoring module
          |
ranked Markdown/JSON report
```

The first prototype should not depend on a complex frontend or production database.

## Proposed boundaries

```text
backend/domain/       entities and scoring contracts
backend/services/     recommendation orchestration
backend/adapters/     external-source adapters
models/rules/         versioned rule sets
frontend/             map and report UI
data/catalogue/       small curated public dataset
```

## Decisions still required

- Python package and dependency manager;
- GeoJSON/Parquet versus early PostGIS adoption;
- routing provider and cache policy;
- permitted imagery sources for automated processing;
- tide prediction source and station-assignment method;
- licensing strategy for code and derived datasets.
