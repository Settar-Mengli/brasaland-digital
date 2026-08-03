"""LangGraph support agent: retrieve then generate with conditional edges.

Graph nodes call ``pipelines.rag.retrieve`` and ``generate_answer`` separately —
never monolithic ``query()``. Traces are stored in-process under ``TRACES``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from pipelines.rag import generate_answer, retrieve

REFUSAL_ANSWER = (
    "I don't have information about that in the official Brasaland manuals."
)
EMPTY_QUESTION_ERROR = "question must not be empty"

TRACES: dict[str, dict[str, Any]] = {}


class AgentState(TypedDict):
    question: str
    context: list[dict[str, Any]]
    answer: str | None
    error: str | None
    run_id: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_trace(run_id: str, node: str, **payload: Any) -> None:
    entry = TRACES.setdefault(
        run_id,
        {"run_id": run_id, "nodes": [], "final": None},
    )
    entry["nodes"].append({"node": node, "timestamp": _utc_now(), **payload})


def validate_question(state: AgentState) -> dict[str, Any]:
    cleaned = (state.get("question") or "").strip()
    run_id = state["run_id"]
    if not cleaned:
        _append_trace(
            run_id,
            "validate_question",
            question=cleaned,
            error=EMPTY_QUESTION_ERROR,
        )
        return {
            "question": cleaned,
            "error": EMPTY_QUESTION_ERROR,
            "answer": None,
            "context": [],
        }
    _append_trace(run_id, "validate_question", question=cleaned, error=None)
    return {"question": cleaned, "error": None}


def retrieve_context(state: AgentState) -> dict[str, Any]:
    run_id = state["run_id"]
    chunks = retrieve(state["question"])
    _append_trace(
        run_id,
        "retrieve_context",
        question=state["question"],
        context=chunks,
        hit_count=len(chunks),
    )
    return {"context": chunks}


def refuse_no_context(state: AgentState) -> dict[str, Any]:
    run_id = state["run_id"]
    _append_trace(
        run_id,
        "refuse_no_context",
        answer=REFUSAL_ANSWER,
        context=state.get("context") or [],
    )
    return {"answer": REFUSAL_ANSWER}


def generate_answer_node(state: AgentState) -> dict[str, Any]:
    run_id = state["run_id"]
    context = state.get("context") or []
    prompt_chunks = [{k: v for k, v in c.items() if k != "_score"} for c in context]
    answer = generate_answer(state["question"], prompt_chunks)
    _append_trace(
        run_id,
        "generate_answer_node",
        question=state["question"],
        context=context,
        answer=answer,
    )
    return {"answer": answer}


def _route_after_validate(state: AgentState) -> Literal["retrieve_context", "__end__"]:
    if state.get("error"):
        return "__end__"
    return "retrieve_context"


def _route_after_retrieve(
    state: AgentState,
) -> Literal["refuse_no_context", "generate_answer_node"]:
    if not state.get("context"):
        return "refuse_no_context"
    return "generate_answer_node"


def _build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("validate_question", validate_question)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("refuse_no_context", refuse_no_context)
    builder.add_node("generate_answer_node", generate_answer_node)

    builder.add_edge(START, "validate_question")
    builder.add_conditional_edges(
        "validate_question",
        _route_after_validate,
        {
            "retrieve_context": "retrieve_context",
            "__end__": END,
        },
    )
    builder.add_conditional_edges(
        "retrieve_context",
        _route_after_retrieve,
        {
            "refuse_no_context": "refuse_no_context",
            "generate_answer_node": "generate_answer_node",
        },
    )
    builder.add_edge("refuse_no_context", END)
    builder.add_edge("generate_answer_node", END)

    return builder.compile(checkpointer=MemorySaver())


COMPILED_GRAPH = _build_graph()


def get_trace(run_id: str) -> dict[str, Any] | None:
    """Return the structured trace for a completed (or in-progress) run."""
    trace = TRACES.get(run_id)
    if trace is None:
        return None
    return dict(trace)


def invoke_support_agent(question: str, *, run_id: str | None = None) -> dict[str, Any]:
    """Run the compiled graph. Always passes thread_id for MemorySaver.

    Returns ``{"run_id", "answer"}`` on success paths (including refusal).
    On empty question or node failure returns ``{"run_id", "error"}`` (no stack).
    """
    rid = run_id or str(uuid.uuid4())
    TRACES[rid] = {"run_id": rid, "nodes": [], "final": None}
    config = {"configurable": {"thread_id": rid}}
    initial: AgentState = {
        "question": question or "",
        "context": [],
        "answer": None,
        "error": None,
        "run_id": rid,
    }
    try:
        final = COMPILED_GRAPH.invoke(initial, config=config)
    except Exception as exc:  # noqa: BLE001 — map any node failure to clear error
        message = str(exc).strip() or "agent node failed"
        _append_trace(rid, "error", error=message)
        TRACES[rid]["final"] = {"error": message}
        return {"run_id": rid, "error": message}

    error = final.get("error")
    answer = final.get("answer")
    TRACES[rid]["final"] = {
        "question": final.get("question"),
        "context": final.get("context") or [],
        "answer": answer,
        "error": error,
    }
    if error:
        return {"run_id": rid, "error": error}
    return {"run_id": rid, "answer": answer or ""}
