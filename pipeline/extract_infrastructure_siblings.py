#!/usr/bin/env python3
"""Bloom the SIBLING infrastructure-consent regimes (planning writ large, not spine).

The Planning Act breadcrumbs reach the consent regimes a DCO interacts with. These are
IN-domain for planning (the consenting fabric a project traverses), not deferred "other
domains" — so the bloom flourishes to them (build-out strategy v0.2). Scoped per #11 to each
regime's core consent-granting power.

  * Marine and Coastal Access Act 2009 s.71 — the MMO grants/refuses a marine licence.
  * Transport and Works Act 1992 s.1 — the SoS (Transport) makes an order authorising a
    railway/tramway/inland-waterway.
  * Harbours Act 1964 s.14 — the SoS (Transport) makes a harbour revision/empowerment order.

VOCAB SIGNAL: the DCO (Planning Act s.114), TWA orders (s.1) and harbour orders (s.14) are all
bespoke statutory "consent orders" authorising infrastructure works — a recurring type with no
`power_type` term (recorded as `approval`, the closest). `consent_order` is a candidate term
for the sponsor (three instances now).

    py -3 pipeline/extract_infrastructure_siblings.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-21-infra-siblings"
MMO = "uk-state-body-marine-management-organisation"
SOS_T = "office-secretary-of-state-for-transport"
DFT = "uk-state-body-department-for-transport"


def ext(c):
    return {"confidence": c, "extracted_by": "llm", "extraction_run_id": RUN, "requires_review": True}


V = {"verification_status": "unverified", "verified_by": None, "verified_date": None,
     "verification_notes": None}

CONSENT_ORDER_NOTE = ("VOCAB SIGNAL: a bespoke statutory 'consent order' authorising "
                      "infrastructure works — the same shape as the Planning Act DCO (s.114) and "
                      "harbour/TWA orders. Recorded as `approval`; `consent_order` is a candidate "
                      "power_type for the sponsor (recurs 3x).")

POWERS = [
    {"power_id": "power-mmo-marine2009-s71", "holder_type": "body", "body_id": MMO, "office_id": None,
     "power_label": "Grant, condition or refuse a marine licence",
     "power_type": "licence", "power_basis": "statutory", "modality": "power", "legal_effect": "must",
     "summary": ("Having considered an application, the Marine Management Organisation must grant "
                 "a marine licence unconditionally, grant it subject to conditions, or refuse it "
                 "(Marine and Coastal Access Act 2009 s.71). The consent for licensable marine "
                 "activities (s.66) — the offshore counterpart a reservoir/transfer scheme with "
                 "any marine works must clear."),
     "constraints": ["Conditions per s.71(2); the activity must be a licensable marine activity (s.66)."],
     "source_id": "source-act-marine-and-coastal-access-act-2009",
     "provision_key": "marine-and-coastal-access-act-2009-s71",
     "citation": {"provision": "s.71(1)", "url": "https://www.legislation.gov.uk/ukpga/2009/23/section/71", "quote": None},
     "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.88), "verification": dict(V),
     "notes": None, "record_status": "extracted"},

    {"power_id": "power-sos-transport-twa1992-s1", "holder_type": "office", "office_id": SOS_T,
     "body_id": DFT, "power_label": "Make a Transport and Works Act order",
     "power_type": "approval", "power_basis": "statutory", "modality": "power", "legal_effect": "may",
     "summary": ("The Secretary of State may make an order authorising the construction or "
                 "operation of a railway, tramway, trolley-vehicle or guided-transport system in "
                 "England and Wales (Transport and Works Act 1992 s.1). The consent-order route "
                 "for transport works below the NSIP threshold — a sibling of the DCO."),
     "constraints": ["Subject to the Act's application and objection procedure."],
     "source_id": "source-act-transport-and-works-act-1992",
     "provision_key": "transport-and-works-act-1992-s1",
     "citation": {"provision": "s.1(1)", "url": "https://www.legislation.gov.uk/ukpga/1992/42/section/1", "quote": None},
     "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.87), "verification": dict(V),
     "notes": CONSENT_ORDER_NOTE, "record_status": "extracted"},

    {"power_id": "power-sos-transport-twa1992-s3", "holder_type": "office", "office_id": SOS_T,
     "body_id": DFT, "power_label": "Make a Transport and Works Act order for inland waterways / navigation works",
     "power_type": "approval", "power_basis": "statutory", "modality": "power", "legal_effect": "may",
     "summary": ("The Secretary of State may make an order relating to the construction or "
                 "operation of an inland waterway, or works interfering with rights of navigation "
                 "(Transport and Works Act 1992 s.3). Directly reservoir-relevant: a reservoir with "
                 "water-transfer or navigation-affecting works needs this consent unless subsumed "
                 "into a DCO."),
     "constraints": ["Subject to the Act's application and objection procedure."],
     "source_id": "source-act-transport-and-works-act-1992",
     "provision_key": "transport-and-works-act-1992-s3",
     "citation": {"provision": "s.3(1)", "url": "https://www.legislation.gov.uk/ukpga/1992/42/section/3", "quote": None},
     "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.86), "verification": dict(V),
     "notes": CONSENT_ORDER_NOTE, "record_status": "extracted"},

    {"power_id": "power-sos-transport-harbours1964-s14", "holder_type": "office", "office_id": SOS_T,
     "body_id": DFT, "power_label": "Make a harbour revision or empowerment order",
     "power_type": "approval", "power_basis": "statutory", "modality": "power", "legal_effect": "may",
     "summary": ("On the application of a harbour authority (or others), the appropriate Minister "
                 "may make an order for securing the improvement, maintenance or management of a "
                 "harbour, or reconstituting a harbour authority (Harbours Act 1964 s.14). The "
                 "harbour consent-order route — another DCO sibling."),
     "constraints": ["Subject to the Act's provisions and objection procedure."],
     "source_id": "source-act-harbours-act-1964",
     "provision_key": "harbours-act-1964-s14",
     "citation": {"provision": "s.14(1)", "url": "https://www.legislation.gov.uk/ukpga/1964/40/section/14", "quote": None},
     "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.85), "verification": dict(V),
     "notes": CONSENT_ORDER_NOTE + " 'Appropriate Minister' modelled as the SoS for Transport; "
             "for some harbours it is another department — holder-resolution note.",
     "record_status": "extracted"},
]


def main():
    have = {p["provision_key"] for p in store.load("provisions")}
    for pk in ("marine-and-coastal-access-act-2009-s71", "transport-and-works-act-1992-s1",
               "transport-and-works-act-1992-s3", "harbours-act-1964-s14"):
        if pk not in have:
            sys.exit(f"FAIL: {pk} not fetched.")
    store.upsert("powers", POWERS)
    print("--- infrastructure siblings ---")
    print(f"  + {len(POWERS)} sibling consent powers (MMO marine licence; SoS-T TWA + harbour orders)")
    print(f"  totals — powers {len(store.load('powers'))}")


if __name__ == "__main__":
    main()
