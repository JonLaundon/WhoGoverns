# pipeline/

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

After any step, validate from the repo root:

    py -3 validate.py

`validate.py` stays at the repo root as the canonical, every-session entry point
(referenced in `AGENT.md` and the handoff guide).

Raw API responses are cached under `data/sources/raw/` (gitignored) and are
reproducible by re-running steps 1 and 5; only the curated SourceRecords are committed.
