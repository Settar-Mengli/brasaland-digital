"""Shared SlowAPI limiter for reporting enqueue."""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
ENQUEUE_RATE_LIMIT = os.environ.get("RATE_LIMIT_REPORTING_ENQUEUE", "10/minute")
