"""Deferred daily/global usage caps for the public knowledge route."""

from __future__ import annotations

import os


def public_daily_caps_enabled() -> bool:
    raw = os.environ.get("PUBLIC_DAILY_CAPS_ENABLED", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def check_public_usage_caps(client_key: str) -> None:
    """Raise when daily/global caps are exceeded (stub until Hetzner hardening)."""
    if not public_daily_caps_enabled():
        return
    # TODO(post-video): Redis INCR per client_key + global daily keys.
    _ = client_key
