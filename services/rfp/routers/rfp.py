"""HTTP routes for RFP ticket upload and row-status poll."""

from typing import Annotated, Any, Literal
from uuid import uuid4

from brasaland_auth_verify.deps import get_verified_claims
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlmodel import Session

from approval_driver import (
    apply_ceo_decision,
    apply_section_decision,
    serialize_final_document,
)
from database import get_db
from dependencies import require_ticket_access
from pipelines.rfp_intake.repository import (
    create_ticket,
    get_department_sections,
    get_final_document,
    get_ticket,
)
from rate_limit import RFP_UPLOAD_RATE_LIMIT, limiter
from tasks import process_rfp, process_rfp_approval, process_rfp_response
import upload
from upload import _safe_unlink, save_upload_to_temp

router = APIRouter(prefix="/rfp")


class SectionDecisionBody(BaseModel):
    action: Literal["approve", "reject", "request_changes"]
    feedback: str | None = Field(default=None)


class CeoDecisionBody(BaseModel):
    action: Literal["approve", "reject"]


def _caller_uuid(claims: dict[str, Any]) -> str:
    user_id = claims.get("user_id", claims.get("sub"))
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(user_id)


@router.post("/tickets", status_code=202)
@limiter.limit(RFP_UPLOAD_RATE_LIMIT)
async def post_ticket(
    request: Request,
    file: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_db)],
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> JSONResponse:
    owner_uuid = _caller_uuid(claims)
    temp_path, content_hash = await save_upload_to_temp(file)
    final_path = upload.DATA_RAW / f"{uuid4().hex}.pdf"
    try:
        temp_path.rename(final_path)
    except OSError as exc:
        _safe_unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="failed to store uploaded PDF",
        ) from exc
    try:
        ticket, created = create_ticket(
            session,
            rfp_id=uuid4().hex,
            content_hash=content_hash,
            raw_pdf_path=str(final_path),
            owner_user_uuid=owner_uuid,
        )
    except Exception:
        _safe_unlink(final_path)
        raise
    if not created:
        _safe_unlink(final_path)
    else:
        process_rfp.delay(ticket.ticket_id)
    return JSONResponse(
        status_code=202,
        content={
            "ticket_id": ticket.ticket_id,
            "rfp_id": ticket.rfp_id,
            "status": ticket.status,
        },
    )


@router.post("/tickets/{ticket_id}/response", status_code=202)
def post_ticket_response(
    ticket_id: str,
    session: Annotated[Session, Depends(get_db)],
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> JSONResponse:
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
    require_ticket_access(ticket, claims)
    if ticket.status != "intake_complete":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "ticket must be intake_complete to start response generation "
                f"(current status: {ticket.status})"
            ),
        )
    process_rfp_response.delay(ticket.ticket_id)
    return JSONResponse(
        status_code=202,
        content={
            "ticket_id": ticket.ticket_id,
            "rfp_id": ticket.rfp_id,
            "status": ticket.status,
        },
    )


@router.post("/tickets/{ticket_id}/approval", status_code=202)
def post_ticket_approval(
    ticket_id: str,
    session: Annotated[Session, Depends(get_db)],
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> JSONResponse:
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
    require_ticket_access(ticket, claims)
    if ticket.status != "under_evaluation":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "ticket must be under_evaluation to start approval "
                f"(current status: {ticket.status})"
            ),
        )
    process_rfp_approval.delay(ticket.ticket_id)
    return JSONResponse(
        status_code=202,
        content={
            "ticket_id": ticket.ticket_id,
            "rfp_id": ticket.rfp_id,
            "status": ticket.status,
        },
    )


@router.post("/tickets/{ticket_id}/sections/{department_id}/decision")
def post_section_decision(
    ticket_id: str,
    department_id: str,
    body: SectionDecisionBody,
    session: Annotated[Session, Depends(get_db)],
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> dict[str, Any]:
    """Resume one department approval interrupt (approve / reject / request_changes).

    Resume-value contract (matches ``approve_node`` in approval_graph.py):
    - plain string action when no feedback
    - ``{action, feedback}`` dict when feedback is present (feeds human_feedback → regen)
    """
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
    require_ticket_access(ticket, claims)
    try:
        return apply_section_decision(
            session,
            ticket_id=ticket_id,
            department_id=department_id,
            action=body.action,
            feedback=body.feedback,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001 — graph/checkpointer failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"approval resume failed: {type(exc).__name__}",
        ) from exc


@router.post("/tickets/{ticket_id}/ceo/decision")
def post_ceo_decision(
    ticket_id: str,
    body: CeoDecisionBody,
    session: Annotated[Session, Depends(get_db)],
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> dict[str, Any]:
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
    require_ticket_access(ticket, claims)
    try:
        return apply_ceo_decision(
            session,
            ticket_id=ticket_id,
            action=body.action,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001 — graph/checkpointer failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CEO resume failed: {type(exc).__name__}",
        ) from exc


@router.get("/tickets/{ticket_id}")
def get_ticket_status(
    ticket_id: str,
    session: Annotated[Session, Depends(get_db)],
    claims: Annotated[dict[str, Any], Depends(get_verified_claims)],
) -> dict[str, Any]:
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
    require_ticket_access(ticket, claims)
    sections = get_department_sections(session, ticket_id)
    arbitration: dict[str, Any] | None = None
    section_payloads: list[dict[str, Any]] = []
    for row in sections:
        eval_results = dict(row.evaluation_results or {}) if row.evaluation_results else None
        if arbitration is None and isinstance(eval_results, dict):
            arb = eval_results.get("arbitration")
            if isinstance(arb, dict):
                arbitration = dict(arb)
        awaiting = (
            row.approval_status == "pending"
            and isinstance(eval_results, dict)
            and bool(eval_results.get("interrupt_id"))
        )
        section_payloads.append(
            {
                "department_id": row.department_id,
                "key_aspects": row.key_aspects,
                "draft_content": row.draft_content,
                "evaluation_results": row.evaluation_results,
                "approval_status": row.approval_status,
                "approver": row.approver,
                "approved_at": (
                    row.approved_at.isoformat() if row.approved_at else None
                ),
                "awaiting_decision": awaiting,
            }
        )

    payload: dict[str, Any] = {
        "ticket_id": ticket.ticket_id,
        "rfp_id": ticket.rfp_id,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
        "sections": section_payloads,
        "arbitration": arbitration,
    }
    if ticket.status == "done":
        payload["final_document"] = serialize_final_document(
            get_final_document(session, ticket_id)
        )
    return payload
