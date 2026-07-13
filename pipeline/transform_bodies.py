#!/usr/bin/env python3
"""Transform the cached GOV.UK Organisations pages into Body records.

One job: read the raw pages ingest_organisations.py cached, select the live
in-scope bodies, classify each via the format->body_type crosswalk, and write
one schema-valid Body record per body to data/bodies/. No network.

Scope (Spiral 1 workpack v0.2, task 2): bodies + classification + external IDs
only. It does NOT populate relationships (sponsor/parent -> task 3), ministers
(task 4), budgets/staffing (bolt-on) or powers/duties/vetoes (Spiral 2). So
sponsor_department_id and parent_body_id are left null here.

Safety: create-if-absent. Existing records (the three curated seeds) are never
overwritten — they are reconciled (body_type compared) and reported. To fully
regenerate the machine-written records, delete data/bodies/*.json except the
seeds and re-run.

    py -3 pipeline/transform_bodies.py            # write records
    py -3 pipeline/transform_bodies.py --dry-run  # report only, write nothing

Boring by design: stdlib only, deterministic output (sorted keys), runnable
standalone from a clean checkout after the ingest has run.
"""
import argparse
import glob
import json
import os
import sys

import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (this file lives in pipeline/)
RAW_GLOB = os.path.join(REPO, "data", "sources", "raw", "govuk-organisations-api", "page-*.json")
FORMAT_MAP_PATH = os.path.join(REPO, "vocab", "govuk_format_to_body_type.json")
SOURCE_ID = "source-official-dataset-govuk-organisations-api"

# govuk_status -> Body status. live/exempt are established bodies (active);
# joining/transitioning are bodies in formation (forming) — included and rendered
# with a dashed outline on the map. Anything else (closed/superseded) is skipped.
STATUS_MAP = {"live": "active", "exempt": "active",
              "joining": "forming", "transitioning": "forming"}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_raw_records():
    """Flatten every org across the cached pages. Fail loudly if the cache is missing."""
    pages = sorted(glob.glob(RAW_GLOB))
    if not pages:
        sys.exit("No raw cache found. Run ingest_organisations.py first.")
    records = []
    for page in pages:
        records.extend(load(page).get("results", []))
    return records


def classify(fmt, fmt_map, flag_formats):
    """Return (body_type, needs_review). Unmapped -> other_body + review (AGENT rule 3)."""
    if fmt in fmt_map:
        return fmt_map[fmt], (fmt in flag_formats)
    return "other_body", True


def build_body(rec, body_type, needs_review, status, govuk_status):
    details = rec.get("details", {})
    slug = details.get("slug")
    # Forming bodies keep the raw govuk_status in notes so the distinction
    # (joining vs transitioning) survives; the map dashes any status=forming node.
    notes = None
    if status == "forming":
        notes = "In formation (govuk_status: {}); render dashed.".format(govuk_status)
    return {
        "body_id": "uk-state-body-" + slug,
        "name": rec.get("title"),
        "other_names": [],
        "status": status,
        "body_type": body_type,
        "jurisdiction": ["UK"],  # the API carries no jurisdiction; UK is the honest default (see review pack)
        "sponsor_department_id": None,  # task 3 (relationships)
        "parent_body_id": None,         # task 3 (relationships)
        "govuk_organisation_slug": slug,
        "external_ids": {
            "govuk_content_id": details.get("content_id"),
            "govuk_analytics_identifier": rec.get("analytics_identifier"),
            "company_number": None,
            "charity_number": None,
        },
        "founding_source_ids": [],
        "framework_document_source_ids": [],
        "annual_report_source_ids": [],
        "classification_source_ids": [SOURCE_ID],
        "notes": notes,
        "needs_classification_review": needs_review,
        "record_status": "extracted",
        "last_reviewed": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would happen; write nothing")
    args = parser.parse_args()

    fmt_doc = load(FORMAT_MAP_PATH)
    fmt_map = fmt_doc["map"]
    flag_formats = set(fmt_doc.get("flag_for_review", []))

    records = load_raw_records()
    existing = store.load_map("bodies")

    written, reconciled, forming, skipped_status = [], [], [], 0
    reconcile_mismatch, missing_slug, collisions = [], [], []
    seen_ids = {}
    type_counts = {}
    flagged_count = 0

    for rec in records:
        govuk_status = rec.get("details", {}).get("govuk_status")
        status = STATUS_MAP.get(govuk_status)
        if status is None:  # closed / superseded / anything else -> out of scope
            skipped_status += 1
            continue

        slug = rec.get("details", {}).get("slug")
        if not slug:
            missing_slug.append(rec.get("title"))
            continue

        body_type, needs_review = classify(rec.get("format"), fmt_map, flag_formats)
        body = build_body(rec, body_type, needs_review, status, govuk_status)
        body_id = body["body_id"]
        if status == "forming":
            forming.append((rec.get("title"), govuk_status))

        if body_id in seen_ids:
            collisions.append((body_id, seen_ids[body_id], rec.get("title")))
            continue
        seen_ids[body_id] = rec.get("title")
        type_counts[body_type] = type_counts.get(body_type, 0) + 1
        if needs_review:
            flagged_count += 1

        if body_id in existing:
            # Never overwrite a curated/seed record. Reconcile classification.
            existing_body = existing[body_id]
            if existing_body.get("body_type") != body_type:
                reconcile_mismatch.append(
                    (body_id, existing_body.get("body_type"), body_type))
            reconciled.append(body_id)
            continue

        existing[body_id] = body
        written.append(body_id)

    if not args.dry_run:
        store.save("bodies", list(existing.values()))

    # ---- report ----
    print("--- transform_bodies summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print("raw orgs read:            {}".format(len(records)))
    print("in-scope total:           {}".format(len(written) + len(reconciled)))
    print("  records written (new):  {}".format(len(written)))
    print("  reconciled (existing):  {}  {}".format(len(reconciled), reconciled or ""))
    print("  of which forming (in formation, status=forming, dashed): {}".format(len(forming)))
    for title, st in forming:
        print("    - [{}] {}".format(st, title))
    print("skipped (closed/superseded/other status):    {}".format(skipped_status))
    print("\nbody_type distribution (in-scope):")
    for bt in sorted(type_counts, key=lambda k: -type_counts[k]):
        print("  {:5} {}".format(type_counts[bt], bt))
    print("\nneeds_classification_review=true (coarse/unmapped formats): {}".format(flagged_count))

    if reconcile_mismatch:
        print("\n!! RECONCILE MISMATCH (existing body_type != computed) — investigate:")
        for bid, old, new in reconcile_mismatch:
            print("   {} existing={} computed={}".format(bid, old, new))
    if missing_slug:
        print("\n!! MISSING SLUG (skipped) — investigate:")
        for t in missing_slug:
            print("   {}".format(t))
    if collisions:
        print("\n!! BODY_ID COLLISION (skipped 2nd) — investigate:")
        for bid, first, second in collisions:
            print("   {}: {!r} vs {!r}".format(bid, first, second))

    # Non-zero exit on structural problems so a bad run is visible.
    if reconcile_mismatch or collisions:
        sys.exit(1)


if __name__ == "__main__":
    main()
