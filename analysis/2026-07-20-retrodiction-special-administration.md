# Retrodiction scrub — Water Special Administration

**Decision traced:** an incoming government seeks to place a failing water company (the Thames
Water situation) into **special administration** — the direct public-control lever short of
statutory renationalisation.

**Method (binding constraint, 2026-07-20):** the model must stand on its own. Every step below
is referenced to a record in `/data` by ID; gaps are surfaced from the records' **own** summary,
constraint and note fields (or from a provision node's cited text), never from outside knowledge.
This is the completeness AUDIT of the body-first extraction: where the trace needs something the
model can't supply, that is a gap, not a fact to import. `/analysis` references `/data`, never
writes to it (Annex A2.8).

---

## 1. The delivery chain, as the model represents it

**Trigger — who can petition, and who gates it**
- `power-sos-defra-wia1991-s24-1-a` — the Secretary of State may petition the High Court for a
  special administration order, on the s.24(2) grounds. Its summary calls it *"the direct
  public-control lever short of statutory renationalisation."*
- `power-ofwat-wia1991-s24-1-b` — Ofwat may petition, **but only with the SoS's consent**.
- `veto-sos-defra-wia1991-s24` — that consent, materialised: the SoS gates Ofwat's petition
  route (derived from the Ofwat power). So **either route runs through the SoS** — a clean,
  cited answer to "who can trigger this, and who can block the trigger."
- `duty-ofwat-wia1991-s24-consult` — before a Welsh-licensee petition, a duty to consult the
  Welsh Ministers.

**Precursor pressure / grounds**
- `power-ofwat-wia1991-s22a` — the financial-penalty power, noted in-record as *"the lever behind
  the … Thames Water penalty"*; `duty-ofwat-wia1991-s22a-notice` is its procedural gate.
- Grounds live in s.24(2), cited in the petition-power summaries (serious breach of a principal
  duty; inability to pay debts; etc.).

**Aftermath — replacement and exit**
- `duty-sos-defra-wia1991-s7-1` — the SoS **must** secure that every area always has an
  undertaker (continuity backstop — constrains how a company can be removed).
- `power-sos-defra-wia1991-s7-2-a` / `power-sos-defra-wia1991-s6-1-a` — terminate/vary an
  appointment, and appoint a replacement undertaker (with `veto-sos-defra-wia1991-s7-2-b` /
  `-s6-1-b` gating Ofwat's parallel routes).

**Verdict on this layer:** the model answers the **regulatory trigger-and-aftermath** question
end-to-end, with citations. Who can pull the lever (SoS or Ofwat), who gates it (SoS), what the
grounds are, what consultation is owed, and how the company is replaced afterwards — all present.

---

## 2. Gaps the trace surfaces — and how

The decision needs three layers the model does **not** hold. Note *how* each was found: two were
flagged by the model's own records (the breadcrumb method working); one was silent.

| Gap | Layer | How surfaced | Status |
|---|---|---|---|
| **The High Court makes the order** (s.24(1): the SoS/Ofwat *petition*, but the Court *decides* and can refuse) | Judicial | The summaries of `power-sos-defra-wia1991-s24-1-a` and `-s24-1-b` both name *"the High Court"* — the model points at the decision-maker it hasn't modelled | **Breadcrumb (in-model)** — courts exist as `other_body` nodes (decision #17), powers not extracted |
| **Insolvency Act 1986 machinery** (s.24(2)/(6) hang "unable to pay debts", winding-up and the SAR rules on the Insolvency Act) | Insolvency | The s.24 petition summaries cite *"inability to pay debts"*; the `water-industry-act-1991-s24` provision text cross-references the Insolvency Act 1986 (ss.123, 124A, 411) | **Breadcrumb (out-of-domain)** — Insolvency Act 1986 not in the model |
| **The special administrator + Treasury funding/indemnity** (a SAR installs an administrator to run the company; it needs government funding to operate) | Fiscal / operational | **Not stated in the statutory text** — no record or provision points to it | **Silent gap** — caught only by the decision-first trace / an external study |

---

## 3. What this proves about "is the net wide enough?"

- **The body-first register is strong on the statutory blocker layer** and answers the flagship
  "who can trigger / who can block" query with citations.
- **The breadcrumb method extends it correctly** to the adjacent instruments the decision touches
  — the model's own s.24 records name the **High Court** and the **Insolvency Act 1986**, so
  following those breadcrumbs closes those gaps without a whole-statute-book sweep.
- **But the fiscal gap is silent** — the Treasury funding a SAR needs is an operational reality,
  not in the statute, so neither the body-first sweep nor the breadcrumb trail reveals it. **Only
  the decision-first trace (or a reputable external study) surfaces it.** That is the honest limit
  of the extraction method, and the reason the retrodiction is the completeness gate: some
  blockers are practical/fiscal, not statutory.

**Net:** for special administration, the net is wide enough on the *statutory trigger* layer,
demonstrably widen-able (via breadcrumbs) on the *judicial* and *insolvency* layers, and **not yet
wide enough** on the *fiscal* layer — which the model itself cannot tell us, by construction.

---

## 4. Gap-closing work items (from this scrub)
1. **Court order-making power** — extract the High Court's power to make/refuse a special
   administration order (s.24(1)); begins the judicial-layer records (decision #17).
2. **Insolvency Act 1986** — register as an instrument; extract the SAR machinery it carries
   (via the s.24 breadcrumb).
3. **Treasury / funding** — add the fiscal actor; source it from the SAR regulations and any
   reputable study (see §5). This is the actor-type-checklist "Treasury" gap made concrete.
4. **Special administrator** — model the role (an Office under the vested-vs-delegated test, #28).

## 5. External validation (for the sponsor to obtain — outside the model)
The retrodiction exit test wants the model checked against an **independently documented** list of
blockers. Candidate reputable, pre-made sources on the water SAR (to be verified externally by the
sponsor — surfaced from general knowledge, not browsed, so treat as leads not facts):
- a **House of Commons Library** briefing on water-company finances / special administration
  (the Thames Water episode almost certainly generated one — the best neutral synthesis);
- **Defra**'s consultation and regulations on the water Special Administration Regime;
- the **National Audit Office** on Thames Water / water-sector regulation;
- the **Cunliffe Independent Water Commission (2025)** final report (already a project reference).
If such a study lists a blocker absent from §1, that is a new gap — feeding step 1's method.
