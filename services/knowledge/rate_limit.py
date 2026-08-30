"""Shared SlowAPI limiter for metered knowledge/agent query routes."""

import os

from brasaland_proxy_trust import rate_limit_client_key
from slowapi import Limiter

limiter = Limiter(key_func=rate_limit_client_key)

# Align with analyze (10/minute); knowledge RAG gets slight headroom.
AGENT_QUERY_RATE_LIMIT = os.environ.get("RATE_LIMIT_AGENT_QUERY", "10/minute")
KNOWLEDGE_QUERY_RATE_LIMIT = os.environ.get(
    "RATE_LIMIT_KNOWLEDGE_QUERY", "20/minute"
)
PUBLIC_KNOWLEDGE_QUERY_RATE_LIMIT = os.environ.get(
    "RATE_LIMIT_PUBLIC_KNOWLEDGE_QUERY", "5/minute"
)
