# Data

This directory is for schemas, small curated open datasets, fixtures, and documentation.

Do not commit:

- restricted or non-redistributable imagery;
- bulk raw LiDAR or raster downloads;
- API credentials;
- private trip history or exact sensitive locations;
- generated caches and large intermediate files.

Large reproducible inputs should be acquired by scripts and documented with checksums and provenance.

Committed run examples are intentionally synthetic:

- `catalogue/` contains the fictional shoreline catalogue and its contract;
- `trips/` documents user constraints and the target time;
- `conditions/` documents explicit spatial applicability and time-varying evidence; and
- `travel/` documents manual per-segment travel estimates.

Copy the schemas for private manual work, use `manual_user_supplied`, and do not commit the result
without deliberate privacy, provenance, licensing, legal, and safety review. Live integrations are
not implemented.
