"""Shared RFP draft-prompt helpers: metadata serialization and prose style rules."""

from __future__ import annotations

from typing import Any

DRAFT_PROSE_STYLE_RULES = (
    "Write client-facing prose. Weave metadata values into sentences. "
    "Never copy field labels, keys, None, null, or sentinels "
    '("not stated", "n/a"). Omit missing figures silently unless a compliance '
    "rule requires acknowledging a gap — then use one natural phrase such as "
    '"final figure to be confirmed", never null or not stated.'
)

_METADATA_LABELS: tuple[tuple[str, str], ...] = (
    ("client_name", "Client name"),
    ("location", "Location"),
    ("service_type", "Service type"),
    ("scope", "Scope"),
    ("deadline", "Deadline"),
    ("budget_range", "Budget range"),
    ("open_questions", "Open questions"),
)

_OMIT_TEXTS = frozenset({"none", "null", "not stated"})

_FENCE_OPEN = "<<<METADATA>>>"
_FENCE_CLOSE = "<<<END METADATA>>>"
_EMPTY_METADATA = "(no metadata extracts)"


def _strip_fence_delimiters(value: str) -> str:
    """Delete every ``<<<`` and ``>>>`` so interpolated values cannot close a fence."""
    return value.replace("<<<", "").replace(">>>", "")


def _should_omit_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    return stripped.casefold() in _OMIT_TEXTS


def _prepare_text(value: Any) -> str | None:
    if value is None:
        return None
    text = _strip_fence_delimiters(str(value)).strip()
    if _should_omit_text(text):
        return None
    return text


def _prepare_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        prepared = _prepare_text(value)
        return [prepared] if prepared is not None else None
    items: list[str] = []
    for item in value:
        prepared = _prepare_text(item)
        if prepared is not None:
            items.append(prepared)
    return items or None


def format_metadata_for_prompt(metadata: dict[str, Any] | None) -> str:
    """Serialize known metadata keys as a fenced block; omit empty/sentinel values."""
    source = metadata or {}
    lines: list[str] = []
    for key, label in _METADATA_LABELS:
        raw = source.get(key)
        if key == "open_questions":
            items = _prepare_list(raw)
            if not items:
                continue
            lines.append(f"{label}:")
            lines.extend(f"- {item}" for item in items)
            continue
        prepared = _prepare_text(raw)
        if prepared is None:
            continue
        lines.append(f"{label}: {prepared}")
    if not lines:
        return _EMPTY_METADATA
    return f"{_FENCE_OPEN}\n" + "\n".join(lines) + f"\n{_FENCE_CLOSE}"


def format_key_aspects_for_prompt(aspects: list[Any] | None) -> str:
    """One bullet per non-empty aspect; fence-stripped; never a Python list repr."""
    items = _prepare_list(aspects if aspects is not None else [])
    if not items:
        return ""
    return "\n".join(f"- {item}" for item in items)
