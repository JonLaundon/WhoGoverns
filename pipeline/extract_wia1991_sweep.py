#!/usr/bin/env python3
"""Section-sweep batch: WIA 1991 ss.6, 7, 203 — Ofwat/SoS appointment, termination and
information powers, run through the reusable extract.py core.

This is the renationalisation-relevant core of who controls whether a private company runs
water, and who can block a change of control:
  - s.6   appointment of a relevant undertaker (SoS direct; Ofwat with SoS consent)
  - s.7   continuity duty (SoS) + termination/variation of an appointment (SoS; Ofwat gated)
  - s.203 power to require information/documents for enforcement

Two consent-gate vetoes are DERIVED here (the SoS's consent over Ofwat's gated powers) —
the same shape as the s.24 special-administration gate. Paragraph-level provision_keys are
used where a section confers independent powers on more than one holder (A2.5), consistent
with the s.24 calibration.

    py -3 pipeline/extract_wia1991_sweep.py            # write
    py -3 pipeline/extract_wia1991_sweep.py --dry-run  # build + validate only
"""
import sys

import extract

RUN_ID = "run-2026-07-15-wia1991-sweep-appointments-info"
URL6 = "https://www.legislation.gov.uk/ukpga/1991/56/section/6"
URL7 = "https://www.legislation.gov.uk/ukpga/1991/56/section/7"
URL203 = "https://www.legislation.gov.uk/ukpga/1991/56/section/203"
SOS_GEN_AUTH = ("A general authorisation given by the Secretary of State (pre-clears Ofwat to "
                "act without case-by-case consent).")

UNITS = [
    # --- s.6 Appointment of relevant undertakers ---
    {
        "record_id": "power-sos-defra-wia1991-s6-1-a", "kind": "power", "holder": "sos-defra",
        "label": "Appoint a company as water or sewerage undertaker",
        "subtype": "appointment", "legal_effect": "may",
        "summary": ("The Secretary of State may appoint a company to be the water undertaker or "
                    "sewerage undertaker for any area of England and Wales (s.6(1)(a)), by written "
                    "instrument served on the company (s.6(3))."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s6-1-a", "provision_ref": "s.6(1)(a)",
        "citation_url": URL6,
        "constraints": ["Appointee must be a limited company (s.6(5)) and not a water/sewerage "
                        "licensee (s.6(5A))."],
        "confidence": 0.9,
    },
    {
        "record_id": "power-ofwat-wia1991-s6-1-b", "kind": "power", "holder": "ofwat",
        "label": "Appoint a company as undertaker (with SoS consent/authorisation)",
        "subtype": "appointment", "legal_effect": "conditional",
        "summary": ("Ofwat may appoint a company to be the water or sewerage undertaker for an "
                    "area, but only with the consent of, or in accordance with a general "
                    "authorisation given by, the Secretary of State (s.6(1)(b))."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s6-1-b", "provision_ref": "s.6(1)(b)",
        "citation_url": URL6,
        "related_power_ids": ["power-sos-defra-wia1991-s6-1-a"],
        "confidence": 0.9,
        "blocks": {
            "holder": "sos-defra", "veto_id": "veto-sos-defra-wia1991-s6-1-b",
            "veto_type": "consent_required", "strength": "hard_stop",
            "veto_label": "Consent/authorisation gate over Ofwat's appointment of undertakers",
            "decision_affected": "Whether Ofwat may appoint a company as a water/sewerage undertaker.",
            "overridable": "yes", "override_mechanism": SOS_GEN_AUTH,
        },
    },
    # --- s.7 Continuity / replacement / termination of appointments ---
    {
        "record_id": "duty-sos-defra-wia1991-s7-1", "kind": "duty", "holder": "sos-defra",
        "label": "Secure continuity of water and sewerage undertakers for every area",
        "subtype": "other", "mandatory": True,
        "summary": ("It is the duty of the Secretary of State to secure that appointments are made "
                    "so that for every area of England and Wales there is at all times both a water "
                    "undertaker and a sewerage undertaker (s.7(1)). The continuity-of-supply backstop "
                    "that constrains how an undertaker can be removed or replaced."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s7-1", "provision_ref": "s.7(1)",
        "citation_url": URL7,
        "trigger": "At all times — a continuing duty.",
        "beneficiary_or_object": "Consumers in every area; continuity of water/sewerage service.",
        "failure_consequence": "judicial_review_risk",
        "confidence": 0.9,
    },
    {
        "record_id": "power-sos-defra-wia1991-s7-2-a", "kind": "power", "holder": "sos-defra",
        "label": "Terminate or vary an undertaker's appointment",
        "subtype": "other", "legal_effect": "may",
        "summary": ("The Secretary of State may, by notice to a company holding an appointment, "
                    "terminate the appointment or vary the area to which it relates (s.7(2)(a)). The "
                    "direct lever for removing/replacing a private undertaker — central to any "
                    "renationalisation route short of special administration (s.24)."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s7-2-a", "provision_ref": "s.7(2)(a)",
        "citation_url": URL7,
        "constraints": [
            "Termination takes effect only from the coming into force of a replacement "
            "appointment (s.7(3)).",
            "A replacement generally requires the incumbent company's consent (s.7(4)(a)) unless "
            "the s.7(4)(b)-(c)/(5) conditions apply — a PRIVATE-party consent, not a state veto.",
        ],
        "confidence": 0.85,
    },
    {
        "record_id": "power-ofwat-wia1991-s7-2-b", "kind": "power", "holder": "ofwat",
        "label": "Terminate or vary an undertaker's appointment (with SoS consent/authorisation)",
        "subtype": "other", "legal_effect": "conditional",
        "summary": ("Ofwat may, by notice, terminate an undertaker's appointment or vary its area, "
                    "but only with the consent of, or under a general authorisation given by, the "
                    "Secretary of State (s.7(2)(b)); subject to the same replacement/consent "
                    "conditions as the SoS power."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s7-2-b", "provision_ref": "s.7(2)(b)",
        "citation_url": URL7,
        "related_power_ids": ["power-sos-defra-wia1991-s7-2-a"],
        "confidence": 0.85,
        "blocks": {
            "holder": "sos-defra", "veto_id": "veto-sos-defra-wia1991-s7-2-b",
            "veto_type": "consent_required", "strength": "hard_stop",
            "veto_label": "Consent/authorisation gate over Ofwat's termination/variation of appointments",
            "decision_affected": "Whether Ofwat may terminate or vary an undertaker's appointment.",
            "overridable": "yes", "override_mechanism": SOS_GEN_AUTH,
        },
    },
    # --- s.203 Power to acquire information for enforcement purposes ---
    {
        "record_id": "power-ofwat-wia1991-s203", "kind": "power", "holder": "ofwat",
        "label": "Require information/documents for enforcement purposes",
        "subtype": "information_request", "legal_effect": "may",
        "summary": ("Ofwat may serve a notice requiring a relevant undertaker, a licensee, or any "
                    "person (for purposes connected with Chapter 2 of Part 2) to produce specified "
                    "documents or furnish specified information, where it is of the opinion the "
                    "enforcement conditions in s.203(1A)/(1B) are met (s.203(1),(2)). Non-compliance "
                    "is a summary offence (s.203(4)); the High Court may order the default made good "
                    "(s.203(6))."),
        "source_id": "source-act-water-industry-act-1991",
        "provision_key": "water-industry-act-1991-s203", "provision_ref": "s.203(2)",
        "citation_url": URL203,
        "constraints": [
            "No document compellable that could not be compelled in High Court civil proceedings "
            "(s.203(3)).",
        ],
        "provenance_note": ("Co-held by 'the Minister' — the Secretary of State for England, the "
                            "Welsh Ministers for Wales (s.203(8)); modelled here on Ofwat, "
                            "multi-holder deferred. Each regulator holding its own s.203-style "
                            "information power is the statutory root of the overlapping-reporting "
                            "burden documented in the Over Ruled water example (30+ reports to "
                            "Ofwat/Defra/EA)."),
        "confidence": 0.85,
    },
]


# Paragraph-level provision nodes for the sections that confer independent powers on more
# than one holder (A2.5), so the records' provision_keys resolve (s.24 calibration convention).
INSTRUMENT = "instrument-act-water-industry-act-1991"
VERSION_DATE = "2026-07-20"
PROVISIONS = [
    extract.paragraph_provision("water-industry-act-1991-s6-1-a", "s.6(1)(a)", URL6, INSTRUMENT, VERSION_DATE),
    extract.paragraph_provision("water-industry-act-1991-s6-1-b", "s.6(1)(b)", URL6, INSTRUMENT, VERSION_DATE),
    extract.paragraph_provision("water-industry-act-1991-s7-1", "s.7(1)", URL7, INSTRUMENT, VERSION_DATE),
    extract.paragraph_provision("water-industry-act-1991-s7-2-a", "s.7(2)(a)", URL7, INSTRUMENT, VERSION_DATE),
    extract.paragraph_provision("water-industry-act-1991-s7-2-b", "s.7(2)(b)", URL7, INSTRUMENT, VERSION_DATE),
]


def main():
    dry = "--dry-run" in sys.argv
    extract.run(UNITS, RUN_ID, provisions=PROVISIONS, dry_run=dry)


if __name__ == "__main__":
    main()
