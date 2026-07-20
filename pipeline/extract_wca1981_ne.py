#!/usr/bin/env python3
"""Cross-body batch: Wildlife and Countryside Act 1981 — Natural England's SSSI gates.

The "left field" blocker: Natural England can veto water infrastructure (reservoirs,
abstraction works) affecting a protected site, under an Act with nothing to do with the water
industry. Two NE self-block consent/approval vetoes (veto holder = power holder):
  - s.28H assent gate over a public body's / statutory undertaker's damaging operations (the
    water-undertaker route — reservoirs, abstraction works)
  - s.28E consent gate over an owner/occupier's damaging operations on SSSI land (general)

For European sites (SAC/SPA) the sharper gate is the assimilated Conservation of Habitats and
Species Regs 2017 — flagged in fetch_legislation, not yet extracted.

    py -3 pipeline/extract_wca1981_ne.py            # write
    py -3 pipeline/extract_wca1981_ne.py --dry-run  # build + validate only
"""
import sys

import extract

RUN_ID = "run-2026-07-20-wca1981-ne-sssi-gates"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
EA = "uk-state-body-environment-agency"
URL28E = "https://www.legislation.gov.uk/ukpga/1981/69/section/28E"
URL28H = "https://www.legislation.gov.uk/ukpga/1981/69/section/28H"

UNITS = [
    {
        "record_id": "power-natural-england-wca1981-s28h-assent", "kind": "power",
        "holder": "natural-england",
        "label": "Assent to (or refuse) a public body's operations affecting an SSSI",
        "subtype": "approval", "legal_effect": "may",
        "summary": ("A 'section 28G authority' (a public body, including a water or sewerage "
                    "undertaker) must give Natural England notice before carrying out operations "
                    "likely to damage an SSSI, even off-site (WCA 1981 s.28H(1)-(2)). Natural "
                    "England may refuse assent, or assent with or without conditions (s.28H(3)); "
                    "silence for 28 days is treated as a refusal. The gate on undertaker "
                    "infrastructure — reservoirs, abstraction works — affecting protected sites."),
        "source_id": "source-act-wildlife-and-countryside-act-1981",
        "provision_key": "wildlife-and-countryside-act-1981-s28h", "provision_ref": "s.28H(3)",
        "citation_url": URL28H,
        "related_body_ids": [OFWAT, EA],
        "provenance_note": ("CROSS-BODY / LEFT-FIELD BLOCKER: Natural England's SSSI assent gates "
                            "the very water infrastructure (reservoirs, abstraction works) that "
                            "Ofwat's resilience duty and the EA's abstraction regime bear on — a "
                            "veto from an entirely different Act (WCA 1981), invisible to any "
                            "water-Act-only scrub. For European sites the sharper gate is the "
                            "assimilated Conservation of Habitats and Species Regs 2017."),
        "confidence": 0.85,
        "blocks": {
            "veto_type": "approval_required", "strength": "hard_stop",
            "veto_label": "Refusal of SSSI assent to a public body's operations",
            "decision_affected": ("Whether a public body (e.g. a water undertaker) may carry out "
                                  "operations likely to damage an SSSI — the gate on reservoirs / "
                                  "abstraction works affecting protected sites."),
            "trigger": "Notice of proposed damaging operations under s.28H(1).",
            "overridable": "unknown",
        },
    },
    {
        "record_id": "power-natural-england-wca1981-s28e-consent", "kind": "power",
        "holder": "natural-england",
        "label": "Consent to (or withhold consent from) damaging operations on an SSSI",
        "subtype": "consent", "legal_effect": "may",
        "summary": ("An owner or occupier of SSSI land may not carry out a notified "
                    "potentially-damaging operation unless Natural England has given written "
                    "consent (WCA 1981 s.28E(1),(3)(a)), or the operation is under a management "
                    "agreement/scheme. The general SSSI consent gate."),
        "source_id": "source-act-wildlife-and-countryside-act-1981",
        "provision_key": "wildlife-and-countryside-act-1981-s28e", "provision_ref": "s.28E(3)(a)",
        "citation_url": URL28E,
        "constraints": [
            "Does not apply to a s.28G authority (e.g. a water undertaker) acting in its "
            "functions — they use the s.28H assent route (s.28E(2)).",
            "Consent is one route; a management agreement (s.16 1949 Act / s.7 NERC Act) is an "
            "alternative (s.28E(3)(b)).",
        ],
        "confidence": 0.85,
        "blocks": {
            "veto_type": "consent_required", "strength": "hard_stop",
            "veto_label": "Withholding of SSSI consent to an owner/occupier's operations",
            "decision_affected": ("Whether an owner/occupier may carry out a potentially-damaging "
                                  "operation on SSSI land."),
            "overridable": "unknown",
        },
    },
]


def main():
    dry = "--dry-run" in sys.argv
    extract.run(UNITS, RUN_ID, dry_run=dry)


if __name__ == "__main__":
    main()
