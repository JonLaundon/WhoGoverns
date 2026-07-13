"""compile.summarise_budget / summarise_staffing — the aggregations behind the entity tabs.

Includes regression tests for two real bugs: budget income leaking into TME, and the
group/core double-count (identical scopes duplicating professions).
"""
import compile as comp


def _budget(**kw):
    base = {"budget_type": "resource_del", "basis": "net", "programme": None,
            "amount": 0, "financial_year": "2024-25"}
    base.update(kw)
    return base


def test_summarise_budget_splits_headline_programmes_income():
    recs = [
        _budget(budget_type="resource_del", amount=100),
        _budget(budget_type="resource_del", programme="Defence", amount=80),
        _budget(budget_type="income", programme="Fees", amount=30),
        _budget(budget_type="income", programme=None, amount=30),
    ]
    s = comp.summarise_budget(recs)
    assert s["headline"]["resource_del_net"] == 100
    assert s["programmes"] == [{"name": "Defence", "net": 80}]
    assert s["income"] == [{"name": "Fees", "value": 30}]
    # income must NOT be counted as a programme
    assert all(p["name"] != "Fees" for p in s["programmes"])


def _staff(scope, value, grade=None, profession=None, notes=None, metric="headcount"):
    return {"scope": scope, "grade": grade, "profession": profession, "metric": metric,
            "value": value, "period": "2025", "notes": notes}


def test_staffing_group_core_split_kept_when_they_differ():
    recs = [_staff("group", 100, notes="disclaimer"), _staff("core", 60)]
    s = comp.summarise_staffing(recs)
    assert s["headcount_total"] == 100
    assert s["core"]["headcount_total"] == 60
    assert s["disclaimer"] == "disclaimer"


def test_staffing_collapses_when_group_equals_core():
    # No real agencies: identical group/core -> single figure, no toggle, no disclaimer.
    recs = [_staff("group", 100, notes="disclaimer"), _staff("core", 100)]
    s = comp.summarise_staffing(recs)
    assert s["core"] is None
    assert s["disclaimer"] is None


def test_staffing_no_duplicate_professions_regression():
    # The Charity Commission bug: scope None + group in one file double-counted professions.
    recs = [_staff(None, 10, profession="Policy"), _staff(None, 5, profession="Legal")]
    s = comp.summarise_staffing(recs)
    names = [p["name"] for p in s["professions"]]
    assert len(names) == len(set(names))            # no duplicates
    assert s["professions"][0]["name"] == "Policy"  # sorted by headcount desc (10 > 5)
