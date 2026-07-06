#!/usr/bin/env python3
"""Tag bodies on the FUNCTIONAL axis (functions[]), orthogonal to body_type.

Spiral 1.5 bolt-on. body_type is the constitutional/structural axis; a grouping like
"regulator" cross-cuts it (regulators are non_ministerial_department, executive_ndpb,
public_corporation or other_body). Rather than reopen decision #12 (which correctly
dropped `regulator` as a body_type), this adds a second, multi-valued axis and populates
one function from an official list:

  regulation  <- the Department for Business and Trade "List of UK regulators" (an
                 official published list; OGL v3.0). A body is tagged 'regulation' iff
                 it appears on that list, matched by EXACT normalised name / alias
                 (plus any acronym in a parenthetical, e.g. "... (Ofgem)"). No fuzzy
                 matching (house rule — see refine_classification.py).

Every populated tag records the anchoring source in function_source_ids. Bodies on the
list that are NOT in the graph are printed as off-register candidates (they are the
professional/statutory self-regulators and devolved regulators — Part B / later passes),
never silently dropped.

Reads the cached DBT ODS with the standard library (no new dependency); writes updated
Body records (functions/function_source_ids only) on change.
    py -3 pipeline/refine_functions.py [--dry-run]
"""
import argparse
import glob
import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
ODS = os.path.join(DATA, "sources", "raw", "list-of-uk-regulators",
                   "list-of-uk-regulatory-organisations.ods")
SOURCE_ID = "source-official-dataset-list-of-uk-regulators"
BODIES = os.path.join(DATA, "bodies")

T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
P = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p"
STOP = {"the", "of", "for", "in", "uk", "gb", "great", "britain"}
# phrases in a parenthetical that are commentary, not an alias
COMMENT = re.compile(r"(formerly|former|to be|aml|following|will become|part of)", re.I)


def norm(s):
    s = s.lower().replace("&", "and").replace("’", "'")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(w for w in s.split() if w not in STOP)


def source_keys(raw):
    """Match keys for a source-list entry: the base name plus any alias in parens."""
    keys = {norm(re.sub(r"\(.*?\)", "", raw))}
    for frag in re.findall(r"\((.*?)\)", raw):
        frag = COMMENT.split(frag)[0].strip(" ,")
        if frag and len(frag) <= 60:
            keys.add(norm(frag))
    return {k for k in keys if k}


def cell_text(c):
    return "".join(t.text or "" for t in c.iter(P))


def read_regulator_names():
    xml = zipfile.ZipFile(ODS).read("content.xml").decode("utf-8")
    root = ET.fromstring(xml)
    names = []
    for tbl in root.iter(T + "table"):
        for r in tbl.findall(".//" + T + "table-row"):
            cells = r.findall(T + "table-cell")
            if cells:
                first = cell_text(cells[0]).strip()
                if first and first != "Regulatory Body":
                    names.append(first)
    return names


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # body lookup: normalised name / alias -> body_id  (first wins, deterministic)
    paths = sorted(glob.glob(os.path.join(BODIES, "*.json")))
    lut, bodies = {}, {}
    for p in paths:
        d = load(p)
        bodies[d["body_id"]] = (p, d)
        for n in [d["name"]] + d.get("other_names", []):
            lut.setdefault(norm(n), d["body_id"])

    names = read_regulator_names()
    matched, unmatched = {}, []
    for raw in names:
        hit = next((lut[k] for k in source_keys(raw) if k in lut), None)
        if hit:
            matched[hit] = raw
        else:
            unmatched.append(re.sub(r"\(.*?\)", "", raw).strip())

    changed = []
    for bid in matched:
        _, d = bodies[bid]
        funcs = set(d.get("functions", []))
        srcs = set(d.get("function_source_ids", []))
        if "regulation" in funcs and SOURCE_ID in srcs:
            continue
        funcs.add("regulation")
        srcs.add(SOURCE_ID)
        d["functions"] = sorted(funcs)
        d["function_source_ids"] = sorted(srcs)
        changed.append(bid)

    if not args.dry_run:
        for bid in changed:
            p, d = bodies[bid]
            write_json(p, d)

    print("--- refine_functions summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print("regulator-list entries read:      {}".format(len(names)))
    print("distinct bodies matched:          {}".format(len(matched)))
    print("bodies newly tagged 'regulation': {}".format(len(changed)))
    print("off-register (not in graph):      {}".format(len(unmatched)))
    print("\nOff-register regulators (Part B / devolved candidates), first 60:")
    for n in sorted(set(unmatched))[:60]:
        print("   - {}".format(n))


if __name__ == "__main__":
    main()
