from __future__ import annotations

from pathlib import Path

import pytest

from auth.db import _resolve_path, get_db, reset_db


def test_resolve_path_uses_explicit_argument(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit.json"
    assert _resolve_path(explicit) == explicit


def test_resolve_path_uses_auth_db_path_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_path = tmp_path / "from-env.json"
    monkeypatch.setenv("AUTH_DB_PATH", str(env_path))
    assert _resolve_path(None) == env_path


def test_resolve_path_uses_default_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTH_DB_PATH", raising=False)
    resolved = _resolve_path(None)
    assert resolved.name == "users.json"
    assert resolved.parent.name == "data"


def test_get_db_opens_explicit_path_and_reopens_on_path_change(
    tmp_path: Path,
) -> None:
    reset_db()
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"

    first_db = get_db(first_path)
    second_db = get_db(second_path)

    assert first_db is not second_db
    assert first_path.exists()
    assert second_path.exists()
    reset_db()


def test_reset_db_when_no_connection_is_open() -> None:
    reset_db()
    reset_db()
