# Session review pack (Annex A11.5)

**Session date:** 2026-07-06
**Agent / operator:** WhoGoverns build agent (Claude Code, host-side)
**Task stated at start:** Refine **R3** — office-centred layering so the map reads top-down
PM → cabinet → junior → department → ALB (people → machines).

## Records created / changed
- `site/index.html` — a **Layout** control (Hierarchy / Rings).
- `site/app.js` — a top-down **tiered "hierarchy" layout** and a layout switcher.
- No `data/`, schema, or compiled changes (layout is client-side).

## What R3 does
- **Hierarchy (default):** a tiered preset — the *people* on top as an org chart
  (PM band → cabinet band → junior band → other-offices band, wired by the R2 `leads`
  edges), and the *machines* (663 bodies) in a grid below, grouped and colour-banded by
  `body_type` (ministerial dept → non-ministerial → agency → NDPB → … → other). Reads
  people → machines top to bottom.
- **Rings:** the original concentric office-centred overview, retained as a toggle for the
  whole-state view.
- The empty `independent_official` tier is where senior officials will sit at Spiral 5.

## Why not breadthfirst
A directed breadthfirst from the PM collapsed to a thin line — one rank holds ~560 bodies,
so an edge-following tree is 4 ranks tall and hundreds wide. The tiered preset controls the
bands explicitly and stays readable (zoom/pan for the body grid).

## Verified in-browser
Hard-reloaded; the hierarchy renders PM apex → cabinet → junior → other → body grid, with
`leads` edges visible at the top and bodies colour-banded by type. Layout toggle works. No
console errors.

## Validation result
`py -3 validate.py` — **1553 records, 0 errors, 0 warnings** (R3 touches no records).

## Recommended next action
Functionality + node-link comparison vs machineryofgovernment.uk (this session, separate
note), then task 8 (package/push).
