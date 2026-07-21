# Build-out strategy — how the powers register grows

**Version:** 0.1 (2026-07-21) · **Status:** active from Spiral 2 · **Owner:** handoff owner
**Parents:** Project Plan v0.5 (§5 Spiral 2; decisions #10, #11, #24, #25, #27, #33); Annex A (A9, A11.4)

This note fixes *how* the register is grown from a single calibration domain (Water) to
whole-of-state coverage — the question of what to extract next, in what order, and how to
know a domain is done. It composes the sponsor's four candidate approaches (2026-07-21) into
one method, discarding one, and pins the metric that runs it.

## The empirical finding that decides it

Following an in-domain breadcrumb (the CMA licence-veto chain, s.17K → s.17O/17P) and
measuring, 2026-07-21:

| | before | after fetching 4 sections |
|---|---|---|
| in-domain dangling refs (un-fetched sections of Acts we hold) | 65 | 63 |
| cross-domain dangling refs | 32 | 36 |
| **distinct un-held INSTRUMENTS** | **16** | **16** |

The raw reference count churns (you resolve some, each new section adds its own), but the
number that matters — **distinct un-held instruments** — held flat. New references pointed
back at Acts already in the queue, not new ones. **A policy domain's adjacent-instrument
footprint is finite and converges; the water domain is essentially mapped at ~16 instruments.**
Cross-domain references (to general competition / company / insolvency law) are where the
fan-out lives, because that general law is shared by *every* domain.

This is the load-bearing fact: **in-domain breadcrumbs self-limit; cross-domain breadcrumbs
would explode if chased per-domain.**

## The method: theme-seeded blooms, catalogued, run to convergence

Three of the sponsor's four options are not rivals — they compose:

1. **Theme / SoS remit picks the seed** (sponsor option 3; plan decision #10, domain-first).
   The unit is a **policy domain** (water, energy/planning, competition, health…), because a
   domain's Acts cross-reference each other densely and reach shared general law only at the
   edges — exactly the convergence shape measured above. An SoS remit is a coarser folder that
   holds several domains; the domain is the sharper unit.
2. **Breadcrumb bloom is the growth engine** inside a seed (sponsor option 1, the "bacterial
   colony on a petri dish"). Follow `Provision.references` outward, extracting blocker-bearing
   provisions a decision actually reaches (decision #27), until the domain's distinct-instrument
   count stops rising. That flat count is the "colony has filled its plate" signal.
3. **The "Over Ruled" 115-Act list is the catalogue/map** (sponsor option 4), used STRICTLY as
   discovery per decision #24 — never imported. It answers "which seeds remain, and which Acts
   should a domain have reached?", so seeding has no blind spots and a domain's coverage can be
   cross-checked. It does not replace the bloom.

**Dropped: ring traversal** (sponsor option 2 — go round Ofwat's ring). The ring is
`body_type` (constitutional *form*); Ofwat's ring-neighbours (Ofgem, ORR, HMRC, the CMA) sit
in unrelated domains. Traversing form gives shallow coverage of many disconnected things and
never completes a delivery chain. Form is the wrong axis; function/domain is the right one.

## The shared general-law spine — extracted ONCE, not per domain

The convergence finding has a direct consequence. The ~16 cross-domain instruments the water
breadcrumbs reach — the Enterprise Act 2002, Competition Act 1998, Companies Act 1985/1989,
Insolvency Act 1986, FSMA 2000 — are **general law referenced by every regulated domain**.
Extracting them repeatedly, a few sections at a time, from each domain would re-create the
s.16 problem (a veto whose target lives in an un-fetched section) at scale.

**Rule: the cross-cutting statutory spine is extracted once, deliberately, as its own tranche,
scoped to the provisions the breadcrumb register actually reaches** (decision #11 still binds —
not whole Acts). Every later domain then inherits it: its references to `enterprise-act-2002`
resolve instead of dangling. The breadcrumb register's *cross-domain* count is the trigger and
the scope for this tranche.

## The metric: distinct un-held instruments per domain

Coverage is measured, not felt (plan §5; Annex A11.4). The standing numbers, from
`issues/breadcrumbs.md` (regenerated every session by `pipeline/breadcrumbs.py`):

- **unmined provisions** — fetched but never extracted (the false-assurance case). Drive to 0
  within a domain before calling it first-pass complete.
- **distinct un-held instruments** — the convergence gauge. When it stops rising for a domain,
  the domain's adjacent-instrument footprint is mapped: first-pass complete.
- **narrative stubs** — deliberately-deferred sub-provisions; each is a known debt, not a miss.

A domain is **first-pass complete** when its unmined-provision count is 0 and its
distinct-instrument count has gone flat across a bloom round. "Complete" always means
"first-pass complete on the extracted sections", never "whole-statute" (decision #11).

## Sequence

1. **Now: the cross-cutting competition/company-law spine** (Enterprise Act 2002, Competition
   Act 1998, Companies Act, Insolvency Act, FSMA 2000 — the provisions the water register
   reaches). Extract once; every future domain inherits it.
2. **Then: Energy / planning** as Tranche A (plan decision #10 — Energy next after Water), the
   densest veto field, bloomed to convergence.
3. **Then** outward by domain, catalogued against the 115-Act list, each bloomed to a flat
   instrument count, the shared spine reused rather than re-touched.
4. Retrodiction remains the completeness *audit* at the spiral exits (the decision-first half;
   the breadcrumb register is the automatic half).

## Open (sponsor)

- **#34** (duplication/conflict flag) rides on this: once multiple domains share the spine, the
  same authority *will* be reached from different provisions, and conflicting duties *will*
  co-occur — surface them (the U15 seam), never silently dedupe.
