"""HTTP routes for public guest knowledge Q&A (website BFF only)."""

from typing import Annotated

from brasaland_proxy_trust import rate_limit_client_key
from dependencies import require_website_service
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from public_settings import public_knowledge_enabled
from public_usage import check_public_usage_caps
from pydantic import BaseModel, Field
from rate_limit import PUBLIC_KNOWLEDGE_QUERY_RATE_LIMIT, limiter

router = APIRouter(prefix="/public/knowledge")


class PublicKnowledgeQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)


class PublicKnowledgeQueryResponse(BaseModel):
    answer: str


@router.post("/query", response_model=PublicKnowledgeQueryResponse)
@limiter.limit(PUBLIC_KNOWLEDGE_QUERY_RATE_LIMIT)
def post_public_query(
    request: Request,
    body: Annotated[PublicKnowledgeQueryRequest, Body()],
    _service: Annotated[dict, Depends(require_website_service)],
) -> PublicKnowledgeQueryResponse:
    if not public_knowledge_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Public knowledge is not enabled",
        )

    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="question must not be empty",
        )

    check_public_usage_caps(rate_limit_client_key(request))

    from pipelines.public_rag import query_public
    from pipelines.rag import PublicKnowledgeNotIndexedError

    try:
        answer = query_public(question)
    except PublicKnowledgeNotIndexedError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Public knowledge is not available",
        ) from None
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return PublicKnowledgeQueryResponse(answer=answer)
