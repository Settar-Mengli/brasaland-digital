from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supplier_directory.db import get_db, reset_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "suppliers.json"
    monkeypatch.setenv("SUPPLIER_DB_PATH", str(db_path))
    reset_db()
    get_db()
    yield
    reset_db()
