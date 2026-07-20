#!/usr/bin/env python3
"""Cross-body batch: the CMA veto over Ofwat (WIA s.16A) and CCW as a consumer voice (s.27C).

- CMA (s.16A): the statute's OWN word is a "power of veto" — following its report on a
  modification reference, the CMA may direct Ofwat not to make some/all proposed licence
  modifications (including price controls), and Ofwat must comply. A self-block veto whose
  power is a direction (blocks.self_block bypasses the blocking-family heuristic), with the
  block target set to Ofwat's modification. The appellate check that sits ABOVE Ofwat.
- CCW (s.27C): the honest boundary case. CCW represents consumers and must have regard to
  vulnerable groups, but its external leverage is INFLUENCE (representations to Ofwat and
  undertakers) — no veto, no power to compel. One duty recorded; deliberately veto-less.

    py -3 pipeline/extract_wia1991_cma_ccw.py [--dry-run]
"""
import sys

import extract

RUN_ID = "run-2026-07-20-wia1991-cma-ccw"
OFWAT = "uk-state-body-the-water-services-regulation-authority"

UNITS = [
    {
        "record_id": "power-cma-wia1991-s16a-veto", "kind": "power", "holder": "cma",
        "label": "Veto Ofwat's licence modifications following a CMA report",
        "subtype": "direction", "legal_effect": "may",
        "summary": ("Following its report on a modification reference, the CMA may (within four "
                    "weeks) direct Ofwat not to make some or all of the proposed licence/appointment "
                    "modifications, and Ofwat must comply (WIA 1991 s.16A(1)). The direction may "
                    "only cover modifications that are not requisite to remedy the adverse effects "
                    "identified in the report (s.16A(3)). The statute's own term is a 'power of "
                    "veto'."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s16a", "provision_ref": "s.16A(1)",
        "citation_url": "https://www.legislation.gov.uk/ukpga/1991/56/section/16A",
        "related_body_ids": [OFWAT],
        "related_power_ids": ["power-ofwat-wia1991-s14"],
        "provenance_note": ("CROSS-BODY VETO: the CMA can override Ofwat's licence-modification "
                            "(including price-control) decisions — the appellate check above Ofwat, "
                            "reached via Ofwat's s.14 reference power. The statute names it a 'power "
                            "of veto' (s.16A)."),
        "confidence": 0.9,
        "blocks": {
            "self_block": True, "veto_type": "other", "strength": "hard_stop",
            "veto_label": "CMA veto of Ofwat's proposed licence modifications",
            "decision_affected": ("Whether Ofwat's proposed modifications to a water company's "
                                  "licence/appointment conditions (including price controls) take "
                                  "effect."),
            "blocks_holder_type": "body", "blocks_body_id": OFWAT,
            "blocks_provision_key": "water-industry-act-1991-s14",
            "overridable": "no",
        },
    },
    {
        "record_id": "duty-ccw-wia1991-s27c-consumer-interests", "kind": "duty", "holder": "ccw",
        "label": "Represent consumer interests, with regard to vulnerable groups",
        "subtype": "other", "mandatory": True,
        "summary": ("In considering the interests of consumers, the Consumer Council for Water "
                    "shall have regard in particular to the interests of the disabled or chronically "
                    "sick, people of pensionable age, those on low incomes, rural residents, and "
                    "household customers (WIA 1991 s.27C). CCW's role is to represent and safeguard "
                    "water consumers' interests."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s27c", "provision_ref": "s.27C(1)",
        "citation_url": "https://www.legislation.gov.uk/ukpga/1991/56/section/27C",
        "related_body_ids": [OFWAT],
        "provenance_note": ("INFLUENCE BOUNDARY: CCW's external leverage is INFLUENCE — it "
                            "investigates complaints and makes representations to Ofwat and "
                            "undertakers, but holds NO veto and no power to compel. Per the strict "
                            "test its representation/consultation rights are influence, not recorded "
                            "as vetoes. CCW is the consumer-voice node, deliberately veto-less — an "
                            "honest outcome, not a gap."),
        "confidence": 0.8,
    },
]


def main():
    extract.run(UNITS, RUN_ID, dry_run="--dry-run" in sys.argv)


if __name__ == "__main__":
    main()
