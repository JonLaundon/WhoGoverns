# Moving WhoGoverns to Claude Code — plain-English guide

**For:** Jon. **Why:** the build needs to run scripts and use git (version history), which the Cowork sandbox can't do on a OneDrive folder. Claude Code is the same kind of assistant, running directly on your laptop inside the project folder, so it can.

You don't need to be technical. You open the folder, paste one starter message, and approve steps as Claude Code proposes them.

---

## What Claude Code is (in one line)

The same assistant as here, but running in a terminal on your computer, able to edit files, run the build scripts, and save version history — all inside the `whogoverns` folder.

## One-time setup

1. Install Claude Code (Anthropic's guide: https://docs.claude.com/en/docs/claude-code). If you'd rather, it also runs inside VS Code.
2. Make sure git is installed (Claude Code will tell you if it isn't and how to get it).
3. That's it — no accounts or keys to wire up beyond signing in to Claude Code.

## Starting the session

1. Open a terminal (or VS Code) in this folder:
   `…\His Majesty's Government\whogoverns`
2. Delete the leftover `.git_corrupt_*` folder first if it's still there (right-click → Delete in Explorer). It's harmless junk from the sandbox.
3. Start Claude Code and paste the **starter message** below.

## The starter message to paste

```
You are the build agent for WhoGoverns, an open, machine-readable model of the UK state.

Read AGENT.md first — it is your operating digest. Then read
../2026-07-05-spiral-1-workpack-v0-2.md for the Spiral 1 plan and
../2026-07-05-annex-a-backend-baseline-v0-4.md for the binding data standard.

Setup is already done: schemas, vocabularies, validate.py, and three seed
body records (Cabinet Office, Ofgem, ACOBA) that pass validation. Do not redo setup.

First, initialise git and make the first commit (setup is complete):
  git init -b main
  git add -A
  git commit -m "Pre-Spiral 1 setup: schemas, vocab, AGENT.md, validation, three seed records"

Then begin Spiral 1 build task 1 from the workpack: write ingest_organisations.py
to page through the GOV.UK Organisations API, cache the raw JSON to data/sources,
and create a Source record. Follow the boring-code standard (plain Python, standard
library preferred, one script one job). Show me the script before running it.
Run validate.py after each step. Do not populate powers/duties/vetoes (Spiral 2)
or budgets/staffing (deferred bolt-on). End the session with a review pack and a small commit.
```

## What to expect, and your part

- Claude Code proposes each step and waits for your approval before running scripts or committing. Say yes, or ask it to explain.
- After each script it runs `validate.py`; you'll see "0 errors" when a batch is clean.
- Work grows the `data/` folder (one small file per body) and, later, the map in `site/`.
- **Your only real jobs:** approve steps, eyeball the occasional record against its GOV.UK source when it asks (the "spot-check"), and, at the very end of Spiral 1, push to your personal GitHub — Claude Code will give you the exact command.

## How to know Spiral 1 is finished

The workpack's exit criteria (§6): every live body mapped and classified, sponsor relationships and ministers in place, the Cytoscape map renders with clickable body pages, 30 spot-checks pass, and a side-by-side against machineryofgovernment.uk shows nothing structural missing. Then you push it up as your first commit to GitHub.

## If you get stuck

Bring the question back here (Cowork) — I hold the plan and can untangle anything Claude Code raises, then send you back with a clear next instruction.
