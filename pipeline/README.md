# pipeline/

`store.py` is the shared data-access layer: each data type is one `data/<type>.json` array
file, read/written via `store.load / load_map / save / upsert`. Every script below goes
through it (raw API caches under `data/sources/raw/` stay individual files, gitignored).

The build scripts, in run order. Each is stdlib-only, one job, runnable standalone
from a clean checkout, and idempotent. Run from the repo root with `py -3 pipeline/<script>.py`
(on this Windows host the launcher is `py -3`; see `issues/build-environment.md`).
Most accept `--dry-run` to report without writing.

| # | Script | Reads | Writes | Network |
|---|---|---|---|---|
| 1 | `ingest_organisations.py` | GOV.UK Organisations API | raw cache + Organisations SourceRecord | yes |
| 2 | `transform_bodies.py` | raw cache | `data/bodies/` (classified) | no |
| 3 | `transform_relationships.py` | raw cache + `data/bodies/` | `data/relationships/` + fills body sponsor/parent | no |
| 4 | `enrich_aliases.py` | raw cache + `data/bodies/` | old-name aliases onto live successors | no |
| 5 | `ingest_ministers.py` | `data/bodies/` + GOV.UK content API | `data/offices/`, `data/person-roles/` + content SourceRecord | yes |
| 6 | `compile.py` | all of `data/` | `compiled/graph.json`, `compiled/state_machine.sqlite`, `manifest.json` | no |

Refinement / enrichment passes run after `transform_bodies` and before `compile` (each
create-if-absent or write-only-on-change, so re-running is safe):
`refine_classification.py` (Cabinet Office rank-2 body_type), `refine_sponsors.py` (CO
sponsor cross-check), `ingest_officials.py` (dept heads + perm secs).

Spiral 1.5 added two more, also before `compile`:

| Script | Reads | Writes | Network |
|---|---|---|---|
| `refine_functions.py` | DBT List of UK regulators (cached ODS) + `data/bodies/` | `functions:["regulation"]` + `function_source_ids` on matched bodies | no |
| `ingest_offregister.py` | curated table (in-script) | 22 off-register `data/bodies/` (5 royal_charter_body + 17 statutory-regulator other_body) + charter/DBT SourceRecords | no |

Budget/staffing bolt-on (Annex A13.2), run after the bodies exist:

| Script | Reads | Writes | Network |
|---|---|---|---|
| `ingest_budget.py` | HMT OSCAR outturn xlsx (cached) + `data/bodies/` | `data/budgets/` — net/gross DEL/AME + by-programme, matched bodies | no |
| `ingest_staffing.py` | Civil Service Statistics ODS (cached) + `data/bodies/` | `data/staffing/` — total + by-grade + by-profession, headcount/FTE | no |

Spiral 2 — the powers layer (Annex A6). Structural half is rule-based (no LLM); the
operative records are hand-built from the cached text, then compiled onto the map:

| Script | Reads | Writes | Network |
|---|---|---|---|
| `fetch_legislation.py` | legislation.gov.uk CLML per section | `data/sources`, `data/instruments`, `data/provisions` (+ mines `Provision.references` from the operative text) | yes |
| `extract_wia1991_water.py` | cached WIA 1991 text | first Water powers/duties/vetoes (calibration slice) | no |
| `extract_wia1991_licensing.py` | cached WIA ss.17A+ text | the water supply/sewerage licensing regime (2 SoS gates on Ofwat) | no |
| `extract_wia1991_s16.py` | cached WIA s.16 | the duty the CMA's s.16A veto blocks (breadcrumb tie-out) | no |
| `extract_wra1991_ea*.py`, `extract_wca1981_ne.py`, `extract_wia1991_{cma_ccw,dwi,sar_gaps,sweep,s2}.py` | cached text | cross-body + retrodiction records | no |
| `audit_veto_strength.py` | `data/vetoes` | applies the strength audit + logs calibration; idempotent | no |
| `audit_duty_counterparty.py` | `data/duties` | fills `owed_to_*` where a duty runs to a state actor | no |
| `breadcrumbs.py` | all operative data | `issues/breadcrumbs.md` — the derived completeness register (run after any extraction) | no |

`compile.py` (step 6 above) reads the operative layer too: it attaches card-ready
powers/duties/vetoes to each holder node, emits `can_veto` and `must_consult` edges, and
builds the powers/duties/vetoes/instruments/provisions SQLite tables. Re-run it after any
extraction, then run `validate.py` and `breadcrumbs.py`.

After any step, validate from the repo root:

    py -3 validate.py

`validate.py` stays at the repo root as the canonical, every-session entry point
(referenced in `AGENT.md` and the handoff guide).

Raw API responses are cached under `data/sources/raw/` (gitignored) and are
reproducible by re-running steps 1 and 5; only the curated SourceRecords are committed.
