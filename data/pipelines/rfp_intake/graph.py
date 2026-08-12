"""RFP intake LangGraph — pure nodes; persistence lives outside this module."""

from __future__ import annotations

import logging
import operator
import re
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from pipelines.rfp_intake.generation import clean_markdown_artifacts, generate_json

logger = logging.getLogger(__name__)

ALL_DEPARTMENTS = ("marketing", "operaciones", "procurement", "training")

DEPARTMENT_OWNERS: dict[str, str] = {
    "marketing": "Camila Ospina",
    "operaciones": "Felipe Guerrero",
    "procurement": "Lucía Fernández",
    "training": "Jake Morrison",
}

_MIN_MARKDOWN_CHARS = 20

_SCOPE_RE = re.compile(
    r"\b("
    r"scope\s+of\s+work|seeking\s+a|looking\s+for\s+a|catering\s+partner|"
    r"food[\s-]?and[\s-]?beverage|concession|operate\s+(?:one|a)|"
    r"provide\s+lunch|weekly\s+catering|proposal\s+with"
    r")\b",
    re.IGNORECASE,
)
_BUDGET_RE = re.compile(
    r"\b("
    r"budget|usd|cop|pricing|price|contract\s+value|per\s+year|quotes?\s+in"
    r")\b",
    re.IGNORECASE,
)
_DEADLINE_RE = re.compile(
    r"\b("
    r"deadline|timeline|submission|target\s+\w+\s+opening|"
    r"\d+\s+months?|april|june|renewable"
    r")\b",
    re.IGNORECASE,
)
_SERVICE_RE = re.compile(
    r"\b("
    r"catering|restaurant|concession|menu|food[\s-]?and[\s-]?beverage|"
    r"lunch\s+for|co-branded"
    r")\b",
    re.IGNORECASE,
)


class IntakeState(TypedDict, total=False):
    """Graph state. ``department_sections`` uses operator.add for parallel fan-in."""

    ticket_id: str
    rfp_id: str
    raw_pdf_path: str
    markdown: str | None
    is_valid_rfp: bool | None
    discard_reason: str | None
    metadata: dict | None
    departments_needed: list[str] | None
    department_sections: Annotated[list[dict], operator.add]
    summary: str | None
    error: str | None


def prefilter_validity(markdown: str) -> Literal["valid", "invalid", "ambiguous"]:
    """Deterministic triage before any LLM call."""
    text = markdown or ""
    has_scope = bool(_SCOPE_RE.search(text))
    has_budget = bool(_BUDGET_RE.search(text))
    has_deadline = bool(_DEADLINE_RE.search(text))
    has_service = bool(_SERVICE_RE.search(text))

    if has_scope and (has_budget or has_deadline or has_service):
        return "valid"
    if not has_scope and not has_budget and not has_deadline:
        return "invalid"
    return "ambiguous"


def convert_node(state: IntakeState) -> dict[str, Any]:
    """PDF → markdown via MarkItDown; clean (cid:N) artifacts."""
    raw_pdf_path = state.get("raw_pdf_path") or ""
    path = Path(raw_pdf_path)
    try:
        if not path.is_file():
            return {
                "is_valid_rfp": False,
                "discard_reason": f"source file not found: {raw_pdf_path}",
            }
        from markitdown import MarkItDown

        result = MarkItDown().convert(str(path))
        text = clean_markdown_artifacts((result.text_content or "").strip())
    except Exception as exc:  # noqa: BLE001 — never crash the graph
        logger.warning("convert failed: %s", type(exc).__name__)
        return {
            "is_valid_rfp": False,
            "discard_reason": f"PDF conversion failed: {type(exc).__name__}",
        }

    if len(text) < _MIN_MARKDOWN_CHARS:
        return {
            "is_valid_rfp": False,
            "discard_reason": "unreadable or empty PDF",
        }
    return {"markdown": text}


def classify_node(state: IntakeState) -> dict[str, Any]:
    """Prefilter + optional LLM for ambiguous cases."""
    markdown = state.get("markdown") or ""
    verdict = prefilter_validity(markdown)
    if verdict == "valid":
        return {"is_valid_rfp": True, "discard_reason": None}
    if verdict == "invalid":
        return {
            "is_valid_rfp": False,
            "discard_reason": "not an actionable RFP (missing scope/budget/deadline)",
        }

    try:
        parsed = generate_json(
            system_prompt=(
                "You classify whether a document is a real commercial RFP or RFQ "
                "for food service, catering, or restaurant concession work. "
                "Respond with JSON only: "
                '{"is_valid_rfp": true|false, "reason": string}.'
            ),
            user_prompt=markdown[:12000],
            max_tokens=256,
        )
        is_valid = bool(parsed.get("is_valid_rfp"))
        reason = parsed.get("reason")
        return {
            "is_valid_rfp": is_valid,
            "discard_reason": None
            if is_valid
            else (str(reason) if reason else "classifier rejected"),
        }
    except Exception as exc:  # noqa: BLE001 — fail closed
        logger.warning("classify LLM failed: %s", type(exc).__name__)
        return {
            "is_valid_rfp": False,
            "discard_reason": f"classifier unavailable: {type(exc).__name__}",
        }


def extract_node(state: IntakeState) -> dict[str, Any]:
    """LLM structured extract + textstat readability into metadata."""
    markdown = state.get("markdown") or ""
    parsed = generate_json(
        system_prompt=(
            "Extract structured fields from this RFP. Never invent missing figures. "
            "Select departments_needed by matching the RFP against these departments: "
            "- marketing: ALWAYS include — it owns every ticket. Also specifically for "
            "brand terms, exclusivity, co-branding, offer validity. "
            "- operaciones: include if the RFP involves event/catering operations, kitchen "
            "or staff capacity, setup times, or per-event cost. "
            "- procurement: include if the RFP implies ingredient sourcing, volume-based "
            "cost, or supplier lead times (e.g. recurring catering, large volume, "
            "multi-site supply). "
            "- training: include ONLY if a NEW recipe, new signature menu, or a new "
            "standard/certification is required. "
            "Include every department that applies — a large co-branded contract with a "
            "new menu typically needs all four. Do not omit a department that clearly "
            "applies. "
            "Respond with JSON only matching: "
            '{"client_name":str|null,"location":str|null,"service_type":str|null,'
            '"scope":str|null,"deadline":str|null,"budget_range":str|null,'
            '"open_questions":[str],'
            '"departments_needed":["marketing"|"operaciones"|"procurement"|"training"]}.'
        ),
        user_prompt=markdown[:20000],
        max_tokens=1024,
    )

    import textstat

    allowed = set(ALL_DEPARTMENTS)
    raw_depts = parsed.get("departments_needed") or []
    if not isinstance(raw_depts, list):
        raw_depts = []
    departments_needed = [str(d) for d in raw_depts if str(d) in allowed]
    if "marketing" not in departments_needed:
        departments_needed = ["marketing", *departments_needed]

    open_questions = parsed.get("open_questions") or []
    if not isinstance(open_questions, list):
        open_questions = []
    open_questions = [str(q) for q in open_questions]

    metadata: dict[str, Any] = {
        "client_name": parsed.get("client_name"),
        "location": parsed.get("location"),
        "service_type": parsed.get("service_type"),
        "scope": parsed.get("scope"),
        "deadline": parsed.get("deadline"),
        "budget_range": parsed.get("budget_range"),
        "open_questions": open_questions,
        "departments_needed": departments_needed,
        "readability_metrics": {
            "flesch_reading_ease": float(
                textstat.flesch_reading_ease(markdown or " ")
            ),
            "flesch_kincaid_grade": float(
                textstat.flesch_kincaid_grade(markdown or " ")
            ),
        },
    }
    return {"metadata": metadata, "departments_needed": departments_needed}


def orchestrator_node(state: IntakeState) -> dict[str, Any]:
    """Ensure at least marketing; record open question if defaulting."""
    needed = list(state.get("departments_needed") or [])
    if needed:
        return {}
    metadata = dict(state.get("metadata") or {})
    questions = list(metadata.get("open_questions") or [])
    questions.append(
        "Extractor returned no departments; defaulted to marketing (routing unclear)."
    )
    metadata["open_questions"] = questions
    metadata["departments_needed"] = ["marketing"]
    return {
        "departments_needed": ["marketing"],
        "metadata": metadata,
    }


def _department_worker(department: str, state: IntakeState) -> dict[str, Any]:
    needed = state.get("departments_needed") or []
    if department not in needed:
        return {"department_sections": []}

    metadata = state.get("metadata") or {}
    relevant = {
        "client_name": metadata.get("client_name"),
        "location": metadata.get("location"),
        "service_type": metadata.get("service_type"),
        "scope": metadata.get("scope"),
        "deadline": metadata.get("deadline"),
        "budget_range": metadata.get("budget_range"),
        "open_questions": metadata.get("open_questions"),
    }
    try:
        parsed = generate_json(
            system_prompt=(
                f"You extract key aspects for the {department} department reviewing "
                "this Brasaland RFP. Never invent absent figures. Respond with JSON only: "
                '{"key_aspects": [str]}.'
            ),
            user_prompt=f"Metadata extracts:\n{relevant}",
            max_tokens=800,
        )
        aspects = parsed.get("key_aspects") or []
        if not isinstance(aspects, list):
            aspects = []
        return {
            "department_sections": [
                {
                    "department_id": department,
                    "key_aspects": [str(a) for a in aspects],
                }
            ]
        }
    except Exception as exc:  # noqa: BLE001 — soft-fail section
        logger.warning("department worker %s failed: %s", department, type(exc).__name__)
        return {
            "department_sections": [
                {
                    "department_id": department,
                    "key_aspects": [f"{department} worker failed: {type(exc).__name__}"],
                }
            ]
        }


def marketing_worker(state: IntakeState) -> dict[str, Any]:
    return _department_worker("marketing", state)


def operaciones_worker(state: IntakeState) -> dict[str, Any]:
    return _department_worker("operaciones", state)


def procurement_worker(state: IntakeState) -> dict[str, Any]:
    return _department_worker("procurement", state)


def training_worker(state: IntakeState) -> dict[str, Any]:
    return _department_worker("training", state)


def synthesize_node(state: IntakeState) -> dict[str, Any]:
    """Sales-facing summary: what each dept needs and who to ask."""
    metadata = state.get("metadata") or {}
    sections = state.get("department_sections") or []
    by_dept = {
        str(s.get("department_id")): s for s in sections if s.get("department_id")
    }

    lines: list[str] = [
        "RFP intake summary",
        f"Client: {metadata.get('client_name') or 'unknown'}",
        f"Service: {metadata.get('service_type') or 'unknown'}",
        f"Location: {metadata.get('location') or 'unknown'}",
        f"Deadline: {metadata.get('deadline') or 'unknown'}",
        f"Budget: {metadata.get('budget_range') or 'not stated'}",
        "",
        "Department follow-ups:",
    ]
    for dept in ALL_DEPARTMENTS:
        section = by_dept.get(dept)
        if not section:
            continue
        owner = DEPARTMENT_OWNERS.get(dept, dept)
        aspects = section.get("key_aspects") or []
        aspect_text = "; ".join(str(a) for a in aspects) if aspects else "(none)"
        lines.append(f"- {dept} ({owner}): {aspect_text}")

    open_qs = metadata.get("open_questions") or []
    lines.append("")
    lines.append("Open questions:")
    if open_qs:
        for q in open_qs:
            lines.append(f"- {q}")
    else:
        lines.append("- (none)")

    return {"summary": "\n".join(lines)}


def _route_after_convert(state: IntakeState) -> Literal["classify", "__end__"]:
    if state.get("is_valid_rfp") is False:
        return "__end__"
    return "classify"


def _route_after_classify(state: IntakeState) -> Literal["extract", "__end__"]:
    if state.get("is_valid_rfp") is False:
        return "__end__"
    return "extract"


def build_intake_graph() -> Any:
    """Compile intake graph without a checkpointer."""
    builder: StateGraph = StateGraph(IntakeState)
    builder.add_node("convert", convert_node)
    builder.add_node("classify", classify_node)
    builder.add_node("extract", extract_node)
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("marketing_worker", marketing_worker)
    builder.add_node("operaciones_worker", operaciones_worker)
    builder.add_node("procurement_worker", procurement_worker)
    builder.add_node("training_worker", training_worker)
    builder.add_node("synthesize", synthesize_node)

    builder.add_edge(START, "convert")
    builder.add_conditional_edges(
        "convert",
        _route_after_convert,
        {"classify": "classify", "__end__": END},
    )
    builder.add_conditional_edges(
        "classify",
        _route_after_classify,
        {"extract": "extract", "__end__": END},
    )
    builder.add_edge("extract", "orchestrator")
    for worker in (
        "marketing_worker",
        "operaciones_worker",
        "procurement_worker",
        "training_worker",
    ):
        builder.add_edge("orchestrator", worker)
        builder.add_edge(worker, "synthesize")
    builder.add_edge("synthesize", END)
    return builder.compile()


COMPILED_INTAKE_GRAPH = build_intake_graph()


def run_intake(*, ticket_id: str, rfp_id: str, raw_pdf_path: str) -> dict[str, Any]:
    """Invoke the compiled graph. No DB I/O."""
    result = COMPILED_INTAKE_GRAPH.invoke(
        {
            "ticket_id": ticket_id,
            "rfp_id": rfp_id,
            "raw_pdf_path": raw_pdf_path,
        },
    )
    return dict(result)
