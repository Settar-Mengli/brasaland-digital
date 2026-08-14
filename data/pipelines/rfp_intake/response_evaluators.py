"""Pure evaluators for RFP response drafts (no LLM, no DB)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Bounded generate↔evaluate retries inside each department worker (1 + 2 retries).
ITERATION_LIMIT = 3

# Readability pass band (not specified in CONTEXT-rfp.md — documented here).
READABILITY_MIN_FLESCH = 30.0
READABILITY_MAX_GRADE = 16.0

# Finite competitor deny-list — NOT in CONTEXT-rfp.md; documented for §5 "no competitors".
COMPETITOR_DENYLIST: frozenset[str] = frozenset(
    {
        "mcdonald's",
        "mcdonalds",
        "burger king",
        "kfc",
        "subway",
        "chipotle",
        "starbucks",
        "dominos",
        "domino's",
        "pizza hut",
        "wendy's",
        "wendys",
        "taco bell",
        "arbys",
        "arby's",
        "sodexo",
        "compass group",
        "aramark",
    }
)

_BRAND_PILLARS = (
    "consistent quality",
    "warm experience",
    "speed of service",
)

_CONTEXT_SECTION_5: str | None = None

_PRICE_TOKEN_RE = re.compile(
    r"(?:\$\s*\d|\d[\d,]*(?:\.\d+)?\s*(?:USD|COP)\b|(?:USD|COP)\s*\$?\s*\d)",
    re.IGNORECASE,
)
_SETUP_SLA_RE = re.compile(
    r"(?:"
    r"(?:setup|delivery|deliver|lead\s*time)[^\d]{0,40}(\d{1,2})\s*"
    r"(?:business\s+)?days?"
    r"|"
    r"(\d{1,2})\s*(?:business\s+)?days?[^\w]{0,40}"
    r"(?:setup|delivery|deliver|lead\s*time)"
    r")",
    re.IGNORECASE,
)
_BUDGET_AMOUNT_RE = re.compile(
    r"\$?\s*([\d,]+(?:\.\d+)?)\s*(k|m)?",
    re.IGNORECASE,
)


def _context_rfp_path() -> Path:
    """``data/raw/CONTEXT-rfp.md`` relative to this package (CWD-robust)."""
    # .../data/pipelines/rfp_intake/response_evaluators.py → parents[2] == data/
    return Path(__file__).resolve().parents[2] / "raw" / "CONTEXT-rfp.md"


def _load_compliance_rules() -> str:
    """Load CONTEXT §5 rulebook text (cached). Check logic uses stable rule_ids."""
    global _CONTEXT_SECTION_5
    if _CONTEXT_SECTION_5 is not None:
        return _CONTEXT_SECTION_5

    text = _context_rfp_path().read_text(encoding="utf-8")
    start = text.find("## 5.")
    if start < 0:
        raise RuntimeError("CONTEXT-rfp.md missing '## 5.' heading")
    rest = text[start:]
    # Next markdown heading after §5 (e.g. "## 7.")
    next_match = re.search(r"\n## (?!5\.)", rest)
    section = rest[: next_match.start()] if next_match else rest
    _CONTEXT_SECTION_5 = section.strip()
    return _CONTEXT_SECTION_5


def compliance_requirements_prompt() -> str:
    """Actionable §5 instruction block shared with the response generator prompt.

    Literals match the coded checks in ``evaluate_compliance`` (CURRENCY codes,
    brand-pillar strings, 30-day validity, competitor ban, setup SLA).
    Optionally preceded by the on-disk CONTEXT §5 text so prompt and rulebook stay aligned.
    """
    rulebook = _load_compliance_rules()
    return (
        f"{rulebook}\n\n"
        "When drafting, you MUST satisfy all of the following (automatic checks):\n"
        '- State every price in BOTH Colombian Pesos (COP) and US Dollars (USD) — '
        'include the literal currency codes "COP" and "USD" next to each amount.\n'
        '- Mention all three brand pillars verbatim at least once: '
        '"consistent quality", "warm experience", "speed of service".\n'
        "- Include an offer validity period: state it is valid for 30 days from issuance.\n"
        "- Do not name any competitor.\n"
        "- Do not promise setup or delivery in under 10 business days.\n"
        "- Never invent figures not present in the metadata; if a needed figure is "
        "missing, acknowledge the gap in natural client language "
        '(e.g. "final figure to be confirmed"); never write null, None, or not stated.'
    )


def evaluate_readability(draft: str) -> dict[str, Any]:
    """Score draft with textstat Flesch metrics (same pair as intake extract_node)."""
    import textstat

    sample = draft or " "
    flesch = float(textstat.flesch_reading_ease(sample))
    grade = float(textstat.flesch_kincaid_grade(sample))
    passed = flesch >= READABILITY_MIN_FLESCH and grade <= READABILITY_MAX_GRADE
    return {
        "pass": passed,
        "score": flesch,
        "details": {
            "flesch_reading_ease": flesch,
            "flesch_kincaid_grade": grade,
        },
    }


def evaluate_relevance(draft: str, key_aspects: list[str]) -> dict[str, Any]:
    """Require each key aspect as a case-insensitive substring of the draft."""
    haystack = (draft or "").lower()
    missing: list[str] = []
    for aspect in key_aspects:
        needle = str(aspect).strip()
        if not needle:
            continue
        if needle.lower() not in haystack:
            missing.append(str(aspect))
    return {"pass": not missing, "missing_aspects": missing}


def _parse_budget_usd_ceiling(budget_range: str | None) -> float | None:
    """Best-effort max USD figure from metadata.budget_range (not from draft)."""
    if not budget_range:
        return None
    text = budget_range.strip()
    if not text:
        return None
    amounts: list[float] = []
    for match in _BUDGET_AMOUNT_RE.finditer(text):
        raw = match.group(1).replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        suffix = (match.group(2) or "").lower()
        if suffix == "k":
            value *= 1_000
        elif suffix == "m":
            value *= 1_000_000
        amounts.append(value)
    if not amounts:
        return None
    return max(amounts)


def evaluate_compliance(
    draft: str, budget_range: str | None
) -> dict[str, Any]:
    """Check draft against CONTEXT §5 rules; ceo_threshold flags from budget_range only."""
    _load_compliance_rules()  # ensure CONTEXT §5 is readable; text is rulebook source

    text = draft or ""
    lower = text.lower()
    failed_ids: list[str] = []
    violations: list[str] = []

    # dual_currency
    if _PRICE_TOKEN_RE.search(text):
        has_usd_marker = bool(re.search(r"\bUSD\b", text, re.IGNORECASE))
        has_cop_marker = bool(re.search(r"\bCOP\b", text, re.IGNORECASE))
        if not (has_usd_marker and has_cop_marker):
            failed_ids.append("dual_currency")
            violations.append(
                "Every price must appear in both COP and USD (explicit COP and USD markers)."
            )

    # brand_pillars
    missing_pillars = [p for p in _BRAND_PILLARS if p not in lower]
    if missing_pillars:
        failed_ids.append("brand_pillars")
        violations.append(
            "Missing brand pillar(s): " + ", ".join(missing_pillars) + "."
        )

    # setup_sla
    for match in _SETUP_SLA_RE.finditer(text):
        raw = match.group(1) or match.group(2)
        if raw is None:
            continue
        days = int(raw)
        if days < 10:
            failed_ids.append("setup_sla")
            violations.append(
                f"Setup/delivery must not be promised under 10 business days (found {days})."
            )
            break

    # no_competitors
    for name in COMPETITOR_DENYLIST:
        if name in lower:
            failed_ids.append("no_competitors")
            violations.append(f"Proposal must not name competitor {name!r}.")
            break

    # offer_validity
    has_validity = bool(
        re.search(
            r"(offer\s+valid|validity\s+period|valid\s+for\s+30\s+days|30\s+days\s+from)",
            text,
            re.IGNORECASE,
        )
    ) or ("30 days" in lower and "valid" in lower)
    if not has_validity:
        failed_ids.append("offer_validity")
        violations.append(
            "Proposal must include an offer validity period (30 days from issuance)."
        )

    # ceo_threshold — metadata.budget_range only; never fails compliance.pass
    ceiling = _parse_budget_usd_ceiling(budget_range)
    ceo_required = ceiling is not None and ceiling > 50_000

    return {
        "pass": len(failed_ids) == 0,
        "rule_ids": failed_ids,
        "violations": violations,
        "ceo_approval_required": ceo_required,
    }


def _build_feedback(
    readability: dict[str, Any],
    relevance: dict[str, Any],
    compliance: dict[str, Any],
) -> str:
    parts: list[str] = []
    if not readability.get("pass"):
        details = readability.get("details") or {}
        parts.append(
            "Improve readability "
            f"(Flesch {details.get('flesch_reading_ease')}, "
            f"grade {details.get('flesch_kincaid_grade')}; "
            f"need Flesch>={READABILITY_MIN_FLESCH} and grade<={READABILITY_MAX_GRADE})."
        )
    if not relevance.get("pass"):
        missing = relevance.get("missing_aspects") or []
        parts.append(
            "Incorporate these missing key aspects verbatim: "
            + "; ".join(str(m) for m in missing)
            + "."
        )
    if not compliance.get("pass"):
        for violation in compliance.get("violations") or []:
            parts.append(str(violation))
    return " ".join(parts)


def evaluate_all(
    draft: str,
    key_aspects: list[str],
    budget_range: str | None,
    department_id: str,
) -> dict[str, Any]:
    """Assemble the fixed EvaluationResult for one department draft."""
    readability = evaluate_readability(draft)
    relevance = evaluate_relevance(draft, key_aspects)
    compliance = evaluate_compliance(draft, budget_range)
    overall = bool(
        readability["pass"] and relevance["pass"] and compliance["pass"]
    )
    feedback = "" if overall else _build_feedback(readability, relevance, compliance)
    return {
        "department_id": department_id,
        "readability": readability,
        "relevance": relevance,
        "compliance": {
            "pass": compliance["pass"],
            "rule_ids": compliance["rule_ids"],
            "violations": compliance["violations"],
        },
        "overall_pass": overall,
        "feedback_for_generator": feedback,
        "iterations": 1,
        "exhausted": False,
        "needs_human_review": False,
        "ceo_approval_required": bool(compliance.get("ceo_approval_required")),
    }
