# GeoWeaver v0.1 GeoJSON Contract

The offline loader accepts a UTF-8 GeoJSON `FeatureCollection` containing at least one
`Feature`. Geometry must be a WGS 84 `Point` or `LineString`; coordinates are validated for
finite longitude/latitude bounds. Each feature represents one shoreline segment.

Required properties are:

- identity: `segment_id`, `name`, `region`, `waterway`;
- classification: `shoreline_type`, `substrate`, `bank_slope_class`;
- access: `public_access_status`, `casting_space_rating`, `parking` (`available`,
  `spaces_estimate`, `notes`), `toilets`, `family_suitability`, `privacy_rating`;
- environment: `mud_risk`, `snag_risk`, `boat_traffic_rating`, `wind_shelter_rating`,
  `habitat_features`, `preferred_tide_stages`;
- integrity: `verification_status`, `activity_permission_status`, matching
  `activity_permission_evidence`, `tidal_status`, `health_advisory_status`, matching
  `health_advisory_evidence`, `legal_status_known`, `legal_status_evidence`,
  `safety_information_complete`, `restrictions`, `restriction_review_evidence`, unique
  `source_refs`, and timezone-aware `last_updated`.

Ratings are integers from 0 (least/lowest) through 5 (most/highest). Nullable parking and
toilet fields represent unknown evidence and are never treated favourably. Legal and safety
unknowns must be stated explicitly and fail closed during ranking. IDs must be stable and
unique. Habitat features, tide stages, and source references must not contain duplicates.
Unsupported enums, invalid geometry, non-WGS-84 `crs` declarations, missing required fields,
and duplicate IDs make the entire catalogue invalid.

The v0.1 habitat vocabulary is `creek_mouth`, `drain_outfall`, `shallow_gutter`,
`mangrove_edge`, `sand_bar`, `built_structure`, and `estuarine_connection`. Unknown or
misspelled habitat tags are rejected rather than silently scoring zero. Restriction and health
evidence records include authority, source reference, retrieval time, verified or inferred state,
and nullable effective start/end timestamps. Legal-status, activity-permission, and
closure-review provenance each
include authority, source reference, retrieval time, and a verified or inferred state. Inferred,
future-dated, or more-than-180-day-old critical legal evidence fails closed; an empty restriction
array is only usable with a current verified closure-review record.

Travel time is deliberately not stored as a stable segment property. Each recommendation run
supplies sourced manual travel records from one explicit origin using the format documented in
`data/travel/`; missing or over-limit estimates fail closed.

`demo_segments.geojson` contains fictional synthetic fixtures only. Its coordinates, access
claims, restrictions, and environmental characteristics do not describe real places.
