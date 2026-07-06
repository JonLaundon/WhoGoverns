#!/usr/bin/env python3
"""Ingest the senior officials tranche: non-ministerial department heads + departmental
permanent secretaries, as Office + PersonRole records.

Scope (sponsor, 2026-07-06 — reclassified from Spiral 5 to now, because these office-holders
carry statutory powers needed by the Spiral 2 powers register):
  - each NON-MINISTERIAL DEPARTMENT -> its head / accounting officer  (office_type independent_official)
  - each MINISTERIAL DEPARTMENT     -> its permanent secretary         (office_type civil_servant)

No network — reads two caches already on disk:
  - the Cabinet Office Public Bodies Directory xlsx (accounting-officer name per ALB)
  - the GOV.UK content-API responses cached by ingest_ministers.py (ordered_board_members)

    py -3 pipeline/ingest_officials.py [--dry-run]

Boring by design: stdlib + openpyxl (for the xlsx). Idempotent.
"""
import argparse
import glob
import json
import os
import re

import openpyxl

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
XLSX = os.path.join(DATA, "sources", "raw", "cabinet-office-public-bodies", "public-bodies-directory-2023-24.xlsx")
CONTENT_CACHE = os.path.join(DATA, "sources", "raw", "govuk-content-ministers")
OFFICES_DIR = os.path.join(DATA, "offices")
PERSONROLES_DIR = os.path.join(DATA, "person-roles")
CO_SOURCE_ID = "source-official-dataset-cabinet-office-public-bodies"
CONTENT_SOURCE_ID = "source-official-dataset-govuk-content-api"


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()


def person_slug(name):
    honor = {"the", "rt", "hon", "sir", "dame", "dr", "lord", "baroness", "mp", "kc", "qc",
             "cb", "cbe", "obe", "mbe", "kcb", "dbe", "qpm", "professor", "prof"}
    toks = [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t and t not in honor]
    return "-".join(toks) or norm(name).replace(" ", "-")


def clean_name(raw):
    """CO accounting-officer values are free text; take the leading name and flag if it
    still looks like a sentence rather than a name."""
    s = str(raw).strip()
    for delim in [" (", ";", " is ", " until", " - ", ","]:
        i = s.find(delim)
        if i > 0:
            s = s[:i]
    s = s.strip()
    messy = bool(re.search(r"\b(is|and|the|of)\b", s.lower())) or len(s.split()) > 4 or not s
    return s, messy


def perm_sec_from_content(data):
    """Find the department's permanent secretary among ordered_board_members: prefer a role
    titled exactly 'Permanent Secretary', excluding Acting/Second/Deputy."""
    best = None
    for m in data.get("links", {}).get("ordered_board_members", []):
        for ra in m.get("links", {}).get("role_appointments", []):
            for role in ra.get("links", {}).get("role", []):
                t = (role.get("title") or "").strip()
                if t == "Permanent Secretary":
                    return m.get("title")
                if "Permanent Secretary" in t and not any(w in t for w in ("Acting", "Second", "Deputy")) and best is None:
                    best = m.get("title")
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    bodies = [load(p) for p in glob.glob(os.path.join(DATA, "bodies", "*.json"))]
    nmd = {norm(b["name"]): b for b in bodies if b["body_type"] == "non_ministerial_department"}
    md = {b["govuk_organisation_slug"]: b for b in bodies if b["body_type"] == "ministerial_department"}

    # CO directory: accounting officer per non-ministerial department
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Data"]; ws.reset_dimensions(); rows = [r for r in ws.iter_rows(values_only=True)]; hdr = 6
    H = {str(c): j for j, c in enumerate(rows[hdr]) if c}
    co_ao = {}
    for r in rows[hdr + 1:]:
        if r[H["overall_alb_name"]] and r[H["overall_classification"]] == "Non-Ministerial Department":
            co_ao[norm(r[H["overall_alb_name"]])] = r[H["overall_accounts_officer" if "overall_accounts_officer" in H else "accountability_accounts_officer"]]

    offices, person_roles, flagged, missing = [], [], [], []

    # 1) non-ministerial department heads -> independent_official
    for nm, b in nmd.items():
        raw = co_ao.get(nm)
        if not raw:
            missing.append(("head", b["name"])); continue
        name, messy = clean_name(raw)
        oid = "office-head-" + b["govuk_organisation_slug"]
        offices.append({
            "office_id": oid, "title": "Head of " + b["name"], "body_id": b["body_id"],
            "office_type": "independent_official", "source_ids": [CO_SOURCE_ID],
            "notes": "Accounting officer / head per CO Public Bodies Directory." + (" Name needs review." if messy else ""),
            "record_status": "extracted", "last_reviewed": None,
        })
        person_roles.append({
            "person_role_id": "personrole-head-" + b["govuk_organisation_slug"] + "-" + person_slug(name),
            "person_name": name, "office_id": oid, "body_id": b["body_id"],
            "start_date": None, "end_date": None, "is_current": True, "source_ids": [CO_SOURCE_ID],
            "notes": None, "record_status": "extracted", "last_reviewed": None,
        })
        if messy:
            flagged.append((b["name"], raw))

    # 2) ministerial department permanent secretaries -> civil_servant
    for slug, b in md.items():
        cache = os.path.join(CONTENT_CACHE, slug + ".json")
        if not os.path.exists(cache):
            missing.append(("permsec", b["name"])); continue
        ps = perm_sec_from_content(load(cache))
        if not ps:
            missing.append(("permsec", b["name"])); continue
        oid = "office-permanent-secretary-" + slug
        offices.append({
            "office_id": oid, "title": "Permanent Secretary, " + b["name"], "body_id": b["body_id"],
            "office_type": "civil_servant", "source_ids": [CONTENT_SOURCE_ID],
            "notes": "Permanent secretary per GOV.UK content API board members.",
            "record_status": "extracted", "last_reviewed": None,
        })
        person_roles.append({
            "person_role_id": "personrole-permsec-" + slug + "-" + person_slug(ps),
            "person_name": ps, "office_id": oid, "body_id": b["body_id"],
            "start_date": None, "end_date": None, "is_current": True, "source_ids": [CONTENT_SOURCE_ID],
            "notes": None, "record_status": "extracted", "last_reviewed": None,
        })

    if not args.dry_run:
        for o in offices:
            write_json(os.path.join(OFFICES_DIR, o["office_id"] + ".json"), o)
        for pr in person_roles:
            write_json(os.path.join(PERSONROLES_DIR, pr["person_role_id"] + ".json"), pr)

    print("--- ingest_officials summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print("independent officials (non-min dept heads): {}".format(sum(1 for o in offices if o["office_type"] == "independent_official")))
    print("civil servants (dept permanent secretaries): {}".format(sum(1 for o in offices if o["office_type"] == "civil_servant")))
    print("total Office + PersonRole records:          {} + {}".format(len(offices), len(person_roles)))
    if flagged:
        print("\nnames flagged for review (messy CO free-text): {}".format(len(flagged)))
        for name, raw in flagged:
            print("   {:38} <- {}".format(name[:38], str(raw)[:60]))
    if missing:
        print("\nno official found (skipped): {}".format(len(missing)))
        for kind, name in missing:
            print("   [{}] {}".format(kind, name))


if __name__ == "__main__":
    main()
