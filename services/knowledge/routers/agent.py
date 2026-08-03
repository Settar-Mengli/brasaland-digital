"""HTTP routes for the LangGraph support agent."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dependencies import get_current_user_uuid, oauth2_scheme

router = APIRouter(prefix="/agent")


class AgentQueryRequest(BaseModel):
    question: str = Field(default="")


class AgentQueryResponse(BaseModel):
    run_id: str
    answer: str


@router.post("/query", response_model=AgentQueryResponse)
def post_agent_query(
    body: AgentQueryRequest,
    user_uuid: Annotated[str, Depends(get_current_user_uuid)],
    access_token: Annotated[str, Depends(oauth2_scheme)],
) -> AgentQueryResponse:
    from pipelines.support_agent import invoke_support_agent

    # Forward inbound Bearer into MCP client via configurable (not AgentState).
    result = invoke_support_agent(
        body.question,
        access_token=access_token,
        user_id=user_uuid,
    )
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )
    return AgentQueryResponse(run_id=result["run_id"], answer=result["answer"])


@router.get("/trace/{run_id}")
def get_agent_trace(
    run_id: str,
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> dict[str, Any]:
    from pipelines.support_agent import get_trace

    trace = get_trace(run_id)
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="trace not found",
        )
    return trace
