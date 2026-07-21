# Build-out strategy — how the powers register grows

**Version:** 0.2 (2026-07-21; consolidates v0.1 + the two 2026-07-21 additions) · **Status:** active from Spiral 2
**Parents:** Project Plan v0.5 (§5, §6.1; decisions #2, #10, #11, #24, #27, #33, #37); Annex A (A9, A11.4)

How the register goes from one calibration domain (Water) to whole-of-state coverage: what to
extract next, in what order, and how to know a domain is done. One rule governs everything
below, so it leads.

## The one rule: DATA is systematic; the CHAIN is goal-directed

- **Domain EXTRACTION is systematic and decision-agnostic.** A domain is bloomed from its seed
  instrument's own operative structure plus its breadcrumbs, to breadcrumb-exhaustion — NOT
  scoped to the provisions one target case needs. The value of the Water tranche (the 8/8
  strength audit, the s.16 breadcrumb, the licence-veto chain) came *because* the Act's
  structure drove the extraction and surfaced gaps no goal could have predicted.
- **CHAIN assembly is goal-directed by nature** (a DeliveryChain / fusion / retrodiction traces
  one decision through the register) — but it runs *against a completed domain*, in `/analysis`,
  as the completeness AUDIT, never as the extraction driver.
- **The test:** if you can only name the next provision to extract from "what my target case
  needs" — not from the domain's own structure or a breadcrumb — you have slipped into
  goal-directed extraction. Stop and return to the bloom. (This is the drift caught 2026-07-21:
  the "reservoir DCO decision-spine" was extracted as if it were the planning bloom; the fix is
  to bloom the DCO regime systematically, then retrodict the reservoir against it.)

## The method: theme-seeded blooms, catalogued, run to convergence

Three moves, composed (they are not rivals):

1. **A policy domain is the seed** (plan decision #10, domain-first). A domain's Acts
   cross-reference each other densely and reach shared general law only at the edges — which is
   why it converges (below). An SoS remit is a coarser folder holding several domains; the
   domain is the sharper unit. Ring-by-`body_type` was rejected — form is the wrong axis.
2. **The breadcrumb bloom is the growth engine** inside a seed (the "petri-dish colony"). Follow
   `Provision.references` outward, extracting blocker-bearing provisions (decision #27), until
   the domain's distinct-instrument count stops rising.
3. **The "Over Ruled" 115-Act list is the catalogue** (discovery only, #24 — never imported): it
   says which seeds remain and lets a domain's coverage be cross-checked. It does not replace
   the bloom.

## Why domains converge — the measured finding

Following an in-domain breadcrumb and measuring (2026-07-21): the raw reference count churns
(you resolve some, each new section adds its own) but **distinct un-held instruments held flat
at ~16** — new references pointed back at Acts already in the queue. A domain's
adjacent-instrument footprint is finite and converges. The fan-out lives only in the general
law shared by every domain, which is why the spine is extracted once:

## The shared general-law spine — extracted ONCE

The general law every regulated domain reaches (Enterprise Act 2002, Competition Act 1998,
Companies/Insolvency Acts, FSMA 2000) is extracted once as its own tranche, scoped to the
reached provisions (#11), and every later domain inherits it — so a reference to
`enterprise-act-2002` resolves instead of dangling. Re-touching it per domain recreates the
missing-target (s.16) problem at scale. Its onward references are mostly *constitutive* (Acts
that create/define bodies), not blocker-bearing, so the spine bloom stops at the blocker layer.

## The metric: `issues/breadcrumbs.md`, regenerated every session (A11.4)

- **unmined provisions** — fetched but never extracted (the false-assurance case). Drive to 0
  before calling a domain first-pass complete.
- **distinct un-held instruments** — the convergence gauge. Flat = footprint mapped.
- **narrative stubs / orphan instruments** — known, deliberate debts, not misses.

A domain is **first-pass complete** when unmined = 0 and the instrument count has gone flat.
"Complete" always means "first-pass complete on the extracted sections", never "whole-statute"
(#11).

## Complete-body presentation gate

The derived role/responsibility card (functions sourced + derived; responsibility areas
grouped from the cited powers/duties, per #19) is built for a body **only when its breadcrumb
is exhausted**. Presenting a body as "complete" earlier is the false-assurance failure the
register exists to prevent. **Guard:** the view is computed, not authored — it recomputes in
`compile.py` when a later cross-domain breadcrumb adds powers — so "complete" means "as at this
compile", and the human verification pass must re-run.

## Sequence

1. **Done:** the competition/company-law spine (once).
2. **In progress:** Planning / infrastructure (Tranche A). Bloom the DCO regime systematically
   to convergence; the reservoir is the retrodiction against it (#37), not the extraction
   driver.
3. **Then** outward by domain, catalogued against the 115-Act list, the spine reused.
4. **Frontier (deferred):** convention / prerogative / international obligations — the last of
   these is captured by citing the DOMESTIC implementing instrument (#23; the UK is dualist),
   not by modelling the treaty.

## Open (sponsor)

- **#34** rides on this: once domains share the spine, the same authority will be reached from
  different provisions and conflicting duties will co-occur — surface them (the U15 seam), never
  silently dedupe.
