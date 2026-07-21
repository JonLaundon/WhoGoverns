#!/usr/bin/env python3
"""Extract the cross-cutting competition-law SPINE — once, for every regulated domain.

One job (build-out strategy v0.1). The water breadcrumbs reach general competition/company
law that EVERY regulated sector reaches the same way. Rather than re-touch it per domain (and
recreate the s.16 missing-target problem at scale), it is extracted once here, scoped to the
provisions actually reached (decision #11).

Three records, all cross-cutting:
  * Enterprise Act 2002 s.109 — the CMA's power to require attendance of witnesses and
    production of documents for its investigations (reached via WIA s.17M).
  * Enterprise Act 2002 s.75 — the CMA's power to make an order where an undertaking is not
    fulfilled (reached via WIA s.17R).
  * Competition Act 1998 s.54 — the CONCURRENCY regime: Ofwat (and the other named sector
    regulators — Ofgem, Ofcom, ORR, CAA, FCA) exercises the Chapter I/II competition-
    enforcement functions concurrently with the CMA in its sector. This is the record that
    explains why `regulation` is a cross-cutting function: the same concurrent power sits on
    every utility regulator. Reached via WIA s.22A.

NOT extracted (correctly): the Chapter I/II prohibitions themselves (CA1998 ss.2, 18) bind
undertakings, not the state — the state-side record is the enforcement power above. The
s.124A trigger instruments (Companies Act 1985, FSMA 2000, Criminal Justice Act 1987) are
registered as instrument nodes but belong to a future corporate-enforcement domain.

Re-runnable and idempotent.

    py -3 pipeline/extract_competition_spine.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-21-competition-spine"
EA = "source-act-enterprise-act-2002"
CA = "source-act-competition-act-1998"
CMA = "uk-state-body-competition-and-markets-authority"
OFWAT = "uk-state-body-the-water-services-regulation-authority"


def cite(url, prov):
    return {"provision": prov, "quote": None, "url": url}


def ext(c):
    return {"confidence": c, "extracted_by": "llm", "extraction_run_id": RUN, "requires_review": True}


V = {"verification_status": "unverified", "verified_by": None, "verified_date": None,
     "verification_notes": None}

EA_URL = "https://www.legislation.gov.uk/ukpga/2002/40/section/"
CA_URL = "https://www.legislation.gov.uk/ukpga/1998/41/section/"

POWERS = [
    {"power_id": "power-cma-enterprise2002-s109", "holder_type": "body", "body_id": CMA,
     "office_id": None,
     "power_label": "Require attendance of witnesses and production of documents",
     "power_type": "information_request", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("The CMA may, for the purposes of its investigation and enforcement functions "
                 "under Part 3, require any person to attend and give evidence or to produce "
                 "documents (Enterprise Act 2002 s.109), enforced by penalties (ss.110-116). The "
                 "general investigatory machinery applied to sectoral references — reached from "
                 "the water regime via WIA 1991 s.17M and shared by every regulated sector."),
     "constraints": ["Exercisable for the 'permitted purposes' in s.109(A1) — assisting the CMA "
                     "(or SoS) in Part 3 functions connected with a reference."],
     "source_id": EA, "provision_key": "enterprise-act-2002-s109",
     "citation": cite(EA_URL + "109", "s.109"), "related_body_ids": [], "related_power_ids": [],
     "derived_from_record_id": None, "legal_status": "current", "extraction": ext(0.88),
     "verification": dict(V),
     "notes": "Cross-cutting spine record: reached identically by every sector that refers to "
              "the CMA (water via WIA ss.17K-17M; energy/telecoms/rail likewise).",
     "record_status": "extracted"},

    {"power_id": "power-cma-enterprise2002-s75", "holder_type": "body", "body_id": CMA,
     "office_id": None,
     "power_label": "Make an order where an undertaking is not fulfilled",
     "power_type": "enforcement", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("Where the CMA considers that an undertaking it accepted under s.73 has not "
                 "been or will not be fulfilled (or was procured by false information), it may "
                 "make an order to achieve the purposes of that undertaking (Enterprise Act 2002 "
                 "s.75). The order-making power reached from the water regime via WIA 1991 s.17R "
                 "(competition orders that can modify a licence)."),
     "constraints": ["Contingent on an accepted s.73 undertaking having failed (s.75(1))."],
     "source_id": EA, "provision_key": "enterprise-act-2002-s75",
     "citation": cite(EA_URL + "75", "s.75"), "related_body_ids": [], "related_power_ids": [],
     "derived_from_record_id": None, "legal_status": "current", "extraction": ext(0.86),
     "verification": dict(V),
     "notes": "Reached from WIA s.17R: such an order 'may also provide for the modification' of "
              "water/sewerage licence conditions — the competition-remedy route into the licence "
              "regime.",
     "record_status": "extracted"},

    {"power_id": "power-ofwat-competition1998-s54", "holder_type": "body", "body_id": OFWAT,
     "office_id": None,
     "power_label": "Enforce competition law concurrently with the CMA (water sector)",
     "power_type": "enforcement", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("Ofwat is a named 'regulator' under Competition Act 1998 s.54 and (via "
                 "Schedule 10) exercises the Act's functions — enforcing the Chapter I "
                 "prohibition on anti-competitive agreements (s.2) and the Chapter II "
                 "prohibition on abuse of a dominant position (s.18) — CONCURRENTLY with the CMA, "
                 "so far as they relate to the water and sewerage sector. The statutory basis of "
                 "Ofwat's competition role, distinct from its WIA licensing role."),
     "constraints": ["Concurrent with the CMA, confined to the water/sewerage sector (s.54; "
                     "Sch 10)."],
     "source_id": CA, "provision_key": "competition-act-1998-s54",
     "citation": cite(CA_URL + "54", "s.54"), "related_body_ids": [CMA], "related_power_ids": [],
     "derived_from_record_id": None, "legal_status": "current", "extraction": ext(0.87),
     "verification": dict(V),
     "notes": "THE spine payoff: s.54 names Ofwat, Ofgem/GEMA, Ofcom, ORR, the CAA, the NI "
              "utility regulator, the PSR and the FCA as concurrent 'regulators'. The identical "
              "concurrent-enforcement power sits on each — a cross-cutting record every utility "
              "domain reuses, and part of why `regulation` is a function spanning body_types. "
              "The Chapter I/II prohibitions (ss.2, 18) themselves bind UNDERTAKINGS (private "
              "parties), so they are not state-body records; this enforcement power is.",
     "record_status": "extracted"},
]


def main():
    provs = {p["provision_key"] for p in store.load("provisions")}
    for pk in ("enterprise-act-2002-s109", "enterprise-act-2002-s75", "competition-act-1998-s54"):
        if pk not in provs:
            sys.exit(f"FAIL: {pk} not fetched — run fetch_legislation.py (spine acts added).")
    store.upsert("powers", POWERS)
    print("--- competition-law spine ---")
    print(f"  + {len(POWERS)} cross-cutting powers (CMA s.109 investigation, CMA s.75 orders, "
          f"Ofwat s.54 concurrency)")
    print(f"  totals — powers {len(store.load('powers'))}")


if __name__ == "__main__":
    main()
