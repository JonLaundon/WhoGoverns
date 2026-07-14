"""validate.py — the gate must fail CLOSED (review finding #3).

Before hardening, a vanished data file loaded as [] and validation still exited 0. The
gate now treats a missing data file as an integrity failure and exits non-zero.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root, for `import validate`
import validate  # noqa: E402

import store  # noqa: E402


def test_validate_fails_closed_on_missing_data_files(tmp_path, monkeypatch, capsys):
    # Point the data layer at an empty dir: every required array file is absent.
    monkeypatch.setattr(store, "DATA", str(tmp_path))
    with pytest.raises(SystemExit) as exc:
        validate.main()
    assert exc.value.code == 1                       # fails, rather than silently passing on []
    assert "is missing" in capsys.readouterr().out   # and says why
