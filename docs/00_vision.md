# Vision

## Mission

GeoWeaver turns heterogeneous spatial evidence into transparent, practical location recommendations.

It should answer not only **where something is**, but also:

- what the environment is likely to be like at a particular time;
- whether a person can legally and safely access it;
- why one location ranks above another;
- how confident the system should be;
- what evidence would change the recommendation.

## First application: CastNetGPT

CastNetGPT will rank publicly accessible shoreline locations for recreational cast-net fishing. The initial study area is Ipswich, Brisbane, and Logan, Queensland.

The application is a useful test bed because recommendations require several interacting systems:

- shoreline geometry and terrain;
- tidal timing and water movement;
- weather and daylight;
- habitat and likely bait-funnelling features;
- public access, parking, facilities, and travel time;
- legal restrictions and health advisories;
- privacy, family suitability, and user skill;
- uncertain and sparse field outcomes.

## Product principles

1. **Evidence before confidence.** Never convert weak evidence into precise-looking probabilities.
2. **Safety and legality are hard gates.** A productive but prohibited or unsafe location must not rank.
3. **Explain every recommendation.** Scores must expose their strongest positive and negative factors.
4. **Separate observed, derived, and inferred data.** Users should know what was measured, calculated, or estimated.
5. **Design for uncertainty.** Missing tide, access, or terrain data should lower confidence rather than silently default to favourable values.
6. **Respect access and ecosystems.** Do not encourage trespass, habitat damage, overcrowding, or disclosure of sensitive ecological locations.
7. **Start physics-informed.** Use transparent environmental rules before machine learning.
8. **Learn from field results.** User observations should calibrate the model without erasing prior ecological knowledge.

## MVP success criteria

The first usable version should:

- store at least 20 manually verified shoreline candidates;
- filter candidates by drive-time limit and hard safety/legal constraints;
- rank candidates using a deterministic scoring model;
- show the recommendation window and supporting reasons;
- record a field trip and catch outcome;
- produce the same result from the same inputs;
- clearly label missing or stale data.

## Non-goals for the first release

- guaranteed catch predictions;
- autonomous scraping of restricted mapping platforms;
- high-resolution computer vision over the entire region;
- live hydrodynamic simulation;
- publishing exact sensitive ecological locations;
- replacing official weather, fisheries, navigation, or emergency advice.
