#!/usr/bin/env python3
"""Validate WhoGoverns data records against their JSON Schemas.

Boring by design: one job, stdlib + jsonschema. Run from the repo root:
    python3 validate.py
Exit code 0 if no schema errors, 1 otherwise.
"""
import json
import os
import sys
import glob

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("jsonschema not installed. Run: pip install -r requirements.txt --break-system-packages")

REPO = os.path.dirname(os.path.abspath(__file__))

# data subfolder -> active schema file
FOLDER_SCHEMA = {
    "bodies": "body.schema.json",
    "sources": "source.schema.json",
    "offices": "office.schema.json",
    "person-roles": "person_role.schema.json",
    "relationships": "relationship.schema.json",
    "budgets": "budget.schema.json",
    "staffing": "staffing.schema.json",
}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    errors = 0
    warnings = 0
    records = 0

    body_ids = {load(p).get("body_id") for p in glob.glob(os.path.join(REPO, "data/bodies/*.json"))}
    source_ids = {load(p).get("source_id") for p in glob.glob(os.path.join(REPO, "data/sources/*.json"))}

    for folder, schema_file in FOLDER_SCHEMA.items():
        schema_path = os.path.join(REPO, "schemas", schema_file)
        if not os.path.exists(schema_path):
            continue
        validator = Draft202012Validator(load(schema_path))
        for path in sorted(glob.glob(os.path.join(REPO, "data", folder, "*.json"))):
            records += 1
            rec = load(path)
            rel = os.path.relpath(path, REPO)
            errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
            if errs:
                errors += len(errs)
                print("FAIL " + rel)
                for e in errs:
                    loc = "/".join(str(x) for x in e.path) or "(root)"
                    print("   - {}: {}".format(loc, e.message))
            else:
                print("ok   " + rel)
            # referential warnings
            if folder == "bodies":
                for field in ("sponsor_department_id", "parent_body_id"):
                    ref = rec.get(field)
                    if ref and ref not in body_ids:
                        warnings += 1
                        print("   ! warn {} -> {} not yet among body records (expected until more bodies land)".format(field, ref))
                for field in ("classification_source_ids", "founding_source_ids", "framework_document_source_ids", "annual_report_source_ids"):
                    for ref in rec.get(field, []):
                        if ref not in source_ids:
                            warnings += 1
                            print("   ! warn {} -> {} not among source records".format(field, ref))
            if folder == "relationships":
                for field in ("from_body_id", "to_body_id"):
                    ref = rec.get(field)
                    if ref and ref not in body_ids:
                        warnings += 1
                        print("   ! warn {} -> {} not among body records".format(field, ref))

    # provision_key duplicate check (canonical records only) — none in Spiral 1
    seen = {}
    for folder in ("powers", "duties", "vetoes"):
        for path in glob.glob(os.path.join(REPO, "data", folder, "*.json")):
            rec = load(path)
            pk = rec.get("provision_key")
            if pk and rec.get("derived_from_record_id") is None:
                if pk in seen:
                    errors += 1
                    print("FAIL duplicate canonical provision_key '{}' in {} and {}".format(pk, os.path.relpath(path, REPO), seen[pk]))
                else:
                    seen[pk] = os.path.relpath(path, REPO)

    print("\n---")
    print("records checked: {}  schema errors: {}  warnings: {}".format(records, errors, warnings))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
