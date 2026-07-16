# Manual condition files

`demo_conditions.json` contains fictional synthetic conditions. A manual real-trip file must
set `data_classification` to `manual_user_supplied`, cite the sources actually consulted, and
use the exact timezone-aware trip target time in `observed_or_predicted_at`.

Every snapshot declares one applicability form:

- `segment`: `scope_id` is one catalogue `segment_id`;
- `waterway`: `scope_id` exactly matches a catalogue waterway label; or
- `explicit_segment_group`: `scope_id` names the scope and `segment_ids` lists its members.

Every catalogue segment must resolve to exactly one snapshot. Unknown IDs, missing coverage,
and overlapping scopes are rejected; location-specific evidence is never copied to an
unrelated segment. Source arrays for weather, footing, tide, and daylight must each contain at
least one non-blank reference.

Each snapshot also requires `tide_source` metadata recording the source location ID and label,
manually supplied distance to the declared scope, controlled assignment method (`co_located`,
`manually_reviewed`, or `inferred`), applicability source, retrieval timestamp, and evidence state.
The applicability reference must also appear in `source_refs.tide`. Missing, stale, unlinked, or
inferred tide applicability fails the tide gate. GeoWeaver reports these claims but does not
calculate the distance or independently verify the station assignment.

Controlled states are `clear`, `active`, or `unknown` for warnings and lightning; `safe`,
`unsafe`, or `unknown` for footing; the documented tide stages; and `verified` or `inferred`
for evidence. Wind, gust, and daylight may be `null` when genuinely unknown. Those values fail
the relevant hard gates rather than receiving defaults. An `inferred` snapshot is never marked
verified and fails the critical weather, footing, tide, and daylight gates. Retrieval timestamps
must include a timezone and must not postdate the trip target.
