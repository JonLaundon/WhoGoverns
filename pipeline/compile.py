#!/usr/bin/env python3
"""Compile the record set into the map/query artefacts.

One job: read everything in data/ and emit
  - compiled/graph.json          the office-centred graph the Cytoscape map reads
  - compiled/state_machine.sqlite a queryable mirror (one table per record type)
  - manifest.json (refreshed)     counts, generated timestamp, annex version

The graph carries two layers. STRUCTURE (Spiral 1): bodies and offices as nodes, sponsor
and derived `leads` edges. OPERATIVE (Spiral 2, Annex A6): each holder node gains an
`operative` block of its cited powers, duties and vetoes — card-ready, each with its
citation, its "since" year and its assurance tier — and every veto with a modelled blocked
party becomes a first-class `can_veto` EDGE. Those edges are what the structural graph could
never express: they run sideways across the sponsor hierarchy (HM Treasury -> Defra), which
is exactly why "who can legally block this?" was unanswerable before them.

Vetoes over parties outside the modelled state (a private abstractor, an owner/occupier)
correctly draw no edge — validate.py warns so the gap stays a conscious choice.

No network. Reads only; never writes into data/. Deterministic apart from the
generated timestamp. Re-runnable.

    py -3 pipeline/compile.py

Boring by design: stdlib only (json, sqlite3), one job.
"""
import datetime
import json
import os
import sqlite3

import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (this file lives in pipeline/)
DATA = os.path.join(REPO, "data")
COMPILED = os.path.join(REPO, "compiled")
GRAPH_JSON = os.path.join(COMPILED, "graph.json")
SQLITE = os.path.join(COMPILED, "state_machine.sqlite")
MANIFEST = os.path.join(REPO, "manifest.json")
ANNEX_A_VERSION = "0.4"

# A department parent is a body's sponsor; any other parent is its parent_body.
DEPARTMENT_TYPES = {"ministerial_department", "non_ministerial_department"}


def load_dir(name):
    return store.load(name)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def load_records_by_body(t):
    """Group a bulk dataset's flat array into body_id -> [records]."""
    by_body = {}
    for rec in store.load(t):
        by_body.setdefault(rec["body_id"], []).append(rec)
    return by_body


def summarise_budget(recs):
    head, progs, income = {}, [], []
    for r in recs:
        if r["budget_type"] == "income" and r.get("programme"):
            income.append({"name": r["programme"], "value": r["amount"]})
        elif r.get("programme"):
            if r["budget_type"] == "resource_del" and r.get("basis") == "net":
                progs.append({"name": r["programme"], "net": r["amount"]})
        else:
            head["{}_{}".format(r["budget_type"], r.get("basis", "net"))] = r["amount"]
    progs.sort(key=lambda x: -x["net"])
    income.sort(key=lambda x: -x["value"])
    src = sorted({r["source_id"] for r in recs if r.get("source_id")})
    return {"fy": recs[0]["financial_year"], "headline": head, "programmes": progs,
            "income": income, "source_ids": src}


def _summ_staffing_set(recs):
    total_hc = total_fte = disclaimer = None
    grades, profs = {}, []
    for r in recs:
        if r.get("notes"):
            disclaimer = r["notes"]
        if r["grade"] is None and r["profession"] is None:
            if r["metric"] == "headcount":
                total_hc = r["value"]
            else:
                total_fte = r["value"]
        elif r["grade"]:
            grades.setdefault(r["grade"], {})[r["metric"]] = r["value"]
        elif r["profession"] and r["metric"] == "headcount":
            profs.append({"name": r["profession"], "headcount": r["value"]})
    profs.sort(key=lambda x: -x["headcount"])
    order = ["scs", "grade_6_7", "seo_heo", "eo", "aa_ao", "unreported"]
    glist = [dict(grade=g, **grades[g]) for g in order if g in grades]
    return {"headcount_total": total_hc, "fte_total": total_fte,
            "grades": glist, "professions": profs, "disclaimer": disclaimer}


def summarise_staffing(recs):
    # Top-level fields are the GROUP/primary figure (backward-compatible); `core` holds the
    # department's excl-agencies figure for the whole-group/core toggle (null for others).
    group = [r for r in recs if r.get("scope") in (None, "group")]
    core = [r for r in recs if r.get("scope") == "core"]
    g = _summ_staffing_set(group)
    c = _summ_staffing_set(core) if core else None
    # Where core == group the body has no real agencies (identical "Overall" and plain rows):
    # collapse to a single figure — no whole-group/core toggle, no double-count disclaimer.
    if c and c.get("headcount_total") == g.get("headcount_total"):
        c, g["disclaimer"] = None, None
    out = {"period": recs[0]["period"]}
    out.update(g)
    out["core"] = c
    out["source_ids"] = sorted({r["source_id"] for r in recs if r.get("source_id")})
    return out


# --- Operative layer (Annex A6): powers, duties and vetoes onto the map ------------------
# The Spiral 1 graph carried structure only. These helpers put the cited legal records on
# the nodes (so an entity card can render them) and the blocking relation on the edges (so
# "who can block this?" is answerable by traversal rather than by re-reading statute).

# Which of the three colour axes a veto belongs to. DERIVED ONLY from sourced fields —
# never a hand-kept list of bodies, which would be an uncited taxonomy in the presentation
# layer (A2.2/A2.8). Order matters: a funding consent held by a Minister is fiscal first.
# English, not string concatenation: "duty" + "s" is not "duties".
PLURAL = {"power": "powers", "duty": "duties", "veto": "vetoes"}


def blocker_kind(veto, power_by_id, body_by_id):
    src = power_by_id.get(veto.get("derived_from_record_id")) or {}
    ptype = src.get("power_type")
    funcs = set((body_by_id.get(veto.get("body_id")) or {}).get("functions") or [])
    if ptype == "adjudication" or "judicial" in funcs:
        return "judicial"
    if ptype in ("funding", "charging"):
        return "fiscal"
    if "regulation" in funcs:
        return "regulatory"
    # A Minister blocking a decision is a real, distinct category from a regulator doing
    # so, and it is derivable from the office tier — without it, ministerial consents
    # (3 of the 8 Water vetoes) fall through uncoloured.
    if veto.get("holder_type") == "office":
        return "ministerial"
    return None


def _since(rec, provision_by_key, instrument_by_id):
    """The year the authority dates from, via provision -> instrument (the MoG 'Since YYYY')."""
    prov = provision_by_key.get(rec.get("provision_key")) or {}
    return (instrument_by_id.get(prov.get("instrument_id")) or {}).get("year")


def summarise_operative(rec, kind, ctx):
    """One cited legal record, flattened for an entity card. Carries its own assurance."""
    out = {
        "id": rec[{"power": "power_id", "duty": "duty_id", "veto": "veto_id"}[kind]],
        "kind": kind,
        "label": rec.get(kind + "_label"),
        "type": rec.get(kind + "_type"),
        "summary": rec.get("summary"),
        "since": _since(rec, ctx["provisions"], ctx["instruments"]),
        "citation": rec.get("citation"),
        "source_id": rec.get("source_id"),
        "provision_key": rec.get("provision_key"),
        "holder_type": rec.get("holder_type"),
        "office_id": rec.get("office_id"),
        "legal_status": rec.get("legal_status"),
        # Assurance on the face of the card — the differentiator the precedent lacks.
        "verification_status": (rec.get("verification") or {}).get("verification_status"),
        "confidence": (rec.get("extraction") or {}).get("confidence"),
        "notes": rec.get("notes"),
    }
    prov = ctx["provisions"].get(rec.get("provision_key")) or {}
    if prov.get("outstanding_effects"):
        out["outstanding_effects"] = True   # consolidation-lag badge
    if kind == "power":
        out.update({"legal_effect": rec.get("legal_effect"), "basis": rec.get("power_basis"),
                    "constraints": rec.get("constraints") or []})
    elif kind == "duty":
        out.update({"mandatory": rec.get("mandatory")})
    elif kind == "veto":
        out.update({
            "strength": rec.get("strength"),
            "overridable": rec.get("overridable"),
            "override_mechanism": rec.get("override_mechanism"),
            "decision_affected": rec.get("decision_affected"),
            "derived_from_record_id": rec.get("derived_from_record_id"),
            "blocks_body_id": rec.get("blocks_body_id"),
            "blocks_office_id": rec.get("blocks_office_id"),
            "blocker_kind": blocker_kind(rec, ctx["powers"], ctx["bodies"]),
        })
    return out


def attach_operative(graph, powers, duties, vetoes, provisions, instruments, bodies):
    """Hang the operative records on their holder nodes and add the CAN_VETO edges.

    A record held by an office attaches to that office's node where one exists (offices are
    consolidated by person in build_graph, so some do not survive as nodes) and otherwise
    falls back to the hosting body — a power must never vanish because its office was folded
    away. Bodies additionally carry `office_operative`: the records held by offices hosted
    there, so a department's card can show what its ministers hold without double-counting.
    """
    ctx = {"provisions": {p["provision_key"]: p for p in provisions},
           "instruments": {i["instrument_id"]: i for i in instruments},
           "powers": {p["power_id"]: p for p in powers},
           "bodies": {b["body_id"]: b for b in bodies}}
    node_by_id = {n["data"]["id"]: n for n in graph["nodes"]}

    def holder_node(rec):
        if rec.get("holder_type") == "office" and rec.get("office_id") in node_by_id:
            return rec["office_id"]
        return rec.get("body_id")

    for recs, kind in ((powers, "power"), (duties, "duty"), (vetoes, "veto")):
        for rec in recs:
            card = summarise_operative(rec, kind, ctx)
            nid = holder_node(rec)
            node = node_by_id.get(nid)
            if not node:
                continue
            bucket = PLURAL[kind]
            node["data"].setdefault("operative", {}).setdefault(bucket, []).append(card)
            # Mirror office-held records onto the hosting body, flagged as held via an office.
            host = rec.get("body_id")
            if nid != host and host in node_by_id:
                node_by_id[host]["data"].setdefault("office_operative", {}) \
                    .setdefault(bucket, []).append(card)

    # Node rollups: counts for a tab badge, and the blocker kinds present for the legend.
    for n in graph["nodes"]:
        op = n["data"].get("operative")
        if not op:
            continue
        for key in ("powers", "duties", "vetoes"):
            op.setdefault(key, []).sort(key=lambda c: (-(c.get("since") or 0), c["id"]))
        op["counts"] = {k: len(op[k]) for k in ("powers", "duties", "vetoes")}
        kinds = sorted({v["blocker_kind"] for v in op["vetoes"] if v.get("blocker_kind")})
        if kinds:
            op["blocker_kinds"] = kinds

    # CAN_VETO edges: the blocking relation as a first-class traversable edge. These run
    # SIDEWAYS across the sponsor hierarchy (HM Treasury -> Defra), which is exactly why the
    # structural graph alone could never answer "who can block this?".
    for v in vetoes:
        target = (v.get("blocks_office_id") if v.get("blocks_holder_type") == "office"
                  and v.get("blocks_office_id") in node_by_id else v.get("blocks_body_id"))
        source = holder_node(v)
        if not target or target not in node_by_id or source not in node_by_id:
            continue
        graph["edges"].append({"data": {
            "id": "canveto-" + v["veto_id"],
            "source": source,
            "target": target,
            "kind": "can_veto",
            "veto_id": v["veto_id"],
            "strength": v.get("strength"),
            "blocker_kind": blocker_kind(v, ctx["powers"], ctx["bodies"]),
            "decision_affected": v.get("decision_affected"),
            "source_id": v.get("source_id"),
        }})


def build_graph(bodies, relationships, offices, person_roles):
    """Office-centred graph: bodies and offices are nodes; sponsor edges join bodies,
    host edges join each office to the body it sits in. The current holder is an
    attribute of the office node (people at the centre, per decision #13)."""
    holders = {}  # office_id -> list of (person_name, start_date)
    for pr in person_roles:
        if pr.get("is_current"):
            holders.setdefault(pr["office_id"], []).append((pr["person_name"], pr.get("start_date")))

    # Sponsor/parent derived from the canonical relationship edges (#8): the relationships
    # are the single source of truth, so the map, details panel and radial layout can never
    # disagree with them the way a separately-stored body field could. A department parent is
    # the sponsor; any other parent is the parent_body. The single scalar keeps the
    # deterministic first-alphabetical choice (for the tree layout, which needs one parent);
    # the full lists are exposed too, so joint sponsorship is never truncated.
    btype = {b["body_id"]: b["body_type"] for b in bodies}
    dept_parents, other_parents = {}, {}
    for r in relationships:
        if r.get("relationship_type") != "sponsors":
            continue
        child, parent = r["to_body_id"], r["from_body_id"]
        bucket = dept_parents if btype.get(parent) in DEPARTMENT_TYPES else other_parents
        bucket.setdefault(child, set()).add(parent)
    dept_of = {c: sorted(ps) for c, ps in dept_parents.items()}
    parent_of = {c: sorted(ps) for c, ps in other_parents.items()}

    nodes, edges = [], []
    for b in bodies:
        bid = b["body_id"]
        depts, parents = dept_of.get(bid, []), parent_of.get(bid, [])
        nodes.append({"data": {
            "id": bid,
            "label": b["name"],
            "kind": "body",
            "body_type": b["body_type"],
            "status": b["status"],
            "needs_review": b.get("needs_classification_review", False),
            "functions": b.get("functions", []),
            "source_ids": sorted(set(b.get("classification_source_ids", [])
                                     + b.get("function_source_ids", []))),
            "sponsor_department_id": depts[0] if depts else None,
            "parent_body_id": parents[0] if parents else None,
            "sponsor_department_ids": depts,
            "parent_body_ids": parents,
            "govuk_slug": b.get("govuk_organisation_slug"),
            "other_names": b.get("other_names", []),
        }})
    # Consolidate offices by person: one node per office-holder, at their most senior
    # office. A person's other titles (the PM is also First Lord of the Treasury, etc.)
    # fold into that node's `also_holds` instead of spawning extra nodes — which also
    # clears the stray "other" office nodes that weren't in the PM's leads chain.
    holder_of = {}
    for pr in person_roles:
        if pr.get("is_current") and pr["office_id"] not in holder_of:
            holder_of[pr["office_id"]] = pr["person_name"]
    seniority = {"prime_minister": 5, "cabinet_minister": 4, "junior_minister": 3,
                 "independent_official": 2, "civil_servant": 2, "other": 1}
    by_person = {}
    for o in offices:
        person = holder_of.get(o["office_id"])
        if person:
            by_person.setdefault(person, []).append(o)
    primary_ids, also_holds = set(), {}
    for offs in by_person.values():
        offs.sort(key=lambda o: (-seniority.get(o.get("office_type"), 0), o["office_id"]))
        primary_ids.add(offs[0]["office_id"])
        also_holds[offs[0]["office_id"]] = [o["title"] for o in offs[1:]]
    for o in offices:
        if o["office_id"] not in holder_of:
            primary_ids.add(o["office_id"])   # an office with no current holder stands alone

    for o in offices:
        if o["office_id"] not in primary_ids:
            continue
        held = holders.get(o["office_id"], [])
        nodes.append({"data": {
            "id": o["office_id"], "label": o["title"], "kind": "office",
            "office_type": o.get("office_type"), "body_id": o["body_id"],
            "holder": held[0][0] if held else None,
            "holder_since": held[0][1] if held else None,
            "also_holds": also_holds.get(o["office_id"], []),
        }})
        edges.append({"data": {"id": "hostedge-" + o["office_id"],
                               "source": o["office_id"], "target": o["body_id"], "kind": "office_of"}})
    for r in relationships:
        edges.append({"data": {
            "id": r["relationship_id"],
            "source": r["from_body_id"],
            "target": r["to_body_id"],
            "kind": r["relationship_type"],
            "source_id": r.get("source_id"),  # #6: keep the provenance of the sponsor claim
        }})

    # Derived governance edges (by convention — NOT raw data, so they live only here,
    # flagged derived:true): the Prime Minister leads the cabinet; within a department
    # its cabinet minister(s) lead its junior ministers. This is what makes the map read
    # as an org chart (PM -> cabinet -> junior) rather than each office floating by its body.
    pm = next((o for o in offices if o.get("office_type") == "prime_minister" and o["office_id"] in primary_ids), None)
    by_body = {}
    for o in offices:
        if o["office_id"] in primary_ids:
            by_body.setdefault(o["body_id"], []).append(o)
    if pm:
        for c in offices:
            if c.get("office_type") == "cabinet_minister" and c["office_id"] in primary_ids:
                edges.append({"data": {"id": "leads-{}-{}".format(pm["office_id"], c["office_id"]),
                                       "source": pm["office_id"], "target": c["office_id"],
                                       "kind": "leads", "derived": True}})
    for offs in by_body.values():
        cabs = [o for o in offs if o.get("office_type") == "cabinet_minister"]
        juns = [o for o in offs if o.get("office_type") == "junior_minister"]
        for j in juns:
            for c in cabs:
                edges.append({"data": {"id": "leads-{}-{}".format(c["office_id"], j["office_id"]),
                                       "source": c["office_id"], "target": j["office_id"],
                                       "kind": "leads", "derived": True}})
    # Fallback: a junior minister at a body with no cabinet minister (e.g. the law officers'
    # standalone offices, like the Advocate General for Scotland) still answers to the PM —
    # link it to the PM directly so it isn't left orphaned on the ring.
    if pm:
        led = {e["data"]["target"] for e in edges if e["data"]["kind"] == "leads"}
        for o in offices:
            if o.get("office_type") == "junior_minister" and o["office_id"] in primary_ids and o["office_id"] not in led:
                edges.append({"data": {"id": "leads-{}-{}".format(pm["office_id"], o["office_id"]),
                                       "source": pm["office_id"], "target": o["office_id"],
                                       "kind": "leads", "derived": True}})
    return {"nodes": nodes, "edges": edges}


def build_sqlite_operative(cur, powers, duties, vetoes, instruments, provisions):
    """The operative layer as query tables — this is what the MCP/query layer (U12) reads,
    and what makes 'who can block X?' a SQL join rather than a statute-reading exercise."""
    cur.executescript("""
        CREATE TABLE powers (power_id TEXT PRIMARY KEY, power_label TEXT, power_type TEXT,
            power_basis TEXT, modality TEXT, legal_effect TEXT, holder_type TEXT, body_id TEXT,
            office_id TEXT, summary TEXT, source_id TEXT, provision_key TEXT, provision TEXT,
            url TEXT, legal_status TEXT, verification_status TEXT, confidence REAL,
            record_status TEXT);
        CREATE TABLE duties (duty_id TEXT PRIMARY KEY, duty_label TEXT, duty_type TEXT,
            modality TEXT, holder_type TEXT, body_id TEXT, office_id TEXT, summary TEXT,
            source_id TEXT, provision_key TEXT, provision TEXT, url TEXT, legal_status TEXT,
            verification_status TEXT, confidence REAL, record_status TEXT);
        CREATE TABLE vetoes (veto_id TEXT PRIMARY KEY, veto_label TEXT, veto_type TEXT,
            strength TEXT, overridable TEXT, override_mechanism TEXT, holder_type TEXT,
            body_id TEXT, office_id TEXT, blocks_body_id TEXT, blocks_office_id TEXT,
            decision_affected TEXT, derived_from_record_id TEXT, summary TEXT, source_id TEXT,
            provision_key TEXT, provision TEXT, url TEXT, verification_status TEXT,
            confidence REAL, record_status TEXT);
        CREATE TABLE instruments (instrument_id TEXT PRIMARY KEY, title TEXT,
            instrument_type TEXT, year INTEGER, number TEXT, status TEXT, source_id TEXT,
            legislation_url TEXT);
        CREATE TABLE provisions (provision_key TEXT PRIMARY KEY, instrument_id TEXT,
            provision_ref TEXT, heading TEXT, status TEXT, url TEXT, version_date TEXT,
            outstanding_effects INTEGER);
        CREATE INDEX idx_vetoes_blocks_body ON vetoes(blocks_body_id);
        CREATE INDEX idx_vetoes_blocks_office ON vetoes(blocks_office_id);
        CREATE INDEX idx_powers_body ON powers(body_id);
    """)
    for p in powers:
        c = p.get("citation") or {}
        cur.execute("INSERT INTO powers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            p["power_id"], p.get("power_label"), p.get("power_type"), p.get("power_basis"),
            p.get("modality"), p.get("legal_effect"), p.get("holder_type"), p.get("body_id"),
            p.get("office_id"), p.get("summary"), p.get("source_id"), p.get("provision_key"),
            c.get("provision"), c.get("url"), p.get("legal_status"),
            (p.get("verification") or {}).get("verification_status"),
            (p.get("extraction") or {}).get("confidence"), p.get("record_status")))
    for d in duties:
        c = d.get("citation") or {}
        cur.execute("INSERT INTO duties VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            d["duty_id"], d.get("duty_label"), d.get("duty_type"), d.get("modality"),
            d.get("holder_type"), d.get("body_id"), d.get("office_id"), d.get("summary"),
            d.get("source_id"), d.get("provision_key"), c.get("provision"), c.get("url"),
            d.get("legal_status"), (d.get("verification") or {}).get("verification_status"),
            (d.get("extraction") or {}).get("confidence"), d.get("record_status")))
    for v in vetoes:
        c = v.get("citation") or {}
        cur.execute("INSERT INTO vetoes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            v["veto_id"], v.get("veto_label"), v.get("veto_type"), v.get("strength"),
            v.get("overridable"), v.get("override_mechanism"), v.get("holder_type"),
            v.get("body_id"), v.get("office_id"), v.get("blocks_body_id"),
            v.get("blocks_office_id"), v.get("decision_affected"),
            v.get("derived_from_record_id"), v.get("summary"), v.get("source_id"),
            v.get("provision_key"), c.get("provision"), c.get("url"),
            (v.get("verification") or {}).get("verification_status"),
            (v.get("extraction") or {}).get("confidence"), v.get("record_status")))
    for i in instruments:
        cur.execute("INSERT INTO instruments VALUES (?,?,?,?,?,?,?,?)", (
            i["instrument_id"], i.get("title"), i.get("instrument_type"), i.get("year"),
            i.get("number"), i.get("status"), i.get("source_id"), i.get("legislation_url")))
    for pr in provisions:
        c = pr.get("citation") or {}
        cur.execute("INSERT INTO provisions VALUES (?,?,?,?,?,?,?,?)", (
            pr["provision_key"], pr.get("instrument_id"), pr.get("provision_ref"),
            pr.get("heading"), pr.get("status"), c.get("url"), c.get("version_date"),
            1 if pr.get("outstanding_effects") else 0))


def build_sqlite(bodies, relationships, offices, person_roles, sources,
                 powers=(), duties=(), vetoes=(), instruments=(), provisions=()):
    if os.path.exists(SQLITE):
        os.remove(SQLITE)
    os.makedirs(COMPILED, exist_ok=True)
    con = sqlite3.connect(SQLITE)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE bodies (body_id TEXT PRIMARY KEY, name TEXT, body_type TEXT, status TEXT,
            jurisdiction TEXT, sponsor_department_id TEXT, parent_body_id TEXT, govuk_slug TEXT,
            needs_classification_review INTEGER, record_status TEXT);
        CREATE TABLE other_names (body_id TEXT, name TEXT);
        CREATE TABLE relationships (relationship_id TEXT PRIMARY KEY, from_body_id TEXT,
            to_body_id TEXT, relationship_type TEXT, source_id TEXT);
        CREATE TABLE offices (office_id TEXT PRIMARY KEY, title TEXT, body_id TEXT,
            office_type TEXT, record_status TEXT);
        CREATE TABLE person_roles (person_role_id TEXT PRIMARY KEY, person_name TEXT,
            office_id TEXT, body_id TEXT, start_date TEXT, is_current INTEGER, record_status TEXT);
        CREATE TABLE sources (source_id TEXT PRIMARY KEY, title TEXT, source_type TEXT,
            url TEXT, accessed_date TEXT);
    """)
    for b in bodies:
        cur.execute("INSERT INTO bodies VALUES (?,?,?,?,?,?,?,?,?,?)", (
            b["body_id"], b["name"], b["body_type"], b["status"], ",".join(b.get("jurisdiction", [])),
            b.get("sponsor_department_id"), b.get("parent_body_id"), b.get("govuk_organisation_slug"),
            1 if b.get("needs_classification_review") else 0, b.get("record_status")))
        for n in b.get("other_names", []):
            cur.execute("INSERT INTO other_names VALUES (?,?)", (b["body_id"], n))
    for r in relationships:
        cur.execute("INSERT INTO relationships VALUES (?,?,?,?,?)", (
            r["relationship_id"], r["from_body_id"], r["to_body_id"], r["relationship_type"], r.get("source_id")))
    for o in offices:
        cur.execute("INSERT INTO offices VALUES (?,?,?,?,?)", (
            o["office_id"], o["title"], o["body_id"], o.get("office_type"), o.get("record_status")))
    for pr in person_roles:
        cur.execute("INSERT INTO person_roles VALUES (?,?,?,?,?,?,?)", (
            pr["person_role_id"], pr["person_name"], pr["office_id"], pr["body_id"],
            pr.get("start_date"), 1 if pr.get("is_current") else 0, pr.get("record_status")))
    for s in sources:
        cur.execute("INSERT INTO sources VALUES (?,?,?,?,?)", (
            s["source_id"], s["title"], s["source_type"], s.get("url"), s.get("accessed_date")))
    build_sqlite_operative(cur, powers, duties, vetoes, instruments, provisions)
    con.commit()
    con.close()


def main():
    bodies = load_dir("bodies")
    relationships = load_dir("relationships")
    offices = load_dir("offices")
    person_roles = load_dir("person-roles")
    sources = load_dir("sources")

    powers = load_dir("powers")
    duties = load_dir("duties")
    vetoes = load_dir("vetoes")
    provisions = load_dir("provisions")
    instruments = load_dir("instruments")

    budgets_by_body = load_records_by_body("budgets")
    staffing_by_body = load_records_by_body("staffing")
    counts = {"bodies": len(bodies), "relationships": len(relationships),
              "offices": len(offices), "person_roles": len(person_roles), "sources": len(sources),
              "budget_records": sum(len(v) for v in budgets_by_body.values()),
              "staffing_records": sum(len(v) for v in staffing_by_body.values()),
              "powers": len(powers), "duties": len(duties), "vetoes": len(vetoes),
              "instruments": len(instruments), "provisions": len(provisions)}

    graph = build_graph(bodies, relationships, offices, person_roles)
    attach_operative(graph, powers, duties, vetoes, provisions, instruments, bodies)
    # Attach each body's budget/staffing summary to its node (ST5 entity tabs).
    for n in graph["nodes"]:
        if n["data"].get("kind") == "body":
            bid = n["data"]["id"]
            if bid in budgets_by_body:
                n["data"]["budget"] = summarise_budget(budgets_by_body[bid])
            if bid in staffing_by_body:
                n["data"]["staffing"] = summarise_staffing(staffing_by_body[bid])

    # Department "by body" (budget) / "by organisation" (staffing): the children it sponsors,
    # from the sponsor edges. Second pass so children's summaries already exist.
    DEPT = ("ministerial_department", "non_ministerial_department")
    node_by_id = {n["data"]["id"]: n for n in graph["nodes"]}
    children = {}
    for e in graph["edges"]:
        if e["data"].get("kind") == "sponsors":
            children.setdefault(e["data"]["source"], []).append(e["data"]["target"])
    for n in graph["nodes"]:
        if n["data"].get("body_type") not in DEPT:
            continue
        by_body, by_org = [], []
        for c in children.get(n["data"]["id"], []):
            cn = node_by_id.get(c)
            if not cn:
                continue
            label = cn["data"].get("label")
            cb = cn["data"].get("budget")
            if cb and cb["headline"].get("total_managed_expenditure_net"):
                by_body.append({"name": label, "value": cb["headline"]["total_managed_expenditure_net"]})
            cs = cn["data"].get("staffing")
            if cs and cs.get("headcount_total"):
                by_org.append({"name": label, "value": cs["headcount_total"]})
        if by_body and n["data"].get("budget"):
            n["data"]["budget"]["by_body"] = sorted(by_body, key=lambda x: -x["value"])
        if by_org and n["data"].get("staffing"):
            n["data"]["staffing"]["by_org"] = sorted(by_org, key=lambda x: -x["value"])
    generated = datetime.datetime.now().isoformat(timespec="seconds")
    # Source lookup so the map can cite each record's ACTUAL source(s), not a fixed blurb.
    source_index = {s["source_id"]: {"title": s.get("title"), "url": s.get("url"),
                                     "publisher": s.get("publisher")} for s in sources}
    graph_out = {"generated": generated, "counts": counts, "sources": source_index,
                 "nodes": graph["nodes"], "edges": graph["edges"]}
    write_json(GRAPH_JSON, graph_out)

    build_sqlite(bodies, relationships, offices, person_roles, sources,
                 powers, duties, vetoes, instruments, provisions)

    write_json(MANIFEST, {
        "project": "WhoGoverns",
        "working_name": "The State Machine",
        "annex_a_version": ANNEX_A_VERSION,
        "spiral": 1,
        "generated": generated,
        "record_counts": counts,
        "graph": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])},
        "notes": "Compiled by pipeline/compile.py from data/. graph.json is the map contract; "
                 "state_machine.sqlite is the query mirror (gitignored, regenerable).",
    })

    print("--- compile summary ---")
    for k, v in counts.items():
        print(f"  {k:14} {v}")
    print("  graph nodes:   {}".format(len(graph["nodes"])))
    print("  graph edges:   {}".format(len(graph["edges"])))
    print("wrote:")
    print(f"  {os.path.relpath(GRAPH_JSON, REPO)}")
    print(f"  {os.path.relpath(SQLITE, REPO)}")
    print(f"  {os.path.relpath(MANIFEST, REPO)}")


if __name__ == "__main__":
    main()
