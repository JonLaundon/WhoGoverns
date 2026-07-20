#!/usr/bin/env python3
"""Extract the WIA 1991 water supply / sewerage LICENSING regime (ss.17A+).

One job. This closes the gap the sponsor identified: Ofwat was showing 11 records and a
derived `regulation` function while its entire licensing power set was missing, because the
Water Act 2014 inserted that regime into WIA 1991 as ss.17A+ and we had never fetched them.
Declaring the body "complete" on that basis was a false assurance.

What the trawl found — two Secretary of State gates on Ofwat that the register did not hold:

  * s.17A(5) "The Authority may exercise the power to grant a water supply licence ONLY in
    accordance with a general authorisation given by the Secretary of State." Ofwat cannot
    licence at all without it. Same-holder rule applies (the authorisation is the Secretary of
    State's own act), so hard_stop / overridable no — consistent with ss.6(1)(b), 7(2)(b).
  * s.17J(5) "If ... the Secretary of State ... directs the Authority not to make any
    modification, the Authority SHALL comply with the direction."

...and two further consultation duties owed to the Welsh Ministers (s.17A(6), s.17J(5A)),
which are counterparty duties of exactly the kind U13 needs.

Re-runnable and idempotent.

    py -3 pipeline/extract_wia1991_licensing.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-20-wia1991-licensing-17a"
SRC = "source-act-water-industry-act-1991"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
DEFRA = "uk-state-body-department-for-environment-food-rural-affairs"
SOS = "office-secretary-of-state-for-environment-food-and-rural-affairs"
WELSH = "uk-state-body-welsh-government"


def cite(prov):
    return {"provision": prov, "quote": None,
            "url": "https://www.legislation.gov.uk/ukpga/1991/56/section/" + prov.split("(")[0].lstrip("s.")}


def extraction(conf):
    return {"confidence": conf, "extracted_by": "llm", "extraction_run_id": RUN,
            "requires_review": True}


VERIFY = {"verification_status": "unverified", "verified_by": None,
          "verified_date": None, "verification_notes": None}

POWERS = [
    {"power_id": "power-ofwat-wia1991-s17a", "holder_type": "body", "body_id": OFWAT,
     "office_id": None, "power_label": "Grant a water supply licence",
     "power_type": "licence", "power_basis": "statutory", "modality": "power",
     "legal_effect": "conditional",
     "summary": ("Ofwat may grant a person a licence to use the supply system of a water "
                 "undertaker (a water supply licence), giving retail, wholesale, restricted "
                 "retail and/or supplementary authorisations (WIA 1991 s.17A(1)-(2)). The "
                 "gateway to competition in the water market. Exercisable ONLY in accordance "
                 "with a general authorisation given by the Secretary of State (s.17A(5))."),
     "constraints": ["s.17A(5): exercisable only in accordance with a general authorisation "
                     "given by the Secretary of State — Ofwat cannot licence at all without one.",
                     "Authorisations operate as provided by Schedule 2A (s.17A(3))."],
     "source_id": SRC, "provision_key": "water-industry-act-1991-s17a",
     "citation": cite("s.17A(1)"), "related_body_ids": [DEFRA], "related_power_ids": [],
     "derived_from_record_id": None, "legal_status": "current",
     "extraction": extraction(0.93), "verification": dict(VERIFY), "notes": None,
     "record_status": "extracted"},

    {"power_id": "power-ofwat-wia1991-s17j", "holder_type": "body", "body_id": OFWAT,
     "office_id": None, "power_label": "Modify the standard conditions of water supply and sewerage licences",
     "power_type": "rulemaking", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("Ofwat may modify the standard conditions of water supply or sewerage "
                 "licences, and make incidental or consequential modifications to any licence "
                 "affected (WIA 1991 s.17J(1)-(2)). The sector-wide rule-change lever: it "
                 "reaches every licensee at once, unlike s.13 modification by agreement."),
     "constraints": ["s.17J(3): 28 days' notice and representations must be considered first.",
                     "s.17J(5): the Secretary of State may direct Ofwat not to modify, and "
                     "Ofwat shall comply.",
                     "s.17J(6): blocked where enough relevant licence holders object — by "
                     "number and by market share, against thresholds set by SI."],
     "source_id": SRC, "provision_key": "water-industry-act-1991-s17j",
     "citation": cite("s.17J(1)"), "related_body_ids": [DEFRA], "related_power_ids": [],
     "derived_from_record_id": None, "legal_status": "current",
     "extraction": extraction(0.93), "verification": dict(VERIFY), "notes": None,
     "record_status": "extracted"},
]

VETOES = [
    {"veto_id": "veto-sos-defra-wia1991-s17a-5", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "veto_label": "General authorisation required before Ofwat may licence",
     "veto_type": "consent_required", "modality": "veto", "strength": "hard_stop",
     "overridable": "no", "override_mechanism": None,
     "summary": ("Ofwat 'may exercise the power to grant a water supply licence only in "
                 "accordance with a general authorisation given by the Secretary of State' "
                 "(WIA 1991 s.17A(5)). Without one there is no licensing at all — the entry "
                 "gate to the competitive water market is held by the Secretary of State, "
                 "not the regulator."),
     "decision_affected": "Whether Ofwat may grant water supply licences at all.",
     "derived_from_record_id": "power-ofwat-wia1991-s17a",
     "blocks_holder_type": "body", "blocks_body_id": OFWAT, "blocks_office_id": None,
     "blocks_record_id": "power-ofwat-wia1991-s17a", "blocks_record_type": "power",
     "blocks_provision_key": "water-industry-act-1991-s17a",
     "source_id": SRC, "provision_key": "water-industry-act-1991-s17a-5",
     "citation": cite("s.17A(5)"), "legal_status": "current",
     "extraction": extraction(0.93), "verification": dict(VERIFY),
     "notes": ("Same-holder rule (vocab/veto_strength.json v0.2): the general authorisation is "
               "the Secretary of State's own act, so it is that holder consenting in class "
               "rather than a route around the consent — hard_stop, overridable no, as with "
               "ss.6(1)(b) and 7(2)(b)."),
     "record_status": "extracted"},

    {"veto_id": "veto-sos-defra-wia1991-s17j-5", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "veto_label": "Direction not to modify standard licence conditions",
     "veto_type": "other", "modality": "veto", "strength": "hard_stop",
     "overridable": "no", "override_mechanism": None,
     "summary": ("Within the notice period, the Secretary of State may direct Ofwat not to "
                 "make any modification of standard licence conditions, and 'the Authority "
                 "shall comply with the direction' (WIA 1991 s.17J(5)). A direct ministerial "
                 "stop on the regulator's sector-wide rule-change power."),
     "decision_affected": ("Whether Ofwat may modify the standard conditions of water supply "
                           "or sewerage licences."),
     "derived_from_record_id": "power-ofwat-wia1991-s17j",
     "blocks_holder_type": "body", "blocks_body_id": OFWAT, "blocks_office_id": None,
     "blocks_record_id": "power-ofwat-wia1991-s17j", "blocks_record_type": "power",
     "blocks_provision_key": "water-industry-act-1991-s17j",
     "source_id": SRC, "provision_key": "water-industry-act-1991-s17j-5",
     "citation": cite("s.17J(5)"), "legal_status": "current",
     "extraction": extraction(0.92), "verification": dict(VERIFY),
     "notes": ("veto_type 'other' with a note per the vocab rule: a bare power to direct "
               "another body NOT to act matches no existing term cleanly — it is not a consent "
               "(silence lets Ofwat proceed) and not an objection power. Recurs with WIA s.16A; "
               "two instances now, so a `direction_not_to_act` term is worth proposing."),
     "record_status": "extracted"},
]

DUTIES = [
    {"duty_id": "duty-sos-defra-wia1991-s17a-6-consult", "holder_type": "office",
     "office_id": SOS, "body_id": DEFRA,
     "duty_label": "Consult the Welsh Ministers before a general authorisation to licence",
     "duty_type": "consultation", "modality": "duty", "mandatory": True,
     "summary": ("Before giving a general authorisation as regards Ofwat, the Secretary of "
                 "State must consult the Welsh Ministers (WIA 1991 s.17A(6)) — the devolved "
                 "check on the gate that controls water-market entry."),
     "trigger": "Before giving a general authorisation to Ofwat under s.17A(5).",
     "beneficiary_or_object": "The Welsh Ministers (devolved interest).",
     "failure_consequence": "judicial_review_risk",
     "owed_to_holder_type": "body", "owed_to_body_id": WELSH, "owed_to_office_id": None,
     "source_id": SRC, "provision_key": "water-industry-act-1991-s17a-6",
     "citation": cite("s.17A(6)"), "related_body_ids": [WELSH],
     "derived_from_record_id": None, "in_force_from": None, "in_force_to": None,
     "legal_status": "current", "extraction": extraction(0.93),
     "verification": dict(VERIFY),
     "notes": ("Counterparty mapped to the Welsh Government body; statute names 'the Welsh "
               "Ministers', who are officeholders under the Government of Wales Act 2006 and "
               "have no office node yet."),
     "record_status": "extracted"},

    {"duty_id": "duty-sos-defra-wia1991-s17j-5a-consult", "holder_type": "office",
     "office_id": SOS, "body_id": DEFRA,
     "duty_label": "Consult the Welsh Ministers before directing Ofwat not to modify",
     "duty_type": "consultation", "modality": "duty", "mandatory": True,
     "summary": ("The Secretary of State is to consult the Welsh Ministers before giving a "
                 "direction under s.17J(5) in relation to a water supply licence (WIA 1991 "
                 "s.17J(5A))."),
     "trigger": "Before directing Ofwat not to modify standard conditions of a water supply licence.",
     "beneficiary_or_object": "The Welsh Ministers (devolved interest).",
     "failure_consequence": "judicial_review_risk",
     "owed_to_holder_type": "body", "owed_to_body_id": WELSH, "owed_to_office_id": None,
     "source_id": SRC, "provision_key": "water-industry-act-1991-s17j-5a",
     "citation": cite("s.17J(5A)"), "related_body_ids": [WELSH],
     "derived_from_record_id": None, "in_force_from": None, "in_force_to": None,
     "legal_status": "current", "extraction": extraction(0.92),
     "verification": dict(VERIFY), "notes": None, "record_status": "extracted"},

    {"duty_id": "duty-ofwat-wia1991-s17j-3-notice", "holder_type": "body", "body_id": OFWAT,
     "office_id": None,
     "duty_label": "Notice and representations before modifying standard conditions",
     "duty_type": "consultation", "modality": "duty", "mandatory": True,
     "summary": ("Before modifying standard licence conditions Ofwat must give notice setting "
                 "out the modifications, their effect and the reasons, allow at least 28 days "
                 "for representations or objections, and consider any duly made and not "
                 "withdrawn (WIA 1991 s.17J(3)). Notice is served on each relevant licence "
                 "holder, the Consumer Council for Water, the Secretary of State, the Welsh "
                 "Government and the Chief Inspector of Drinking Water (s.17J(4))."),
     "trigger": "Before making any modification of standard conditions under s.17J.",
     "beneficiary_or_object": ("Relevant licence holders (private companies), plus the bodies "
                               "served under s.17J(4)."),
     "failure_consequence": "judicial_review_risk",
     "owed_to_holder_type": None, "owed_to_body_id": None, "owed_to_office_id": None,
     "source_id": SRC, "provision_key": "water-industry-act-1991-s17j-3",
     "citation": cite("s.17J(3)"), "related_body_ids": [],
     "derived_from_record_id": None, "in_force_from": None, "in_force_to": None,
     "legal_status": "current", "extraction": extraction(0.9),
     "verification": dict(VERIFY),
     "notes": ("owed_to left null deliberately: the consultees are chiefly private licence "
               "holders, so no single state counterparty is named and no must_consult edge is "
               "drawn. The s.17J(4) service list is a candidate for multi-counterparty "
               "modelling if that shape recurs."),
     "record_status": "extracted"},

    {"duty_id": "duty-ofwat-wia1991-s17f-4-refusal-notice", "holder_type": "body",
     "body_id": OFWAT, "office_id": None,
     "duty_label": "Notice and reasons before refusing a licence application",
     "duty_type": "consultation", "modality": "duty", "mandatory": True,
     "summary": ("Where Ofwat proposes to refuse an application for the grant or variation of "
                 "a water supply or sewerage licence, it shall notify the applicant, state its "
                 "reasons, specify a period for representations or objections, and consider any "
                 "duly made and not withdrawn (WIA 1991 s.17F(4)). The procedural protection "
                 "around market entry being refused."),
     "trigger": "Where Ofwat proposes to refuse a relevant application under s.17F.",
     "beneficiary_or_object": "The applicant for the licence (a private party).",
     "failure_consequence": "judicial_review_risk",
     "owed_to_holder_type": None, "owed_to_body_id": None, "owed_to_office_id": None,
     "source_id": SRC, "provision_key": "water-industry-act-1991-s17f-4",
     "citation": cite("s.17F(4)"), "related_body_ids": [],
     "derived_from_record_id": None, "in_force_from": None, "in_force_to": None,
     "legal_status": "current", "extraction": extraction(0.9),
     "verification": dict(VERIFY),
     "notes": "Owed to a private applicant, so no counterparty edge — carried on the card only.",
     "record_status": "extracted"},
]

# Paragraph-level provisions for the records above (A2.5: create a Provision at the
# granularity the operative record cites; split where a section carries more than one
# independent canonical record).
PROVISIONS = [
    ("water-industry-act-1991-s17a-5", "s.17A(5)", "Water supply licences — general authorisation"),
    ("water-industry-act-1991-s17a-6", "s.17A(6)", "Water supply licences — consultation with the Welsh Ministers"),
    ("water-industry-act-1991-s17f-4", "s.17F(4)", "Procedure for granting licences — notice of proposed refusal"),
    ("water-industry-act-1991-s17j-3", "s.17J(3)", "Modification of standard conditions — notice and representations"),
    ("water-industry-act-1991-s17j-5", "s.17J(5)", "Modification of standard conditions — Secretary of State direction"),
    ("water-industry-act-1991-s17j-5a", "s.17J(5A)", "Modification of standard conditions — consultation with the Welsh Ministers"),
]


def main():
    parents = {p["provision_key"]: p for p in store.load("provisions")}
    new = []
    for key, ref, heading in PROVISIONS:
        parent = parents.get(key.rsplit("-", 1)[0] if key.count("-s") else key)
        base = parents.get("water-industry-act-1991-" + ref.lstrip("s.").split("(")[0].lower())
        src = parent or base
        if not src:
            sys.exit(f"FAIL: no parent provision fetched for {key}")
        new.append({
            "provision_key": key, "instrument_id": src["instrument_id"],
            "provision_ref": ref, "heading": heading, "in_force_from": None,
            "status": "in_force", "citation": dict(src["citation"]),
            "references": [], "made_under": None, "commenced_by": None,
            "outstanding_effects": src.get("outstanding_effects", False),
            "outstanding_effects_note": src.get("outstanding_effects_note"),
            "notes": ("Paragraph-level provision (A2.5): the section carries more than one "
                      "independent canonical record, so the operative records cite at this "
                      "granularity. Hash and version_date inherited from the section fetch."),
            "record_status": "extracted"})
    store.upsert("provisions", new)
    store.upsert("powers", POWERS)
    store.upsert("vetoes", VETOES)
    store.upsert("duties", DUTIES)

    print("--- WIA ss.17A+ licensing regime ---")
    print(f"  provisions added: {len(new)}")
    print(f"  powers:  {len(POWERS)}   vetoes: {len(VETOES)}   duties: {len(DUTIES)}")
    print(f"  totals now — powers {len(store.load('powers'))}, "
          f"duties {len(store.load('duties'))}, vetoes {len(store.load('vetoes'))}")


if __name__ == "__main__":
    main()
