#!/usr/bin/env python3
"""Report open breadcrumb stubs — the known-unknowns the model has pointed at itself.

One job. Decision #27 (breadcrumb / cross-reference mining) is how the net widens without
sweeping the whole statute book: when a provision or record names something OUTSIDE what we
hold, that is a lead. The method only works if the leads are TRACKED — otherwise a stub is
closed by whoever happens to notice it, and completeness is a feeling rather than a number.
WIA 1991 s.16 was exactly this: s.16A (the CMA's veto) was extracted without s.16 (the duty
it blocks), and it surfaced only because someone went looking for the veto's target.

DERIVED, not hand-maintained. A hand-kept list would drift out of date the moment a stub was
closed; this reads the records every time, so a closed stub disappears on its own. Four
detectors, each a real completeness gap:

  1. UNTIED VETO      — a veto whose blocked party IS modelled but whose blocked record is
                        not. The chain traverses body-to-body instead of record-to-record.
  2. DANGLING REF     — a Provision.references entry pointing at a provision we do not hold
                        (the classic adjacent-instrument lead).
  3. NARRATIVE STUB   — a record whose own notes flag something deliberately not extracted.
                        Convention: write "breadcrumb stub" or "NOT separately extracted".
  4. ORPHAN INSTRUMENT— an instrument registered with no provisions extracted from it.

Writes issues/breadcrumbs.md and prints a summary. Read-only over data/.

    py -3 pipeline/breadcrumbs.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "issues", "breadcrumbs.md")
STUB_MARKERS = ("breadcrumb stub", "not separately extracted", "not yet extracted",
                "have not extracted", "extraction work item")

# A provision can be legitimately unmined for three reasons, and a register that flags those
# forever is noise rather than a completeness measure. Each entry needs a stated reason, so
# the suppression is auditable and not just a way of making the number go down.
#
#   AMENDING     — the provision's operative content lives in the Act it amends, and is
#                  extracted THERE. Re-minting it would duplicate the same law twice.
#   CONSTITUTIVE — establishes or defines a body or term; confers no power or duty.
#   PRIVATE      — imposes the obligation on a private party (a water undertaker, an
#                  abstractor), not on a body or office in the model. Real law, but its
#                  holder is outside what the register models.
CORRECTLY_UNMINED = {
    "water-act-2014-s22":
        "AMENDING — inserts the resilience objective into WIA 1991 s.2(2A)(e)/(2DA); the "
        "operative duty is extracted from the consolidated WIA s.2 text, citing this as "
        "amending provenance.",
    "water-industry-act-1991-s27a":
        "CONSTITUTIVE — establishes the Consumer Council for Water and its committees; the "
        "Council's operative duties are extracted from s.27C.",
    "water-special-measures-act-2025-s14":
        "AMENDING — inserts WIA 1991 s.12J (the SoS's power to modify appointment conditions to "
        "recover special-administration losses); the operative power is extracted from the "
        "consolidated WIA s.12J (power-sos-defra-wia1991-s12j), citing WSMA 2025 as provenance.",
    "water-industry-act-1991-s37":
        "PRIVATE — the general duty to maintain an efficient and economical water supply "
        "system falls on the water UNDERTAKER, a private company, not on a modelled body. "
        "Ofwat's enforcement of it is held separately at s.18.",
    "water-resources-act-1991-s24":
        "PRIVATE — the restriction on abstraction binds any PERSON abstracting water. The "
        "state-side records are the Environment Agency's licensing power (s.38) and its "
        "enforcement power (s.25A), both held.",
    # The licensing regime's definitional scaffolding. Fetched because ss.17A+ were fetched as
    # a block, and they matter for INTERPRETING the operative sections — but they confer
    # nothing, so flagging them forever would bury the sections that do.
    "water-industry-act-1991-s17b":
        "CONSTITUTIVE — defines 'supply system' for the licensing regime; confers no power.",
    "water-industry-act-1991-s17c":
        "CONSTITUTIVE — defines 'household premises'; confers no power.",
    "water-industry-act-1991-s17d":
        "CONSTITUTIVE — defines the threshold requirement; confers no power.",
    "water-industry-act-1991-s17q":
        "CONSTITUTIVE — supplementary provision to s.17P; confers no free-standing power.",
    "water-industry-act-1991-s17l":
        "PROCEDURAL — time limits on s.17K references; confers no operative power.",
    "water-industry-act-1991-s17m":
        "CROSS-REFERRING — applies the Enterprise Act 2002 investigation powers (ss.109-116) to "
        "s.17K references; the operative power is the Enterprise Act's s.109 (now extracted).",
    # Competition-law spine: the substantive prohibitions bind undertakings (private parties);
    # the state-side records are the enforcement powers (CA1998 s.54 concurrency, EA2002 powers).
    "competition-act-1998-s2":
        "PRIVATE — the Chapter I prohibition binds UNDERTAKINGS, not the state; enforced via the "
        "s.54 concurrency power (power-ofwat-competition1998-s54) and the CMA.",
    "competition-act-1998-s18":
        "PRIVATE — the Chapter II prohibition (abuse of dominance) binds UNDERTAKINGS; enforced "
        "via s.54 concurrency and the CMA.",
    # s.124A public-interest-winding-up trigger instruments — registered, future domain.
    "companies-act-1985-s431":
        "REGISTERED-NOT-EXTRACTED — a s.124A winding-up trigger (Part XIV company investigations); "
        "belongs to a future corporate-enforcement domain, not the competition spine.",
    "financial-services-and-markets-act-2000-s167":
        "REGISTERED-NOT-EXTRACTED — a s.124A trigger (FCA/inspector reports); future domain.",
    "criminal-justice-act-1987-s2":
        "REGISTERED-NOT-EXTRACTED — a s.124A trigger (SFO fraud investigations); future domain.",
}


def collect():
    powers = store.load("powers")
    duties = store.load("duties")
    vetoes = store.load("vetoes")
    provs = store.load("provisions")
    instruments = store.load("instruments")
    bodies = {b["body_id"]: b["name"] for b in store.load("bodies")}
    record_ids = {p["power_id"] for p in powers} | {d["duty_id"] for d in duties}
    prov_keys = {p["provision_key"] for p in provs}
    rows = []

    # 1. Vetoes that name a modelled blocked party but no blocked record.
    for v in vetoes:
        party = v.get("blocks_body_id") or v.get("blocks_office_id")
        if party and not v.get("blocks_record_id"):
            rows.append(("untied veto", v["veto_id"],
                         f"blocks {bodies.get(party, party)} but names no blocks_record_id — "
                         f"the obstructed power or duty is not extracted"))
        elif v.get("blocks_record_id") and v["blocks_record_id"] not in record_ids:
            rows.append(("untied veto", v["veto_id"],
                         f"blocks_record_id {v['blocks_record_id']} does not resolve"))

    # 2. Cross-references pointing out of what we hold.
    for p in provs:
        for ref in p.get("references") or []:
            target = ref if isinstance(ref, str) else (ref.get("provision_key") or "")
            if target and target not in prov_keys:
                rows.append(("dangling reference", p["provision_key"],
                             f"references {target}, which is not held"))

    # 3. Notes that flag something deliberately left out.
    for rec in powers + duties + vetoes:
        note = (rec.get("notes") or "").lower()
        if any(m in note for m in STUB_MARKERS):
            rid = rec.get("power_id") or rec.get("duty_id") or rec.get("veto_id")
            excerpt = re.sub(r"\s+", " ", (rec.get("notes") or "")).strip()
            rows.append(("narrative stub", rid, excerpt[:300]))

    # 4. Instruments registered but never mined.
    mined = {p["instrument_id"] for p in provs}
    for i in instruments:
        if i["instrument_id"] not in mined:
            rows.append(("orphan instrument", i["instrument_id"],
                         f"{i.get('title')} registered with no provisions extracted"))

    # 5. UNMINED PROVISION — fetched, hashed and cited-ready, but no operative record was ever
    # extracted from it. This is the false-assurance case: the provision is in the model, so a
    # body looks covered, while the powers and duties that provision confers are simply absent.
    # A section-level provision counts as mined if a paragraph-level record cites into it
    # (s.24 is mined by s24-1-a), so this is not tripped by granularity.
    cited = {r["provision_key"] for r in powers + duties + vetoes if r.get("provision_key")}
    for p in provs:
        pk = p["provision_key"]
        if pk in cited or any(c.startswith(pk + "-") for c in cited):
            continue
        if pk in CORRECTLY_UNMINED:
            continue
        rows.append(("unmined provision", pk,
                     f"{p.get('heading') or '(no heading)'} — fetched but no power, duty or "
                     f"veto extracted from it"))
    return rows


def main():
    rows = collect()
    by_kind = {}
    for kind, ref, detail in rows:
        by_kind.setdefault(kind, []).append((ref, detail))

    lines = ["# Breadcrumb register — open stubs", "",
             "**Generated by `pipeline/breadcrumbs.py`. Do not edit by hand — rerun it.**", "",
             "Decision #27's breadcrumb method widens the net without sweeping the whole statute "
             "book, but it only works if the leads are tracked. This file is derived from the "
             "records every time it runs, so a stub that has been closed disappears by itself "
             "and the count is a real completeness measure rather than a feeling.", "",
             f"**{len(rows)} open stub(s).**", "",
             f"{len(CORRECTLY_UNMINED)} provision(s) are suppressed as CORRECTLY unmined "
             "(amending, constitutive, or binding a private party) — see `CORRECTLY_UNMINED` "
             "in the script for the reason recorded against each.", ""]
    for kind in sorted(by_kind):
        lines.append(f"## {kind} ({len(by_kind[kind])})")
        lines.append("")
        for ref, detail in sorted(by_kind[kind]):
            lines.append(f"- **`{ref}`** — {detail}")
        lines.append("")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("--- breadcrumb register ---")
    for kind in sorted(by_kind):
        print(f"  {kind:22} {len(by_kind[kind])}")
    print(f"  {'TOTAL':22} {len(rows)}")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
