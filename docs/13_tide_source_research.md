# Authoritative v0.1 tide source — research note (M1.7a)

> **Status:** research note satisfying task M1.7a. It selects **no live provider**,
> implements **no adapter**, and authorises **no automated retrieval** (M2).
> It establishes the single authoritative source that manual M1.7 station-selection
> work must be based on.
>
> **Recommendation (one line):** for v0.1, read tide evidence manually from the
> **Maritime Safety Queensland Queensland Tide Tables** (annual publication),
> using the **Brisbane Bar** standard-port predictions and, where the candidate
> matches a listed secondary place, the publication's official secondary-place
> calculation method. Everything else fails closed.

Read first:

1. `docs/03_data_sources.md` — source classes and provenance contract;
2. `docs/04_scoring_engine.md` — hard gates and fail-closed unknowns;
3. `docs/10_implementation_plan.md` — M1.7a contract and the M1.7 task it unblocks.

All external claims below were verified against primary-source pages on 2026-09-11
(see "Sources consulted"). Do not treat this note as navigation or safety advice.

## 1. Recommended v0.1 source

| Field | Value |
|---|---|
| Publisher | Queensland Department of Transport and Main Roads — Maritime Safety Queensland (MSQ) |
| Exact product/dataset | **Queensland Tide Tables**, annual publication (e.g. 2026 edition); standard-port prediction tables plus secondary-place calculation instructions, tidal planes, highest-tide tables, and sun/moon tables |
| Canonical access points | `https://www.msq.qld.gov.au/tides/tide-tables` (publication), `https://www.msq.qld.gov.au/tides/calculating-secondary-port-tide-times` (official offset method), `https://www.msq.qld.gov.au/tides/open-data` (gauge datasets on `data.qld.gov.au`); identical prediction tables mirrored at `https://www.bom.gov.au/oceanography/projects/ntc/qld_tide_tables.shtml` |
| Underlying predictions | Bureau of Meteorology National Operations Centre (NOC) Tidal Unit (formerly National Tidal Centre), computed from the Queensland tide-gauge network that MSQ coordinates, validates, and archives with port authorities and the science portfolio |
| Relevant stations | **Brisbane Bar** (standard port at the river mouth; 2026/2027 prediction PDFs published); **Port Office, Brisbane River** gauge datasets (predicted interval + high/low; a secondary location related to Brisbane Bar); and the officially listed secondary places below — Brisbane River (Boat Passage, Pinkenba, Cairncross Dock, New Farm, Port Office Edward St Ferry, Tennyson Long Pocket, Indooroopilly, Seventeen Mile Rocks, Wacol Wolston Creek, Goodna Woogaroo Creek, Moggill Ferry, Kholo Creek), **Bremer River — Warrego Highway Bridge**, Logan/Albert system (Rocky Point at the Logan mouth, Junction Albert River, Slacks Creek mouth, Waterford, Pacific Highway Bridge, Wolffdene, Pimpama River Kerkin Rd Weir), and Moreton Bay places (e.g. Jacobs Well, Cabbage Tree Point, Russell Island) — each with official time-difference/ratio/constant data relative to Brisbane Bar in the Semidiurnal Tidal Planes |
| Update/publication frequency | Annual publication (2026 edition PDF; page last updated 02 June 2026); open-data gauge prediction resources updated annually (annual prediction year published the preceding December) |
| Licence/terms | Publication text (MSQ material): Creative Commons Attribution 4.0 Australia, © State of Queensland (DTMR). Prediction tables themselves: © Commonwealth of Australia (BoM NOC Tidal Unit) under the BoM tide-prediction **Conditions of Use**. Open-data gauge resources: Creative Commons Attribution 4.0 |
| Attribution | Whole/part republication of the Tide Tables must carry the inside-cover copyright, acknowledgements, and disclaimers; individual prediction tables must carry the BoM acknowledgement + disclaimer; non-table MSQ information must acknowledge DTMR (MSQ) + disclaimer; open-data extracts need CC BY 4.0 attribution |
| Redistribution | The publication may be freely published, reproduced, added to, or repackaged in whole or part for private or commercial purposes **provided** the notices above travel with it; must not imply BoM endorsement or connection; must not scrape `bom.gov.au` (use MSQ pages/open data instead). The formal BoM Data Licence Agreement (2025) governs licensed data feeds, **not** a human reading published tables — flag it for M2/owner before any automated retrieval |

## 2. Why this source (and not the alternatives)

- **Authoritative for the study area.** MSQ states its gauge network, validation, and
  archiving are the basis of the *official* tide predictions used for port operations
  in all Queensland ports. Brisbane Bar is the designated standard port at the mouth
  of the Brisbane River system that drains the Ipswich/Brisbane catchments.
- **Offsets are officially documented.** The publication's secondary-place method
  (time differences, height ratio/constant, tidal planes) is the only sanctioned way
  to move a prediction off the standard port. Ad-hoc offsets are therefore easy to
  recognise and reject in M1.7 review.
- **Licence permits the v0.1 workflow.** Manual reading plus CC BY-compatible citation
  fits an offline, file-based milestone with no redistribution of bulk data.
- **Alternatives rejected for v0.1:** direct BoM website use adds nothing (same
  prediction tables) while carrying the no-scraping and endorsement constraints, so
  MSQ is the cleaner citation; commercial tide apps and aggregators (e.g.
  WillyWeather) are Tier C/D at best and must never establish tide evidence; the
  Australian Hydrographic Service and AMSA gauges feed the network but publish no
  more suitable study-area product; the DES coastal storm-tide gauges exist for
  storm-surge recording, not routine predictions.

## 3. Study-area and station coverage findings

The Semidiurnal Tidal Planes (verified in the MSQ 2025 edition; plane values are
fixed for tidal datum epoch 2010–2029, so the listed Brisbane Bar relationships
stand for the 2026 tables year) give official coverage in **three tiers**. M1.7 must
turn these tiers into per-candidate assignment boundaries; listing here is not itself
an assignment.

- **Tier 1 — Brisbane Bar direct.** Candidates at the river mouth, open Moreton Bay
  shoreline, and lower river near the Bar use the standard-port predictions directly.
- **Tier 2 — listed secondary places with official differences.** Candidates
  reasonably associated with a listed place use the official calculation:
  - *Brisbane River:* Boat Passage (+0:00/+0:00), Pinkenba (+0:11/+0:16),
    Cairncross Dock, New Farm, Port Office Edward St Ferry (+0:35/+0:36), Tennyson
    (Long Pocket), Indooroopilly, Seventeen Mile Rocks, Wacol (Wolston Creek),
    Goodna (Woogaroo Creek, +2:03/+2:10), Moggill Ferry (+2:21/+2:33),
    Kholo Creek (+2:30/+2:50);
  - *Bremer River:* **Warrego Highway Bridge (+2:30/+2:55)** — the listed official
    relationship covering the Ipswich urban reach of the Bremer;
  - *Logan/Albert system:* Rocky Point at the Logan mouth (+0:40/+0:55, ratio 0.96),
    Junction Albert River (+1:22/+2:14), Slacks Creek mouth (+2:13/+3:05),
    Waterford (+2:39/+3:34), Pacific Highway Bridge, Wolffdene, Pimpama River
    (Kerkin Rd Weir);
  - *Moreton Bay:* Jacobs Well, Cabbage Tree Point, Russell Island, and other listed
    bay places for southern-bay shorelines (ocean beaches from Cape Moreton to
    Snapper Rocks run 1 h 30 min earlier than Brisbane Bar).
- **Tier 3 — reaches between or beyond listed places: default fail-closed.**
  Official coverage does **not** mean every candidate inherits a prediction:
  - *Ipswich/Bremer:* the Warrego Highway Bridge secondary place covers the listed
    reach; candidates upstream of it (toward Walloon/Rosewood), on unlisted side
    creeks, or anywhere the relationship to the listed place is not defensible stay
    excluded — the Bremer approaches its tidal limit upstream, where river flow
    dominates and MSQ charting marks an end of tidal influence.
  - *Logan/Albert:* listed places cover the mouth-to-Waterford corridor and named
    junctions; candidates above Waterford, on unlisted tributaries, or in reaches
    whose mapping to a listed place cannot be defended stay excluded.
  - *Brisbane mid/upper river:* same rule between Kholo Creek / Moggill Ferry and
    Mount Crosby — tidal influence reaches Mount Crosby but phase lag and
    attenuation grow, so only listed-place associations count.

## 4. Station-assignment risks that must stay fail-closed

- **Unlisted reaches.** Never extend a listed secondary place to a candidate whose
  association with it cannot be defended — especially above Waterford (Logan),
  above the Warrego Highway Bridge reach (Bremer), between Kholo Creek / Moggill
  Ferry and Mount Crosby, on unlisted tributaries and side creeks, or across
  hydraulically separated water bodies.
- **Distant stations.** Never apply Brisbane Bar (or Gold Coast Seaway) directly to
  a candidate better served by a listed secondary place, or to any Tier 3 reach,
  without the official secondary-place calculation.
- **River travel time / phase lag.** Up-river high/low waters lag the Bar by amounts
  the official tables quantify only for listed secondary places; guessed lags are
  manual judgement, not evidence.
- **Inland tidal reaches and hydraulic separation.** Near Mt Crosby (Brisbane River)
  and the upper tidal Bremer, tidal signal competes with river flow and weir/gauge
  structures; a rising river can mask or mimic tide stage.
- **High-flow events.** Flood flows decouple river levels from astronomical
  predictions entirely; any tide evidence recorded during elevated flows is suspect.
- **Predictions are not observations.** Table heights exclude meteorological effects
  (pressure, wind, surge) and seasonal variation; heights are relative to LAT
  (Queensland Port Datum) and times to AEST — mixing datums or timezones invalidates
  the evidence.
- **Staleness.** Predictions are computed per calendar year; using a superseded
  edition without checking the current one fails the freshness expectation.

## 5. What M1.7 must record (evidence contract for the next task)

Each tide assignment in run evidence must cite, at minimum: the station or secondary
place ID (Tier 1 standard port or Tier 2 listed place — never an unlisted reach
presented as if it were listed); the source edition and table used (e.g. "2026
Queensland Tide Tables, Brisbane Bar" plus the Semidiurnal Tidal Planes row for the
listed place); the method (direct standard-port reading vs official secondary-place
calculation with the applied differences); `retrieved_at`; datum (LAT) and timezone
(AEST); and the assignment rationale linking the candidate's reach to the station.
Where no listed station or secondary place covers the reach, the candidate is
excluded on tide evidence — that exclusion **is** the correct output, not a gap to
work around.

Proposed M1.3 registry citation for M1.7 to register (metadata only, no data copied):

- `source_id`: `msq://tide-tables/2026` (stable per edition; mint a new ID per year)
- publisher: Queensland Department of Transport and Main Roads — Maritime Safety Queensland
- title: Queensland Tide Tables 2026 (Brisbane Bar standard port + secondary-place method)
- `source_url`: `https://www.msq.qld.gov.au/tides/tide-tables`
- licence: CC BY 4.0 AU (MSQ material) + BoM Conditions of Use (prediction tables)
- `retrieved_at`: date the human read the tables for the run
- limitations: predictions only; AEST/LAT; secondary method valid solely for listed
  places (Brisbane River places, Bremer Warrego Highway Bridge, Logan/Albert
  places, Moreton Bay places as listed); unlisted reaches fail closed

## 6. Unresolved questions (remain fail-closed; some need owner input)

1. Exact secondary-place coverage of future real candidate reaches — resolved per
   candidate inside M1.7 by checking the tables (Tier 2 association vs Tier 3
   exclusion), not here.
2. Reaches beyond the listed places (above Waterford, above the Warrego Highway
   Bridge reach, unlisted tributaries) — excluded until an official relationship
   is documented for them.
3. Redistribution of table extracts inside the repo beyond short citations — needs
   the D1 data-licensing decision; until then, cite and link, do not copy tables.
4. Automated retrieval and any formal BoM data licence — M2 scope and may need
   owner/provider approval; this note authorises manual reading only.

## Sources consulted (2026-09-11; public documentation only, no downloads copied)

- MSQ Queensland Tide Tables page (`msq.qld.gov.au/tides/tide-tables`) — publication
  contents, gauge-network provenance, CC/conditions summary; 2026 edition listed.
- MSQ "Calculating secondary port tide times", "Notes and definitions", and tidal
  datum/epoch notes — official offset method; standard vs secondary-place
  definitions; 2022 plane values fixed for tidal datum epoch 2010–2029.
- MSQ 2025 Semidiurnal Tidal Planes (standalone PDF) — verified listed Brisbane Bar
  relationships and differences for Rocky Point (Logan mouth), Junction Albert
  River, Slacks Creek mouth, Waterford, Pacific Highway Bridge, Wolffdene, Pimpama
  River, Brisbane River places (Boat Passage through Kholo Creek), Bremer River
  Warrego Highway Bridge, and Moreton Bay places; 2015 appendices corroborate the
  Logan/Bremer rows (plane values fixed per datum epoch, so rows stand for 2026).
- MSQ Sea level measurement in Queensland — gauge-network operators, Port Office
  gauge context, DES storm-tide network purpose.
- MSQ Open data page — Port Office Brisbane River and Brisbane Bar gauge datasets
  on `data.qld.gov.au`, including "Secondary Location — Related to Brisbane Bar".
- `data.qld.gov.au` Brisbane Bar predicted interval/high-low resources — CC BY 4.0
  licence, annual update frequency, CSV format.
- BoM NTC Queensland tide tables page — Brisbane Bar 2026/2027 tables, Conditions
  of Use (acknowledgement + disclaimer, modified-product wording, no scraping).
- BoM Data Licence Agreement (2025, PDF) — scope of formal licensed feeds vs
  published tables; attribution/endorsement constraints noted for M2.
- BoM Tide Predictions portal (`bom.gov.au/australia/tides`) — Queensland
  standard/secondary *port* lists (no Logan River *port* entry; Logan coverage comes
  from MSQ secondary *places*, not ports).
- 2024/2025 Queensland Tide Tables PDFs (inside-cover matter) — CC BY 4.0 AU text,
  three-way reproduction conditions, predictions-only warning.
- BoM Brisbane River below Wivenhoe Dam flood brochure — tidal influence to
  Mount Crosby; Bremer joins at Moggill.
- Queensland WetlandInfo Bremer catchment story — lower-Bremer tidal/backwater
  influence.
- MSQ Beacon-to-Beacon Brisbane River and Bremer River chart — end-of-tidal-
  influence marking on the Bremer upstream of Ipswich urban reaches.
- Khalil et al. 2025 (Brisbane River estuary modelling, via publisher page) —
  estuary tidal range and ~80 km tidal influence, Bremer junction context.
- Peer-reviewed estuary literature citing Brisbane Bar open-data gauge records —
  corroborates gauge identity and continuity (not used as tide evidence itself).
