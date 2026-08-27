"""SQLModel tables for the RFP intake workflow (public schema)."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

_STATUS_CHECK = (
    "status IN ("
    "'analyzing', 'discarded', 'intake_complete', 'drafting', "
    "'under_evaluation', 'waiting_for_approval', 'done'"
    ")"
)


class Ticket(SQLModel, table=True):
    __tablename__ = "ticket"
    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_ticket_content_hash"),
        CheckConstraint(_STATUS_CHECK, name="ck_ticket_status"),
    )

    ticket_id: str = Field(sa_column=Column(Text, primary_key=True))
    rfp_id: str = Field(sa_column=Column(Text, nullable=False, index=True))
    status: str = Field(sa_column=Column(Text, nullable=False))
    raw_pdf_path: str = Field(sa_column=Column(Text, nullable=False))
    content_hash: str = Field(sa_column=Column(Text, nullable=False))
    owner_user_uuid: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True, index=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime, nullable=False),
    )


class RfpMetadata(SQLModel, table=True):
    """RFP metadata row â€” linked to Ticket by shared rfp_id uuid, not a DB FK."""

    __tablename__ = "rfp_metadata"

    rfp_id: str = Field(sa_column=Column(Text, primary_key=True))
    client_name: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    location: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    service_type: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    scope: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    deadline: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    budget_range: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    departments_needed: Optional[list[Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    readability_metrics: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    open_questions: Optional[list[Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime, nullable=False),
    )


class DepartmentSection(SQLModel, table=True):
    __tablename__ = "department_section"
    __table_args__ = (
        CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected')",
            name="ck_department_section_approval_status",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: str = Field(
        sa_column=Column(Text, ForeignKey("ticket.ticket_id"), nullable=False)
    )
    department_id: str = Field(sa_column=Column(Text, nullable=False))
    key_aspects: Optional[list[Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    draft_content: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    evaluation_results: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    approval_status: str = Field(
        default="pending",
        sa_column=Column(Text, nullable=False),
    )
    approver: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    approved_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime, nullable=False),
    )


class FinalDocument(SQLModel, table=True):
    __tablename__ = "final_document"

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: str = Field(
        sa_column=Column(Text, ForeignKey("ticket.ticket_id"), nullable=False)
    )
    sections: list[Any] = Field(sa_column=Column(JSON, nullable=False))
    total_estimated_value: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    document: Optional[dict[str, Any]] = Field(
        default=None,
        sa_column=Column(
            JSON().with_variant(JSONB(), "postgresql"),
            nullable=True,
        ),
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime, nullable=False),
    )

