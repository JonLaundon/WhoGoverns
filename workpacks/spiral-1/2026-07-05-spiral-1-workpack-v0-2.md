# Spiral 1 Workpack — v0.2 (structure-first) — signed off

**Project:** WhoGoverns (working name "The State Machine")
**Date:** 2026-07-05
**Supersedes:** v0.1 (departments-only POC). v0.1 retained as historical record.
**Governs:** Spiral 1 only. Binds to Project Plan v0.5 and Annex A v0.3.
**Status:** Signed off by sponsor 2026-07-05. Pre-Spiral 1 setup complete; build not yet started.

> Reviewer note: a planning artefact. Nothing here adopts a policy position; it fixes what Spiral 1 builds.

---

## 1. What changed from v0.1, and why

v0.1 scoped a lean POC: ~25 ministerial departments only, with budgets and staffing. Sponsor reshaped it: **map the whole structural graph of the state first, defer budgets and staffing to a later bolt-on.** Rationale — the GOV.UK Organisations API returns every body, its classification and its parent/child links in one download, so mapping all bodies is barely more work than filtering to departments, and it is the structure (not the finance numbers) that makes the map navigable. Budgets and staffing are per-body attributes that attach later without touching the graph. Powers and vetoes remain Spiral 2.

**Renderer decision also reversed:** a whole-state graph is hundreds of nodes, so Spiral 1 adopts **Cytoscape.js** (the benchmark's graph library) now, rather than the vanilla renderer v0.1 proposed for 24 nodes.

---

## 2. Fixed Spiral 1 scope (v0.2)

**In scope**
- **Bodies:** every **live** UK public body from the GOV.UK Organisations API — all types: ministerial and non-ministerial departments, executive agencies, executive and advisory NDPBs, public corporations, tribunals, and the "other/sub-organisation" tail. Filter to live/active (`govuk_status` live or exempt); exclude closed/superseded except as historical links.
- **Classification:** `body_type` for every body, via the GOV.UK `format` → `body_type` map.
- **Relationships:** sponsor/parent edges across the whole set, from the API's `parent_organisations` / `child_organisations`.
- **Officeholders:** ministers attached to departments (from the GOV.UK content API `role_appointments`). Minister layer only; senior officials deferred.
- **Presentation:** an interactive **Cytoscape** map — whole-state → sector/parent → body — with a per-body entity page and a search box. GDS *principles* (accessibility, plain language, civic-minimal), no restricted Crown/GDS brand assets, explicit "not affiliated with HM Government" line.
- **Provenance:** every body, classification, relationship and minister cited to its primary source (the GOV.UK APIs).

**Deferred — bolt-on after the graph is signed off**
- Budget records (HMT OSCAR) and staffing records (Civil Service Statistics). Schemas already exist; population is a later pass.

**Deferred — Spiral 2**
- Statutory powers, duties, vetoes; the statutory "who can block whom" interactions (as opposed to the org-chart sponsor edges).

**Deferred — Spiral 5**
- Devolved administrations' internal machinery; senior officials/appointments graph.

---

## 3. Data sources (fixed, confirmed)

| Layer | Source | Status |
|---|---|---|
| All bodies + classification + parent/child edges + external IDs | GOV.UK Organisations API (`/api/organisations`, 63 pages) | ✅ Confirmed |
| Ministers → department | GOV.UK content API per organisation (`/api/content/government/organisations/{slug}` → `role_appointments`) | ✅ Confirmed present; full parse runs locally (no size cap) |
| Budget (deferred) | HMT OSCAR outturn | Bolt-on pass |
| Staffing (deferred) | Civil Service Statistics | Bolt-on pass |

---

## 4. Pre-Spiral 1 setup — COMPLETE (2026-07-05)

Repo `whogoverns/` scaffolded per Annex A13.1: Annex A12 folder tree; seven active schemas (Body, Source, Office, PersonRole, Relationship, Budget, Staffing) + Power/Duty/Veto draft stubs; vocabularies + `format`→`body_type` map; `AGENT.md`; `validate.py`; calibration log; issue logs; three official-data seed records (Cabinet Office, Ofgem, ACOBA) + the API source record. `validate.py`: 0 errors. Gate met.

---

## 5. Spiral 1 build tasks (ordered) — run in Claude Code

1. **`ingest_organisations.py`** — page through all 63 pages of the Organisations API; cache raw JSON to `data/sources`; write/refresh the SourceRecord.
2. **Bodies** — transform every live body → Body record (all types), classification via the format map, external IDs stored, `record_status: extracted`.
3. **Relationships** — `parent/child_organisations` → Relationship records (`sponsors` / parent edges) across the whole set.
4. **`ingest_ministers.py`** — for each department, fetch the content API object, read `role_appointments` → Office + PersonRole records.
5. **`compile.py`** — emit `compiled/graph.json`, `compiled/state_machine.sqlite`, refresh `manifest.json`.
6. **Map face (`/site`)** — Cytoscape reading `graph.json`: whole-state graph, node colour by `body_type`, drill to per-body entity page (classification, sponsor, ministers, every claim linked to source), search box. GDS principles; not-affiliated line.
7. **Verify** — 30 structural spot-checks against source; populate the calibration log; side-by-side vs the benchmark's structural coverage.
8. **Package** — session review packs (A11.5); commit host-side/Claude Code (A11.6); push to personal GitHub as the single Spiral 1 push at exit.

**Then (separate bolt-on):** budgets + staffing pass.

---

## 6. Exit criteria (v0.2)

Annex A13.2, structure-first reading: canonical body list covers all live bodies; body IDs stable; sponsor/parent relationships recorded; classification recorded; ministers load for departments; the graph compiles; the Cytoscape map renders with per-body entity pages; 30 spot-checks pass; side-by-side confirms nothing material in the benchmark's *structural* coverage is missing. (A13.2 items 5–6, budget/staffing, move to the bolt-on.)

---

## 7. Forward-compatibility

Schemas built general; adding budgets, staffing, more officials, powers or devolved bodies is additive. Stable compiled data contract (`graph.json`/SQLite) means the map is a swappable layer. Cytoscape scales to the Spiral 2 powers graph without a renderer change.

---

## 8. Risks (Spiral 1)

| Risk | Mitigation |
|---|---|
| The "other/sub-organisation" tail is noisy (units, historical bodies) | Filter to live; map ambiguous `format`s to `other` with a review flag; spot-check |
| Content API minister parse varies by department | Handle missing `role_appointments` gracefully; log gaps in `issues/source-gaps.md` |
| Whole-state graph is visually dense | Cytoscape layout + collapse-by-parent; entity pages carry the detail |
| Git can't run in the Cowork sandbox (OneDrive) | Build/commit in Claude Code on the host (see the handoff guide) |
