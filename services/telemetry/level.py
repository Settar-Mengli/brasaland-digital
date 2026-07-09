from __future__ import annotations


def derive_level(event_type: str) -> str:
    if event_type.endswith("_failed") or event_type.endswith("_rejected"):
        return "warning"
    return "info"
