# Initial backlog

## Ready

- [ ] Confirm the v0.1 architecture and package layout.
- [ ] Select code and data licences.
- [ ] Define the shoreline GeoJSON schema.
- [ ] Curate the first 20 candidate segments.
- [ ] Verify cast-net legal constraints and source provenance.
- [ ] Implement the deterministic scorer.
- [ ] Add a CLI that emits JSON and Markdown.
- [ ] Complete the first field observation.

## Implemented foundations

- [x] Validate a typed file-based trip request with timezone-aware target time and practical
  constraints.
- [x] Validate manually supplied, provenance-bearing condition snapshots with explicit segment,
  waterway, or named segment-group applicability.
- [x] Validate sourced manual travel estimates against catalogue segment IDs and trip origin.
- [x] Rank from explicit catalogue, trip, condition, and travel files without favourable demo
  fallback.
- [x] Preserve an explicitly named synthetic demo workflow and report trip/condition/travel
  provenance in JSON and Markdown.
- [x] Fail inferred critical conditions closed and require current legal, closure, health, tide
  applicability, and travel provenance.

## Later

- [ ] Automate weather and warnings.
- [ ] Implement automatic tide-station assignment; v0.1 accepts only explicit manual assignment
  provenance.
- [ ] Add route-time estimation.
- [ ] Evaluate LiDAR and DEM coverage.
- [ ] Design imagery annotation classes.
- [ ] Build the interactive map.
- [ ] Add additional objective profiles.

## Definition of done for v0.1

A user can provide a time window and practical constraints, receive a reproducible ranked shortlist with explanations, visit a recommended site, and record the outcome in the repository's observation format.

## Current implementation status

The repository currently contains an offline scoring foundation using fictional synthetic
fixtures plus a validated file-based workflow for manually prepared trip, condition, and travel
inputs. It does not yet satisfy the definition of done above or complete Issue #1. Twenty reviewed
candidates, authoritative real-trip provenance, licence decisions, and a documented field
observation remain open work. Live source and routing integrations remain later milestones.
