"""RFP response LangGraph — generate/evaluate loop; persistence outside this module."""

from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from pipelines.rfp_intake.generation import generate_json
from pipelines.rfp_intake.graph import ALL_DEPARTMENTS, DEPARTMENT_OWNERS
from pipelines.rfp_intake.response_evaluators import (
    ITERATION_LIMIT,
    compliance_requirements_prompt,
    evaluate_all,
)
logger = logging.getLogger(__name__)


class ResponseState(TypedDict, total=False):
    """Response-graph state. ``department_sections`` uses operator.add for fan-in."""

    ticket_id: str
    rfp_id: str
    metadata: dict | None
    departments_needed: list[str] | None
    input_sections: list[dict] | None
    department_sections: Annotated[list[dict], operator.add]
    error: str | None


def bootstrap_node(state: ResponseState) -> dict[str, Any]:
    """Passthrough — fan-out starts from here (mirrors intake orchestrator role)."""
    return {}


def join_node(state: ResponseState) -> dict[str, Any]:
    """Passthrough join after parallel department workers."""
    return {}


def _metadata_subset(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "client_name": metadata.get("client_name"),
        "location": metadata.get("location"),
        "service_type": metadata.get("service_type"),
        "scope": metadata.get("scope"),
        "deadline": metadata.get("deadline"),
        "budget_range": metadata.get("budget_range"),
        "open_questions": metadata.get("open_questions"),
    }


def _key_aspects_for(department: str, input_sections: list[dict] | None) -> list[str]:
    for section in input_sections or []:
        if str(section.get("department_id")) == department:
            aspects = section.get("key_aspects") or []
            if isinstance(aspects, list):
                return [str(a) for a in aspects]
            return []
    return []


def make_worker(department: str) -> Callable[[ResponseState], dict[str, Any]]:
    """Build a department worker with an in-node generate↔evaluate Python loop."""

    def _worker(state: ResponseState) -> dict[str, Any]:
        needed = state.get("departments_needed") or []
        if department not in needed:
            return {"department_sections": []}

        metadata = dict(state.get("metadata") or {})
        key_aspects = _key_aspects_for(department, state.get("input_sections"))
        budget_range = metadata.get("budget_range")
        if budget_range is not None:
            budget_range = str(budget_range)

        owner = DEPARTMENT_OWNERS.get(department, department)
        relevant = _metadata_subset(metadata)
        feedback = ""
        draft = ""
        evaluation: dict[str, Any] = evaluate_all(
            "", key_aspects, budget_range, department
        )

        for i in range(1, ITERATION_LIMIT + 1):
            system_prompt = (
                f"You draft the {department} department proposal section for Brasaland "
                f"(owner: {owner}). Never invent absent figures. Respond with JSON only: "
                '{"draft_content": str}.\n\n'
                "Compliance requirements (your section will be automatically checked "
                f"against these):\n{compliance_requirements_prompt()}"
            )
            user_parts = [
                f"Metadata extracts:\n{relevant}",
                f"Key aspects to cover:\n{key_aspects}",
            ]
            if feedback:
                user_parts.append(f"Prior evaluator feedback to address:\n{feedback}")
            user_prompt = "\n\n".join(user_parts)

            try:
                parsed = generate_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=2048,
                )
                draft = str(parsed.get("draft_content") or "").strip()
            except Exception as exc:  # noqa: BLE001 — soft-fail iteration
                logger.warning(
                    "response worker %s generate failed: %s",
                    department,
                    type(exc).__name__,
                )
                draft = (
                    f"{department} draft unavailable after generation error "
                    f"({type(exc).__name__})."
                )

            evaluation = evaluate_all(
                draft, key_aspects, budget_range, department
            )
            evaluation["iterations"] = i
            if evaluation["overall_pass"]:
                break
            feedback = str(evaluation.get("feedback_for_generator") or "")
        else:
            evaluation["exhausted"] = True
            evaluation["needs_human_review"] = True

        return {
            "department_sections": [
                {
                    "department_id": department,
                    "draft_content": draft,
                    "evaluation_results": evaluation,
                }
            ]
        }

    _worker.__name__ = f"{department}_worker"
    _worker.__qualname__ = f"{department}_worker"
    return _worker


marketing_worker = make_worker("marketing")
operaciones_worker = make_worker("operaciones")
procurement_worker = make_worker("procurement")
training_worker = make_worker("training")

_WORKER_BY_DEPT: dict[str, Callable[[ResponseState], dict[str, Any]]] = {
    "marketing": marketing_worker,
    "operaciones": operaciones_worker,
    "procurement": procurement_worker,
    "training": training_worker,
}


def build_response_graph() -> Any:
    """Compile response graph without a checkpointer."""
    builder: StateGraph = StateGraph(ResponseState)
    builder.add_node("bootstrap", bootstrap_node)
    for department in ALL_DEPARTMENTS:
        name = f"{department}_worker"
        builder.add_node(name, _WORKER_BY_DEPT[department])
    builder.add_node("join", join_node)

    builder.add_edge(START, "bootstrap")
    for department in ALL_DEPARTMENTS:
        name = f"{department}_worker"
        builder.add_edge("bootstrap", name)
        builder.add_edge(name, "join")
    builder.add_edge("join", END)
    return builder.compile()


COMPILED_RESPONSE_GRAPH = build_response_graph()


def run_response(
    *,
    ticket_id: str,
    rfp_id: str,
    metadata: dict | None,
    departments_needed: list[str] | None,
    input_sections: list[dict] | None,
) -> dict[str, Any]:
    """Invoke the compiled response graph. No DB I/O."""
    result = COMPILED_RESPONSE_GRAPH.invoke(
        {
            "ticket_id": ticket_id,
            "rfp_id": rfp_id,
            "metadata": metadata,
            "departments_needed": departments_needed,
            "input_sections": input_sections,
        },
    )
    return dict(result)
