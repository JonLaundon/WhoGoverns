#!/usr/bin/env python3
"""Refine sponsor links using the Cabinet Office Public Bodies Directory (R1b).

The task-3 sponsor graph comes from the GOV.UK parent/child links. The CO directory
(rank-2 for ALB *sponsorship*, A3.2) independently states each ALB's parent department.
This pass, conservatively:
  - FILLS sponsor_department_id where we have none (a body that came through as a root),
    from the CO parent department, and adds the matching Relationship record;
  - CONFIRMS where CO agrees with the GOV.UK-derived sponsor (adds CO to the edge source);
  - LOGS discrepancies where CO and GOV.UK disagree — WITHOUT overriding, because the live
    GOV.UK data is more current than the 2023/24 directory. Discrepancies go to issues.

Reads the cached CO xlsx; writes Body + Relationship records. Needs openpyxl.
    py -3 pipeline/refine_sponsors.py [--dry-run]
"""
import argparse
import os
import re

import openpyxl

import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
XLSX = os.path.join(DATA, "sources", "raw", "cabinet-office-public-bodies", "public-bodies-directory-2023-24.xlsx")
CO_SOURCE_ID = "source-official-dataset-cabinet-office-public-bodies"
SOURCE_URL = "https://www.gov.uk/government/publications/public-bodies-2024"
DEPT_STOP = {"and", "the", "of", "for"}


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()


def normdept(s):
    return " ".join(t for t in norm(s).split() if t not in DEPT_STOP)


def rel_record(dept_id, body_id):
    fs, ts = dept_id[len("uk-state-body-"):], body_id[len("uk-state-body-"):]
    return {
        "relationship_id": f"rel-{fs}-sponsors-{ts}",
        "from_body_id": dept_id, "to_body_id": body_id, "relationship_type": "sponsors",
        "source_id": CO_SOURCE_ID, "citation": {"provision": None, "url": SOURCE_URL},
        "start_date": None, "end_date": None, "legal_status": "current", "record_status": "extracted",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    # CO: alb name -> parent department name
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Data"]; ws.reset_dimensions(); rows = list(ws.iter_rows(values_only=True)); hdr = 6
    H = {str(c): j for j, c in enumerate(rows[hdr]) if c}
    co_sponsor = {}
    for r in rows[hdr + 1:]:
        nm = r[H["overall_alb_name"]]
        if nm:
            co_sponsor[norm(nm)] = r[H["overall_parent_department"]]

    bodies = store.load_map("bodies")
    dept_index = {normdept(b["name"]): bid for bid, b in bodies.items()
                  if b["body_type"] in ("ministerial_department", "non_ministerial_department")}

    rels = store.load_map("relationships")
    filled, confirmed, discrepancies, unresolved_dept = [], 0, [], set()

    for bid, b in bodies.items():
        # Departments are top-level; they don't get a sponsor. (CO lists them as their
        # own parent, which would otherwise create a self-referential sponsor edge.)
        if b["body_type"] in ("ministerial_department", "non_ministerial_department"):
            continue
        keys = [norm(b["name"])] + [norm(a) for a in b.get("other_names", [])]
        co_dept_name = next((co_sponsor[k] for k in keys if k in co_sponsor), None)
        if not co_dept_name:
            continue
        co_dept_id = dept_index.get(normdept(co_dept_name))
        if not co_dept_id or co_dept_id == bid:
            if not co_dept_id:
                unresolved_dept.add(str(co_dept_name))
            continue

        current = b.get("sponsor_department_id")
        if current == co_dept_id:
            confirmed += 1
        elif current is None and b.get("parent_body_id") is None:
            b["sponsor_department_id"] = co_dept_id
            filled.append((b["name"], co_dept_id))
            rel = rel_record(co_dept_id, bid)
            if rel["relationship_id"] not in rels:
                rels[rel["relationship_id"]] = rel
        elif current and current != co_dept_id:
            discrepancies.append((b["name"], current, co_dept_id))

    if filled and not args.dry_run:
        store.save("bodies", list(bodies.values()))
        store.save("relationships", list(rels.values()))

    print("--- refine_sponsors summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print(f"sponsors FILLED (were root):     {len(filled)}")
    for name, dept in filled[:30]:
        print("   {:44} -> {}".format(name[:44], dept[len('uk-state-body-'):]))
    print(f"sponsors CONFIRMED (CO == GOV.UK): {confirmed}")
    print(f"DISCREPANCIES (CO != GOV.UK; not overridden, logged): {len(discrepancies)}")
    for name, ours, co in discrepancies[:30]:
        print("   {:40} GOV.UK={} CO={}".format(name[:40], ours[len('uk-state-body-'):], co[len('uk-state-body-'):]))
    if unresolved_dept:
        print(f"CO parent departments we could not resolve to a body: {sorted(unresolved_dept)}")


if __name__ == "__main__":
    main()
