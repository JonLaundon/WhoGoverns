#!/usr/bin/env python3
"""Enrichment batch: WIA 1991 s.2 (Ofwat's general/primary duty) + Water Act 2014 provenance.

The calibration slice already captured the s.2 general duty (duty-ofwat-wia1991-s2). This
Water Act 2014 scale-up step does NOT add a twin (A2.5: one canonical record per provision);
it re-processes s.2 through the reusable extract.py core to (a) sharpen the summary to the
five limbs of s.2(2A), and (b) attach the amend-provenance: limb (e) (the resilience
objective) and its s.2(2DA) definition were inserted by Water Act 2014 s.22 — recorded as
provenance on the WIA 1991 record, NOT re-minted as a separate Water Act 2014 power. The
upsert enriches the existing record in place, preserving its trigger / beneficiary /
failure-consequence fields.

    py -3 pipeline/extract_wia1991_s2.py            # write (enrich in place)
    py -3 pipeline/extract_wia1991_s2.py --dry-run  # build + validate only
"""
import sys

import extract

RUN_ID = "run-2026-07-15-wia1991-s2-wateract2014-provenance"

UNITS = [
    {
        "record_id": "duty-ofwat-wia1991-s2",
        "kind": "duty", "holder": "ofwat",
        "label": "General duties in regulating the water industry",
        "subtype": "other", "mandatory": True,
        "summary": (
            "In exercising and performing its water-industry powers and duties, Ofwat must act in "
            "the manner it considers best calculated to further: (a) the consumer objective; (b) the "
            "proper carrying-out of water and sewerage undertakers' functions across England and "
            "Wales; (c) securing that appointed companies can (in particular by reasonable returns on "
            "capital) finance the proper carrying-out of those functions; (d) the proper carrying-out "
            "of licensees' authorised activities; and (e) the resilience objective. The overarching "
            "duty that conditions how EVERY Ofwat power is exercised — the financeability limb (c) is "
            "the statutory hook behind price-review and bill decisions."
        ),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s2",
        "provision_ref": "s.2(2A)",
        "citation_url": "https://www.legislation.gov.uk/ukpga/1991/56/section/2",
        "trigger": "Whenever Ofwat exercises its functions under the Act.",
        "beneficiary_or_object": "Consumers; the water/sewerage sector.",
        "failure_consequence": "judicial_review_risk",
        "related_body_ids": ["uk-state-body-department-for-environment-food-rural-affairs"],
        "provenance_note": (
            "s.2 is long and multi-limbed; captured as one general-duties record (candidate for "
            "splitting per limb later). Co-held by the Secretary of State (s.2(1)); modelled here on "
            "the primary operative holder (Ofwat) per the calibration convention — full multi-holder "
            "modelling deferred (known issue). Limb (e) 'the resilience objective' and its s.2(2DA) "
            "definition were inserted by Water Act 2014 s.22 (instrument-act-water-act-2014 / "
            "provision water-act-2014-s22): amend-provenance, not a separate Water Act 2014 power."
        ),
        "confidence": 0.9,
    },
]


def main():
    dry = "--dry-run" in sys.argv
    extract.run(UNITS, RUN_ID, dry_run=dry)


if __name__ == "__main__":
    main()
