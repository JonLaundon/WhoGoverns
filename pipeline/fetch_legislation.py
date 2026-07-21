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
    # s.16 added 2026-07-20 by breadcrumb trawl: s.16A was extracted (the CMA's power to
    # direct Ofwat NOT to modify) without s.16, the obligation it bites on. A veto whose
    # target is missing is only half a record — the chain could name the blocked BODY but
    # not the blocked decision.
    # ss.17A+ added 2026-07-20 (sponsor challenge): the water supply and sewerage LICENSING
    # regime inserted by the Water Act 2003 and rebuilt by the Water Act 2014. This is the
    # gap that made "Ofwat is complete" a false assurance — the whole licensing power set was
    # absent while the body showed 11 records and a derived `regulation` function.
    "sections": ["2", "6", "7", "12J", "13", "14", "15", "16", "16A", "17A", "17B", "17C", "17D",
                 "17F", "17G", "17H", "17I", "17J", "17K", "17L", "17M", "17N", "17O", "17P", "17Q", "17R",
                 "18", "22A", "24", "27A", "27C", "37", "70", "86", "153", "203"],
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

# ---- The cross-cutting competition/company-law SPINE (build-out strategy v0.1). ----
# General law reached by EVERY regulated domain's breadcrumbs, so extracted ONCE here rather
# than re-touched per domain. Scoped (decision #11) to the provisions the water register
# actually reaches, not the whole Acts.
ENTERPRISE_2002 = {
    "instrument_id": "instrument-act-enterprise-act-2002",
    "source_id": "source-act-enterprise-act-2002",
    "slug": "enterprise-act-2002",
    "title": "Enterprise Act 2002",
    "leg_type": "ukpga", "year": 2002, "number": "40",
    # s.109 = CMA investigatory powers (attendance/documents) applied to sectoral references;
    # s.75 = orders (reached from WIA s.17R, competition orders that modify licences).
    "sections": ["75", "109"],
    "instrument_note": "Cross-cutting spine: the CMA's general investigation and order-making "
                       "machinery, applied to the water references by WIA 1991 ss.17M/17R and "
                       "reached the same way by every regulated sector. Scoped to the reached "
                       "provisions, not the whole Act.",
}
COMPETITION_1998 = {
    "instrument_id": "instrument-act-competition-act-1998",
    "source_id": "source-act-competition-act-1998",
    "slug": "competition-act-1998",
    "title": "Competition Act 1998",
    "leg_type": "ukpga", "year": 1998, "number": "41",
    # s.54 = concurrency (sector regulators exercise CA1998 powers concurrently with the CMA);
    # s.2 / s.18 = the Chapter I / Chapter II prohibitions those powers enforce.
    "sections": ["2", "18", "54"],
    "instrument_note": "Cross-cutting spine: the Chapter I/II prohibitions and the concurrency "
                       "regime by which sector regulators (Ofwat, Ofgem, etc.) enforce competition "
                       "law in their sector alongside the CMA. Reached from WIA 1991 s.22A.",
}
# The s.124A public-interest-winding-up TRIGGER instruments — company-investigation and
# fraud-investigation machinery. Registered as instrument nodes (resolving the orphan
# references) but NOT extracted: they belong to a future corporate-enforcement domain, not the
# competition spine. One principal section each so the node exists.
COMPANIES_1985 = {
    "instrument_id": "instrument-act-companies-act-1985", "source_id": "source-act-companies-act-1985",
    "slug": "companies-act-1985", "title": "Companies Act 1985", "leg_type": "ukpga",
    "year": 1985, "number": "6", "sections": ["431"],
    "instrument_note": "Breadcrumb (s.124A trigger): Part XIV company-investigation reports found "
                       "expedient in the public interest can ground a winding-up petition. Future "
                       "corporate-enforcement domain; registered, not extracted.",
}
FSMA_2000 = {
    "instrument_id": "instrument-act-financial-services-and-markets-act-2000",
    "source_id": "source-act-financial-services-and-markets-act-2000",
    "slug": "financial-services-and-markets-act-2000", "title": "Financial Services and Markets Act 2000",
    "leg_type": "ukpga", "year": 2000, "number": "8", "sections": ["167"],
    "instrument_note": "Breadcrumb (s.124A trigger): FCA/inspector reports under FSMA can ground a "
                       "public-interest winding-up. Registered, not extracted.",
}
CJA_1987 = {
    "instrument_id": "instrument-act-criminal-justice-act-1987",
    "source_id": "source-act-criminal-justice-act-1987",
    "slug": "criminal-justice-act-1987", "title": "Criminal Justice Act 1987",
    "leg_type": "ukpga", "year": 1987, "number": "38", "sections": ["2"],
    "instrument_note": "Breadcrumb (s.124A trigger): SFO fraud-investigation information (s.2) can "
                       "ground a public-interest winding-up. Registered, not extracted.",
}

ACTS = [WIA_1991, WATER_ACT_2014, WRA_1991, WCA_1981, INSOLVENCY_1986, WSMA_2025,
        ENTERPRISE_2002, COMPETITION_1998, COMPANIES_1985, FSMA_2000, CJA_1987]


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


# Decision #27 (breadcrumb mining) needs each provision's OUTBOUND references — they are the
# leads that widen the net to adjacent instruments without sweeping the whole statute book.
# They have to be read out of the TEXT: CLML marks up <Citation>/<CitationSubRef> only in the
# amendment commentary, so an operative "section 14 above" or "of the Insolvency Act 1986"
# carries no markup at all. Verified against WIA 1991 s.16, whose references to ss.14, 16A
# and 7 are all plain text inside <Body>.
# An Act title may contain lowercase connectives ("Financial Services AND Markets Act 2000")
# and parenthesised qualifiers ("Water (Special Measures) Act 2025"), so the token class has
# to allow both — a capitals-only pattern silently truncates titles to their last few words.
_TOK = r"(?:[A-Z][\w'-]*|\([^)]{1,40}\)|and|of|the|in|for|to)"
ACT_RE = re.compile(rf"([A-Z][\w'-]*(?:\s+{_TOK}){{0,8}}\s+Act\s+((?:1[6-9]|20)\d{{2}}))")
SEC_RE = re.compile(r"\bsections?\s+(\d+[A-Z]{0,2})(?:\s*\(\d+[A-Za-z]?\))?", re.I)
# How far after a "section N" to look for "of the ... Act YYYY" before treating it as internal.
LOOKAHEAD = 90


def clean_act_title(title):
    """Trim the preamble a greedy title match drags in.

    "Part XIV except section 448A of the Companies Act 1985" -> "Companies Act 1985";
    "a of the Insolvency Act 1986" -> "Insolvency Act 1986". Without this the slug — and so
    the breadcrumb — points at an instrument that does not exist.
    """
    title = re.split(r"\bof the\b", title)[-1]
    title = re.sub(r"^\s*(?:Part|Chapter|Schedule)\s+[IVXLC0-9A-Za-z]+\s+", "", title)
    return title.strip()


def act_slug(title):
    """'Water Act 2014' -> 'water-act-2014' (the slug convention used for provision keys)."""
    return re.sub(r"[^a-z0-9]+", "-", clean_act_title(title).lower()).strip("-")


def extract_references(body, act, known_slugs):
    """-> [{raw, provision_key, instrument_slug, internal, in_model}] for one provision.

    A reference resolves to a provision_key only when we can name both the instrument and the
    section. Anything pointing OUT of what we hold is exactly the breadcrumb we want to keep,
    so unresolved references are retained with their raw text rather than dropped.
    """
    refs, seen = [], set()
    for m in SEC_RE.finditer(body):
        num = m.group(1)
        tail = body[m.end():m.end() + LOOKAHEAD]
        am = ACT_RE.search(tail)
        # "section 14 above" (no Act named) is a reference within this same Act.
        internal = not (am and re.match(r"\s*(above|below)?\s*of\b", tail[:am.start()] or " of "))
        if am and re.search(r"\bof\b", tail[:am.start()] + " "):
            slug, internal = act_slug(am.group(1)), False
        else:
            slug = act["slug"]
        pk = f"{slug}-s{num.lower()}"
        if pk in seen:
            continue
        seen.add(pk)
        refs.append({"raw": m.group(0).strip(), "provision_key": pk, "instrument_slug": slug,
                     "internal": internal, "in_model": slug in known_slugs})
    # Acts named without a section — still a lead ("the Habitats Regulations", "Insolvency Act").
    for am in ACT_RE.finditer(body):
        slug = act_slug(am.group(1))
        if slug == act["slug"] or slug in seen:
            continue
        seen.add(slug)
        refs.append({"raw": am.group(1), "provision_key": None, "instrument_slug": slug,
                     "internal": False, "in_model": slug in known_slugs})
    return refs


UKM = "{http://www.legislation.gov.uk/namespaces/metadata}"


def unapplied_effects(root, sec):
    """Effects legislation.gov.uk records against THIS section but has NOT yet applied to the
    consolidated text (decision #36). Returns [(affecting_title, affecting_provisions, type)].

    Each section's CLML carries the WHOLE Act's <ukm:UnappliedEffects> block, so the signal is
    per-section only after filtering on the affected provision. The nested <ukm:Section
    FoundRef="section-17A"> resolves a sub-paragraph effect ("s. 17A(c)") to its parent section
    — the reliable key; the flat AffectedProvisions attribute is a boundary-matched fallback.
    Part/Chapter-level effects ("Pt. 3 Ch. 2B") are deliberately NOT attributed to individual
    sections: mapping sections to chapters is not cheap, and a false 'stale' flag is worse than
    a conservative miss. This is why the flag means "a change to THIS SECTION is pending", not
    "this Act has any pending change".
    """
    want = "section-" + sec
    # 17A must not match 17AA: after the section token the next char must not be alphanumeric.
    attr_re = re.compile(r"s\. " + re.escape(sec) + r"(?![0-9A-Za-z])")
    hits = []
    for eff in root.iter(UKM + "UnappliedEffect"):
        matched = False
        for prov in eff.findall(UKM + "AffectedProvisions"):
            for s in prov.iter(UKM + "Section"):
                if want in (s.get("FoundRef"), s.get("Ref")):
                    matched = True
        if not matched and attr_re.match(eff.get("AffectedProvisions", "")):
            matched = True
        if matched:
            title = (eff.findtext(UKM + "AffectingTitle")
                     or "{} {} c.{}".format(eff.get("AffectingClass", ""),
                                            eff.get("AffectingYear", ""), eff.get("AffectingNumber", "")))
            hits.append((title.strip(), eff.get("AffectingProvisions", ""), eff.get("Type", "")))
    # De-dup identical (title, provisions, type) triples, keep order.
    seen, out = set(), []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def build_act(act, dry_run, known_slugs=()):
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
        root = ET.fromstring(xml)
        heading, body = parse_section(xml, sec)
        if body is None:
            print(f"  ! section {sec}: not found in XML (skipped)")
            continue
        texts[sec] = (heading, body)
        pk = f"{act['slug']}-s{sec.lower()}"
        effects = unapplied_effects(root, sec)
        if effects:
            note = "Unapplied amendment(s) to this section as at {}: {}. Consolidated text may " \
                   "lag the law in force.".format(accessed, "; ".join(
                       f"{t} {p} ({ty})".strip() for t, p, ty in effects))
        else:
            note = f"No unapplied effects recorded against this section as at {accessed} (Act/Chapter-level " \
                   "effects are not attributed to individual sections)."
        provisions.append({
            "provision_key": pk, "instrument_id": act["instrument_id"],
            "provision_ref": f"s.{sec}", "heading": heading, "in_force_from": None,
            "status": "in_force",
            "citation": {"url": f"{base}/section/{sec}", "version_date": accessed,
                         "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]},
            "references": extract_references(body, act, known_slugs),
            "made_under": None, "commenced_by": None,
            "outstanding_effects": bool(effects),
            "outstanding_effects_note": note,
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

    known_slugs = {a["slug"] for a in ACTS}
    texts_by_slug = {}
    for act in ACTS:
        texts_by_slug[act["slug"]] = build_act(act, args.dry_run, known_slugs)

    if args.show:
        s = args.show.lstrip("s")
        for slug, texts in texts_by_slug.items():
            if s in texts:
                print(f"\n=== {slug} s.{s} — {texts[s][0]} ===\n{texts[s][1]}")


if __name__ == "__main__":
    main()
