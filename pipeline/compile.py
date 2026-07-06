#!/usr/bin/env python3
"""Compile the record set into the map/query artefacts.

One job: read everything in data/ and emit
  - compiled/graph.json          the office-centred graph the Cytoscape map reads
  - compiled/state_machine.sqlite a queryable mirror (one table per record type)
  - manifest.json (refreshed)     counts, generated timestamp, annex version

No network. Reads only; never writes into data/. Deterministic apart from the
generated timestamp. Re-runnable.

    py -3 pipeline/compile.py

Boring by design: stdlib only (json, sqlite3), one job.
"""
import datetime
import glob
import json
import os
import sqlite3

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (this file lives in pipeline/)
DATA = os.path.join(REPO, "data")
COMPILED = os.path.join(REPO, "compiled")
GRAPH_JSON = os.path.join(COMPILED, "graph.json")
SQLITE = os.path.join(COMPILED, "state_machine.sqlite")
MANIFEST = os.path.join(REPO, "manifest.json")
ANNEX_A_VERSION = "0.4"


def load_dir(name):
    return [load(p) for p in sorted(glob.glob(os.path.join(DATA, name, "*.json")))]


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def build_graph(bodies, relationships, offices, person_roles):
    """Office-centred graph: bodies and offices are nodes; sponsor edges join bodies,
    host edges join each office to the body it sits in. The current holder is an
    attribute of the office node (people at the centre, per decision #13)."""
    holders = {}  # office_id -> list of (person_name, start_date)
    for pr in person_roles:
        if pr.get("is_current"):
            holders.setdefault(pr["office_id"], []).append((pr["person_name"], pr.get("start_date")))

    nodes, edges = [], []
    for b in bodies:
        nodes.append({"data": {
            "id": b["body_id"],
            "label": b["name"],
            "kind": "body",
            "body_type": b["body_type"],
            "status": b["status"],
            "needs_review": b.get("needs_classification_review", False),
            "functions": b.get("functions", []),
            "sponsor_department_id": b.get("sponsor_department_id"),
            "parent_body_id": b.get("parent_body_id"),
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


def build_sqlite(bodies, relationships, offices, person_roles, sources):
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
    con.commit()
    con.close()


def main():
    bodies = load_dir("bodies")
    relationships = load_dir("relationships")
    offices = load_dir("offices")
    person_roles = load_dir("person-roles")
    sources = load_dir("sources")

    counts = {"bodies": len(bodies), "relationships": len(relationships),
              "offices": len(offices), "person_roles": len(person_roles), "sources": len(sources)}

    graph = build_graph(bodies, relationships, offices, person_roles)
    generated = datetime.datetime.now().isoformat(timespec="seconds")
    graph_out = {"generated": generated, "counts": counts,
                 "nodes": graph["nodes"], "edges": graph["edges"]}
    write_json(GRAPH_JSON, graph_out)

    build_sqlite(bodies, relationships, offices, person_roles, sources)

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
        print("  {:14} {}".format(k, v))
    print("  graph nodes:   {}".format(len(graph["nodes"])))
    print("  graph edges:   {}".format(len(graph["edges"])))
    print("wrote:")
    print("  {}".format(os.path.relpath(GRAPH_JSON, REPO)))
    print("  {}".format(os.path.relpath(SQLITE, REPO)))
    print("  {}".format(os.path.relpath(MANIFEST, REPO)))


if __name__ == "__main__":
    main()
