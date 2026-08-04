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
    classify_memory_decision,
    clear_pending_memory,
    get_guardrail_summary,
    get_pending_memory,
    record_guardrail,
    set_pending_memory,
    strip_memory_decision_clause,
    validate_output,
    validate_tool_result,
)

logger = logging.getLogger("pipelines.support_agent")

from pipelines.memory_store import (
    log_proposal_event,
    validate_memory_payload,
    write_memory,
)
from pipelines.rag import generate_answer_structured, retrieve
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
MEMORY_SAVED_CONFIRM = "Got it — I'll remember that for next time."
MEMORY_EDITED_CONFIRM = "Got it — I've updated what I'll remember."
MEMORY_REJECTED_ACK = "Okay, I won't store that."

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
# Location ops (hours/close/schedule/delivery) keep the RAG/memory path intentional.
_RAG_SIGNAL = re.compile(
    r"\b(?:loyalty|points|gold|silver|bronze|policy|handbook|"
    r"allergen|waste|supplier|ordering|discount|tier|program|"
    r"hours?|opening|closing|schedule|what\s+time|"
    r"open(?:s|ing)?|clos(?:e|es|ing)|delivery\s+days?|"
    r"hora(?:s)?|abre|abren|cierra|cierran|horario|entrega(?:s)?)\b|"
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
    memory_proposal: dict[str, Any] | None
    memory_decision: str | None
    skip_sources: bool


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
    return {"guardrail_blocked": False, "skip_sources": False}


def resolve_memory(
    state: AgentState, config: RunnableConfig
) -> dict[str, Any]:
    """Resolve a pending memory proposal before routing a new question."""
    run_id = state["run_id"]
    session_id = _session_id_from_config(config)
    pending = get_pending_memory(session_id)
    if not pending:
        _append_trace(run_id, "resolve_memory", action="noop")
        return {
            "memory_decision": None,
            "skip_sources": False,
            "memory_proposal": None,
        }

    question = state.get("question") or ""
    decision, edited = classify_memory_decision(question)
    residual = strip_memory_decision_clause(question)

    def _reject(*, reason: str) -> dict[str, Any]:
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
                "originating_message": question,
                "reason": reason,
            }
        )
        clear_pending_memory(session_id)
        # Topic-change: clear pending, then answer the new question normally.
        if reason == "topic_change":
            _append_trace(
                run_id,
                "resolve_memory",
                action="reject_continue",
                reason=reason,
                decision="reject",
            )
            return {
                "question": question,
                "memory_decision": "reject",
                "skip_sources": False,
                "memory_proposal": None,
            }
        _append_trace(
            run_id,
            "resolve_memory",
            action="reject",
            reason=reason,
            decision="reject",
        )
        return {
            "answer": MEMORY_REJECTED_ACK,
            "memory_decision": "reject",
            "skip_sources": True,
            "sources_ran": [],
            "memory_proposal": None,
        }

    if decision == "reject":
        # Bare reject / silence-like vs topic-change (has residual operational text).
        if residual and residual != question and len(residual.split()) > 2:
            return _reject(reason="topic_change")
        # Full message didn't match approve/edit — treat as topic-change if it
        # looks like a new question, else reject-only.
        if "?" in question or len(question.split()) > 8:
            return _reject(reason="topic_change")
        return _reject(reason="ambiguous")

    summary = (
        edited
        if decision == "edit" and edited
        else (pending.get("summary") or "")
    )
    location = pending.get("location") or "unknown"
    category = pending.get("category") or "known_incidents"
    poison = validate_memory_payload(summary=summary, category=category)
    if poison:
        log_proposal_event(
            {
                "session_id": session_id,
                "outcome": "rejected",
                "proposal": {
                    "summary": summary,
                    "location": location,
                    "category": category,
                    "proposal_id": pending.get("proposal_id"),
                },
                "originating_message": question,
                "reason": poison,
            }
        )
        clear_pending_memory(session_id)
        _append_trace(
            run_id,
            "resolve_memory",
            action="write_rejected",
            reason=poison,
            decision=decision,
        )
        return {
            "answer": MEMORY_REJECTED_ACK,
            "memory_decision": "reject",
            "skip_sources": True,
            "sources_ran": [],
            "memory_proposal": None,
        }

    result = write_memory(
        {
            "location": location,
            "category": category,
            "summary": summary,
            "proposal_id": pending.get("proposal_id"),
        }
    )
    outcome = "edited" if decision == "edit" else "approved"
    if not result["ok"]:
        log_proposal_event(
            {
                "session_id": session_id,
                "outcome": "rejected",
                "proposal": {
                    "summary": summary,
                    "location": location,
                    "category": category,
                    "proposal_id": pending.get("proposal_id"),
                },
                "originating_message": question,
                "reason": result.get("reason"),
            }
        )
        clear_pending_memory(session_id)
        _append_trace(
            run_id,
            "resolve_memory",
            action="write_failed",
            reason=result.get("reason"),
            decision=decision,
        )
        return {
            "answer": MEMORY_REJECTED_ACK,
            "memory_decision": "reject",
            "skip_sources": True,
            "sources_ran": [],
            "memory_proposal": None,
        }

    log_proposal_event(
        {
            "session_id": session_id,
            "outcome": outcome,
            "proposal": {
                "summary": summary,
                "location": location,
                "category": category,
                "proposal_id": pending.get("proposal_id"),
            },
            "originating_message": question,
            "reason": None,
        }
    )
    clear_pending_memory(session_id)
    confirm = MEMORY_EDITED_CONFIRM if outcome == "edited" else MEMORY_SAVED_CONFIRM

    # Residual new question after approve/edit.
    if residual and residual.strip() and residual.strip() != question.strip():
        # Heuristic: residual still looks like a question/request.
        if "?" in residual or len(residual.split()) > 3:
            _append_trace(
                run_id,
                "resolve_memory",
                action="approve_continue",
                decision=decision,
                outcome=outcome,
            )
            return {
                "question": residual.strip(),
                "answer": None,
                "memory_decision": decision,
                "skip_sources": False,
                "memory_proposal": None,
            }

    _append_trace(
        run_id,
        "resolve_memory",
        action="approve",
        decision=decision,
        outcome=outcome,
    )
    return {
        "answer": confirm,
        "memory_decision": decision,
        "skip_sources": True,
        "sources_ran": [],
        "memory_proposal": None,
    }


def attach_memory_proposal(
    state: AgentState, config: RunnableConfig
) -> dict[str, Any]:
    """Register at most one pending proposal; drop if one already pending."""
    run_id = state["run_id"]
    session_id = _session_id_from_config(config)
    proposal = state.get("memory_proposal")
    if not proposal:
        _append_trace(run_id, "attach_memory_proposal", action="noop")
        return {"memory_proposal": None}

    if get_pending_memory(session_id):
        _append_trace(
            run_id,
            "attach_memory_proposal",
            action="dropped_one_pending",
        )
        return {"memory_proposal": None}

    summary = (proposal.get("summary") or "").strip()
    category = proposal.get("category") or "known_incidents"
    poison = validate_memory_payload(summary=summary, category=category)
    if poison:
        log_proposal_event(
            {
                "session_id": session_id,
                "outcome": "rejected",
                "proposal": proposal,
                "originating_message": state.get("question") or "",
                "reason": poison,
            }
        )
        _append_trace(
            run_id,
            "attach_memory_proposal",
            action="never_store",
            reason=poison,
        )
        return {"memory_proposal": None}

    proposal_id = str(uuid.uuid4())
    pending = {
        "proposal_id": proposal_id,
        "summary": summary,
        "location": proposal.get("location") or "unknown",
        "category": category,
        "why": proposal.get("why") or "",
        "originating_message": state.get("question") or "",
        "proposed_at": _utc_now(),
    }
    set_pending_memory(session_id, pending)
    log_proposal_event(
        {
            "id": proposal_id,
            "session_id": session_id,
            "outcome": "proposed",
            "proposal": {
                "summary": summary,
                "location": pending["location"],
                "category": category,
                "why": pending["why"],
                "proposal_id": proposal_id,
            },
            "originating_message": state.get("question") or "",
            "reason": None,
        }
    )
    _append_trace(
        run_id,
        "attach_memory_proposal",
        action="proposed",
        proposal_id=proposal_id,
        category=category,
    )
    return {"memory_proposal": pending}


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
    structured = generate_answer_structured(state["question"], prompt_chunks)
    answer = structured["answer"]
    proposal = structured.get("memory_proposal")
    sources_ran = ["retrieve_context"]
    _append_trace(
        run_id,
        "generate_answer_node",
        question=state["question"],
        context=context,
        answer=answer,
        sources_ran=sources_ran,
        memory_proposal=proposal,
    )
    return {
        "answer": answer,
        "sources_ran": sources_ran,
        "memory_proposal": proposal,
    }


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
    proposal: dict[str, Any] | None = None

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
            structured = generate_answer_structured(
                state["question"], prompt_chunks
            )
            rag_text = structured["answer"]
            proposal = structured.get("memory_proposal")
            answer = f"{tool_text}\n\n{rag_text}"
            sources_ran = ["ticket_lookup", "retrieve_context"]
        elif tool_ok and tool_text:
            answer = tool_text
            sources_ran = ["ticket_lookup"]
        elif context:
            prompt_chunks = [
                {k: v for k, v in c.items() if k != "_score"} for c in context
            ]
            structured = generate_answer_structured(
                state["question"], prompt_chunks
            )
            rag_text = structured["answer"]
            proposal = structured.get("memory_proposal")
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
        memory_proposal=proposal,
    )
    return {
        "answer": answer,
        "sources_ran": sources_ran,
        "memory_proposal": proposal,
    }


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
) -> Literal["resolve_memory", "output_guardrails"]:
    if state.get("guardrail_blocked"):
        return "output_guardrails"
    return "resolve_memory"


def _route_after_resolve(
    state: AgentState,
) -> Literal["route_sources", "output_guardrails"]:
    if state.get("skip_sources"):
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


def _memory_available_for_question(question: str) -> bool:
    """True when persistent memory has entries relevant to the question."""
    try:
        from pipelines.memory_store import guess_location_from_text, read_memory
    except Exception:  # noqa: BLE001
        return False
    location = guess_location_from_text(question)
    entries = read_memory(location=location) if location else []
    return bool(entries)


def _route_after_retrieve(
    state: AgentState,
) -> Literal["refuse_no_context", "generate_answer_node", "compose_answer"]:
    if state.get("route") == "both":
        return "compose_answer"
    if state.get("context"):
        return "generate_answer_node"
    # Empty RAG: still generate when location memory can answer (hours, etc.).
    if _memory_available_for_question(state.get("question") or ""):
        return "generate_answer_node"
    return "refuse_no_context"


def _build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("validate_question", validate_question)
    builder.add_node("input_guardrails", input_guardrails)
    builder.add_node("resolve_memory", resolve_memory)
    builder.add_node("route_sources", route_sources)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("refuse_no_context", refuse_no_context)
    builder.add_node("generate_answer_node", generate_answer_node)
    builder.add_node("lookup_ticket", lookup_ticket_node)
    builder.add_node("compose_answer", compose_answer)
    builder.add_node("attach_memory_proposal", attach_memory_proposal)
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
            "resolve_memory": "resolve_memory",
            "output_guardrails": "output_guardrails",
        },
    )
    builder.add_conditional_edges(
        "resolve_memory",
        _route_after_resolve,
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
    builder.add_edge("refuse_no_context", "attach_memory_proposal")
    builder.add_edge("generate_answer_node", "attach_memory_proposal")
    builder.add_edge("compose_answer", "attach_memory_proposal")
    builder.add_edge("attach_memory_proposal", "output_guardrails")
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
        "memory_proposal": None,
        "memory_decision": None,
        "skip_sources": False,
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
            "memory_proposal": None,
        }
        return {"run_id": rid, "answer": safe, "memory_proposal": None}

    error = final.get("error")
    answer = final.get("answer")
    tool_result = final.get("tool_result") or {}
    sources_ran = list(final.get("sources_ran") or [])
    route = final.get("route")
    memory_proposal = final.get("memory_proposal")
    final_payload: dict[str, Any] = {
        "question": final.get("question"),
        "context": final.get("context") or [],
        "answer": answer,
        "error": error,
        "route": route,
        "sources_ran": sources_ran,
        "user_id": final.get("user_id"),
        "guardrail_blocked": bool(final.get("guardrail_blocked")),
        "memory_proposal": memory_proposal,
        "memory_decision": final.get("memory_decision"),
    }
    if tool_result.get("ok"):
        final_payload["matched_by"] = tool_result.get("matched_by")
    TRACES[rid]["final"] = final_payload
    if error:
        return {"run_id": rid, "error": error}
    return {
        "run_id": rid,
        "answer": answer or "",
        "memory_proposal": memory_proposal,
    }


# Re-export for HTTP summary endpoint.
__all__ = [
    "COMPILED_GRAPH",
    "TRACES",
    "get_checkpoint_state",
    "get_guardrail_summary",
    "get_trace",
    "invoke_support_agent",
]
