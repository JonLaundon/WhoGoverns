#!/usr/bin/env python3
"""EA round-out: WRA 1991 drought powers (s.73, s.79A).

Closes the abstraction-override loop: both powers relax the s.24 abstraction restriction that
the EA abstraction veto (veto-ea-wra1991-s38-abstraction-licence) cites as its override.
Cross-actor: the EA/undertaker applies, the SoS makes a s.73 drought order; the EA itself
issues the lighter-touch s.79A drought permit.

    py -3 pipeline/extract_wra1991_ea_drought.py [--dry-run]
"""
import sys

import extract

RUN_ID = "run-2026-07-20-wra1991-drought"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
EA = "uk-state-body-environment-agency"
URL73 = "https://www.legislation.gov.uk/ukpga/1991/57/section/73"
URL79A = "https://www.legislation.gov.uk/ukpga/1991/57/section/79A"

UNITS = [
    {
        "record_id": "power-sos-defra-wra1991-s73-drought-order", "kind": "power",
        "holder": "sos-defra",
        "label": "Make an ordinary or emergency drought order", "subtype": "other",
        "legal_effect": "may",
        "summary": ("If satisfied that an exceptional shortage of rain has caused or threatens a "
                    "serious deficiency of water supplies (or a serious threat to flora/fauna "
                    "dependent on inland waters), the Secretary of State may make an ordinary "
                    "drought order — or, where the deficiency is likely to impair economic or "
                    "social well-being, an emergency drought order (s.73(1)-(2)) — authorising "
                    "measures, including relaxing abstraction restrictions, to meet the deficiency."),
        "source_id": "source-act-water-resources-act-1991",
        "provision_key": "water-resources-act-1991-s73", "provision_ref": "s.73(1)",
        "citation_url": URL73,
        "constraints": [
            "Made on the application of the Environment Agency or a water undertaker (Chapter III).",
            "Overrides normal abstraction restrictions (s.24(1)) for its duration.",
        ],
        "related_body_ids": [EA, OFWAT],
        "provenance_note": ("BREADCRUMB: Chapter III drought orders override the s.24 abstraction "
                            "restriction — the override_mechanism cited on the EA abstraction veto "
                            "(veto-ea-wra1991-s38-abstraction-licence). Cross-actor: EA/undertaker "
                            "applies, SoS makes the order."),
        "confidence": 0.85,
    },
    {
        "record_id": "power-ea-wra1991-s79a-drought-permit", "kind": "power", "holder": "ea",
        "label": "Issue a drought permit", "subtype": "licence", "legal_effect": "may",
        "summary": ("If satisfied that an exceptional shortage of rain has caused or threatens a "
                    "serious deficiency of supplies in an area, the Environment Agency may, on the "
                    "application of a water undertaker supplying that area, issue a drought permit "
                    "authorising the undertaker to take water from a source (relaxing normal "
                    "abstraction limits for the emergency) (s.79A(1)-(2))."),
        "source_id": "source-act-water-resources-act-1991",
        "provision_key": "water-resources-act-1991-s79a", "provision_ref": "s.79A(1)",
        "citation_url": URL79A,
        "constraints": [
            "A lighter-touch alternative to a s.73 drought order (Agency-issued, not SoS-made).",
            "Relaxes the s.24 abstraction restriction for the emergency.",
        ],
        "related_body_ids": [OFWAT],
        "provenance_note": ("Enabling emergency relief, NOT a gate — modelled as a power with no "
                            "veto: refusal maintains the normal abstraction limit rather than "
                            "blocking a distinct decision (veto-attribution discipline)."),
        "confidence": 0.85,
    },
]


def main():
    extract.run(UNITS, RUN_ID, dry_run="--dry-run" in sys.argv)


if __name__ == "__main__":
    main()
