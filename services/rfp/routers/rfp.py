"""HTTP routes for RFP ticket upload and row-status poll."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlmodel import Session

from database import get_db
from dependencies import get_current_user_uuid
from pipelines.rfp_intake.repository import create_ticket, get_ticket
from tasks import process_rfp
from upload import save_upload

router = APIRouter(prefix="/rfp")


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


@router.get("/tickets/{ticket_id}")
def get_ticket_status(
    ticket_id: str,
    session: Annotated[Session, Depends(get_db)],
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> dict[str, str]:
    ticket = get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ticket not found",
        )
    return {
        "ticket_id": ticket.ticket_id,
        "rfp_id": ticket.rfp_id,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }
