#!/usr/bin/env python3
"""Extract the Planning Act 2008 DCO decision-spine — the reservoir/NSIP consenting chain.

One job. First operative pass over the planning/infrastructure domain (Tranche A), scoped
(decision #11) to the blocker-bearing decision-spine a reservoir DCO reaches. The reservoir
(SESRO) is an NSIP consented by a Development Consent Order; this records who decides it, the
land-taking power over private owners, and — the fusion edge — the environment bodies' veto
over a DCO subsuming their consents.

Holder note: the Planning Act says "the Secretary of State"; the decision-maker is the SoS
responsible for the relevant National Policy Statement. For a WATER reservoir that is the
Defra SoS (who directed SESRO's NSIP status), so the DCO powers are recorded on the Defra SoS
office with a holder-resolution note. The Planning Inspectorate is the examining authority
(acts on the SoS's behalf — the #28 delegated pattern) and is carried in related_body_ids.

THE FUSION FINDING (s.150). "A DCO may remove a requirement for a prescribed consent only if
the relevant body has consented." So any body whose consent a DCO would subsume — the
Environment Agency (abstraction), Natural England (SSSI/Habitats) — holds a veto over that
removal. A genuine statutory link from the environment tranche to the planning decision, not
merely an assembled one. Recorded on the EA (the water-relevant instance) with a class note;
Natural England holds the equivalent.

    py -3 pipeline/extract_planning_dco.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-21-planning-dco"
SRC = "source-act-planning-act-2008"
SOS = "office-secretary-of-state-for-environment-food-and-rural-affairs"
DEFRA = "uk-state-body-department-for-environment-food-rural-affairs"
PINS = "uk-state-body-planning-inspectorate"
EA = "uk-state-body-environment-agency"
NE = "uk-state-body-natural-england"
URL = "https://www.legislation.gov.uk/ukpga/2008/29/section/"


def cite(prov):
    return {"provision": prov, "quote": None, "url": URL + prov.split("(")[0].lstrip("s.")}


def ext(c):
    return {"confidence": c, "extracted_by": "llm", "extraction_run_id": RUN, "requires_review": True}


V = {"verification_status": "unverified", "verified_by": None, "verified_date": None,
     "verification_notes": None}

HOLDER_NOTE = ("Holder: the Planning Act says 'the Secretary of State'; the decision-maker is "
               "the SoS responsible for the relevant National Policy Statement — for a water "
               "reservoir the Defra SoS (holder-resolution per sector). PINS examines on the "
               "SoS's behalf (#28 delegated pattern).")

POWERS = [
    {"power_id": "power-sos-defra-planning2008-s35", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "power_label": "Direct a project into the development-consent regime",
     "power_type": "designation", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("The Secretary of State may direct that development in the field of energy, "
                 "transport, WATER, waste water or waste be treated as development for which "
                 "development consent is required (Planning Act 2008 s.35) — bringing a project "
                 "into the NSIP/DCO regime. The 'in-scope' gate; this is how SESRO was directed "
                 "in."),
     "constraints": ["Limited to the fields in s.35(2) and subject to s.35ZA."],
     "source_id": SRC, "provision_key": "planning-act-2008-s35", "citation": cite("s.35(1)"),
     "related_body_ids": [PINS], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.9), "verification": dict(V),
     "notes": HOLDER_NOTE, "record_status": "extracted"},

    {"power_id": "power-sos-defra-planning2008-s55", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "power_label": "Accept or reject a development-consent application",
     "power_type": "approval", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("The Secretary of State must decide within 28 days whether to accept a DCO "
                 "application, and may accept it only if satisfied it is a proper application "
                 "meeting the statutory standards (Planning Act 2008 s.55). The acceptance gate "
                 "before examination."),
     "constraints": ["Acceptance only if the s.55(3) standards are met."],
     "source_id": SRC, "provision_key": "planning-act-2008-s55", "citation": cite("s.55(2)"),
     "related_body_ids": [PINS], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.88), "verification": dict(V),
     "notes": HOLDER_NOTE, "record_status": "extracted"},

    {"power_id": "power-sos-defra-planning2008-s114", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "power_label": "Grant or refuse development consent",
     "power_type": "approval", "power_basis": "statutory", "modality": "power",
     "legal_effect": "must",
     "summary": ("Once the Secretary of State has decided a DCO application, the Secretary of "
                 "State must either make an order granting development consent or refuse it "
                 "(Planning Act 2008 s.114). THE decision — the reservoir is built or not on "
                 "this. A refusal blocks the private applicant (the undertaker); a grant "
                 "authorises development that could otherwise not lawfully proceed."),
     "constraints": ["Decided having regard to the NPS (s.104) and the examining authority's "
                     "report."],
     "source_id": SRC, "provision_key": "planning-act-2008-s114", "citation": cite("s.114(1)"),
     "related_body_ids": [PINS], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.9), "verification": dict(V),
     "notes": HOLDER_NOTE + " The applicant (e.g. Thames Water) is a PRIVATE party — the "
              "state->private dimension surfaces here and at s.122 (#29).", "record_status": "extracted"},

    {"power_id": "power-sos-defra-planning2008-s122", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "power_label": "Authorise compulsory acquisition of land in a DCO",
     "power_type": "other", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("A DCO may authorise the compulsory acquisition of land only if the Secretary "
                 "of State is satisfied the land is required for (or incidental to) the "
                 "development and there is a compelling case in the public interest (Planning Act "
                 "2008 ss.122-123). The land-taking power — for a reservoir, often the hardest "
                 "blocker, and the clearest state->private relationship (it overrides private "
                 "landowners)."),
     "constraints": ["Only if the s.122(2)-(3) conditions (land required; compelling public "
                     "interest) are met."],
     "source_id": SRC, "provision_key": "planning-act-2008-s122", "citation": cite("s.122(1)"),
     "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.9), "verification": dict(V),
     "notes": "power_type 'other': compulsory acquisition is a sui generis land-taking power "
              "with no closer vocab term (candidate `compulsory_acquisition` if it recurs). The "
              "blocked party is a PRIVATE landowner — the #29 state->private role-class, not a "
              "state-to-state edge; carried on the card, surfaced in the reservoir chain view.",
     "record_status": "extracted"},

    # s.150 = the fusion edge, recorded as the consenting body's power (canonical) + its veto.
    {"power_id": "power-ea-planning2008-s150-consent", "holder_type": "body", "body_id": EA,
     "office_id": None,
     "power_label": "Consent to a DCO removing the body's own consent requirement",
     "power_type": "consent", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("A DCO may remove a requirement for a prescribed consent or authorisation only "
                 "if the body that would otherwise grant it consents to that removal (Planning "
                 "Act 2008 s.150). So a consenting body — for a reservoir, the Environment Agency "
                 "(abstraction) or Natural England (SSSI/Habitats) — controls whether its consent "
                 "regime is folded into the DCO. The statutory link between the planning decision "
                 "and the environment/water tranches."),
     "constraints": ["Applies to any 'prescribed consent'; the relevant body varies by what the "
                     "DCO seeks to subsume."],
     "source_id": SRC, "provision_key": "planning-act-2008-s150", "citation": cite("s.150(1)"),
     "related_body_ids": [NE], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.87), "verification": dict(V),
     "notes": "CLASS power held by ANY consenting body whose consent a DCO would remove; recorded "
              "on the Environment Agency as the water-relevant instance, with Natural England as "
              "related. The reservoir chain instantiates it for the specific consents subsumed.",
     "record_status": "extracted"},
]

DUTIES = [
    {"duty_id": "duty-sos-defra-planning2008-s104", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "duty_label": "Decide a DCO having regard to the National Policy Statement",
     "duty_type": "other", "modality": "duty", "mandatory": True,
     "summary": ("Where a National Policy Statement has effect for the development, the Secretary "
                 "of State must have regard to it (and to any other important and relevant "
                 "matters) in deciding the DCO application (Planning Act 2008 s.104). The NPS "
                 "frames — and largely predetermines — the decision, which is why the NPS itself "
                 "is the real policy battleground."),
     "trigger": "When deciding a DCO application for which an NPS has effect.",
     "beneficiary_or_object": "The public interest, as framed by the NPS.",
     "failure_consequence": "judicial_review_risk",
     "owed_to_holder_type": None, "owed_to_body_id": None, "owed_to_office_id": None,
     "source_id": SRC, "provision_key": "planning-act-2008-s104", "citation": cite("s.104(2)"),
     "related_body_ids": [], "derived_from_record_id": None, "in_force_from": None,
     "in_force_to": None, "legal_status": "current", "extraction": ext(0.88),
     "verification": dict(V),
     "notes": "Breadcrumb: the National Policy Statement is the framework instrument the DCO "
              "decision turns on; not yet held (a designated NPS, not primary legislation).",
     "record_status": "extracted"},
]

VETOES = [
    {"veto_id": "veto-ea-planning2008-s150", "holder_type": "body", "body_id": EA, "office_id": None,
     "veto_label": "Consenting body's veto over a DCO subsuming its consent",
     "veto_type": "consent_required", "modality": "veto", "strength": "hard_stop",
     "overridable": "no", "override_mechanism": None,
     "summary": ("A DCO may remove a body's consent requirement ONLY IF that body consents "
                 "(Planning Act 2008 s.150) — so the Environment Agency (and, for SSSI/Habitats, "
                 "Natural England) can refuse to let its consent regime be folded into the DCO, "
                 "forcing the developer to obtain that consent separately. The environment "
                 "tranche's statutory hold over the planning decision."),
     "decision_affected": ("Whether a Development Consent Order may remove/subsume the "
                           "Environment Agency's (or another body's) separate consent requirement."),
     "derived_from_record_id": "power-ea-planning2008-s150-consent",
     "blocks_holder_type": "office", "blocks_office_id": SOS, "blocks_body_id": DEFRA,
     "blocks_record_id": "power-sos-defra-planning2008-s114", "blocks_record_type": "power",
     "blocks_provision_key": "planning-act-2008-s150",
     "source_id": SRC, "provision_key": "planning-act-2008-s150", "citation": cite("s.150(1)"),
     "legal_status": "current", "extraction": ext(0.86),
     "verification": {"verification_status": "unverified", "verified_by": None,
                      "verified_date": None,
                      "verification_notes": "First-pass; the s.150 consent is unqualified in the "
                      "text (no override), hence hard_stop — but confirm no deemed-consent clock "
                      "in the prescribed-consent regulations before publication."},
     "notes": "Class veto (any consenting body); recorded on the EA as the water instance. This "
              "is the FUSION edge: it draws a can_veto link from the Environment Agency to the "
              "SoS's DCO decision, connecting the planning and environment tranches in-statute.",
     "record_status": "extracted"},
]


def main():
    provs = {p["provision_key"] for p in store.load("provisions")}
    for pk in ("planning-act-2008-s35", "planning-act-2008-s55", "planning-act-2008-s114",
               "planning-act-2008-s122", "planning-act-2008-s104", "planning-act-2008-s150"):
        if pk not in provs:
            sys.exit(f"FAIL: {pk} not fetched — run fetch_legislation.py.")
    store.upsert("powers", POWERS)
    store.upsert("duties", DUTIES)
    store.upsert("vetoes", VETOES)
    print("--- Planning Act 2008 DCO decision-spine ---")
    print(f"  powers {len(POWERS)}, duties {len(DUTIES)}, vetoes {len(VETOES)}")
    print("  fusion edge: veto-ea-planning2008-s150 (EA -> SoS DCO decision)")
    print(f"  totals — powers {len(store.load('powers'))}, duties {len(store.load('duties'))}, "
          f"vetoes {len(store.load('vetoes'))}")


if __name__ == "__main__":
    main()
