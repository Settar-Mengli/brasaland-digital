"""Shared SlowAPI limiter for metered knowledge/agent query routes."""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Align with analyze (10/minute); knowledge RAG gets slight headroom.
AGENT_QUERY_RATE_LIMIT = os.environ.get("RATE_LIMIT_AGENT_QUERY", "10/minute")
KNOWLEDGE_QUERY_RATE_LIMIT = os.environ.get(
    "RATE_LIMIT_KNOWLEDGE_QUERY", "20/minute"
)
