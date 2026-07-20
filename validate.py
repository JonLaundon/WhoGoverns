#!/usr/bin/env python3
"""Validate WhoGoverns data records against their JSON Schemas.

Boring by design: one job, stdlib + jsonschema. Reads the consolidated array files via
pipeline/store.py (each data type is one data/<type>.json list). Run from the repo root:
    py -3 validate.py
Exit 1 on any schema error OR integrity failure (a missing data file/schema, a reference
pointing nowhere, or a body sponsor field disagreeing with the canonical edges); else 0.
The gate fails closed: a vanished file is a failure, not a silent pass.
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
    # Powers layer (Annex A6, active from Spiral 2).
    "powers": "power.schema.json",
    "duties": "duty.schema.json",
    "vetoes": "veto.schema.json",
    "instruments": "instrument.schema.json",
    "provisions": "provision.schema.json",
    "definitions": "definition.schema.json",
}


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# Which vocab file backs which schema enum. Kept beside the check that uses it.
VOCAB_FIELDS = {
    "veto_type": ("veto.schema.json", "veto_type"),
    "veto_strength": ("veto.schema.json", "strength"),
    "power_type": ("power.schema.json", "power_type"),
    "duty_type": ("duty.schema.json", "duty_type"),
    "legal_effect": ("power.schema.json", "legal_effect"),
}


def veto_strength_errors(vetoes):
    """Tier 1 of the strength audit (2026-07-20): internal coherence of a veto's grading.

    A veto graded `hard_stop` claims there is NO lawful route around it, so a record that
    also says `overridable: yes` contradicts itself, and one saying `unknown` asserts a
    grading it admits it cannot support. Both are defects rather than opinions — this is
    the check that would have caught all 8 Water-tranche vetoes being labelled hard_stop.
    Rubric: vocab/veto_strength.json v0.2. Returns a list of message strings.
    """
    out = []
    for rec in vetoes:
        vid, strength, ovr = rec.get("veto_id"), rec.get("strength"), rec.get("overridable")
        if strength == "hard_stop" and ovr == "yes":
            out.append(f"vetoes[{vid}]: strength 'hard_stop' contradicts overridable 'yes' "
                       f"(override: {rec.get('override_mechanism')!r}) — grade strong_delay")
        elif strength == "hard_stop" and ovr in (None, "unknown"):
            out.append(f"vetoes[{vid}]: strength 'hard_stop' unsupported while overridable is "
                       f"'{ovr}' — run the override sweep before grading")
        if strength == "strong_delay" and ovr != "yes":
            out.append(f"vetoes[{vid}]: strength 'strong_delay' requires overridable 'yes' "
                       f"(is '{ovr}')")
        if ovr == "yes" and not rec.get("override_mechanism"):
            out.append(f"vetoes[{vid}]: overridable 'yes' requires a cited override_mechanism")
    return out


def vocab_schema_errors(repo=REPO):
    """Core rule 3 (no uncontrolled vocabulary drift): the vocab files are the human-readable
    definitions, the schema enums are what is enforced. If they diverge, one is lying."""
    out = []
    for vocab_name, (schema_file, field) in VOCAB_FIELDS.items():
        vpath = os.path.join(repo, "vocab", vocab_name + ".json")
        spath = os.path.join(repo, "schemas", schema_file)
        if not (os.path.exists(vpath) and os.path.exists(spath)):
            continue
        terms = load_json(vpath).get("terms", [])
        # v0.2+ vocabs carry {term, definition, ...}; older ones are bare strings.
        vocab_terms = {t["term"] if isinstance(t, dict) else t for t in terms}
        enum = load_json(spath).get("properties", {}).get(field, {}).get("enum")
        if enum and vocab_terms != set(enum):
            out.append(f"vocab/{vocab_name}.json disagrees with {schema_file}.{field}: "
                       f"only-in-vocab={sorted(vocab_terms - set(enum))} "
                       f"only-in-schema={sorted(set(enum) - vocab_terms)}")
    return out


def main():
    # errors     = schema violations (a record breaks its contract)
    # integrity  = a data file/schema is missing, or a reference points nowhere, or a
    #              body's sponsor field disagrees with the canonical edges. These are real
    #              defects, so they FAIL the build (exit 1) — the gate must not pass open.
    # warnings   = advisory only.
    errors = integrity = warnings = records = 0
    body_ids = {r["body_id"] for r in store.load("bodies")}
    source_ids = {r["source_id"] for r in store.load("sources")}
    office_ids = {r["office_id"] for r in store.load("offices")}
    # Powers-layer FK sets (Annex A6, active from Spiral 2; empty until records land).
    power_ids = {r["power_id"] for r in store.load("powers")}
    duty_ids = {r["duty_id"] for r in store.load("duties")}
    provision_keys = {r["provision_key"] for r in store.load("provisions")}
    instrument_ids = {r["instrument_id"] for r in store.load("instruments")}

    # Sponsor/parent truth from the canonical relationship edges, to check the body
    # convenience fields against (#8: duplicated truth must not silently diverge).
    btype = {r["body_id"]: r["body_type"] for r in store.load("bodies")}
    DEPARTMENT_TYPES = {"ministerial_department", "non_ministerial_department"}
    dept_parents, other_parents = {}, {}
    for r in store.load("relationships"):
        if r.get("relationship_type") != "sponsors":
            continue
        child, parent = r.get("to_body_id"), r.get("from_body_id")
        bucket = dept_parents if btype.get(parent) in DEPARTMENT_TYPES else other_parents
        bucket.setdefault(child, set()).add(parent)

    for t, schema_file in TYPE_SCHEMA.items():
        schema_path = os.path.join(REPO, "schemas", schema_file)
        # Fail closed: a required data file or its schema going missing must not pass
        # silently (the old code skipped a missing schema and load() returns [] for a
        # missing array, so a vanished file would validate clean).
        if not os.path.exists(store.path(t)):
            integrity += 1
            print(f"FAIL {t}: data file {t}.json is missing")
            continue
        if not os.path.exists(schema_path):
            integrity += 1
            print(f"FAIL {t}: schema {schema_file} is missing")
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
            # referential integrity (per record) — a reference pointing nowhere is a defect
            if t == "bodies":
                bid = rec["body_id"]
                sp = rec.get("sponsor_department_id")
                if sp and sp not in body_ids:
                    integrity += 1
                    print(f"FAIL {t}.sponsor_department_id -> {sp} not among bodies")
                elif sp and sp not in dept_parents.get(bid, set()):
                    integrity += 1
                    print(f"FAIL {t}.sponsor_department_id {bid} -> {sp} has no matching 'sponsors' edge (#8 divergence)")
                pb = rec.get("parent_body_id")
                if pb and pb not in body_ids:
                    integrity += 1
                    print(f"FAIL {t}.parent_body_id -> {pb} not among bodies")
                elif pb and pb not in other_parents.get(bid, set()):
                    integrity += 1
                    print(f"FAIL {t}.parent_body_id {bid} -> {pb} has no matching 'sponsors' edge (#8 divergence)")
                for field in ("classification_source_ids", "founding_source_ids",
                              "framework_document_source_ids", "annual_report_source_ids", "function_source_ids"):
                    for ref in rec.get(field, []):
                        if ref not in source_ids:
                            integrity += 1
                            print(f"FAIL {t}.{field} -> {ref} not among sources")
            elif t == "relationships":
                for field in ("from_body_id", "to_body_id"):
                    ref = rec.get(field)
                    if ref and ref not in body_ids:
                        integrity += 1
                        print(f"FAIL relationships.{field} -> {ref} not among bodies")
            elif t in ("offices", "person-roles", "budgets", "staffing"):
                ref = rec.get("body_id")
                if ref and ref not in body_ids:
                    integrity += 1
                    print(f"FAIL {t}.body_id -> {ref} not among bodies")
            elif t in ("powers", "duties", "vetoes"):
                if rec.get("body_id") not in body_ids:
                    integrity += 1
                    print(f"FAIL {t}.body_id -> {rec.get('body_id')} not among bodies")
                if rec.get("holder_type") == "office" and rec.get("office_id") not in office_ids:
                    integrity += 1
                    print(f"FAIL {t}.office_id -> {rec.get('office_id')} not among offices (holder_type=office)")
                if rec.get("source_id") not in source_ids:
                    integrity += 1
                    print(f"FAIL {t}.source_id -> {rec.get('source_id')} not among sources")
                if rec.get("provision_key") not in provision_keys:
                    integrity += 1
                    print(f"FAIL {t}.provision_key -> {rec.get('provision_key')} not among provisions")
                if t == "vetoes" and rec.get("derived_from_record_id") not in power_ids:
                    integrity += 1
                    print(f"FAIL vetoes.derived_from_record_id -> {rec.get('derived_from_record_id')} not among powers")
            elif t == "instruments":
                if rec.get("source_id") not in source_ids:
                    integrity += 1
                    print(f"FAIL instruments.source_id -> {rec.get('source_id')} not among sources")
            elif t in ("provisions", "definitions"):
                if rec.get("instrument_id") not in instrument_ids:
                    integrity += 1
                    print(f"FAIL {t}.instrument_id -> {rec.get('instrument_id')} not among instruments")
            if t == "person-roles":
                ref = rec.get("office_id")
                if ref and ref not in office_ids:
                    integrity += 1
                    print(f"FAIL person-roles.office_id -> {ref} not among offices")
        print("ok   {}.json  ({} records{})".format(t, len(recs), ", " + str(bad) + " FAIL" if bad else ""))

    for msg in veto_strength_errors(store.load("vetoes")):
        errors += 1
        print("FAIL " + msg)
    for msg in vocab_schema_errors():
        integrity += 1
        print("FAIL " + msg)

    # Two distinct gaps, deliberately reported differently (sponsor ruling 2026-07-20).
    #
    # (a) No blocked PARTY. The veto blocks someone outside the modelled state — a private
    #     person or an unnamed class. No CAN_VETO edge is drawn and that is CORRECT: the map
    #     models what the state does to itself. The record still surfaces on the entity card
    #     and in the query layer, which is where "can I do this?" is answered. Informational.
    #
    # (b) Blocked party IS modelled, but the power it is blocked from exercising is not.
    #     That is a real COVERAGE GAP — the chain can only traverse body-to-body, not
    #     power-to-power — and it is an extraction work item (cf. decision #27 breadcrumbs).
    for rec in store.load("vetoes"):
        blocked_party = rec.get("blocks_body_id") or rec.get("blocks_office_id")
        if not blocked_party:
            warnings += 1
            print(f"WARN vetoes[{rec['veto_id']}]: blocks a party outside the modelled state — "
                  f"no CAN_VETO edge by design; carried on the card only "
                  f"({(rec.get('decision_affected') or '')[:56]}...)")
        elif not rec.get("blocks_record_id"):
            warnings += 1
            print(f"WARN vetoes[{rec['veto_id']}]: blocks {blocked_party} but names no "
                  f"blocks_record_id — the gated power is not yet extracted (coverage gap)")
        # Polymorphic: a veto can obstruct the exercise of a POWER or the discharge of a
        # DUTY (WIA 1991 s.16A blocks the s.16 duty to modify). Check against the right set,
        # and reject a type that disagrees with the id it points at.
        ref, rtype = rec.get("blocks_record_id"), rec.get("blocks_record_type")
        if ref:
            pool = duty_ids if rtype == "duty" else power_ids
            if ref not in pool:
                integrity += 1
                print(f"FAIL vetoes.blocks_record_id -> {ref} not among {rtype or 'power'}s")
            expected = "duty" if ref.startswith("duty-") else "power"
            if rtype and rtype != expected:
                integrity += 1
                print(f"FAIL vetoes[{rec['veto_id']}]: blocks_record_type '{rtype}' disagrees "
                      f"with the id it points at ({ref})")
        elif rtype:
            integrity += 1
            print(f"FAIL vetoes[{rec['veto_id']}]: blocks_record_type '{rtype}' set with no "
                  f"blocks_record_id")

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
    print(f"records checked: {records}  schema errors: {errors}  "
          f"integrity failures: {integrity}  warnings: {warnings}")
    sys.exit(1 if errors or integrity else 0)


if __name__ == "__main__":
    main()
