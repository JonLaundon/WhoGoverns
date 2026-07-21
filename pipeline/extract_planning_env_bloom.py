#!/usr/bin/env python3
"""Bloom round — planning in-domain (s.60) + the environment/heritage siblings the DCO reaches.

Following the breadcrumbs (not the reservoir): the Planning one-consent list and the
environment tranche reach heritage consent and the biodiversity duty, both genuine
infrastructure blockers.

  * Ancient Monuments Act 1979 s.2 — scheduled monument consent (SoS/DCMS). Note s.2(1)
    confirms a DCO can authorise the works, so SMC is another consent a DCO can subsume
    (the s.150 fusion pattern, for heritage).
  * NERC Act 2006 s.40 — the biodiversity duty on EVERY public authority (a cross-cutting
    have-regard duty; the reservoir decision-maker must have regard to it).
  * Planning Act 2008 s.60 — the SoS must invite Local Impact Reports, the statutory input
    of the local authorities (a class-counterparty consultation duty).

s.43 (defines which local authorities) is classified constitutive.

    py -3 pipeline/extract_planning_env_bloom.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-21-planning-env-bloom"
SOS_D = "office-secretary-of-state-for-environment-food-and-rural-affairs"
DEFRA = "uk-state-body-department-for-environment-food-rural-affairs"
DCMS = "uk-state-body-department-for-culture-media-and-sport"
HE = "uk-state-body-historic-england"


def ext(c):
    return {"confidence": c, "extracted_by": "llm", "extraction_run_id": RUN, "requires_review": True}


V = {"verification_status": "unverified", "verified_by": None, "verified_date": None,
     "verification_notes": None}

POWERS = [
    {"power_id": "power-sos-dcms-amaa1979-s2", "holder_type": "body", "body_id": DCMS,
     "office_id": None, "power_label": "Grant scheduled monument consent",
     "power_type": "consent", "power_basis": "statutory", "modality": "power", "legal_effect": "may",
     "summary": ("Works to a scheduled monument are an offence unless authorised by scheduled "
                 "monument consent (or by development consent) — the Secretary of State grants "
                 "SMC (Ancient Monuments and Archaeological Areas Act 1979 s.2). A heritage gate a "
                 "reservoir affecting archaeology must clear; Historic England advises. s.2(1) "
                 "confirms a DCO can authorise the works instead, so SMC is another consent a DCO "
                 "can subsume (the s.150 fusion pattern, for heritage)."),
     "constraints": ["Works to a scheduled monument are otherwise an offence (s.2(1))."],
     "source_id": "source-act-ancient-monuments-and-archaeological-areas-act-1979",
     "provision_key": "ancient-monuments-and-archaeological-areas-act-1979-s2",
     "citation": {"provision": "s.2", "url": "https://www.legislation.gov.uk/ukpga/1979/46/section/2", "quote": None},
     "related_body_ids": [HE], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.86), "verification": dict(V),
     "notes": "HOLDER: the SoS for Culture (DCMS) grants SMC; recorded on the DCMS body (no clean "
              "DCMS-SoS office yet). Historic England (related) advises/administers.",
     "record_status": "extracted"},
]

DUTIES = [
    {"duty_id": "duty-sos-defra-nerc2006-s40", "holder_type": "office", "office_id": SOS_D,
     "body_id": DEFRA, "duty_label": "Have regard to conserving and enhancing biodiversity",
     "duty_type": "environmental", "modality": "duty", "mandatory": True,
     "summary": ("A public authority with functions in relation to England must have regard to "
                 "the general biodiversity objective — conserving and enhancing biodiversity — in "
                 "exercising its functions (NERC Act 2006 s.40, as strengthened by the "
                 "Environment Act 2021). A cross-cutting have-regard duty: the reservoir "
                 "decision-maker must weigh biodiversity, and departure invites challenge."),
     "trigger": "In exercising any function in relation to England.",
     "beneficiary_or_object": "Biodiversity; the environment.",
     "failure_consequence": "judicial_review_risk",
     "owed_to_holder_type": None, "owed_to_body_id": None, "owed_to_office_id": None,
     "source_id": "source-act-natural-environment-and-rural-communities-act-2006",
     "provision_key": "natural-environment-and-rural-communities-act-2006-s40",
     "citation": {"provision": "s.40", "url": "https://www.legislation.gov.uk/ukpga/2006/16/section/40", "quote": None},
     "related_body_ids": [], "derived_from_record_id": None, "in_force_from": None,
     "in_force_to": None, "legal_status": "current", "extraction": ext(0.85), "verification": dict(V),
     "notes": "CROSS-CUTTING: a general duty on EVERY public authority (like the Equality Act "
              "s.149 duty). Recorded on the Defra SoS as the reservoir DCO decision-maker "
              "instance; the same duty sits on every body exercising English functions.",
     "record_status": "extracted"},

    {"duty_id": "duty-sos-defra-planning2008-s60", "holder_type": "office", "office_id": SOS_D,
     "body_id": DEFRA, "duty_label": "Invite Local Impact Reports from the affected local authorities",
     "duty_type": "consultation", "modality": "duty", "mandatory": True,
     "summary": ("Where the Secretary of State has accepted a DCO application, the Secretary of "
                 "State must give each affected local authority the opportunity to submit a Local "
                 "Impact Report on the likely impact of the development (Planning Act 2008 s.60). "
                 "The statutory channel for local-authority input into the decision — the local "
                 "objectors' formal voice."),
     "trigger": "After accepting a DCO application (s.55).",
     "beneficiary_or_object": "The affected local authorities (a class); local impact evidence.",
     "failure_consequence": "judicial_review_risk",
     "owed_to_holder_type": None, "owed_to_body_id": None, "owed_to_office_id": None,
     "source_id": "source-act-planning-act-2008",
     "provision_key": "planning-act-2008-s60",
     "citation": {"provision": "s.60(2)", "url": "https://www.legislation.gov.uk/ukpga/2008/29/section/60", "quote": None},
     "related_body_ids": [], "derived_from_record_id": None, "in_force_from": None,
     "in_force_to": None, "legal_status": "current", "extraction": ext(0.86), "verification": dict(V),
     "notes": "Class counterparty: the 'affected local authorities' under s.43 — no single body, "
              "so owed_to is null (a multi-counterparty consultation, #29-adjacent).",
     "record_status": "extracted"},
]


def main():
    have = {p["provision_key"] for p in store.load("provisions")}
    for pk in ("ancient-monuments-and-archaeological-areas-act-1979-s2",
               "natural-environment-and-rural-communities-act-2006-s40", "planning-act-2008-s60"):
        if pk not in have:
            sys.exit(f"FAIL: {pk} not fetched.")
    store.upsert("powers", POWERS)
    store.upsert("duties", DUTIES)
    print("--- planning + environment bloom ---")
    print(f"  + {len(POWERS)} power (SMC), {len(DUTIES)} duties (biodiversity, LIR)")
    print(f"  totals — powers {len(store.load('powers'))}, duties {len(store.load('duties'))}")


if __name__ == "__main__":
    main()
