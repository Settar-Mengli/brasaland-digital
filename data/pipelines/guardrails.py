"""Layered guardrails for the Brasaland support agent.

Classifiers + in-process session extraction ledger. ``session_id`` is owned by
callers (request / LangGraph configurable) — never stored in AgentState.
"""

from __future__ import annotations

import re
import time
from typing import Any, Literal, TypedDict

FailureType = Literal["structural", "content", "security"]
MemoryDecision = Literal["approve", "reject", "edit"]

PERSONAL_USE_REDIRECT = (
    "I'm here to help with Brasaland's procedures and recipes. "
    "Do you have a question about your shift or preparation?"
)

SENSITIVE_DATA_REFUSAL = (
    "I can't share proprietary formulas, supplier contract terms or prices, "
    "or payroll and performance information. "
    "I can help with Brasaland procedures, training topics, and the official manuals — "
    "what do you need for your shift?"
)

INJECTION_REFUSAL = (
    "I can't change my instructions or act outside Brasaland's rules. "
    "I'm here to help with Brasaland's procedures and recipes. "
    "Do you have a question about your shift or preparation?"
)

SMALL_TALK_RECONNECT = (
    "Glad you're here. At Brasaland we focus on consistent prep and service standards — "
    "what can I help you with for your shift or preparation?"
)

OUTPUT_SAFE_REFUSAL = (
    "I can't share that. "
    "I'm here to help with Brasaland's procedures and recipes. "
    "Do you have a question about your shift or preparation?"
)

SESSION_TTL_SECONDS = 3600

# Process-wide trigger counts (also reset by clear_session_guard).
PROCESS_COUNTS: dict[FailureType, int] = {
    "structural": 0,
    "content": 0,
    "security": 0,
}

SESSION_GUARD: dict[str, dict[str, Any]] = {}


class GuardDecision(TypedDict):
    blocked: bool
    failure_type: FailureType | None
    action: Literal["block", "redirect", "pass"]
    answer: str | None
    reason: str | None


_INJECTION = re.compile(
    r"(ignore\s+(all\s+)?(your\s+)?(previous|prior|above)\s+instructions|"
    r"forget\s+(that\s+)?you\s+work\s+for|"
    r"forget\s+(you'?re|you\s+are)\s+(a\s+)?brasaland|"
    r"act\s+as\s+(an?\s+)?unrestricted|"
    r"act\s+with\s+no\s+rules|"
    r"disregard\s+(your\s+)?(system\s+)?(prompt|instructions)|"
    r"you\s+are\s+now\s+(dan|jailbroken|unrestricted))",
    re.IGNORECASE,
)

_PERSONAL_USE = re.compile(
    r"\b(write\s+(me\s+)?(an?\s+)?(poem|essay|homework)|"
    r"do\s+my\s+homework|"
    r"help\s+me\s+write\s+(an?\s+)?(poem|essay)|"
    r"generate\s+(some\s+)?code\s+for\s+(my|another|a)\s+project|"
    r"personal\s+advice|"
    r"be\s+my\s+(therapist|life\s+coach))\b",
    re.IGNORECASE,
)

_SMALL_TALK = re.compile(
    r"^\s*(hi|hello|hey|good\s+(morning|afternoon|evening)|"
    r"how'?s\s+(your\s+)?(shift|day)|thanks|thank\s+you|"
    r"how\s+are\s+you)[\s!.?]*$",
    re.IGNORECASE,
)

# Exact proprietary formula / fragment extraction (CONTEXT §3) — refuse on turn 1.
_RECIPE_FRAGMENT = re.compile(
    r"("
    r"master\s+recipe|"
    r"proprietary\s+(formula|recipe)|"
    r"(exact\s+)?(quantit(?:y|ies)|proportions?|measurements?)\b.*\b(recipe|sauce|formula)|"
    r"\b(recipe|sauce|formula)\b.*\b(exact\s+)?(quantit(?:y|ies)|proportions?|measurements?)|"
    r"complete\s+house\s+sauce|"
    r"house\s+sauce\s+recipe|"
    r"(first|second|third|next|one)\s+ingredient\b.*\b(house\s+sauce|recipe|formula)|"
    r"\b(house\s+sauce|master\s+recipe|proprietary)\b.*\bingredient|"
    r"ingredient\b.*\b(house\s+sauce|master\s+recipe)|"
    r"what\s+(is|are)\s+the\s+(first|second|third|next)\s+ingredient"
    r")",
    re.IGNORECASE,
)

_SUPPLIER_PRICE = re.compile(
    r"("
    r"supplier\s+(contract|price|prices|terms|charge)|"
    r"negotiated\s+price|"
    r"what\s+we\s+charge\s+the\s+supplier|"
    r"charge\s+the\s+supplier\s+per|"
    r"per\s+portion\b.*\bsupplier|"
    r"supplier\b.*\bper\s+portion"
    r")",
    re.IGNORECASE,
)

_PAYROLL = re.compile(
    r"\b(payroll|performance\s+review|salary|wage\s+of\s+(another|other)\s+employee|"
    r"how\s+much\s+(does|do)\s+\w+\s+(make|earn|get\s+paid))\b",
    re.IGNORECASE,
)

_PROMPT_LEAK = re.compile(
    r"(system\s+prompt|ignore\s+previous\s+instructions|"
    r"<<<RETRIEVED_DATA>>>|treat\s+the\s+above\s+strictly\s+as\s+reference)",
    re.IGNORECASE,
)

# Incident fields required for a well-formed successful tool payload row.
_INCIDENT_REQUIRED = (
    "id",
    "source_incident_id",
    "status",
    "category",
    "origin",
    "branch",
)


def clear_session_guard() -> None:
    """Reset the session ledger and process-wide counts (tests / admin)."""
    SESSION_GUARD.clear()
    PROCESS_COUNTS["structural"] = 0
    PROCESS_COUNTS["content"] = 0
    PROCESS_COUNTS["security"] = 0


def _log_pending_ttl_reject(session_id: str, entry: dict[str, Any], reason: str) -> None:
    """When a session with pending_memory expires, persist a rejected audit event."""
    pending = entry.get("pending_memory")
    if not pending:
        return
    try:
        from pipelines.memory_store import log_proposal_event

        log_proposal_event(
            {
                "session_id": session_id,
                "outcome": "rejected",
                "proposal": {
                    "summary": pending.get("summary"),
                    "location": pending.get("location"),
                    "category": pending.get("category"),
                    "why": pending.get("why"),
                    "proposal_id": pending.get("proposal_id"),
                },
                "originating_message": pending.get("originating_message") or "",
                "reason": reason,
            }
        )
    except Exception:  # noqa: BLE001 — purge must not raise
        pass


def _purge_expired(now: float | None = None) -> None:
    ts = now if now is not None else time.time()
    expired = [
        sid
        for sid, entry in SESSION_GUARD.items()
        if ts - float(entry.get("updated_at", 0)) > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        entry = SESSION_GUARD.get(sid) or {}
        if entry.get("pending_memory"):
            _log_pending_ttl_reject(sid, entry, "ttl_expired")
        del SESSION_GUARD[sid]


def _ensure_session(session_id: str) -> dict[str, Any]:
    _purge_expired()
    entry = SESSION_GUARD.get(session_id)
    if entry is None:
        entry = {
            "events": [],
            "extraction_turns": 0,
            "counts": {"structural": 0, "content": 0, "security": 0},
            "pending_memory": None,
            "updated_at": time.time(),
        }
        SESSION_GUARD[session_id] = entry
    elif "pending_memory" not in entry:
        entry["pending_memory"] = None
    return entry


def get_pending_memory(session_id: str | None) -> dict[str, Any] | None:
    """Return pending memory proposal for the session, if any."""
    if not session_id:
        return None
    entry = get_session_entry(session_id)
    if entry is None:
        return None
    pending = entry.get("pending_memory")
    return dict(pending) if isinstance(pending, dict) else None


def set_pending_memory(
    session_id: str | None, pending: dict[str, Any] | None
) -> None:
    """Set or clear the one pending memory proposal for the session."""
    if not session_id:
        return
    entry = _ensure_session(session_id)
    entry["pending_memory"] = dict(pending) if pending else None
    entry["updated_at"] = time.time()


def clear_pending_memory(session_id: str | None) -> None:
    set_pending_memory(session_id, None)


def record_guardrail(
    session_id: str | None,
    failure_type: FailureType,
    *,
    reason: str | None = None,
    extraction: bool = False,
) -> None:
    """Increment process + session counters; optionally bump extraction_turns."""
    PROCESS_COUNTS[failure_type] = PROCESS_COUNTS.get(failure_type, 0) + 1
    if not session_id:
        return
    entry = _ensure_session(session_id)
    entry["counts"][failure_type] = int(entry["counts"].get(failure_type, 0)) + 1
    entry["updated_at"] = time.time()
    entry["events"].append(
        {
            "failure_type": failure_type,
            "reason": reason,
            "extraction": extraction,
            "ts": entry["updated_at"],
        }
    )
    if extraction:
        entry["extraction_turns"] = int(entry.get("extraction_turns", 0)) + 1


def get_session_entry(session_id: str) -> dict[str, Any] | None:
    _purge_expired()
    entry = SESSION_GUARD.get(session_id)
    return dict(entry) if entry else None


def get_guardrail_summary(session_id: str | None = None) -> dict[str, Any]:
    """Return per-failure-type trigger counts (session or process-wide)."""
    _purge_expired()
    if session_id:
        entry = SESSION_GUARD.get(session_id)
        if entry is None:
            return {
                "structural": 0,
                "content": 0,
                "security": 0,
                "session_id": session_id,
                "extraction_turns": 0,
            }
        return {
            "structural": int(entry["counts"].get("structural", 0)),
            "content": int(entry["counts"].get("content", 0)),
            "security": int(entry["counts"].get("security", 0)),
            "session_id": session_id,
            "extraction_turns": int(entry.get("extraction_turns", 0)),
        }
    return {
        "structural": int(PROCESS_COUNTS.get("structural", 0)),
        "content": int(PROCESS_COUNTS.get("content", 0)),
        "security": int(PROCESS_COUNTS.get("security", 0)),
        "sessions": len(SESSION_GUARD),
    }


def is_injection_attempt(question: str) -> bool:
    return bool(_INJECTION.search(question or ""))


def is_personal_use(question: str) -> bool:
    return bool(_PERSONAL_USE.search(question or ""))


def is_small_talk(question: str) -> bool:
    return bool(_SMALL_TALK.match((question or "").strip()))


def is_recipe_fragment_extraction(question: str) -> bool:
    return bool(_RECIPE_FRAGMENT.search(question or ""))


def is_supplier_price_request(question: str) -> bool:
    return bool(_SUPPLIER_PRICE.search(question or ""))


def is_payroll_request(question: str) -> bool:
    return bool(_PAYROLL.search(question or ""))


def is_sensitive_extraction(question: str) -> bool:
    """True when the turn alone seeks §3 secrets (formula fragment, prices, payroll)."""
    return (
        is_recipe_fragment_extraction(question)
        or is_supplier_price_request(question)
        or is_payroll_request(question)
    )


# In-domain follow-ups that must never escalate as recipe reconstruction.
# Includes location-operational cues (CONTEXT-memory §2 hours/suppliers).
_IN_DOMAIN_FOLLOWUP = re.compile(
    r"\b(points?|tier|gold|silver|bronze|ticket|incident|allergen|"
    r"loyalty|waste|supplier\s+order|discount|program|"
    r"hours?|opening|closing|schedule|what\s+time|"
    r"open(?:s|ing)?|clos(?:e|es|ing)|delivery\s+days?|"
    r"hora(?:s)?|abre|abren|cierra|cierran|horario|entrega(?:s)?)\b",
    re.IGNORECASE,
)

# Location store-ops questions (hours / schedule / delivery days) — in-domain.
_LOCATION_OPERATIONAL = re.compile(
    r"("
    r"\b(what\s+time|hours?|opening|closing|schedule)\b|"
    r"\b(open(?:s|ing)?|clos(?:e|es|ing))\b|"
    r"\b(delivery\s+days?|supplier\s+delivery)\b|"
    r"\b(hora(?:s)?|abre|abren|cierra|cierran|horario|d[ií]as?\s+de\s+entrega|entrega(?:s)?)\b"
    r")",
    re.IGNORECASE,
)


def is_location_operational_query(question: str) -> bool:
    """True for named-location ops (hours/open/close/schedule/delivery days).

    CONTEXT-memory §2 / store operations — does not cover supplier prices or recipes.
    """
    return bool(_LOCATION_OPERATIONAL.search(question or ""))


# Narrow continuation cues: recipe-tied tokens only (no loyalty/ticket/allergen).
_EXTRACTION_CONTINUATION = re.compile(
    r"("
    r"(first|second|third|fourth|next)\s+ingredient\b|"
    r"(and\s+)?(the\s+)?(first|second|third|fourth|next)\b.{0,48}\b"
    r"(ingredient|amount|quantity|proportion|measurement|formula|sauce)s?\b|"
    r"\b(exact\s+)?(amount|quantity|proportion|measurement|formula)s?\b|"
    r"\b(next\s+)?ingredient\b|"
    r"\b(house\s+)?sauce\b.{0,24}\b(ingredient|amount|quantity|proportion)\b"
    r")",
    re.IGNORECASE | re.DOTALL,
)


def is_extraction_continuation(question: str) -> bool:
    """True for ordinal/amount/ingredient follow-ups continuing a prior extraction.

    Narrow on purpose: does not match bare in-domain follow-ups (points, tiers,
    tickets, allergens, location hours) even when the session already has
    extraction_turns.
    """
    q = (question or "").strip()
    if not q:
        return False
    if _IN_DOMAIN_FOLLOWUP.search(q) or is_location_operational_query(q):
        return False
    return bool(_EXTRACTION_CONTINUATION.search(q))


def classify_input(question: str) -> GuardDecision:
    """Classify a user question. Does not mutate the session ledger.

    Sensitive / injection / personal / small-talk checks run first and are
    unchanged. Location-operational questions (hours, schedule, delivery days)
    are explicitly in-domain and pass when those refuse lanes do not fire.
    """
    q = question or ""
    if is_injection_attempt(q):
        return {
            "blocked": True,
            "failure_type": "security",
            "action": "block",
            "answer": INJECTION_REFUSAL,
            "reason": "instruction_override",
        }
    if is_sensitive_extraction(q):
        return {
            "blocked": True,
            "failure_type": "security",
            "action": "block",
            "answer": SENSITIVE_DATA_REFUSAL,
            "reason": "sensitive_extraction",
        }
    if is_personal_use(q):
        return {
            "blocked": True,
            "failure_type": "content",
            "action": "redirect",
            "answer": PERSONAL_USE_REDIRECT,
            "reason": "personal_use",
        }
    if is_small_talk(q):
        return {
            "blocked": True,
            "failure_type": "content",
            "action": "redirect",
            "answer": SMALL_TALK_RECONNECT,
            "reason": "small_talk_redirect",
        }
    if is_location_operational_query(q):
        return {
            "blocked": False,
            "failure_type": None,
            "action": "pass",
            "answer": None,
            "reason": "location_operational",
        }
    return {
        "blocked": False,
        "failure_type": None,
        "action": "pass",
        "answer": None,
        "reason": None,
    }


# Explicit memory approve/edit — bare yes/sí/ok alone is NOT enough.
_MEMORY_APPROVE = re.compile(
    r"("
    r"^\s*(yes|sí|si)[,!]?\s+(please\s+)?(remember|save|store|keep)\b|"
    r"\b(please\s+)?(remember|save|store|keep)\s+(that|this|it)\b|"
    r"\b(yes|sí|si)[,!]?\s+(please\s+)?(guárdalo|guardalo|recuérdalo|recuerdalo)\b|"
    r"\b(guárdalo|guardalo|recuérdalo|recuerdalo|aprobad[oa]?)\b|"
    r"\b(confirm|approve)\s+(that|this|it|the\s+memory)?\b|"
    r"\bsí[,!]?\s+guárdalo\b|"
    r"\byes[,!]?\s+remember\b|"
    r"^\s*save\s+it\b|"
    r"^\s*keep\s+it\b|"
    r"^\s*store\s+it\b"
    r")",
    re.IGNORECASE,
)

# EDIT cues — must win over refuse/approve (value correction, including "as X, not Y").
_MEMORY_EDIT = re.compile(
    r"("
    r"\b(change|edit|update|correct)\s+(it|that|this|the\s+memory)?\s*(to|:)\s*(?P<v1>.+)|"
    r"\b(make\s+it)\s+(?P<v2>.+)|"
    r"\b(actually,?\s+remember|remember\s+instead)\s*:?\s*(?P<v3>.+)|"
    r"\bremember\s+(?:it|that|this)\s+as\s+(?P<v4>.+)|"
    r"\b(rather)\s+(?!not\s+(store|save|remember|keep)\b)(?:remember\s+)?(?P<v5>.+)|"
    r"\b(corrige|cambia|edita)\s*:?\s*(?P<v6>.+)|"
    r"\b(en\s+vez(?:\s+de)?|mejor)\s*:?\s*(?P<v7>.+)|"
    r"\bedit\s*:\s*(?P<v8>.+)"
    r")",
    re.IGNORECASE | re.DOTALL,
)

# Refusal-of-storage only — never bare mid-sentence "not"/"no".
_MEMORY_REFUSE_STORE = re.compile(
    r"("
    r"\b(don'?t|dont|do\s+not|never)\s+(please\s+)?(remember|save|store|keep)\b|"
    r"\bno\s+lo\s+(recuerdes|guardes|almacenes)\b|"
    r"\b(no|nunca)\s+(?:me\s+)?(?:lo\s+)?(recuerdes|guardes|almacenes)\b|"
    r"\brather\s+not\s+(store|save|remember|keep)\b|"
    r"\bnot\s+(store|save|remember|keep)\s+(it|that|this)\b"
    r")",
    re.IGNORECASE,
)

_BARE_AFFIRM = re.compile(
    r"^\s*(yes|sí|si|ok|okay|yep|yeah|sure)\s*[.!]?\s*$",
    re.IGNORECASE,
)

_BARE_NO = re.compile(
    r"^\s*(no|nope|nah)\s*[.!]?\s*$",
    re.IGNORECASE,
)

_TRAILING_NOT_CLAUSE = re.compile(
    r"\s*,\s*not\b.+$",
    re.IGNORECASE | re.DOTALL,
)


def _extract_edit_value(question: str) -> str | None:
    """Return revised memory text when an edit/correction cue + new value is present."""
    m = _MEMORY_EDIT.search(question or "")
    if not m:
        return None
    edited: str | None = None
    for name, value in m.groupdict().items():
        if name.startswith("v") and value and value.strip():
            edited = value.strip()
    if not edited:
        # Fallback: last non-empty unnamed group with content.
        for group in m.groups():
            if group and len(group.strip()) > 1:
                edited = group.strip()
    if not edited:
        return None
    # Prefer the corrected value before a trailing ", not <old>" contrast.
    edited = _TRAILING_NOT_CLAUSE.sub("", edited).strip(" .,;:")
    # Drop leading filler from "it as …" style captures already handled by named groups.
    if len(edited) < 1:
        return None
    return edited


def classify_memory_decision(
    question: str,
) -> tuple[MemoryDecision, str | None]:
    """Classify a user reply against a pending memory proposal.

    Precedence: storage-refusal REJECT → EDIT (value correction) → APPROVE →
    default reject (silence / small-talk / bare yes-ok / topic-change).

    Storage refusal matches don't/do-not/never + remember|save|store|keep,
    \"rather not store/save/remember/keep\", not-store-it/that/this (and ES
    equivalents) — never a bare mid-sentence \"not\".
    Returns (decision, edited_summary_or_None).
    """
    q = (question or "").strip()
    if not q:
        return "reject", None

    # 1) Storage-refusal REJECT first (incl. "rather not store").
    if _MEMORY_REFUSE_STORE.search(q) or _BARE_NO.match(q):
        return "reject", None

    # 2) EDIT — value correction (e.g. "remember it as 11:30, not 11").
    edited = _extract_edit_value(q)
    if edited:
        return "edit", edited

    # 3) APPROVE — explicit save cue (not a refusal; refusals already returned).
    if _MEMORY_APPROVE.search(q):
        return "approve", None

    # 4) Default reject: small-talk, bare affirm, ambiguity, topic-change.
    if is_small_talk(q) or _BARE_AFFIRM.match(q):
        return "reject", None

    return "reject", None


def strip_memory_decision_clause(question: str) -> str:
    """Remove approve/edit cue spans so residual question text can be routed."""
    q = (question or "").strip()
    if not q:
        return ""
    # Split on sentence boundaries; drop sentences that are pure approve/edit.
    parts = re.split(r"(?<=[.!?])\s+", q)
    kept: list[str] = []
    for part in parts:
        decision, _ = classify_memory_decision(part)
        if decision == "approve" and not re.search(
            r"\?", part
        ) and len(part.split()) <= 12:
            continue
        if decision == "edit" and _MEMORY_EDIT.fullmatch(part.strip()):
            continue
        # Also strip leading approve clause before a residual question.
        cleaned = _MEMORY_APPROVE.sub("", part).strip(" ,;-")
        if cleaned:
            kept.append(cleaned if cleaned != part.strip() else part)
    residual = " ".join(kept).strip()
    # If whole message was approve+question without clear split, strip approve prefix.
    if not residual or residual == q:
        m = _MEMORY_APPROVE.search(q)
        if m and m.start() == 0:
            residual = q[m.end() :].strip(" ,;-")
            # Drop conjunction leftovers
            residual = re.sub(
                r"^(and|also|también|y)\b[, ]*",
                "",
                residual,
                flags=re.IGNORECASE,
            ).strip()
    return residual


def apply_input_guard(
    question: str, session_id: str | None
) -> GuardDecision:
    """Classify and, when blocking, record ledger / process counts.

    Also escalates: if the session already has a proprietary-extraction event and
    this turn looks like a keyword-less continuation, refuse as security.
    """
    decision = classify_input(question)
    if decision["blocked"] and decision["failure_type"] is not None:
        extraction = decision["reason"] == "sensitive_extraction"
        record_guardrail(
            session_id,
            decision["failure_type"],
            reason=decision["reason"],
            extraction=extraction,
        )
        return decision

    if session_id and is_extraction_continuation(question):
        entry = get_session_entry(session_id)
        if entry is not None and int(entry.get("extraction_turns", 0)) >= 1:
            decision = {
                "blocked": True,
                "failure_type": "security",
                "action": "block",
                "answer": SENSITIVE_DATA_REFUSAL,
                "reason": "session_extraction_continuation",
            }
            record_guardrail(
                session_id,
                "security",
                reason="session_extraction_continuation",
                extraction=True,
            )
            return decision

    return decision


def validate_tool_result(tool_result: dict[str, Any] | None) -> GuardDecision:
    """Structural check on MCP/ticket tool payload shape."""
    if tool_result is None:
        return {
            "blocked": False,
            "failure_type": None,
            "action": "pass",
            "answer": None,
            "reason": None,
        }
    if not isinstance(tool_result, dict):
        return {
            "blocked": True,
            "failure_type": "structural",
            "action": "block",
            "answer": None,
            "reason": "tool_result_not_dict",
        }
    if "ok" not in tool_result:
        return {
            "blocked": True,
            "failure_type": "structural",
            "action": "block",
            "answer": None,
            "reason": "tool_result_missing_ok",
        }
    if tool_result.get("ok"):
        incidents = tool_result.get("incidents")
        if not isinstance(incidents, list):
            return {
                "blocked": True,
                "failure_type": "structural",
                "action": "block",
                "answer": None,
                "reason": "incidents_not_list",
            }
        for row in incidents:
            if not isinstance(row, dict):
                return {
                    "blocked": True,
                    "failure_type": "structural",
                    "action": "block",
                    "answer": None,
                    "reason": "incident_not_dict",
                }
            missing = [f for f in _INCIDENT_REQUIRED if f not in row]
            if missing:
                return {
                    "blocked": True,
                    "failure_type": "structural",
                    "action": "block",
                    "answer": None,
                    "reason": f"incident_missing_fields:{','.join(missing)}",
                }
    return {
        "blocked": False,
        "failure_type": None,
        "action": "pass",
        "answer": None,
        "reason": None,
    }


def validate_output(answer: str | None) -> GuardDecision:
    """Output validation before returning to the caller."""
    if answer is None or not isinstance(answer, str) or not answer.strip():
        return {
            "blocked": True,
            "failure_type": "structural",
            "action": "block",
            "answer": OUTPUT_SAFE_REFUSAL,
            "reason": "empty_or_invalid_answer",
        }
    if _PROMPT_LEAK.search(answer):
        return {
            "blocked": True,
            "failure_type": "security",
            "action": "block",
            "answer": OUTPUT_SAFE_REFUSAL,
            "reason": "prompt_leak",
        }
    # Block answers that invent exact proprietary house-sauce formulas.
    if re.search(
        r"house\s+sauce.{0,80}(\d+\s*(g|kg|ml|cups?|tbsp|tsp)|exact\s+proportions)",
        answer,
        re.IGNORECASE | re.DOTALL,
    ):
        return {
            "blocked": True,
            "failure_type": "security",
            "action": "block",
            "answer": SENSITIVE_DATA_REFUSAL,
            "reason": "sensitive_in_output",
        }
    return {
        "blocked": False,
        "failure_type": None,
        "action": "pass",
        "answer": None,
        "reason": None,
    }
