# WhoGoverns — project plan

A public, non-partisan statement of what this project is building, why, and in what order. It is
the fuller strategy behind the [README](../README.md). (This is the openly-publishable plan; the
project's internal governance and decision register are kept separately.)

## 1. Purpose

We are building, from scratch and from primary sources, an **open, machine-readable model of the
UK state**: every department, agency and arm's-length body, its budget, staffing, and — the layer
that exists nowhere today — its statutory powers, duties and veto points, all queryable down to the
section of the Act.

The result is a machine you can interrogate: trace any proposal's path through the state, enumerate
the vetoes, size a pledge to abolish arm's-length bodies, or audit a whole programme for government.

## 2. The gap

No dataset can currently answer the question at the centre of the project:

> **"Who can legally block this policy, and under what authority?"**

The state-capacity ecosystem (the Institute for Government, Re:State, the Future Governance Forum,
and others) produces diagnosis in prose; none of it produces a *model*. The best existing structural
map, [machineryofgovernment.uk](https://machineryofgovernment.uk), demonstrated demand for the
structural layer but covers statutory powers for only a handful of senior office-holders. The
**functional layer — powers, duties, vetoes at body level — does not exist anywhere**, and whoever
publishes a credible, cited, open version first sets the standard. Large-language-model extraction
now makes converting statutory prose into structured data tractable for the first time.

## 3. What you can do with it

The structural layer ships first; the powers register makes the deeper questions answerable.

| Use case | Delivered | What it answers |
|---|---|---|
| **Policy stress-testing** | Spiral 2 → 3 | Trace a proposal's delivery chain; enumerate statutory vetoes, consultation duties and judicial-review exposure, with citations. |
| **Veto-density index** | Spiral 2 → 3 | Count and weight the veto points between a ministerial decision and its delivery, per policy area — a publishable "levers of the state" metric. |
| **Day-one government packs** | Spiral 2 → 3 | For any office: what powers it holds, what needs primary legislation, what can be done by direction tomorrow. |
| **Machinery-of-government modelling** | Spiral 3 | Model a merger, abolition or cull of arm's-length bodies as a graph operation — which functions, duties and budgets move, and which duties have nowhere to land. |
| **Whole-programme audit** | Spiral 3 | Run an entire programme through the model at once: aggregate blockage map, legislative-load estimate, sequencing constraints. |
| **Duty-conflict register** | Spiral 3 / 5 | Pairs of statutory duties that pull against each other (e.g. a growth duty against an environmental duty) — explains gridlock with citations. |
| **Form-follows-function review** | Spiral 5 | A function inventory from the powers register; orphaned, duplicated and misfit functions surfaced against a published taxonomy. |
| **AI substrate (MCP)** | Spiral 4 | Expose the model as a queryable tool so AI assistants ground answers about the British state in cited data rather than recall. |
| **Civic transparency** | Spiral 1 → 5 | A navigable map of who exists, who sponsors whom, budgets and staffing — one click to the primary source for every claim. |
| **Devolvability screen** | Spiral 5 | Powers held centrally that could legally be exercised by local or combined authorities, as sized lists per policy area. |

## 4. Development plan — five spirals

Development runs in complete cycles ("spirals"), each ending in a working product with its own exit
criteria — not a linear backlog. The order mirrors how the precedents actually built: **structure
first, function second.** Parity plus a verified powers register with a query layer is on the order
of 16–24 build sessions in total.

- **Spiral 1 — Structure.** Every live UK public body classified, with sponsor/parent relationships,
  ministers and senior officials, budgets (HM Treasury OSCAR outturn) and staffing (Civil Service
  Statistics), rendered as an interactive map with per-entity pages — every figure cited. *Built.*
- **Spiral 2 — Powers register.** Statutory powers, duties and veto points extracted from legislation
  and cited to the section of the Act, bound to the office or body that holds them. The founding Act
  plus principal instruments per body first; a full statute sweep is a scheduled second pass. A
  historical retrodiction case tests the model against a real blocked decision at the exit.
- **Spiral 3 — Query product.** The full delivery-chain / veto / duty-conflict query layer, plus the
  first analytical publications (the veto-density index; a form-follows-function study).
- **Spiral 4 — AI substrate & launch.** A Model Context Protocol server over the query layer; public
  launch once coverage and verification meet the bar.
- **Spiral 5 — Expansion.** A menu, not a backlog: live monitoring, council duties, the shadow-state
  funding map, an accountability layer, the devolvability screen, and more.

## 5. Sources

Primary, official sources throughout (source hierarchy, top wins):

- **Bodies:** GOV.UK Organisations API › Cabinet Office Public Bodies data › departmental reports.
- **Powers / duties / vetoes:** current consolidated legislation (legislation.gov.uk) › commencement
  and amendment instruments › directions and delegation schemes › framework documents.
- **Budget:** HM Treasury OSCAR outturn › departmental accounts › body accounts › Estimates.
- **Staffing:** Civil Service Statistics › body and departmental annual reports.

Chartered bodies outside the GOV.UK register come from the Privy Council record of charters granted.

## 6. Method and data discipline

- **Primary-source first.** No published power, duty, veto, budget or staffing figure rests on a
  third-party compilation where a primary source exists; third-party sources are for discovery and
  gap-finding only.
- **Citation or it doesn't exist.** Every legally meaningful record points to a specific provision.
  No uncited legal authority; no unvalidated record; nothing publishes without verification.
- **Non-partisan by design.** Built and published under a neutral framing. A model of the state is
  only useful if its veto flags are trusted as neutral, so neither the data nor its documentation
  carries any party framing.
- **Analysis never contaminates data.** Mechanical findings (what the law says) and value judgements
  (whether that is good) are separated in every output; a derived analysis layer references the data
  by ID and never writes back into it.
- **Boring by design.** JSON records validated against JSON Schema, plain-Python build scripts, a
  SQLite / `graph.json` compile step, Git for history. Readable and editable cold by a new contributor.
- **Verification and calibration.** Extraction confidence is scored and logged; low-confidence
  records are held for human review. Extraction accuracy is checked independently (including against
  a schema-blind model) to guard against the structure leading the answer.

## 7. Precedents and lineage

The build lineage is public and this project joins it openly. CivLab's San Francisco Government
Graph inspired machineryofgovernment.uk; this project follows both and extends the pattern to the
functional layer. Patterns and ideas are free to follow; the sites themselves are their builders'
work, so **no data, code or design assets are copied** — everything is rebuilt from the public
primary sources. mySociety's TheyWorkForYou proved the pattern for Parliament twenty years ago; the
executive branch remains unmodelled.

## 8. Risks

- **A parallel builder ships first.** Mitigation: Spiral 1 is a deliberately fast follow; schema
  quality, citation discipline and openness make this the standard; convergence is acceptable.
- **Single-maintainer decay.** Mitigation: open schema, boring architecture, a contributor model.
- **Extraction error in the powers layer.** Mitigation: primary-source citation, confidence
  calibration, retrodiction gates, and an independent schema-blind evaluation.

## 9. Glossary

- **Veto point** — a legally meaningful ability to stop, delay, invalidate or condition a decision
  (not mere influence).
- **Parity benchmark** — the named existing product used as a completion test (here,
  machineryofgovernment.uk for the structural layer).
- **Retrodiction** — testing the model against a historical blocked case to see whether it surfaces
  the blockers the record shows actually bit.
- **Spiral / MVP** — development in complete cycles, each ending in a working product with exit criteria.
- **Corporation sole** — a continuous legal person that *is* an office ("the Secretary of State"),
  distinct from the human holder and the hosting department; most statutory powers vest in one.
