from __future__ import annotations

from typing import Any

from tinydb import Query

from auth.db import get_db
from auth.types import UserRecord


def _table() -> Any:
    return get_db().table("users")


def _next_id(records: list[UserRecord]) -> int:
    """Return the next user id as max(existing ids) + 1.

    Assumes a single-process writer. Concurrent inserts could produce duplicate
    ids; that is acceptable for this single-process CLI/API scope.
    """
    if not records:
        return 1
    return max(record["id"] for record in records) + 1


def create_user(record: dict[str, Any]) -> UserRecord:
    table = _table()
    existing = table.all()
    user_id = _next_id(existing)
    stored: UserRecord = {
        "id": user_id,
        "email": record["email"],
        "hashed_password": record["hashed_password"],
        "is_active": bool(record["is_active"]),
        "is_admin": bool(record["is_admin"]),
        "created_at": record["created_at"],
        "reset_token_hash": record.get("reset_token_hash"),
        "reset_token_expires": record.get("reset_token_expires"),
        "name": str(record.get("name") or ""),
        "phone": str(record.get("phone") or ""),
        "address": str(record.get("address") or ""),
    }
    table.insert(stored)
    return stored


def get_user_by_id(user_id: int) -> UserRecord | None:
    query = Query()
    result = _table().get(query.id == user_id)
    if result is None:
        return None
    return result


def get_user_by_email(email: str) -> UserRecord | None:
    query = Query()
    result = _table().get(query.email == email)
    if result is None:
        return None
    return result


def list_users() -> list[UserRecord]:
    return sorted(_table().all(), key=lambda record: record["id"])


def update_user(user_id: int, fields: dict[str, Any]) -> UserRecord | None:
    query = Query()
    table = _table()
    if not table.contains(query.id == user_id):
        return None

    table.update(fields, query.id == user_id)
    return get_user_by_id(user_id)


def delete_user(user_id: int) -> bool:
    query = Query()
    table = _table()
    removed = table.remove(query.id == user_id)
    return len(removed) > 0
