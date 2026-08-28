"""Auth liveness/readiness probes. ``/livez`` must not import this module's checks."""

from __future__ import annotations

import os
from pathlib import Path

from auth.db import resolve_db_path
from auth.security import TokenError, create_access_token, decode_access_token


def _directory_writable(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    probe = directory / ".readyz_probe"
    try:
        probe.write_bytes(b"ok")
        probe.unlink(missing_ok=True)
    except OSError:
        return False
    return True


def jwt_signing_ready_reason() -> str | None:
    """Return a short reason if JWT signing keys are missing or unusable."""
    if not (os.environ.get("JWT_PRIVATE_KEY") or "").strip():
        return "jwt private key is not configured"
    if not (os.environ.get("JWT_PUBLIC_KEY") or "").strip():
        return "jwt public key is not configured"
    try:
        token = create_access_token({"readyz_probe": True}, expires_minutes=1)
        decoded = decode_access_token(token)
        if decoded.get("readyz_probe") is not True:
            return "jwt signing key unusable"
    except (ValueError, TokenError):
        return "jwt signing key unusable"
    return None


def auth_ready_reason() -> str | None:
    """Return a short reason if auth dependencies are not ready, else ``None``.

    Does not create the database file. Parent must exist and be writable.
    If ``users.json`` already exists, it must also be writable.
    """
    path = resolve_db_path()
    parent = path.parent
    if not _directory_writable(parent):
        return "tinydb parent path is missing or not writable"
    if path.exists():
        try:
            with path.open("a", encoding="utf-8"):
                pass
        except OSError:
            return "tinydb file is not writable"
    return jwt_signing_ready_reason()
