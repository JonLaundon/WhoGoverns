# WhoGoverns

**An open, machine-readable model of the UK state** — every department, agency and
arm's-length body, its budget, staffing, and (the layer that exists nowhere today) its
statutory powers, duties and veto points, cited down to the section of the Act.

No existing dataset can answer the question at the centre of this project:

> **"Who can legally block this policy, and under what authority?"**

The answer sits in prose across hundreds of statutes, statutory instruments and framework
documents. Large-language-model extraction now makes converting that prose into structured,
queryable data tractable — so WhoGoverns builds it, from primary sources, and publishes it open.

> **Independent and non-partisan.** WhoGoverns is built entirely from public, official primary
> sources and published under a non-partisan framing. It is not affiliated with, or endorsed by,
> HM Government. A model of the state is only useful if its veto flags are trusted as neutral, so
> the data and its documentation carry no party framing.

---

## What you can do with it

The structural layer ships first; the powers register is what makes the questions below answerable.

| Use case | What it answers |
|---|---|
| **Policy stress-testing** | Trace a proposal's path through the state and enumerate the statutory vetoes, consultation duties and judicial-review exposure that stand between decision and delivery — each with a citation. |
| **Veto-density index** | Count and weight the veto points between a ministerial decision and its delivery, per policy area — a publishable "levers of the state" metric. |
| **Day-one government packs** | For any office: what powers does this Secretary of State actually hold; what needs primary legislation; what can be done by direction tomorrow. |
| **Machinery-of-government modelling** | Model a merger, abolition or cull of arm's-length bodies as a graph operation — which functions, duties and budgets move, and which duties have nowhere to land. |
| **Form-follows-function review** | A function inventory from the powers register: orphaned, duplicated and misfit functions surfaced against a published taxonomy. |
| **AI substrate (MCP)** | Expose the model as a queryable tool so AI assistants ground answers about the British state in cited data rather than recall. |
| **Civic transparency** | A navigable map of who exists, who sponsors whom, budgets and staffing — one click to the primary source for every claim. |

## How it's built — spiral by spiral

Development runs in complete cycles ("spirals"), each ending in a working product. The order
mirrors the proven precedents: **structure first, function second.**

| Spiral | Delivers | Status |
|---|---|---|
| **1 · Structure** | Every live UK public body classified, with sponsor/parent relationships, ministers and senior officials, budgets and staffing — an interactive map with per-entity pages, every figure cited. | **Built** |
| **2 · Powers register** | Statutory powers, duties and veto points extracted from legislation and cited to the section of the Act; bound to the office or body that holds them. | Next |
| **3 · Query product** | The full delivery-chain / veto / duty-conflict query layer, plus the first analytical publications. | Planned |
| **4 · AI substrate & launch** | A Model Context Protocol server over the query layer; public launch. | Planned |
| **5 · Expansion** | Live monitoring, council duties, devolvability screens, the shadow-state funding map, and more. | Menu |

## Method and sources

- **Primary sources only.** Nothing is published on a third-party compilation where a primary
  source exists. Powers cite consolidated legislation (legislation.gov.uk); bodies come from the
  GOV.UK Organisations API and Cabinet Office data; budgets from HM Treasury OSCAR outturn;
  staffing from Civil Service Statistics.
- **Citation or it doesn't exist.** Every legally meaningful record points to a specific provision;
  nothing publishes without verification.
- **Boring by design.** JSON records validated against JSON Schema, plain-Python build scripts,
  a SQLite/`graph.json` compile step, Git for history. Follows presentation patterns set by
  machineryofgovernment.uk and CivLab's SF Government Graph — patterns only; no data or code copied.

## Build & run

Runtime needs only `jsonschema` + `openpyxl` (`pip install -r requirements.txt`). From the repo root:

- `py -3 pipeline/compile.py` — build `compiled/graph.json` + `state_machine.sqlite` + `manifest.json` from `data/`.
- `py -3 validate.py` — schema-validate every record; check IDs, source links, referential integrity.
- `py -3 -m ruff check .` and `py -3 -m pytest -q` — lint and unit tests (dev tools in `pyproject.toml`).
- Serve the map: `py -3 -m http.server` from the repo root, then open `/site/`.

Data lives in `data/` as one JSON array per type (`bodies`, `relationships`, `offices`,
`person-roles`, `sources`, `budgets`, `staffing`), read/written through `pipeline/store.py`.
Pipeline run-order and details in `pipeline/README.md`; schema decisions in `issues/`.

## Licence & status

Open data under the Open Government Licence v3.0 for the underlying official sources; the compiled
dataset's own licence is finalised at first public launch. Records are machine-extracted and
carry a `record_status` — those marked `extracted` await human verification.
