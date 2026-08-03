"""LangGraph support agent: heuristic route → RAG and/or ticket tool.

Graph nodes call ``pipelines.rag.retrieve`` / ``generate_answer`` and
``pipelines.tools.ticket_lookup`` separately — never monolithic ``query()``.
Routing is a deterministic heuristic on the question alone (LLM router later).
``compose_answer`` owns all tool and both-route finalization.
Traces are stored in-process under ``TRACES``.

Guardrails: ``input_guardrails`` (pre-route) and ``output_guardrails`` (pre-END).
``session_id`` travels only via ``config["configurable"]`` (never AgentState).
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from pipelines.guardrails import (
    OUTPUT_SAFE_REFUSAL,
    apply_input_guard,
    get_guardrail_summary,
    record_guardrail,
    validate_output,
    validate_tool_result,
)

logger = logging.getLogger("pipelines.support_agent")

from pipelines.rag import generate_answer, retrieve
from pipelines.tools.ticket_lookup import (
    TicketLookupInput,
    TicketLookupResult,
    format_ticket_answer,
    lookup_ticket,
)

REFUSAL_ANSWER = (
    "I don't have information about that in the official Brasaland manuals."
)
EMPTY_QUESTION_ERROR = "question must not be empty"
TICKET_FALLBACK_ANSWER = (
    "I couldn't confirm that ticket's status right now."
)
TICKET_UNCONFIRMED_NOTE = (
    "I couldn't confirm that ticket's status right now."
)

# Heuristic signals — keyword/regex router; LLM router is a later swap.
_TICKET_SIGNAL = re.compile(
    r"\b(?:ticket|incident)\b|\b#\d+\b",
    re.IGNORECASE,
)
_TICKET_REF = re.compile(
    r"(?:ticket|incident)\s*#?\s*([A-Za-z0-9-]+)|#(\d+)",
    re.IGNORECASE,
)
# "manual" uses hyphen-aware boundaries so MANUAL-98 is not a RAG hit.
_RAG_SIGNAL = re.compile(
    r"\b(?:loyalty|points|gold|silver|bronze|policy|handbook|"
    r"allergen|waste|supplier|ordering|discount|tier|program)\b|"
    r"(?<![A-Za-z0-9-])manual(?![A-Za-z0-9-])",
    re.IGNORECASE,
)

TRACES: dict[str, dict[str, Any]] = {}

RouteKind = Literal["rag", "tool", "both"]


class AgentState(TypedDict):
    question: str
    context: list[dict[str, Any]]
    answer: str | None
    error: str | None
    run_id: str
    route: RouteKind | None
    tool_result: dict[str, Any] | None
    sources_ran: list[str]
    user_id: str | None
    guardrail_blocked: bool


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_trace(run_id: str, node: str, **payload: Any) -> None:
    entry = TRACES.setdefault(
        run_id,
        {"run_id": run_id, "nodes": [], "final": None},
    )
    entry["nodes"].append({"node": node, "timestamp": _utc_now(), **payload})


def _session_id_from_config(config: RunnableConfig) -> str | None:
    configurable = config.get("configurable") or {}
    raw = configurable.get("session_id")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _decide_route(question: str) -> tuple[RouteKind, dict[str, bool]]:
    has_ticket = bool(_TICKET_SIGNAL.search(question))
    has_rag = bool(_RAG_SIGNAL.search(question))
    signals = {"ticket": has_ticket, "rag": has_rag}
    if has_ticket and has_rag:
        return "both", signals
    if has_ticket:
        return "tool", signals
    return "rag", signals


def _parse_ticket_input(question: str) -> TicketLookupInput:
    match = _TICKET_REF.search(question)
    if match:
        ref_str = match.group(1) or match.group(2)
        if ref_str.isdigit():
            return TicketLookupInput(ticket_ref=int(ref_str))
        return TicketLookupInput(ticket_ref=ref_str)
    # Ticket wording without a ref — cannot invent an id.
    return TicketLookupInput(ticket_ref=None)


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
            "route": None,
            "tool_result": None,
            "sources_ran": [],
            "guardrail_blocked": False,
        }
    _append_trace(run_id, "validate_question", question=cleaned, error=None)
    return {"question": cleaned, "error": None, "guardrail_blocked": False}


def input_guardrails(
    state: AgentState, config: RunnableConfig
) -> dict[str, Any]:
    run_id = state["run_id"]
    session_id = _session_id_from_config(config)
    decision = apply_input_guard(state["question"], session_id)
    if decision["blocked"]:
        answer = decision["answer"] or ""
        _append_trace(
            run_id,
            "input_guardrails",
            guardrail=True,
            failure_type=decision["failure_type"],
            action=decision["action"],
            reason=decision["reason"],
            answer=answer,
        )
        return {
            "answer": answer,
            "guardrail_blocked": True,
            "sources_ran": [],
        }
    _append_trace(
        run_id,
        "input_guardrails",
        guardrail=True,
        failure_type=None,
        action="pass",
    )
    return {"guardrail_blocked": False}


def route_sources(state: AgentState) -> dict[str, Any]:
    run_id = state["run_id"]
    route, signals = _decide_route(state["question"])
    _append_trace(
        run_id,
        "route_sources",
        question=state["question"],
        route=route,
        signals=signals,
    )
    return {"route": route}


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
    sources_ran = ["retrieve_context"]
    _append_trace(
        run_id,
        "refuse_no_context",
        answer=REFUSAL_ANSWER,
        context=state.get("context") or [],
        sources_ran=sources_ran,
    )
    return {"answer": REFUSAL_ANSWER, "sources_ran": sources_ran}


def generate_answer_node(state: AgentState) -> dict[str, Any]:
    run_id = state["run_id"]
    context = state.get("context") or []
    prompt_chunks = [{k: v for k, v in c.items() if k != "_score"} for c in context]
    answer = generate_answer(state["question"], prompt_chunks)
    sources_ran = ["retrieve_context"]
    _append_trace(
        run_id,
        "generate_answer_node",
        question=state["question"],
        context=context,
        answer=answer,
        sources_ran=sources_ran,
    )
    return {"answer": answer, "sources_ran": sources_ran}


def lookup_ticket_node(
    state: AgentState, config: RunnableConfig
) -> dict[str, Any]:
    run_id = state["run_id"]
    session_id = _session_id_from_config(config)
    inp = _parse_ticket_input(state["question"])
    # Bearer lives only in configurable — never AgentState / traces.
    access_token = (config.get("configurable") or {}).get("access_token")
    if inp.get("ticket_ref") is None and not any(
        inp.get(k) for k in ("status", "origin", "branch", "category")
    ):
        result: TicketLookupResult = {
            "ok": False,
            "incidents": [],
            "matched_by": None,
            "error": "no ticket reference found in question",
        }
    else:
        result = lookup_ticket(inp, access_token=access_token)

    payload: dict[str, Any] = dict(result)
    structural = validate_tool_result(payload)
    if structural["blocked"]:
        record_guardrail(
            session_id,
            "structural",
            reason=structural["reason"],
        )
        _append_trace(
            run_id,
            "lookup_ticket",
            ok=False,
            matched_by=None,
            error=structural["reason"],
            incident_ids=[],
            incident_count=0,
            user_id=state.get("user_id"),
            guardrail=True,
            failure_type="structural",
        )
        return {
            "tool_result": {
                "ok": False,
                "incidents": [],
                "matched_by": None,
                "error": structural["reason"],
            }
        }

    _append_trace(
        run_id,
        "lookup_ticket",
        ok=result["ok"],
        matched_by=result.get("matched_by"),
        error=result.get("error"),
        incident_ids=[row["id"] for row in result.get("incidents") or []],
        incident_count=len(result.get("incidents") or []),
        user_id=state.get("user_id"),
    )
    return {"tool_result": payload}


def compose_answer(state: AgentState) -> dict[str, Any]:
    """Finalize tool-only and both routes. Never invents ticket status."""
    run_id = state["run_id"]
    route = state.get("route") or "tool"
    tool_result = state.get("tool_result") or {}
    tool_ok = bool(tool_result.get("ok"))
    incidents = list(tool_result.get("incidents") or [])
    context = state.get("context") or []
    sources_ran: list[str] = []

    tool_text = format_ticket_answer(incidents) if tool_ok and incidents else ""

    if route == "tool":
        if tool_ok and tool_text:
            answer = tool_text
            sources_ran = ["ticket_lookup"]
        else:
            answer = TICKET_FALLBACK_ANSWER
            sources_ran = []
    else:
        # both — compose_answer owns all finalization (no generate_answer_node)
        if tool_ok and tool_text and context:
            prompt_chunks = [
                {k: v for k, v in c.items() if k != "_score"} for c in context
            ]
            rag_text = generate_answer(state["question"], prompt_chunks)
            answer = f"{tool_text}\n\n{rag_text}"
            sources_ran = ["ticket_lookup", "retrieve_context"]
        elif tool_ok and tool_text:
            answer = tool_text
            sources_ran = ["ticket_lookup"]
        elif context:
            prompt_chunks = [
                {k: v for k, v in c.items() if k != "_score"} for c in context
            ]
            rag_text = generate_answer(state["question"], prompt_chunks)
            answer = f"{TICKET_UNCONFIRMED_NOTE}\n\n{rag_text}"
            sources_ran = ["retrieve_context"]
        else:
            answer = TICKET_FALLBACK_ANSWER
            sources_ran = []

    matched_by = tool_result.get("matched_by") if tool_ok else None
    _append_trace(
        run_id,
        "compose_answer",
        route=route,
        answer=answer,
        sources_ran=sources_ran,
        matched_by=matched_by,
        tool_ok=tool_ok,
    )
    return {"answer": answer, "sources_ran": sources_ran}


def output_guardrails(
    state: AgentState, config: RunnableConfig
) -> dict[str, Any]:
    run_id = state["run_id"]
    session_id = _session_id_from_config(config)
    # Input already set a safe answer — pass through without re-counting.
    if state.get("guardrail_blocked"):
        _append_trace(
            run_id,
            "output_guardrails",
            guardrail=True,
            failure_type=None,
            action="pass_input_block",
            answer=state.get("answer"),
        )
        return {}

    decision = validate_output(state.get("answer"))
    if decision["blocked"] and decision["failure_type"] is not None:
        record_guardrail(
            session_id,
            decision["failure_type"],
            reason=decision["reason"],
        )
        safe = decision["answer"] or ""
        _append_trace(
            run_id,
            "output_guardrails",
            guardrail=True,
            failure_type=decision["failure_type"],
            action=decision["action"],
            reason=decision["reason"],
            answer=safe,
        )
        return {"answer": safe}
    _append_trace(
        run_id,
        "output_guardrails",
        guardrail=True,
        failure_type=None,
        action="pass",
    )
    return {}


def _route_after_validate(
    state: AgentState,
) -> Literal["input_guardrails", "__end__"]:
    if state.get("error"):
        return "__end__"
    return "input_guardrails"


def _route_after_input(
    state: AgentState,
) -> Literal["route_sources", "output_guardrails"]:
    if state.get("guardrail_blocked"):
        return "output_guardrails"
    return "route_sources"


def _route_after_sources(
    state: AgentState,
) -> Literal["retrieve_context", "lookup_ticket"]:
    if state.get("route") in ("tool", "both"):
        return "lookup_ticket"
    return "retrieve_context"


def _route_after_lookup(
    state: AgentState,
) -> Literal["compose_answer", "retrieve_context"]:
    if state.get("route") == "both":
        return "retrieve_context"
    return "compose_answer"


def _route_after_retrieve(
    state: AgentState,
) -> Literal["refuse_no_context", "generate_answer_node", "compose_answer"]:
    if state.get("route") == "both":
        return "compose_answer"
    if not state.get("context"):
        return "refuse_no_context"
    return "generate_answer_node"


def _build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("validate_question", validate_question)
    builder.add_node("input_guardrails", input_guardrails)
    builder.add_node("route_sources", route_sources)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("refuse_no_context", refuse_no_context)
    builder.add_node("generate_answer_node", generate_answer_node)
    builder.add_node("lookup_ticket", lookup_ticket_node)
    builder.add_node("compose_answer", compose_answer)
    builder.add_node("output_guardrails", output_guardrails)

    builder.add_edge(START, "validate_question")
    builder.add_conditional_edges(
        "validate_question",
        _route_after_validate,
        {
            "input_guardrails": "input_guardrails",
            "__end__": END,
        },
    )
    builder.add_conditional_edges(
        "input_guardrails",
        _route_after_input,
        {
            "route_sources": "route_sources",
            "output_guardrails": "output_guardrails",
        },
    )
    builder.add_conditional_edges(
        "route_sources",
        _route_after_sources,
        {
            "retrieve_context": "retrieve_context",
            "lookup_ticket": "lookup_ticket",
        },
    )
    builder.add_conditional_edges(
        "lookup_ticket",
        _route_after_lookup,
        {
            "compose_answer": "compose_answer",
            "retrieve_context": "retrieve_context",
        },
    )
    builder.add_conditional_edges(
        "retrieve_context",
        _route_after_retrieve,
        {
            "refuse_no_context": "refuse_no_context",
            "generate_answer_node": "generate_answer_node",
            "compose_answer": "compose_answer",
        },
    )
    builder.add_edge("refuse_no_context", "output_guardrails")
    builder.add_edge("generate_answer_node", "output_guardrails")
    builder.add_edge("compose_answer", "output_guardrails")
    builder.add_edge("output_guardrails", END)

    return builder.compile(checkpointer=MemorySaver())


COMPILED_GRAPH = _build_graph()


def get_trace(run_id: str) -> dict[str, Any] | None:
    """Return the structured trace for a completed (or in-progress) run."""
    trace = TRACES.get(run_id)
    if trace is None:
        return None
    return dict(trace)


def get_checkpoint_state(run_id: str) -> dict[str, Any] | None:
    """Return the latest checkpointed AgentState values for ``run_id`` (no secrets)."""
    config = {"configurable": {"thread_id": run_id}}
    snapshot = COMPILED_GRAPH.get_state(config)
    if snapshot is None or not snapshot.values:
        return None
    return dict(snapshot.values)


def invoke_support_agent(
    question: str,
    *,
    run_id: str | None = None,
    access_token: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Run the compiled graph. Always passes thread_id for MemorySaver.

    ``access_token`` and ``session_id`` are passed only via
    ``config["configurable"]`` — never as AgentState fields (not checkpointed).
    Guardrail ledger key is the explicit ``session_id`` when provided, otherwise
    an ephemeral per-call UUID (never ``user_id``).

    Returns ``{"run_id", "answer"}`` on success paths (including refusal and
    sanitized generation failures). On empty question returns ``{"run_id", "error"}``.
    """
    rid = run_id or str(uuid.uuid4())
    TRACES[rid] = {"run_id": rid, "nodes": [], "final": None}
    sid = (session_id or str(uuid.uuid4())).strip()
    configurable: dict[str, Any] = {"thread_id": rid, "session_id": sid}
    if access_token is not None:
        configurable["access_token"] = access_token
    config = {"configurable": configurable}
    initial: AgentState = {
        "question": question or "",
        "context": [],
        "answer": None,
        "error": None,
        "run_id": rid,
        "route": None,
        "tool_result": None,
        "sources_ran": [],
        "user_id": user_id,
        "guardrail_blocked": False,
    }
    try:
        final = COMPILED_GRAPH.invoke(initial, config=config)
    except Exception as exc:  # noqa: BLE001 — never leak provider text to clients
        logger.exception("support agent node failed")
        record_guardrail(sid, "security", reason="generation_blocked")
        safe = OUTPUT_SAFE_REFUSAL
        _append_trace(
            rid,
            "error",
            error="generation_blocked",
            failure_type="security",
            guardrail=True,
        )
        TRACES[rid]["final"] = {
            "answer": safe,
            "error": None,
            "guardrail_blocked": True,
            "sources_ran": [],
        }
        return {"run_id": rid, "answer": safe}

    error = final.get("error")
    answer = final.get("answer")
    tool_result = final.get("tool_result") or {}
    sources_ran = list(final.get("sources_ran") or [])
    route = final.get("route")
    final_payload: dict[str, Any] = {
        "question": final.get("question"),
        "context": final.get("context") or [],
        "answer": answer,
        "error": error,
        "route": route,
        "sources_ran": sources_ran,
        "user_id": final.get("user_id"),
        "guardrail_blocked": bool(final.get("guardrail_blocked")),
    }
    if tool_result.get("ok"):
        final_payload["matched_by"] = tool_result.get("matched_by")
    TRACES[rid]["final"] = final_payload
    if error:
        return {"run_id": rid, "error": error}
    return {"run_id": rid, "answer": answer or ""}


# Re-export for HTTP summary endpoint.
__all__ = [
    "COMPILED_GRAPH",
    "TRACES",
    "get_checkpoint_state",
    "get_guardrail_summary",
    "get_trace",
    "invoke_support_agent",
]
