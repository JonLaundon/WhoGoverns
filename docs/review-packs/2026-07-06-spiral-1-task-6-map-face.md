# Session review pack (Annex A11.5)

**Session date:** 2026-07-06
**Agent / operator:** WhoGoverns build agent (Claude Code, host-side)
**Task stated at start:** Spiral 1 build **task 6** — the map face (`/site`): a Cytoscape
view of `compiled/graph.json`, office-centred, colour by type, per-entity detail with
source links, alias-aware search, GDS principles, not-affiliated line.

## Records created / changed
- New **static site** in `site/`: `index.html`, `style.css`, `app.js`, `README.md`.
- No `data/` or schema changes — the site reads the compiled contract only.

## What it does (verified in-browser)
- **Renders** the office-centred graph (`concentric` layout): the Prime Minister at the centre, cabinet ministers in the inner ring, ministerial departments next, ALBs/other outward. 788 nodes / 762 edges, no console errors.
- **Colour + shape by type**: bodies = circles coloured by the 10 `body_type`s; offices = diamonds coloured by the 4 office tiers; forming bodies dashed. Legend included.
- **Alias-aware search** — verified: "Ofgem" → Ofgem; "Atomic Weapons" → AWE Nuclear Security Technologies (found by its old name); "Chancellor of the Exch" → the office, with the holder shown in the result.
- **Entity panel, every claim sourced** — body view (type, status, sponsor link, parent link, GOV.UK page, "also known as" aliases, source citation); office view (current holder, in-post-since, hosted-at link, content-API source). Sponsor/parent/host/minister are cross-links that re-focus the graph.
- **Focus behaviour**: selecting fades the rest and centres the node + its neighbourhood.
- **GDS principles, no restricted assets**: system font stack (no GDS Transport), no Crown logo; high-contrast palette paired with shape + legend (not colour alone). Prominent "Not affiliated with, or endorsed by, HM Government" line; OGL attribution and compiled-timestamp in the footer.

## Uncertainties
- Whole-state view is dense by nature (788 nodes); the design leans on search + focus + the details panel for navigation (as the workpack risk table anticipated). A collapse-by-parent view could be a later refinement.
- One CDN runtime dependency (Cytoscape.js, pinned). Could be vendored locally later if fully offline/self-contained hosting is wanted.
- Accessibility: canvas is backed by keyboard-navigable search + text panel; a fuller a11y pass (focus order, ARIA live regions, reduced-motion) is a candidate refinement.

## Schema questions
- None. Presentation layer only.

## Validation result
`py -3 validate.py` — **1552 records, 0 errors, 0 warnings** (unchanged; the site touches no records). Verified live in Chrome against a local server; no console errors.

## Recommended next action
**Task 7 (verify):** 30 structural spot-checks against source, populate the calibration log,
and a side-by-side vs machineryofgovernment.uk's structural coverage. Then task 8 (package/push).
The classification-refinement pass (Cabinet Office Public Bodies data) remains queued after the
initial model, as agreed.
