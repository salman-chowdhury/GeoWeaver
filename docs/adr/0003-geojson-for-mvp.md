# ADR 0003: GeoJSON for the MVP

## Status

Accepted for v0.1.

## Context

The demonstration catalogue is small, file-based, and version controlled. PostGIS would add
setup and operational cost before the project needs concurrent writes or large spatial joins.

## Decision

Use a UTF-8 GeoJSON FeatureCollection with WGS 84 Point or LineString geometries and strictly
validated properties. Preserve stable IDs, provenance, verification, timestamps, and explicit
unknowns. Reject an invalid catalogue as a unit.

## Consequences

Fixtures are portable and reviewable in Git. GeoJSON is not the long-term analytical store;
move to PostGIS only when dataset size, history, concurrency, or spatial-query needs justify it.

