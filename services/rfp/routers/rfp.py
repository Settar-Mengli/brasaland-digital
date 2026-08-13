"""HTTP routes for RFP ticket upload and row-status poll."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlmodel import Session
from uuid import uuid4

from approval_driver import (
    apply_ceo_decision,
    apply_section_decision,
    serialize_final_document,
)
from database import get_db
from dependencies import get_current_user_uuid
from pipelines.rfp_intake.repository import (
    create_ticket,
    get_department_sections,
    get_final_document,
    get_ticket,
)
from tasks import process_rfp, process_rfp_approval, process_rfp_response
from upload import save_upload

router = APIRouter(prefix="/rfp")


class SectionDecisionBody(BaseModel):
    action: Literal["approve", "reject", "request_changes"]
    feedback: str | None = Field(default=None)


class CeoDecisionBody(BaseModel):
    action: Literal["approve", "reject"]


@router.post("/tickets", status_code=202)
async def post_ticket(
    file: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_db)],
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> JSONResponse:
    path, content_hash = await save_upload(file)
    rfp_id = uuid4().hex
    ticket, created = create_ticket(
        session,
        rfp_id=rfp_id,
        content_hash=content_hash,
        raw_pdf_path=str(path),
    )
    if created:
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
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> JSONResponse:
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
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
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> JSONResponse:
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
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
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> dict[str, Any]:
    """Resume one department approval interrupt (approve / reject / request_changes).

    Resume-value contract (matches ``approve_node`` in approval_graph.py):
    - plain string action when no feedback
    - ``{action, feedback}`` dict when feedback is present (feeds human_feedback → regen)
    """
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
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> dict[str, Any]:
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
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> dict[str, Any]:
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
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
