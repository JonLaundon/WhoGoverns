# WhoGoverns — data repository

Open, machine-readable model of the UK state. Working name "The State Machine"; published as **WhoGoverns**. Not affiliated with HM Government.

Built to Annex A (backend baseline) of the governing plan. Boring by design: JSON records, JSON Schema validation, plain-Python scripts, SQLite compile, Git history.

## What runs, in what order
1. `python3 ingest_organisations.py` — (build session) pull the GOV.UK Organisations API into `data/sources` + `data/bodies`. *Not yet written.*
2. `python3 validate.py` — validate every record in `data/` against its schema; checks IDs, source links, provision_key duplicates.
3. `python3 compile.py` — (build session) emit `compiled/graph.json` + `compiled/state_machine.sqlite`. *Not yet written.*

## Setup
`pip install -r requirements.txt --break-system-packages`

## Layout
- `schemas/` — JSON Schemas. Body, Source, Office, PersonRole, Relationship, Budget, Staffing are **active** for Spiral 1. Power/Duty/Veto are **draft** (Spiral 2).
- `vocab/` — controlled vocabularies + the GOV.UK `format` → `body_type` map.
- `data/` — one JSON file per record.
- `compiled/` — build artefacts (git-tracked or ignored per decision #6).
- `site/` — the static map face (Spiral 1 build task).
- `docs/` — governing docs, data dictionary, review template.
- `calibration/` — confidence calibration log (mandatory from day one, A9.3).
- `issues/` — schema decisions, source gaps, uncertain records.

## Scope (Spiral 1, v0.2 structure-first)
Every live UK public body (all types) from the GOV.UK Organisations API, classified, with sponsor/parent relationships and ministers on departments, rendered as a Cytoscape map. Budgets and staffing are a deferred bolt-on; powers/vetoes are Spiral 2. See `workpacks/spiral-1/`.

## Version control note (important)
Git is **not** run inside the Cowork sandbox: the OneDrive-synced mount corrupts git's internal files (null-byte placeholders that cannot be deleted). Initialise git and commit from **your own machine** (Windows, where OneDrive + git coexist normally) or from **Claude Code**. Suggested first commit once you open the folder locally:
```
cd whogoverns
git init -b main
git add -A
git commit -m "Pre-Spiral 1 setup: schemas, vocab, AGENT.md, validation, three seed records"
```
A leftover `.git_corrupt_*` folder from the sandbox's failed init can be deleted in Explorer — it is not a valid repo.
