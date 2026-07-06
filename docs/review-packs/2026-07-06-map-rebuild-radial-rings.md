# Session review pack (Annex A11.5)

**Session date:** 2026-07-06
**Agent / operator:** WhoGoverns build agent (Claude Code, host-side)
**Task stated at start:** Rebuild the map to the machineryofgovernment.uk look — 7 concentric
rings in a fixed order, MoG colours/shapes, and hover-to-show-title-and-links. (Sponsor
directed this after playing with MoG; the previous hierarchy default was the wrong shape.)

## Records created / changed
- `site/app.js`, `site/index.html`, `site/style.css` — rebuilt map. No `data`/schema/compiled change.

## What changed (informed by actually driving MoG in Chrome)
- **Radial sunburst, 7 rings, fixed evenly-stepped radii** (a custom preset — Cytoscape's
  concentric balloons a crowded ring). Order, centre → rim, per sponsor's spec:
  1 PM · 2 cabinet · 3 junior/under-secretaries · 4 independent officials (empty until Spiral 5)
  · 5 ministerial + non-ministerial departments · 6 agencies + divisions · 7 public bodies.
- **Radial spokes:** each ring is sorted by the node's *home department*, so a department and
  its ministers/agencies/bodies line up on the same spoke (Defra's ~35 bodies cluster together).
- **MoG-style colours + shapes:** officials = circles (PM dark red → cabinet red → junior pink;
  civil servant blue, independent official green — last two reserved for Spiral 5), departments
  = rounded squares, NDPBs/tribunals = diamonds, other bodies = squares. Legend regrouped into
  Officials / Departments / Public bodies to match.
- **Hover = title + links:** hovering a node shows a tooltip (title · type · N links) and
  highlights its whole link chain (department → ministers inward, sponsored bodies outward),
  fading other edges. Verified in-browser (Defra: 41 links; DWP: 21).
- **Rings is now the default layout;** the top-down Hierarchy is kept as a toggle.

## Not done yet (observed on MoG — candidate enhancements)
- **Rotation on select** so the chosen node's spoke swings to a canonical position (MoG does this).
- Category filter panel, "Territory"/nations view, dark mode, help overlay, click-to-pin.
- Populating the empty officials rings (civil servants / independent officials) — Spiral 5.

## Validation result
`py -3 validate.py` — **1553 records, 0 errors, 0 warnings** (presentation only; no records touched).

## Recommended next action
R1b (CO sponsor-link refinement) this session; then decide which MoG-parity enhancements to add.
