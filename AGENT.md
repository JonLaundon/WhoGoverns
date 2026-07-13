# AGENT.md — WhoGoverns build agent boot digest

You are contributing to **WhoGoverns** (working name "The State Machine"), an open, machine-readable model of the UK state. Load this at the start of every session. It is the operational digest of Annex A; Annex A is authoritative and consulted on demand. A digest that drifts from the annex is a defect. Regenerate this file whenever Annex A changes. **Reflects Annex A v0.4 (06 Jul 2026).**

## The five core rules (Annex A19)
1. No uncited legal authority.
2. No unvalidated record.
3. No uncontrolled vocabulary drift.
4. No publication without verification.
5. No analysis inside the raw data layer.

## Sponsor discipline
Official / primary sources only. Commit nothing until official information is surfaced. Never use tacit knowledge. Structural and statutory-powers modelling from public sources does not engage the PfB recusal.

## Source hierarchy (top wins)
- Powers/duties/vetoes: current consolidated legislation (legislation.gov.uk) > commencement/amendment SIs > directions/delegation schemes > framework docs > annual reports > guidance > third-party (discovery only).
- Body existence/classification: GOV.UK Organisations API > Cabinet Office Public Bodies > departmental annual reports > framework docs > legislation.
- Budget: HMT OSCAR outturn > departmental accounts > body accounts > Estimates.
- Staffing: Civil Service Statistics > body annual reports > departmental reports > transparency returns.

## ID conventions
- Body: `uk-state-body-{slug}`
- Source: `source-{source_type}-{short_title}-{year}` (datasets: `source-official-dataset-{slug}`)
- Power/Duty/Veto: `{type}-{body_slug}-{source_slug}-{provision_slug}-{seq}`
- Every legal record carries `provision_key` (shared per provision) and `derived_from_record_id` (null on the canonical record). Two canonical records may not share a `provision_key`.

## Active schemas (Spiral 1)
Body, Source, Office, PersonRole, Relationship are populated in Spiral 1 (full structural graph). **Budget is now populated** (Spiral 1 bolt-on): HMT OSCAR 2024-25 outturn → net/gross resource/capital DEL + AME + TME + by-programme (COFOG), 132 major bodies, `ingest_budget.py`; amounts GBP, cited to the OSCAR SourceRecord; `programme`/`basis` fields added to the schema. **Staffing is now populated** (Civil Service Statistics 2025, at 31 Mar 2025): total + by-grade (SCS/G6-7/SEO-HEO/EO/AA-AO) + by-profession, headcount and FTE, 77 bodies, `ingest_staffing.py`; `grade`/`profession` fields added. Department 'Overall' rows = GROUP total (incl agencies) carrying a double-count disclaimer; agencies also held separately, so never sum a department with its agencies. Power/Duty/Veto are DRAFT (Spiral 2) — do not populate. Budget/staffing match OSCAR/CSS organisation names by EXACT normalised name, or safe containment (body + legal-form suffix); never fuzzy/overlap (mis-maps — see refine_classification). **Storage: ONE ARRAY FILE PER TYPE** (`data/<type>.json` — bodies, relationships, offices, person-roles, sources, budgets, staffing). All data access goes through `pipeline/store.py` (`load`/`load_map`/`save`/`upsert`, keyed by each type's primary key). Raw API caches under `data/sources/raw/` stay individual files (gitignored). ~1,858 per-record files → 7 arrays (Annex A2.7 amended 2026-07-13). Never add per-record files or re-glob `data/<folder>/*.json` — read/write via store.

## Body taxonomy (v0.2) and officials
`body_type` (10 terms): ministerial_department, non_ministerial_department, executive_agency, division_directorate, executive_ndpb, advisory_ndpb, tribunal, public_corporation, royal_charter_body, other_body. No `regulator` (regulation is a function, not a type). `royal_charter_body` is NOT from the GOV.UK API (separate Privy Council tranche). Classify from `vocab/govuk_format_to_body_type.json` v0.2; unmapped `format` → `other_body` + review flag, never dropped.

**Functional axis (Spiral 1.5).** `functions[]` on Body is a SECOND, multi-valued axis orthogonal to `body_type` (a grouping like "regulator" cross-cuts four body_types, so it is a function not a form — decision #12 stands). Vocab `functions.json` v0.1. Populated: `regulation` only, from the DBT List of UK regulators, exact-match, cited via `function_source_ids`. Never tag a function from tacit knowledge — source it or leave it.

**Off-register tranche (Spiral 1.5).** Bodies outside the GOV.UK Organisations API (`ingest_offregister.py`): `royal_charter_body` is now POPULATED (5 chartered bodies, sourced to the Privy Council register — 8th outer ring on the map); plus 17 independent statutory regulators as `other_body`+flag+`functions:["regulation"]` (health/legal professional regulators etc.), sourced to the DBT list. Scope = statutory-function test (exclude private/voluntary chartered institutes). Chartered bodies already on GOV.UK (BBC, Bank of England, British Council) keep their API classification — not re-added.

**Officials are not a body_type.** Office is a first-class, power-holding node (a corporation sole: "the Secretary of State may…"). In Spiral 2, Power/Duty/Veto carry a polymorphic holder — `holder_type` (`office`|`body`), `office_id` when an office holds it, `body_id` the holder or hosting department. The map is office-centred: PM → Cabinet → ministers → departments → agencies/ALBs.

## Spiral 1 scope (v0.2, structure-first)
Every LIVE UK public body (all types) from the GOV.UK Organisations API, classified, with sponsor/parent relationships and ministers on departments, as a Cytoscape map. Budgets/staffing deferred; powers/vetoes are Spiral 2.

## Confidence (A9.3) — conservative
0.95–1.00 explicit text + exact citation · 0.80–0.94 minor interpretation · 0.60–0.79 classification uncertain · 0.40–0.59 uncertain · <0.40 no record, log issue. Nothing below 0.80 publishes without human review. Log every verification as (predicted_confidence, outcome) in `calibration/confidence_log.csv`.

## Session output contract (A11.5)
End every session with: records created; records changed; records rejected; uncertainties; schema questions; sources used; recommended next action. Validate (`python3 validate.py`), then a small explainable commit (A11.6). No session leaves the repo broken.

## Do not
Confuse influence with legal authority; guidance with law; a consultation duty with a veto. Do not invent vocabulary. Do not write analysis into `/data`.
