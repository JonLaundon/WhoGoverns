#!/usr/bin/env python3
"""Close the s.17K breadcrumb: the CMA's veto over LICENCE-condition modifications (s.17P).

One job. s.17K (Ofwat's power to refer a licence modification to the CMA) was extracted with
a logged stub: the CMA's veto-following-report for LICENCES — the s.16A-equivalent — was a
later un-fetched section. Followed the breadcrumb; it is s.17P ("Power of veto following
report"), mechanism identical to s.16A ("direct the Authority ... not to make the
modifications ... and the Authority shall comply"). Exactly mirrors the appointment-condition
chain (s.14 -> s.15 -> s.16 duty -> s.16A veto) one Chapter over.

Records the full triple, so the veto has a real target (the s.16 lesson: never extract the
veto without the duty it blocks):
  * s.17O — Ofwat's DUTY to modify licence conditions following an adverse CMA report.
  * s.17P — the CMA's `direction` POWER, and its derived VETO over that duty.

s.17L (time limits) and s.17M (investigation powers, applied FROM the Enterprise Act 2002)
are marked CORRECTLY_UNMINED — procedural, and the operative investigation powers are the
Enterprise Act's (a cross-domain breadcrumb, captured in Provision.references, not re-minted).

Re-runnable and idempotent.

    py -3 pipeline/extract_wia1991_licence_veto.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-21-wia1991-licence-veto"
SRC = "source-act-water-industry-act-1991"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
CMA = "uk-state-body-competition-and-markets-authority"


def cite(prov):
    return {"provision": prov, "quote": None,
            "url": "https://www.legislation.gov.uk/ukpga/1991/56/section/" + prov.split("(")[0].lstrip("s.")}


def ext(c):
    return {"confidence": c, "extracted_by": "llm", "extraction_run_id": RUN, "requires_review": True}


V = {"verification_status": "unverified", "verified_by": None, "verified_date": None,
     "verification_notes": None}

DUTY = {
    "duty_id": "duty-ofwat-wia1991-s17o", "holder_type": "body", "body_id": OFWAT,
    "office_id": None,
    "duty_label": "Modify licence conditions following an adverse CMA report",
    "duty_type": "other", "modality": "duty", "mandatory": True,
    "summary": ("Where a CMA report on a s.17K licence-modification reference concludes that "
                "matters operate against the public interest and specifies remedying "
                "modifications, Ofwat shall make such modifications of the relevant licence "
                "conditions as appear to it requisite (WIA 1991 s.17O). The licence analogue of "
                "the s.16 duty; the decision the CMA's s.17P veto blocks."),
    "trigger": "A CMA report on a s.17K reference meeting all four limbs of s.17O(1)(a)-(d).",
    "beneficiary_or_object": "The public interest; the licensee whose conditions are modified.",
    "failure_consequence": "unknown",
    "owed_to_holder_type": None, "owed_to_body_id": None, "owed_to_office_id": None,
    "source_id": SRC, "provision_key": "water-industry-act-1991-s17o", "citation": cite("s.17O(1)"),
    "related_body_ids": [CMA], "derived_from_record_id": None,
    "in_force_from": None, "in_force_to": None, "legal_status": "current",
    "extraction": ext(0.9), "verification": dict(V),
    "notes": "The mirror of duty-ofwat-wia1991-s16 in the licence chapter.",
    "record_status": "extracted",
}

POWER = {
    "power_id": "power-cma-wia1991-s17p", "holder_type": "body", "body_id": CMA, "office_id": None,
    "power_label": "Veto Ofwat's licence-condition modifications following report",
    "power_type": "direction", "power_basis": "statutory", "modality": "power",
    "legal_effect": "may",
    "summary": ("Within four weeks of the s.17O(6) notice, the CMA may direct Ofwat not to make "
                "some or all of the proposed licence-condition modifications, and Ofwat shall "
                "comply (WIA 1991 s.17P(1)). The licence analogue of the s.16A CMA veto."),
    "constraints": ["Exercisable only within the four-week window (s.17P(1)); the Secretary of "
                    "State may extend it on the CMA's application (s.17P(2))."],
    "source_id": SRC, "provision_key": "water-industry-act-1991-s17p", "citation": cite("s.17P(1)"),
    "related_body_ids": [OFWAT], "related_power_ids": [], "derived_from_record_id": None,
    "legal_status": "current", "extraction": ext(0.92), "verification": dict(V),
    "notes": None, "record_status": "extracted",
}

VETO = {
    "veto_id": "veto-cma-wia1991-s17p", "holder_type": "body", "body_id": CMA, "office_id": None,
    "veto_label": "CMA veto of Ofwat's proposed licence-condition modifications",
    "veto_type": "direction", "modality": "veto", "strength": "hard_stop",
    "overridable": "no", "override_mechanism": None,
    "summary": ("The CMA may direct Ofwat not to make proposed licence-condition modifications "
                "following an adverse report, and Ofwat must comply (WIA 1991 s.17P(1)). No "
                "appeal for Ofwat; s.17P(2) only lets the Secretary of State extend the CMA's "
                "own four-week window on the CMA's application."),
    "decision_affected": ("Whether Ofwat may modify the conditions of a water supply or "
                          "sewerage licence following a CMA report."),
    "derived_from_record_id": "power-cma-wia1991-s17p",
    "blocks_holder_type": "body", "blocks_body_id": OFWAT, "blocks_office_id": None,
    "blocks_record_id": "duty-ofwat-wia1991-s17o", "blocks_record_type": "duty",
    "blocks_provision_key": "water-industry-act-1991-s17o",
    "source_id": SRC, "provision_key": "water-industry-act-1991-s17p", "citation": cite("s.17P(1)"),
    "legal_status": "current", "extraction": ext(0.92),
    "verification": {"verification_status": "machine_verified", "verified_by": None,
                     "verified_date": "2026-07-21",
                     "verification_notes": "Structurally identical to veto-cma-wia1991-s16a-veto "
                     "(confirmed hard_stop in the strength audit); same 'shall comply', same "
                     "SoS-extends-window-only escape."},
    "notes": ("veto_type `direction` (the established term — statute heading 'Power of veto', "
              "mechanism 'may direct ... not to make'); blocks the s.17O DUTY, the third case of "
              "a veto obstructing a duty rather than a power."),
    "record_status": "extracted",
}


def main():
    provs = {p["provision_key"] for p in store.load("provisions")}
    for pk in ("water-industry-act-1991-s17o", "water-industry-act-1991-s17p"):
        if pk not in provs:
            sys.exit(f"FAIL: {pk} not fetched — run fetch_legislation.py (ss.17O/17P added).")
    store.upsert("duties", [DUTY])
    store.upsert("powers", [POWER])
    store.upsert("vetoes", [VETO])
    print("--- WIA s.17P licence veto (breadcrumb closure) ---")
    print("  + duty s.17O, power s.17P, veto s.17P (blocks the s.17O duty)")
    print(f"  totals — powers {len(store.load('powers'))}, duties {len(store.load('duties'))}, "
          f"vetoes {len(store.load('vetoes'))}")


if __name__ == "__main__":
    main()
