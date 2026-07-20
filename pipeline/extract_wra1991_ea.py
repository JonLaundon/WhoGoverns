#!/usr/bin/env python3
"""Cross-body batch: Water Resources Act 1991 — the Environment Agency's water powers.

The first holder beyond Ofwat/SoS, chosen because the EA is where the cross-body magic (and
collisions) surface. Two records, each carrying a documented cross-body relationship to Ofwat:
  - s.38  grant/refuse an ABSTRACTION LICENCE (s.24 makes abstraction unlawful without one).
          A `licence` power whose refusal is a hard block on supply -> a SELF-BLOCK veto
          (licence_refusal), the contrast to the SoS consent-gates. TENSION with Ofwat: this
          caps the supply Ofwat's resilience duty (WIA 1991 s.2(2A)(e)) presses undertakers to
          secure — Cunliffe's "regulators working against each other".
  - s.25A environmental ENFORCEMENT NOTICE. OVERLAP with Ofwat's s.18 enforcement: both bodies
          can act against the same water company on different statutory grounds.

    py -3 pipeline/extract_wra1991_ea.py            # write
    py -3 pipeline/extract_wra1991_ea.py --dry-run  # build + validate only
"""
import sys

import extract

RUN_ID = "run-2026-07-20-wra1991-ea-abstraction-enforcement"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
URL38 = "https://www.legislation.gov.uk/ukpga/1991/57/section/38"
URL25A = "https://www.legislation.gov.uk/ukpga/1991/57/section/25A"

UNITS = [
    {
        "record_id": "power-ea-wra1991-s38-abstraction-licence", "kind": "power", "holder": "ea",
        "label": "Grant or refuse an abstraction licence",
        "subtype": "licence", "legal_effect": "may",
        "summary": ("No person may abstract water from a source of supply except under a licence "
                    "granted by the Environment Agency (WRA 1991 s.24). On an application the "
                    "Agency may grant a licence on such terms as it considers appropriate, or — "
                    "where it considers it necessary or expedient having regard to the Chapter — "
                    "refuse to grant a licence (s.38(2)). The gate on all new or increased water "
                    "abstraction, including by water undertakers."),
        "source_id": "source-act-water-resources-act-1991",
        "provision_key": "water-resources-act-1991-s38", "provision_ref": "s.38(2)",
        "citation_url": URL38,
        "constraints": [
            "No abstraction is lawful without a licence (s.24) — the licence requirement is the "
            "source of the gate.",
            "In determining an application the Agency shall have regard to all relevant "
            "circumstances, other inland-waters bodies' duties, and written representations "
            "(s.38(3)).",
            "Drought orders/permits under Chapter III can override the abstraction restriction "
            "(s.24(1)).",
        ],
        "related_body_ids": [OFWAT],
        "provenance_note": ("CROSS-BODY TENSION: this EA abstraction gate caps the water supply "
                            "that Ofwat's resilience duty (WIA 1991 s.2(2A)(e)) presses undertakers "
                            "to secure — the Ofwat/EA conflict Cunliffe documented as regulators "
                            "'working against each other'. Discharge/pollution consents largely "
                            "moved to the Environmental Permitting Regs 2016 (later SI)."),
        "confidence": 0.85,
        "blocks": {
            "veto_type": "licence_refusal", "strength": "hard_stop",
            "veto_label": "Refusal of an abstraction licence (cap on supply)",
            "decision_affected": ("Whether a person (including a water undertaker) may lawfully "
                                  "abstract water — the cap on new or increased supply."),
            "overridable": "yes",
            "override_mechanism": "A drought order/permit under WRA 1991 Chapter III (s.24(1)).",
        },
    },
    {
        "record_id": "power-ea-wra1991-s25a-enforcement", "kind": "power", "holder": "ea",
        "label": "Serve an environmental enforcement notice (abstraction/impounding)",
        "subtype": "enforcement", "legal_effect": "may",
        "summary": ("Where it appears to the Environment Agency that a person is in breach of the "
                    "abstraction/impounding restrictions (WRA 1991 ss.24-25) or a licence "
                    "condition, and the breach is causing or likely to cause significant damage to "
                    "the environment (s.25A(2)), the Agency may serve an enforcement notice "
                    "requiring the person to cease the breach or comply, and to carry out remedial "
                    "works (s.25A(3))."),
        "source_id": "source-act-water-resources-act-1991",
        "provision_key": "water-resources-act-1991-s25a", "provision_ref": "s.25A",
        "citation_url": URL25A,
        "constraints": [
            "Threshold: the breach must be causing or likely to cause significant damage to the "
            "environment (s.25A(2)).",
        ],
        "related_body_ids": [OFWAT],
        "provenance_note": ("CROSS-BODY OVERLAP with Ofwat's enforcement power (WIA 1991 s.18): "
                            "both the EA and Ofwat can take enforcement action against the same "
                            "water company on different statutory grounds (EA: environmental damage "
                            "from abstraction; Ofwat: breach of appointment conditions/statutory "
                            "requirements) — the overlapping-enforcement pattern the Over Ruled and "
                            "Cunliffe reviews flag."),
        "confidence": 0.85,
    },
]


def main():
    dry = "--dry-run" in sys.argv
    extract.run(UNITS, RUN_ID, dry_run=dry)


if __name__ == "__main__":
    main()
