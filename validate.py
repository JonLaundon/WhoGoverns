#!/usr/bin/env python3
"""Validate WhoGoverns data records against their JSON Schemas.

Boring by design: one job, stdlib + jsonschema. Reads the consolidated array files via
pipeline/store.py (each data type is one data/<type>.json list). Run from the repo root:
    py -3 validate.py
Exit code 0 if no schema errors, 1 otherwise.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline"))
import store  # noqa: E402

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("jsonschema not installed. Run: pip install -r requirements.txt --break-system-packages")

REPO = os.path.dirname(os.path.abspath(__file__))

# data type -> active schema file
TYPE_SCHEMA = {
    "bodies": "body.schema.json",
    "sources": "source.schema.json",
    "offices": "office.schema.json",
    "person-roles": "person_role.schema.json",
    "relationships": "relationship.schema.json",
    "budgets": "budget.schema.json",
    "staffing": "staffing.schema.json",
}


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    errors = warnings = records = 0
    body_ids = {r["body_id"] for r in store.load("bodies")}
    source_ids = {r["source_id"] for r in store.load("sources")}
    office_ids = {r["office_id"] for r in store.load("offices")}

    for t, schema_file in TYPE_SCHEMA.items():
        schema_path = os.path.join(REPO, "schemas", schema_file)
        if not os.path.exists(schema_path):
            continue
        validator = Draft202012Validator(load_json(schema_path))
        recs = store.load(t)
        bad = 0
        for rec in recs:
            records += 1
            for e in sorted(validator.iter_errors(rec), key=lambda e: list(e.path)):
                errors += 1
                bad += 1
                loc = "/".join(str(x) for x in e.path) or "(root)"
                print(f"FAIL {t} [{loc}]: {e.message}")
            # referential warnings (per record)
            if t == "bodies":
                for field in ("sponsor_department_id", "parent_body_id"):
                    ref = rec.get(field)
                    if ref and ref not in body_ids:
                        warnings += 1
                        print(f"   ! warn {t}.{field} -> {ref} not among bodies")
                for field in ("classification_source_ids", "founding_source_ids",
                              "framework_document_source_ids", "annual_report_source_ids", "function_source_ids"):
                    for ref in rec.get(field, []):
                        if ref not in source_ids:
                            warnings += 1
                            print(f"   ! warn {t}.{field} -> {ref} not among sources")
            elif t == "relationships":
                for field in ("from_body_id", "to_body_id"):
                    ref = rec.get(field)
                    if ref and ref not in body_ids:
                        warnings += 1
                        print(f"   ! warn relationships.{field} -> {ref} not among bodies")
            elif t in ("offices", "person-roles", "budgets", "staffing"):
                ref = rec.get("body_id")
                if ref and ref not in body_ids:
                    warnings += 1
                    print(f"   ! warn {t}.body_id -> {ref} not among bodies")
            if t == "person-roles":
                ref = rec.get("office_id")
                if ref and ref not in office_ids:
                    warnings += 1
                    print(f"   ! warn person-roles.office_id -> {ref} not among offices")
        print("ok   {}.json  ({} records{})".format(t, len(recs), ", " + str(bad) + " FAIL" if bad else ""))

    # provision_key duplicate check on canonical Power/Duty/Veto records (none in Spiral 1)
    seen = {}
    for t in ("powers", "duties", "vetoes"):
        for rec in store.load(t) if t in store.PK else []:
            pk = rec.get("provision_key")
            if pk and rec.get("derived_from_record_id") is None:
                if pk in seen:
                    errors += 1
                    print(f"FAIL duplicate canonical provision_key '{pk}'")
                else:
                    seen[pk] = True

    print("\n---")
    print(f"records checked: {records}  schema errors: {errors}  warnings: {warnings}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
