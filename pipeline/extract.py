#!/usr/bin/env python3
"""Materialise Power/Duty/Veto records from classified statutory units, and write them.

This is the DETERMINISTIC half of Spiral 2 extraction — the reusable core that the
per-domain LLM classification step feeds. The LLM's job is judgement (read a provision,
decide modality/type/holder/effect); THIS module owns the parts a script must own so they
are repeatable, testable and cheap across the ~100M-token corpus:

  - resolve a textual actor ("the Authority", "the Secretary of State") to a real
    office_id/body_id — never a free-text holder (holder drift is the costliest error);
  - materialise the DERIVED Veto from a blocking Power (decision #18) mechanically, so a
    veto is never hand-authored and can never disagree with its power;
  - stamp extraction/verification metadata and schema-validate every record before writing.

`is_amendment()` is exposed so callers can route amending provisions to provenance rather
than mint a duplicate power (most of e.g. Water Act 2014 amends WIA 1991 — the power lives
in the consolidated host Act, cited with the amending Act as provenance).

Input = a list of `units` (one operative unit each). See UNIT_SHAPE for the contract.
Boring by design: stdlib + jsonschema, one job, editable cold.

    from extract import run
    run(UNITS, run_id="run-2026-07-15-wia1991-s2")
"""
import json
import os
import re

from jsonschema import Draft202012Validator

import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS = os.path.join(REPO, "schemas")

# The one place actor phrasing meets identity. Extend per tranche; every id is a real
# node in data/bodies.json / data/offices.json (verified at add time). An office holder
# still carries body_id (the hosting department) — the schema requires it.
HOLDER_ALIASES = {
    "ofwat": {"holder_type": "body",
              "body_id": "uk-state-body-the-water-services-regulation-authority"},
    "sos-defra": {"holder_type": "office",
                  "office_id": "office-secretary-of-state-for-environment-food-and-rural-affairs",
                  "body_id": "uk-state-body-department-for-environment-food-rural-affairs"},
    "cma": {"holder_type": "body",
            "body_id": "uk-state-body-competition-and-markets-authority"},
    "ea": {"holder_type": "body", "body_id": "uk-state-body-environment-agency"},
    "ccw": {"holder_type": "body", "body_id": "uk-state-body-consumer-council-for-water"},
    "natural-england": {"holder_type": "body", "body_id": "uk-state-body-natural-england"},
}

# Markers that a provision AMENDS another Act rather than conferring directly.
_AMEND = re.compile(
    r"\b(is amended|are amended|after section|before section|"
    r"insert(?:ed)?|substitute(?:d)?|omit(?:ted)?|"
    r"for .{0,60}? substitute|in subsection)\b", re.I)

# Power families whose exercise can block another actor's decision -> yield a Veto.
BLOCKING_POWER_TYPES = {"consent", "approval", "designation", "licence"}

UNIT_SHAPE = """One operative unit (the LLM classification output):
{
  "record_id": "duty-ofwat-wia1991-s2-primary",   # follows the naming convention
  "kind": "power" | "duty",
  "holder": "ofwat",                                # a HOLDER_ALIASES key
  "label": "...", "summary": "...",
  "subtype": "<power_type or duty_type>",
  "legal_effect": "may|must|...",                  # power only
  "mandatory": true,                                # duty only
  "source_id": "source-act-...", "provision_key": "water-industry-act-1991-s2",
  "provision_ref": "s.2(2A)", "citation_url": "https://...", "quote": null,
  "constraints": [...], "related_power_ids": [...], "related_body_ids": [...],
  "provenance_note": "limb (e)/s.2(2DA) inserted by Water Act 2014 s.22.",  # amend-provenance
  "confidence": 0.9,
  "blocks": {                                       # optional -> derives a Veto
     "veto_type": "consent_required", "strength": "hard_stop",
     "decision_affected": "...", "veto_label": "...",
     "overridable": "unknown", "blocks_provision_key": null
  }
}"""


def resolve_holder(key):
    """Actor alias -> {holder_type, office_id?, body_id}. Raises on an unknown holder:
    an unresolved actor must stop the batch, never be written as free text."""
    h = HOLDER_ALIASES.get(key)
    if h is None:
        raise KeyError(f"unresolved holder '{key}' — add it to HOLDER_ALIASES (verify the id first)")
    return dict(h)


def is_amendment(text):
    """True if the provision text reads as an amendment to another Act (route to provenance)."""
    return bool(_AMEND.search(text or ""))


def _extraction(run_id, confidence):
    return {"extracted_by": "llm", "extraction_run_id": run_id,
            "confidence": confidence, "requires_review": True}


def _verification():
    return {"verification_status": "unverified", "verified_by": None,
            "verified_date": None, "verification_notes": None}


def _holder_fields(key):
    h = resolve_holder(key)
    return {"holder_type": h["holder_type"], "office_id": h.get("office_id"),
            "body_id": h["body_id"]}


def _citation(u):
    return {"provision": u["provision_ref"], "url": u["citation_url"], "quote": u.get("quote")}


def power_record(u, run_id):
    r = {
        "power_id": u["record_id"], **_holder_fields(u["holder"]),
        "power_label": u["label"], "power_type": u["subtype"],
        "power_basis": u.get("power_basis", "statutory"),
        "modality": "power", "legal_effect": u["legal_effect"], "summary": u["summary"],
        "source_id": u["source_id"], "provision_key": u["provision_key"],
        "citation": _citation(u),
        "constraints": u.get("constraints", []),
        "related_body_ids": u.get("related_body_ids", []),
        "related_power_ids": u.get("related_power_ids", []),
        "legal_status": "current",
        "extraction": _extraction(run_id, u.get("confidence", 0.8)),
        "verification": _verification(),
        "notes": u.get("provenance_note"), "record_status": "extracted",
    }
    return r


def duty_record(u, run_id):
    r = {
        "duty_id": u["record_id"], **_holder_fields(u["holder"]),
        "duty_label": u["label"], "duty_type": u["subtype"],
        "modality": "duty", "mandatory": u.get("mandatory", True), "summary": u["summary"],
        "source_id": u["source_id"], "provision_key": u["provision_key"],
        "citation": _citation(u),
        "related_body_ids": u.get("related_body_ids", []),
        "legal_status": "current",
        "extraction": _extraction(run_id, u.get("confidence", 0.8)),
        "verification": _verification(),
        "notes": u.get("provenance_note"), "record_status": "extracted",
    }
    # Optional duty fields, carried through only when the classification supplies them
    # (so an enrichment pass over an existing record does not drop them).
    for f in ("trigger", "beneficiary_or_object", "failure_consequence"):
        if u.get(f) is not None:
            r[f] = u[f]
    return r


def derive_veto(power, blocks, run_id):
    """Materialise the Veto that a Power projects (decision #18), pointing back via
    derived_from_record_id. Two shapes:
      - self-block: the power IS the block (a consent/approval/licence/designation power) —
        the veto holder is the power holder (default);
      - consent-gate: the power is GATED by another actor's consent — the veto holder is that
        gate-keeper, NOT the power holder (e.g. the SoS consent over Ofwat's petition, s.24).
    For a consent-gate, blocks carries `holder` (a HOLDER_ALIASES key) and usually its own
    `veto_id` (so the id names the gate-keeper). Citation/provision/source mirror the power."""
    if blocks.get("holder"):
        h = resolve_holder(blocks["holder"])
    else:
        h = {"holder_type": power["holder_type"], "office_id": power.get("office_id"),
             "body_id": power["body_id"]}
    return {
        "veto_id": blocks.get("veto_id") or power["power_id"].replace("power-", "veto-", 1),
        "holder_type": h["holder_type"], "office_id": h.get("office_id"), "body_id": h["body_id"],
        "veto_label": blocks.get("veto_label", power["power_label"]),
        "veto_type": blocks["veto_type"], "modality": "veto", "strength": blocks["strength"],
        "summary": blocks.get("summary", power["summary"]),
        "source_id": power["source_id"], "provision_key": power["provision_key"],
        "citation": power["citation"],
        "derived_from_record_id": power["power_id"],
        "decision_affected": blocks["decision_affected"],
        "blocks_holder_type": blocks.get("blocks_holder_type"),
        "blocks_body_id": blocks.get("blocks_body_id"),
        "blocks_office_id": blocks.get("blocks_office_id"),
        "blocks_provision_key": blocks.get("blocks_provision_key"),
        "overridable": blocks.get("overridable", "unknown"),
        "override_mechanism": blocks.get("override_mechanism"),
        "legal_status": "current",
        "extraction": _extraction(run_id, power["extraction"]["confidence"]),
        "verification": _verification(),
        "notes": blocks.get("notes"), "record_status": "extracted",
    }


def build(units, run_id):
    """units -> ({powers, duties, vetoes}, issues). A blocking power with `blocks` also
    yields its derived veto. Duplicate record_ids in a batch are an issue, not silent."""
    bundle = {"powers": [], "duties": [], "vetoes": []}
    issues, seen = [], set()
    for u in units:
        rid = u["record_id"]
        if rid in seen:
            issues.append(f"duplicate record_id in batch: {rid}")
            continue
        seen.add(rid)
        if u["kind"] == "power":
            p = power_record(u, run_id)
            bundle["powers"].append(p)
            if u.get("blocks"):
                b = u["blocks"]
                # A self-block normally comes from a blocking-family power; a consent-gate (a named
                # `holder` gate-keeper) may sit on any power type. `self_block: true` is an explicit
                # extractor assertion that this power IS the block despite its type (e.g. a bespoke
                # statutory "power of veto" exercised by direction — WIA s.16A, the CMA veto).
                if (not b.get("holder") and not b.get("self_block")
                        and u["subtype"] not in BLOCKING_POWER_TYPES):
                    issues.append(f"{rid}: self-block on power_type '{u['subtype']}' "
                                  "is not a blocking family — set blocks.self_block if intended")
                bundle["vetoes"].append(derive_veto(p, b, run_id))
        elif u["kind"] == "duty":
            bundle["duties"].append(duty_record(u, run_id))
        else:
            issues.append(f"{rid}: unknown kind '{u['kind']}'")
    return bundle, issues


def _validator(name):
    with open(os.path.join(SCHEMAS, name), encoding="utf-8") as fh:
        return Draft202012Validator(json.load(fh))


def validate_bundle(bundle):
    """Schema-validate every record; return a list of '<id>: <error>' strings ([] = clean)."""
    errors = []
    for kind, schema, idfield in (("powers", "power.schema.json", "power_id"),
                                  ("duties", "duty.schema.json", "duty_id"),
                                  ("vetoes", "veto.schema.json", "veto_id")):
        v = _validator(schema)
        for rec in bundle[kind]:
            for e in v.iter_errors(rec):
                errors.append(f"{rec.get(idfield, '?')}: {e.message}")
    return errors


def paragraph_provision(pk, ref, url, instrument_id, version_date):
    """A paragraph-level Provision node for an independent operative record that shares a
    section with another (A2.5 — two canonical records may not share a provision_key). No
    separate text is fetched, so content_hash/heading are null; the node exists so the
    provision_key references resolve. Mirrors the s.24 calibration convention."""
    return {
        "provision_key": pk, "instrument_id": instrument_id, "provision_ref": ref,
        "heading": None, "in_force_from": None, "status": "in_force",
        "citation": {"url": url, "version_date": version_date, "content_hash": None},
        "references": [], "made_under": None, "commenced_by": None,
        "outstanding_effects": False,
        "outstanding_effects_note": "Outstanding-effects check not yet wired (Spiral 2 TODO).",
        "notes": "Paragraph-level provision for an independent operative record (see extract driver).",
        "record_status": "extracted",
    }


def write(bundle, provisions=None):
    if provisions:
        store.upsert("provisions", provisions)
    for kind in ("powers", "duties", "vetoes"):
        if bundle[kind]:
            store.upsert(kind, bundle[kind])


def run(units, run_id, provisions=None, dry_run=False):
    """Full path: build -> validate -> (write). Refuses to write an invalid batch. Any
    paragraph-level `provisions` are written first so the records' provision_keys resolve."""
    bundle, issues = build(units, run_id)
    for i in issues:
        print(f"  ! {i}")
    errors = validate_bundle(bundle)
    if errors:
        print(f"REFUSING TO WRITE — {len(errors)} schema error(s):")
        for e in errors:
            print(f"  x {e}")
        return bundle, issues, errors
    counts = {k: len(v) for k, v in bundle.items()}
    counts["provisions"] = len(provisions or [])
    print(f"built {counts} — run_id={run_id}")
    if not dry_run:
        write(bundle, provisions)
        print("written.")
    return bundle, issues, errors
