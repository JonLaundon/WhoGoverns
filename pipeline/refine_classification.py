#!/usr/bin/env python3
"""Refine body_type using the Cabinet Office Public Bodies Directory (rank-2 source).

The GOV.UK Organisations API `format` (rank 1 for identity) is coarse — it dumps many
NDPBs and advisory committees into "Other". The Cabinet Office Public Bodies Directory
is the designated rank-2 authority for ALB classification (Annex A3.2), so where it
speaks we adopt it. Two high-precision, sourced steps:

  A. Exact-name match to the CO directory -> adopt the CO classification, add the CO
     SourceRecord, clear the review flag. (Fuzzy matching is deliberately avoided — it
     mis-mapped Arts Council of Wales -> England, Royal Mint -> Royal Mint Advisory
     Committee, etc.)
  B. For bodies STILL flagged, if the official name contains an advisory phrase
     ("advisory committee/group/panel/council/board"), classify advisory_ndpb — an
     advisory body by its own name (sourced to the API name, not a guess). The phrase
     requirement avoids false hits like "Advisory, Conciliation and Arbitration Service".

Reads the cached CO xlsx; writes updated Body records and the CO SourceRecord.
    py -3 pipeline/refine_classification.py [--dry-run]

Needs openpyxl (see requirements.txt) to read the source spreadsheet.
"""
import argparse
import datetime
import os
import re

import openpyxl

import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
XLSX = os.path.join(DATA, "sources", "raw", "cabinet-office-public-bodies",
                    "public-bodies-directory-2023-24.xlsx")
CO_SOURCE_ID = "source-official-dataset-cabinet-office-public-bodies"
API_SOURCE_ID = "source-official-dataset-govuk-organisations-api"
TODAY = datetime.date.today().isoformat()

CO_MAP = {
    "Executive NDPB": "executive_ndpb", "Advisory NDPB": "advisory_ndpb",
    "Executive Agency": "executive_agency", "Non-Ministerial Department": "non_ministerial_department",
    "Tribunal NDPB": "tribunal", "Crown NDPB": "executive_ndpb",
}
ADVISORY_PHRASES = ["advisory committee", "advisory group", "advisory panel",
                    "advisory council", "advisory board", "advisory sub-committee"]


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()


def load_co_index():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["Data"]; ws.reset_dimensions()
    rows = [r for r in ws.iter_rows(values_only=True)]
    hdr = 6
    H = {str(c): j for j, c in enumerate(rows[hdr]) if c}
    index = {}
    for r in rows[hdr + 1:]:
        nm = r[H["overall_alb_name"]]
        if nm:
            index[norm(nm)] = CO_MAP.get(r[H["overall_classification"]], "other_body")
    return index


def co_source_record():
    return {
        "source_id": CO_SOURCE_ID,
        "title": "Cabinet Office Public Bodies Directory 2023/24",
        "source_type": "official_dataset",
        "publisher": "Cabinet Office",
        "url": "https://www.gov.uk/government/publications/public-bodies-2024",
        "accessed_date": TODAY,
        "publication_date": None,
        "version_date": "2025-05-29",
        "legal_status": "current",
        "licence": "Open Government Licence v3.0",
        "notes": "Directory of arm's-length bodies with authoritative classification "
                 "(Executive/Advisory/Tribunal/Crown NDPB, Executive Agency, "
                 "Non-Ministerial Department). Rank-2 classification source (Annex A3.2). "
                 "Raw xlsx cached under data/sources/raw/cabinet-office-public-bodies/.",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    co = load_co_index()
    bodies = store.load_map("bodies")

    co_changes, adv_changes, co_confirmed, cleared = [], [], 0, 0
    for b in bodies.values():
        changed = False
        keys = [norm(b["name"])] + [norm(a) for a in b.get("other_names", [])]
        co_hit = next((co[k] for k in keys if k in co), None)

        if co_hit:
            if co_hit != b["body_type"]:
                co_changes.append((b["name"], b["body_type"], co_hit))
                b["body_type"] = co_hit
                changed = True
            else:
                co_confirmed += 1
            if CO_SOURCE_ID not in b.get("classification_source_ids", []):
                b.setdefault("classification_source_ids", []).append(CO_SOURCE_ID)
                changed = True
            if b.get("needs_classification_review"):
                b["needs_classification_review"] = False
                cleared += 1
                changed = True
        elif b.get("needs_classification_review"):
            name_l = b["name"].lower()
            if any(p in name_l for p in ADVISORY_PHRASES) and b["body_type"] != "advisory_ndpb":
                adv_changes.append((b["name"], b["body_type"]))
                b["body_type"] = "advisory_ndpb"
                b["needs_classification_review"] = False
                b["notes"] = ((b.get("notes") or "") +
                              " Classified advisory_ndpb from official name (CO directory: no exact match).").strip()
                cleared += 1
                changed = True

    if not args.dry_run:
        store.save("bodies", list(bodies.values()))
        store.upsert("sources", [co_source_record()])

    still_flagged = sum(1 for b in bodies.values() if b.get("needs_classification_review")) if not args.dry_run \
        else "(dry-run)"

    print("--- refine_classification summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print("CO exact matches confirmed (no change): {}".format(co_confirmed))
    print("CO reclassifications:                   {}".format(len(co_changes)))
    for name, old, new in co_changes:
        print("   {:42} {} -> {}".format(name[:42], old, new))
    print("advisory name-phrase reclassifications: {}".format(len(adv_changes)))
    for name, old in adv_changes[:30]:
        print("   {:50} {} -> advisory_ndpb".format(name[:50], old))
    if len(adv_changes) > 30:
        print("   ... and {} more".format(len(adv_changes) - 30))
    print("review flags cleared:                   {}".format(cleared))
    print("bodies still flagged:                   {}".format(still_flagged))


if __name__ == "__main__":
    main()
