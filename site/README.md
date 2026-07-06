# site/

The public map face — a static, dependency-light page that reads `compiled/graph.json`
and renders the office-centred state graph with search and a per-entity details panel.

## Run
Served, not opened as a file (the page fetches `../compiled/graph.json`, which browsers
block over `file://`). From the **repo root**:

    py -3 -m http.server 8000
    # then open http://127.0.0.1:8000/site/

Regenerate the data it reads with `py -3 pipeline/compile.py`.

## Files
- `index.html` — structure, header/disclaimer, search, filters, legend, details panel, footer.
- `style.css` — civic-minimal styling on GDS *principles* (system fonts; no GDS Transport font or Crown logo — those are restricted assets).
- `app.js` — loads the graph, builds the Cytoscape view, drives search (name + alias + minister), focus and the details panel where every claim links to its source.

## Notes
- One runtime dependency: Cytoscape.js, pinned, from a CDN (`index.html`).
- Layout is `concentric`, office-centred: the Prime Minister sits at the centre, then
  cabinet, ministerial departments, and the wider ALB/other rings outward.
- Accessibility: the canvas is backed by a keyboard-navigable search and a text details
  panel; colours carry high contrast and are paired with node shape (bodies = circles,
  offices = diamonds) and a legend, not colour alone.
- Not affiliated with HM Government; every claim cites its official source.
