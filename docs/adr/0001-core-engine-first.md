# ADR 0001: Core Engine First

## Status

Accepted for v0.1.

## Context

GeoWeaver needs to prove that canonical evidence, hard constraints, deterministic ranking, and
explanations form a useful workflow before introducing network or interface complexity.

## Decision

Implement the first vertical slice as an offline Python package with a console interface.
Domain, validation, constraint, scoring, and report modules remain independent of the CLI. Do
not add a web frontend, API, production database, authentication, or live adapters.

## Consequences

The core can be tested reproducibly and reused by later interfaces. Conditions, preferences,
origin, and manual travel estimates are fixed synthetic inputs for the demonstration, so v0.1
is not operational advice.
