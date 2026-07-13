#!/usr/bin/env python3
"""Ingest the GOV.UK Organisations API and cache the raw pages.

One job: page through https://www.gov.uk/api/organisations, save each page of
raw JSON verbatim to data/sources/raw/govuk-organisations-api/, and refresh the
SourceRecord for the dataset. It does NOT transform anything into Body or
Relationship records — that is a separate script (task 2).

Boring by design: stdlib only, runnable standalone from a clean checkout:
    py -3 pipeline/ingest_organisations.py            # full pull (all pages)
    py -3 pipeline/ingest_organisations.py --max-pages 2   # smoke test (first 2 pages)

Raw pages land under data/sources/raw/... (a subfolder), so validate.py — which
globs data/sources/*.json non-recursively — never schema-validates them against
the Source schema. Only the curated SourceRecord in data/sources/ is validated.
"""
import argparse
import datetime
import json
import os
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (this file lives in pipeline/)

BASE_URL = "https://www.gov.uk/api/organisations"
RAW_DIR = os.path.join(REPO, "data", "sources", "raw", "govuk-organisations-api")
SOURCE_RECORD = os.path.join(
    REPO, "data", "sources", "source-official-dataset-govuk-organisations-api.json"
)
# Identify ourselves honestly to the API (courtesy, and it aids their logs).
USER_AGENT = "WhoGoverns/0.1 (open UK-state dataset; contact jonnylaundon@gmail.com)"


def fetch(url, timeout, retries=3):
    """GET a URL and parse JSON, with a small retry on transient failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json"})
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as err:
            last_err = err
            wait = attempt * 2
            print(f"  ! fetch failed (attempt {attempt}/{retries}): {err} — retrying in {wait}s")
            time.sleep(wait)
    raise SystemExit(f"Gave up fetching {url} after {retries} attempts: {last_err}")


def absolute(next_url):
    """The API returns next_page_url as an absolute or root-relative URL."""
    if not next_url:
        return None
    if next_url.startswith("http"):
        return next_url
    return "https://www.gov.uk" + next_url


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def refresh_source_record(accessed_date, pages, total_orgs):
    """Rewrite the dataset SourceRecord, stamping the access date and counts.

    Curated fields are held here so the script is the single source of the
    record's shape; validate.py checks it against source.schema.json afterwards.
    """
    record = {
        "source_id": "source-official-dataset-govuk-organisations-api",
        "title": "GOV.UK Organisations API",
        "source_type": "official_dataset",
        "publisher": "Government Digital Service (GOV.UK)",
        "url": BASE_URL,
        "accessed_date": accessed_date,
        "publication_date": None,
        "version_date": accessed_date,
        "legal_status": "current",
        "licence": "Open Government Licence v3.0",
        "notes": (
            "Machine-readable register of public organisations. Fields used: "
            "format, parent/child_organisations, govuk_status, content_id, "
            "analytics_identifier. Raw pages cached under "
            "data/sources/raw/govuk-organisations-api/ by ingest_organisations.py. "
            f"This access: {pages} pages, {total_orgs} organisations."
        ),
    }
    write_json(SOURCE_RECORD, record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=BASE_URL,
                        help="API entry point (default: %(default)s)")
    parser.add_argument("--max-pages", type=int, default=0,
                        help="stop after N pages (0 = all; use a small N to smoke-test)")
    parser.add_argument("--sleep", type=float, default=0.5,
                        help="seconds to pause between pages (courtesy; default 0.5)")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="per-request timeout in seconds (default 30)")
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)
    accessed_date = datetime.date.today().isoformat()

    url = args.base_url
    page_num = 0
    total_orgs_seen = 0
    reported_total = None
    reported_pages = None
    saved_files = []

    print(f"Ingesting {args.base_url} -> {os.path.relpath(RAW_DIR, REPO)}")
    while url:
        page_num += 1
        print(f"  page {page_num}: {url}")
        data = fetch(url, timeout=args.timeout)

        results = data.get("results", [])
        total_orgs_seen += len(results)
        if reported_total is None:
            reported_total = data.get("total")
            reported_pages = data.get("pages")

        page_path = os.path.join(RAW_DIR, f"page-{page_num:03d}.json")
        write_json(page_path, data)
        saved_files.append(os.path.basename(page_path))

        if args.max_pages and page_num >= args.max_pages:
            print(f"  (stopping early: --max-pages {args.max_pages})")
            break

        url = absolute(data.get("next_page_url"))
        if url and args.sleep:
            time.sleep(args.sleep)

    # An ingest-meta sidecar: a faithful record of exactly what this pull grabbed.
    meta = {
        "base_url": args.base_url,
        "accessed_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "pages_fetched": page_num,
        "pages_reported_by_api": reported_pages,
        "organisations_fetched": total_orgs_seen,
        "organisations_reported_by_api": reported_total,
        "page_files": saved_files,
        "partial": bool(args.max_pages) and page_num >= args.max_pages,
    }
    write_json(os.path.join(RAW_DIR, "_ingest_meta.json"), meta)

    refresh_source_record(accessed_date, page_num, total_orgs_seen)

    print("\n--- ingest summary ---")
    print(f"pages fetched:        {page_num}")
    print(f"pages reported (API): {reported_pages}")
    print(f"orgs fetched:         {total_orgs_seen}")
    print(f"orgs reported (API):  {reported_total}")
    print(f"raw cache:            {os.path.relpath(RAW_DIR, REPO)}")
    print(f"source record:        {os.path.relpath(SOURCE_RECORD, REPO)}")
    if meta["partial"]:
        print("NOTE: partial pull (--max-pages). Re-run without --max-pages for the full set.")
    if reported_total is not None and not meta["partial"] and total_orgs_seen != reported_total:
        print(f"WARN: fetched {total_orgs_seen} orgs but API reported {reported_total}. Investigate before "
              "transforming.")


if __name__ == "__main__":
    main()
