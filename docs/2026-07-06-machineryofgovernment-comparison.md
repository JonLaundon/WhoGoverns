# WhoGoverns vs machineryofgovernment.uk — functionality, node/link, and source comparison

**Date:** 2026-07-06. **Status:** comparison / gap-finding only (Annex A2.1). MoG (© Harry
Rushworth, `machinery-of-government.vercel.app` → `machineryofgovernment.uk`) sets the
*presentation pattern*; no data, code or design is copied. MoG's live app is a client-rendered
SPA that could not be crawled here, so the functionality notes draw on the sponsor's own
description, public write-ups, and the classification counts the sponsor supplied; **link
fidelity is compared against the shared primary sources (GOV.UK, Cabinet Office), not by
scraping MoG.**

## 1. Functionality parity

| Capability | MoG | WhoGoverns (Spiral 1) | Status |
|---|---|---|---|
| Interactive whole-state graph | ✅ office-centred org chart | ✅ office-centred; Hierarchy + Rings layouts | **parity** |
| PM → cabinet → junior hierarchy | ✅ | ✅ (R2 leads edges, R3 layering) | **parity** |
| Search | ✅ | ✅ incl. **former-name/alias search** (e.g. "Atomic Weapons" → AWE NST) | **parity+** |
| Per-entity drill-down | ✅ | ✅ with **a cited source for every claim** | **parity+** |
| Body classification taxonomy | ✅ (its scheme) | ✅ (adopted the same scheme) | **parity** |
| Ministers | ✅ | ✅ (125 offices, current holders) | **parity** |
| Senior officials (civil servants, independent officials) | ✅ | ❌ deferred to Spiral 5 | **gap** |
| Budgets | ✅ | ❌ deferred bolt-on | **gap** |
| Staffing | ✅ | ❌ deferred bolt-on | **gap** |
| Royal Charter bodies | ✅ (8) | ❌ deferred Privy Council tranche | **gap** |
| Open machine-readable dataset | ✕ (presentation app) | ✅ JSON records + JSON Schema + SQLite + graph.json | **WhoGoverns only** |
| Every record cited to a primary source | ✕ (curated) | ✅ | **WhoGoverns only** |
| Statutory powers / duties / **vetoes** ("who can legally block") | ✕ | ⏳ Spiral 2 (the core mission) | **WhoGoverns roadmap** |
| Reproducible pipeline (re-runnable from source) | ✕ | ✅ `pipeline/` | **WhoGoverns only** |

**Read:** MoG is more complete *today on presentation* (budgets, staffing, senior officials,
chartered bodies) and is a polished product. WhoGoverns' differentiators are structural: an
**open, cited, reproducible dataset**, and the **powers/veto layer** (Spiral 2) that answers
"who can legally block this?" — which no org chart, MoG included, does. The MoG gaps
(officials, budgets, staffing, royal charter) are all already tracked/deferred, not surprises.

## 2. Node & link comparison

Counts, post-R1 (ours) vs MoG (sponsor-supplied). MoG is compared, not copied; where we
differ we reconcile against the **primary source**, not against MoG.

| body_type | Ours | MoG | Why they differ |
|---|---:|---:|---|
| ministerial_department | 23 | 24 | near-match (±1 counting of PMO/parity) |
| non_ministerial_department | 20 | 21 | near-match |
| executive_agency | 45 | 48 | a few sub-orgs we hold as division/other |
| executive_ndpb | 137 | 151 | bodies not exact-matching the CO directory by name |
| advisory_ndpb | 77 | 80 | **within 3** after R1 |
| tribunal | 28 | 7 | **granularity**: GOV.UK lists every First-tier/Upper Tribunal *chamber*; MoG aggregates |
| public_corporation | 19 | 33 | MoG classes more financial/commercial bodies as public corps |
| royal_charter_body | 0 | 8 | our deferred Privy Council tranche |
| other_body | 186 | 174 | our catch-all still larger |

**Do our links line up?** Our sponsor/parent edges are derived from the GOV.UK
`parent_organisations`/`child_organisations` and were verified in task 7 (re-derivation: 0
mismatches; live re-fetch confirmed no drift; 10/10 known-facts). MoG's edges are hand-curated
but from the same public sources, so at department→ALB level they should broadly agree. The
*differences* are the ones above — node granularity (tribunal chambers), the royal-charter
tranche, and layers we haven't built (budget/staffing edges). Our edge fidelity advantage is
that **every link is cited and reproducible**, so a disagreement with MoG is adjudicable against
the source rather than by opinion. A true node-by-node diff against MoG would need their data,
which the constraints forbid ingesting — so the correct check is against GOV.UK/CO, which we do.

## 3. Other sources for finer linkage fidelity

Ranked by value for *linkages* specifically, and mapped to our source hierarchy (A3):

1. **Cabinet Office Public Bodies Directory — sponsor fields (already downloaded).** We used its
   `overall_classification` for R1 but it also carries `overall_direct_sponsor`,
   `overall_senior_sponsor` and `overall_parent_department`. A quick follow-up ("R1b") could
   refine the **sponsor links** for the 225 matched ALBs from this rank-2 source. *Highest-value
   quick win — the file is already in the cache.*
2. **Departmental annual reports & accounts (A3.2 rank 3).** The consolidation boundary /
   "departmental group" is the authoritative statement of which ALBs sit under which department —
   firms up sponsor/accountability edges where GOV.UK and CO disagree.
3. **Framework documents (per ALB, A3.1 rank 4).** Define the *nature* of each department↔body
   link (accountability, appointments, funding, direction powers) — turns a bare "sponsors" edge
   into typed governance relationships.
4. **data.gov.uk organograms (departmental org-chart CSVs, twice-yearly).** Machine-readable
   senior-civil-servant roles and reporting lines — the source for the **senior-officials layer
   (Spiral 5)** and internal reporting edges, and would populate the empty `civil_servant` /
   `independent_official` office tiers.
5. **legislation.gov.uk (A3.1 rank 1).** Statutory establishment and the powers/duties/**vetoes**
   — the finest "who can legally block whom" links. This is **Spiral 2** and the whole point.
6. **GOV.UK content API role details (`attends_cabinet_type`).** Would turn the R2 cabinet-vs-junior
   *heuristic* into a sourced tiering.
7. **Privy Council chartered-bodies register** — the royal-charter tranche (the 8 MoG has, we don't).
8. **HMT OSCAR / departmental accounts** (budget) and **Civil Service Statistics** (staffing) —
   the deferred bolt-ons; also add financial/staffing edges MoG already shows.
9. **Institute for Government — Whitehall Monitor** (third-party, discovery/comparison only, like MoG).

**Recommended next linkage step:** (1) above — re-use the already-downloaded CO directory to refine
sponsor links (R1b), then (3) framework documents to type the edges, then (5) legislation for the
Spiral 2 powers/veto layer, which is where WhoGoverns overtakes any org chart.

## Sources
- machinery-of-government.vercel.app / machineryofgovernment.uk (© Harry Rushworth) — comparison only.
- GOV.UK Organisations API; GOV.UK content API; Cabinet Office Public Bodies Directory 2023/24.
