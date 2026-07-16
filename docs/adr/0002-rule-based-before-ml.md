# ADR 0002: Rule-Based Before Machine Learning

## Status

Accepted for v0.1.

## Context

There are not yet enough trustworthy field outcomes to train or evaluate a ranking model.
Opaque precision would conflict with the project's evidence and explanation principles.

## Decision

Use a deterministic, versioned rule profile with bounded components, explicit weights, and
plain-language explanations. Any change to scoring behavior requires a model-version change
and regression-test updates. Do not estimate catch probability or expected catch.

## Consequences

Every ranking is reproducible and auditable. Initial weights remain provisional and must later
be evaluated against recorded field outcomes before learning-to-rank work begins.

