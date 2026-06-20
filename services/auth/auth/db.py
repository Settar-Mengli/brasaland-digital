"""TinyDB access for the auth service.

The database is a lazy module-level singleton: the first call to ``get_db()``
opens ``data/users.json`` (or an explicit path) and later calls reuse the
same ``TinyDB`` instance until ``reset_db()`` or a path change.

Each uvicorn worker process holds its own singleton. Run a single worker in
production, or point every worker at the same file via a shared path.

``AUTH_DB_PATH`` overrides the JSON file location and is intended for tests
and local tooling only. Leave it unset in production shells so the default
``data/users.json`` under this service is used.
"""

from __future__ import annotations

import os
from pathlib import Path

from tinydb import TinyDB

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "users.json"
_db: TinyDB | None = None
_db_path: Path | None = None


def _resolve_path(path: Path | None) -> Path:
    if path is not None:
        return path
    env_path = os.environ.get("AUTH_DB_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_PATH


def get_db(path: Path | None = None) -> TinyDB:
    global _db, _db_path

    resolved = _resolve_path(path)
    if _db is None or _db_path != resolved:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        _db = TinyDB(resolved)
        _db_path = resolved

    return _db


def reset_db() -> None:
    global _db, _db_path

    if _db is not None:
        _db.close()
    _db = None
    _db_path = None
