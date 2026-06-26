from __future__ import annotations

from typing import Any, TypedDict

from tinydb import Query

from auth.db import get_db


class RefreshTokenRecord(TypedDict):
    id: int
    user_id: int
    token_hash: str
    expires_at: str
    revoked: bool
    created_at: str


def _table() -> Any:
    return get_db().table("refresh_tokens")


def _next_id(records: list[RefreshTokenRecord]) -> int:
    if not records:
        return 1
    return max(record["id"] for record in records) + 1


def create_refresh_token(record: dict[str, Any]) -> RefreshTokenRecord:
    table = _table()
    existing = table.all()
    token_id = _next_id(existing)
    stored: RefreshTokenRecord = {
        "id": token_id,
        "user_id": record["user_id"],
        "token_hash": record["token_hash"],
        "expires_at": record["expires_at"],
        "revoked": bool(record.get("revoked", False)),
        "created_at": record["created_at"],
    }
    table.insert(stored)
    return stored


def get_by_hash(token_hash: str) -> RefreshTokenRecord | None:
    query = Query()
    result = _table().get(query.token_hash == token_hash)
    if result is None:
        return None
    return result


def revoke(token_hash: str) -> bool:
    query = Query()
    table = _table()
    if not table.contains(query.token_hash == token_hash):
        return False
    table.update({"revoked": True}, query.token_hash == token_hash)
    return True


def revoke_all_for_user(user_id: int) -> int:
    query = Query()
    table = _table()
    updated = table.update({"revoked": True}, query.user_id == user_id)
    return len(updated)
