# Session review pack (Annex A11.5)

**Session date:** 2026-07-06
**Task:** Build the senior-officials tranche (non-ministerial dept heads + departmental
permanent secretaries), reclassified from Spiral 5 to now (they hold Spiral-2 powers).

## Records created
- **34 Office + 34 PersonRole records** via `pipeline/ingest_officials.py` (stdlib + openpyxl; no network).
  - **17 `independent_official`** — heads/accounting officers of non-ministerial departments (CPS→Stephen Parkinson, CMA→Sarah Cardell, UK Statistics Authority→Sir Ian Diamond, …), from the Cabinet Office Public Bodies Directory.
  - **17 `civil_servant`** — departmental permanent secretaries (HM Treasury→James Bowler, MoD→Jeremy Pocklington, …), from the GOV.UK content-API board members (already cached).

## Records changed
- None. Recompiled `graph.json`/SQLite: office nodes now include the two officials rings.

## Uncertainties / skipped (9, logged by the script)
- **Non-min dept heads not matched (3):** Ofgem, The Charity Commission, UK Supreme Court — name variations vs the CO directory; refine the match or add aliases.
- **Perm secs not found (6):** Attorney General's Office, Advocate General for Scotland, both House Leaders' offices, Scotland Office, UK Export Finance — small offices/law-officer/whip/territorial bodies with no distinct "Permanent Secretary" board member (some share a perm sec or have a CEO). Legitimate gaps.
- Non-min dept head **office title** is generic ("Head of X"); the precise statutory titles (DPP, Comptroller & Auditor General, National Statistician) can be refined later. Classification `independent_official` vs `civil_servant` is a first-pass rule.

## Schema questions
- None. `office_type` already had `civil_servant`/`independent_official`; the ring (level 4), legend and detail panel already supported them.

## Validation result
`py -3 validate.py` — **1623 records, 0 errors, 0 warnings.**

## Decision logged
Plan decision register **#14** (2026-07-06): officials pulled forward from Spiral 5 — first
tranche now (structure), powers in Spiral 2; deeper senior-civil-service graph (organograms) stays Spiral 5.

## Recommended next action
Sponsor review of the tranche; then the Spiral-2 powers register (the office-holders now exist to carry powers).
