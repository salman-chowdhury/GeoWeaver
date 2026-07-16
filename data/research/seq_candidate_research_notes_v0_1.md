# SEQ CastNetGPT candidate desk review — Logan batch 1

**Review timestamp:** `2026-07-16T16:41:28+10:00`  
**Scope:** 10 official Logan City Council fishing locations on the Logan and Albert Rivers.

## What was completed

- Discovered and recorded ten council-recognised fishing locations.
- Extracted the coordinates embedded in each official council park page.
- Verified public fishing access and listed facilities from Logan City Council pages.
- Applied the current Queensland cast-net equipment rules.
- Reviewed Queensland closed-water guidance.
- Created conservative remote classifications and ratings.
- Produced a GeoWeaver v0.1 GeoJSON catalogue with stable IDs and provenance.
- Ran a structural validation mirroring the current GeoWeaver contract.

## Evidence treatment

**Verified facts** are limited to directly supportable items such as council-listed fishing access,
pontoons, ramps, toilets, carparks, playgrounds and waterfront facilities, plus current Queensland
gear rules.

**Remote inferences** include substrate, bank slope, casting space, mud risk, snag risk, boat
traffic, shelter, privacy and some family-suitability ratings. These are deliberately conservative
and must be confirmed before promoting a record to `field_verified`.

A public aerial/oblique image was available for Riedel Park and supports the presence of a broad
platform, boardwalk, carpark connection, tidal-zone rock works, saltmarsh and mangrove habitat.
Comprehensive current satellite inspection was not available through the connected browser in this
session, so the other sites remain based on official maps/pages rather than claimed satellite
verification.

## Critical unresolved blocker

Every feature deliberately has:

```text
health_advisory_status = unknown
```

A precautionary seafood-consumption warning affected tidal reaches of the Logan and Albert Rivers
in 2024. Searches did not locate a current authoritative lifting notice. This does **not** prove the
warning is active; it means the current state is unresolved. GeoWeaver should therefore fail closed
until current official advice and onsite signage are checked.

The catalogue also leaves `safety_information_complete = false` for the four less-documented
riverbank/boat-ramp locations.

## Field-check order

This is a **verification priority**, not a fishing recommendation.

| Priority | Segment | Candidate | Remote casting space | Family rating | Current blockers |
|---:|---|---|---:|---:|---|
| 1 | `logan-alexander-clark-park` | Alexander Clark Park river pontoons | 3/5 | 5/5 | current health-advisory status unresolved |
| 1 | `logan-logan-river-parklands` | Logan River Parklands fishing pontoon | 3/5 | 5/5 | current health-advisory status unresolved |
| 1 | `logan-riedel-park` | Riedel Park fishing platform | 3/5 | 4/5 | current health-advisory status unresolved |
| 2 | `logan-albert-river-park` | Albert River Park fishing pontoon | 3/5 | 4/5 | current health-advisory status unresolved |
| 2 | `logan-riverdale-park` | Riverdale Park fishing pontoon | 3/5 | 5/5 | current health-advisory status unresolved |
| 2 | `logan-skinners-park` | Skinners Park fishing pontoon | 3/5 | 4/5 | current health-advisory status unresolved |
| 3 | `logan-tansey-park` | Tansey Park boat-ramp bank | 2/5 | 3/5 | current health-advisory status unresolved; stable safety information incomplete; remote casting-space rating below 3/5 |
| 4 | `logan-federation-drive-reserve` | Federation Drive Reserve riverbank | 2/5 | 2/5 | current health-advisory status unresolved; stable safety information incomplete; remote casting-space rating below 3/5 |
| 5 | `logan-larry-storey-park` | Larry Storey Park boat-ramp bank | 1/5 | 2/5 | current health-advisory status unresolved; stable safety information incomplete; remote casting-space rating below 3/5 |
| 5 | `logan-lawrence-park-wharf-road` | Lawrence Park (Wharf Road) riverbank | 1/5 | 1/5 | current health-advisory status unresolved; stable safety information incomplete; remote casting-space rating below 3/5 |

## Common legal and access sources

- Logan City Council fishing locations: https://www.logan.qld.gov.au/fishing
- Queensland fishing gear rules: https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/rules/equipment
- Queensland closed seasons and waters: https://www.qld.gov.au/recreation/activities/boating-fishing/rec-fishing/rules/closures
- Closed tidal waters list: https://www.dpi.qld.gov.au/business-priorities/fisheries/closures/tidal/waters
- Riedel Park public aerial/context article: https://mycitylogan.com.au/anglers-paradise-opens-at-carbrook/

## Health-review sources retained for audit

- 2024 Logan River warning report:
  https://www.couriermail.com.au/questnews/logan/precautionary-warning-remains-in-place-on-logan-river-as-prawn-farms-get-all-clear/news-story/04311cffdd234e0bfa7888d645e9700f
- 2024 Albert/Logan River spill and recreational-use report:
  https://www.couriermail.com.au/news/gold-coast/untreated-effluent-flowing-into-albert-river-north-of-the-gold-coast-for-a-week/news-story/1945662ce272868fe7f60f9f93767ef8

## Special hazard note

A December 2025 report described a fatal mud entrapment at an Albert Street boat ramp in Logan.
Larry Storey Park is the council-listed fishing/boat-ramp location at 74 Albert Street, Waterford.
The catalogue therefore assigns a maximum remote mud-risk rating and keeps stable safety information
incomplete. The exact incident-site linkage should still be confirmed independently.

## Promotion criteria before a real ranking

For a candidate to move beyond this preliminary batch:

1. Confirm current health/consumption advice and inspect onsite signs.
2. Check the exact point in the current Qld Fishing 2.0 app.
3. Confirm no temporary park, ramp or waterway closure.
4. Confirm a safe cast-net swing radius without people, rails, trees, boats or powerlines.
5. Confirm footing, exposed mud, bank drop and recovery route.
6. Verify the correct tide station assignment in the conditions file.
7. Record current travel time separately; it does not belong in the stable catalogue.
