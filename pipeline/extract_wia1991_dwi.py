#!/usr/bin/env python3
"""DWI batch: WIA 1991 drinking-water-quality enforcement — held by the Defra office.

Per sponsor decision (2026-07-20): the Drinking Water Inspectorate is NOT a separate body
node. s.86 shows why — its inspectors are appointed to act "on [the Secretary of State's]
behalf" exercising HIS water-quality powers (ss.67-70). So the power is held by the Defra
office (SoS), tagged to the DWI / Chief Inspector function — a "micro-department" partition
within Defra, not a spurious node. (If finer fidelity is wanted later, the Chief Inspector of
Drinking Water is itself a statutory OFFICE under s.86(1A) and could become an Office node —
the reference is already in the record.)

    py -3 pipeline/extract_wia1991_dwi.py [--dry-run]
"""
import sys

import extract

RUN_ID = "run-2026-07-20-wia1991-dwi-quality"
OFWAT = "uk-state-body-the-water-services-regulation-authority"

UNITS = [
    {
        "record_id": "power-sos-defra-wia1991-s70-dwi-quality-enforcement", "kind": "power",
        "holder": "sos-defra",
        "label": "Enforce drinking water quality (via the Drinking Water Inspectorate)",
        "subtype": "enforcement", "legal_effect": "may",
        "summary": ("Supplying water unfit for human consumption is an offence by the water "
                    "undertaker (WIA 1991 s.70). The Secretary of State enforces drinking-water "
                    "quality and sufficiency standards (ss.67-70, 77-82); proceedings for the s.70 "
                    "offence may be instituted only by the Secretary of State or the DPP (s.70(3)). "
                    "These functions are exercised on the Secretary of State's behalf by appointed "
                    "inspectors — the Drinking Water Inspectorate, led by the Chief Inspector of "
                    "Drinking Water (s.86) — a unit within Defra, not a separate body."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s70", "provision_ref": "s.70",
        "citation_url": "https://www.legislation.gov.uk/ukpga/1991/56/section/70",
        "constraints": [
            "Proceedings for the s.70 offence may be instituted only by the Secretary of State or "
            "the DPP (s.70(3)).",
            "Quality standards themselves are set by regulations under s.67.",
        ],
        "related_body_ids": [OFWAT],
        "provenance_note": ("DWI MODELLING (sponsor, 2026-07-20): the Drinking Water Inspectorate "
                            "has no separate legal personality — s.86 inspectors act 'on [the "
                            "Secretary of State's] behalf'. Its powers are held by the Defra office "
                            "(SoS), tagged to the DWI / Chief Inspector function (a micro-department "
                            "partition within Defra). The Chief Inspector is itself a statutory "
                            "office (s.86(1A)) and could be promoted to an Office node if finer "
                            "fidelity is wanted — the reference is already here."),
        "confidence": 0.85,
    },
]


def main():
    extract.run(UNITS, RUN_ID, dry_run="--dry-run" in sys.argv)


if __name__ == "__main__":
    main()
