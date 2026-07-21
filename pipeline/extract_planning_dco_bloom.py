#!/usr/bin/env python3
"""Continue the DCO bloom SYSTEMATICALLY — the regime's structure, not the reservoir's needs.

One job. The first planning pass was goal-directed (reservoir decision-spine). This adds the
DCO regime's own structural pieces that a systematic bloom reaches regardless of any target
case (build-out strategy: data is systematic, the chain is goal-directed):

  * s.5   — the SoS's power to DESIGNATE a National Policy Statement. The NPS is the framework
            the DCO decision must accord with (s.104): a proposal counter to the relevant NPS
            faces refusal / heightened risk. Registered as an INSTRUMENT node (sponsor: the
            NPS is a node) even though it is a designated policy statement, not legislation.
  * s.105 — the decision framework where NO NPS has effect (parallel to the held s.104).
  * s.118 — legal challenge: a DCO may be questioned only by judicial review within 6 weeks —
            the Planning Court's jurisdiction, the accountability backstop (the judicial layer
            of the planning domain, as the Chancery Division is for the water SAR). Planning
            Court also gains its sourced `judicial` function tag.

Deferred (noted, not extracted): s.87 (examination conduct) is procedural scaffolding, not a
blocker — the Examining Authority examines on the SoS's behalf (PINS delegated, #28), and the
decision powers already vest in the SoS.

    py -3 pipeline/extract_planning_dco_bloom.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-21-planning-dco-bloom"
SRC = "source-act-planning-act-2008"
SOS = "office-secretary-of-state-for-environment-food-and-rural-affairs"
DEFRA = "uk-state-body-department-for-environment-food-rural-affairs"
PCOURT = "uk-state-body-planning-court"
URL = "https://www.legislation.gov.uk/ukpga/2008/29/section/"


def cite(prov):
    return {"provision": prov, "quote": None, "url": URL + prov.split("(")[0].lstrip("s.")}


def ext(c):
    return {"confidence": c, "extracted_by": "llm", "extraction_run_id": RUN, "requires_review": True}


V = {"verification_status": "unverified", "verified_by": None, "verified_date": None,
     "verification_notes": None}

# The National Policy Statement — a designated policy statement, not legislation. Registered as
# an instrument node (sponsor decision) with its own source; made under Planning Act 2008 s.5.
NPS_SOURCE = {
    "source_id": "source-framework-national-policy-statement-water-resources",
    "title": "National Policy Statement for Water Resources Infrastructure (designated framework)",
    "source_type": "framework_document",
    "publisher": "Department for Environment, Food and Rural Affairs",
    "url": "https://www.gov.uk/government/collections/national-policy-statements-for-water-resources-infrastructure",
    "accessed_date": "2026-07-21", "publication_date": None, "version_date": "2026-07-21",
    "legal_status": "current", "licence": "Open Government Licence v3.0",
    "notes": "The relevant National Policy Statement is a designated POLICY STATEMENT (Planning "
             "Act 2008 s.5), not legislation.gov.uk content, so it has no fetched provisions — a "
             "framework node, not a statutory instrument. Confirm the exact designated water NPS "
             "and its designation date before publication.",
}
NPS_INSTRUMENT = {
    "instrument_id": "instrument-nps-water-resources", "title": NPS_SOURCE["title"],
    "instrument_type": "other", "year": None, "number": None, "status": "in_force",
    "source_id": NPS_SOURCE["source_id"],
    "legislation_url": NPS_SOURCE["url"], "enacted_by": "Secretary of State (designation)",
    "made_under": "planning-act-2008-s5",
    "notes": "Designated National Policy Statement — the framework a DCO decision must have "
             "regard to (s.104). A proposal counter to it faces refusal / heightened risk: a "
             "mild-to-strong policy blocker, not a hard statutory veto. Orphan-instrument by "
             "design (no legislation.gov.uk provisions).",
    "record_status": "extracted",
}

POWERS = [
    {"power_id": "power-sos-defra-planning2008-s5", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "power_label": "Designate a National Policy Statement",
     "power_type": "designation", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("The Secretary of State may designate a statement as a National Policy "
                 "Statement setting out national policy for described developments (Planning Act "
                 "2008 s.5), subject to consultation, publicity and parliamentary requirements "
                 "(ss.7-9). The NPS is the framework every DCO decision must have regard to "
                 "(s.104) — designating it is where the policy that shapes consenting is set."),
     "constraints": ["Subject to consultation and publicity (s.7), parliamentary requirements "
                     "(s.9), and appraisal of sustainability."],
     "source_id": SRC, "provision_key": "planning-act-2008-s5", "citation": cite("s.5(1)"),
     "related_body_ids": [], "related_power_ids": [], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.9), "verification": dict(V),
     "notes": "Produces the NPS instrument node (instrument-nps-water-resources). For water the "
              "designating SoS is Defra; holder-resolution per NPS.",
     "record_status": "extracted"},

    {"power_id": "power-planning-court-planning2008-s118", "holder_type": "body", "body_id": PCOURT,
     "office_id": None,
     "power_label": "Judicial review of a development consent order",
     "power_type": "adjudication", "power_basis": "statutory", "modality": "power",
     "legal_effect": "may",
     "summary": ("A DCO may be questioned only by a claim for judicial review filed within six "
                 "weeks of the order (or its statement of reasons) being published (Planning Act "
                 "2008 s.118) — heard in the Planning Court. The narrow accountability backstop: "
                 "the court can quash a DCO for illegality, but the 6-week ouster makes it a "
                 "high-bar, time-boxed challenge, not an open appeal on the merits."),
     "constraints": ["Only by judicial review; only within the 6-week window (s.118(1))."],
     "source_id": SRC, "provision_key": "planning-act-2008-s118", "citation": cite("s.118(1)"),
     "related_body_ids": [DEFRA],
     "related_power_ids": ["power-sos-defra-planning2008-s114"], "derived_from_record_id": None,
     "legal_status": "current", "extraction": ext(0.9), "verification": dict(V),
     "notes": "The planning domain's judicial layer (as the Chancery Division is the water SAR's). "
              "A quash is adjudication, not a veto — the court decides on legality, deferring to "
              "the SoS on planning merits.",
     "record_status": "extracted"},
]

DUTIES = [
    {"duty_id": "duty-sos-defra-planning2008-s105", "holder_type": "office", "office_id": SOS,
     "body_id": DEFRA, "duty_label": "Decide a DCO on relevant matters where no NPS has effect",
     "duty_type": "other", "modality": "duty", "mandatory": True,
     "summary": ("Where no National Policy Statement has effect for the development, the "
                 "Secretary of State must decide the DCO application having regard to any local "
                 "impact report, any relevant prescribed matters, and any other important and "
                 "relevant matters (Planning Act 2008 s.105). The fallback decision framework "
                 "parallel to s.104 — and the one that applies where a sector's NPS is not yet "
                 "designated."),
     "trigger": "Deciding a DCO application for which no NPS has effect.",
     "beneficiary_or_object": "The public interest; the decision framework.",
     "failure_consequence": "judicial_review_risk",
     "owed_to_holder_type": None, "owed_to_body_id": None, "owed_to_office_id": None,
     "source_id": SRC, "provision_key": "planning-act-2008-s105", "citation": cite("s.105(2)"),
     "related_body_ids": [], "derived_from_record_id": None, "in_force_from": None,
     "in_force_to": None, "legal_status": "current", "extraction": ext(0.88),
     "verification": dict(V),
     "notes": "Relevant where a designated water NPS is absent/pending — then s.105, not s.104, "
              "frames the reservoir decision.",
     "record_status": "extracted"},
]


def main():
    provs = {p["provision_key"] for p in store.load("provisions")}
    for pk in ("planning-act-2008-s5", "planning-act-2008-s105", "planning-act-2008-s118"):
        if pk not in provs:
            sys.exit(f"FAIL: {pk} not fetched — run fetch_legislation.py.")
    store.upsert("sources", [NPS_SOURCE])
    store.upsert("instruments", [NPS_INSTRUMENT])
    store.upsert("powers", POWERS)
    store.upsert("duties", DUTIES)
    # Planning Court gains its sourced judicial function tag (as the Chancery Division has).
    bodies = store.load("bodies")
    for b in bodies:
        if b["body_id"] == PCOURT:
            b["functions"] = sorted(set((b.get("functions") or []) + ["judicial"]))
            b["function_source_ids"] = sorted(set((b.get("function_source_ids") or [])
                                                  + ["source-act-senior-courts-act-1981"]))
    store.save("bodies", bodies)
    print("--- DCO systematic bloom ---")
    print(f"  + NPS instrument node, {len(POWERS)} powers, {len(DUTIES)} duties; "
          f"Planning Court tagged judicial")
    print(f"  totals — powers {len(store.load('powers'))}, duties {len(store.load('duties'))}")


if __name__ == "__main__":
    main()
