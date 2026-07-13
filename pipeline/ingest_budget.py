#!/usr/bin/env python3
"""Budget bolt-on (Spiral 1) — HMT OSCAR outturn -> Budget records.

Rank-1 budget source (Annex A3.3): HM Treasury OSCAR II annual outturn, FY 2024-25.
Aggregates the raw OSCAR extract to per-body figures and writes Budget records.

Aggregation (validated against published figures — Home Office resource DEL ~£18bn net,
MoD ~£44bn):
  - Rows kept: CONTROL_BUDGET_L1 in {DEL, AME}, ECONOMIC_BUDGET in {RESOURCE, CAPITAL}.
  - Do NOT filter TYPE_LONG_NAME — IN-YEAR RETURN and FINAL OUTTURN partition the year.
  - AMOUNT is in GBP thousands (x1000 here).
  - net  = sum of all rows for the (boundary, resource/capital) slice.
  - gross = rows flagged INCOME_CATEGORY_SHORT_NAME == 'GROSS' (income excluded).
  - programme = COFOG FUNCTION_LONG_NAME (resource DEL only; net).

Body match: EXACT normalised organisation name / alias (no fuzzy — house rule). Several
OSCAR accounting entities can map to one body (e.g. 'Arts Council' + 'Arts Council of
England Lottery' -> Arts Council England); they are summed. Unmatched OSCAR orgs are
reported (candidates for a reviewed alias pass), never guessed.

    py -3 pipeline/ingest_budget.py [--dry-run]
Needs openpyxl.
"""
import argparse
import collections
import os
import re

import openpyxl

import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
XLSX = os.path.join(DATA, "sources", "raw", "oscar", "BUD_24-25.xlsx")
SHEET = "Transparency_report_BUD_REPORTI"
SOURCE_ID = "source-official-dataset-hmt-oscar-outturn-2024-25"
FY = "2024-25"
BUDGETS = os.path.join(DATA, "budgets")

STOP = {"the", "of", "for", "in", "uk", "gb", "great", "britain", "and", "department"}
# (L1, ECONOMIC_BUDGET) -> budget_type
BUDGET_TYPE = {("DEL", "RESOURCE"): "resource_del", ("DEL", "CAPITAL"): "capital_del",
               ("AME", "RESOURCE"): "resource_ame", ("AME", "CAPITAL"): "capital_ame"}


def norm(s):
    s = str(s).lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(w for w in s.split() if w not in STOP)


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-")


# Legal-form words that may pad an OSCAR accounting-entity name vs the body name.
# Containment modulo these is NOT fuzzy matching — it is the body name plus a corporate
# suffix (e.g. "British Business Bank plc" -> "British Business Bank"). Overlap matching
# is deliberately NOT done (it mis-maps "British Tourist Authority" -> "British Transport
# Police Authority" etc. — same reason fuzzy matching was rejected in refine_classification).
LEGAL_SUFFIX = {"plc", "ltd", "limited", "office", "dbs", "corporation", "co"}


def toks(s):
    return frozenset(norm(s).split())


def body_lookup():
    """Return (exact_lut, body_toks). exact_lut: normalised name/alias -> body_id."""
    exact, body_toks = {}, {}
    for d in store.load("bodies"):
        body_toks[d["body_id"]] = toks(d["name"])
        for n in [d["name"]] + d.get("other_names", []):
            exact.setdefault(norm(n), d["body_id"])
    return exact, body_toks


def match_org(org, exact, body_toks):
    """Exact normalised match first; then safe containment (body tokens subset of org
    tokens, extra org tokens all legal-form suffixes, unique body). Returns body_id or None."""
    bid = exact.get(norm(org))
    if bid:
        return bid
    ot = toks(org)
    cands = [b for b, bt in body_toks.items() if bt and bt <= ot and (ot - bt) <= LEGAL_SUFFIX]
    return cands[0] if len(cands) == 1 else None


def aggregate():
    """Return agg[body_id][(budget_type, basis, programme)] = amount_gbp, and unmatched set."""
    exact, body_toks = body_lookup()
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb[SHEET]; ws.reset_dimensions()
    it = ws.iter_rows(values_only=True)
    H = {c: i for i, c in enumerate(next(it))}
    iO, iL1, iEco, iInc, iFun = (H["ORGANISATION_LONG_NAME"], H["CONTROL_BUDGET_L1_LONG_NAME"],
                                 H["ECONOMIC_BUDGET_CODE"], H["INCOME_CATEGORY_SHORT_NAME"],
                                 H["FUNCTION_LONG_NAME"])
    iAmt = H["AMOUNT"]
    agg = collections.defaultdict(lambda: collections.defaultdict(float))
    matched_orgs, unmatched_orgs = set(), collections.Counter()
    for r in it:
        bt = BUDGET_TYPE.get((r[iL1], r[iEco]))
        if not bt:
            continue
        bid = match_org(r[iO], exact, body_toks)
        if not bid:
            unmatched_orgs[r[iO]] += 1
            continue
        matched_orgs.add(r[iO])
        amt = (r[iAmt] or 0) * 1000.0
        agg[bid][(bt, "net", None)] += amt
        inc = r[iInc]
        if inc == "GROSS":
            agg[bid][(bt, "gross", None)] += amt
        elif inc and inc != "n/a":
            # Income row (Assets, Goods and services, Other income, etc.) — negative amount.
            agg[bid][("income", "net", inc.title())] += amt   # income by category
            agg[bid][("income", "net", None)] += amt          # total income
        if bt == "resource_del" and r[iFun]:
            agg[bid][("resource_del", "net", r[iFun])] += amt
    return agg, matched_orgs, unmatched_orgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    agg, matched_orgs, unmatched = aggregate()
    fy_slug = FY  # 2024-25 already dash-formatted
    all_records = []
    for bid, cells in agg.items():
        body_slug = bid[len("uk-state-body-"):]
        # total managed expenditure (net) = sum of the four headline net boundaries (NOT income).
        tme = sum(v for (bt, basis, prog), v in cells.items()
                  if basis == "net" and prog is None
                  and bt in ("resource_del", "capital_del", "resource_ame", "capital_ame"))
        records = []
        for (bt, basis, prog), amount in cells.items():
            if round(amount) == 0:
                continue
            amount = abs(amount) if bt == "income" else amount   # income rows are negative
            rid = f"budget-{body_slug}-{fy_slug}-{bt}-{basis}"
            if prog:
                rid += "-" + slug(prog)
            records.append({
                "budget_record_id": rid,
                "body_id": bid,
                "financial_year": FY,
                "budget_type": bt,
                "basis": basis,
                "programme": prog,
                "amount": round(amount),
                "currency": "GBP",
                "cash_or_real_terms": "cash",
                "source_id": SOURCE_ID,
                "citation": {"dataset": SOURCE_ID, "table": "BUD_24-25", "financial_year": FY},
                "notes": None,
                "record_status": "extracted",
            })
        if round(tme) != 0:
            records.append({
                "budget_record_id": f"budget-{body_slug}-{fy_slug}-total-managed-expenditure-net",
                "body_id": bid, "financial_year": FY, "budget_type": "total_managed_expenditure",
                "basis": "net", "programme": None, "amount": round(tme), "currency": "GBP",
                "cash_or_real_terms": "cash", "source_id": SOURCE_ID,
                "citation": {"dataset": SOURCE_ID, "table": "BUD_24-25", "financial_year": FY},
                "notes": "Sum of resource/capital DEL and AME (net).", "record_status": "extracted",
            })
        all_records.extend(records)

    if not args.dry_run:
        store.save("budgets", all_records)
    print("--- ingest_budget summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print(f"bodies with budget records:   {len(agg)}")
    print(f"budget records written:       {len(all_records)}")
    print(f"OSCAR orgs matched:           {len(matched_orgs)}")
    print(f"OSCAR orgs UNMATCHED:         {len(unmatched)}  (candidates for a reviewed alias pass)")


if __name__ == "__main__":
    main()
