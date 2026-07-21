#!/usr/bin/env python3
"""Extract the 10 unmined Water-tranche provisions the breadcrumb register surfaced.

One job. `issues/breadcrumbs.md` flagged 10 provisions as fetched-but-never-extracted (the
false-assurance case the sponsor caught). This works through each from its cached operative
text — the calibration-tranche discipline: hand-built, cited, one record per operative unit.

Findings recorded on the way:
  * s.86 VINDICATES decision #28 (DWI): the water-quality inspectorate has no separate legal
    personality — "The Secretary of State may appoint persons to act on his behalf" — so its
    powers are the Defra SoS office's, not a body node.
  * WSMA 2025 s.14 is an AMENDING provision: its operative power is inserted as WIA 1991
    s.12J, which is fetched and extracted HERE (WSMA s.14 is reclassified CORRECTLY_UNMINED).
  * s.17K (Ofwat's licence-modification reference to the CMA) reaches a CMA veto-following-
    report that is the s.16A-equivalent for LICENCES and is NOT yet fetched — logged as a
    breadcrumb stub, not extracted, so the register keeps owing it.
  * Insolvency Act s.124A vests in "the Secretary of State" (Business), for which no office
    node exists yet — recorded on the DBT body with a holder-resolution note (an office
    should be created when the company-law tranche is built).

Re-runnable and idempotent.

    py -3 pipeline/extract_water_unmined.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

RUN = "run-2026-07-21-water-unmined"
WIA = "source-act-water-industry-act-1991"
INS = "source-act-insolvency-act-1986"
OFWAT = "uk-state-body-the-water-services-regulation-authority"
CMA = "uk-state-body-competition-and-markets-authority"
DEFRA = "uk-state-body-department-for-environment-food-rural-affairs"
SOS = "office-secretary-of-state-for-environment-food-and-rural-affairs"
DBT = "uk-state-body-department-for-business-and-trade"
WELSH = "uk-state-body-welsh-government"
CHANCERY = "uk-state-body-chancery-division-of-the-high-court"


def wia(prov):
    return {"provision": prov, "quote": None,
            "url": "https://www.legislation.gov.uk/ukpga/1991/56/section/" + prov.split("(")[0].lstrip("s.")}


def ins(prov):
    return {"provision": prov, "quote": None,
            "url": "https://www.legislation.gov.uk/ukpga/1986/45/section/124A"}


def ext(conf):
    return {"confidence": conf, "extracted_by": "llm", "extraction_run_id": RUN,
            "requires_review": True}


V = {"verification_status": "unverified", "verified_by": None,
     "verified_date": None, "verification_notes": None}


def power(pid, holder_type, holder, body, label, ptype, effect, summary, pk, cite,
          related=None, constraints=None, note=None, conf=0.9):
    return {"power_id": pid, "holder_type": holder_type,
            "office_id": holder if holder_type == "office" else None,
            "body_id": body, "power_label": label, "power_type": ptype,
            "power_basis": "statutory", "modality": "power", "legal_effect": effect,
            "summary": summary, "constraints": constraints or [], "source_id": SRC_OF[pk[:3]],
            "provision_key": pk, "citation": cite, "related_body_ids": related or [],
            "related_power_ids": [], "derived_from_record_id": None, "legal_status": "current",
            "extraction": ext(conf), "verification": dict(V), "notes": note,
            "record_status": "extracted"}


def duty(did, holder_type, holder, body, label, dtype, summary, pk, cite, trigger=None,
         beneficiary=None, owed_to=None, related=None, note=None, conf=0.9):
    return {"duty_id": did, "holder_type": holder_type,
            "office_id": holder if holder_type == "office" else None,
            "body_id": body, "duty_label": label, "duty_type": dtype, "modality": "duty",
            "mandatory": True, "summary": summary, "trigger": trigger,
            "beneficiary_or_object": beneficiary, "failure_consequence": "judicial_review_risk",
            "owed_to_holder_type": "body" if owed_to else None, "owed_to_body_id": owed_to,
            "owed_to_office_id": None, "source_id": SRC_OF[pk[:3]], "provision_key": pk,
            "citation": cite, "related_body_ids": related or [], "derived_from_record_id": None,
            "in_force_from": None, "in_force_to": None, "legal_status": "current",
            "extraction": ext(conf), "verification": dict(V), "notes": note,
            "record_status": "extracted"}


# provision_key prefix -> source_id (wia keys start "wat", insolvency "ins")
SRC_OF = {"wat": WIA, "ins": INS}

POWERS = [
    power("power-sos-defra-wia1991-s12j", "office", SOS, DEFRA,
          "Modify appointment conditions to recover special-administration losses",
          "direction", "may",
          "The Secretary of State may modify a company's appointment conditions so that they "
          "require or enable the company to raise charges on its customers and pay the amounts "
          "to the Secretary of State to make good any 'SAO loss' — financial assistance given "
          "under the special administration regime that the Secretary of State does not expect "
          "otherwise to recover (WIA 1991 s.12J, inserted by the Water (Special Measures) Act "
          "2025 s.14). The cost-recovery counterpart to the s.153 funding lever.",
          "water-industry-act-1991-s12j", wia("s.12J(2)"),
          related=[OFWAT], note="Applies to companies whose area is wholly or mainly in England "
          "(s.12J(1)). Recovers 'relevant financial assistance' given under s.153 etc. — the "
          "fiscal loop closed on the SAR funding power (veto-hm-treasury-wia1991-s153).",
          conf=0.9),

    power("power-ofwat-wia1991-s17g", "body", OFWAT, OFWAT,
          "Attach conditions to water supply and sewerage licences",
          "licence", "may",
          "Ofwat may include in a water supply or sewerage licence such conditions as appear to "
          "it requisite or expedient having regard to its Part 1 duties, including conditions "
          "requiring payments to Ofwat on grant or while the licence is in force (WIA 1991 "
          "s.17G). The substantive content of the licence sits under this power; s.17A grants "
          "the licence, s.17G shapes what it may contain.",
          "water-industry-act-1991-s17g", wia("s.17G(1)"),
          note="s.17G(1)(b) is a charging condition — Ofwat may make licence grant/holding "
          "conditional on payment.", conf=0.9),

    power("power-sos-defra-wia1991-s17h", "office", SOS, DEFRA,
          "Determine the standard conditions of water supply licences",
          "rulemaking", "may",
          "The Secretary of State may determine the conditions that are to be the STANDARD "
          "conditions of water supply licences granted by Ofwat, and must publish them (WIA "
          "1991 s.17H). The baseline licence terms are set by the Secretary of State; Ofwat "
          "grants against them and may modify them only under ss.17I-17J.",
          "water-industry-act-1991-s17h-1", wia("s.17H(1)"),
          related=[OFWAT], conf=0.9),

    power("power-ofwat-wia1991-s17i", "body", OFWAT, OFWAT,
          "Modify licence conditions by agreement",
          "rulemaking", "conditional",
          "Ofwat may modify the conditions of a particular water supply or sewerage licence "
          "where the licence holder has consented, and (for standard conditions) Ofwat is "
          "satisfied the modification is requisite to the case and leaves no licensee unduly "
          "disadvantaged in competition (WIA 1991 s.17I). The licence analogue of s.13 "
          "(appointment conditions by agreement).",
          "water-industry-act-1991-s17i", wia("s.17I(1)"),
          constraints=["Requires the licence holder's consent (s.17I(2))."], conf=0.9),

    power("power-ofwat-wia1991-s17k", "body", OFWAT, OFWAT,
          "Refer a licence-condition modification to the CMA",
          "rulemaking", "may",
          "Ofwat may refer to the CMA the question whether matters relating to a water supply "
          "or sewerage licence operate against the public interest and, if so, whether licence "
          "modifications could remedy them (WIA 1991 s.17K). The licence analogue of s.14 "
          "(appointment-condition references).",
          "water-industry-act-1991-s17k", wia("s.17K(1)"),
          related=[CMA],
          note="BREADCRUMB STUB: the CMA's veto-following-report for LICENCE modifications (the "
          "s.16A-equivalent, a later section in Chapter 1A not yet fetched) and the s.17-series "
          "modification-following-report duty are not yet extracted. s.17N (the CMA's reporting "
          "duty on these references) IS extracted.", conf=0.88),

    power("power-cma-wia1991-s17r", "body", CMA, CMA,
          "Modify licence conditions by order under other enactments",
          "rulemaking", "may",
          "Where the CMA or the Secretary of State makes a relevant competition order (under "
          "the Enterprise Act 2002 or the Competition Act 1998), the order may also modify the "
          "conditions or standard conditions of water supply and sewerage licences to the "
          "extent requisite to give effect to it (WIA 1991 s.17R). Competition remedies can "
          "reach into the licence regime directly.",
          "water-industry-act-1991-s17r", wia("s.17R(1)"),
          related=[DEFRA],
          note="Multi-holder: the 'relevant authority' is the CMA OR the Secretary of State — "
          "modelled on the CMA (primary) with the SoS as related; per the multi-holder rule "
          "(schema-decisions 2026-07-14). Reaches the Enterprise Act 2002 and Competition Act "
          "1998 (breadcrumb references on the provision).", conf=0.85),

    power("power-sos-defra-wia1991-s86", "office", SOS, DEFRA,
          "Appoint drinking-water inspectors to act on the Secretary of State's behalf",
          "appointment", "may",
          "The Secretary of State may appoint persons to act on his behalf in relation to the "
          "water-quality powers and duties under WIA 1991 ss.67-70 and 77-82 (WIA 1991 s.86). "
          "These are the Drinking Water Inspectorate inspectors. Because they act 'on his "
          "behalf', the water-quality enforcement powers remain the Secretary of State's — DWI "
          "has no separate legal personality (decision #28).",
          "water-industry-act-1991-s86-1", wia("s.86(1)"),
          note="Vindicates decision #28: DWI is a delegated inspectorate, not a body node. Its "
          "s.70 enforcement power is already held by the Defra SoS office "
          "(power-sos-defra-wia1991-s70-dwi-quality-enforcement).", conf=0.92),

    power("power-sos-dbt-insolvency1986-s124a", "body", DBT, DBT,
          "Petition for winding up on grounds of public interest",
          "application_to_court", "may",
          "Where it appears to the Secretary of State, from company-investigation or "
          "fraud-investigation reports and information (Companies Act 1985 Pt XIV; FSMA 2000; "
          "Criminal Justice Act 1987), that it is expedient in the public interest, the "
          "Secretary of State may petition for a company to be wound up (Insolvency Act 1986 "
          "s.124A). Reached via the water SAR: the ordinary public-interest winding-up route, "
          "the general-company-law alternative to a water special administration order.",
          "insolvency-act-1986-s124a", ins("s.124A(1)"),
          related=[CHANCERY],
          note="HOLDER-RESOLUTION GAP: this vests in 'the Secretary of State' exercising the "
          "insolvency/company-investigation function (in practice the Secretary of State for "
          "Business and Trade), for which no OFFICE node exists yet. Recorded on the DBT body "
          "with holder_type=body; an office should be created when a company-law/insolvency "
          "tranche is built (holder-resolution follows decision #13). The trigger instruments "
          "(Companies Act 1985/1989, FSMA 2000, Criminal Justice Act 1987, Criminal Law "
          "(Consolidation) (Scotland) Act 1995) are breadcrumb references on the provision.",
          conf=0.85),
]

DUTIES = [
    duty("duty-cma-wia1991-s15", "body", CMA, CMA,
         "Report definite conclusions on an appointment-modification reference",
         "reporting",
         "In reporting on a s.14 appointment-condition reference, the CMA shall include definite "
         "conclusions with reasons, specify any effects adverse to the public interest, and "
         "specify modifications that could remedy them (WIA 1991 s.15). Conclusions bind s.16 "
         "only if reached by at least two-thirds of the CMA group (s.15(1A)).",
         "water-industry-act-1991-s15", wia("s.15(1)"),
         trigger="On making a report on a s.14 reference.",
         beneficiary="The public interest; Ofwat and the company (the report gates s.16).",
         conf=0.9),

    duty("duty-cma-wia1991-s17n", "body", CMA, CMA,
         "Report definite conclusions on a licence-modification reference",
         "reporting",
         "In reporting on a s.17K licence-modification reference, the CMA shall include definite "
         "conclusions with reasons, specify effects adverse to the public interest, and specify "
         "modifications that could remedy them (WIA 1991 s.17N). The licence analogue of s.15.",
         "water-industry-act-1991-s17n", wia("s.17N(1)"),
         trigger="On making a report on a s.17K reference.",
         beneficiary="The public interest; Ofwat and the licensee.", conf=0.9),

    duty("duty-sos-defra-wia1991-s17h-1a-consult", "office", SOS, DEFRA,
         "Consult the Welsh Ministers before determining standard licence conditions",
         "consultation",
         "Before determining the standard conditions of water supply licences, the Secretary of "
         "State must consult the Welsh Ministers as regards conditions relating to a restricted "
         "retail authorisation or a supplementary authorisation (WIA 1991 s.17H(1A)).",
         "water-industry-act-1991-s17h-1a", wia("s.17H(1A)"),
         trigger="Before determining standard conditions under s.17H(1).",
         beneficiary="The Welsh Ministers (devolved interest).", owed_to=WELSH,
         related=[WELSH],
         note="Counterparty mapped to the Welsh Government body; statute names 'the Welsh "
         "Ministers' (Government of Wales Act 2006 office-holders, no office node yet).",
         conf=0.9),

    duty("duty-sos-defra-wia1991-s86-1a", "office", SOS, DEFRA,
         "Designate a Chief Inspector of Drinking Water",
         "other",
         "The Secretary of State shall designate one of the persons appointed under s.86(1) as "
         "the Chief Inspector of Drinking Water (WIA 1991 s.86(1A)). The statutory head of the "
         "Drinking Water Inspectorate — an office within the Defra SoS's function, not a "
         "separate body (decision #28).",
         "water-industry-act-1991-s86-1a", wia("s.86(1A)"),
         trigger="On appointing inspectors under s.86(1).",
         beneficiary="Drinking-water quality regulation; the public.",
         note="A candidate OFFICE node (Chief Inspector of Drinking Water) under the #28 "
         "vested-vs-delegated test — the post is named in statute. Held for now as the Defra "
         "SoS's duty; promote to an office if the DWI tranche is built out.", conf=0.9),
]

# Paragraph-level provisions for the sections carrying more than one canonical record (A2.5).
NEW_PROVISIONS = [
    ("water-industry-act-1991-s17h-1", "s.17H(1)", "Standard conditions of water supply licences — Secretary of State's power to determine"),
    ("water-industry-act-1991-s17h-1a", "s.17H(1A)", "Standard conditions of water supply licences — consultation with the Welsh Ministers"),
    ("water-industry-act-1991-s86-1", "s.86(1)", "Appointment of drinking-water inspectors"),
    ("water-industry-act-1991-s86-1a", "s.86(1A)", "Designation of the Chief Inspector of Drinking Water"),
]


def main():
    parents = {p["provision_key"]: p for p in store.load("provisions")}
    new = []
    for key, ref, heading in NEW_PROVISIONS:
        base_sec = key.rsplit("-", 1)[0]  # s17h-1 -> s17h
        src = parents.get(base_sec)
        if not src:
            sys.exit(f"FAIL: parent provision {base_sec} not fetched")
        p = dict(src)
        p.update({"provision_key": key, "provision_ref": ref, "heading": heading,
                  "citation": dict(src["citation"]), "references": [],
                  "notes": "Paragraph-level provision (A2.5): the section carries more than one "
                           "independent canonical record. Hash/version inherited from the section."})
        new.append(p)
    store.upsert("provisions", new)
    store.upsert("powers", POWERS)
    store.upsert("duties", DUTIES)

    print("--- water unmined provisions ---")
    print(f"  paragraph-provisions added: {len(new)}")
    print(f"  powers: {len(POWERS)}   duties: {len(DUTIES)}")
    print(f"  totals now — powers {len(store.load('powers'))}, duties {len(store.load('duties'))}, "
          f"vetoes {len(store.load('vetoes'))}")


if __name__ == "__main__":
    main()
