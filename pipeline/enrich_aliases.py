#!/usr/bin/env python3
"""Carry old names of renamed/merged bodies onto their live successors as aliases.

One job: for each CLOSED org in the cache that was renamed/merged/replaced into a
single successor we hold, add its old name (and abbreviation) to that successor's
`other_names`, so a search for the old name finds the current body. Example:
"Atomic Weapons Establishment" (closed, changed_name) -> alias on
"AWE Nuclear Security Technologies" (the live successor).

Deliberately conservative — only closures that are a 1:1 rename of the SAME body,
so `other_names` stays "former names of this body":
  include: changed_name, replaced, WITH exactly one held live/exempt successor
  exclude: merged (a distinct body absorbed into another, e.g. National School of
           Government -> Cabinet Office — that is succession history, not an alias),
           devolved (transfer to another tier, e.g. -> Northern Ireland Executive),
           split (one body -> many; not an alias of any single successor),
           no_longer_exists / left_gov (defunct)

It never creates or deletes bodies and never touches classification — only appends
to `other_names` (de-duplicated, idempotent).

    py -3 pipeline/enrich_aliases.py            # apply
    py -3 pipeline/enrich_aliases.py --dry-run  # report only

Boring by design: stdlib only, deterministic, no network.
"""
import argparse
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (this file lives in pipeline/)
RAW_GLOB = os.path.join(REPO, "data", "sources", "raw", "govuk-organisations-api", "page-*.json")
BODIES_DIR = os.path.join(REPO, "data", "bodies")

ALIAS_CLOSED_STATUS = {"changed_name", "replaced"}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = parser.parse_args()

    body_paths = {os.path.basename(p)[:-5]: p for p in glob.glob(os.path.join(BODIES_DIR, "*.json"))}
    if not body_paths:
        sys.exit("No Body records found. Run transform_bodies.py first.")
    bodies = {bid: load(p) for bid, p in body_paths.items()}

    pages = sorted(glob.glob(RAW_GLOB))
    if not pages:
        sys.exit("No raw cache found. Run ingest_organisations.py first.")
    raw = []
    for page in pages:
        raw.extend(load(page).get("results", []))

    # successor body_id -> ordered list of alias strings to add
    proposed = {}
    skipped_multi, skipped_no_held_successor = [], []

    for r in raw:
        d = r.get("details", {})
        if d.get("govuk_status") != "closed":
            continue
        if d.get("govuk_closed_status") not in ALIAS_CLOSED_STATUS:
            continue
        sups = r.get("superseding_organisations", [])
        if len(sups) != 1:
            if sups:
                skipped_multi.append(r.get("title"))
            continue
        succ_id = "uk-state-body-" + sups[0]["id"].rstrip("/").split("/")[-1]
        if succ_id not in bodies:
            skipped_no_held_successor.append(r.get("title"))
            continue
        aliases = [r.get("title")]
        if d.get("abbreviation"):
            aliases.append(d["abbreviation"])
        proposed.setdefault(succ_id, [])
        for a in aliases:
            if a and a not in proposed[succ_id]:
                proposed[succ_id].append(a)

    updated, alias_added = [], 0
    for succ_id, aliases in proposed.items():
        rec = bodies[succ_id]
        existing = rec.get("other_names", [])
        current_name = rec.get("name")
        new = [a for a in aliases if a != current_name and a not in existing]
        if not new:
            continue
        rec["other_names"] = existing + new
        alias_added += len(new)
        updated.append((succ_id, new))
        if not args.dry_run:
            write_json(body_paths[succ_id], rec)

    print("--- enrich_aliases summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print("successors gaining aliases:  {}".format(len(updated)))
    print("alias strings added:         {}".format(alias_added))
    print("skipped (split -> many successors):     {}".format(len(skipped_multi)))
    print("skipped (successor not held/live):      {}".format(len(skipped_no_held_successor)))
    print("\nexamples:")
    for succ_id, new in sorted(updated)[:20]:
        print("  {} += {}".format(succ_id[len("uk-state-body-"):], new))


if __name__ == "__main__":
    main()
