# Data-source catalogue

This document is a working catalogue. Every adapter must verify current access terms, licensing, spatial coverage, update frequency, and attribution requirements before implementation.

## Required source classes

| Domain | Preferred source class | MVP use |
|---|---|---|
| Administrative boundaries | government open data | clip study areas |
| Roads and access | OpenStreetMap and council data | candidate access and routing inputs |
| Parks and facilities | council open data and official park pages | parking, toilets, playgrounds |
| Hydrography | government hydrology datasets | waterways, drains, catchments |
| Elevation | government DEM and LiDAR catalogues | bank slope and tidal-flat morphology |
| Aerial/satellite imagery | legally reusable public imagery | manual review and later feature extraction |
| Weather | Bureau of Meteorology products | current conditions and warnings |
| Tides | authoritative Queensland/Australian tide products | station predictions and tide phase |
| Marine/fishing rules | Queensland fisheries and marine-park sources | hard legal constraints |
| Water quality | health, environment, and council authorities | advisories and confidence penalties |
| Field results | user-entered observations | model calibration |

## Candidate Australian and Queensland sources

Research and validate adapters for:

- Queensland Open Data Portal;
- Queensland Globe catalogue;
- Geoscience Australia elevation and ELVIS services;
- Bureau of Meteorology forecasts, observations, radar, and warnings;
- Maritime Safety Queensland tide tables and maritime facilities;
- Queensland fisheries rules and closed-water datasets;
- Moreton Bay Marine Park zoning information;
- Ipswich, Brisbane, and Logan council open-data and park information;
- OpenStreetMap for roads, paths, facilities, and public-access context;
- Sentinel and Landsat imagery where resolution and licensing are suitable.

## Provenance contract

Every imported dataset should record:

- publisher;
- dataset title;
- source URL or catalogue identifier;
- licence;
- retrieved timestamp;
- source publication/update timestamp where available;
- spatial resolution and CRS;
- temporal resolution;
- transformation history;
- known limitations.

## Source quality tiers

1. **Tier A:** current authoritative government source.
2. **Tier B:** recognised open dataset with documented provenance.
3. **Tier C:** council page, community report, or manually verified mapping observation.
4. **Tier D:** unverified social-media or forum claim.

Tier D data may generate a candidate for inspection but must not independently establish legality, safety, or health status.

## Immediate research tasks

- determine the best tide source and local station offsets for inland tidal reaches;
- identify public LiDAR coverage for Ipswich, Brisbane, and Logan;
- inventory council park/facility datasets;
- confirm which aerial imagery licences permit automated analysis and redistribution of derivatives;
- identify authoritative machine-readable closure and advisory feeds;
- document routing-provider limits and caching rules.
