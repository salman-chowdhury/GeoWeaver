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

For the offline v0.1 rule profile, weather eligibility requires sourced and verified warning,
lightning/thunderstorm, sustained-wind, and gust inputs. Sustained wind above 40 km/h or gusts
above 60 km/h fail the weather gate. Missing values fail closed. These conservative thresholds
are explicit rule constants and must be reviewed before any operational use. Condition snapshots
also declare the segment IDs to which their location-specific footing, tide, and daylight
evidence applies.

A casting-space rating of 0/5 always fails the absolute casting-footprint gate. User preferences
may require a higher rating but cannot reduce that safety minimum.

## Baseline score

The MVP uses a 0–100 deterministic score:

```text
score =
  0.30 * habitat_opportunity
+ 0.32 * environmental_condition_match
+ 0.12 * access_and_usability
+ 0.08 * privacy
+ 0.08 * family_suitability
+ 0.05 * safety_and_risk
+ 0.05 * travel_efficiency
```

`environmental_condition_match` is 65% tide match and 35% wind match. Travel efficiency falls
linearly from 100 at zero minutes to 0 at the configured maximum; travel beyond the maximum
still fails the hard gate. Weights are provisional and must be versioned.

Evidence quality is reported as an unweighted diagnostic component. Verification state, source
coverage, inference, missing data, and freshness affect confidence only; they do not change the
suitability score.

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
