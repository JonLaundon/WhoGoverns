# AGENT.md — WhoGoverns build agent boot digest

You are contributing to **WhoGoverns** (working name "The State Machine"), an open, machine-readable model of the UK state. Load this at the start of every session. It is the operational digest of Annex A; Annex A is authoritative and consulted on demand. A digest that drifts from the annex is a defect. Regenerate this file whenever Annex A changes.

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
Body, Source, Office, PersonRole, Relationship are populated in Spiral 1 (full structural graph). Budget, Staffing exist but are a deferred bolt-on. Power/Duty/Veto are DRAFT (Spiral 2) — do not populate.

## Spiral 1 scope (v0.2, structure-first)
Every LIVE UK public body (all types) from the GOV.UK Organisations API, classified, with sponsor/parent relationships and ministers on departments, as a Cytoscape map. Budgets/staffing deferred; powers/vetoes are Spiral 2.

## Confidence (A9.3) — conservative
0.95–1.00 explicit text + exact citation · 0.80–0.94 minor interpretation · 0.60–0.79 classification uncertain · 0.40–0.59 uncertain · <0.40 no record, log issue. Nothing below 0.80 publishes without human review. Log every verification as (predicted_confidence, outcome) in `calibration/confidence_log.csv`.

## Session output contract (A11.5)
End every session with: records created; records changed; records rejected; uncertainties; schema questions; sources used; recommended next action. Validate (`python3 validate.py`), then a small explainable commit (A11.6). No session leaves the repo broken.

## Do not
Confuse influence with legal authority; guidance with law; a consultation duty with a veto. Do not invent vocabulary. Do not write analysis into `/data`.
