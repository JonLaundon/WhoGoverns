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

// Short, factual descriptions shown when a legend type/heading is clicked.
const TYPE_INFO = {
  ministerial_department: "A department led by a government minister and accountable to Parliament. Ministerial departments set policy and direct the agencies and arm's-length bodies beneath them (e.g. the Treasury, the Home Office).",
  non_ministerial_department: "A department led by senior officials or a board rather than a minister — usually to keep a regulatory or quasi-judicial function at arm's length from day-to-day politics (e.g. HMRC, Ofgem, the Competition and Markets Authority).",
  executive_agency: "A unit run at arm's length inside a department to deliver a specific operational service, with its own chief executive but no separate legal identity (e.g. DVLA, HM Prison and Probation Service).",
  division_directorate: "An internal division, directorate or sub-organisation of a department — part of the machinery rather than a separate body.",
  executive_ndpb: "An executive non-departmental public body: an arm's-length body carrying out executive, administrative or regulatory functions on a department's behalf, but not part of it (e.g. the Environment Agency).",
  advisory_ndpb: "An advisory non-departmental public body: an expert committee that advises ministers, usually without executive powers (e.g. the Committee on Toxicity, SAGE).",
  tribunal: "A body exercising a judicial or quasi-judicial function, resolving disputes between citizens and the state or between parties, outside the ordinary courts (e.g. the First-tier Tribunal chambers).",
  public_corporation: "A trading body owned by government that operates commercially with a degree of independence (e.g. Channel Four, the Bank of England group).",
  royal_charter_body: "A body incorporated by Royal Charter, giving it independence from government; often with historic, professional or ceremonial functions. Populated from a separate Privy Council source (not the GOV.UK register).",
  other_body: "Bodies that don't fall into the main classifications — statutory commissioners, cross-cutting units, and bodies with mixed functions. The catch-all pending finer classification.",
  prime_minister: "The head of government, who chairs the Cabinet and advises the Crown on the appointment of all ministers. The most senior office in the executive.",
  cabinet_minister: "A minister who sits in the Cabinet — usually a Secretary of State heading a department. Cabinet ministers are collectively responsible for government policy.",
  junior_minister: "A minister below Cabinet rank (Minister of State or Parliamentary Under-Secretary) supporting a Secretary of State with a specific brief.",
  independent_official: "A statutory office-holder independent of ministers — commissioners, inspectors, ombudsmen, and the heads of the non-ministerial departments — who exercise their functions in their own right.",
  civil_servant: "A senior civil servant. Here: departmental permanent secretaries, the most senior official in each department and its principal accounting officer.",
  other: "Office roles that don't fall into the standard tiers — ceremonial offices, law officers, and special envoys.",
};
const GROUP_INFO = {
  Officials: "The people who run the state: the Prime Minister, cabinet and junior ministers, and the senior officials (permanent secretaries and independent office-holders) who exercise its functions.",
  Departments: "The core machinery of central government: ministerial and non-ministerial departments, their executive agencies and internal divisions.",
  "Public bodies": "Arm's-length bodies: executive and advisory NDPBs, tribunals, public corporations, chartered bodies and the wider 'other' tail.",
};

// ---- The operative layer (Spiral 2): powers, duties and veto points ----
// Blocker kinds colour the CAN_VETO links. Every one of these is DERIVED in compile.py from
// a sourced field (a body's `functions` tag, or the type of the power being gated) — never a
// hand-kept list here, which would be an uncited taxonomy living in the presentation layer.
// Gold and red deliberately echo the existing regulator/minister colours.
const BLOCKER_KINDS = {
  regulatory:  ["Regulatory", "#d4a017"],
  ministerial: ["Ministerial", "#c0392b"],
  fiscal:      ["Fiscal", "#0d7d74"],
  judicial:    ["Judicial", "#6b4fbb"],
};
const BLOCKER_INFO = {
  regulatory: "A regulator's consent, licence or direction stands between the decision and its delivery.",
  ministerial: "A Minister's consent is required — the block is held by an elected officeholder, not an arm's-length body.",
  fiscal: "The block is a money gate: a consent to funding, indemnity, guarantee or charging. These are the blockers least visible in the statute of the sector itself.",
  judicial: "A court determines the matter. Note that a court adjudicates rather than vetoes — it decides, and may refuse.",
};
// How hard the veto bites, audited against the mandatory/directory doctrine (JOYS 6th ed
// ss.2.57-2.60). Line style on the map encodes this; colour encodes the kind.
const STRENGTHS = {
  hard_stop:       ["Hard stop", "No lawful route around it — the decision cannot proceed without this holder."],
  strong_delay:    ["Strong delay", "Can ultimately be got past, but only via a further legal process (usually an appeal) that costs substantial time."],
  procedural_risk: ["Procedural risk", "Breach does not automatically invalidate the decision, but exposes it to judicial review."],
  advisory_only:   ["Advisory only", "The holder's disagreement carries no legal consequence."],
};
const MODALITY = { power: ["may", "A discretion — the holder may act, and may lawfully decline."],
                   duty: ["must", "An obligation — not acting is a breach."],
                   veto: ["blocks", "The holder's decision determines whether ANOTHER actor may lawfully proceed."] };

// The FUNCTIONAL axis, orthogonal to body_type — a grouping (chiefly "regulator") that
// cross-cuts the constitutional forms. Sourced to the DBT List of UK regulators.
const FUNCTION_TYPES = {
  regulation: ["Regulators", "#d4a017"],
};
const FUNCTION_INFO = {
  regulation: "Bodies that set, license, supervise or enforce rules on a sector or profession. Regulation is a function, not a legal form: these bodies are non-ministerial departments, executive NDPBs, public corporations and 'other' bodies alike — which is why they can't be a single body_type. Tagged from the Department for Business and Trade's List of UK regulators. (Professional and statutory self-regulators outside the GOV.UK register, and devolved regulators, are not yet held.)",
};

// Eight rings, centre → rim (higher value = nearer the centre in a concentric layout):
//   7 PM · 6 cabinet · 5 junior/under-secretaries · 4 independent officials ·
//   3 ministerial + non-ministerial departments · 2 agencies + divisions · 1 public bodies ·
//   0 off-register royal-charter bodies (self-governing; no sponsor spine, so at the rim).
function level(d) {
  if (d.kind === "office") {
    return { prime_minister: 7, cabinet_minister: 6, junior_minister: 5,
             independent_official: 4, civil_servant: 4, other: 5 }[d.office_type] || 5;
  }
  const b = d.body_type;
  if (b === "ministerial_department" || b === "non_ministerial_department") return 3;
  if (b === "executive_agency" || b === "division_directorate") return 2;
  if (b === "royal_charter_body") return 0; // 8th ring: off-register chartered bodies, at the rim
  return 1; // executive/advisory NDPB, tribunal, public corp, other body
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
const RING_RADIUS = { 7: 0, 6: 110, 5: 190, 4: 260, 3: 340, 2: 480, 1: 760, 0: 980 };

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
let SOURCES = {};   // source_id -> { title, url, publisher }, from graph.json
const GROUP_TYPES = {
  Officials: ["prime_minister", "cabinet_minister", "junior_minister", "independent_official", "civil_servant", "other"],
  Departments: ["ministerial_department", "non_ministerial_department", "executive_agency", "division_directorate"],
  "Public bodies": ["executive_ndpb", "advisory_ndpb", "tribunal", "public_corporation", "royal_charter_body", "other_body"],
};
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
  SOURCES = graph.sources || {};

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
    d.hasVeto = !!(d.operative && d.operative.counts && d.operative.counts.vetoes);
    const aliases = (d.other_names || []).join(" ");
    const alsoHolds = (d.also_holds || []).join(" ");
    searchIndex.push({ id: d.id, label: d.label, sub: subOf(d),
      text: (d.label + " " + aliases + " " + (d.holder || "") + " " + alsoHolds).toLowerCase() });
  });

  // Resolve each blocking link's colour once, here, from the kind compile.py derived.
  graph.edges.forEach((e) => {
    if (e.data.kind === "can_veto") {
      e.data.kindColor = (BLOCKER_KINDS[e.data.blocker_kind] || ["", "#6b7280"])[1];
    }
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
      // CAN_VETO links. Two independent encodings: COLOUR = the kind of blocker (derived from
      // sourced fields in compile.py); LINE STYLE = how hard it bites, from the audited
      // strength grading. Solid means there is no lawful way round it.
      { selector: "edge[kind = 'can_veto']", style: {
        "line-color": "data(kindColor)", "target-arrow-color": "data(kindColor)",
        "target-arrow-shape": "tee", "arrow-scale": 1.1, "width": 2.2, "opacity": 0.85,
        "curve-style": "bezier", "z-index": 60 } },
      { selector: "edge[kind = 'can_veto'][strength = 'strong_delay']", style: { "line-style": "dashed", "width": 1.8, "opacity": 0.7 } },
      { selector: "edge[kind = 'can_veto'][strength = 'procedural_risk']", style: { "line-style": "dotted", "width": 1.5, "opacity": 0.6 } },
      { selector: "edge.veto-hide", style: { "display": "none" } },
      { selector: "edge.struct-hide", style: { "display": "none" } },
      { selector: "edge.struct-quiet", style: { "opacity": 0.12 } },
      { selector: "edge.rot-hide", style: { "display": "none" } },
      { selector: ".faded", style: { "opacity": 0.08, "text-opacity": 0 } },
      { selector: "node.thread-lbl", style: { "label": "data(label)", "z-index": 95, "border-width": 2, "border-color": "#0b0c0c" } },
      { selector: "edge.thread-edge", style: { "line-color": "#0b0c0c", "opacity": 1, "width": 2.5, "z-index": 85, "target-arrow-color": "#0b0c0c", "line-style": "solid" } },
      { selector: "edge.thread-assoc", style: { "line-color": "#0b0c0c", "opacity": 0.55, "width": 1.4, "z-index": 84, "target-arrow-color": "#0b0c0c", "line-style": "dashed" } },
      // A highlighted blocking link keeps its OWN colour and just gets louder. Declared
      // AFTER thread-edge/hover-hl so it wins — otherwise selecting a node turned every
      // blocking link black and you could no longer tell accountability from obstruction.
      { selector: "edge[kind = 'can_veto'].thread-veto", style: {
        "line-color": "data(kindColor)", "target-arrow-color": "data(kindColor)",
        "width": 3.4, "opacity": 1, "z-index": 99 } },
      { selector: "node.hover-hl", style: { "label": "data(label)", "z-index": 90, "border-width": 2, "border-color": "#0b0c0c" } },
      { selector: "edge.hover-hl", style: { "line-color": "#0b0c0c", "opacity": 1, "width": 2, "z-index": 80, "target-arrow-color": "#0b0c0c" } },
      { selector: "node:selected", style: { "label": "data(label)", "border-width": 3, "border-color": "#0b0c0c", "z-index": 100, "font-size": 11, "font-weight": "bold" } },
      { selector: "node.func-hl", style: { "border-width": 4, "border-color": "#d4a017", "z-index": 70 } },
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
  applyMapMode();      // blocking links start hidden; they appear with a selection
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
  else cy.elements().removeClass("faded thread-lbl thread-edge thread-assoc hover-hl");
}

/* ---------- click: golden thread + rotation + details ---------- */

// Walk the graph from a node following edges one way: "in" = towards the centre
// (sponsor department → minister → cabinet → PM), "out" = away (agencies → bodies →
// sub-bodies, the whole downstream subtree). Returns the nodes AND connecting edges.
// STRUCTURAL edges only. A blocking link is not a line of accountability — walking one
// would drag an unrelated department's whole subtree into the golden thread (select Ofwat,
// and the CMA's entire estate lights up because the CMA can veto it).
const STRUCTURAL = "edge[kind != 'can_veto']";

function traverse(node, dir) {
  let acc = node;
  let frontier = node;
  for (let i = 0; i < 25; i++) {
    // incomers(selector) FILTERS the result, so passing an edge selector returns edges only
    // and drops the nodes at the far end — walk to those explicitly, or the thread dies after
    // one hop and no connected body is ever highlighted.
    const edges = dir === "in" ? frontier.incomers(STRUCTURAL) : frontier.outgoers(STRUCTURAL);
    const reached = dir === "in" ? edges.sources() : edges.targets();
    const fresh = reached.difference(acc);
    acc = acc.union(edges).union(reached);
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
  let tree = up.union(downstreamTree(node));   // + the downstream subtree
  // This node's own blocking links, and whoever sits at the other end. They join the
  // highlight but keep their OWN colour (see thread-veto) — the whole point is to see, at a
  // glance, which lines are accountability and which are "this can stop you".
  // ...but only the ones currently on show, so the Info tab doesn't label bodies whose
  // blocking links are hidden.
  const vetoEdges = node.connectedEdges("edge[kind = 'can_veto']").not(".veto-hide");
  tree = tree.union(vetoEdges).union(vetoEdges.connectedNodes());
  cy.elements().addClass("faded")
    .removeClass("thread-lbl thread-edge thread-assoc thread-veto hover-hl");
  tree.removeClass("faded");
  vetoEdges.connectedNodes().addClass("thread-lbl");
  up.nodes().addClass("thread-lbl");   // label only the upward thread (downstream is too many)
  node.addClass("thread-lbl");
  if (node.data("kind") === "body") {
    // Selecting a body reaches its department's ministers — but only the accountable
    // Secretary of State is a direct link; the department's OTHER ministers are merely
    // associated (same department, different brief), so draw those dashed (as MoG does).
    tree.edges().forEach((e) => {
      if (e.data("kind") === "can_veto") return;   // keeps its blocker colour
      const assoc = (e.data("kind") === "office_of" && ["junior_minister", "other"].includes(e.source().data("office_type")))
        || (e.data("kind") === "leads" && e.target().data("office_type") === "junior_minister");
      e.addClass(assoc ? "thread-assoc" : "thread-edge");
    });
  } else {
    tree.edges().not("edge[kind = 'can_veto']").addClass("thread-edge");
  }
  vetoEdges.addClass("thread-veto");
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
  activeTab = "info";          // a fresh selection opens on Info
  applyMapMode();
  if (currentLayout === "rings") rotateToTop(node);
  else cy.animate({ center: { eles: node }, zoom: Math.max(cy.zoom(), 1.0) }, { duration: 250 });
}

function clearFocus() {
  selectedId = null;
  activeTab = "info";
  $("#tooltip").style.display = "none";
  cy.elements().removeClass("faded hover-hl thread-lbl thread-edge thread-assoc thread-veto");
  applyMapMode();
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
  el.querySelectorAll(".tab").forEach((btn) =>
    btn.addEventListener("click", () => {
      const k = btn.getAttribute("data-tab");
      el.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b === btn));
      el.querySelectorAll(".tabpanel").forEach((p) => { p.hidden = p.getAttribute("data-panel") !== k; });
      activeTab = k;          // the tab IS the declared intent — let the map follow it
      applyMapMode();
    }));
  // Power / Duty / Veto filter pills.
  el.querySelectorAll(".op-pill").forEach((btn) =>
    btn.addEventListener("click", () => {
      const k = btn.getAttribute("data-op");
      el.querySelectorAll(".op-pill").forEach((b) => b.classList.toggle("active", b === btn));
      el.querySelectorAll(".op-wrap").forEach((w) => {
        w.hidden = k !== "all" && w.getAttribute("data-op") !== k;
      });
    }));
  wireViz(el, d);
}

// Data-viz sub-toggles + the whole-group/core scope toggle. The scope toggle re-renders the
// civil panel at the chosen scope (re-pointing the grade/profession donuts) and re-wires it.
function wireViz(root, d) {
  root.querySelectorAll(".viz-toggle button").forEach((btn) =>
    btn.addEventListener("click", () => {
      const bar = btn.parentElement, k = btn.getAttribute("data-view");
      bar.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
      let sib = bar.nextElementSibling;
      while (sib && sib.classList.contains("viz-view")) {
        sib.hidden = sib.getAttribute("data-view") !== k;
        sib = sib.nextElementSibling;
      }
    }));
  root.querySelectorAll(".scope-toggle button").forEach((btn) =>
    btn.addEventListener("click", () => {
      const panel = btn.closest(".tabpanel");
      panel.innerHTML = staffingTabHtml(d.staffing, btn.getAttribute("data-scope"));
      wireViz(panel, d);
    }));
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
    mins = "<h3>Led by</h3><ul>" + ministers.map((o) =>
      `<li><button class="linkish" data-goto="${esc(o.id())}">${esc(o.data("label"))}</button>` +
      (o.data("holder") ? ` — ${esc(o.data("holder"))}` : "") + "</li>").join("") + "</ul>";
  }
  const aliases = (d.other_names || []).length
    ? `<h3>Also known as</h3><ul>${d.other_names.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>` : "";
  const flag = d.needs_review ? ` <span class="flag" title="Classified from the API format field; flagged for a finer human pass">classification: review</span>` : "";
  // All department sponsors (a body can be jointly sponsored, e.g. NISTA by Cabinet Office + HM Treasury).
  const deptSponsors = cy.getElementById(d.id).incomers("edge[kind = 'sponsors']").sources()
    .filter((s) => ["ministerial_department", "non_ministerial_department"].includes(s.data("body_type")));
  const sponsorHtml = deptSponsors.nonempty()
    ? deptSponsors.map((s) => `<button class="linkish" data-goto="${esc(s.id())}">${esc(s.data("label"))}</button>`).join(", ")
    : (d.sponsor_department_id ? gotoBtn(d.sponsor_department_id) : "—");
  // Downward relationships (MoG-style) — the bodies this one sponsors/parents, from the
  // sourced sponsor edges. A department "Sponsors" its ALBs; a body is "Parent of" children.
  const node = cy.getElementById(d.id);
  // Provenance of the sponsor relationships (#6): the source record behind each incoming
  // sponsor edge, so a sponsor claim is followable to its source like every other figure.
  const sponsorSrcIds = node.incomers("edge[kind = 'sponsors']").map((e) => e.data("source_id")).filter(Boolean);
  const down = node.outgoers("edge[kind = 'sponsors']").targets().sort((a, b) => a.data("label").localeCompare(b.data("label")));
  const isDept = ["ministerial_department", "non_ministerial_department"].includes(d.body_type);
  const relDown = down.nonempty()
    ? `<h3>${isDept ? "Sponsors" : "Parent of"} <span class="muted">(${down.length})</span></h3>`
      + `<ul class="rel-list">` + down.map((n) => `<li><button class="linkish" data-goto="${esc(n.id())}">${esc(n.data("label"))}</button></li>`).join("") + `</ul>`
    : "";
  const infoPanel = `
    <dl>
      <dt>Status</dt><dd>${esc(d.status)}${d.forming ? " (in formation)" : ""}</dd>
      <dt>Sponsored by</dt><dd>${sponsorHtml}</dd>
      ${d.parent_body_id ? `<dt>Child of</dt><dd>${gotoBtn(d.parent_body_id)}</dd>` : ""}
      <dt>On GOV.UK</dt><dd>${govuk ? `<a href="${esc(govuk)}" rel="noopener" target="_blank">gov.uk page ↗</a>` : "—"}</dd>
    </dl>
    ${relDown}
    ${mins}
    ${aliases}
    <h3>Source</h3>
    ${sourceHtml(d.source_ids)}
    ${sponsorSrcIds.length ? `<p class="src">Sponsor relationships cited to:</p>${sourceLinks(sponsorSrcIds)}` : ""}`;

  // Tabs — MoG-style. Budget / Civil service appear only where we hold the data.
  const nOp = opCount(d);
  const tabs = [["info", "Info"], ["powers", `Powers${nOp ? ` <span class="tab-n">${nOp}</span>` : ""}`]];
  if (d.budget) tabs.push(["budget", `Budget <span class="tab-sub">${esc(d.budget.fy)}</span>`]);
  if (d.staffing) tabs.push(["civil", "Civil service"]);
  const tabBar = `<div class="tabs" role="tablist">` + tabs.map(([k, label], i) =>
    `<button class="tab${i === 0 ? " active" : ""}" role="tab" data-tab="${k}">${label}</button>`).join("") + `</div>`;
  const panel = (k, html) => `<div class="tabpanel" data-panel="${k}"${k === "info" ? "" : " hidden"}>${html}</div>`;
  const powers = powersTabHtml(d);

  return `
    <p class="kicker">${esc(type)}${flag}</p>
    <h2>${esc(d.label)}</h2>
    ${tabBar}
    ${panel("info", infoPanel)}
    ${panel("powers", powers)}
    ${d.budget ? panel("budget", budgetTabHtml(d.budget)) : ""}
    ${d.staffing ? panel("civil", staffingTabHtml(d.staffing)) : ""}`;
}

function fmtGBP(n) {
  if (n == null) return "—";
  const a = Math.abs(n);
  if (a >= 1e9) return "£" + (n / 1e9).toFixed(1) + "bn";
  if (a >= 1e6) return "£" + Math.round(n / 1e6) + "m";
  if (a >= 1e3) return "£" + Math.round(n / 1e3) + "k";
  return "£" + n;
}
function fmtNum(n) { return n == null ? "—" : n.toLocaleString("en-GB"); }

// ---- Data-viz: hollow donut + legend (dataviz skill: validated categorical palette,
// colour carries identity, figures + % in the legend, native per-segment tooltip). ----
const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)",
  "var(--series-5)", "var(--series-6)", "var(--series-7)", "var(--series-8)"];

// Keep the top n by value; fold the remainder into a muted "Other" so a categorical
// hue is never cycled (skill non-negotiable).
function topN(items, n) {
  const sorted = items.filter((x) => x.value > 0).sort((a, b) => b.value - a.value);
  if (sorted.length <= n) return sorted;
  const rest = sorted.slice(n).reduce((s, x) => s + x.value, 0);
  const head = sorted.slice(0, n);
  if (rest > 0) head.push({ label: "Other", value: rest, other: true });
  return head;
}
function colourise(segs) {
  return segs.map((s, i) => ({ ...s, color: s.other ? "var(--series-other)" : SERIES[i % SERIES.length] }));
}

function donutSVG(segments, centerMain, centerCap) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const r = 52, cx = 70, cy = 70, sw = 22, C = 2 * Math.PI * r, gap = 2;
  let offset = 0;
  const rings = segments.map((s) => {
    const frac = s.value / total;
    const len = Math.max(1, frac * C - gap);
    const seg = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="${sw}"`
      + ` stroke-dasharray="${len.toFixed(2)} ${(C - len).toFixed(2)}" stroke-dashoffset="${(-offset).toFixed(2)}"`
      + ` transform="rotate(-90 ${cx} ${cy})"><title>${esc(s.label)} — ${(frac * 100).toFixed(0)}%</title></circle>`;
    offset += frac * C;
    return seg;
  }).join("");
  const main = centerMain ? `<text x="${cx}" y="${cy - 1}" text-anchor="middle" dominant-baseline="middle" class="donut-total" font-size="15">${esc(centerMain)}</text>` : "";
  const cap = centerCap ? `<text x="${cx}" y="${cy + 15}" text-anchor="middle" class="donut-cap" font-size="8.5">${esc(centerCap)}</text>` : "";
  return `<svg class="donut" viewBox="0 0 140 140" width="128" height="128" role="img" aria-label="donut chart">${rings}${main}${cap}</svg>`;
}

// segments: [{label, value}] (colours assigned here). fmt formats the absolute figure.
function donutBlock(segments, fmt, centerMain, centerCap) {
  const segs = colourise(segments);
  const total = segs.reduce((s, x) => s + x.value, 0) || 1;
  const legend = `<ul class="donut-legend">` + segs.map((s) =>
    `<li><span class="dot" style="background:${s.color}"></span><span class="lbl">${esc(s.label)}</span>`
    + `<span class="val">${fmt(s.value)} <span class="pct">${(s.value / total * 100).toFixed(0)}%</span></span></li>`).join("")
    + `</ul>`;
  return `<div class="donut-wrap">${donutSVG(segs, centerMain, centerCap)}${legend}</div>`;
}

// A titled toggle over several donut "views" (By type / By programme, etc.).
function vizToggle(views) {
  const bar = `<div class="viz-toggle">` + views.map((v, i) =>
    `<button class="${i === 0 ? "active" : ""}" data-view="${v.key}">${esc(v.label)}</button>`).join("") + `</div>`;
  const panels = views.map((v, i) => `<div class="viz-view" data-view="${v.key}"${i === 0 ? "" : " hidden"}>${v.html}</div>`).join("");
  return bar + panels;
}

const GRADE_LABEL = { scs: "Senior Civil Service", grade_6_7: "Grade 6 / 7", seo_heo: "SEO / HEO",
  eo: "Executive Officer", aa_ao: "AA / AO", unreported: "Unreported" };

function budgetTabHtml(b) {
  const h = b.headline || {};
  const row = (label, net, gross) => (net == null && gross == null) ? "" :
    `<dt>${label}</dt><dd>${fmtGBP(net)}${gross != null && gross !== net ? ` <span class="muted">(gross ${fmtGBP(gross)})</span>` : ""}</dd>`;
  // By-type donut: the four budgeting boundaries (net), centre = TME.
  const byType = [
    { label: "Resource DEL", value: h.resource_del_net || 0 },
    { label: "Capital DEL", value: h.capital_del_net || 0 },
    { label: "Resource AME", value: h.resource_ame_net || 0 },
    { label: "Capital AME", value: h.capital_ame_net || 0 },
  ].filter((s) => s.value > 0);
  const tme = h.total_managed_expenditure_net;
  const byProg = topN((b.programmes || []).map((p) => ({ label: p.name.replace(/^\d+\.\s*/, ""), value: p.net })), 8);
  const byBody = topN((b.by_body || []).map((x) => ({ label: x.name, value: x.value })), 8);
  const byIncome = topN((b.income || []).map((x) => ({ label: x.name, value: x.value })), 8);
  const bodyTotal = byBody.reduce((s, x) => s + x.value, 0);
  const views = [{ key: "type", label: "By type", html: donutBlock(byType, fmtGBP, fmtGBP(tme), "net TME") }];
  if (byProg.length) views.push({ key: "programme", label: "By programme", html: donutBlock(byProg, fmtGBP, fmtGBP(h.resource_del_net), "resource DEL") });
  if (byBody.length) views.push({ key: "body", label: "By body", html: donutBlock(byBody, fmtGBP, fmtGBP(bodyTotal), "sponsored bodies") });
  if (byIncome.length) views.push({ key: "income", label: "Income", html: donutBlock(byIncome, fmtGBP, fmtGBP(h.income_net), "income") });
  return `<p class="src">HM Treasury OSCAR outturn, ${esc(b.fy)} (net of income unless gross shown).</p>
    <dl>
      ${row("Resource DEL", h.resource_del_net, h.resource_del_gross)}
      ${row("Capital DEL", h.capital_del_net, h.capital_del_gross)}
      ${row("Resource AME", h.resource_ame_net, h.resource_ame_gross)}
      ${row("Capital AME", h.capital_ame_net, h.capital_ame_gross)}
      ${row("Total managed expenditure", h.total_managed_expenditure_net, null)}
    </dl>${vizToggle(views)}${sourceLinks(b.source_ids)}`;
}

function staffingTabHtml(s, scope) {
  scope = scope || "group";
  const src = (scope === "core" && s.core) ? s.core : s;   // grade/profession donuts re-point
  const total = src.headcount_total;
  const byGrade = (src.grades || []).map((g) => ({ label: GRADE_LABEL[g.grade] || g.grade, value: g.headcount || 0 })).filter((x) => x.value > 0);
  const byProf = topN((src.professions || []).map((p) => ({ label: p.name, value: p.headcount })), 8);
  const byOrg = topN((s.by_org || []).map((x) => ({ label: x.name, value: x.value })), 8);   // a group concept
  const views = [];
  if (byGrade.length) views.push({ key: "grade", label: "By grade", html: donutBlock(byGrade, fmtNum, fmtNum(total), "headcount") });
  if (byOrg.length && scope === "group") views.push({ key: "org", label: "By organisation", html: donutBlock(byOrg, fmtNum, fmtNum(byOrg.reduce((a, x) => a + x.value, 0)), "agencies") });
  if (byProf.length) views.push({ key: "prof", label: "By profession", html: donutBlock(byProf, fmtNum, fmtNum(total), "headcount") });
  // Whole-group / core toggle only where a department has a core (excl. agencies) figure.
  const scopeToggle = s.core
    ? `<div class="scope-toggle"><button class="${scope === "group" ? "active" : ""}" data-scope="group">Whole group</button>`
      + `<button class="${scope === "core" ? "active" : ""}" data-scope="core">Core department</button></div>`
    : "";
  return `<p class="src">Civil Service Statistics, headcount as at 31 March ${esc(s.period)}.${(scope === "group" && s.disclaimer) ? " " + esc(s.disclaimer) : ""}</p>
    <dl>
      <dt>Headcount</dt><dd>${fmtNum(total)}</dd>
      ${src.fte_total != null ? `<dt>Full-time equivalent</dt><dd>${fmtNum(src.fte_total)}</dd>` : ""}
    </dl>${scopeToggle}${vizToggle(views)}${sourceLinks(s.source_ids)}`;
}

/* ---------- the operative layer: powers / duties / vetoes on an entity card ---------- */

// Standing caveat at the head of every Powers tab. The register holds STATUTORY authority
// only, and saying so plainly is the honest alternative to a card that looks empty for a
// convention-heavy office (culture, sport) and leaves the reader to guess why.
const POWERS_CAVEAT =
  `<p class="caveat"><strong>Statutory powers only.</strong> This register records authority
   conferred by legislation, cited to the provision. Powers resting on the <em>royal
   prerogative</em> or on <em>convention</em> are not yet held and may be added later; where a
   body's real remit rests on those, this tab will understate it. Statutory authority takes
   precedence: where Parliament has legislated in a field, statute governs and displaces the
   prerogative to that extent.</p>`;

function badge(text, cls, title) {
  return `<span class="badge ${cls || ""}"${title ? ` title="${esc(title)}"` : ""}>${esc(text)}</span>`;
}

// One record, MoG's card anatomy — type pill, "Since YYYY", short title, plain-English
// paragraph, typed source badge — plus the three things a purely editorial product cannot
// carry: the may/must/blocks modality, the decision actually blocked, and the assurance tier.
function operativeCard(r) {
  const mod = MODALITY[r.kind] || MODALITY.power;
  const kindLabel = { power: "POWER", duty: "DUTY", veto: "VETO" }[r.kind];
  const since = r.since ? `<span class="since">Since ${esc(r.since)}</span>` : "";
  const typeLabel = (r.type || "").replace(/_/g, " ");

  let extra = "";
  if (r.kind === "veto") {
    const s = STRENGTHS[r.strength] || [r.strength, ""];
    const k = BLOCKER_KINDS[r.blocker_kind];
    // The head of the CAN_VETO edge: whose decision is stopped. This single line is the
    // register's whole thesis — a Power record structurally cannot carry it.
    const blocked = r.blocks_party_outside_state
      ? `<span class="muted">a party outside the state</span> — ${esc(r.decision_affected || "")}`
      : `${gotoBtn(r.blocks_office_id || r.blocks_body_id)} — ${esc(r.decision_affected || "")}`;
    extra += `<p class="blocks"><strong>Blocks:</strong> ${blocked}</p>`;
    if (r.blocks_party_outside_state) {
      extra += `<p class="src note-outside">Not drawn on the map: the map models what the state
        does to itself. This block falls on a private party or an unnamed class — it is real,
        cited, and answers "can I do this?", but there is no state body at the other end.</p>`;
    }
    extra += `<p class="chips">${badge(s[0], "strength-" + r.strength, s[1])}` +
      (k ? badge(k[0], "kind-" + r.blocker_kind, BLOCKER_INFO[r.blocker_kind]) : "") +
      (r.overridable === "yes" ? badge("overridable", "warn", r.override_mechanism || "") : "") +
      `</p>`;
    if (r.override_mechanism) {
      extra += `<p class="override"><strong>Way around it:</strong> ${esc(r.override_mechanism)}</p>`;
    }
  }
  if (r.kind === "power" && (r.constraints || []).length) {
    extra += `<p class="constraints"><strong>Limits:</strong></p><ul class="constraints-list">` +
      r.constraints.map((c) => `<li>${esc(c)}</li>`).join("") + `</ul>`;
  }

  // Assurance, on the face of the card rather than buried. Nothing here is human-checked yet.
  const vs = r.verification_status || "unverified";
  const vLabel = { unverified: "unverified", machine_verified: "machine-checked",
                   single_checked: "checked", double_checked: "double-checked" }[vs] || vs;
  const assurance = badge(vLabel, "assure-" + vs,
    "How far this record has been verified. machine-checked = passed an independent blind " +
    "re-grading; it has not yet been checked by a person.") +
    (r.confidence != null ? badge("confidence " + r.confidence.toFixed(2), "assure-conf") : "");

  const cite = r.citation || {};
  const src = SOURCES[r.source_id] || {};
  const citation = cite.url
    ? `<a href="${esc(cite.url)}" rel="noopener" target="_blank">${esc(src.title || r.source_id || "")}${cite.provision ? ", " + esc(cite.provision) : ""} ↗</a>`
    : esc((src.title || "") + (cite.provision ? ", " + cite.provision : ""));

  return `<article class="op-card op-${r.kind}">
    <div class="op-head">
      <span class="op-kind op-kind-${r.kind}">${kindLabel}</span>
      ${badge(mod[0], "mod mod-" + r.kind, mod[1])}
      ${typeLabel ? `<span class="op-type">${esc(typeLabel)}</span>` : ""}
      ${since}
    </div>
    <h4>${esc(r.label || "")}</h4>
    <p class="op-summary">${esc(r.summary || "")}</p>
    ${extra}
    ${r.outstanding_effects ? `<p class="src warn-line">⚠ This provision has amendments not yet
      applied to the consolidated text — the wording may lag the law in force.</p>` : ""}
    <p class="op-src"><span class="src-kind">${esc((src.source_type || "act").toUpperCase())}</span> ${citation}</p>
    <p class="chips assurance">${assurance}</p>
  </article>`;
}

// The Powers tab. Filter pills follow the precedent's pattern, but over OUR three cited
// primitives (Power / Duty / Veto) rather than its four — we decline Function and
// Responsibility, which are the soft, un-citable descriptors.
function powersTabHtml(d) {
  const own = d.operative || {};
  const via = d.office_operative || {};
  const all = [].concat(own.powers || [], own.duties || [], own.vetoes || []);
  const viaAll = [].concat(via.powers || [], via.duties || [], via.vetoes || []);
  if (!all.length && !viaAll.length) {
    return POWERS_CAVEAT + `<p class="src">No statutory powers, duties or veto points have been
      extracted for this entity yet. Extraction runs domain by domain (water first), so an empty
      tab means "not yet reached", not "holds no powers".</p>`;
  }
  const pills = [["all", "All", all.length], ["power", "Powers", (own.powers || []).length],
                 ["duty", "Duties", (own.duties || []).length], ["veto", "Veto points", (own.vetoes || []).length]]
    .filter(([k, , n]) => k === "all" || n)
    .map(([k, label, n], i) => `<button class="op-pill${i === 0 ? " active" : ""}" data-op="${k}">${esc(label)} <span class="pill-n">${n}</span></button>`)
    .join("");

  const cards = all.map((r) => `<div class="op-wrap" data-op="${r.kind}">${operativeCard(r)}</div>`).join("");
  const viaCards = viaAll.length
    ? `<h3>Held by its ministers <span class="muted">(${viaAll.length})</span></h3>
       <p class="src">Most statutory authority in a department vests in the <em>office</em> —
       "the Secretary of State may…" — not in the department as a body. These are held by
       officeholders hosted here.</p>`
      + viaAll.map((r) => operativeCard(r)).join("")
    : "";
  return POWERS_CAVEAT + (all.length ? `<div class="op-pills">${pills}</div>${cards}` : "") + viaCards;
}

// Cite the record's ACTUAL sources (resolved via the graph's source index), not a fixed
// blurb — off-register bodies come from the Privy Council register or the DBT regulators
// list, not the GOV.UK API.
function sourceHtml(ids) {
  const items = (ids || []).map((id) => SOURCES[id]).filter(Boolean);
  if (!items.length) return `<p class="src">Source pending.</p>`;
  const li = items.map((s) => s.url
    ? `<li><a href="${esc(s.url)}" rel="noopener" target="_blank">${esc(s.title || s.url)} ↗</a></li>`
    : `<li>${esc(s.title || "")}</li>`).join("");
  return `<p class="src">Existence and classification cited to:</p><ul class="src-list">${li}</ul>` +
    `<p class="src">Under the Open Government Licence v3.0 unless the source states otherwise.</p>`;
}

// A bare list of source links (resolved via the graph's source index), for citing a
// specific claim — a budget figure, staffing total or sponsor edge — back to its record.
function sourceLinks(ids) {
  const items = [...new Set(ids || [])].map((id) => SOURCES[id]).filter(Boolean);
  if (!items.length) return "";
  return `<ul class="src-list">` + items.map((s) => s.url
    ? `<li><a href="${esc(s.url)}" rel="noopener" target="_blank">${esc(s.title || s.url)} ↗</a></li>`
    : `<li>${esc(s.title || "")}</li>`).join("") + `</ul>`;
}

function opCount(d) {
  const c = (d.operative || {}).counts || {};
  return (c.powers || 0) + (c.duties || 0) + (c.vetoes || 0);
}

// An office is a power-holding node in its own right — a corporation sole ("the Secretary of
// State may…"), distinct from both the person and the department. Most statutory authority
// vests here, so the office card carries the same Powers tab a body does.
function officeHtml(d) {
  const type = (OFFICE_TYPES[d.office_type] || OFFICE_TYPES.other)[0];
  const nOp = opCount(d);
  const info = `
    <dl>
      <dt>Current holder</dt><dd>${esc(d.holder || "—")}</dd>
      ${d.holder_since ? `<dt>In post since</dt><dd>${esc(d.holder_since)}</dd>` : ""}
      <dt>Hosted at</dt><dd>${gotoBtn(d.body_id)}</dd>
    </dl>
    ${(d.also_holds && d.also_holds.length) ? `<h3>Also holds</h3><ul>${d.also_holds.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>` : ""}
    <h3>Source</h3>
    <p class="src">Appointment from the GOV.UK content API
      (<code>ordered_ministers → role_appointments</code>), Open Government Licence v3.0.
      Office type is a heuristic tier; PM→cabinet→junior links are derived by convention.</p>`;
  const tabs = [["info", "Info"], ["powers", `Powers${nOp ? ` <span class="tab-n">${nOp}</span>` : ""}`]];
  const tabBar = `<div class="tabs" role="tablist">` + tabs.map(([k, label], i) =>
    `<button class="tab${i === 0 ? " active" : ""}" role="tab" data-tab="${k}">${label}</button>`).join("") + `</div>`;
  return `
    <p class="kicker">${esc(type)} · office</p>
    <h2>${esc(d.label)}</h2>
    ${tabBar}
    <div class="tabpanel" data-panel="info">${info}</div>
    <div class="tabpanel" data-panel="powers" hidden>${powersTabHtml(d)}</div>`;
}

/* ---------- legend = clickable index (lists the type in the details panel) ---------- */
function buildLegend() {
  const group = (title, keys, map, cls, kind) =>
    `<h3 data-group="${title}">${title}</h3>` + keys.map((k) => {
      const [label, color] = map[k];
      return `<div class="row" data-type="${k}" data-kind="${kind}"><span class="swatch ${cls}" style="background:${color}"></span>${esc(label)}</div>`;
    }).join("");
  $("#legend").innerHTML =
    `<p class="fhint">Click a type — or a heading — to list every entry of that kind.</p>` +
    group("Officials", ["prime_minister", "cabinet_minister", "junior_minister", "independent_official", "civil_servant", "other"], OFFICE_TYPES, "office", "office") +
    group("Departments", ["ministerial_department", "non_ministerial_department", "executive_agency", "division_directorate"], BODY_TYPES, "dept", "body") +
    group("Public bodies", ["executive_ndpb", "advisory_ndpb", "tribunal", "public_corporation", "royal_charter_body", "other_body"], BODY_TYPES, "pub", "body") +
    `<h3 data-group="Functions">Functions <span class="flag" style="font-weight:400">cross-cutting</span></h3>` +
    Object.keys(FUNCTION_TYPES).map((k) => {
      const [label, color] = FUNCTION_TYPES[k];
      return `<div class="row" data-func="${k}"><span class="swatch pub" style="background:${color}"></span>${esc(label)}</div>`;
    }).join("") +
    `<h3 data-group="Blocking">Blocking <span class="flag" style="font-weight:400">who can stop what</span></h3>` +
    Object.keys(BLOCKER_KINDS).map((k) => {
      const [label, color] = BLOCKER_KINDS[k];
      return `<div class="row" data-blocker="${k}"><span class="swatch" style="background:none;border-top:3px solid ${color};height:0;border-radius:0"></span>${esc(label)}</div>`;
    }).join("") +
    `<div class="row nohover"><span class="swatch" style="background:none;border-top:3px solid #6b7280;height:0;border-radius:0"></span>solid = hard stop (no lawful route past it)</div>` +
    `<div class="row nohover"><span class="swatch" style="background:none;border-top:2px dashed #6b7280;height:0;border-radius:0"></span>dashed = a cited appeal or override exists</div>` +
    `<h3>Links</h3>` +
    `<div class="row nohover"><span class="swatch" style="background:none;border-top:2px solid #d3d6d8;height:0;border-radius:0"></span>sponsors</div>` +
    `<div class="row nohover"><span class="swatch" style="background:none;border-top:2px solid #8a1a12;height:0;border-radius:0"></span>leads (PM → cabinet → junior) <span class="flag" style="margin-left:4px">derived</span></div>`;
  $("#legend").querySelectorAll(".row[data-blocker]").forEach((row) =>
    row.addEventListener("click", () => renderBlockerList(row.getAttribute("data-blocker"))));
  $("#legend").querySelectorAll(".row[data-type]").forEach((row) =>
    row.addEventListener("click", () => renderTypeList(row.getAttribute("data-kind"), row.getAttribute("data-type"))));
  $("#legend").querySelectorAll(".row[data-func]").forEach((row) =>
    row.addEventListener("click", () => renderFuncList(row.getAttribute("data-func"))));
  $("#legend").querySelectorAll("h3[data-group]").forEach((h) =>
    h.addEventListener("click", () => renderGroupList(h.getAttribute("data-group"))));
}

// Every veto of a given kind, wherever it sits — the cross-cutting "who can block things"
// view. Lists the veto points themselves, not just their holders, because the answer people
// want is "what exactly can they stop, and under which section".
function renderBlockerList(kind) {
  const rows = [];
  cy.nodes().forEach((n) => {
    ((n.data("operative") || {}).vetoes || []).forEach((v) => {
      if (v.blocker_kind === kind) rows.push({ node: n, v });
    });
  });
  const [label] = BLOCKER_KINDS[kind] || [kind];
  const items = rows.map(({ node, v }) => {
    const s = (STRENGTHS[v.strength] || [v.strength])[0];
    const target = v.blocks_party_outside_state
      ? "<span class='muted'>a party outside the state</span>"
      : gotoBtn(v.blocks_office_id || v.blocks_body_id);
    return `<li><button class="linkish" data-goto="${esc(node.id())}">${esc(node.data("label"))}</button>
      <span class="muted">blocks</span> ${target}
      <div class="r-sub">${esc(v.label || "")} · ${esc((v.citation || {}).provision || "")} · ${esc(s)}</div></li>`;
  }).join("");
  const el = $("#detail-body");
  el.innerHTML = `<p class="kicker">Blocking</p><h2>${esc(label)} veto points</h2>` +
    `<p>${esc(BLOCKER_INFO[kind] || "")}</p>` +
    `<h3>${rows.length} ${rows.length === 1 ? "veto point" : "veto points"}</h3>` +
    `<ul class="type-list">${items}</ul>`;
  el.hidden = false;
  $("#detail-empty").hidden = true;
  el.querySelectorAll("[data-goto]").forEach((b) =>
    b.addEventListener("click", () => selectNode(b.getAttribute("data-goto"))));
}

function renderFuncList(func) {
  const members = cy.nodes().filter((n) => n.data("kind") === "body" &&
    (n.data("functions") || []).includes(func));
  showList((FUNCTION_TYPES[func] || [func])[0], FUNCTION_INFO[func] || "", members);
}

function renderTypeList(kind, type) {
  const label = ((kind === "office" ? OFFICE_TYPES : BODY_TYPES)[type] || [type])[0];
  const members = cy.nodes().filter((n) => n.data("kind") === kind &&
    (kind === "office" ? n.data("office_type") : n.data("body_type")) === type);
  showList(label, TYPE_INFO[type] || "", members);
}
function renderGroupList(name) {
  if (name === "Functions") {
    const members = cy.nodes().filter((n) => n.data("kind") === "body" && (n.data("functions") || []).length);
    return showList("Functions", "Bodies carrying a functional tag (a cross-cutting role, orthogonal to legal form). Currently: regulators, from the DBT List of UK regulators.", members);
  }
  const types = GROUP_TYPES[name] || [];
  const kind = name === "Officials" ? "office" : "body";
  const members = cy.nodes().filter((n) => n.data("kind") === kind &&
    types.includes(kind === "office" ? n.data("office_type") : n.data("body_type")));
  showList(name, GROUP_INFO[name] || "", members);
}
function showList(title, desc, members) {
  const sorted = members.sort((a, b) => a.data("label").localeCompare(b.data("label")));
  const items = sorted.map((n) =>
    `<li><button class="linkish" data-goto="${esc(n.id())}">${esc(n.data("label"))}</button>` +
    (n.data("holder") ? ` — ${esc(n.data("holder"))}` : "") + "</li>").join("");
  const el = $("#detail-body");
  el.innerHTML = `<p class="kicker">Category</p><h2>${esc(title)}</h2>` +
    (desc ? `<p>${esc(desc)}</p>` : "") +
    `<h3>${sorted.length} ${sorted.length === 1 ? "entry" : "entries"}</h3><ul class="type-list">${items}</ul>`;
  el.hidden = false;
  $("#detail-empty").hidden = true;
  el.querySelectorAll("[data-goto]").forEach((b) =>
    b.addEventListener("click", () => selectNode(b.getAttribute("data-goto"))));
}

/* ---------- dark mode ---------- */
function applyTheme(dark) {
  document.body.classList.toggle("dark", dark);
  const btn = $("#theme-toggle");
  if (btn) { btn.textContent = dark ? "☀️ Light" : "🌙 Dark"; btn.setAttribute("aria-pressed", String(dark)); }
  try { localStorage.setItem("wg-theme", dark ? "dark" : "light"); } catch (e) { /* ignore */ }
  if (!cy) return;
  const ink = dark ? "#f1f3f4" : "#0b0c0c";     // thread/selection colour that reads on the canvas
  cy.style()
    .selector("edge.thread-edge").style({ "line-color": ink, "target-arrow-color": ink })
    .selector("edge.thread-assoc").style({ "line-color": ink, "target-arrow-color": ink })
    .selector("edge.hover-hl").style({ "line-color": ink, "target-arrow-color": ink })
    .selector("node.thread-lbl").style({ "border-color": ink })
    .selector("node.hover-hl").style({ "border-color": ink })
    .selector("node:selected").style({ "border-color": ink })
    .selector("node[?forming]").style({ "border-color": ink })
    // re-assert AFTER the thread overrides above, or dark mode repaints blocking links black
    .selector("edge[kind = 'can_veto'].thread-veto")
    .style({ "line-color": "data(kindColor)", "target-arrow-color": "data(kindColor)" })
    .update();
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
  // Selecting always tidies up: pick the node, close the dropdown, drop focus so it
  // can't linger open over the panel (the search-Enter glitch).
  const doSelect = (id) => { results.innerHTML = ""; input.blur(); selectNode(id); };

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    results.innerHTML = "";
    if (q.length < 2) return;
    searchMatches(q).forEach((m, i) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      if (i === 0) li.setAttribute("aria-selected", "true");
      li.innerHTML = `${esc(m.label)}<div class="r-sub">${esc(m.sub)}</div>`;
      li.addEventListener("click", () => doSelect(m.id));
      results.appendChild(li);
    });
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { results.innerHTML = ""; input.blur(); return; }
    if (e.key !== "Enter") return;
    const q = input.value.trim().toLowerCase();      // recompute now — never a stale list
    if (q.length < 2) return;
    const m = searchMatches(q);
    if (m.length) { e.preventDefault(); doSelect(m[0].id); }
  });
  // Close the dropdown when focus leaves the search (click elsewhere).
  input.addEventListener("blur", () => setTimeout(() => { results.innerHTML = ""; }, 150));

  $("#toggle-forming").addEventListener("change", applyFilters);
  $("#toggle-regulators").addEventListener("change", applyRegulatorHighlight);
  $("#toggle-vetoes").addEventListener("change", applyMapMode);
  $("#toggle-sponsors").addEventListener("change", applyMapMode);
  document.querySelectorAll("input[name='layout']").forEach((r) =>
    r.addEventListener("change", (e) => { clearFocus(); runLayout(e.target.value); }));

  // dark mode: stored preference, else the OS setting
  let stored = null;
  try { stored = localStorage.getItem("wg-theme"); } catch (e) { /* ignore */ }
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(stored ? stored === "dark" : prefersDark);
  $("#theme-toggle").addEventListener("click", () => applyTheme(!document.body.classList.contains("dark")));
}

function applyFilters() {
  const showForming = $("#toggle-forming").checked;
  cy.batch(() => cy.nodes().forEach((n) =>
    n.style("display", (n.data("forming") && !showForming) ? "none" : "element")));
}

// What the map shows is driven by what you are looking at, not by a standing setting.
// Blocking links are OFF by default — drawn across the whole state at once they are noise —
// and appear for whatever you select, or across the board on the Powers tab, where they are
// the subject. Two checkboxes override: show blocking everywhere, or hide the structural
// spine so the blocking layer reads on its own.
let activeTab = "info";

function applyMapMode() {
  if (!cy) return;
  const always = $("#toggle-vetoes") && $("#toggle-vetoes").checked;
  const structuralOn = !$("#toggle-sponsors") || $("#toggle-sponsors").checked;
  const onPowers = activeTab === "powers";
  cy.batch(() => {
    // The two layers genuinely SWAP. Off the Powers tab you get accountability — who
    // sponsors whom, who answers to which minister. On the Powers tab you get obstruction.
    // Showing both at once for the selected node was the muddle: it looked like the blocking
    // layer never turned off.
    cy.edges("[kind = 'can_veto']").toggleClass("veto-hide", !(always || onPowers));
    cy.edges(STRUCTURAL).toggleClass("struct-hide", !structuralOn)
      .toggleClass("struct-quiet", structuralOn && onPowers);
  });
  // Re-run the highlight so the thread reflects the layer now on show.
  if (selectedId) {
    const n = cy.getElementById(selectedId);
    if (!n.empty()) highlightThread(n);
  }
}

// Gold halo on every regulator, wherever it sits in the rings — the cross-cutting view
// the body_type axis can't give (regulators span four legal forms).
function applyRegulatorHighlight() {
  const on = $("#toggle-regulators").checked;
  cy.batch(() => {
    cy.nodes().removeClass("func-hl");
    if (on) cy.nodes().filter((n) => (n.data("functions") || []).includes("regulation")).addClass("func-hl");
  });
}
