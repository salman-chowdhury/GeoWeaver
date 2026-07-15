# Scoring engine

## Objective

Rank eligible shoreline segments for a specific activity, user, time, and origin while preserving explainability and uncertainty.

## Processing order

1. Resolve user request and time window.
2. Retrieve candidate segments within the travel constraint.
3. Apply legal and safety hard gates.
4. Calculate stable spatial features.
5. Calculate time-dependent condition features.
6. Apply application-specific scoring weights.
7. calculate uncertainty and freshness penalties.
8. Return ranked results with explanations.

## Hard gates for CastNetGPT

A candidate is ineligible when any of the following is established:

- cast-netting is prohibited;
- the water is non-tidal where the method is not permitted;
- an active closure or relevant health advisory conflicts with the intended use;
- access requires trespass;
- severe weather or lightning risk exceeds the configured threshold;
- no safe casting footprint exists;
- the required travel time exceeds the user limit;
- daylight or safe lighting is insufficient for the user profile.

Unknown status is not equivalent to safe status. Critical unknowns should exclude or sharply reduce confidence.

## Baseline score

The MVP uses a 0–100 deterministic score:

```text
score =
  0.30 * habitat_opportunity
+ 0.20 * tide_match
+ 0.12 * wind_shelter
+ 0.12 * physical_access
+ 0.08 * privacy
+ 0.08 * family_suitability
+ 0.05 * travel_efficiency
+ 0.05 * evidence_quality
- risk_penalties
- uncertainty_penalties
```

Weights are provisional and must be versioned.

## Candidate feature groups

### Habitat opportunity

- drain or creek-mouth proximity;
- shallow gutter or edge availability;
- mangrove or structure adjacency;
- bank-accessible water depth;
- likely snags and retrieval hazards;
- estuarine connectivity.

### Tide match

- activity-specific preferred tide stage;
- time to tide turn;
- local range and rate of change;
- whether productive water remains within throwing range.

### Wind shelter

- forecast wind and gusts;
- shoreline orientation;
- terrain/vegetation shelter;
- crosswind penalty for novice users.

### Access and usability

- firm footing;
- clear casting radius;
- walk distance;
- parking reliability;
- boat, swimmer, and pedestrian conflicts.

### User fit

- skill level;
- family and child requirements;
- privacy preference;
- maximum drive time;
- intended catch and consumption preference.

## Confidence

Confidence is separate from score.

A high-scoring candidate with weak or stale data should display high potential but low confidence. Suggested bands:

- `high`: field verified and current authoritative conditions;
- `medium`: remotely verified with current conditions;
- `low`: incomplete access, morphology, or condition evidence.

## Output contract

Each result should include:

- score and confidence;
- eligibility status;
- recommended arrival and fishing window;
- strongest three positive factors;
- strongest three limitations;
- missing critical data;
- field-verification instructions;
- model and data timestamps.

## Integrity rules

- Do not present a score as catch probability until calibrated against sufficient observations.
- Do not fabricate expected catch counts.
- Do not silently mix tide predictions from distant stations.
- Do not infer safe consumption solely from the absence of a search result.
