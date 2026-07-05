# Spiral 1 Workpack — POC (v0.1, draft for sponsor sign-off)

**Project:** The State Machine (working name "His Majesty's Government")
**Date:** 2026-07-05
**Author:** Handoff owner (Claude), for sponsor (Jon) sign-off
**Governs:** Spiral 1 only. Binds to Project Plan v0.5 and Annex A v0.3.
**Status:** Draft. No build begins until Jon signs this off.

> Reviewer note: this is a planning artefact. Nothing here adopts a position or commits the project; it fixes what Spiral 1 will and will not do so the build is bounded and sustainable against the annexes.

---

## 1. Bottom line

Spiral 1 is a **deliberately lean proof of concept**: the ~25 live UK ministerial departments, their ministers, and their department-level budget and staffing, rendered as an interactive map with per-department entity pages, every figure cited to a primary source. It proves the whole pipeline end-to-end — ingest → schema → validate → compile → map — on a clean, narrow slice. It is a *subset* of the plan's parity benchmark, not full parity; the arm's-length-body estate and the powers layer are deliberately deferred. Nothing in the POC forecloses them.

Effort: **~4–6 sessions** (setup 2–3, build 2–3), well inside the plan's 6–9 for full parity because the scope is narrower.

---

## 2. Decisions closed at the scoping interview

To be logged into the plan's decision register (§10) on sign-off. I have not edited the governing plan yet.

| # | Decision | Closed as | Note |
|---|---|---|---|
| 1 | Publication entity | **Personal GitHub** (handoff/sponsor), interim | Build and compile in the folder first; push all of Spiral 1 as a single first push at exit. Local commit discipline (A11.6) still applies. |
| 4 | Project name / public identity | **"His Majesty's Government"** as folder + internal working name | Public-facing name held provisional; recommend locking at Spiral 4 (see §8 governance flag). |
| 10 | Tranche A0 body list | **Deferred to Spiral 2** | A Spiral 2 input; not needed for the POC. |
| — | Repo layout | **Nested `state-machine/` subfolder** inside the HMG folder | Matches Annex A12; governing docs stay at folder root, referenced into `/docs`. |
| — | Map renderer | **Vanilla static (SVG/JS) reading compiled graph.json** | Cytoscape.js adopted later when graph density needs it; drop-in because the data contract is stable. Boring-code standard ring-fenced to the Python pipeline. |
| — | Design language | **GDS *principles* only** (accessibility, plain language, civic-minimal), **not** GOV.UK brand assets | Crown and GDS Transport font are Crown-restricted; explicit "not affiliated with HM Government" line on the site. |
| — | Recusal | **Does not bite on public/official data.** Structural modelling (and later statutory-powers extraction from legislation.gov.uk) is public official information, not tacit knowledge or partisan development | Sponsor discipline: commit nothing until official information is surfaced. MoD/FCDO/agencies included as ordinary structural nodes. |

---

## 3. Fixed Spiral 1 POC scope

**In scope**
- **Bodies:** the live UK **ministerial departments** (~25; exact set fixed by filtering the GOV.UK Organisations API on `format = "Ministerial department"` and `govuk_status = "live"` at setup). MoD, FCDO and any intelligence bodies that appear as departments are included as structural nodes.
- **Officeholders:** **ministers only** (Secretary of State / ministers of state / parliamentary under-secretaries), attached to their department. Minimum Office + PersonRole fields per the Annex A4 exception.
- **Finance:** **department-level** budget and staffing.
- **Relationships:** sponsor/parent edges *among departments* (most sponsorship edges point to ALBs, which are out of scope, so this layer is thin by design — see §8).
- **Presentation:** interactive map + per-department entity pages; a plain search box alongside.
- **Provenance:** every body, minister, budget and staffing figure cited to a primary source.

**Deferred (out of Spiral 1, not foreclosed)**
- The arm's-length-body estate (executive agencies, NDPBs, public corporations, regulators, tribunals) — needed for full parity and for real drill-down depth.
- The **powers/duties/vetoes layer** — this is Spiral 2, the thing nobody else has.
- More officeholders (permanent secretaries, ALB chairs/CEOs).
- Devolved administrations' internal machinery (Spiral 5).

---

## 4. Parity checklist (POC-calibrated), grounded in the live benchmark

I inspected machineryofgovernment.uk directly. Its structural coverage is the full org graph — **departments, non-ministerial departments, executive agencies, executive/advisory NDPBs, public corporations, royal charter bodies, tribunals, and officials** (PM, cabinet ministers, junior ministers, civil servants, independent officials) — with classification, parent/child edges, and a **powers panel on officeholders** (e.g. the DSIT Secretary of State shows 11 powers/functions/responsibilities, each with Act citations). It carries budget and staffing on body nodes and a "data last reviewed" date.

The POC matches the **structural spine for departments only**. Explicit match/defer against the benchmark:

| Benchmark element | POC | 
|---|---|
| Ministerial departments as nodes, classified | ✅ Match |
| Ministers attached to departments | ✅ Match (ministers only) |
| Department budget + staffing | ✅ Match (department level) |
| Parent/child (sponsor) edges | ◑ Partial — department-level only; ALB edges deferred |
| Interactive map + entity pages | ✅ Match (vanilla renderer) |
| Every figure cited | ✅ Match |
| ALB / agency / public-body nodes | ⬜ Deferred (full parity / Spiral 2) |
| Officeholder powers panel | ⬜ Deferred (Spiral 2) |
| "Data last reviewed" currency stamp | ✅ Match (A2.6 field) |

**POC exit test:** for the department slice, nothing material in the benchmark's *structural* coverage is missing from ours; full-parity side-by-side (ALBs + officials' powers) is a later gate.

---

## 5. Data sources (fixed, with confirmed shapes)

| Layer | Source | Status | Notes |
|---|---|---|---|
| Body list + classification + sponsor edges + external IDs | **GOV.UK Organisations API** (`https://www.gov.uk/api/organisations`) | ✅ Confirmed reachable; 1,255 orgs, 63 pages, `page_size 20` | Gives `format` (→ body_type), `parent/child_organisations`, `govuk_status`, `analytics_identifier` + `content_id` (stable external IDs). Filter to live ministerial departments. |
| Ministers → department | GOV.UK ministers data (`/government/ministers`) | ⚠️ **Gap to close at setup** | Not in the Organisations API. Confirm a machine-readable route (content API / ministers index) or a small hand-built table for ~25 departments as fallback. |
| Budget (department level) | **HMT OSCAR** outturn; departmental Estimates/annual reports as needed | To fetch | Department-level figures only for the POC; pick one clean financial year and state it. |
| Staffing (department level) | **Civil Service Statistics** | To fetch | Department FTE/headcount; state period. |

Connectivity for OSCAR and Civil Service Statistics I will test at the start of setup, as I did for the Organisations API. If a bulk file is not sandbox-reachable, it becomes a small manual-download step for you.

---

## 6. Pre-Spiral 1 setup tasks (Annex A13.1) — sessions 1–2

Executed inside `state-machine/` in the HMG folder.

1. `git init`; create the Annex A12 folder tree (`/schemas`, `/vocab`, `/data/{bodies,sources,relationships,budgets,staffing}`, `/data/offices`, `/data/person-roles`, `/compiled`, `/site`, `/docs`, `/calibration`, `/workpacks/spiral-1`, `/issues`).
2. Copy the three governing docs + this workpack into `/docs`.
3. Write the **five core schemas** (Body, Source — plus Power/Duty/Veto left in draft for Spiral 2) and the **reduced Office + PersonRole schemas** (A4 exception), including `provision_key` / `derived_from_record_id` on the legal schemas.
4. Controlled vocabularies (`body_type`, `source_type`, `jurisdiction`, `record_status`, `legal_status`, `relationship_type`), plus a **`format` → `body_type` mapping** table from the API's values.
5. Generate `AGENT.md` from Annex A (five core rules, source hierarchy, ID conventions, session output contract).
6. Empty `manifest.json`; empty `/calibration/confidence_log.csv`.
7. `validate.py` — plain Python, stdlib `json` + `jsonschema`: schema validation, ID checks, source-link presence, vocab checks, and the `provision_key` duplicate check.
8. **Three hand-built body records** to test the schema: one ministerial department, one statutory regulator, one advisory/low-power body (per A18).
9. Run validation; revise schemas before scaling. Human review template into `/docs`.

**Gate:** setup is done when the three hand-built records validate clean and `AGENT.md` reflects the annex.

---

## 7. Spiral 1 build tasks (ordered) — sessions 3–5, to the A13.2 exit

1. **Ingest** the Organisations API (`ingest_organisations.py`): page through all 63 pages, cache raw JSON to `/data/sources`, create a SourceRecord for the API pull with `accessed_date`.
2. **Transform** live ministerial departments → Body records (stable `uk-state-body-{slug}`, external IDs stored, classification via the format map, `record_status: extracted`).
3. **Sponsor edges** among the department set → Relationship records from `parent/child_organisations`.
4. **Ministers** → Office + PersonRole records attached to departments (from the confirmed ministers source).
5. **Budget** records (department, chosen FY, cited to OSCAR/Estimates).
6. **Staffing** records (department, chosen period, cited to Civil Service Statistics).
7. **Compile** (`compile.py`): emit `/compiled/graph.json`, `/compiled/state_machine.sqlite`, updated `manifest.json`.
8. **Map face** (`/site`): vanilla static page rendering `graph.json` — department nodes, ministers, drill to per-department entity page (classification, ministers, budget, staffing, every figure linked to its source). Search box alongside. GDS *principles*, no restricted brand assets; "not affiliated with HM Government" line.
9. **Verify:** 30 spot-checks against source; calibration log populated; side-by-side vs the benchmark's department layer.
10. **Package:** session review packs (A11.5), small commits (A11.6). Push to personal GitHub as the single Spiral 1 push at exit.

---

## 8. Forward-compatibility — what keeps later spirals open

- **Schemas built general, populated narrow.** Full entity list anticipated in naming/IDs (A4); only the five core + reduced Office/PersonRole leave draft. Adding ALBs, powers, more officials or devolved bodies is additive, no rework.
- **Stable data contract.** Presentation reads `graph.json`/SQLite; swapping the vanilla renderer for Cytoscape later touches only `/site`.
- **The thin-sponsor-layer consequence is understood and accepted.** Departments-only leaves a shallow graph (little to drill through, since sponsor edges mostly point to the deferred ALBs). This is the known cost of the lean POC; it under-demonstrates drill-down but proves the plumbing. Widening to one department's ALBs later restores depth cheaply.

---

## 9. Risks specific to Spiral 1

| Risk | Mitigation |
|---|---|
| Ministers not machine-readable | Confirm source at setup; hand-built ~25-row table as fallback (small, verifiable) |
| OSCAR/Civil Service Statistics not sandbox-reachable | Test early; fall back to a one-off manual download you provide |
| Sandbox is ephemeral between sessions | Repo lives in the HMG folder (persistent), not scratch; commit every session |
| Shallow demo under-sells the idea at pitch | Accepted for now; flagged; one deep branch is the cheap fix when you want it |
| Name + official styling imply an official product | Provisional public name to Spiral 4; GDS principles not brand; explicit non-affiliation line |

---

## 10. Open items needing you before setup

1. **Confirm the name split** — "His Majesty's Government" as internal/working name, public name locked at Spiral 4? Or publish under it verbatim (I'll note the risk and proceed either way).
2. **Sign off this scope** as the Spiral 1 definition (POC subset, not full parity).
3. **On sign-off I will:** log the §2 decisions into the plan's register, soften the recusal caveat in `CLAUDE.md` to match your ruling, then either hand you the plan or (your call) roll into setup session 1.

---

## 11. Files this workpack anticipates creating (at setup, not yet)

`state-machine/` repo tree per §6; nothing outside the HMG folder. Full created-file list will be reported at each session end (your global rule).
