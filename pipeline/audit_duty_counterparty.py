#!/usr/bin/env python3
"""Populate `owed_to_*` on Duty records — the counterparty a duty runs to.

One job. Background (sponsor review, 2026-07-20): the register had been built out on the
VETO axis while duties stayed second-class. A Veto carries `blocks_body_id` and
`blocks_power_id`, so "who can block X?" is a traversal. A Duty carried only free-text
`beneficiary_or_object`, so "which bodies must legally be consulted before X?" — use case
U13, and the middle third of U1 ("statutory vetoes, CONSULTATION DUTIES and JR exposure") —
could not be answered by query at all. A consultation duty is a relationship between two
actors, exactly as traversable as a veto, and it was being stored as prose.

This fills the field ONLY where the record's own text names a state actor. Most duties in
the tranche run to consumers, the public or a private company: those stay null and draw no
edge, on the same principle the sponsor set for vetoes — the map models what the state does
to itself, and the card carries the rest.

Re-runnable and idempotent.

    py -3 pipeline/audit_duty_counterparty.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store

# duty_id -> (owed_to_body_id, note). None means "no state counterparty" and is a POSITIVE
# finding, recorded so a later pass does not re-litigate it.
COUNTERPARTY = {
    # The only duty in the tranche that runs to another state actor. s.24 requires the
    # Secretary of State or Ofwat to consult "the Welsh Ministers" before petitioning in
    # relation to a qualifying licensee with a supplementary authorisation.
    "duty-ofwat-wia1991-s24-consult": (
        "uk-state-body-welsh-government",
        "Statute names 'the Welsh Ministers' — the collective devolved executive, modelled "
        "here as the Welsh Government body. The two are not perfectly co-extensive (the "
        "Welsh Ministers are office-holders under the Government of Wales Act 2006); mapped "
        "to the body because no corresponding office node exists yet. Revisit if Welsh "
        "ministerial offices are modelled."),

    # Runs to consumers and the public, not to a state actor.
    "duty-ccw-wia1991-s27c-consumer-interests": (
        None, "Runs to consumers (disabled, chronically sick, pensionable age, low income, "
              "rural, household customers) — no state counterparty."),
    "duty-ofwat-wia1991-s2": (
        None, "A general duty conditioning how Ofwat exercises every power; its objects are "
              "consumers and the sector, not a state counterparty."),
    "duty-sos-defra-wia1991-s7-1": (
        None, "A continuity backstop owed to consumers in every area — no state counterparty."),
    # Run to the regulated company: a private party, outside the modelled state.
    "duty-ofwat-wia1991-s18": (
        None, "Enforcement duty directed at the contravening company/licensee — a private party."),
    "duty-ofwat-wia1991-s22a-notice": (
        None, "Notice and representations owed to the company facing the penalty — a private "
              "party. Note this is a consultation duty whose consultee is NOT a state body, "
              "which is why the type alone cannot imply an edge."),
}


def main():
    duties = store.load("duties")
    body_ids = {b["body_id"] for b in store.load("bodies")}
    linked = unlinked = 0
    for rec in duties:
        if rec["duty_id"] not in COUNTERPARTY:
            continue
        target, note = COUNTERPARTY[rec["duty_id"]]
        if target and target not in body_ids:
            sys.exit(f"FAIL {rec['duty_id']}: counterparty {target} is not a known body")
        rec["owed_to_body_id"] = target
        rec["owed_to_office_id"] = None
        rec["owed_to_holder_type"] = "body" if target else None
        existing = rec.get("notes") or ""
        if "Counterparty (2026-07-20)" not in existing:
            rec["notes"] = (existing + " Counterparty (2026-07-20): " + note).strip()
        linked += 1 if target else 0
        unlinked += 0 if target else 1

    store.save("duties", duties)
    print("--- duty counterparty pass ---")
    print(f"  duties reviewed:            {len(COUNTERPARTY)}")
    print(f"  with a state counterparty:  {linked}")
    print(f"  none (consumers/private):   {unlinked}")


if __name__ == "__main__":
    main()
