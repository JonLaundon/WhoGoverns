#!/usr/bin/env python3
"""Bloom the Gas Act 1965 sibling — the gas-storage consent-order regime (planning writ large).

Reached from Planning Act s.120 (a DCO can subsume a Gas Act order). Another `consent_order`
sibling, tangential to a reservoir but IN the infrastructure-consenting fabric — bloomed to
its core order power, not pruned.

    py -3 pipeline/extract_gas_sibling.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

DESNZ = "uk-state-body-department-for-energy-security-and-net-zero"

POWER = {
    "power_id": "power-sos-energy-gas1965-s4", "holder_type": "body", "body_id": DESNZ,
    "office_id": None, "power_label": "Make a gas-storage authorisation order",
    "power_type": "consent_order", "power_basis": "statutory", "modality": "power",
    "legal_effect": "may",
    "summary": ("The Minister may make a storage authorisation order authorising a public gas "
                "transporter to store gas in underground porous strata, having regard to public "
                "safety and the protection of water resources (Gas Act 1965 s.4). A "
                "consent-order sibling of the DCO/TWA/harbour orders, reached from Planning Act "
                "s.120."),
    "constraints": ["Subject to the Act's provisions; regard to safety and water protection."],
    "source_id": "source-act-gas-act-1965", "provision_key": "gas-act-1965-s4",
    "citation": {"provision": "s.4(1)", "url": "https://www.legislation.gov.uk/ukpga/1965/36/section/4", "quote": None},
    "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
    "legal_status": "current",
    "extraction": {"confidence": 0.84, "extracted_by": "llm",
                   "extraction_run_id": "run-2026-07-21-gas-sibling", "requires_review": True},
    "verification": {"verification_status": "unverified", "verified_by": None,
                     "verified_date": None, "verification_notes": None},
    "notes": "HOLDER-RESOLUTION: 'the Minister' is the SoS for Energy Security and Net Zero; "
             "recorded on the DESNZ body (no clean energy-SoS office node yet), like the s.124A "
             "Business-SoS case. A candidate office when the energy tranche is built.",
    "record_status": "extracted",
}


def main():
    if "gas-act-1965-s4" not in {p["provision_key"] for p in store.load("provisions")}:
        sys.exit("FAIL: gas-act-1965-s4 not fetched.")
    store.upsert("powers", [POWER])
    print("--- gas sibling ---")
    print(f"  + 1 consent_order (Gas Act 1965 s.4); totals powers {len(store.load('powers'))}")


if __name__ == "__main__":
    main()
