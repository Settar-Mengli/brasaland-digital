"""Shared SlowAPI limiter for RFP upload."""

from __future__ import annotations

import os

from brasaland_proxy_trust import rate_limit_client_key
from slowapi import Limiter

limiter = Limiter(key_func=rate_limit_client_key)
RFP_UPLOAD_RATE_LIMIT = os.environ.get("RATE_LIMIT_RFP_UPLOAD", "10/minute")
