"""compile.build_graph — sponsor truth is the canonical edges, and provenance survives.

Guards two review findings:
  #8 — the body sponsor/parent shown on the map is DERIVED from the relationship edges,
       so the panel and the radial layout can never disagree with them; joint sponsorship
       is exposed in full, not truncated to the first alphabetically.
  #6 — sponsor edges keep their source_id, so a sponsor claim stays followable to its source.
"""
import compile as comp


def _body(bid, body_type="executive_ndpb"):
    return {"body_id": bid, "name": bid, "body_type": body_type, "status": "active"}


def _rel(frm, to, source_id="source-x"):
    fs, ts = frm.split("uk-state-body-")[-1], to.split("uk-state-body-")[-1]
    return {"relationship_id": f"rel-{fs}-sponsors-{ts}", "from_body_id": frm,
            "to_body_id": to, "relationship_type": "sponsors", "source_id": source_id}


def test_sponsor_scalar_derived_from_edges_not_body_field():
    # The stored body field says one thing; the edges say another. The edges win.
    bodies = [
        _body("uk-state-body-dept-a", "ministerial_department"),
        _body("uk-state-body-dept-b", "ministerial_department"),
        dict(_body("uk-state-body-alb"), sponsor_department_id="uk-state-body-STALE"),
    ]
    rels = [_rel("uk-state-body-dept-a", "uk-state-body-alb")]
    g = comp.build_graph(bodies, rels, [], [])
    alb = next(n["data"] for n in g["nodes"] if n["data"]["id"] == "uk-state-body-alb")
    assert alb["sponsor_department_id"] == "uk-state-body-dept-a"   # from the edge, not "STALE"


def test_joint_sponsorship_exposed_in_full():
    bodies = [
        _body("uk-state-body-dept-a", "ministerial_department"),
        _body("uk-state-body-dept-b", "ministerial_department"),
        _body("uk-state-body-alb"),
    ]
    rels = [_rel("uk-state-body-dept-b", "uk-state-body-alb"),
            _rel("uk-state-body-dept-a", "uk-state-body-alb")]
    g = comp.build_graph(bodies, rels, [], [])
    alb = next(n["data"] for n in g["nodes"] if n["data"]["id"] == "uk-state-body-alb")
    assert alb["sponsor_department_ids"] == ["uk-state-body-dept-a", "uk-state-body-dept-b"]  # both, sorted
    assert alb["sponsor_department_id"] == "uk-state-body-dept-a"                              # scalar = first


def test_non_department_parent_is_parent_body_not_sponsor():
    bodies = [_body("uk-state-body-agency", "executive_agency"), _body("uk-state-body-sub")]
    rels = [_rel("uk-state-body-agency", "uk-state-body-sub")]
    g = comp.build_graph(bodies, rels, [], [])
    sub = next(n["data"] for n in g["nodes"] if n["data"]["id"] == "uk-state-body-sub")
    assert sub["sponsor_department_id"] is None
    assert sub["parent_body_id"] == "uk-state-body-agency"


def test_sponsor_edges_keep_source_id():
    bodies = [_body("uk-state-body-dept", "ministerial_department"), _body("uk-state-body-alb")]
    rels = [_rel("uk-state-body-dept", "uk-state-body-alb", source_id="source-govuk")]
    g = comp.build_graph(bodies, rels, [], [])
    edge = next(e["data"] for e in g["edges"] if e["data"]["kind"] == "sponsors")
    assert edge["source_id"] == "source-govuk"


def test_budget_and_staffing_summaries_retain_source_ids():
    b = comp.summarise_budget([{"budget_type": "resource_del", "basis": "net", "programme": None,
                                "amount": 5, "financial_year": "2024-25", "source_id": "source-oscar"}])
    assert b["source_ids"] == ["source-oscar"]
    s = comp.summarise_staffing([{"scope": "group", "grade": None, "profession": None,
                                  "metric": "headcount", "value": 5, "period": "2025",
                                  "notes": None, "source_id": "source-css"}])
    assert s["source_ids"] == ["source-css"]
