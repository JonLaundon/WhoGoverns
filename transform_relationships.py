#!/usr/bin/env python3
"""Build the sponsor/parent graph from the cached GOV.UK Organisations pages.

One job: turn the API's parent_organisations / child_organisations links into
Relationship records (the canonical graph edges), and fill each Body record's
sponsor_department_id / parent_body_id convenience fields to match.

Edge direction follows the schema and the seeds: the parent/sponsor is
`from_body_id`, the sponsored body is `to_body_id`, relationship_type `sponsors`
(e.g. DESNZ sponsors Ofgem). Every org-hierarchy edge from this API is a
"sponsors" edge — GOV.UK's parent/sponsor sense; finer legal relationship types
(regulates, consents_to, ...) come with the powers layer in Spiral 2.

Both endpoints of an edge must be Body records we hold; edges to closed/out-of-scope
orgs are skipped and counted (see the report / issues log). Parent and child lists
are unioned and de-duplicated, so an edge asserted from only one side is still caught.

    py -3 transform_relationships.py            # write records + fill body fields
    py -3 transform_relationships.py --dry-run  # report only, write nothing

Boring by design: stdlib only, deterministic, no network. Idempotent — body fields
are filled only when null; an existing value is verified and a mismatch reported,
never overwritten (protects the curated seeds).
"""
import argparse
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
RAW_GLOB = os.path.join(REPO, "data", "sources", "raw", "govuk-organisations-api", "page-*.json")
BODIES_DIR = os.path.join(REPO, "data", "bodies")
RELS_DIR = os.path.join(REPO, "data", "relationships")
SOURCE_ID = "source-official-dataset-govuk-organisations-api"
SOURCE_URL = "https://www.gov.uk/api/organisations"

# A department parent is recorded as the child's sponsor department; any other
# parent (agency, NDPB, sub-org) is recorded as its parent_body.
DEPARTMENT_TYPES = {"ministerial_department", "non_ministerial_department"}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def slug_of(ref):
    """parent/child entries carry an API id URL; the slug is its last segment."""
    return ref.get("id", "").rstrip("/").split("/")[-1]


def relationship_record(from_id, to_id):
    from_slug = from_id[len("uk-state-body-"):]
    to_slug = to_id[len("uk-state-body-"):]
    return {
        "relationship_id": "rel-{}-sponsors-{}".format(from_slug, to_slug),
        "from_body_id": from_id,
        "to_body_id": to_id,
        "relationship_type": "sponsors",
        "source_id": SOURCE_ID,
        "citation": {"provision": None, "url": SOURCE_URL},
        "start_date": None,
        "end_date": None,
        "legal_status": "current",
        "record_status": "extracted",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = parser.parse_args()

    # Bodies we hold: id -> record (for body_type lookup and field fill).
    body_paths = {os.path.basename(p)[:-5]: p for p in glob.glob(os.path.join(BODIES_DIR, "*.json"))}
    if not body_paths:
        sys.exit("No Body records found. Run transform_bodies.py first.")
    bodies = {bid: load(p) for bid, p in body_paths.items()}
    valid = set(bodies)

    # Raw records keyed by our body_id, for their parent/child lists.
    pages = sorted(glob.glob(RAW_GLOB))
    if not pages:
        sys.exit("No raw cache found. Run ingest_organisations.py first.")
    raw = {}
    for page in pages:
        for r in load(page).get("results", []):
            raw["uk-state-body-" + r["details"]["slug"]] = r

    edges = set()               # (from_id/parent, to_id/child)
    skipped_endpoint = []       # edges dropped because one end is not a held Body

    for bid in valid:
        r = raw.get(bid)
        if not r:
            continue
        # parent_organisations: parent -> this body
        for p in r.get("parent_organisations", []):
            pid = "uk-state-body-" + slug_of(p)
            if pid in valid:
                edges.add((pid, bid))
            else:
                skipped_endpoint.append((pid, bid))
        # child_organisations: this body -> child
        for c in r.get("child_organisations", []):
            cid = "uk-state-body-" + slug_of(c)
            if cid in valid:
                edges.add((bid, cid))
            else:
                skipped_endpoint.append((bid, cid))

    # Parents per child, to fill the body convenience fields.
    parents_of = {}
    for frm, to in edges:
        parents_of.setdefault(to, []).append(frm)

    updated_bodies, field_mismatch, multi_sponsor, multi_parent = [], [], [], []
    for child_id, parent_ids in parents_of.items():
        dept_parents = sorted(p for p in parent_ids if bodies[p]["body_type"] in DEPARTMENT_TYPES)
        other_parents = sorted(p for p in parent_ids if bodies[p]["body_type"] not in DEPARTMENT_TYPES)
        if len(dept_parents) > 1:
            multi_sponsor.append((child_id, dept_parents))
        if len(other_parents) > 1:
            multi_parent.append((child_id, other_parents))
        rec = bodies[child_id]
        changed = False
        for field, chosen in (("sponsor_department_id", dept_parents[0] if dept_parents else None),
                              ("parent_body_id", other_parents[0] if other_parents else None)):
            if chosen is None:
                continue
            existing = rec.get(field)
            if existing is None:
                rec[field] = chosen
                changed = True
            elif existing != chosen:
                field_mismatch.append((child_id, field, existing, chosen))
        if changed:
            updated_bodies.append(child_id)

    # ---- write ----
    if not args.dry_run:
        os.makedirs(RELS_DIR, exist_ok=True)
        for frm, to in sorted(edges):
            rel = relationship_record(frm, to)
            write_json(os.path.join(RELS_DIR, rel["relationship_id"] + ".json"), rel)
        for bid in updated_bodies:
            write_json(body_paths[bid], bodies[bid])

    # ---- report ----
    roots = sorted(b for b in valid if b not in parents_of)
    print("--- transform_relationships summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print("bodies held:                 {}".format(len(valid)))
    print("edges (sponsors):            {}".format(len(edges)))
    print("relationship records:        {}".format(len(edges)))
    print("body fields filled:          {}".format(len(updated_bodies)))
    print("root bodies (no parent):     {}".format(len(roots)))
    print("edges skipped (endpoint not held): {}".format(len(skipped_endpoint)))
    for frm, to in sorted(set(skipped_endpoint))[:12]:
        print("    - {} -> {}".format(frm, to))
    if len(set(skipped_endpoint)) > 12:
        print("    ... and {} more".format(len(set(skipped_endpoint)) - 12))
    if multi_sponsor:
        print("\nbodies with >1 department parent (first used as sponsor; all edges kept): {}".format(len(multi_sponsor)))
        for cid, ps in multi_sponsor[:10]:
            print("    - {}: {}".format(cid, ", ".join(ps)))
    if multi_parent:
        print("\nbodies with >1 non-department parent (first used as parent_body): {}".format(len(multi_parent)))
        for cid, ps in multi_parent[:10]:
            print("    - {}: {}".format(cid, ", ".join(ps)))
    if field_mismatch:
        print("\n!! BODY FIELD MISMATCH (computed != existing; NOT overwritten) — investigate:")
        for cid, field, old, new in field_mismatch:
            print("   {} {} existing={} computed={}".format(cid, field, old, new))
        sys.exit(1)


if __name__ == "__main__":
    main()
