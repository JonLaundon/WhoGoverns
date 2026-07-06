/* WhoGoverns map face. Reads compiled/graph.json, renders an office-centred
   Cytoscape graph, and drives search + an entity details panel where every claim
   links to its source. Boring by design: one file, no framework, no build step.
   Serve from the repo root (py -3 -m http.server) and open /site/. */

"use strict";

// Human labels + colours per type. Colours are ordinary web colours (GDS palette
// values are not restricted; the GDS Transport font and Crown logo are, and are not used).
const BODY_TYPES = {
  ministerial_department:      ["Ministerial department", "#1d70b8"],
  non_ministerial_department:  ["Non-ministerial department", "#28a197"],
  executive_agency:            ["Executive agency", "#00703c"],
  division_directorate:        ["Division / directorate", "#85994b"],
  executive_ndpb:              ["Executive NDPB", "#4c2c92"],
  advisory_ndpb:               ["Advisory NDPB", "#d53880"],
  tribunal:                    ["Tribunal", "#f47738"],
  public_corporation:          ["Public corporation", "#b58840"],
  royal_charter_body:          ["Royal charter body", "#942514"],
  other_body:                  ["Other body", "#626a6e"],
};
const OFFICE_TYPES = {
  prime_minister:   ["Prime Minister", "#0b0c0c"],
  cabinet_minister: ["Cabinet minister", "#d4351c"],
  junior_minister:  ["Junior minister", "#e8869a"],
  other:            ["Other office", "#909699"],
};

// Concentric level — higher sits nearer the centre (office-centred: PM in the middle).
function level(d) {
  if (d.kind === "office") {
    return { prime_minister: 10, cabinet_minister: 8, junior_minister: 5, other: 5 }[d.office_type] || 5;
  }
  return {
    ministerial_department: 7, non_ministerial_department: 6, public_corporation: 4,
    executive_agency: 4, executive_ndpb: 4, advisory_ndpb: 3, tribunal: 3,
    division_directorate: 2, royal_charter_body: 2, other_body: 2,
  }[d.body_type] || 2;
}

let cy;                 // cytoscape instance
let searchIndex = [];   // [{id, label, sub, text}]
let GENERATED = "";

const $ = (sel) => document.querySelector(sel);

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

  // Enrich node data with presentation fields, and build the search index.
  graph.nodes.forEach((n) => {
    const d = n.data;
    if (d.kind === "office") {
      d.color = (OFFICE_TYPES[d.office_type] || OFFICE_TYPES.other)[1];
      d.shape = "diamond";
      d.size = d.office_type === "prime_minister" ? 30 : 18;
    } else {
      d.color = (BODY_TYPES[d.body_type] || BODY_TYPES.other_body)[1];
      d.shape = "ellipse";
      d.size = d.body_type === "ministerial_department" ? 34
             : d.body_type === "non_ministerial_department" ? 24 : 16;
    }
    d.forming = d.status === "forming";
    const aliases = (d.other_names || []).join(" ");
    const sub = d.kind === "office"
      ? (OFFICE_TYPES[d.office_type] || OFFICE_TYPES.other)[0] + (d.holder ? " · " + d.holder : "")
      : (BODY_TYPES[d.body_type] || BODY_TYPES.other_body)[0];
    searchIndex.push({ id: d.id, label: d.label, sub, text: (d.label + " " + aliases + " " + (d.holder || "")).toLowerCase() });
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
        "text-background-color": "#fff", "text-background-opacity": 0.85,
        "text-background-padding": 2, "min-zoomed-font-size": 8,
      }},
      { selector: "node[?forming]", style: { "border-style": "dashed", "border-width": 2, "border-color": "#0b0c0c" } },
      { selector: "edge", style: {
        "curve-style": "bezier", "width": 1, "line-color": "#c7cacb",
        "target-arrow-color": "#c7cacb", "target-arrow-shape": "triangle", "arrow-scale": 0.55,
      }},
      { selector: "edge[kind = 'office_of']", style: { "line-color": "#e3b7be", "line-style": "dashed", "target-arrow-shape": "none" } },
      { selector: ".faded", style: { "opacity": 0.12, "text-opacity": 0 } },
      { selector: "node.hl", style: { "label": "data(label)", "z-index": 99, "border-width": 2, "border-color": "#0b0c0c" } },
      { selector: "node:selected", style: { "label": "data(label)", "border-width": 3, "border-color": "#0b0c0c", "z-index": 100, "font-size": 11, "font-weight": "bold" } },
    ],
    layout: { name: "concentric", concentric: (n) => level(n.data()), levelWidth: () => 2, minNodeSpacing: 8, spacingFactor: 0.9 },
  });

  cy.on("tap", "node", (e) => selectNode(e.target.id()));
  cy.on("tap", (e) => { if (e.target === cy) clearFocus(); });

  buildLegend();
  wireControls();
  $("#counts").textContent =
    `${graph.counts.bodies} bodies · ${graph.counts.relationships} sponsor links · ` +
    `${graph.counts.offices} offices · ${graph.counts.person_roles} ministers`;
  if (GENERATED) $("#generated").textContent = "Compiled " + GENERATED.replace("T", " ");
}

/* ---------- focus + selection ---------- */
function selectNode(id) {
  const node = cy.getElementById(id);
  if (node.empty()) return;
  cy.elements().removeClass("hl").addClass("faded");
  const nbh = node.closedNeighborhood();
  nbh.removeClass("faded");
  nbh.nodes().addClass("hl");
  cy.$(":selected").unselect();
  node.select();
  cy.animate({ center: { eles: node }, zoom: Math.max(cy.zoom(), 1.1) }, { duration: 250 });
  renderDetail(node.data());
}

function clearFocus() {
  cy.elements().removeClass("faded hl");
  cy.$(":selected").unselect();
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

function nodeLabel(id) {
  const n = cy.getElementById(id);
  return n.empty() ? id : n.data("label");
}
function gotoBtn(id) {
  if (!id || cy.getElementById(id).empty()) return id ? esc(id) : "—";
  return `<button class="linkish" data-goto="${esc(id)}">${esc(nodeLabel(id))}</button>`;
}
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

function bodyHtml(d) {
  const type = (BODY_TYPES[d.body_type] || BODY_TYPES.other_body)[0];
  const govuk = d.govuk_slug ? `https://www.gov.uk/government/organisations/${d.govuk_slug}` : null;
  // Ministers hosted here = office nodes whose body_id points at this body.
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
      (Open Government Licence v3.0). Ministers from the GOV.UK content API.</p>`;
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
      Office type is a heuristic tier — see the project notes.</p>`;
}

/* ---------- legend ---------- */
function buildLegend() {
  const rows = (title, map, cls) => `<h3>${title}</h3>` + Object.values(map).map(([label, color]) =>
    `<div class="row"><span class="swatch ${cls}" style="background:${color}"></span>${esc(label)}</div>`).join("");
  $("#legend").innerHTML = rows("Bodies", BODY_TYPES, "") + rows("Offices", OFFICE_TYPES, "office") +
    `<h3>Marks</h3><div class="row"><span class="swatch" style="background:#fff;border:2px dashed #0b0c0c"></span>dashed = in formation</div>`;
}

/* ---------- search ---------- */
function wireControls() {
  const input = $("#search-input");
  const results = $("#search-results");
  let matches = [];

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    results.innerHTML = "";
    if (q.length < 2) return;
    matches = searchIndex.filter((r) => r.text.includes(q)).slice(0, 14);
    results.innerHTML = matches.map((m, i) =>
      `<li role="option" data-id="${esc(m.id)}" ${i === 0 ? 'aria-selected="true"' : ""}>` +
      `${esc(m.label)}<div class="r-sub">${esc(m.sub)}</div></li>`).join("");
    results.querySelectorAll("li").forEach((li) =>
      li.addEventListener("click", () => { selectNode(li.getAttribute("data-id")); }));
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && matches.length) { e.preventDefault(); selectNode(matches[0].id); }
  });

  $("#toggle-offices").addEventListener("change", applyFilters);
  $("#toggle-forming").addEventListener("change", applyFilters);
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
