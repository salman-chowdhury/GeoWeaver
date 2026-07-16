# ADR 0004: Score and Confidence Are Separate

## Status

Accepted for v0.1.

## Context

A candidate can appear environmentally promising while relying on incomplete, stale, inferred,
or remotely reviewed evidence. Combining evidence strength with suitability would conceal that
distinction.

## Decision

Report a bounded recommendation score and a separately calculated confidence score and band.
Missing or weak evidence reduces confidence and is disclosed; it never receives a favourable
default. Failed hard gates force the recommendation score to zero and place the candidate after
all eligible records.

The report may expose an unweighted `data_quality` diagnostic, but evidence quality, source
count, verification state, inferred inputs, and freshness do not contribute to the suitability
score. The suitability score includes travel efficiency; confidence carries the evidence
assessment.

## Consequences

Users can distinguish relative suitability from trust in the supporting evidence. Confidence
rules require later calibration and must never be presented as catch probability.
