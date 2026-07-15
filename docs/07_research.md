# Research programme

## Core research question

Can heterogeneous spatial and temporal evidence produce useful, explainable recommendations at locations where direct outcome data is sparse?

## Initial CastNetGPT questions

1. Which remotely observable shoreline features best predict accessible bait-funnelling opportunities?
2. Can DEM or LiDAR-derived morphology identify drains, gutters, bars, and safe bank gradients?
3. How accurately can a local tide stage be estimated when the nearest published station is distant or hydraulically separated?
4. How should wind direction interact with shoreline orientation and user skill?
5. Which access variables determine whether a theoretically productive site is practically usable?
6. How much does field verification improve ranking quality over remote-only analysis?
7. Can outcome data be normalised for throw count, duration, skill, season, and target species?
8. How should the system disclose uncertainty without making the recommendation unusably vague?

## Evaluation framework

### Baselines

- nearest accessible tidal location;
- local popularity-based recommendation;
- deterministic ecological rule set;
- random eligible candidate.

### Metrics

- selected-location utility rating;
- safe and legal access success;
- time spent fishing versus travelling/scouting;
- catch per unit effort, where appropriate;
- recommendation regret versus other inspected candidates;
- explanation usefulness;
- calibration of confidence bands.

### Experimental discipline

- preserve model version and input snapshot for every recommendation;
- record unsuccessful trips;
- avoid training and evaluating on duplicated visits without temporal separation;
- distinguish user skill improvement from location-model improvement;
- report regional coverage and bias;
- document changes to scoring weights before examining held-out outcomes.

## Data ethics

- avoid publishing sensitive ecological or culturally restricted locations;
- avoid encouraging access through private land;
- respect imagery and dataset licences;
- minimise personal-location retention;
- provide a mechanism to suppress locations at risk of overcrowding or habitat damage.

## First experiment

Create 20 candidate shoreline segments, score them using the v0.1 rules, inspect the top three remotely, visit one, and record both environmental observations and usability outcomes. Use the result to revise data fields before expanding the catalogue.
