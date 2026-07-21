#!/usr/bin/env python3
"""Bloom round — Electricity Act 1989 s.36 (energy sibling consent). Planning writ large.

Reached from Planning Act s.120: the consent to construct a generating station (Electricity
Act 1989 s.36) — the pre-DCO route, now used for sub-NSIP stations. Another infrastructure
consent in the fabric.

    py -3 pipeline/extract_electricity_sibling.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

DESNZ = "uk-state-body-department-for-energy-security-and-net-zero"

POWER = {
    "power_id": "power-sos-energy-electricity1989-s36", "holder_type": "body", "body_id": DESNZ,
    "office_id": None, "power_label": "Consent to the construction of a generating station",
    "power_type": "consent", "power_basis": "statutory", "modality": "power", "legal_effect": "may",
    "summary": ("A generating station may not be constructed, extended or operated except with "
                "the consent of the Secretary of State (Electricity Act 1989 s.36). The energy "
                "infrastructure consent — the pre-DCO route, now used for stations below the NSIP "
                "threshold; a sibling of the DCO in the consenting fabric."),
    "constraints": ["Subject to the exceptions in s.36(1A)-(2), (4)."],
    "source_id": "source-act-electricity-act-1989", "provision_key": "electricity-act-1989-s36",
    "citation": {"provision": "s.36(1)", "url": "https://www.legislation.gov.uk/ukpga/1989/29/section/36", "quote": None},
    "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
    "legal_status": "current",
    "extraction": {"confidence": 0.85, "extracted_by": "llm",
                   "extraction_run_id": "run-2026-07-21-electricity-sibling", "requires_review": True},
    "verification": {"verification_status": "unverified", "verified_by": None,
                     "verified_date": None, "verification_notes": None},
    "notes": "HOLDER-RESOLUTION: the SoS for Energy Security and Net Zero; recorded on the DESNZ "
             "body (no clean energy-SoS office yet), like the gas and s.124A cases.",
    "record_status": "extracted",
}

POWER_37 = {
    "power_id": "power-sos-energy-electricity1989-s37", "holder_type": "body", "body_id": DESNZ,
    "office_id": None, "power_label": "Consent to overhead electric lines",
    "power_type": "consent", "power_basis": "statutory", "modality": "power", "legal_effect": "may",
    "summary": ("An overhead electric line may not be installed or kept installed except with the "
                "consent of the appropriate authority (Electricity Act 1989 s.37). The overhead-"
                "lines consent — the routine energy-infrastructure gate, alongside the s.36 "
                "generating-station consent."),
    "constraints": ["Subject to the exceptions in s.37(1A)-(2A)."],
    "source_id": "source-act-electricity-act-1989", "provision_key": "electricity-act-1989-s37",
    "citation": {"provision": "s.37(1)", "url": "https://www.legislation.gov.uk/ukpga/1989/29/section/37", "quote": None},
    "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
    "legal_status": "current",
    "extraction": {"confidence": 0.85, "extracted_by": "llm",
                   "extraction_run_id": "run-2026-07-21-electricity-sibling", "requires_review": True},
    "verification": {"verification_status": "unverified", "verified_by": None,
                     "verified_date": None, "verification_notes": None},
    "notes": "HOLDER-RESOLUTION as s.36 (DESNZ body).", "record_status": "extracted",
}


def main():
    have = {p["provision_key"] for p in store.load("provisions")}
    for pk in ("electricity-act-1989-s36", "electricity-act-1989-s37"):
        if pk not in have:
            sys.exit(f"FAIL: {pk} not fetched.")
    store.upsert("powers", [POWER, POWER_37])
    print("--- electricity sibling ---")
    print(f"  + 2 consents (Electricity Act 1989 s.36, s.37); totals powers {len(store.load('powers'))}")


if __name__ == "__main__":
    main()
