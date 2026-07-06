#!/usr/bin/env python3
"""Off-register bodies tranche (Spiral 1.5) — bodies OUTSIDE the GOV.UK Organisations API.

The GOV.UK Organisations API (source of the 660 core bodies) omits two kinds of body
that nonetheless exercise public functions:

  A. Chartered bodies (body_type royal_charter_body) — self-governing bodies incorporated
     by Royal Charter, sourced to the Privy Council record of charters granted. Only
     PUBLIC-FUNCTION chartered bodies that are NOT already in the graph (sponsor decision:
     British Council, BBC, Bank of England are already held via the API and keep their
     API classification).
  B. Independent STATUTORY regulators (body_type other_body, flagged) — the health and
     legal professional regulators and a few others, established by statute outside the
     departmental family, sourced to the DBT List of UK regulators. Classified other_body
     (they don't fit the departmental scheme) and flagged for review — decision #12 stands,
     so "regulator" is carried on the FUNCTIONAL axis (functions=['regulation']), not as a
     body_type. Voluntary/private professional institutes on the DBT list (accountancy AML
     supervisors, etc.) are EXCLUDED per the statutory-function test.

Founding statute / specific charter provision are Spiral 2 citations (as for the 660 core
bodies, whose founding legislation is likewise deferred). Existence + classification are
sourced here. record_status=extracted (agent-curated, awaits human verification).

Create-if-absent, like transform_bodies — never overwrites an existing record.
    py -3 pipeline/ingest_offregister.py [--dry-run]
"""
import argparse
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODIES = os.path.join(REPO, "data", "bodies")
PRIVY = "source-official-dataset-privy-council-charters"
DBT = "source-official-dataset-list-of-uk-regulators"

# --- Group A: chartered bodies (royal_charter_body), sourced to the Privy Council register.
# (slug, name, aliases, charter_year, also_regulates)
CHARTERED = [
    ("royal-college-of-veterinary-surgeons", "Royal College of Veterinary Surgeons",
     ["RCVS"], 1844, True),
    ("commonwealth-war-graves-commission", "Commonwealth War Graves Commission",
     ["CWGC", "Imperial War Graves Commission"], 1917, False),
    ("royal-society", "The Royal Society",
     ["Royal Society", "Royal Society of London for Improving Natural Knowledge"], 1662, False),
    ("british-academy", "The British Academy",
     ["British Academy"], 1902, False),
    ("royal-academy-of-engineering", "Royal Academy of Engineering",
     ["RAEng", "Fellowship of Engineering"], 1983, False),
]

# --- Group B: independent statutory regulators (other_body, flagged, functions=regulation),
# sourced to the DBT List of UK regulators. (slug, name, aliases)
STATUTORY_REGULATORS = [
    ("general-medical-council", "General Medical Council", ["GMC"]),
    ("general-dental-council", "General Dental Council", ["GDC"]),
    ("nursing-and-midwifery-council", "Nursing and Midwifery Council", ["NMC"]),
    ("general-pharmaceutical-council", "General Pharmaceutical Council", ["GPhC"]),
    ("general-optical-council", "General Optical Council", ["GOC"]),
    ("general-osteopathic-council", "General Osteopathic Council", ["GOsC"]),
    ("general-chiropractic-council", "General Chiropractic Council", ["GCC"]),
    ("health-and-care-professions-council", "Health and Care Professions Council", ["HCPC"]),
    ("solicitors-regulation-authority", "Solicitors Regulation Authority", ["SRA"]),
    ("bar-standards-board", "Bar Standards Board", ["BSB"]),
    ("cilex-regulation", "CILEx Regulation", ["CILEx Regulation Ltd"]),
    ("council-for-licensed-conveyancers", "Council for Licensed Conveyancers", ["CLC"]),
    ("costs-lawyer-standards-board", "Costs Lawyer Standards Board", ["CLSB"]),
    ("intellectual-property-regulation-board", "Intellectual Property Regulation Board", ["IPReg"]),
    ("master-of-the-faculties", "Master of the Faculties", ["Faculty Office"]),
    ("farriers-registration-council", "Farriers Registration Council", ["FRC"]),
    ("panel-on-takeovers-and-mergers", "The Takeover Panel", ["Panel on Takeovers and Mergers"]),
]


def base(slug, name, aliases):
    return {
        "body_id": "uk-state-body-" + slug,
        "name": name,
        "other_names": aliases,
        "status": "active",
        "jurisdiction": ["UK"],
        "sponsor_department_id": None,
        "parent_body_id": None,
        "govuk_organisation_slug": None,
        "external_ids": {"govuk_content_id": None, "govuk_analytics_identifier": None,
                         "company_number": None, "charity_number": None},
        "founding_source_ids": [],
        "framework_document_source_ids": [],
        "annual_report_source_ids": [],
        "record_status": "extracted",
        "last_reviewed": None,
    }


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    records = []
    for slug, name, aliases, year, regs in CHARTERED:
        r = base(slug, name, aliases)
        r["body_type"] = "royal_charter_body"
        r["classification_source_ids"] = [PRIVY]
        r["notes"] = ("Incorporated by Royal Charter ({}); off-register (not on the GOV.UK "
                      "Organisations API). Existence/classification sourced to the Privy "
                      "Council record of charters granted; charter provision is a Spiral 2 "
                      "citation.".format(year))
        if regs:
            r["functions"] = ["regulation"]
            r["function_source_ids"] = [DBT]
            r["notes"] += " Also a statutory regulator on the DBT List of UK regulators."
        records.append(r)

    for slug, name, aliases in STATUTORY_REGULATORS:
        r = base(slug, name, aliases)
        r["body_type"] = "other_body"
        r["needs_classification_review"] = True
        r["classification_source_ids"] = [DBT]
        r["functions"] = ["regulation"]
        r["function_source_ids"] = [DBT]
        r["notes"] = ("Independent statutory regulator on the DBT List of UK regulators; "
                      "off-register (not on the GOV.UK Organisations API). Classified "
                      "other_body pending an ONS-sourced classification pass (decision #12: "
                      "'regulator' is a function, not a body_type); founding statute is a "
                      "Spiral 2 citation.")
        records.append(r)

    written, skipped = [], []
    for r in records:
        path = os.path.join(BODIES, r["body_id"] + ".json")
        if os.path.exists(path):
            skipped.append(r["body_id"]); continue
        if not args.dry_run:
            write_json(path, r)
        written.append(r["body_id"])

    print("--- ingest_offregister summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print("chartered (royal_charter_body):   {}".format(len(CHARTERED)))
    print("statutory regulators (other_body): {}".format(len(STATUTORY_REGULATORS)))
    print("records written (new):            {}".format(len(written)))
    print("skipped (already present):        {}  {}".format(len(skipped), skipped or ""))


if __name__ == "__main__":
    main()
