"""store.py — the data-access layer. Verify round-trips, ordering, and upsert-merge."""
import store


def test_load_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    assert store.load("bodies") == []


def test_save_load_roundtrip_sorted_by_primary_key(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    store.save("bodies", [{"body_id": "b", "name": "B"}, {"body_id": "a", "name": "A"}])
    loaded = store.load("bodies")
    assert [r["body_id"] for r in loaded] == ["a", "b"]  # sorted by primary key
    assert loaded[0]["name"] == "A"


def test_load_map_keys_on_primary_key(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    store.save("bodies", [{"body_id": "x", "name": "X"}])
    assert store.load_map("bodies")["x"]["name"] == "X"


def test_upsert_incoming_wins_and_preserves_others(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    store.save("bodies", [{"body_id": "x", "name": "old"}, {"body_id": "y", "name": "Y"}])
    store.upsert("bodies", [{"body_id": "x", "name": "new"}, {"body_id": "z", "name": "Z"}])
    m = store.load_map("bodies")
    assert m["x"]["name"] == "new"          # incoming overwrites
    assert set(m) == {"x", "y", "z"}        # existing y kept, new z added


def test_every_type_has_a_primary_key():
    # A new data type must declare its key or store.save/load_map would KeyError.
    assert set(store.TYPES) == set(store.PK)


def _pr(pid, office, current=True, end=None):
    return {"person_role_id": pid, "office_id": office, "is_current": current, "end_date": end}


def test_upsert_current_holders_retires_replaced_holder(tmp_path, monkeypatch):
    # The reshuffle landmine: the successor must not leave TWO current holders of one office.
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    store.save("person-roles", [_pr("personrole-chancellor-jane", "office-chancellor")])
    merged, retired = store.upsert_current_holders(
        [_pr("personrole-chancellor-john", "office-chancellor")], "2026-07-14")
    assert (merged, retired) == (1, 1)
    m = store.load_map("person-roles")
    assert m["personrole-chancellor-john"]["is_current"] is True
    assert m["personrole-chancellor-jane"]["is_current"] is False       # retired, not left current
    assert m["personrole-chancellor-jane"]["end_date"] == "2026-07-14"  # with an end date
    # exactly one current holder for the office
    assert sum(1 for r in m.values() if r["office_id"] == "office-chancellor" and r["is_current"]) == 1


def test_upsert_current_holders_leaves_other_offices_untouched(tmp_path, monkeypatch):
    # One ingest must never retire an office it did not touch (e.g. officials vs ministers).
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    store.save("person-roles", [_pr("personrole-permsec-x", "office-permsec-x")])
    store.upsert_current_holders([_pr("personrole-chancellor-john", "office-chancellor")], "2026-07-14")
    assert store.load_map("person-roles")["personrole-permsec-x"]["is_current"] is True


def test_remove_records_for_bodies_cascades(tmp_path, monkeypatch):
    # A departed body takes its offices/holders/budgets and any touching edge with it.
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    store.save("bodies", [{"body_id": "gone"}, {"body_id": "keep"}])
    store.save("offices", [{"office_id": "o1", "body_id": "gone"}, {"office_id": "o2", "body_id": "keep"}])
    store.save("budgets", [{"budget_record_id": "b1", "body_id": "gone"}])
    store.save("relationships", [{"relationship_id": "r1", "from_body_id": "keep", "to_body_id": "gone"},
                                 {"relationship_id": "r2", "from_body_id": "keep", "to_body_id": "keep"}])
    removed = store.remove_records_for_bodies(["gone"])
    assert removed == {"bodies": 1, "offices": 1, "budgets": 1, "relationships": 1}
    assert [b["body_id"] for b in store.load("bodies")] == ["keep"]
    assert [o["office_id"] for o in store.load("offices")] == ["o2"]
    assert store.load("budgets") == []
    assert [r["relationship_id"] for r in store.load("relationships")] == ["r2"]  # edge to 'gone' dropped


def test_remove_records_for_bodies_noop_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    assert store.remove_records_for_bodies([]) == {}
