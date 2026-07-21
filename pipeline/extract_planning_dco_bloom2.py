#!/usr/bin/env python3
"""DCO bloom round 2 — driven by the regime's own cross-references (systematic, not the case).

The breadcrumb targets from the held planning provisions. This round is mostly CLASSIFICATION
— the convergence signal that the planning domain's STATE-side operative records are nearly
exhausted: most remaining DCO sections impose duties on the APPLICANT (a private party) or are
constitutive framework. The one genuine new state record is the SoS's NPS-consultation duty.

    py -3 pipeline/extract_planning_dco_bloom2.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-21-planning-dco-bloom2"
SRC = "source-act-planning-act-2008"
SOS = "office-secretary-of-state-for-environment-food-and-rural-affairs"
DEFRA = "uk-state-body-department-for-environment-food-rural-affairs"
URL = "https://www.legislation.gov.uk/ukpga/2008/29/section/"

DUTY = {
    "duty_id": "duty-sos-defra-planning2008-s7", "holder_type": "office", "office_id": SOS,
    "body_id": DEFRA, "duty_label": "Consult and publicise before designating a National Policy Statement",
    "duty_type": "consultation", "modality": "duty", "mandatory": True,
    "summary": ("Before designating a statement as a National Policy Statement, the Secretary of "
                "State must carry out the consultation and publicity prescribed by Planning Act "
                "2008 s.7 (and satisfy the parliamentary requirements in s.9). The procedural gate "
                "on setting the framework that then shapes every DCO decision (s.104) — the NPS "
                "consultation is where the policy is contested before it hardens into the test a "
                "reservoir must pass."),
    "trigger": "Before designating (or amending) a National Policy Statement under s.5.",
    "beneficiary_or_object": "Consultees and the public; the legitimacy of the NPS framework.",
    "failure_consequence": "judicial_review_risk",
    "owed_to_holder_type": None, "owed_to_body_id": None, "owed_to_office_id": None,
    "source_id": SRC, "provision_key": "planning-act-2008-s7", "citation": {"provision": "s.7",
        "url": URL + "7", "quote": None},
    "related_body_ids": [], "derived_from_record_id": None, "in_force_from": None,
    "in_force_to": None, "legal_status": "current",
    "extraction": {"confidence": 0.88, "extracted_by": "llm", "extraction_run_id": RUN,
                   "requires_review": True},
    "verification": {"verification_status": "unverified", "verified_by": None,
                     "verified_date": None, "verification_notes": None},
    "notes": "Paired with s.9 (parliamentary requirements) — the NPS designation process gates on "
             "the s.5 power. s.9 not separately extracted (parliamentary procedure).",
    "record_status": "extracted",
}


def main():
    if "planning-act-2008-s7" not in {p["provision_key"] for p in store.load("provisions")}:
        sys.exit("FAIL: planning-act-2008-s7 not fetched.")
    store.upsert("duties", [DUTY])
    print("--- DCO bloom round 2 ---")
    print("  + 1 state duty (s.7 NPS consultation); the rest classified in breadcrumbs.py")
    print(f"  totals — duties {len(store.load('duties'))}")


if __name__ == "__main__":
    main()
