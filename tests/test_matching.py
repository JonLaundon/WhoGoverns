"""The name-matching discipline (ingest_budget): exact + safe containment, NEVER fuzzy/overlap.

These guard the house rule that mis-matches (e.g. Arts Council of Wales -> England, or
British Tourist Authority -> British Transport Police) must not happen.
"""
import ingest_budget as ib


def test_norm_lowercases_strips_punct_and_stopwords():
    assert ib.norm("Ministry of Defence") == "ministry defence"      # 'of' dropped
    assert ib.norm("HM Revenue & Customs") == "hm revenue customs"    # '&'->'and'->dropped


def _index(*names_to_ids):
    """Build the (exact, body_toks) structures match_org expects."""
    exact, body_toks = {}, {}
    for name, bid in names_to_ids:
        exact.setdefault(ib.norm(name), bid)
        body_toks[bid] = ib.toks(name)
    return exact, body_toks


def test_exact_match():
    exact, toks = _index(("Home Office", "uk-state-body-home-office"))
    assert ib.match_org("Home Office", exact, toks) == "uk-state-body-home-office"


def test_containment_matches_legal_suffix():
    # "British Business Bank plc" is the body name + a corporate suffix -> matches.
    exact, toks = _index(("British Business Bank", "uk-state-body-bbb"))
    assert ib.match_org("British Business Bank plc", exact, toks) == "uk-state-body-bbb"


def test_overlap_is_rejected_not_matched():
    # Shared words but neither name contains the other -> must be None (no fuzzy matching).
    exact, toks = _index(("British Transport Police Authority", "uk-state-body-btp"))
    assert ib.match_org("British Tourist Authority", exact, toks) is None


def test_ambiguous_containment_rejected():
    # If the org name would contain-match two different bodies, refuse (unique-only).
    exact, toks = _index(("Arts Council", "uk-state-body-a"),
                         ("Arts Council England", "uk-state-body-b"))
    # "Arts Council office" contains "Arts Council" (a) but not "...England" (b) -> unique -> a.
    assert ib.match_org("Arts Council office", exact, toks) == "uk-state-body-a"
    # A bare unknown org matches nothing.
    assert ib.match_org("Some Other Body", exact, toks) is None
