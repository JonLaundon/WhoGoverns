#!/usr/bin/env python3
"""store.py — the single data-access layer for WhoGoverns.

Consolidated storage: each data type is ONE JSON array file, `data/<type>.json`, holding a
list of records. This replaces the earlier one-file-per-record layout (Annex A amended
2026-07-13: source data is one array per type — far fewer files, no OneDrive/git churn;
the compiled graph.json + SQLite remain the query layer). Records are kept sorted by their
primary key and written with sorted keys + a trailing newline, so diffs stay stable and a
one-record change shows as a small, readable hunk inside the array file.

Every pipeline script reads and writes through here, so the storage shape lives in one place.
"""
import json
import os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# data type -> primary-key field
PK = {
    "bodies": "body_id",
    "relationships": "relationship_id",
    "offices": "office_id",
    "person-roles": "person_role_id",
    "sources": "source_id",
    "budgets": "budget_record_id",
    "staffing": "staffing_record_id",
    # Powers layer (Annex A6, active from Spiral 2).
    "powers": "power_id",
    "duties": "duty_id",
    "vetoes": "veto_id",
    "instruments": "instrument_id",
    "provisions": "provision_key",
    "definitions": "definition_id",
}
TYPES = list(PK)


def path(t):
    return os.path.join(DATA, t + ".json")


def load(t):
    """All records of a type as a list ([] if the file does not exist yet)."""
    p = path(t)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def load_map(t):
    """{primary_key: record} for a type."""
    k = PK[t]
    return {r[k]: r for r in load(t)}


def save(t, records):
    """Write a type's records as one array file, sorted by primary key."""
    k = PK[t]
    recs = sorted(records, key=lambda r: str(r.get(k, "")))
    os.makedirs(DATA, exist_ok=True)
    with open(path(t), "w", encoding="utf-8") as fh:
        json.dump(recs, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def upsert(t, records):
    """Merge records into a type by primary key (incoming wins). Returns the count merged."""
    m = load_map(t)
    for r in records:
        m[r[PK[t]]] = r
    save(t, list(m.values()))
    return len(records)


def upsert_current_holders(records, retire_date):
    """Upsert person-role records while enforcing ONE current holder per office.

    A plain upsert() is additive: because a person-role id embeds the person's name, a
    reshuffle writes the successor under a NEW id and leaves the predecessor in place —
    still is_current=true — so one office ends up with two 'current' holders. This instead
    rebuilds the current-holder state: for every office named in `records`, any EXISTING
    current holder not in the incoming set is retired (is_current -> False, end_date ->
    retire_date if unset) rather than left standing. Offices absent from `records` are
    untouched, so one ingest never retires another ingest's holders. Retiring (with an end
    date) rather than deleting keeps the former holder as a deliberate historical record.
    Returns (merged_count, retired_count).
    """
    t = "person-roles"
    k = PK[t]
    m = load_map(t)
    incoming_ids = {r[k] for r in records}
    offices_touched = {r["office_id"] for r in records}
    retired = 0
    for pr in m.values():
        if (pr.get("is_current") and pr.get("office_id") in offices_touched
                and pr[k] not in incoming_ids):
            pr["is_current"] = False
            if not pr.get("end_date"):
                pr["end_date"] = retire_date
            retired += 1
    for r in records:
        m[r[k]] = r
    save(t, list(m.values()))
    return len(records), retired


def remove_records_for_bodies(body_ids):
    """Remove a departed body and everything hanging off it, across every table.

    The live-state dataset holds only current bodies, so when a body drops out of its
    authoritative source (e.g. GOV.UK closes an organisation) it must not be left as a
    stale 'active' node with orphaned offices, holders or budget records pointing at a
    body that no longer exists. Drops records keyed by body_id (bodies, offices,
    person-roles, budgets, staffing) and any relationship touching a removed body.
    Returns {type: removed_count} for the tables actually changed.
    """
    ids = set(body_ids)
    if not ids:
        return {}
    removed = {}
    for t in ("bodies", "offices", "person-roles", "budgets", "staffing"):
        recs = load(t)
        kept = [r for r in recs if r.get("body_id") not in ids]
        if len(kept) != len(recs):
            save(t, kept)
            removed[t] = len(recs) - len(kept)
    rels = load("relationships")
    kept = [r for r in rels
            if r.get("from_body_id") not in ids and r.get("to_body_id") not in ids]
    if len(kept) != len(rels):
        save("relationships", kept)
        removed["relationships"] = len(rels) - len(kept)
    return removed
