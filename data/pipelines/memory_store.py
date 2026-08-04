"""Explicit read/write agent memory (location + category) with audit log.

Never-store scrub applies to memory entries AND audit originating_message.
Write-path poisoning rejects contradictions of CONTEXT allowed-value lists /
proprietary claims. Read-side conflict filter drops memory that fights RAG chunks.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

MemoryCategory = Literal[
    "hours", "suppliers", "known_incidents", "comms_prefs"
]
AuditOutcome = Literal["proposed", "approved", "rejected", "edited"]

MEMORY_CATEGORIES: tuple[str, ...] = (
    "hours",
    "suppliers",
    "known_incidents",
    "comms_prefs",
)
ENTRY_TTL_SECONDS = 180 * 24 * 3600  # 180 days
REDIS_ENTRY_PREFIX = "agent_memory:entry:"
REDIS_AUDIT_KEY = "agent_memory:audit"

ALLOWED_INCIDENT_STATUS = frozenset(
    {"open", "in_progress", "resolved", "discarded"}
)
ALLOWED_INCIDENT_ORIGIN = frozenset({"customer", "branch", "internal"})
ALLOWED_INCIDENT_CATEGORY = frozenset(
    {
        "QUEJA_CLIENTE",
        "EQUIPAMIENTO",
        "ABASTECIMIENTO",
        "CALIDAD_ALIMENTO",
        "PERSONAL",
    }
)

_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
_PHONE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}(?!\d)"
)
_TOKENISH = re.compile(
    r"\b(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|"
    r"sk-[A-Za-z0-9]{16,}|"
    r"Bearer\s+[A-Za-z0-9._\-]+|"
    r"api[_-]?key\s*[:=]\s*\S+)\b",
    re.IGNORECASE,
)
_PAYROLL = re.compile(
    r"\b(payroll|salary|wage|compensation|performance\s+review)\b",
    re.IGNORECASE,
)
_PII_NAME_EMAIL = re.compile(
    r"\b(customer\s+(name|email|phone|address)|credit\s+card|"
    r"ssn|social\s+security|payment\s+details)\b",
    re.IGNORECASE,
)
_PROPRIETARY = re.compile(
    r"("
    r"house\s+sauce.{0,40}(exact|proportion|formula|\d+\s*(g|ml|kg))|"
    r"master\s+recipe|"
    r"proprietary\s+(formula|recipe)|"
    r"supplier\s+(contract|negotiated)\s+price|"
    r"negotiated\s+price"
    r")",
    re.IGNORECASE | re.DOTALL,
)
_LOYALTY_POINTS = re.compile(
    r"\b(bronze|silver|gold)\b.{0,40}?(\d+)\s*\+?\s*points?",
    re.IGNORECASE | re.DOTALL,
)
_STATUS_CLAIM = re.compile(
    r"\bstatus\b.{0,24}\b(open|in_progress|resolved|discarded|closed|pending)\b",
    re.IGNORECASE,
)


class MemoryEntry(TypedDict):
    location: str
    category: str
    summary: str
    updated_at: str
    proposal_id: str | None


class MemoryWrite(TypedDict, total=False):
    location: str
    category: str
    summary: str
    proposal_id: str | None


class WriteResult(TypedDict):
    ok: bool
    reason: str | None
    entry: MemoryEntry | None


class ProposalAuditEvent(TypedDict, total=False):
    id: str
    session_id: str | None
    outcome: AuditOutcome
    proposal: dict[str, Any] | None
    originating_message: str
    timestamp: str
    reason: str | None


# In-memory backend (tests / when REDIS_URL unset).
_ENTRIES: dict[str, MemoryEntry] = {}
_AUDIT: list[ProposalAuditEvent] = []
_FORCE_MEMORY_BACKEND: str | None = None  # "memory" | "redis" | None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry_key(location: str, category: str) -> str:
    loc = _normalize_location_token(location) or "unknown"
    cat = (category or "known_incidents").strip().lower()
    return f"{loc}:{cat}"


def _normalize_location_token(loc: str) -> str:
    """Normalize location labels for tolerant match (Miami Beach ↔ miami_beach)."""
    s = (loc or "").strip().lower()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def locations_match(stored: str | None, query: str | None) -> bool:
    """True when stored and query location labels refer to the same place."""
    if not query:
        return True
    if not stored:
        return False
    a = _normalize_location_token(stored)
    b = _normalize_location_token(query)
    if not a or not b:
        return False
    if a == b:
        return True
    # Compact form: "miamibeach" == "miami_beach"
    return a.replace("_", "") == b.replace("_", "")


def _redis_client() -> Any | None:
    if _FORCE_MEMORY_BACKEND == "memory":
        return None
    url = os.environ.get("REDIS_URL", "").strip()
    if not url or _FORCE_MEMORY_BACKEND == "redis" and not url:
        if _FORCE_MEMORY_BACKEND == "redis":
            raise RuntimeError("REDIS_URL is not set")
        return None
    if not url:
        return None
    try:
        import redis

        return redis.Redis.from_url(url, decode_responses=True)
    except Exception:  # noqa: BLE001 — fall back to in-memory
        return None


def force_memory_backend(kind: str | None) -> None:
    """Test helper: ``\"memory\"``, ``\"redis\"``, or ``None`` (auto)."""
    global _FORCE_MEMORY_BACKEND
    _FORCE_MEMORY_BACKEND = kind


def clear_memory_for_tests() -> None:
    """Reset in-memory store and optionally flush Redis keys used by tests."""
    _ENTRIES.clear()
    _AUDIT.clear()
    client = _redis_client()
    if client is None:
        return
    try:
        for key in client.scan_iter(match=f"{REDIS_ENTRY_PREFIX}*"):
            client.delete(key)
        client.delete(REDIS_AUDIT_KEY)
    except Exception:  # noqa: BLE001
        pass


def scrub_for_audit(text: str) -> str:
    """Redact PII / payroll / token-shaped content before audit persistence."""
    if not text:
        return ""
    out = text
    out = _EMAIL.sub("[REDACTED_EMAIL]", out)
    out = _TOKENISH.sub("[REDACTED_SECRET]", out)
    out = _PHONE.sub("[REDACTED_PHONE]", out)
    out = _PAYROLL.sub("[REDACTED_PAYROLL]", out)
    out = _PII_NAME_EMAIL.sub("[REDACTED_PII]", out)
    return out


def _contains_never_store(text: str) -> str | None:
    """Return rejection reason if text must never enter memory, else None."""
    if not text or not text.strip():
        return "empty_summary"
    if _EMAIL.search(text) or _PHONE.search(text) or _PII_NAME_EMAIL.search(text):
        return "customer_pii"
    if _PAYROLL.search(text):
        return "payroll"
    if _TOKENISH.search(text):
        return "secrets"
    if _PROPRIETARY.search(text):
        return "proprietary_claim"
    # Allowed-value poisoning: invented incident statuses.
    for match in _STATUS_CLAIM.finditer(text):
        status = match.group(1).lower()
        if status not in ALLOWED_INCIDENT_STATUS:
            return "allowed_value_contradiction"
    return None


def validate_memory_payload(
    *, summary: str, category: str | None = None
) -> str | None:
    """Never-store + poisoning checks for a candidate memory summary."""
    reason = _contains_never_store(summary)
    if reason:
        return reason
    cat = (category or "").strip().lower()
    if cat and cat not in MEMORY_CATEGORIES:
        return "invalid_category"
    return None


def filter_memory_against_chunks(
    entries: list[MemoryEntry],
    rag_chunks: list[dict[str, Any]] | None,
) -> list[MemoryEntry]:
    """Drop memory entries that conflict with retrieved manual facts (read-side)."""
    if not entries:
        return []
    if not rag_chunks:
        return list(entries)
    chunk_text = "\n".join(
        str(c.get("text") or "") for c in rag_chunks
    ).lower()
    if not chunk_text.strip():
        return list(entries)

    # Loyalty-tier points in manuals vs memory.
    manual_tiers: dict[str, set[str]] = {}
    for match in _LOYALTY_POINTS.finditer(chunk_text):
        tier = match.group(1).lower()
        pts = match.group(2)
        manual_tiers.setdefault(tier, set()).add(pts)

    kept: list[MemoryEntry] = []
    for entry in entries:
        summary = entry.get("summary") or ""
        conflict = False
        for match in _LOYALTY_POINTS.finditer(summary.lower()):
            tier = match.group(1).lower()
            pts = match.group(2)
            if tier in manual_tiers and pts not in manual_tiers[tier]:
                conflict = True
                break
        if not conflict:
            kept.append(entry)
    return kept


def _parse_updated_at(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _is_expired(entry: MemoryEntry, now: float | None = None) -> bool:
    ts = now if now is not None else time.time()
    return ts - _parse_updated_at(entry.get("updated_at") or "") > ENTRY_TTL_SECONDS


def read_memory(
    *,
    location: str | None = None,
    category: str | None = None,
) -> list[MemoryEntry]:
    """Read consolidated memory entries (expired entries omitted)."""
    client = _redis_client()
    entries: list[MemoryEntry] = []
    if client is not None:
        pattern = f"{REDIS_ENTRY_PREFIX}*"
        if location and category:
            pattern = f"{REDIS_ENTRY_PREFIX}{_entry_key(location, category)}"
        try:
            keys = list(client.scan_iter(match=pattern))
            for key in keys:
                raw = client.get(key)
                if not raw:
                    continue
                data = json.loads(raw)
                if location and not locations_match(data.get("location"), location):
                    continue
                if category and data.get("category") != category:
                    continue
                entries.append(data)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            entries = []
    else:
        for key, entry in list(_ENTRIES.items()):
            if location and not locations_match(entry.get("location"), location):
                continue
            if category and entry.get("category") != category:
                continue
            entries.append(entry)

    alive: list[MemoryEntry] = []
    for entry in entries:
        if _is_expired(entry):
            loc = entry.get("location") or "unknown"
            cat = entry.get("category") or "known_incidents"
            _delete_entry(loc, cat)
            continue
        alive.append(entry)
    return alive


def _delete_entry(location: str, category: str) -> None:
    key = _entry_key(location, category)
    client = _redis_client()
    if client is not None:
        try:
            client.delete(f"{REDIS_ENTRY_PREFIX}{key}")
        except Exception:  # noqa: BLE001
            pass
    _ENTRIES.pop(key, None)


def write_memory(entry: MemoryWrite) -> WriteResult:
    """Upsert one (location, category) entry after never-store / poisoning checks."""
    summary = (entry.get("summary") or "").strip()
    location = (entry.get("location") or "unknown").strip() or "unknown"
    category = (entry.get("category") or "known_incidents").strip()
    reason = validate_memory_payload(summary=summary, category=category)
    if reason:
        return {"ok": False, "reason": reason, "entry": None}

    stored: MemoryEntry = {
        "location": location,
        "category": category,
        "summary": summary,
        "updated_at": _utc_now_iso(),
        "proposal_id": entry.get("proposal_id"),
    }
    key = _entry_key(location, category)
    client = _redis_client()
    if client is not None:
        try:
            client.set(
                f"{REDIS_ENTRY_PREFIX}{key}",
                json.dumps(stored, ensure_ascii=False),
            )
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "reason": f"redis_write_failed:{exc}", "entry": None}
    _ENTRIES[key] = stored
    consolidate_location(location)
    return {"ok": True, "reason": None, "entry": stored}


def consolidate_location(location: str) -> None:
    """Dedupe whitespace within each category for a location (upsert already bounds)."""
    for cat in MEMORY_CATEGORIES:
        rows = read_memory(location=location, category=cat)
        if not rows:
            continue
        # Single upsert slot — normalize summary whitespace only.
        row = rows[0]
        cleaned = re.sub(r"\s+", " ", (row.get("summary") or "").strip())
        if cleaned != row.get("summary"):
            key = _entry_key(location, cat)
            updated: MemoryEntry = {
                "location": row["location"],
                "category": row["category"],
                "summary": cleaned,
                "updated_at": row.get("updated_at") or _utc_now_iso(),
                "proposal_id": row.get("proposal_id"),
            }
            _ENTRIES[key] = updated
            client = _redis_client()
            if client is not None:
                try:
                    client.set(
                        f"{REDIS_ENTRY_PREFIX}{key}",
                        json.dumps(updated, ensure_ascii=False),
                    )
                except Exception:  # noqa: BLE001
                    pass


def log_proposal_event(event: ProposalAuditEvent) -> ProposalAuditEvent:
    """Append audit event; scrub originating_message before persist (Fix 1)."""
    scrubbed = scrub_for_audit(event.get("originating_message") or "")
    record: ProposalAuditEvent = {
        "id": event.get("id") or str(uuid.uuid4()),
        "session_id": event.get("session_id"),
        "outcome": event.get("outcome") or "proposed",
        "proposal": event.get("proposal"),
        "originating_message": scrubbed,
        "timestamp": event.get("timestamp") or _utc_now_iso(),
        "reason": event.get("reason"),
    }
    client = _redis_client()
    if client is not None:
        try:
            client.rpush(
                REDIS_AUDIT_KEY,
                json.dumps(record, ensure_ascii=False),
            )
        except Exception:  # noqa: BLE001 — still keep in-process
            pass
    _AUDIT.append(record)
    return record


def list_audit(*, limit: int = 50) -> list[ProposalAuditEvent]:
    """Return recent audit events (newest last, then sliced from the end)."""
    client = _redis_client()
    if client is not None:
        try:
            raw_rows = client.lrange(REDIS_AUDIT_KEY, -max(limit, 1), -1)
            out: list[ProposalAuditEvent] = []
            for raw in raw_rows:
                out.append(json.loads(raw))
            return out
        except Exception:  # noqa: BLE001
            pass
    if limit <= 0:
        return []
    return list(_AUDIT[-limit:])


def guess_location_from_text(text: str) -> str | None:
    """Best-effort location cue for read-back filtering."""
    q = text or ""
    patterns = [
        (r"\bmiami\s*beach\b", "miami_beach"),
        (r"\bmiami\b", "miami"),
        (r"\bmedell[ií]n\b", "medellin"),
        (r"\bbogot[aá]\b", "bogota"),
        (r"\bzaragoza\b", "zaragoza"),
        (r"\blocation\s*7\b", "location_7"),
        (r"\bCOL-0?(\d+)\b", None),
        (r"\bFLA-0?(\d+)\b", None),
    ]
    for pat, loc in patterns:
        m = re.search(pat, q, re.IGNORECASE)
        if not m:
            continue
        if loc:
            return loc
        return m.group(0).upper().replace(" ", "")
    return None


__all__ = [
    "ENTRY_TTL_SECONDS",
    "MEMORY_CATEGORIES",
    "MemoryEntry",
    "MemoryWrite",
    "ProposalAuditEvent",
    "WriteResult",
    "clear_memory_for_tests",
    "consolidate_location",
    "filter_memory_against_chunks",
    "force_memory_backend",
    "guess_location_from_text",
    "list_audit",
    "locations_match",
    "log_proposal_event",
    "read_memory",
    "scrub_for_audit",
    "validate_memory_payload",
    "write_memory",
]
