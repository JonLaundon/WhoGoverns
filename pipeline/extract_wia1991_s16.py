#!/usr/bin/env python3
"""Close the WIA 1991 s.16 breadcrumb: the obligation the CMA's s.16A veto actually bites on.

One job. Background: s.16A (the CMA's power to direct Ofwat NOT to make licence-condition
modifications) was extracted without s.16, the record it obstructs — so the veto could name
the blocked BODY but not the blocked DECISION, and the delivery chain traversed body-to-body
instead of record-to-record. Found by populating `blocks_record_id` (decision #27 breadcrumb
method) rather than by a human noticing.

Two findings this trawl produced:

  1. s.16 is a DUTY, not a power. "the Authority SHALL, subject to the following provisions
     of this section, make such modifications of the conditions of that appointment as appear
     to it requisite" (s.16(1)). The discretion is in WHICH modifications, not WHETHER — so
     the modality is `duty`. It is emphatically not s.13 (modification by agreement, no CMA
     involvement) nor s.14 (the referral, the step before).

  2. Because of (1), a veto can obstruct the discharge of a DUTY, not only the exercise of a
     power. `blocks_power_id` was therefore generalised to `blocks_record_id` +
     `blocks_record_type`. Done now, at 8 vetoes, rather than at scale.

Re-runnable and idempotent.

    py -3 pipeline/extract_wia1991_s16.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-20-wia1991-s16-breadcrumb"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
CMA = "uk-state-body-competition-and-markets-authority"

DUTY = {
    "duty_id": "duty-ofwat-wia1991-s16",
    "holder_type": "body",
    "body_id": OFWAT,
    "office_id": None,
    "duty_label": "Modify appointment conditions following an adverse CMA report",
    # No `rulemaking` term exists on the duty axis; the obligation is to remedy the adverse
    # effects the CMA found, which none of the other terms fits (vocab rule: 'other' carries a note).
    "duty_type": "other",
    "modality": "duty",
    "mandatory": True,
    "summary": (
        "Where a CMA report on a s.14 reference concludes that matters operate against the "
        "public interest, specifies the adverse effects, and specifies modifications that "
        "would remedy or prevent them, Ofwat SHALL make such modifications of the company's "
        "appointment conditions as appear to it requisite to remedy or prevent those effects "
        "(WIA 1991 s.16(1)). The obligation is mandatory; the discretion is in which "
        "modifications, not whether to act. This is the decision the CMA's s.16A direction "
        "blocks — not s.13 (modification by agreement) and not s.14 (the referral)."),
    "trigger": (
        "A CMA report on a s.14 modification reference meeting all four limbs of s.16(1)(a)-(d)."),
    "beneficiary_or_object": (
        "The public interest, as found by the CMA; the company whose appointment is modified."),
    "failure_consequence": "unknown",
    "owed_to_holder_type": None,
    "owed_to_body_id": None,
    "owed_to_office_id": None,
    "source_id": "source-act-water-industry-act-1991",
    "provision_key": "water-industry-act-1991-s16",
    "citation": {"provision": "s.16(1)",
                 "url": "https://www.legislation.gov.uk/ukpga/1991/56/section/16",
                 "quote": None},
    "related_body_ids": [CMA],
    "derived_from_record_id": None,
    "in_force_from": None,
    "in_force_to": None,
    "legal_status": "current",
    "extraction": {"confidence": 0.92, "extracted_by": "llm",
                   "extraction_run_id": RUN, "requires_review": True},
    "verification": {"verification_status": "unverified", "verified_by": None,
                     "verified_date": None, "verification_notes": None},
    "notes": (
        "Procedural gates NOT separately extracted in this first pass (decision #11), and "
        "logged as breadcrumb stubs instead: s.16(3) requires notice with at least 28 days "
        "for representations or objections, which Ofwat must consider — a genuine consultation "
        "duty in its own right; s.16(4A)-(4B) require notice to the CMA with the representations "
        "received; s.16(4C) makes the modifications due only once four weeks elapse WITHOUT an "
        "s.16A(1)(a) direction — the statutory clock the veto operates through; s.16(5) bars "
        "modification of s.7(4)(c) provisions and of protected-land provisions stated to be "
        "unmodifiable."),
    "record_status": "extracted",
}


def main():
    provisions = {p["provision_key"] for p in store.load("provisions")}
    if DUTY["provision_key"] not in provisions:
        sys.exit("FAIL: provision water-industry-act-1991-s16 missing — run "
                 "pipeline/fetch_legislation.py first (s.16 was added to the WIA section list).")
    store.upsert("duties", [DUTY])

    # Point the CMA veto at what it actually blocks, and migrate the field name.
    vetoes = store.load("vetoes")
    for v in vetoes:
        if "blocks_power_id" in v:                      # migrate the generalised field
            old = v.pop("blocks_power_id")
            v.setdefault("blocks_record_id", old)
            v.setdefault("blocks_record_type", "power" if old else None)
        if v["veto_id"] == "veto-cma-wia1991-s16a-veto":
            v["blocks_record_id"] = DUTY["duty_id"]
            v["blocks_record_type"] = "duty"
            v["notes"] = (v.get("notes") or "") + (
                " Target tied out 2026-07-20 (breadcrumb trawl): the CMA direction blocks the "
                "s.16 DUTY to modify following an adverse report — the first case proving a veto "
                "can obstruct a duty, not only a power.")
    store.save("vetoes", vetoes)

    tied = sum(1 for v in vetoes if v.get("blocks_record_id"))
    print("--- WIA s.16 breadcrumb ---")
    print(f"  duty recorded:      {DUTY['duty_id']}")
    print(f"  vetoes with target: {tied} of {len(vetoes)}")
    print(f"  duties now:         {len(store.load('duties'))}")


if __name__ == "__main__":
    main()
