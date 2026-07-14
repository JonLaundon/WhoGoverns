#!/usr/bin/env python3
"""Spiral 2 CALIBRATION SLICE — hand-verified Power/Duty/Veto records for the Water
Industry Act 1991, holder = Ofwat (and the Defra Secretary of State).

This is the LLM-extraction step done by hand for the first slice, to settle the A6 schema
against real statute before automating (Annex A13.1 discipline). Each record was written
from the actual consolidated text fetched by fetch_legislation.py (cited to the section).
It tells the Tranche-0 Water story: the enforcement/penalty toolkit (Thames Water) and the
special-administration lever (renationalisation, and its SoS-consent gate = a clean veto).

Modelling notes surfaced by this slice (for the schema-decisions log):
  - GRANULARITY: s.24 confers INDEPENDENT powers on the SoS (s.24(1)(a)) and on Ofwat
    (s.24(1)(b)). Two independent canonical records cannot share one section-level
    provision_key (A2.5), so s.24 uses PARAGRAPH-level provision_keys.
  - MULTI-HOLDER: ss.18/22A name 'the Secretary of State OR the Authority'. Modelled with
    the primary holder (Ofwat) + a note; full multi-holder modelling is a later refinement.
  - VETO IS DERIVED: the SoS-consent veto (s.24) derives from Ofwat's petition power; the
    s.22A notice duty derives from the s.22A penalty power (both carry derived_from_record_id).

    py -3 pipeline/extract_wia1991_water.py [--dry-run]
"""
import argparse

import store

SRC = "source-act-water-industry-act-1991"
INSTR = "instrument-act-water-industry-act-1991"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
DEFRA = "uk-state-body-department-for-environment-food-rural-affairs"
SOS = "office-secretary-of-state-for-environment-food-and-rural-affairs"
RUN = "run-2026-07-14-wia1991-water-calibration"
SEC_URL = "https://www.legislation.gov.uk/ukpga/1991/56/section/"


def cite(ref, sec):
    return {"provision": ref, "url": SEC_URL + sec, "quote": None}


def extraction():
    return {"extracted_by": "llm", "extraction_run_id": RUN, "confidence": 0.9, "requires_review": True}


def verification():
    return {"verification_status": "unverified", "verified_by": None, "verified_date": None,
            "verification_notes": None}


# --- extra paragraph-level provisions for s.24 (see granularity note) ---
def provs():
    def p(key, ref):
        return {"provision_key": key, "instrument_id": INSTR, "provision_ref": ref, "heading": None,
                "in_force_from": None, "status": "in_force",
                "citation": {"url": SEC_URL + "24", "version_date": "2026-07-14", "content_hash": None},
                "references": [], "made_under": None, "commenced_by": None, "outstanding_effects": False,
                "outstanding_effects_note": "Outstanding-effects check not yet wired (Spiral 2 TODO).",
                "notes": "Paragraph-level provision for an independent operative record (see extract_wia1991_water).",
                "record_status": "extracted"}
    return [p("water-industry-act-1991-s24-1-a", "s.24(1)(a)"),
            p("water-industry-act-1991-s24-1-b", "s.24(1)(b)"),
            p("water-industry-act-1991-s24-1b", "s.24(1B)")]


def powers():
    return [
        {"power_id": "power-ofwat-wia1991-s13", "holder_type": "body", "office_id": None, "body_id": OFWAT,
         "power_label": "Modify licence/appointment conditions by agreement", "power_type": "rulemaking",
         "modality": "power", "legal_effect": "may",
         "summary": "Ofwat may modify the conditions of a water/sewerage company's appointment where the company consents to the modification.",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s13", "citation": cite("s.13", "13"),
         "conditions": [],
         "constraints": ["Modification is by AGREEMENT — the company (not a state body) must consent; contrast ss.14-16, modification by CMA reference."],
         "related_body_ids": [], "related_power_ids": ["power-ofwat-wia1991-s14"],
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": None, "record_status": "extracted"},

        {"power_id": "power-ofwat-wia1991-s14", "holder_type": "body", "office_id": None, "body_id": OFWAT,
         "power_label": "Refer a licence-condition modification to the CMA", "power_type": "rulemaking",
         "modality": "power", "legal_effect": "may",
         "summary": "Ofwat may refer to the Competition and Markets Authority the question whether conditions of a company's appointment should be modified; the CMA then determines the reference.",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s14", "citation": cite("s.14", "14"),
         "constraints": ["The CMA, not Ofwat, determines the reference — a cross-body check on unilateral modification."],
         "related_body_ids": ["uk-state-body-competition-and-markets-authority"], "related_power_ids": [],
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": "CMA determination role noted; full CMA modelling is a later slice.", "record_status": "extracted"},

        {"power_id": "power-ofwat-wia1991-s22a", "holder_type": "body", "office_id": None, "body_id": OFWAT,
         "power_label": "Impose a financial penalty", "power_type": "sanction", "modality": "power",
         "legal_effect": "may",
         "summary": "Where satisfied a company/licensee has contravened a condition or a statutory requirement, or failed a performance standard, Ofwat may impose a financial penalty of such amount as is reasonable in all the circumstances. (The lever behind the record Thames Water penalty.)",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s22a", "citation": cite("s.22A(1)", "22A"),
         "constraints": ["Capped at 10% of turnover (s.22A(11)).",
                         "Ofwat must first consider whether to proceed under the Competition Act 1998 instead (s.22A(13)-(14)).",
                         "s.22A(2) also confers this on the Secretary of State / Welsh Ministers as enforcement authority — modelled here on the primary holder (Ofwat)."],
         "related_body_ids": [], "related_power_ids": [],
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": None, "record_status": "extracted"},

        {"power_id": "power-sos-defra-wia1991-s24-1-a", "holder_type": "office", "office_id": SOS, "body_id": DEFRA,
         "power_label": "Petition for a special administration order", "power_type": "other", "modality": "power",
         "legal_effect": "may",
         "summary": "The Secretary of State may present a petition to the High Court for a special administration order against a water/sewerage company on the grounds in s.24(2) (e.g. serious breach of a principal duty, or inability to pay debts). The direct public-control lever short of statutory renationalisation.",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s24-1-a", "citation": cite("s.24(1)(a)", "24"),
         "constraints": ["Grounds are limited to those in s.24(2).", "The High Court, not the SoS, makes the order."],
         "related_body_ids": [], "related_power_ids": ["power-ofwat-wia1991-s24-1-b"],
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": None, "record_status": "extracted"},

        {"power_id": "power-ofwat-wia1991-s24-1-b", "holder_type": "body", "office_id": None, "body_id": OFWAT,
         "power_label": "Petition for a special administration order (with SoS consent)", "power_type": "other",
         "modality": "power", "legal_effect": "conditional",
         "summary": "Ofwat may, WITH THE CONSENT of the Secretary of State, present a petition to the High Court for a special administration order against a water/sewerage company.",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s24-1-b", "citation": cite("s.24(1)(b)", "24"),
         "conditions": [{"condition_type": "approve", "actor_holder_type": "office", "actor_office_id": SOS,
                         "actor_body_id": DEFRA, "provision_key": "water-industry-act-1991-s24-1-b"}],
         "constraints": ["Exercisable only with the Secretary of State's consent (materialises as the SoS veto, veto-sos-defra-wia1991-s24)."],
         "related_body_ids": [], "related_power_ids": ["power-sos-defra-wia1991-s24-1-a"],
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": None, "record_status": "extracted"},
    ]


def duties():
    return [
        {"duty_id": "duty-ofwat-wia1991-s2", "holder_type": "body", "office_id": None, "body_id": OFWAT,
         "duty_label": "General duties in regulating the water industry", "duty_type": "other", "modality": "duty",
         "mandatory": True,
         "summary": "In exercising its functions Ofwat must act in the way best calculated to further the statutory objectives in s.2 — protecting consumers, securing that water/sewerage companies can (in particular through returns on capital) finance the proper carrying out of their functions, promoting economy and efficiency, and securing resilience.",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s2", "citation": cite("s.2", "2"),
         "trigger": "Whenever Ofwat exercises its functions under the Act.", "beneficiary_or_object": "Consumers; the water/sewerage sector.",
         "failure_consequence": "judicial_review_risk", "related_body_ids": [],
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": "s.2 is long and multi-limbed; captured as one general-duties record for the calibration slice — candidate for splitting per limb later.",
         "record_status": "extracted"},

        {"duty_id": "duty-ofwat-wia1991-s18", "holder_type": "body", "office_id": None, "body_id": OFWAT,
         "duty_label": "Make an enforcement order to secure compliance", "duty_type": "enforcement", "modality": "duty",
         "mandatory": True,
         "summary": "Where satisfied that a company/licensee is contravening (or is likely to contravene) a condition or an enforceable requirement for which it is the enforcement authority, Ofwat must by a final enforcement order make such provision as is requisite to secure compliance (subject to ss.19-20).",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s18", "citation": cite("s.18(1)", "18"),
         "trigger": "On being satisfied of a contravention or likely contravention.", "beneficiary_or_object": "Compliance with appointment/licence conditions and statutory requirements.",
         "failure_consequence": "judicial_review_risk", "related_body_ids": [],
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": "s.18 also names the Secretary of State as an alternative enforcement authority — modelled on Ofwat.",
         "record_status": "extracted"},

        {"duty_id": "duty-ofwat-wia1991-s22a-notice", "holder_type": "body", "office_id": None, "body_id": OFWAT,
         "duty_label": "Give notice and consider representations before imposing a penalty", "duty_type": "consultation",
         "modality": "duty", "mandatory": True,
         "summary": "Before imposing a penalty under s.22A, Ofwat must give notice of the proposed penalty (with reasons and the acts/omissions relied on), allow at least 21 days for representations or objections, and consider any duly made.",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s22a", "citation": cite("s.22A(4)", "22A"),
         "trigger": "Before imposing a s.22A penalty.", "beneficiary_or_object": "The company/licensee facing the penalty.",
         "failure_consequence": "invalid_decision", "related_body_ids": [],
         "derived_from_record_id": "power-ofwat-wia1991-s22a",
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": "Procedural duty attached to the s.22A penalty power (same provision -> derived record, A2.5).",
         "record_status": "extracted"},

        {"duty_id": "duty-ofwat-wia1991-s24-consult", "holder_type": "body", "office_id": None, "body_id": OFWAT,
         "duty_label": "Consult the Welsh Ministers before a special-administration petition (Welsh licensee)", "duty_type": "consultation",
         "modality": "duty", "mandatory": True,
         "summary": "Before presenting a s.24(1A) petition in relation to a qualifying water supply licensee whose licence gives it a supplementary authorisation, the Secretary of State or Ofwat must consult the Welsh Ministers.",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s24-1b", "citation": cite("s.24(1B)", "24"),
         "trigger": "Before presenting a s.24(1A) petition re a Welsh-authorised licensee.", "beneficiary_or_object": "The Welsh Ministers (devolved interest).",
         "failure_consequence": "judicial_review_risk", "related_body_ids": [],
         "legal_status": "current", "extraction": extraction(), "verification": verification(),
         "notes": "England/Wales split: WIA 1991 is E&W with Welsh Ministers' functions — a devolution touchpoint even within Tranche 0.",
         "record_status": "extracted"},
    ]


def vetoes():
    return [
        {"veto_id": "veto-sos-defra-wia1991-s24", "holder_type": "office", "office_id": SOS, "body_id": DEFRA,
         "veto_label": "SoS consent required for an Ofwat special-administration petition", "veto_type": "consent_required",
         "modality": "veto", "strength": "hard_stop",
         "summary": "Ofwat cannot petition for a special administration order without the consent of the Secretary of State — a hard gate over the regulator's use of the special-administration lever.",
         "source_id": SRC, "provision_key": "water-industry-act-1991-s24-1-b", "citation": cite("s.24(1)(b)", "24"),
         "derived_from_record_id": "power-ofwat-wia1991-s24-1-b",
         "decision_affected": "Ofwat's petition to the High Court for a special administration order against a water/sewerage company.",
         "blocks_holder_type": "body", "blocks_office_id": None, "blocks_body_id": OFWAT,
         "blocks_provision_key": "water-industry-act-1991-s24-1-b",
         "trigger": "Before Ofwat may present a s.24(1)(b) petition.", "overridable": "no", "override_mechanism": None,
         "failure_consequence": "invalid_decision", "legal_status": "current",
         "extraction": extraction(), "verification": verification(),
         "notes": "The 'who can block?' showcase: the SoS gates the regulator's own escalation route.",
         "record_status": "extracted"},
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    P, D, V, PR = powers(), duties(), vetoes(), provs()
    if not args.dry_run:
        store.upsert("provisions", PR)
        store.upsert("powers", P)
        store.upsert("duties", D)
        store.upsert("vetoes", V)
    print("--- extract_wia1991_water (calibration slice){} ---".format(" DRY RUN" if args.dry_run else ""))
    print(f"provisions (paragraph-level added): {len(PR)}")
    print(f"powers:  {len(P)}")
    print(f"duties:  {len(D)}")
    print(f"vetoes:  {len(V)}")


if __name__ == "__main__":
    main()
