#!/usr/bin/env python3
"""Fetch legislation from legislation.gov.uk and build the structural graph nodes.

One job (the STRUCTURAL half of Spiral 2 extraction — no LLM here): fetch a section's
CLML XML from legislation.gov.uk, cache it, and emit the rule-extractable records:
  - one Source record per Act (the citation/provenance object);
  - one Instrument record per Act (the 'module');
  - one Provision record per section (the addressable 'function'): its ref, heading, a
    content_hash of the operative text, and the point-in-time citation (url + version_date).
Provision TEXT is NOT stored (decision 2026-07-13) — only the hash, url and version_date.
The LLM extraction of Power/Duty/Veto records is a SEPARATE step that reads the cached text.

    py -3 pipeline/fetch_legislation.py            # fetch the configured Water slice
    py -3 pipeline/fetch_legislation.py --print s2  # also print a section's parsed text

Boring by design: stdlib only, polite HTTP (UA, timeout, retry), idempotent via store.
"""
import argparse
import hashlib
import datetime
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

import store

L = "{http://www.legislation.gov.uk/namespaces/legislation}"
UA = "WhoGoverns/0.1 (open UK-state dataset; contact jonnylaundon@gmail.com)"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "data", "sources", "raw", "legislation")

# The calibration slice: Water Industry Act 1991 (c.56), the sections carrying Ofwat's
# operative levers (the renationalisation / Thames-Water toolkit). type-year-number identify
# the Act on legislation.gov.uk; sections are fetched individually.
WIA_1991 = {
    "instrument_id": "instrument-act-water-industry-act-1991",
    "source_id": "source-act-water-industry-act-1991",
    "slug": "water-industry-act-1991",
    "title": "Water Industry Act 1991",
    "leg_type": "ukpga", "year": 1991, "number": "56",
    "sections": ["2", "13", "14", "18", "22A", "24", "37"],
}


def fetch(url, timeout=30, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/xml"})
    last = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as err:
            last = err
            time.sleep(attempt * 2)
    raise SystemExit(f"Gave up fetching {url}: {last}")


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def section_node(root, want):
    """Return the P1group whose Pnumber matches `want` (e.g. '13', '22A')."""
    for pg in root.iter(L + "P1group"):
        p1 = pg.find(L + "P1")
        if p1 is None:
            continue
        pn = p1.find(L + "Pnumber")
        if pn is not None and clean("".join(pn.itertext())) == want:
            return pg
    return None


def parse_section(xml, want):
    """-> (heading, operative_text) for section `want`, or (None, None) if absent."""
    root = ET.fromstring(xml)
    pg = section_node(root, want)
    if pg is None:
        return None, None
    title = pg.find(L + "Title")
    heading = clean("".join(title.itertext())) if title is not None else None
    # Operative text = the section's paragraphs, commentary refs stripped.
    for c in pg.iter(L + "CommentaryRef"):
        c.text = ""
    body = clean("".join(pg.itertext()))
    return heading, body


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--print", dest="show", default=None, help="also print a section's text, e.g. s13")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    act = WIA_1991
    accessed = datetime.date.today().isoformat()
    base = f"https://www.legislation.gov.uk/{act['leg_type']}/{act['year']}/{act['number']}"
    cache_dir = os.path.join(RAW, act["slug"])
    os.makedirs(cache_dir, exist_ok=True)

    source = {
        "source_id": act["source_id"],
        "title": act["title"],
        "source_type": "act",
        "publisher": "legislation.gov.uk (The National Archives)",
        "url": base,
        "accessed_date": accessed,
        "publication_date": f"{act['year']}-01-01",
        "version_date": accessed,
        "legal_status": "current",
        "licence": "Open Government Licence v3.0",
        "notes": "Current consolidated ('as amended') text; point-in-time via section version_date. "
                 "Raw CLML cached under data/sources/raw/legislation/ (gitignored).",
    }
    instrument = {
        "instrument_id": act["instrument_id"], "title": act["title"], "instrument_type": "act",
        "year": act["year"], "number": act["number"], "legislation_url": base,
        "enacted_by": "Parliament", "made_under": None, "status": "in_force",
        "source_id": act["source_id"], "notes": None, "record_status": "extracted",
    }

    provisions, texts = [], {}
    for sec in act["sections"]:
        url = f"{base}/section/{sec}/data.xml"
        cache = os.path.join(cache_dir, f"section-{sec}.xml")
        if os.path.exists(cache):
            xml = open(cache, encoding="utf-8").read()
        else:
            xml = fetch(url)
            if not args.dry_run:
                open(cache, "w", encoding="utf-8").write(xml)
        heading, body = parse_section(xml, sec)
        if body is None:
            print(f"  ! section {sec}: not found in XML (skipped)")
            continue
        texts[sec] = (heading, body)
        pk = f"{act['slug']}-s{sec.lower()}"
        provisions.append({
            "provision_key": pk, "instrument_id": act["instrument_id"],
            "provision_ref": f"s.{sec}", "heading": heading, "in_force_from": None,
            "status": "in_force",
            "citation": {"url": f"{base}/section/{sec}", "version_date": accessed,
                         "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]},
            "references": [], "made_under": None, "commenced_by": None,
            "outstanding_effects": False,
            "outstanding_effects_note": "Outstanding-effects check not yet wired (Spiral 2 TODO).",
            "notes": None, "record_status": "extracted",
        })

    if not args.dry_run:
        store.upsert("sources", [source])
        store.upsert("instruments", [instrument])
        store.upsert("provisions", provisions)

    print(f"--- fetch_legislation: {act['title']} ---")
    print(f"sections fetched:  {len(texts)}/{len(act['sections'])}")
    print(f"provision records: {len(provisions)}")
    for sec, (h, _) in texts.items():
        print(f"  s.{sec}: {h}")
    if args.show:
        s = args.show.lstrip("s")
        if s in texts:
            print(f"\n=== s.{s} — {texts[s][0]} ===\n{texts[s][1]}")


if __name__ == "__main__":
    main()
