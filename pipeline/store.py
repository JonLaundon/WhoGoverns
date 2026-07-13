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
