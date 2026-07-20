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
import datetime
import hashlib
import os
import re
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
    "sections": ["2", "6", "7", "13", "14", "15", "16A", "18", "22A", "24", "27A", "27C",
                 "37", "70", "86", "153", "203"],
}

# Water Act 2014 (c.21). NOTE (decision #24 cross-check): the Act operates
# overwhelmingly by AMENDING WIA 1991 — the resilience duty (s.22 → WIA s.2/s.2DA),
# strategic priorities (s.24 → WIA s.2A), the extended penalty time-limit (s.26 → WIA
# s.22A), and most of the new licensing regime (inserted as WIA ss.17A+). Those powers
# live in the consolidated WIA 1991 text and are extracted THERE, citing this Act as
# amending provenance — NOT re-minted here. We fetch only the amending provisions we
# reference as provenance (s.22, the resilience objective) so the node exists.
WATER_ACT_2014 = {
    "instrument_id": "instrument-act-water-act-2014",
    "source_id": "source-act-water-act-2014",
    "slug": "water-act-2014",
    "title": "Water Act 2014",
    "leg_type": "ukpga", "year": 2014, "number": "21",
    "sections": ["22"],
    "instrument_note": "Amending instrument: operates chiefly by amending the Water Industry "
                       "Act 1991. Operative powers/duties are extracted from the consolidated WIA "
                       "1991 text, citing this Act as amending provenance. s.22 inserts the "
                       "resilience objective (WIA 1991 s.2(2A)(e), s.2(2DA)).",
}

# Water Resources Act 1991 (c.57) — the Environment Agency's principal water statute (the twin
# of WIA 1991 c.56). Brings the cross-body / tail blockers the renationalisation story misses:
# abstraction licensing (s.24 restriction), enforcement notices (s.25A), drought orders/permits
# (s.73, s.79A), water-quality objectives (s.83). Supersession wrinkle: discharge consents moved
# largely to the Environmental Permitting (England and Wales) Regulations 2016 (a later SI).
WRA_1991 = {
    "instrument_id": "instrument-act-water-resources-act-1991",
    "source_id": "source-act-water-resources-act-1991",
    "slug": "water-resources-act-1991",
    "title": "Water Resources Act 1991",
    "leg_type": "ukpga", "year": 1991, "number": "57",
    "sections": ["24", "38", "25A", "73", "79A"],
}

# Wildlife and Countryside Act 1981 (c.69) — Natural England's SSSI consent regime, the classic
# "left field" blocker on water infrastructure (reservoirs, abstraction affecting protected sites).
# s.28E: owner/occupier needs NE consent for damaging operations. s.28H: a public body (a water
# undertaker is a "section 28G authority") must get NE's assent before such operations. NOTE: for
# European sites (SAC/SPA) the sharper gate is the Conservation of Habitats and Species Regs 2017
# (assimilated EU law, a later SI) — flagged, not yet extracted.
WCA_1981 = {
    "instrument_id": "instrument-act-wildlife-and-countryside-act-1981",
    "source_id": "source-act-wildlife-and-countryside-act-1981",
    "slug": "wildlife-and-countryside-act-1981",
    "title": "Wildlife and Countryside Act 1981",
    "leg_type": "ukpga", "year": 1981, "number": "69",
    "sections": ["28E", "28H"],
}

# Breadcrumb instruments reached via the special-administration retrodiction. Registered as
# provenance nodes (one principal section each); SAR-specific extraction is a follow-on.
INSOLVENCY_1986 = {
    "instrument_id": "instrument-act-insolvency-act-1986",
    "source_id": "source-act-insolvency-act-1986",
    "slug": "insolvency-act-1986",
    "title": "Insolvency Act 1986",
    "leg_type": "ukpga", "year": 1986, "number": "45",
    "sections": ["124A"],
    "instrument_note": "Breadcrumb: the water SAR (WIA 1991 s.24, Sch 3) applies and modifies "
                       "Insolvency Act 1986 machinery. s.124A = the SoS winding-up petition "
                       "referenced by WIA s.24(2)(d).",
}
WSMA_2025 = {
    "instrument_id": "instrument-act-water-special-measures-act-2025",
    "source_id": "source-act-water-special-measures-act-2025",
    "slug": "water-special-measures-act-2025",
    "title": "Water (Special Measures) Act 2025",
    "leg_type": "ukpga", "year": 2025, "number": "5",
    "sections": ["14"],
    "instrument_note": "Latest amendment to the water SAR: s.14 gives the SoS a shortfall-recovery "
                       "power (modify licences to recover SAR costs not met by a sale/rescue). "
                       "Registered via the retrodiction; full extraction is a follow-on.",
}

ACTS = [WIA_1991, WATER_ACT_2014, WRA_1991, WCA_1981, INSOLVENCY_1986, WSMA_2025]


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


def build_act(act, dry_run):
    """Fetch one Act's configured sections; emit its Source, Instrument and Provision
    records (idempotent via store). Returns {section: (heading, text)} for --print."""
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
        "source_id": act["source_id"], "notes": act.get("instrument_note"), "record_status": "extracted",
    }

    provisions, texts = [], {}
    for sec in act["sections"]:
        url = f"{base}/section/{sec}/data.xml"
        cache = os.path.join(cache_dir, f"section-{sec}.xml")
        if os.path.exists(cache):
            with open(cache, encoding="utf-8") as fh:
                xml = fh.read()
        else:
            xml = fetch(url)
            if not dry_run:
                with open(cache, "w", encoding="utf-8") as fh:
                    fh.write(xml)
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

    if not dry_run:
        store.upsert("sources", [source])
        store.upsert("instruments", [instrument])
        store.upsert("provisions", provisions)

    print(f"--- fetch_legislation: {act['title']} ---")
    print(f"sections fetched:  {len(texts)}/{len(act['sections'])}")
    print(f"provision records: {len(provisions)}")
    for sec, (h, _) in texts.items():
        print(f"  s.{sec}: {h}")
    return texts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--print", dest="show", default=None, help="also print a section's text, e.g. s13")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    texts_by_slug = {}
    for act in ACTS:
        texts_by_slug[act["slug"]] = build_act(act, args.dry_run)

    if args.show:
        s = args.show.lstrip("s")
        for slug, texts in texts_by_slug.items():
            if s in texts:
                print(f"\n=== {slug} s.{s} — {texts[s][0]} ===\n{texts[s][1]}")


if __name__ == "__main__":
    main()
