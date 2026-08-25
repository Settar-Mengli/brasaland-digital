"""Auth liveness/readiness probes. ``/livez`` must not import this module's checks."""

from __future__ import annotations

from pathlib import Path

from auth.db import resolve_db_path


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


def auth_ready_reason() -> str | None:
    """Return a short reason if TinyDB is not ready, else ``None``.

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
    return None
