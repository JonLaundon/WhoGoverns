# Session review pack (Annex A11.5)

**Session date:** 2026-07-06
**Agent / operator:** WhoGoverns build agent (Claude Code, host-side)
**Task stated at start:** Spiral 1 build **task 5** — compile the record set into
`compiled/graph.json` + `compiled/state_machine.sqlite` and refresh `manifest.json`.
Sponsor also flagged the root folder was getting full → light reorg folded in.

## Records created / changed
- New **code**: `pipeline/compile.py` (data/ → graph.json + SQLite + manifest; stdlib only, no network).
- **Reorg:** the 5 build scripts moved from repo root into `pipeline/` (git-tracked renames); `REPO` path resolution and usage docstrings updated; `pipeline/README.md` added with run order. `validate.py` kept at repo root (canonical every-session entry point, referenced in AGENT.md/handoff).
- **`manifest.json`** refreshed (counts, generated timestamp, annex_a_version 0.4, graph sizes).
- **`.gitignore`**: `compiled/*.sqlite` (regenerable binary); `graph.json`/`manifest.json` committed as the data contract.
- Root `README.md` run-order section updated to point at `pipeline/`.
- No `data/` records changed — compile reads only, never writes into `data/`.

## Compiled outputs
- **`compiled/graph.json`** — office-centred graph: **788 nodes** (663 bodies + 125 offices), **762 edges** (637 sponsor + 125 office→body host). Office nodes carry the current holder (e.g. PM node → Keir Starmer, hosted at the Prime Minister's Office). This is the contract the Cytoscape map (task 6) reads.
- **`compiled/state_machine.sqlite`** — 6 tables (bodies, other_names, relationships, offices, person_roles, sources). Joins verified (cabinet ministers → holders; alias search "Atomic Weapons" → AWE Nuclear Security Technologies).

## Uncertainties
- Graph models the current live/forming state; historical/succession layer still parked (open issue).
- Office nodes host at a single body (the 23 joint roles noted in task 4); fine for the map, revisit for dual-hosting later.

## Schema questions
- None. Compile is derived output; no schema change. (Reorg is structural only.)

## Validation result
`py -3 validate.py` — **records checked: 1552 · errors: 0 · warnings: 0** (unchanged by compile — it reads only).

## Recommended next action
**Task 6 (map face, `/site`):** Cytoscape reading `compiled/graph.json` — whole-state office-centred
graph, node colour by `body_type`/`office_type`, drill to a per-body entity page (classification,
sponsor, ministers, every claim linked to source), search box (incl. aliases). GDS principles;
"not affiliated with HM Government" line. Then task 7 (verify) and task 8 (package/push).
