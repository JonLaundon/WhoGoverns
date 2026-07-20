#!/usr/bin/env python3
"""Retrodiction gap-closure: the fiscal and judicial layers of a water special administration.

Both gaps were surfaced by the 2026-07-20 retrodiction scrub. The FISCAL one was silent — the
water Acts' s.24 records never point to it; it took an external SAR study (discovery only, per
decision #24) to name the provision, re-sourced here to legislation.gov.uk:
  - s.153  the SoS may fund / indemnify / guarantee a company in special administration, WITH
           HM TREASURY CONSENT (the "quasi-nationalisation" lever) -> a Treasury consent-gate veto.
  - s.24(1) the HIGH COURT (Chancery Division) makes the special administration order (the
           s.24 petition records name "the High Court"; this extracts that decision step).

    py -3 pipeline/extract_wia1991_sar_gaps.py [--dry-run]
"""
import sys

import extract

RUN_ID = "run-2026-07-20-wia1991-sar-gaps-fiscal-judicial"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
TREASURY = "uk-state-body-hm-treasury"
SOS_OFFICE = "office-secretary-of-state-for-environment-food-and-rural-affairs"
DEFRA = "uk-state-body-department-for-environment-food-rural-affairs"
URL153 = "https://www.legislation.gov.uk/ukpga/1991/56/section/153"
URL24 = "https://www.legislation.gov.uk/ukpga/1991/56/section/24"

PROVISIONS = [
    extract.paragraph_provision("water-industry-act-1991-s24-1-order", "s.24(1)", URL24,
                                "instrument-act-water-industry-act-1991", "2026-07-20"),
]

UNITS = [
    {
        "record_id": "power-sos-defra-wia1991-s153-funding", "kind": "power", "holder": "sos-defra",
        "label": "Fund / indemnify / guarantee a company in special administration (Treasury consent)",
        "subtype": "funding", "legal_effect": "conditional",
        "summary": ("Where a special administration order is in force, the Secretary of State may, "
                    "WITH THE CONSENT OF THE TREASURY, make grants or loans to the company, offer "
                    "indemnities to the special administrator and others, and guarantee the "
                    "company's borrowing (WIA 1991 s.153(1)-(2)). The quasi-nationalisation funding "
                    "lever — the fiscal engine of a water SAR."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s153", "provision_ref": "s.153(1)",
        "citation_url": URL153,
        "related_body_ids": [OFWAT, TREASURY],
        "provenance_note": ("FISCAL GAP CLOSED (retrodiction 2026-07-20): the Treasury-funding "
                            "blocker the model could NOT self-surface — the s.24 records never point "
                            "to it. Named by an external SAR study (Octus briefing; discovery only, "
                            "re-sourced here to legislation.gov.uk per #24). Gated by Treasury "
                            "consent, so a SAR's fiscal viability sits with HM Treasury."),
        "confidence": 0.9,
        "blocks": {
            "holder": "hm-treasury", "veto_id": "veto-hm-treasury-wia1991-s153",
            "veto_type": "consent_required", "strength": "hard_stop",
            "veto_label": "HM Treasury consent to government funding of a water special administration",
            "decision_affected": ("Whether the Secretary of State may fund, indemnify or guarantee "
                                  "a water company in special administration — the fiscal viability "
                                  "of the SAR."),
            "blocks_holder_type": "office", "blocks_office_id": SOS_OFFICE, "blocks_body_id": DEFRA,
            "blocks_provision_key": "water-industry-act-1991-s153", "overridable": "no",
        },
    },
    {
        "record_id": "power-chancery-court-wia1991-s24-1-order", "kind": "power",
        "holder": "chancery-court",
        "label": "Make a special administration order", "subtype": "other", "legal_effect": "may",
        "summary": ("On a petition by the Secretary of State or Ofwat, if satisfied that one or more "
                    "of the s.24(2) grounds is met (serious breach of a principal duty; inability to "
                    "pay debts; etc.), the High Court may make a special administration order in "
                    "relation to a water company (WIA 1991 s.24(1)). The Court is the adjudicator — "
                    "it can refuse if the grounds are not met — but on the public-interest question "
                    "it defers to the SoS and Ofwat as 'the guardians of the public interest'."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s24-1-order", "provision_ref": "s.24(1)",
        "citation_url": URL24,
        "related_body_ids": [OFWAT],
        "related_power_ids": ["power-sos-defra-wia1991-s24-1-a", "power-ofwat-wia1991-s24-1-b"],
        "provenance_note": ("JUDICIAL GAP CLOSED (retrodiction): the s.24 petition records name "
                            "'the High Court' as the decision-maker; this extracts that step. Holder "
                            "= Chancery Division (company/insolvency work). Modelled as a power "
                            "(adjudication on the grounds), NOT a veto — the Court defers to SoS/"
                            "Ofwat on the public interest (Court of Appeal, Thames Water)."),
        "confidence": 0.85,
    },
]


def main():
    extract.run(UNITS, RUN_ID, provisions=PROVISIONS, dry_run="--dry-run" in sys.argv)


if __name__ == "__main__":
    main()
