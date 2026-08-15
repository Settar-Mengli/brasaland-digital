"""HTTP routes for the LangGraph support agent."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from dependencies import (
    get_current_user_uuid,
    get_verified_claims,
    oauth2_scheme,
    require_admin,
)
from rate_limit import AGENT_QUERY_RATE_LIMIT, limiter

router = APIRouter(prefix="/agent")


class AgentQueryRequest(BaseModel):
    question: str = Field(default="")
    session_id: str | None = Field(default=None)


class AgentQueryResponse(BaseModel):
    run_id: str
    answer: str
    memory_proposal: dict[str, Any] | None = None


@router.post("/query", response_model=AgentQueryResponse)
@limiter.limit(AGENT_QUERY_RATE_LIMIT)
def post_agent_query(
    request: Request,
    body: Annotated[AgentQueryRequest, Body()],
    user_uuid: Annotated[str, Depends(get_current_user_uuid)],
    access_token: Annotated[str, Depends(oauth2_scheme)],
) -> AgentQueryResponse:
    from pipelines.support_agent import invoke_support_agent

    # Forward inbound Bearer + session_id via configurable (not AgentState).
    result = invoke_support_agent(
        body.question,
        access_token=access_token,
        user_id=user_uuid,
        session_id=body.session_id,
    )
    if "error" in result:
        # Never forward provider/exception strings to the client.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="agent request failed",
        )
    return AgentQueryResponse(
        run_id=result["run_id"],
        answer=result["answer"],
        memory_proposal=result.get("memory_proposal"),
    )


@router.get("/trace/{run_id}")
def get_agent_trace(
    run_id: str,
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> dict[str, Any]:
    from pipelines.support_agent import get_trace

    user_uuid = str(claims.get("user_id", claims.get("sub")))
    trace = get_trace(
        run_id,
        requester_user_uuid=user_uuid,
        is_admin=bool(claims.get("is_admin")),
    )
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="trace not found",
        )
    return trace


@router.get("/guardrails/summary")
def get_agent_guardrails_summary(
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
    session_id: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    from pipelines.guardrails import get_guardrail_summary

    return get_guardrail_summary(session_id)


@router.get("/memory")
def get_agent_memory(
    user_uuid: Annotated[str, Depends(get_current_user_uuid)],
    location: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    from pipelines.memory_store import read_memory

    entries = read_memory(
        user_id=user_uuid, location=location, category=category
    )
    return {"entries": entries}


@router.get("/memory/audit")
def get_agent_memory_audit(
    _admin_uuid: Annotated[str, Depends(require_admin)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, Any]:
    from pipelines.memory_store import list_audit

    return {"events": list_audit(limit=limit)}
