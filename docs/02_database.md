# Data model

## Design rules

- Use stable identifiers independent of display names.
- Store geometries in WGS 84 and record source CRS before transformation.
- Preserve provenance for every externally sourced or derived field.
- Keep time-varying conditions separate from stable location attributes.
- Represent uncertainty and verification state explicitly.
- Never commit private exact locations or personal trip data without deliberate review.

## Core entities

### `shoreline_segment`

A candidate section of shoreline, initially curated manually.

Key fields:

- `segment_id`
- `name`
- `region`
- `waterway`
- `geometry`
- `length_m`
- `shore_type`
- `bank_slope_class`
- `substrate`
- `orientation_deg`
- `tidal_status`
- `public_access_status`
- `verification_status`
- `source_refs`
- `updated_at`

### `access_point`

- `access_id`
- `segment_id`
- `access_type`
- `geometry`
- `parking_spaces_estimate`
- `walk_distance_m`
- `toilets`
- `playground`
- `lighting`
- `wheelchair_access`
- `notes`

### `environmental_feature`

Represents drains, creek mouths, mangrove edges, sand bars, gutters, culverts, bridges, pontoons, and other relevant structures.

- `feature_id`
- `feature_type`
- `geometry`
- `confidence`
- `detection_method`
- `source_ref`

### `restriction`

- `restriction_id`
- `restriction_type`
- `geometry`
- `effective_from`
- `effective_to`
- `authority`
- `source_url`
- `retrieved_at`
- `status`

### `condition_snapshot`

Time-specific conditions at or near a segment.

- `snapshot_id`
- `segment_id`
- `valid_at`
- `weather_station_id`
- `tide_station_id`
- `wind_speed_kph`
- `wind_direction_deg`
- `gust_kph`
- `rain_probability`
- `storm_warning`
- `tide_height_m`
- `tide_stage`
- `tide_rate_m_per_hr`
- `sunset_at`
- `data_freshness_minutes`

### `field_observation`

- `observation_id`
- `segment_id`
- `observed_at`
- `activity_type`
- `effort_count`
- `duration_minutes`
- `species`
- `catch_count`
- `catch_measure`
- `crowd_level`
- `water_clarity`
- `bait_activity`
- `footing_condition`
- `notes`
- `media_refs`

### `recommendation_run`

- `run_id`
- `application`
- `requested_at`
- `origin`
- `max_drive_minutes`
- `user_constraints`
- `model_version`
- `input_snapshot_refs`
- `ranked_results`

## Verification states

Use a controlled vocabulary:

- `unreviewed`
- `remote_reviewed`
- `field_verified`
- `temporarily_unavailable`
- `rejected`

## MVP storage

For the weekend prototype:

- shoreline geometry: GeoJSON;
- simple attributes: CSV or GeoJSON properties;
- field observations: CSV;
- recommendation output: JSON and Markdown.

Move to PostGIS only when spatial joins, history, concurrent updates, or dataset size justify it.
