/* WhoGoverns map face. Reads compiled/graph.json, renders the UK state as a radial
   "sunburst" of concentric rings (PM at the centre, public bodies on the rim), and
   drives search, hover, and an entity details panel where every claim links to its
   source. Boring by design: one file, no framework, no build step.
   Serve from the repo root (py -3 -m http.server) and open /site/. */

"use strict";

// Human labels + colours per type. Palette follows the machineryofgovernment.uk
// category scheme (colours only — no data/code/design copied). Officials are circles,
// departments rounded squares, NDPBs/tribunals diamonds, other bodies squares.
const BODY_TYPES = {
  ministerial_department:      ["Ministerial department", "#e05a4f"],
  non_ministerial_department:  ["Non-ministerial department", "#4a90d9"],
  executive_agency:            ["Executive agency", "#8e6fc7"],
  division_directorate:        ["Division / directorate", "#e8917d"],
  executive_ndpb:              ["Executive NDPB", "#3fa35b"],
  advisory_ndpb:               ["Advisory NDPB", "#e6c229"],
  tribunal:                    ["Tribunal", "#e8883a"],
  public_corporation:          ["Public corporation", "#e8a13a"],
  royal_charter_body:          ["Royal charter body", "#9b6fc7"],
  other_body:                  ["Other body", "#9aa0a6"],
};
const OFFICE_TYPES = {
  prime_minister:       ["Prime Minister", "#7a1f1a"],
  cabinet_minister:     ["Cabinet minister", "#c0392b"],
  junior_minister:      ["Junior minister", "#f0a6a0"],
  independent_official: ["Independent official", "#3fa35b"],
  civil_servant:        ["Civil servant", "#4a90d9"],
  other:                ["Other office", "#b0b4b8"],
};

// Seven rings, centre → rim (higher value = nearer the centre in a concentric layout):
//   7 PM · 6 cabinet · 5 junior/under-secretaries · 4 independent officials ·
//   3 ministerial + non-ministerial departments · 2 agencies + divisions · 1 public bodies.
function level(d) {
  if (d.kind === "office") {
    return { prime_minister: 7, cabinet_minister: 6, junior_minister: 5,
             independent_official: 4, civil_servant: 4, other: 5 }[d.office_type] || 5;
  }
  const b = d.body_type;
  if (b === "ministerial_department" || b === "non_ministerial_department") return 3;
  if (b === "executive_agency" || b === "division_directorate") return 2;
  return 1; // executive/advisory NDPB, tribunal, public corp, royal charter, other body
}

function bodyShape(bt) {
  if (["ministerial_department", "non_ministerial_department", "executive_agency", "division_directorate"].includes(bt)) return "round-rectangle";
  if (["executive_ndpb", "advisory_ndpb", "tribunal"].includes(bt)) return "diamond";
  return "rectangle"; // public_corporation, royal_charter_body, other_body
}

function subOf(d) {
  return d.kind === "office"
    ? (OFFICE_TYPES[d.office_type] || OFFICE_TYPES.other)[0] + (d.holder ? " · " + d.holder : "")
    : (BODY_TYPES[d.body_type] || BODY_TYPES.other_body)[0];
}

// Layouts. "rings" is the radial sunburst (default, MoG-style). "hierarchy" is the
// top-down tiered org chart, kept as an alternative view.
function hierarchyPositions() {
  const W = 2400, pos = {};
  const band = (pred, y) => {
    const ns = cy.nodes().filter((n) => pred(n.data()));
    ns.forEach((n, i) => { pos[n.id()] = { x: W * (i + 1) / (ns.length + 1), y }; });
  };
  band((d) => d.kind === "office" && d.office_type === "prime_minister", 40);
  band((d) => d.kind === "office" && d.office_type === "cabinet_minister", 150);
  band((d) => d.kind === "office" && d.office_type === "junior_minister", 280);
  band((d) => d.kind === "office" && (d.office_type === "other" || d.office_type === "independent_official"), 400);
  const order = ["ministerial_department", "non_ministerial_department", "executive_agency",
    "executive_ndpb", "advisory_ndpb", "tribunal", "public_corporation",
    "division_directorate", "royal_charter_body", "other_body"];
  const bodies = cy.nodes().filter((n) => n.data("kind") === "body")
    .sort((a, b) => order.indexOf(a.data("body_type")) - order.indexOf(b.data("body_type")));
  const perRow = 42, dx = W / perRow, y0 = 540, dy = 46;
  bodies.forEach((n, i) => { pos[n.id()] = { x: 40 + (i % perRow) * dx, y: y0 + Math.floor(i / perRow) * dy }; });
  return pos;
}

// Radial sunburst with FIXED, evenly-stepped ring radii (unlike Cytoscape's concentric,
// which balloons the radius of a crowded ring). Each ring is sorted by the node's "home
// department" so a department and its ministers/agencies/bodies line up on the same
// radial spoke — the machineryofgovernment.uk look.
const RING_RADIUS = { 7: 0, 6: 110, 5: 190, 4: 260, 3: 340, 2: 480, 1: 760 };

function homeDeptSortKey(node, byId, deptIndex) {
  let cur = node, guard = 0;
  while (cur && guard++ < 20) {
    const d = cur.data();
    if (d.kind === "body" && (d.body_type === "ministerial_department" || d.body_type === "non_ministerial_department")) {
      return deptIndex[d.id] != null ? deptIndex[d.id] : 9999;
    }
    const next = d.kind === "office" ? d.body_id : (d.sponsor_department_id || d.parent_body_id);
    if (!next) break;
    cur = byId[next];
  }
  return 9999;
}

function ringsPositions() {
  const byId = {};
  cy.nodes().forEach((n) => { byId[n.id()] = n; });
  // Stable department order (defines the angular sectors).
  const depts = cy.nodes().filter((n) => ["ministerial_department", "non_ministerial_department"].includes(n.data("body_type")))
    .sort((a, b) => a.data("label").localeCompare(b.data("label")));
  const deptIndex = {};
  depts.forEach((n, i) => { deptIndex[n.id()] = i; });

  const byLevel = {};
  cy.nodes().forEach((n) => { const L = level(n.data()); (byLevel[L] = byLevel[L] || []).push(n); });

  const pos = {};
  Object.keys(byLevel).forEach((L) => {
    const r = RING_RADIUS[L] || 0;
    const ns = byLevel[L];
    if (r === 0) { ns.forEach((n) => { pos[n.id()] = { x: 0, y: 0 }; }); return; }
    ns.sort((a, b) => homeDeptSortKey(a, byId, deptIndex) - homeDeptSortKey(b, byId, deptIndex)
      || a.data("label").localeCompare(b.data("label")));
    ns.forEach((n, i) => {
      const ang = 2 * Math.PI * i / ns.length - Math.PI / 2;
      pos[n.id()] = { x: r * Math.cos(ang), y: r * Math.sin(ang) };
    });
  });
  return pos;
}

function makeLayout(name) {
  if (name === "hierarchy") {
    const pos = hierarchyPositions();
    return { name: "preset", positions: (n) => pos[n.id()] || { x: 0, y: 0 }, fit: true, padding: 30 };
  }
  const pos = ringsPositions();
  return { name: "preset", positions: (n) => pos[n.id()] || { x: 0, y: 0 }, fit: true, padding: 40 };
}

let cy;
let searchIndex = [];
let GENERATED = "";
let currentLayout = "rings";
let basePos = {};        // unrotated node positions of the current layout
let selectedId = null;
let currentAngle = 0;    // rotation currently applied to basePos (rings layout)
let rotAnim = null;
const $ = (sel) => document.querySelector(sel);

function runLayout(name) {
  currentLayout = name;
  if (rotAnim) { cancelAnimationFrame(rotAnim); rotAnim = null; }
  currentAngle = 0;
  cy.layout(makeLayout(name)).run();
  basePos = {};
  cy.nodes().forEach((n) => { basePos[n.id()] = { x: n.position("x"), y: n.position("y") }; });
  cy.fit(undefined, 40);
}

fetch("../compiled/graph.json")
  .then((r) => { if (!r.ok) throw new Error("graph.json not found (serve from repo root)"); return r.json(); })
  .then(init)
  .catch((err) => {
    $("#detail-empty").innerHTML =
      "<h2>Could not load the map</h2><p>" + err.message +
      "</p><p class='help'>Run <code>py -3 -m http.server</code> from the repo root and open <code>/site/</code>.</p>";
  });

function init(graph) {
  GENERATED = graph.generated || "";

  graph.nodes.forEach((n) => {
    const d = n.data;
    if (d.kind === "office") {
      d.color = (OFFICE_TYPES[d.office_type] || OFFICE_TYPES.other)[1];
      d.shape = "ellipse";
      d.size = d.office_type === "prime_minister" ? 30 : d.office_type === "cabinet_minister" ? 20 : 15;
    } else {
      d.color = (BODY_TYPES[d.body_type] || BODY_TYPES.other_body)[1];
      d.shape = bodyShape(d.body_type);
      d.size = d.body_type === "ministerial_department" ? 26
             : d.body_type === "non_ministerial_department" ? 20 : 13;
    }
    d.forming = d.status === "forming";
    const aliases = (d.other_names || []).join(" ");
    searchIndex.push({ id: d.id, label: d.label, sub: subOf(d),
      text: (d.label + " " + aliases + " " + (d.holder || "")).toLowerCase() });
  });

  cy = cytoscape({
    container: $("#cy"),
    elements: { nodes: graph.nodes, edges: graph.edges },
    wheelSensitivity: 0.2,
    style: [
      { selector: "node", style: {
        "background-color": "data(color)", "shape": "data(shape)",
        "width": "data(size)", "height": "data(size)",
        "border-width": 1, "border-color": "rgba(0,0,0,0.35)",
        "label": "", "font-size": 9, "color": "#0b0c0c",
        "text-background-color": "#fff", "text-background-opacity": 0.9,
        "text-background-padding": 2, "min-zoomed-font-size": 7,
      }},
      { selector: "node[?forming]", style: { "border-style": "dashed", "border-width": 2, "border-color": "#0b0c0c" } },
      { selector: "edge", style: {
        "curve-style": "bezier", "width": 1, "line-color": "#d3d6d8", "opacity": 0.5,
        "target-arrow-color": "#d3d6d8", "target-arrow-shape": "triangle", "arrow-scale": 0.5,
      }},
      { selector: "edge[kind = 'office_of']", style: { "line-color": "#e3b7be", "line-style": "dashed", "target-arrow-shape": "none" } },
      { selector: "edge[kind = 'leads']", style: { "line-color": "#8a1a12", "width": 1, "opacity": 0.45, "target-arrow-color": "#8a1a12", "target-arrow-shape": "triangle", "arrow-scale": 0.5 } },
      { selector: "edge.rot-hide", style: { "display": "none" } },
      { selector: ".faded", style: { "opacity": 0.08, "text-opacity": 0 } },
      { selector: "node.thread-lbl", style: { "label": "data(label)", "z-index": 95, "border-width": 2, "border-color": "#0b0c0c" } },
      { selector: "edge.thread-edge", style: { "line-color": "#0b0c0c", "opacity": 1, "width": 2.5, "z-index": 85, "target-arrow-color": "#0b0c0c", "line-style": "solid" } },
      { selector: "node.hover-hl", style: { "label": "data(label)", "z-index": 90, "border-width": 2, "border-color": "#0b0c0c" } },
      { selector: "edge.hover-hl", style: { "line-color": "#0b0c0c", "opacity": 1, "width": 2, "z-index": 80, "target-arrow-color": "#0b0c0c" } },
      { selector: "node:selected", style: { "label": "data(label)", "border-width": 3, "border-color": "#0b0c0c", "z-index": 100, "font-size": 11, "font-weight": "bold" } },
    ],
    layout: { name: "preset" },   // real layout run below, once cy exists
  });

  cy.on("tap", "node", (e) => selectNode(e.target.id()));
  cy.on("tap", (e) => { if (e.target === cy) clearFocus(); });
  cy.on("mouseover", "node", (e) => hoverNode(e.target, e));
  cy.on("mouseout", "node", () => unhover());
  cy.on("mousemove", "node", (e) => positionTooltip(e));

  runLayout("rings");
  buildLegend();
  wireControls();
  $("#counts").textContent =
    `${graph.counts.bodies} bodies · ${graph.counts.relationships} sponsor links · ` +
    `${graph.counts.offices} offices · ${graph.counts.person_roles} ministers`;
  if (GENERATED) $("#generated").textContent = "Compiled " + GENERATED.replace("T", " ");
}

/* ---------- hover: title tooltip + link highlight ---------- */
function hoverNode(node, evt) {
  highlightThread(node);       // same full thread-to-PM as a click, minus rotation/detail
  const d = node.data();
  const n = node.connectedEdges().length;
  $("#tooltip").innerHTML =
    `<strong>${esc(d.label)}</strong><br><span class="tt-sub">${esc(subOf(d))} · ${n} link${n === 1 ? "" : "s"}</span>`;
  $("#tooltip").style.display = "block";
  positionTooltip(evt);
}
function positionTooltip(evt) {
  const e = evt.originalEvent || evt;
  const t = $("#tooltip");
  t.style.left = (e.clientX + 14) + "px";
  t.style.top = (e.clientY + 14) + "px";
}
function unhover() {
  $("#tooltip").style.display = "none";
  if (selectedId) highlightThread(cy.getElementById(selectedId));
  else cy.elements().removeClass("faded thread-lbl thread-edge hover-hl");
}

/* ---------- click: golden thread + rotation + details ---------- */

// Walk the graph from a node following edges one way: "in" = towards the centre
// (sponsor department → minister → cabinet → PM), "out" = away (agencies → bodies →
// sub-bodies, the whole downstream subtree). Returns the nodes AND connecting edges.
function traverse(node, dir) {
  let acc = node;
  let frontier = node;
  for (let i = 0; i < 25; i++) {
    const step = dir === "in" ? frontier.incomers() : frontier.outgoers();
    const fresh = step.nodes().difference(acc);
    acc = acc.union(step);
    if (fresh.empty()) break;
    frontier = fresh;
  }
  return acc;
}

// Downstream tree. For most nodes this is the whole subtree away from the centre; for the
// Prime Minister it stops at the ministerial layer (cabinet + junior ministers, via 'leads'
// edges) — otherwise selecting/hovering the PM would light up the entire state.
function downstreamTree(node) {
  if (node.data("office_type") === "prime_minister") {
    const toCabinet = node.outgoers("edge[kind = 'leads']");
    const cabinet = toCabinet.targets();
    const toJunior = cabinet.outgoers("edge[kind = 'leads']");
    return node.union(toCabinet).union(cabinet).union(toJunior).union(toJunior.targets());
  }
  return traverse(node, "out");
}

// Fade everything, then light up this node's WHOLE tree in black: the golden thread up
// to the Prime Minister AND the downstream subtree (every agency and public body it
// sponsors, and theirs). Clears prior thread/hover classes first, so nothing lingers when
// the highlighted node changes (hover to a new node, or revert to the selected one).
function highlightThread(node) {
  const up = traverse(node, "in");     // node → minister → cabinet → PM
  const tree = up.union(downstreamTree(node));   // + the downstream subtree
  cy.elements().addClass("faded").removeClass("thread-lbl thread-edge hover-hl");
  tree.removeClass("faded");
  tree.addClass("thread-edge");        // every edge in the tree drawn solid black
  up.nodes().addClass("thread-lbl");   // label only the upward thread (downstream is too many)
  node.addClass("thread-lbl");
}

// Smoothly rotate the ring layout by animating an angle applied to the base positions
// (an eased requestAnimationFrame loop — not an instant jump).
function applyRotation(ang) {
  const cos = Math.cos(ang), sin = Math.sin(ang);
  cy.batch(() => cy.nodes().forEach((n) => {
    const p = basePos[n.id()];
    if (p) n.position({ x: p.x * cos - p.y * sin, y: p.x * sin + p.y * cos });
  }));
}
function animateRotation(target, duration) {
  let delta = target - currentAngle;
  while (delta > Math.PI) delta -= 2 * Math.PI;
  while (delta < -Math.PI) delta += 2 * Math.PI;   // take the short way round
  if (Math.abs(delta) < 0.002) { currentAngle = target; return; }
  const start = currentAngle, t0 = performance.now(), dur = duration || 650;
  if (rotAnim) cancelAnimationFrame(rotAnim);
  // Hide edges while nodes move: otherwise all ~890 bezier edges recompute every
  // frame and lock the renderer. They reappear (rendered once) when rotation settles.
  cy.edges().addClass("rot-hide");
  function step(now) {
    const k = Math.min(1, (now - t0) / dur);
    const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;  // ease-in-out
    currentAngle = start + delta * e;
    applyRotation(currentAngle);
    if (k < 1) { rotAnim = requestAnimationFrame(step); }
    else { currentAngle = start + delta; rotAnim = null; cy.edges().removeClass("rot-hide"); }
  }
  rotAnim = requestAnimationFrame(step);
}
// Stand the node's spoke vertical, node at the BOTTOM — so its golden thread runs UP to
// the PM (nearer the centre) and its downstream bodies fan DOWN to the rim, stacking the
// tree top-to-bottom PM → … → node → bodies (the MoG reading).
function rotateToTop(node) {
  const b = basePos[node.id()];
  if (!b || (b.x === 0 && b.y === 0)) return;     // PM sits at the centre: nothing to rotate
  animateRotation((Math.PI / 2) - Math.atan2(b.y, b.x), 650);
}

function selectNode(id) {
  const node = cy.getElementById(id);
  if (node.empty()) return;
  selectedId = id;
  $("#tooltip").style.display = "none";
  highlightThread(node);
  cy.$(":selected").unselect();
  node.select();
  renderDetail(node.data());
  if (currentLayout === "rings") rotateToTop(node);
  else cy.animate({ center: { eles: node }, zoom: Math.max(cy.zoom(), 1.0) }, { duration: 250 });
}

function clearFocus() {
  selectedId = null;
  $("#tooltip").style.display = "none";
  cy.elements().removeClass("faded hover-hl thread-lbl thread-edge");
  cy.$(":selected").unselect();
  if (currentLayout === "rings") animateRotation(0, 500);   // rotate back smoothly
  $("#detail-body").hidden = true;
  $("#detail-empty").hidden = false;
}

/* ---------- details panel ---------- */
function renderDetail(d) {
  const el = $("#detail-body");
  el.innerHTML = d.kind === "office" ? officeHtml(d) : bodyHtml(d);
  el.hidden = false;
  $("#detail-empty").hidden = true;
  el.querySelectorAll("[data-goto]").forEach((b) =>
    b.addEventListener("click", () => selectNode(b.getAttribute("data-goto"))));
}
function nodeLabel(id) { const n = cy.getElementById(id); return n.empty() ? id : n.data("label"); }
function gotoBtn(id) {
  if (!id || cy.getElementById(id).empty()) return id ? esc(id) : "—";
  return `<button class="linkish" data-goto="${esc(id)}">${esc(nodeLabel(id))}</button>`;
}
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

function bodyHtml(d) {
  const type = (BODY_TYPES[d.body_type] || BODY_TYPES.other_body)[0];
  const govuk = d.govuk_slug ? `https://www.gov.uk/government/organisations/${d.govuk_slug}` : null;
  const ministers = cy.nodes().filter((n) => n.data("kind") === "office" && n.data("body_id") === d.id);
  let mins = "";
  if (ministers.length) {
    mins = "<h3>Ministers &amp; offices</h3><ul>" + ministers.map((o) =>
      `<li><button class="linkish" data-goto="${esc(o.id())}">${esc(o.data("label"))}</button>` +
      (o.data("holder") ? ` — ${esc(o.data("holder"))}` : "") + "</li>").join("") + "</ul>";
  }
  const aliases = (d.other_names || []).length
    ? `<h3>Also known as</h3><ul>${d.other_names.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>` : "";
  const flag = d.needs_review ? ` <span class="flag" title="Classified from the API format field; flagged for a finer human pass">classification: review</span>` : "";
  return `
    <p class="kicker">${esc(type)}${flag}</p>
    <h2>${esc(d.label)}</h2>
    <dl>
      <dt>Status</dt><dd>${esc(d.status)}${d.forming ? " (in formation)" : ""}</dd>
      <dt>Sponsor</dt><dd>${gotoBtn(d.sponsor_department_id)}</dd>
      ${d.parent_body_id ? `<dt>Parent</dt><dd>${gotoBtn(d.parent_body_id)}</dd>` : ""}
      <dt>On GOV.UK</dt><dd>${govuk ? `<a href="${esc(govuk)}" rel="noopener" target="_blank">gov.uk page ↗</a>` : "—"}</dd>
    </dl>
    ${mins}
    ${aliases}
    <h3>Source</h3>
    <p class="src">Existence, classification and sponsor relationship from the
      <a href="https://www.gov.uk/api/organisations" rel="noopener" target="_blank">GOV.UK Organisations API</a>
      and the Cabinet Office Public Bodies Directory (Open Government Licence v3.0). Ministers from the GOV.UK content API.</p>`;
}

function officeHtml(d) {
  const type = (OFFICE_TYPES[d.office_type] || OFFICE_TYPES.other)[0];
  return `
    <p class="kicker">${esc(type)} · office</p>
    <h2>${esc(d.label)}</h2>
    <dl>
      <dt>Current holder</dt><dd>${esc(d.holder || "—")}</dd>
      ${d.holder_since ? `<dt>In post since</dt><dd>${esc(d.holder_since)}</dd>` : ""}
      <dt>Hosted at</dt><dd>${gotoBtn(d.body_id)}</dd>
      ${d.holder_count > 1 ? `<dt>Holders</dt><dd>${d.holder_count}</dd>` : ""}
    </dl>
    <h3>Source</h3>
    <p class="src">Appointment from the GOV.UK content API
      (<code>ordered_ministers → role_appointments</code>), Open Government Licence v3.0.
      Office type is a heuristic tier; PM→cabinet→junior links are derived by convention.</p>`;
}

/* ---------- legend ---------- */
function buildLegend() {
  const pick = (keys, map) => keys.map((k) => [map[k][0], map[k][1]]);
  const rows = (title, entries, cls) => `<h3>${title}</h3>` + entries.map(([label, color]) =>
    `<div class="row"><span class="swatch ${cls}" style="background:${color}"></span>${esc(label)}</div>`).join("");
  $("#legend").innerHTML =
    rows("Officials", pick(["prime_minister", "cabinet_minister", "junior_minister", "independent_official", "civil_servant"], OFFICE_TYPES), "office") +
    rows("Departments", pick(["ministerial_department", "non_ministerial_department", "executive_agency", "division_directorate"], BODY_TYPES), "dept") +
    rows("Public bodies", pick(["executive_ndpb", "advisory_ndpb", "tribunal", "public_corporation", "royal_charter_body", "other_body"], BODY_TYPES), "pub") +
    `<h3>Links</h3>` +
    `<div class="row"><span class="swatch" style="background:none;border-top:2px solid #d3d6d8;height:0;border-radius:0"></span>sponsors</div>` +
    `<div class="row"><span class="swatch" style="background:none;border-top:2px solid #8a1a12;height:0;border-radius:0"></span>leads (PM → cabinet → junior) <span class="flag" style="margin-left:4px">derived</span></div>`;
}

/* ---------- search + controls ---------- */
// Rank matches so an exact/prefix name hit wins over a mere substring: "Ministry of
// Defence" resolves to MoD itself, not to some body whose text merely contains it.
function searchMatches(q) {
  return searchIndex
    .filter((r) => r.text.includes(q))
    .map((r) => {
      const l = r.label.toLowerCase();
      const score = l === q ? 0 : l.startsWith(q) ? 1 : l.includes(q) ? 2 : 3;
      return { r, score };
    })
    .sort((a, b) => a.score - b.score || a.r.label.length - b.r.label.length)
    .map((s) => s.r)
    .slice(0, 14);
}

function wireControls() {
  const input = $("#search-input");
  const results = $("#search-results");

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    results.innerHTML = "";
    if (q.length < 2) return;
    const matches = searchMatches(q);
    results.innerHTML = matches.map((m, i) =>
      `<li role="option" data-id="${esc(m.id)}" ${i === 0 ? 'aria-selected="true"' : ""}>` +
      `${esc(m.label)}<div class="r-sub">${esc(m.sub)}</div></li>`).join("");
    results.querySelectorAll("li").forEach((li) =>
      li.addEventListener("click", () => selectNode(li.getAttribute("data-id"))));
  });
  input.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    const q = input.value.trim().toLowerCase();      // recompute now — never a stale list
    if (q.length < 2) return;
    const m = searchMatches(q);
    if (m.length) { e.preventDefault(); selectNode(m[0].id); }
  });

  $("#toggle-offices").addEventListener("change", applyFilters);
  $("#toggle-forming").addEventListener("change", applyFilters);
  document.querySelectorAll("input[name='layout']").forEach((r) =>
    r.addEventListener("change", (e) => { clearFocus(); runLayout(e.target.value); }));
}

function applyFilters() {
  const showOffices = $("#toggle-offices").checked;
  const showForming = $("#toggle-forming").checked;
  cy.batch(() => {
    cy.nodes().forEach((n) => {
      const d = n.data();
      const hide = (d.kind === "office" && !showOffices) || (d.forming && !showForming);
      n.style("display", hide ? "none" : "element");
    });
  });
}
