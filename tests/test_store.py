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
