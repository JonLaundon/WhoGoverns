#!/usr/bin/env python3
"""Ingest current ministers into Office and PersonRole records (office-centred).

One job: for each ministerial department (plus the Prime Minister's Office), fetch
the GOV.UK content API object, read links.ordered_ministers -> role_appointments,
and emit:
  - Office   records (the post: "Chancellor of the Exchequer"), one per role, at a body;
  - PersonRole records (the current holder in that post).
Raw responses are cached; the content-API SourceRecord is refreshed.

This is the officials layer of the office-centred map (decision #13): the post is a
first-class node, the person sits in it, the department hosts it. Only current
appointments are taken (Spiral 1 = the sitting government); senior officials below
minister are deferred.

    py -3 pipeline/ingest_ministers.py            # fetch, cache, write records
    py -3 pipeline/ingest_ministers.py --dry-run  # fetch + report, write nothing

Boring by design: stdlib only, one job, polite HTTP (UA, timeout, retry, pause).
"""
import argparse
import datetime
import json
import os
import re
import time
import urllib.error
import urllib.request

import store

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (this file lives in pipeline/)
RAW_DIR = os.path.join(REPO, "data", "sources", "raw", "govuk-content-ministers")
SOURCE_ID = "source-official-dataset-govuk-content-api"
CONTENT_API = "https://www.gov.uk/api/content/government/organisations/"
USER_AGENT = "WhoGoverns/0.1 (open UK-state dataset; contact jonnylaundon@gmail.com)"

# The PM is the centre of the office-centred map but the API classes the PM's Office
# as "Other", so it is fetched explicitly alongside the ministerial departments.
EXTRA_SLUGS = {"prime-ministers-office-10-downing-street"}

# Cabinet-rank posts whose titles do not contain "Secretary of State".
CABINET_TITLES = {
    "chancellor of the exchequer", "chancellor of the duchy of lancaster",
    "lord chancellor", "leader of the house of commons", "leader of the house of lords",
    "minister without portfolio", "paymaster general", "chief secretary to the treasury",
    "attorney general", "deputy prime minister", "first secretary of state",
}
HONORIFICS = {"the", "rt", "hon", "hon.", "sir", "dame", "dr", "dr.", "lord", "baroness",
              "mp", "kc", "qc", "kcb", "kbe", "cbe", "obe", "mbe", "ksg", "msp", "ms"}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def fetch(url, timeout, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    last = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None  # org has no content item; caller skips
            last = err
        except (urllib.error.URLError, TimeoutError) as err:
            last = err
        wait = attempt * 2
        print("  ! fetch failed ({}/{}) {}: {} — retry in {}s".format(attempt, retries, url, last, wait))
        time.sleep(wait)
    raise SystemExit("Gave up fetching {}: {}".format(url, last))


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def person_slug(name):
    tokens = [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t and t not in HONORIFICS]
    return "-".join(tokens) or slugify(name)


def office_type_for(title):
    t = title.strip().lower()
    if t == "prime minister":
        return "prime_minister"
    if "minister of state" in t:
        return "junior_minister"
    if "parliamentary under" in t or "parliamentary secretary" in t:
        return "junior_minister"
    if "secretary of state" in t or t in CABINET_TITLES:
        return "cabinet_minister"
    # Unambiguous junior ranks the title-word rules miss: whips, the junior Treasury
    # secretaries (Chief Secretary is already cabinet above), and the Solicitor General.
    if "whip" in t or "secretary to the treasury" in t or "solicitor general" in t or "advocate general" in t:
        return "junior_minister"
    return "other"


def source_record(accessed_date, n_orgs):
    return {
        "source_id": SOURCE_ID,
        "title": "GOV.UK Content API — organisation ministers",
        "source_type": "official_dataset",
        "publisher": "Government Digital Service (GOV.UK)",
        "url": "https://www.gov.uk/api/content/government/organisations",
        "accessed_date": accessed_date,
        "publication_date": None,
        "version_date": accessed_date,
        "legal_status": "current",
        "licence": "Open Government Licence v3.0",
        "notes": ("Per-organisation content items; links.ordered_ministers -> "
                  "role_appointments used for current ministers. Raw responses cached "
                  "under data/sources/raw/govuk-content-ministers/ by ingest_ministers.py. "
                  "This access: {} organisations.".format(n_orgs)),
    }


def target_slugs():
    depts = set()
    for b in store.load("bodies"):
        if b["body_type"] == "ministerial_department":
            depts.add(b["govuk_organisation_slug"])
    # EXTRA_SLUGS (the PM's Office) go first so cross-org roles like Prime Minister
    # anchor to their literal home rather than to whichever department sorts first.
    depts -= EXTRA_SLUGS
    return sorted(EXTRA_SLUGS) + sorted(s for s in depts if s)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="fetch + report; write nothing")
    parser.add_argument("--sleep", type=float, default=0.5, help="pause between orgs (default 0.5)")
    parser.add_argument("--timeout", type=float, default=30.0, help="per-request timeout (default 30)")
    args = parser.parse_args()

    body_ids = {b["body_id"] for b in store.load("bodies")}
    slugs = target_slugs()
    accessed_date = datetime.date.today().isoformat()

    offices, person_roles = {}, {}   # id -> record (dedup)
    office_body = {}                 # office_id -> body_id it was first seen at
    type_counts, other_titles = {}, []
    no_ministers, missing_body = [], []

    print("Ingesting ministers for {} organisations".format(len(slugs)))
    for slug in slugs:
        body_id = "uk-state-body-" + slug
        if body_id not in body_ids:
            missing_body.append(slug)
            continue
        url = CONTENT_API + slug
        data = fetch(url, timeout=args.timeout)
        if data is None:
            no_ministers.append(slug)
            continue
        if not args.dry_run:
            write_json(os.path.join(RAW_DIR, slug + ".json"), data)

        ministers = data.get("links", {}).get("ordered_ministers", [])
        if not ministers:
            no_ministers.append(slug)
        for person in ministers:
            pname = person.get("title", "").strip()
            for ra in person.get("links", {}).get("role_appointments", []):
                if not ra.get("details", {}).get("current"):
                    continue
                role_list = ra.get("links", {}).get("role", [])
                if not role_list:
                    continue
                role = role_list[0]
                rtitle = role.get("title", "").strip()
                rslug = slugify(role.get("base_path", "").split("/")[-1] or rtitle)
                office_id = "office-" + rslug
                otype = office_type_for(rtitle)

                # Office: one per role. First body wins; note if a role spans bodies.
                if office_id not in offices:
                    offices[office_id] = {
                        "office_id": office_id,
                        "title": rtitle,
                        "body_id": body_id,
                        "office_type": otype,
                        "source_ids": [SOURCE_ID],
                        "notes": None if otype != "other" else "office_type heuristic = other; review.",
                        "record_status": "extracted",
                        "last_reviewed": None,
                    }
                    office_body[office_id] = body_id
                    type_counts[otype] = type_counts.get(otype, 0) + 1
                    if otype == "other":
                        other_titles.append(rtitle)

                started = (ra.get("details", {}).get("started_on") or "")[:10] or None
                pr_id = "personrole-{}-{}".format(rslug, person_slug(pname))
                person_roles[pr_id] = {
                    "person_role_id": pr_id,
                    "person_name": pname,
                    "office_id": office_id,
                    "body_id": office_body[office_id],
                    "start_date": started,
                    "end_date": None,
                    "is_current": True,
                    "source_ids": [SOURCE_ID],
                    "notes": None,
                    "record_status": "extracted",
                    "last_reviewed": None,
                }
        if args.sleep:
            time.sleep(args.sleep)

    if not args.dry_run:
        store.upsert("offices", list(offices.values()))
        store.upsert("person-roles", list(person_roles.values()))
        store.upsert("sources", [source_record(accessed_date, len(slugs))])

    # ---- report ----
    print("\n--- ingest_ministers summary{} ---".format(" (DRY RUN)" if args.dry_run else ""))
    print("organisations fetched:  {}".format(len(slugs) - len(missing_body)))
    print("offices (roles):        {}".format(len(offices)))
    print("person-roles (current): {}".format(len(person_roles)))
    print("office_type distribution:")
    for k in sorted(type_counts, key=lambda x: -type_counts[x]):
        print("  {:4} {}".format(type_counts[k], k))
    if other_titles:
        print("\noffice_type=other (review these titles): {}".format(len(other_titles)))
        for t in sorted(set(other_titles)):
            print("    - {}".format(t))
    if no_ministers:
        print("\norgs with no current ministers: {}  {}".format(len(no_ministers), no_ministers))
    if missing_body:
        print("\n!! target slug with no Body record (skipped): {}".format(missing_body))


if __name__ == "__main__":
    main()
