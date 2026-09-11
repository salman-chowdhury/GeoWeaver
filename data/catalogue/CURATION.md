# Real-candidate curation workflow (M1.4)

> **Status:** workflow definition. Do **not** commit real redistributable shoreline
> records until owner decision **D1** (code licence + data-licensing strategy) is
> resolved. Keep genuine research in private local files outside Git until then.
> All identifiers, coordinates, and sources in the `curated-example-*` templates are
> synthetic and unmistakably fictional.

## Purpose

Define a repeatable process so a second contributor can curate one real shoreline
candidate that passes catalogue validation with traceable provenance — without
confusing **remote review** with **field verification**.

Read first:

1. `data/catalogue/README.md` — the v0.1 GeoJSON contract (required fields, ratings,
   enums, integrity rules);
2. `docs/02_database.md` — stable IDs, WGS 84, provenance, verification states;
3. `docs/03_data_sources.md` — source tiers (A–D) and provenance contract;
4. `docs/04_scoring_engine.md` — hard gates and fail-closed unknowns.

## Step-by-step checklist

1. **Pick one candidate** in the Ipswich / Brisbane / Logan study area from a
   Tier A–C source (government open data, council park page, recognised open
   dataset, or your own lawful mapping observation). Tier D (unverified social /
   forum claims) may only nominate a site for inspection — never establish access,
   legality, or safety.
2. **Assign a stable `segment_id`** (lowercase slug, e.g. `brisbane-nudgee-drain-01`).
   Never reuse an ID, never rename an ID to change its meaning. Display `name` may
   change; `segment_id` must not.
3. **Capture geometry in WGS 84** (`Point` or `LineString`, longitude/latitude).
   Record the source CRS before any transformation. Do not commit bulk rasters,
   LiDAR, or restricted imagery.
4. **Fill every required property** per the evidence table below. Every material
   claim needs a Tier A–C provenance entry (Step 6). What you cannot verify stays
   explicitly **unknown** (see unknowns rules).
5. **Set `verification_status`** per the verification-state rules. Remote research
   alone is `remote_reviewed` at best — never `field_verified`.
6. **Register every source** in a file-based source registry
   (`src/geoweaver/data/sources.py`, M1.3 contract): stable `source_id`,
   publisher, title, URL/catalogue identifier, licence/terms, `retrieved_at`, plus
   publication timestamp, CRS/resolution, transformation, and limitations where
   relevant. Every `source_refs` entry and every restriction/health `source_ref`
   in the candidate must resolve in that registry.
7. **Validate structurally:**
   `geoweaver validate-catalogue --catalogue <candidate.geojson>`
8. **Validate provenance:**
   `geoweaver validate-catalogue --catalogue <candidate.geojson> --sources <registry.json>`
   Both commands must exit 0. A missing-reference failure lists the unregistered
   IDs — register them or remove the claim, never invent a source.
9. **Submit for review** with the registry entries, retrieval timestamps, and a
   note stating what is still unknown and what would change the assessment.

## Required evidence table

| Evidence | Catalogue field(s) | What to record | Unknown handling |
|---|---|---|---|
| Access | `public_access_status` | `verified_public` only with Tier A–C proof of public access; else `restricted` / `prohibited` / `unknown` | `unknown` fails closed at ranking |
| Legality | `activity_permission_status`, `legal_status_known`, `restrictions[]` | Explicit permission state; each restriction has authority, `source_ref`, `retrieved_at`, effective window | `legal_status_known: false` or permission `unknown` fails closed |
| Tidal status | `tidal_status` | `tidal` / `non_tidal` with source; inland reaches need station/offset rationale (M1.7) | `unknown` fails closed |
| Casting space | `casting_space_rating` (0–5) | Clear casting footprint for the intended method | `0` always fails the footprint gate; never lower the safety minimum via preferences |
| Health / advisory | `health_advisory_status` + `health_advisory_evidence` | Status must match evidence status; authority, `source_ref`, `retrieved_at` required | `unknown` fails closed; absence of a search result is not safety |
| Facilities | `parking{available, spaces_estimate, notes}`, `toilets` | What exists per source; estimates only with a stated basis | `null` = unknown, never favourable |
| Substrate / footing | `substrate`, `bank_slope_class`, `mud_risk`, `snag_risk` | Observed or Tier A–C classification | `unknown` substrate/slope lowers confidence; never assume firm footing |
| Privacy / family | `privacy_rating`, `family_suitability` (0–5) | Best judgement with basis noted; keep conservative | Unknown → mid/low rating with limitation noted, never optimistic |
| Environment | `habitat_features[]`, `preferred_tide_stages[]`, `wind_shelter_rating`, `boat_traffic_rating` | Only tags in the v0.1 vocabulary; misspellings are rejected | Omit unobserved tags rather than guessing |
| Freshness | `last_updated` (timezone-aware) | Time the record was last reviewed against sources | Stale records lose confidence; recheck before any trip |

## Verification-state rules

| State | Meaning | Promotion rule |
|---|---|---|
| `unreviewed` | Draft proposal, not yet checked | Starting state for new proposals |
| `remote_reviewed` | Checked against maps/imagery/pages by a second pair of eyes | Requires Tier A–C remote evidence + registry entries; **ceiling for desk research** |
| `field_verified` | Lawfully visited in person; access, footing, casting space, facilities confirmed on the ground | Requires an in-person visit. Imagery, maps, or web research alone **never** qualify |
| `temporarily_unavailable` | Known closure/works/advisory | Link the active restriction/advisory evidence |
| `rejected` | Unsuitable or unverifiable | Keep the record with reason rather than silently deleting history |

## Unknowns rules (fail closed)

- Unknown legal permission is not permission. Unknown public access is not public access.
- Missing critical health/advisory evidence is not evidence of safety.
- Missing severe-weather, lightning, footing, tide, or daylight evidence must not be
  treated favourably at run time (see `docs/04_scoring_engine.md`).
- In the catalogue, state unknowns explicitly: `unknown` enums,
  `legal_status_known: false`, `safety_information_complete: false`, `null` parking /
  toilets, `unknown` restriction/health status with a matching evidence record.
- A failed hard gate cannot be overridden by a high suitability score, and scores
  are relative rankings — never catch probability.

## Worked synthetic example

`data/templates/curated_candidate.template.geojson` holds one `remote_reviewed`
synthetic candidate (`curated-example-001`) with deliberately unknown parking /
toilet evidence (`null`). `data/templates/curation_registry.template.json` holds
its four provenance records. Neither file describes a real place.

```sh
uv run geoweaver validate-catalogue \
  --catalogue data/templates/curated_candidate.template.geojson
uv run geoweaver validate-catalogue \
  --catalogue data/templates/curated_candidate.template.geojson \
  --sources data/templates/curation_registry.template.json
```

To simulate a second contributor: copy the candidate file, change `segment_id` and
`name` to a new stable ID, adjust the evidence, add your registry entries, and
re-run both commands. Structural errors exit 2; unregistered source references
exit 2 with the missing IDs listed; unreadable/invalid registry files exit 3.

## Non-goals

- No real 20-candidate catalogue (M1.5, needs D1).
- No field-verification claims from desk research.
- No live adapters, routing, tide stations, terrain, imagery, ML, API, or frontend.
- No exact sensitive ecological locations or private trip data in Git.
