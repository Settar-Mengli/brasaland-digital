"""RFP LangGraph SQLite checkpointer (context-manager factory).

``SqliteSaver.from_conn_string`` returns a context manager: the connection
closes on exit. Callers must enter it per graph operation - never cache a
process-global saver.

The DB file lives on the Docker named volume ``rfp_checkpoint``, mounted at
``/app/checkpoint`` in both ``rfp`` (FastAPI resume) and ``rfp-worker`` (Celery
start). Override with ``RFP_CHECKPOINT_PATH`` (default
``/app/checkpoint/rfp.sqlite``).

Why SQLite: Postgres saver failed on the Supabase transaction pooler
(DuplicatePreparedStatement) and on direct :5432 (IPv6 unreachable from Docker);
langgraph-checkpoint-redis 0.5.1 was buggy (get_state empty / _key_registry crash
across fresh saver instances). Redis remains only as the Celery broker.

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

from langgraph.checkpoint.sqlite import SqliteSaver

logger = logging.getLogger(__name__)

_DEFAULT_CHECKPOINT_PATH = "/app/checkpoint/rfp.sqlite"


def _resolve_checkpoint_path() -> str:
    path = (os.environ.get("RFP_CHECKPOINT_PATH") or _DEFAULT_CHECKPOINT_PATH).strip()
    if not path:
        raise RuntimeError("RFP_CHECKPOINT_PATH is empty")
    return path


@contextmanager
def checkpointer_cm() -> Iterator[SqliteSaver]:
    """Yield a ``SqliteSaver`` for one graph operation, then close the connection.

    Uses ``SqliteSaver.from_conn_string`` only. Per-operation lifetime.
    """
    path = _resolve_checkpoint_path()
    logger.info("RFP checkpointer using SqliteSaver path=%s", path)
    with SqliteSaver.from_conn_string(path) as saver:
        yield saver


def run_setup() -> None:
    """Create LangGraph checkpoint tables (OPERATOR invokes explicitly).

    Import-safe: does not run on import.
    """
    path = _resolve_checkpoint_path()
    with SqliteSaver.from_conn_string(path) as saver:
        saver.setup()
    logger.info("RFP checkpointer setup() completed path=%s", path)


if __name__ == "__main__":
    run_setup()
