# Trip request files

`demo_trip.json` is a fictional, synthetic request used by tests and CLI examples. Copy its
shape for a manual run, replace every value deliberately, and set `data_classification` to
`manual_user_supplied`. Do not commit personal trip history or sensitive locations.

The v0.1 schema requires a timezone-aware `target_datetime`, an optional non-empty `run_id`, a
non-empty origin label, controlled skill and activity values, ratings from 0 to 5, travel and
daylight limits from 0 to 1440 minutes, the family requirement, and optional notes. If `run_id`
is omitted, GeoWeaver derives one deterministically from the catalogue, trip, conditions,
travel estimates, and model version.

Currently supported controlled values are:

- `data_classification`: `synthetic_demo`, `manual_user_supplied`
- `skill_level`: `novice`, `intermediate`, `experienced`
- `intended_activity`: `cast_net_fishing`

The origin label is descriptive only. GeoWeaver does not geocode it or calculate routes.
