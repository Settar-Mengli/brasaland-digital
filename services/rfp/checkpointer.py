"""RFP LangGraph Redis checkpointer (context-manager factory).

``RedisSaver.from_conn_string`` returns a context manager: the connection
closes on exit. Callers must enter it per graph operation - never cache a
process-global saver.

Why Redis (not Postgres): the Supabase transaction pooler (:6543) rejects the
Postgres saver's prepared statements (DuplicatePreparedStatement), and the
Supabase direct endpoint (:5432) is IPv6-only and unreachable from the Docker
network. Redis is already in compose and reachable by both ``rfp`` and
``rfp-worker`` over IPv4 via ``REDIS_URL``. (The original Postgres checkpointer
plan was dropped for those reasons.)

Usage::

    with checkpointer_cm() as saver:
        graph = builder.compile(checkpointer=saver)
        graph.invoke(...)
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from urllib.parse import urlparse

from langgraph.checkpoint.redis import RedisSaver

logger = logging.getLogger(__name__)


def _redis_host(url: str) -> str:
    try:
        host = urlparse(url).hostname
    except Exception:  # noqa: BLE001 - never leak URL guts in logs
        return "unknown"
    return host or "unknown"


def _resolve_redis_url() -> str:
    """Require REDIS_URL (shared compose Redis for rfp + rfp-worker)."""
    url = os.environ.get("REDIS_URL")
    if not url or not url.strip():
        raise RuntimeError("REDIS_URL is not set")
    url = url.strip()
    logger.info(
        "RFP checkpointer using REDIS_URL (backend=redis host=%s)",
        _redis_host(url),
    )
    return url


@contextmanager
def checkpointer_cm() -> Iterator[RedisSaver]:
    """Yield a ``RedisSaver`` for one graph operation, then close the connection.

    Uses ``RedisSaver.from_conn_string`` only. Per-operation lifetime.
    """
    redis_url = _resolve_redis_url()
    with RedisSaver.from_conn_string(redis_url) as saver:
        yield saver


def run_setup() -> None:
    """Create LangGraph checkpoint keys/indexes (OPERATOR invokes explicitly).

    Import-safe: does not run on import.
    """
    redis_url = _resolve_redis_url()
    with RedisSaver.from_conn_string(redis_url) as saver:
        saver.setup()
    logger.info(
        "RFP checkpointer setup() completed (backend=redis host=%s)",
        _redis_host(redis_url),
    )


if __name__ == "__main__":
    run_setup()
