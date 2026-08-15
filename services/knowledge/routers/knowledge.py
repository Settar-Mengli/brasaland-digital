"""HTTP routes for Brasaland knowledge-base Q&A."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from dependencies import get_current_user_uuid
from rate_limit import KNOWLEDGE_QUERY_RATE_LIMIT, limiter

router = APIRouter(prefix="/knowledge")


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(min_length=1)


class KnowledgeQueryResponse(BaseModel):
    answer: str


@router.post("/query", response_model=KnowledgeQueryResponse)
@limiter.limit(KNOWLEDGE_QUERY_RATE_LIMIT)
def post_query(
    request: Request,
    body: Annotated[KnowledgeQueryRequest, Body()],
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> KnowledgeQueryResponse:
    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="question must not be empty",
        )
    from pipelines.rag import query as run_query

    answer = run_query(question)
    return KnowledgeQueryResponse(answer=answer)
