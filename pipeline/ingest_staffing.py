#!/usr/bin/env python3
"""Staffing bolt-on (Spiral 1) — Civil Service Statistics 2025 -> Staffing records.

Rank-1 staffing source (Annex A3.4): Cabinet Office Civil Service Statistics, position at
31 March 2025. From the statistical-tables ODS:
  - Table 20 (headcount) / Table 21 (FTE): responsibility level (grade) by organisation.
  - Table 8  (headcount) / Table 8A (FTE): profession by organisation.

Per matched body: a total, a per-grade set, and a per-profession set, each headcount + FTE.
Figures are rounded to 5; '[c]' (headcount 1-4, suppressed) -> no record.

Body match: the 'Civil Service organisation' column, exact normalised name then safe
containment (body + legal-form suffix). 'X Overall' rows are the department GROUP total
(strip ' Overall' to match the department body); '(excl. agencies)' component rows are
skipped. A department group that has agencies gets a double-count disclaimer (its agencies
are also held as separate bodies). No overlap/fuzzy matching.

    py -3 pipeline/ingest_staffing.py [--dry-run]
"""
import argparse
import os
import re
import xml.etree.ElementTree as ET
import zipfile

import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
ODS = os.path.join(DATA, "sources", "raw", "civil-service-statistics", "CSS_2025_statistical_tables.ods")
SOURCE_ID = "source-official-dataset-civil-service-statistics-2025"
PERIOD = "2025"
STAFFING = os.path.join(DATA, "staffing")

T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
P = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p"
STOP = {"the", "of", "for", "in", "uk", "gb", "great", "britain", "and", "department"}
LEGAL_SUFFIX = {"plc", "ltd", "limited", "office", "dbs", "corporation", "co"}
GRADE = [("Senior Civil Service level", "scs"), ("Grade 6 or Grade 7 level", "grade_6_7"),
         ("Senior or Higher Executive Officer level", "seo_heo"), ("Executive Officer level", "eo"),
         ("Administrative Assistant or Administrative Officer level", "aa_ao"),
         ("unreported grade", "unreported")]


def norm(s):
    s = str(s).lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(w for w in s.split() if w not in STOP)


def toks(s):
    return frozenset(norm(s).split())


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-")


def num(x):
    x = str(x).replace(",", "").strip()
    if x in ("", "[c]", "[z]", "[x]", "-"):
        return None
    try:
        return int(round(float(x)))
    except ValueError:
        return None


def cell_text(c):
    return " ".join(t.text or "" for t in c.iter(P)).strip()


def row_values(r):
    out = []
    for c in r.findall(T + "table-cell"):
        rep = int(c.get(T + "number-columns-repeated", "1"))
        out += [cell_text(c)] * min(rep, 60)
    return out


def parse_table(tables, name):
    """-> (header, {org_name: (parent, [values])})."""
    rows = tables[name].findall(".//" + T + "table-row")
    header = row_values(rows[5])
    data = {}
    for r in rows[6:]:
        v = row_values(r)
        if len(v) >= 3 and v[1]:
            data[v[1]] = (v[0], v)
    return header, data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # body lookup
    exact, body_toks = {}, {}
    for d in store.load("bodies"):
        body_toks[d["body_id"]] = toks(d["name"])
        for n in [d["name"]] + d.get("other_names", []):
            exact.setdefault(norm(n), d["body_id"])

    def match(org):
        # Clean the org label to the body name (strip " Overall" / " (excl. agencies)"),
        # then exact or safe-containment match. Scope is decided by the caller.
        cand = org.replace(" (excl. agencies)", "")
        if cand.endswith(" Overall"):
            cand = cand[:-len(" Overall")]
        bid = exact.get(norm(cand))
        if bid:
            return bid
        ot = toks(cand)
        c = [b for b, bt in body_toks.items() if bt and bt <= ot and (ot - bt) <= LEGAL_SUFFIX]
        return c[0] if len(c) == 1 else None

    root = ET.fromstring(zipfile.ZipFile(ODS).read("content.xml"))
    tables = {t.get(T + "name"): t for t in root.iter(T + "table")}
    g_hc = parse_table(tables, "table_20"); g_fte = parse_table(tables, "table_21")
    p_hc = parse_table(tables, "table_8");  p_fte = parse_table(tables, "table_8A")

    orgs = g_hc[1]
    # Group CSS org rows by the body they match. A department reports BOTH an "X Overall"
    # (group total, incl agencies) and a non-Overall core row — named either
    # "X (excl. agencies)" or just "X" — so classify body-centrically: a body with both an
    # Overall and a non-Overall row gets group+core; every other body gets one set (scope
    # None). (First row wins per slot.)
    by_bid = {}
    for org, (_parent, _) in orgs.items():
        bid = match(org)
        if not bid:
            continue
        slot = "overall" if org.endswith(" Overall") else "other"
        by_bid.setdefault(bid, {}).setdefault(slot, org)

    body_scopes = {}
    for bid, slots in by_bid.items():
        if "overall" in slots and "other" in slots:
            body_scopes[bid] = {"group": slots["overall"], "core": slots["other"]}
        else:
            body_scopes[bid] = {None: slots.get("overall") or slots["other"]}

    DISCLAIMER = ("Departmental GROUP total (includes agencies, which are also held as "
                  "separate bodies) — do not sum a department with its agencies.")

    def col_index(header, needle):
        for i, h in enumerate(header):
            if needle in h:
                return i
        return None

    def total_index(header):
        return col_index(header, "Total headcount") or col_index(header, "Total full-time")

    written = []
    for bid, scopes in body_scopes.items():
        body_slug = bid[len("uk-state-body-"):]
        recs = []
        for scope, org in scopes.items():
            note = DISCLAIMER if scope == "group" else None

            # Loop variables bound as defaults so the closure captures THIS iteration's values
            # (and is self-contained — no late binding). add() is called synchronously below.
            def add(metric, value, grade=None, profession=None, staff_group="civil_service",
                    _scope=scope, _note=note, _bid=bid, _slug=body_slug, _recs=recs):
                if not value:   # skip suppressed ([c] -> None) and zero (absent in that grade/profession)
                    return
                key = "total" if (grade is None and profession is None) else \
                      ("grade-" + grade if grade else "profession-" + slug(profession))
                rid = f"staffing-{_slug}-{PERIOD}-{metric}-{key}"
                if _scope:
                    rid += "-" + _scope
                _recs.append({
                    "staffing_record_id": rid,
                    "body_id": _bid, "period": PERIOD, "metric": metric, "value": value,
                    "staff_group": staff_group, "grade": grade, "profession": profession,
                    "scope": _scope, "source_id": SOURCE_ID,
                    "citation": {"dataset": SOURCE_ID, "table": "CSS_2025", "as_at": "2025-03-31"},
                    "notes": _note, "record_status": "extracted",
                })

            for metric, (header, data) in (("headcount", g_hc), ("fte", g_fte)):
                row = data.get(org)
                if not row:
                    continue
                vals = row[1]
                ti = total_index(header)
                if ti is not None and ti < len(vals):
                    add(metric, num(vals[ti]))
                for label, gslug in GRADE:
                    ci = col_index(header, label)
                    if ci is not None and ci < len(vals):
                        add(metric, num(vals[ci]), grade=gslug,
                            staff_group="senior_civil_service" if gslug == "scs" else "civil_service")

            for metric, (header, data) in (("headcount", p_hc), ("fte", p_fte)):
                row = data.get(org)
                if not row:
                    continue
                vals = row[1]
                for i, h in enumerate(header):
                    m = re.search(r"in the (.+?) profession", h)
                    if m and i < len(vals):
                        add(metric, num(vals[i]), profession=m.group(1))

        written.extend(recs)

    if not args.dry_run:
        store.save("staffing", written)
    print("--- ingest_staffing summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print(f"bodies with staffing records:   {len(body_scopes)}")
    print("departments with group+core:    {}".format(sum(1 for sc in body_scopes.values() if "core" in sc)))
    print(f"staffing records written:       {len(written)}")


if __name__ == "__main__":
    main()
