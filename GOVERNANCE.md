# Governance and data standard

This document is the public statement of the rules WhoGoverns is built to. It is the
standard every record in this repository is held to: how sources are chosen, how records are
verified, what "published" means, and how the data is kept independent and auditable. It is a
digest — the project maintains fuller internal build documentation, but nothing in that
documentation overrides or contradicts what is stated here, and this file is authoritative for
anyone reading, reusing or checking the data.

## Independence

WhoGoverns is built entirely from public, official primary sources and published under a
non-partisan framing. It is not affiliated with, or endorsed by, HM Government. A model of the
state is only useful if its findings — especially its veto flags — are trusted as neutral, so
the data and its documentation carry no party framing, and no political programme is expressed
or endorsed anywhere in the dataset.

## The five core rules

1. **No uncited legal authority.** Every legally meaningful record points to a specific provision.
2. **No unvalidated record.** Every record passes schema validation before it enters the dataset.
3. **No uncontrolled vocabulary drift.** Classifications come from versioned controlled vocabularies, not free text.
4. **No publication without verification.** No record is presented as verified until a human has checked it against its source.
5. **No analysis inside the raw data layer.** Mechanical facts and value judgements are kept strictly separate.

## Design principles

- **Primary-source first.** No published record rests on a third-party compilation where a
  primary source exists. Third-party sources are used only for discovery, comparison and
  gap-finding — never as the evidential basis for a published record.
- **Citation or it does not exist.** Every power, duty, veto, budget and staffing figure links
  to the specific source it came from. For legal records the target is a specific provision of
  an Act or statutory instrument; section-level citation is acceptable early but marked as
  lower precision.
- **Current-law default.** The default legal view is current, in-force law, with legal status
  recorded (`current | repealed | prospective | historical`).
- **Do not infer beyond the source.** The extractor may classify what a source says; it may not
  invent authority a source does not state. A body that looks influential but holds no explicit
  legal power belongs in an analytical note, not the powers register.
- **One provision, one canonical record.** A single provision that reads as both (say) a power
  and a veto yields one canonical record plus explicitly-derived records — never two independent
  extractions of the same text.
- **Boring by design.** JSON records validated against JSON Schema, plain-Python build scripts,
  a compile step to a graph file and SQLite, Git for history. Legible and editable cold by a new
  contributor; no frameworks, no clever abstractions.
- **Separation of data, interpretation and products.** Raw sources, structured records,
  analytical outputs and public-facing products are distinct layers. Analytical claims never
  write back into the core dataset.

## Source hierarchy

When sources conflict, the highest-ranking relevant source wins.

- **Powers, duties, vetoes:** current consolidated legislation (legislation.gov.uk) →
  commencement/amendment instruments → departmental directions and delegation schemes →
  framework documents → annual reports (evidence of function, not authority) → guidance →
  third-party (discovery only).
- **Body existence and classification:** GOV.UK Organisations API → Cabinet Office Public
  Bodies → departmental annual reports → framework documents → legislation.
- **Budget:** HM Treasury OSCAR outturn → departmental accounts → body accounts → Estimates.
- **Staffing:** Civil Service Statistics → body annual reports → departmental reports →
  transparency returns.

## Verification lifecycle

Every record carries a `record_status` that moves through a fixed lifecycle:

```
draft → extracted → single_checked → double_checked → published
```

with terminal states `rejected`, `deprecated`, `superseded`, `needs_schema_decision`.

**What the current statuses mean for a reader.** Records marked `extracted` are
machine-extracted from an official source and **awaiting human verification** — they are
present so the dataset is useful and inspectable, but they have not yet been checked by a
person. Do not treat an `extracted` record as verified. Verification happens at defined review
gates, not continuously, so a whole tranche can sit at `extracted` until its gate is reached.

### Minimum publication standard

A record may be presented as verified only when all of the following hold:

1. the cited source opens;
2. the citation points to the relevant provision;
3. the plain-English summary matches the source;
4. the classification is defensible;
5. the legal status is not obviously wrong;
6. the body ID is valid;
7. the source ID is valid;
8. the record passes JSON Schema validation.

High-impact records — contentious classifications, high-impact vetoes, and any launch or
headline examples — require a second, independent check before publication.

## Currency

Law changes after extraction, and records rot silently unless currency is managed. Every legal
source stores the point-in-time version date it was read at; a periodic currency check diffs
stored versions against the live text and flags affected records for review. No record older
than twelve months since its last review is cited in a published analytical output without a
fresh currency check.

## Build discipline

Development runs in complete cycles ("spirals"), each ending in a working, tested product with
explicit exit criteria: structure first, statutory powers second. Every working session ends in
a valid, committed state — schema-valid records, passing validation, an explainable commit — so
the repository is never left broken.

## Corrections

WhoGoverns is built from the public record and will contain errors. Corrections against a
primary source are welcome via the repository's issue tracker; a record challenged against its
cited source is re-checked and, if wrong, corrected or withdrawn with its history preserved in
version control.
