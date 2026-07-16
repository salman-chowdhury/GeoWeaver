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
- integrity: `verification_status`, `activity_permission_status`, `tidal_status`,
  `health_advisory_status`, matching `health_advisory_evidence`, `legal_status_known`,
  `safety_information_complete`, `restrictions`, unique `source_refs`, and timezone-aware
  `last_updated`.

Ratings are integers from 0 (least/lowest) through 5 (most/highest). Nullable parking and
toilet fields represent unknown evidence and are never treated favourably. Legal and safety
unknowns must be stated explicitly and fail closed during ranking. IDs must be stable and
unique. Habitat features, tide stages, and source references must not contain duplicates.
Unsupported enums, invalid geometry, non-WGS-84 `crs` declarations, missing required fields,
and duplicate IDs make the entire catalogue invalid.

The v0.1 habitat vocabulary is `creek_mouth`, `drain_outfall`, `shallow_gutter`,
`mangrove_edge`, `sand_bar`, `built_structure`, and `estuarine_connection`. Unknown or
misspelled habitat tags are rejected rather than silently scoring zero. Restriction and health
evidence records include authority, source reference, retrieval time, and nullable effective
start/end timestamps.

Travel time is deliberately not stored as a stable segment property. Each recommendation run
supplies sourced manual `TravelEstimate` records from one explicit origin; missing or over-limit
estimates fail closed.

`demo_segments.geojson` contains fictional synthetic fixtures only. Its coordinates, access
claims, restrictions, and environmental characteristics do not describe real places.
