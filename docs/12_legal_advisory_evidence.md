# Legal, closure, and health-advisory evidence (M1.6)

> **Status:** operational workflow definition for the offline v0.1 slice.
> All identifiers, authorities, and sources below are synthetic and unmistakably
> fictional. Do **not** treat this document as legal or health advice, and do not
> commit real redistributable restriction/advisory records until owner decision
> **D1** (code licence + data-licensing strategy) is resolved.

## Purpose

Define, for one recommendation run at one requested time (`valid_at`):

1. which sources count as authoritative for activity permission, closures, and
   health advisories (source hierarchy);
2. how effective periods and retrieval timestamps are represented;
3. exactly how active restrictions are evaluated against the run time;
4. how unknown and contradictory evidence fails closed;
5. how a reviewer checks all of this from files and reports.

Read first:

1. `docs/03_data_sources.md` — source classes and provenance contract;
2. `docs/04_scoring_engine.md` — hard gates and fail-closed unknowns;
3. `data/catalogue/CURATION.md` — candidate curation checklist;
4. `src/geoweaver/scoring/constraints.py` — the implemented gate evaluation.

## Authoritative source hierarchy

For the v0.1 manual workflow, rank sources for legal/closure/advisory claims as:

1. **Authoritative government instrument or register** (Tier A): the statute,
   regulation, gazetted closure, marine-park zoning instrument, council closure
   notice, or health-authority advisory that actually creates the restriction.
   Source-class candidates are listed in `docs/03_data_sources.md` (Queensland
   fisheries rules and closed-water datasets, Moreton Bay Marine Park zoning,
   council open-data/park pages, health/environment/council water-quality
   authorities).
2. **Recognised official publication of that instrument** (Tier A/B): the
   official register entry, map layer, or authority web page quoting it, with
   retrieval timestamp and URL/catalogue identifier recorded in the M1.3 source
   registry.
3. **Manual lawful observation or Tier B/C corroboration** (Tier B/C): your own
   dated signage photograph/transcript or a recognised open dataset. This can
   *support* a claim but never overrides a higher-ranked source.
4. **Unverified social/forum claims** (Tier D): may nominate a site for
   inspection only. They must never establish legality, access, or safety.

Conflict rule: where two applicable sources disagree, the run fails closed
toward the most restrictive reading — an applicable `active` restriction gates
even beside an `inactive` one, and an applicable `unknown` status gates even
beside an `inactive` one. Resolve the conflict out-of-band (recheck the
authoritative instrument, correct the record, re-run); do not edit the ranking
output to smooth over it.

## Representation: effective periods and retrieval timestamps

Every `Restriction` (closure/restriction entries) and the per-segment
`health_advisory_evidence` record carries:

- `status`: `active` | `inactive` | `unknown`;
- `authority`: who issued the underlying instrument or statement;
- `source_ref`: stable ID resolving into the M1.3 source registry;
- `reason`: human-readable statement of what applies and why;
- `effective_from` / `effective_to`: optional timezone-aware bounds of the
  declared window. `null` on either side means open-ended in that direction.
- `retrieved_at`: timezone-aware timestamp of when the evidence was obtained.

Catalogue curation rules (see `data/catalogue/CURATION.md`):

- each restriction needs authority, `source_ref`, `retrieved_at`, and the
  effective window as stated by the source (`null` only when the source states
  no bound);
- `health_advisory_status` must equal `health_advisory_evidence.status`
  (rejected at load time otherwise — a direct contradiction cannot be ranked);
- what you cannot verify stays explicitly `unknown` (`legal_status_known:
  false`, permission `unknown`, restriction/health status `unknown`).

## Evaluation against the run time

Implemented in `src/geoweaver/scoring/constraints.py`
(`_health_advisory_check`, `_closure_check`, `Restriction.is_effective_at`).
For a run at `condition.valid_at`:

1. **Applicability:** a restriction applies when its effective window includes
   `valid_at`, both bounds inclusive. An `effective_to` in the past means the
   closure has expired and does not gate; an `effective_from` in the future
   means it is not yet in force and does not gate. Open-ended records
   (`null` bounds) always apply.
2. **Retrieval freshness direction:** any *applicable* restriction (or the
   health evidence, when it is the record under test) with `retrieved_at`
   later than `valid_at` fails its gate — evidence obtained after the
   recommendation time cannot support that run.
3. **Health gate:** the health evidence must apply at `valid_at` (else fail).
   Then `inactive` passes; `active` fails naming the advisory; `unknown`
   fails closed.
4. **Closure gate:** among applicable restrictions, any postdated retrieval
   fails the gate; then any `active` fails naming each active reason; else any
   `unknown` fails closed; otherwise the gate passes.
5. **Score interaction:** none. `score_segment` forces `final_score` to 0 for
   any ineligible segment, and ranking always places eligible records first —
   a high habitat score can never override a legal/closure/advisory failure.
6. **Reporting:** every recommendation carries `applicable_restrictions` (only
   records whose window includes `valid_at`), the full
   `health_advisory_evidence`, and per-gate failure reasons. JSON reports
   expose all three; Markdown reports render them under “Hard-gate failures”
   and “Legal and health evidence”.

Time-sensitive reminder: a passing run is decision support at `valid_at` only.
Recheck official sources before travelling — windows and advisories change.

## Unknown and contradictory evidence (fail closed)

| Situation | Gate outcome |
|---|---|
| Applicable restriction `active` (bounded or open-ended) | `active_legal_closure` fails, reason names each active restriction |
| Applicable restriction `unknown` | `active_legal_closure` fails closed |
| Applicable + postdated `retrieved_at` | Gate fails (restriction evidence postdates run) |
| Expired window (`effective_to` before `valid_at`) | Not applicable — does not gate |
| Future window (`effective_from` after `valid_at`) | Not applicable — does not gate |
| Contradictory applicable pair (`active` + `inactive`) | Fails; active reason is named |
| Contradictory applicable pair (`unknown` + `inactive`) | Fails closed on the unknown |
| Health `active` | `health_advisory` fails naming the advisory |
| Health `unknown`, or health evidence not applicable at `valid_at`, or postdated | `health_advisory` fails closed |
| `health_advisory_status` ≠ evidence `status` | Rejected at catalogue load — never ranked |

## How a reviewer verifies a run

```sh
uv run geoweaver validate-catalogue --catalogue <candidate.geojson> --sources <registry.json>
uv run geoweaver rank --catalogue <catalogue.geojson> --inputs <run_input.json> --sources <registry.json> --format markdown
```

1. Confirm every `source_ref` in the catalogue resolves in the registry
   (exit 0 + “Provenance audit passed”).
2. Confirm every run-input evidence `source_ref` likewise resolves: `rank --sources`
   audits both catalogue and run-input references before ranking and fails closed
   (exit 2) on dangling references.
2. In the report, check “Condition time” equals the intended trip time.
3. For each ineligible candidate, read “Hard-gate failures” (`health_advisory`
   / `active_legal_closure`) and cross-check “Legal and health evidence”
   (restriction IDs, authorities, effective windows, retrieval timestamps,
   reasons) against the authoritative instrument.
4. For each eligible candidate, confirm no applicable `active`/`unknown`
   restriction is silently missing — `applicable_restrictions` lists exactly
   the records whose window includes the run time.

## Non-goals

- No live closure/advisory feeds or adapters (M2).
- No automated tide-station assignment (M1.7).
- No real 20-candidate catalogue (M1.5, needs D1).
- No field-verification claims from desk research.
