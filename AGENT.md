# AGENT.md — WhoGoverns build agent boot digest

You are contributing to **WhoGoverns** (working name "The State Machine"), an open, machine-readable model of the UK state. Load this at the start of every session. It is the operational digest of Annex A; Annex A is authoritative and consulted on demand. A digest that drifts from the annex — or from the live schemas/vocab — is a defect. Regenerate this file whenever they change. **Reflects Annex A v0.4 as amended, and the schema/vocab state at 2026-07-21 (Spiral 2 Water tranche: operative layer ACTIVE and COMPILED to the map).**

## The five core rules (Annex A19)
1. No uncited legal authority.
2. No unvalidated record.
3. No uncontrolled vocabulary drift.
4. No publication without verification.
5. No analysis inside the raw data layer.

## Sponsor discipline
Official / primary sources only. Commit nothing until official information is surfaced. Never use tacit knowledge. Structural and statutory-powers modelling from public sources does not engage the PfB recusal.

## Source hierarchy (top wins)
- Powers/duties/vetoes: current consolidated legislation (legislation.gov.uk) > commencement/amendment SIs > directions/delegation schemes > framework docs > annual reports > guidance > third-party (discovery only).
- Body existence/classification: GOV.UK Organisations API > Cabinet Office Public Bodies > departmental annual reports > framework docs > legislation.
- Budget: HMT OSCAR outturn > departmental accounts > body accounts > Estimates.
- Staffing: Civil Service Statistics > body annual reports > departmental reports > transparency returns.

## ID conventions
- Body: `uk-state-body-{slug}` · Source: `source-{source_type}-{short_title}-{year}` (datasets: `source-official-dataset-{slug}`)
- Power/Duty/Veto: `{type}-{body_slug}-{source_slug}-{provision_slug}-{seq}`
- Every legal record carries `provision_key` (shared per provision) and `derived_from_record_id` (null on the canonical record). Two canonical records may not share a `provision_key` (A2.5).

## Storage and access
**ONE ARRAY FILE PER TYPE** (`data/<type>.json`). All access via `pipeline/store.py` (`load`/`load_map`/`save`/`upsert`, keyed by each type's PK). Raw API/legislation caches under `data/sources/raw/` stay individual files (gitignored). Never add per-record files or re-glob `data/<folder>/*.json` — read/write via store. `py -3 validate.py` is the gate (fails closed); `py -3 pipeline/compile.py` builds `compiled/graph.json` (the map contract) + `compiled/state_machine.sqlite` (the query mirror).

## Structural layer (Spiral 1 — populated)
Body, Source, Office, PersonRole, Relationship + Budget (HMT OSCAR 2024-25) + Staffing (CSS 2025). Department "Overall" staffing rows = GROUP total (incl. agencies) with a double-count disclaimer; agencies also held separately — never sum a department with its agencies. OSCAR/CSS matched by EXACT normalised name or safe containment, never fuzzy.

`body_type` v0.2 (10 terms): ministerial_department, non_ministerial_department, executive_agency, division_directorate, executive_ndpb, advisory_ndpb, tribunal, public_corporation, royal_charter_body, other_body. No `regulator` (regulation is a function). `royal_charter_body` is a separate Privy Council tranche, NOT the GOV.UK API. Unmapped `format` → `other_body` + review flag, never dropped.

**Functional axis.** `functions[]` (+ `function_source_ids[]`) on Body, orthogonal to `body_type`. Vocab `functions.json` **v0.2** (adds `judicial`, held separately from `tribunal_justice`). SOURCED population: `regulation` (94 bodies, DBT list) and `judicial` (courts, from their constituting Act). Never tag from tacit knowledge — source it or leave it. (A DERIVED functional read also exists — see compile below — kept separate from this sourced field.)

**Officials are not a body_type.** Office is a first-class, power-holding node (a corporation sole). Modelling test (#28): power **vested in the post** → an Office node; power **delegated "on behalf of" the parent** → parent holder + function tag, no node (e.g. DWI). Render offices as markers WITHIN their host body, not peer rings.

## Powers layer (Spiral 2, Annex A6 — ACTIVE and COMPILED)
Six types via store: **powers, duties, vetoes** (operative) + **instruments, provisions, definitions** (the legislative graph). All powers-layer vocab now carries a **definition + operational test per term** (not bare lists): power_type **v0.3**, duty_type **v0.2**, veto_type **v0.3**, veto_strength **v0.2**, modality **v0.2**, legal_effect **v0.2**. READ the relevant vocab file before extracting — the bare-list era caused a whole tranche to misgrade.

- **Holder is polymorphic:** `holder_type` (`office`|`body`), `office_id` when an office holds it, `body_id` always set (holder or hosting department).
- **modality** is const per record type (`power`|`duty`|`veto`) — schema-enforced. may (power) vs must (duty) vs block (veto) is the extractor's single most important call. See modality.json boundary traps ("must be consulted" = duty; "have regard to" = not recorded; "may, with the consent of X" = a power + a derived veto).
- **power_basis** (required, #21): Spiral 2 sets `statutory` only. `prerogative`/`common_law`/`contractual` exist so a statutorily-thin domain reads "prerogative likely" not "no power"; not extracted yet. Conventions never recorded (#22). Retained-EU law and the ECHR enter as `statutory` (SIs; HRA 1998) — never a separate basis (#23).
- **power_type v0.3** added `adjudication` (a court/tribunal DECIDES — e.g. the High Court's SA order) and `application_to_court` (an actor ASKS a court — e.g. the SoS's s.24 petition). Kept separate deliberately: the delivery chain depends on which end of the interaction the holder sits. `other` requires a note; a recurring `other` is a vocab gap to raise.

### Veto = a DERIVED projection, never a primitive
- Emitted ONLY as the blocking projection of a consent/approval/concurrence/call-in/objection/licence-refusal/designation Power. `derived_from_record_id` (the canonical `power-*`) and `decision_affected` both REQUIRED.
- **`derived_from_record_id` = PROVENANCE** (the canonical power at the veto's OWN provision). **`blocks_record_id` + `blocks_record_type` (`power`|`duty`) = the TARGET** — what the veto obstructs, populated uniformly regardless of statutory shape. A veto can obstruct a **duty**, not only a power (WIA s.16A blocks the s.16 duty to modify). Validate checks this polymorphically.
- **Two statutory shapes, both correct** (derived in compile as `projection_shape`, never stored): *embedded consent* ("A may, with the consent of B, do X" — canonical record is A's power, derived_from points at the blocked actor) and *free-standing block* ("B may direct A not to…" — canonical record is B's own power, derived_from points at the holder).
- **STRICT veto test:** only a genuine statutory block. "must be consulted" → a consultation Duty. Soft influence / "have regard to" → not recorded. No "Responsibility" record type (#19) — decompose into powers+duties, or a derived heading.

### Grading a veto's strength (READ vocab/veto_strength.json v0.2 BEFORE GRADING)
An audit (2026-07-20) found all 8 Water vetoes graded `hard_stop` because the vocab had no criteria; 5 were wrong. Non-negotiable:
- **Override sweep before `hard_stop`.** Look for an appeal, deemed-consent/refusal clock, direction power, general authorisation, disapplication, or alternative route — **in adjacent sections too** (WCA s.28E's appeal is at s.28F).
- **Same-holder rule.** A route operated by the *same* holder (SoS giving a general authorisation instead of case-by-case consent) is NOT an override — stays `hard_stop`, `overridable: no`.
- **Wrong-mechanism trap.** A different power with a similar practical effect is not an override of *this* veto (a drought order is not a route round an abstraction-licence refusal).
- **Gateway test first.** Can the other actor lawfully proceed if the holder says no? If yes it is not a veto — a Duty, or nothing.
- `validate.py` FAILS the build on incoherent gradings (hard_stop+overridable:yes; hard_stop+unknown; strong_delay without a cited override) and on any vocab↔schema enum drift. The four strength terms are PROJECT vocabulary anchored to the mandatory/directory doctrine in JOYS 6th ed. §§2.57-2.60 (`source-guidance-judge-over-your-shoulder-2022`, methodological only — never cited as authority for a record).

### Duties carry a counterparty (U13)
`owed_to_body_id` / `owed_to_office_id` / `owed_to_holder_type` — the OTHER state actor a duty runs to (consult / notify / report / co-operate). Mirrors the veto `blocks_*` pattern; compile emits a **`must_consult`** edge. Null where the duty runs to consumers, the public or a private party — `beneficiary_or_object` carries that in free text, no edge (same rule as private-party vetoes).

### One provision, one canonical record; text not stored
All records from a provision share `provision_key`; canonical one has `derived_from_record_id` null. Provision node carries the point-in-time `url` + `version_date` + `content_hash` — **not the text**. `outstanding_effects=true` flags unapplied amendments (consolidation lag) — **currently only wired by hand; a systematic check is an open work item**.

### Assurance tiers (verification_status)
`unverified` → `machine_verified` (passed the schema-blind eval, no human) → `single_checked`/`double_checked` (human, A10). All 8 original Water vetoes are `machine_verified` after an independent blind re-grading (8/8 agreement); everything else is `unverified`. Nothing is human-checked yet. Machine-verified may publish WITH an honest reader-visible label; high-impact vetoes still need a human double-check (#3). Log every verification as (predicted_confidence, outcome) in `calibration/confidence_log.csv` — this layer was invisible to calibration until 2026-07-20; keep feeding it.

## Extraction scope and the breadcrumb method
- **Scope (#11):** first pass over a body = its founding Act + principal instruments (those conferring current operative powers), NOT a full statute sweep. "Complete" means "first-pass complete on the extracted sections" — say so; do not imply whole-statute coverage.
- **Breadcrumb mining (#27, now AUTOMATIC).** `fetch_legislation.py` populates `Provision.references` from the OPERATIVE text (CLML marks up `<Citation>` only in amendment commentary, so internal cross-refs are plain text and must be read out of the body). Any reference OUT of the held instruments is a lead to an adjacent instrument.
- **`pipeline/breadcrumbs.py` → `issues/breadcrumbs.md`** is the derived completeness register. Run it after any extraction. Detectors: untied veto (blocked party modelled, blocked record not), dangling reference (adjacent instrument not held), narrative stub (a note flags something left out), orphan instrument, **unmined provision** (fetched but no operative record — the false-assurance case). `CORRECTLY_UNMINED` suppresses provisions legitimately empty (amending / constitutive / private-holder), each with a stated reason. The stub COUNT is a real target — drive it down; it may rise honestly when new sections are fetched before extraction catches up.

## Compile → the map contract (`pipeline/compile.py`)
Each holder node gains an `operative` block (card-ready powers/duties/vetoes: citation, "since" year via provision→instrument, verification_status + confidence on the face, `outstanding_effects` badge). Office-held records mirror onto the host department as `office_operative`. Edges: **`can_veto`** (blocking, coloured by `blocker_kind`) and **`must_consult`** (duty counterparty). **The map models what the STATE does to itself** (#29): a veto/duty against a private party or unnamed class draws NO edge — it stays on the card, flagged `blocks_party_outside_state`, so the register never implies the drawable edges are the whole field. `blocker_kind` (regulatory/ministerial/fiscal/judicial) is DERIVED from sourced fields only — never a hand-kept list. `functions_derived` computes a functional read from the powers a body actually holds (regulation ← licence+enforcement/sanction; judicial ← adjudication; etc.), separate from the sourced `functions[]` — a derived view, never written into data (A2.8).

## Confidence (A9.3) — conservative
0.95–1.00 explicit text + exact citation · 0.80–0.94 minor interpretation · 0.60–0.79 classification uncertain · 0.40–0.59 uncertain · <0.40 no record, log issue. Nothing below 0.80 publishes without human review.

## Session output contract (A11.5)
End every session with: records created / changed / rejected; uncertainties; schema questions; sources used; recommended next action. Run `validate.py` AND `breadcrumbs.py`, then a small explainable commit (A11.6). No session leaves the repo broken.

## Do not
Confuse influence with legal authority; guidance with law; a consultation duty with a veto. Invent vocabulary (propose a term when `other` recurs). Write analysis into `/data`. Imply whole-statute coverage from a first-pass tranche. Draw a private-party block as a state-to-state edge.
