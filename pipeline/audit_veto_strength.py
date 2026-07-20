#!/usr/bin/env python3
"""Apply the 2026-07-20 veto-strength audit corrections, and log them for calibration.

One job. Background: every one of the 8 vetoes in the Water tranche carried
`strength: hard_stop` — the signature of a missing rubric rather than eight independent
judgements (vocab/veto_strength.json was a bare list of four terms with no definitions).

The audit ran in three tiers:
  Tier 1  internal coherence — `hard_stop` + `overridable: yes` is a self-contradiction;
          `hard_stop` + `overridable: unknown` is an unsupported grading. Now enforced in
          validate.py, so this class of defect fails the build from here on.
  Tier 2  override sweep — each veto re-read against its instrument AND the adjacent
          sections, since appeal routes rarely sit in the cited provision itself.
  Tier 3  blind re-grading by an independent agent that was not shown the existing labels.

Corrections below are Tier 2 findings, each cited. Re-runnable and idempotent.

    py -3 pipeline/audit_veto_strength.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALIBRATION = os.path.join(REPO, "calibration", "confidence_log.csv")
AUDIT_DATE = "2026-07-20"
REVIEWER = "build-agent (Tier 2 override sweep, primary sources)"

# veto_id -> (fields to set, calibration outcome, calibration note)
CORRECTIONS = {
    # The stated override (a drought order) was the WRONG MECHANISM: a drought order is a
    # separate power on separate grounds, not a route around a licence refusal. The real
    # override is the applicant's appeal to the Secretary of State — in an adjacent section.
    "veto-ea-wra1991-s38-abstraction-licence": (
        {"strength": "strong_delay",
         "overridable": "yes",
         "override_mechanism": "Appeal to the Secretary of State under Water Resources Act 1991 "
                               "s.43(1): an applicant 'dissatisfied with the decision of the "
                               "appropriate agency on the application' may by notice appeal.",
         "notes": "Strength corrected hard_stop -> strong_delay (audit 2026-07-20). The prior "
                  "override_mechanism cited a drought order under WRA 1991 Chapter III; that is a "
                  "separate power on separate grounds, not an override of a licence refusal."},
        "corrected", "hard_stop -> strong_delay; override re-cited to WRA s.43 appeal"),

    # Falsified at source: WCA 1981 s.28F gives a full appeal, and the Secretary of State may
    # direct Natural England to give consent. There is also a 4-month deemed-refusal clock —
    # a textbook strong_delay signature.
    "veto-natural-england-wca1981-s28e-consent": (
        {"strength": "strong_delay",
         "overridable": "yes",
         "override_mechanism": "Appeal to the Secretary of State under Wildlife and Countryside Act "
                               "1981 s.28F(5): the Secretary of State may 'direct Natural England to "
                               "give consent', or quash or vary its terms. If Natural England neither "
                               "gives nor refuses consent within four months the applicant may treat "
                               "it as refused and appeal. (The s.28E(3)(b)-(c) routes are Natural "
                               "England's own instruments — same holder, so not overrides.)",
         "notes": "Strength corrected hard_stop -> strong_delay and overridable unknown -> yes "
                  "(audit 2026-07-20), on the s.28F appeal route."},
        "corrected", "hard_stop -> strong_delay; overridable unknown -> yes (WCA s.28F appeal)"),

    # Falsified harder: under s.28H(4)-(5) a public body may proceed WITHOUT assent 28 days
    # after notice. Natural England therefore has no block here, so this arguably fails the
    # strict veto test entirely. Graded down and FLAGGED — re-typing is a sponsor decision,
    # not something to do silently, so the record is retained pending that call.
    "veto-natural-england-wca1981-s28h-assent": (
        {"strength": "procedural_risk",
         "overridable": "yes",
         "override_mechanism": "Wildlife and Countryside Act 1981 s.28H(4)-(5): the public body "
                               "'shall not carry out the operations unless the condition set out in "
                               "subsection (5) is satisfied', which is satisfied by notifying the "
                               "start date 'after the expiry of the period of 28 days'. Subsection "
                               "(6) then requires only that damage be minimised and the site restored.",
         "notes": "Strength hard_stop -> procedural_risk (audit 2026-07-20). Under s.28H(4)-(6) a "
                  "public body may proceed 28 days after notice regardless of assent, subject to "
                  "minimising damage and restoring the site. SPONSOR RULING 2026-07-20: RETAIN as a "
                  "Veto record at procedural_risk rather than re-typing it as a Duty or withdrawing "
                  "it. The independent blind re-grading reached procedural_risk on the same "
                  "reasoning, while noting advisory_only would also be defensible if the grading "
                  "keyed purely on the assent decision's effect rather than the mandatory duties "
                  "surrounding it."},
        "corrected", "hard_stop -> procedural_risk; retained as a veto per sponsor ruling"),

    # NOT a strength error: a general authorisation is the SAME holder (the Secretary of State)
    # consenting in class rather than case by case. That is not an override, so the veto stands
    # as a hard_stop and it is the overridable/mechanism fields that were wrong.
    "veto-sos-defra-wia1991-s6-1-b": (
        {"overridable": "no",
         "override_mechanism": None,
         "notes": "overridable corrected yes -> no (audit 2026-07-20). A general authorisation "
                  "under s.6(1)(b) is given BY the Secretary of State, so it is the same holder "
                  "consenting in class, not a route around the consent (same-holder rule, "
                  "vocab/veto_strength.json v0.2). Strength hard_stop confirmed."},
        "corrected", "strength confirmed; overridable yes -> no (same-holder rule)"),

    "veto-sos-defra-wia1991-s7-2-b": (
        {"overridable": "no",
         "override_mechanism": None,
         "notes": "overridable corrected yes -> no (audit 2026-07-20). A general authorisation "
                  "under s.7(2)(b) is given BY the Secretary of State, so it is the same holder "
                  "consenting in class, not a route around the consent (same-holder rule, "
                  "vocab/veto_strength.json v0.2). Strength hard_stop confirmed."},
        "corrected", "strength confirmed; overridable yes -> no (same-holder rule)"),
}

# Swept and confirmed unchanged — recorded so the calibration log shows the hits, not just
# the misses (a log of corrections alone would overstate the error rate).
CONFIRMED = {
    "veto-cma-wia1991-s16a-veto":
        "hard_stop confirmed: WIA 1991 s.16A(1) — 'the Authority shall comply with any such "
        "direction' — with no appeal for Ofwat. s.16A(2) only lets the Secretary of State extend "
        "the CMA's four-week window on the CMA's own application, and s.16(4C) confirms Ofwat may "
        "proceed only if the four weeks elapse with no direction.",
    "veto-hm-treasury-wia1991-s153":
        "hard_stop confirmed: 'with the consent of the Treasury' gates grants and loans (s.153(1)), "
        "indemnities (s.153(1A)), guarantees (s.153(2)) and repayment terms (s.153(3)), with no "
        "exception, general authorisation, delegation or class consent anywhere in the section.",
    "veto-sos-defra-wia1991-s24":
        "hard_stop confirmed: Ofwat cannot petition under s.24(1)(b) without the Secretary of "
        "State's consent. The Secretary of State's own power to petition under s.24(1)(a) is the "
        "same holder acting directly, not an override available to Ofwat.",
}

# Tier 3: an independent agent re-graded all eight from primary sources WITHOUT being shown
# the existing labels. It agreed with every corrected grading above (8/8), and independently
# derived both the same-holder rule (items 4-5) and the finding that WCA s.28H is not a veto
# at all. Convergent, not self-confirming — so the records rise to `machine_verified` (Annex
# A10: passed the schema-blind eval, no human check yet). High-impact vetoes still need a
# human double-check before publication.
BLIND_EVAL = ("Re-graded 2026-07-20 by an independent agent blind to the existing labels "
              "(schema-blind eval, Annex A10); agreed 8/8 with the post-audit gradings.")


def main():
    vetoes = store.load("vetoes")
    changed, rows = 0, []
    for rec in vetoes:
        vid = rec["veto_id"]
        if vid in CORRECTIONS:
            fields, outcome, note = CORRECTIONS[vid]
            before = {k: rec.get(k) for k in fields}
            rec.update(fields)
            if before != fields:
                changed += 1
            rows.append((rec["extraction"]["confidence"], outcome, vid, note))
        elif vid in CONFIRMED:
            rows.append((rec["extraction"]["confidence"], "confirmed", vid, CONFIRMED[vid]))
        else:
            continue
        # Tier 3 passed for every swept record — raise the assurance tier honestly.
        rec["verification"]["verification_status"] = "machine_verified"
        rec["verification"]["verification_notes"] = BLIND_EVAL
        rec["verification"]["verified_date"] = AUDIT_DATE

    store.save("vetoes", vetoes)

    # Calibration log (A9.3): every verification logged as (predicted_confidence, outcome).
    # This layer had never been logged — which is precisely why the 8/8 went unnoticed.
    existing = set()
    if os.path.exists(CALIBRATION):
        with open(CALIBRATION, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                existing.add((r["record_id"], r["date"]))
    with open(CALIBRATION, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        for conf, outcome, vid, note in rows:
            if (vid, AUDIT_DATE) in existing:
                continue
            w.writerow([conf, outcome, vid, REVIEWER, AUDIT_DATE, note])

    corrected = sum(1 for _, o, _, _ in rows if o == "corrected")
    print("--- veto strength audit ---")
    print(f"  vetoes swept:   {len(rows)}")
    print(f"  corrected:      {corrected}")
    print(f"  confirmed:      {len(rows) - corrected}")
    print(f"  records changed:{changed}")
    print(f"  logged to:      {os.path.relpath(CALIBRATION, REPO)}")


if __name__ == "__main__":
    main()
