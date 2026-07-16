# Manual travel-estimate files

`demo_travel.json` contains fictional estimates only. For a manual run, set
`data_classification` to `manual_user_supplied`, record the origin label exactly as it appears
in the trip request, and cite the manual or cached estimate source. GeoWeaver does not calculate
or refresh routes.

Each entry requires a known catalogue `segment_id`, a non-negative integer number of minutes,
a non-blank source reference, a timezone-aware retrieval timestamp that does not postdate the
trip target, and an evidence state of `verified` or `inferred`. Duplicate and unknown segment
IDs are rejected. A catalogue segment may be omitted only to represent missing travel data;
that segment then fails the travel hard gate and the report discloses the missing estimate.
Travel evidence older than 30 days at the target time is reported as stale and fails the travel
gate; GeoWeaver does not refresh it automatically.
