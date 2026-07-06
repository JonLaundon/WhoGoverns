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

After any step, validate from the repo root:

    py -3 validate.py

`validate.py` stays at the repo root as the canonical, every-session entry point
(referenced in `AGENT.md` and the handoff guide).

Raw API responses are cached under `data/sources/raw/` (gitignored) and are
reproducible by re-running steps 1 and 5; only the curated SourceRecords are committed.
