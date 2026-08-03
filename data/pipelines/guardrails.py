"""Layered guardrails for the Brasaland support agent.

Classifiers + in-process session extraction ledger. ``session_id`` is owned by
callers (request / LangGraph configurable) — never stored in AgentState.
"""

from __future__ import annotations

import re
import time
from typing import Any, Literal, TypedDict

FailureType = Literal["structural", "content", "security"]

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


def _purge_expired(now: float | None = None) -> None:
    ts = now if now is not None else time.time()
    expired = [
        sid
        for sid, entry in SESSION_GUARD.items()
        if ts - float(entry.get("updated_at", 0)) > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del SESSION_GUARD[sid]


def _ensure_session(session_id: str) -> dict[str, Any]:
    _purge_expired()
    entry = SESSION_GUARD.get(session_id)
    if entry is None:
        entry = {
            "events": [],
            "extraction_turns": 0,
            "counts": {"structural": 0, "content": 0, "security": 0},
            "updated_at": time.time(),
        }
        SESSION_GUARD[session_id] = entry
    return entry


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
_IN_DOMAIN_FOLLOWUP = re.compile(
    r"\b(points?|tier|gold|silver|bronze|ticket|incident|allergen|"
    r"loyalty|waste|supplier\s+order|discount|program)\b",
    re.IGNORECASE,
)

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
    tickets, allergens) even when the session already has extraction_turns.
    """
    q = (question or "").strip()
    if not q:
        return False
    if _IN_DOMAIN_FOLLOWUP.search(q):
        return False
    return bool(_EXTRACTION_CONTINUATION.search(q))


def classify_input(question: str) -> GuardDecision:
    """Classify a user question. Does not mutate the session ledger."""
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
    return {
        "blocked": False,
        "failure_type": None,
        "action": "pass",
        "answer": None,
        "reason": None,
    }


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
