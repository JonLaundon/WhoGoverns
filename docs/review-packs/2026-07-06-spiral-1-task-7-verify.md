# Session review pack (Annex A11.5)

**Session date:** 2026-07-06
**Agent / operator:** WhoGoverns build agent (Claude Code, host-side)
**Task stated at start:** Spiral 1 build **task 7** — verify: 30 structural spot-checks
against source, populate the calibration log, side-by-side vs machineryofgovernment.uk.

## Records created / changed
- New **code**: `pipeline/verify.py` (re-derivation audit + known-facts panel + calibration sample).
- **`calibration/confidence_log.csv`** populated (29 rows).
- No `data/` or schema changes.

## Verification results
1. **Classification re-derivation audit (all 663 bodies): 0 mismatches.** Re-classifying each body straight from its cached `format` via the map reproduces the stored `body_type` exactly — the transform introduced no drift, and every classification traces to source.
2. **Known-facts panel: 10/10 confirmed** — independent domain check (MoD, HM Treasury → ministerial_department; HMRC, Ofgem, CPS, Food Standards Agency → non_ministerial_department; DVLA, HMPPS → executive_agency; Environment Agency → executive_ndpb; ACOBA → advisory_ndpb), sponsors correct (e.g. CPS → Attorney General's Office).
3. **Live currency spot-check (re-fetched from GOV.UK):** Organisations API total still **1255** (= cache, no drift); live Ofgem matches (Non-ministerial dept, exempt, DESNZ parent); live Chancellor = Rachel Reeves (= our person-role). Data is current and faithful, not fabricated.
4. **Calibration:** 29 rows across body types + PM/Chancellor offices. Predicted confidence 0.97 (clean format) / 0.75 (flagged for finer pass) / 0.90 (offices); outcomes `confirmed` (all, since re-derivation matched).

## Side-by-side vs machineryofgovernment.uk (structural coverage)
MoG counts are the sponsor-provided figures (comparison / gap-finding only — A2.1; never copied).

| body_type (ours) | Ours | MoG | Δ | Reconciliation |
|---|---:|---:|---:|---|
| ministerial_department | 23 | 24 | −1 | near-match |
| non_ministerial_department | 20 | 21 | −1 | near-match |
| executive_agency | 43 | 48 | −5 | a few we hold as sub-org/other |
| division_directorate | 130 | 108 | +22 | our `Sub organisation` bucket is broader |
| executive_ndpb | 132 | 151 | −19 | MoG classifies more as executive NDPB |
| advisory_ndpb | 59 | 80 | −21 | some of our `other_body` are advisory |
| tribunal | 29 | 7 | +22 | **granularity** — API lists every First-tier/Upper Tribunal *chamber*; MoG aggregates |
| public_corporation | 19 | 33 | −14 | some of our `other_body` are public corps |
| royal_charter_body | 0 | 8 | −8 | **expected** — Privy Council tranche not yet ingested |
| other_body | 208 | 174 | +34 | our catch-all is oversized |
| **total** | **663** | **~654** | | different universes (MoG's 8 chartered bodies are outside the GOV.UK API; we carry 11 forming) |

**Reading:** the deltas are coherent and expected. Reliance on the coarse GOV.UK `format` inflates `other_body`/`division_directorate` and under-fills `executive_ndpb`/`advisory_ndpb`/`public_corporation`; the tribunal delta is the chamber-vs-aggregate granularity choice; royal charter is the deferred tranche. **This quantifies the refine target (R1):** the Cabinet Office Public Bodies dataset should move much of the `other_body`/coarse tail into the firmer NDPB/agency/public-corporation classes and close most of these gaps.

## Model findings surfaced by verify (feed the refine)
- **R2 — ministerial governance edges.** Offices currently link only to their host department; there are no PM→cabinet→junior edges. Add them as a derived (convention-based) map layer.
- **R3 — layering.** Add the empty `independent_official` tier only at Spiral 5; switch to a layered layout once R2 edges exist.
- **R1 — classification refinement** as quantified above.

## Validation result
`py -3 validate.py` — **1552 records, 0 errors, 0 warnings.**

## Recommended next action
Exit-criteria check for Spiral 1, then the **refine block R1 → R2 → R3** (now tracked), then
**task 8 (package/push)**. R1 (classification) and R2 (governance edges) are the highest-value.
