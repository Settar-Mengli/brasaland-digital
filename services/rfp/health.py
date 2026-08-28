"""RFP readiness checks. ``/livez`` must not call these functions."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

READYZ_TIMEOUT_SECONDS = 2


class ReadyCheckError(Exception):
    """One bounded readiness check failed."""


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


def _connect_args(url: str) -> dict[str, object]:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {"connect_timeout": READYZ_TIMEOUT_SECONDS}


def check_postgres() -> None:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise ReadyCheckError("DATABASE_URL is not set")
    engine = create_engine(
        url,
        poolclass=NullPool,
        connect_args=_connect_args(url),
    )
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except ReadyCheckError:
        raise
    except Exception as exc:
        raise ReadyCheckError("postgres SELECT 1 failed") from exc
    finally:
        engine.dispose()


def check_redis() -> None:
    url = (os.environ.get("REDIS_URL") or "").strip()
    if not url:
        raise ReadyCheckError("REDIS_URL is not set")
    try:
        import redis
    except ImportError as exc:
        raise ReadyCheckError("redis client is not installed") from exc
    client = redis.Redis.from_url(
        url,
        socket_connect_timeout=READYZ_TIMEOUT_SECONDS,
        socket_timeout=READYZ_TIMEOUT_SECONDS,
    )
    try:
        if client.ping() is not True:
            raise ReadyCheckError("redis PING failed")
    except ReadyCheckError:
        raise
    except Exception as exc:
        raise ReadyCheckError("redis PING failed") from exc
    finally:
        client.close()


def check_checkpoint_path() -> None:
    from checkpointer import resolve_checkpoint_path

    path = Path(resolve_checkpoint_path())
    if not _directory_writable(path.parent):
        raise ReadyCheckError("checkpoint parent path is missing or not writable")


def check_generation_config() -> None:
    flag = (os.environ.get("RFP_REQUIRE_GENERATION_CONFIG") or "").strip().lower()
    if flag not in ("1", "true", "yes"):
        return
    from pipelines.rfp_intake.generation import _rfp_generation_tiers

    if not _rfp_generation_tiers():
        raise ReadyCheckError("generation provider config is missing or incomplete")


def rfp_ready_reason() -> str | None:
    """Run bounded checks in order; return the first failure reason."""
    for check in (
        check_postgres,
        check_redis,
        check_checkpoint_path,
        check_generation_config,
    ):
        try:
            check()
        except ReadyCheckError as exc:
            return str(exc)
    return None
