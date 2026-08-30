"""Runtime flags for the public guest knowledge route."""

from __future__ import annotations

import os


def public_knowledge_enabled() -> bool:
    raw = os.environ.get("PUBLIC_KNOWLEDGE_ENABLED", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}
