# Spiral 1 — exit assessment (2026-07-06)

Against the Spiral 1 workpack v0.2 (§5 build tasks, §6 exit criteria). Verdict: **structurally
complete and past the exit bar; only the final push (task 8) is outstanding.** The build went
well beyond the minimum (classification refinement, governance edges, an officials tranche, and
a full MoG-parity map).

## Build tasks (§5)
| # | Task | Status |
|---|---|---|
| 1 | `ingest_organisations.py` — raw cache + SourceRecord | ✅ 63 pages, 1255 orgs |
| 2 | Bodies transform (classified) | ✅ 663 live bodies |
| 3 | Relationships (sponsor/parent) | ✅ 639 edges |
| 4 | `ingest_ministers.py` — Office + PersonRole | ✅ ministers + officials (159 offices, 159 person-roles) |
| 5 | `compile.py` — graph.json + SQLite + manifest | ✅ 798-node graph |
| 6 | Map face `/site` (Cytoscape) | ✅ radial rings, search, golden thread, filters, dark mode |
| 7 | Verify (spot-checks, calibration, MoG side-by-side) | ✅ 0 re-derivation mismatches, 10/10 known facts, calibration log |
| 8 | Package / **push to personal GitHub** | ⏳ committed locally (27 commits); the single Spiral-1 push not yet done |

## Exit criteria (§6)
- Canonical body list covers all live bodies — ✅ 663 live/forming
- Body IDs stable — ✅ `uk-state-body-{slug}`
- Sponsor/parent relationships recorded — ✅ (+ CO cross-check, R1b)
- Classification recorded — ✅ (+ CO rank-2 refinement, R1)
- Ministers load for departments — ✅ (consolidated one-node-per-person)
- Graph compiles — ✅
- Cytoscape map renders with per-entity pages — ✅ every claim links to source
- 30 spot-checks pass — ✅ (task 7)
- Side-by-side vs the benchmark's structural coverage — ✅ (task 7; gaps explained, not missing)

**All met bar task 8 (push).** Budget/staffing (A13.2 items 5–6) are the deferred bolt-on, not an exit gate.

## Beyond the Spiral 1 minimum (delivered anyway)
- R1 classification refinement from the Cabinet Office Public Bodies Directory (rank 2).
- R2 derived governance edges (PM → cabinet → junior) and R3 office-centred layering.
- Old-name alias enrichment (findability of renamed bodies, e.g. AWE).
- **Officials tranche** — 34 non-min dept heads + dept perm secs (decision #14; pulled forward from Spiral 5).
- Full MoG-parity map: 7-ring radial sunburst, ranked alias search, hover/click golden thread to the PM, rotation, category filters, dark mode, person-consolidated office nodes.

## Bridge to Spiral 2 (the powers register) — clear, with named next steps
**Ready:**
- Entity model + IDs finalised; **Power/Duty/Veto carry a polymorphic `holder` (`office_id` | `body_id`)** — Annex A6 v0.4.
- The **office-holders that will carry powers already exist** (ministers + the officials tranche): "the Secretary of State may…", "the Comptroller & Auditor General may…".
- Classified body register + compiled contract; the Cytoscape renderer scales to a powers graph without change (forward-compat §7).
- Source hierarchy for powers is set: **legislation.gov.uk** (rank 1); confidence calibration + verification discipline in place.

**Needed to start Spiral 2:**
1. Move **Power/Duty/Veto schemas out of draft** (implement Annex A6 v0.4, incl. the `holder` field + `provision_key`/`derived_from_record_id`).
2. Build the **extraction pipeline** — fetch consolidated legislation, LLM-extract powers/duties/vetoes with exact citations and confidence.
3. Close **decision #10** (Tranche A0: the 10–15 pipeline-priority bodies to extract first) and **decision #2** (retrodiction case) — both open in the register.
4. Add a **powers/holder layer to the map** (holder edges from office/body to power records).

## Codebase health (2026-07-06 clean)
Audited: every app.js function has a call site (no dead functions); removed two dead `import sys`
and one unused CSS rule. The one-script-one-job / boring-code standard kept churn low. Scripts
live in `pipeline/` with a run-order README; `validate.py` at root. **1623 records, 0 errors, 0 warnings.**
