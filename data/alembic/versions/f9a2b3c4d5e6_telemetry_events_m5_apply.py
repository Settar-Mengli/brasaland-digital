"""telemetry_events_m5_apply

Revision ID: f9a2b3c4d5e6
Revises: e4f8a1b2c3d4
Create Date: 2026-08-31 08:40:00.000000

Idempotent create of public.telemetry_events for brasaland-m5 where the table was
missing after a baseline stamp without full upgrade. No-op when the table already
exists (disposable Postgres CI with full baseline).
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "f9a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e4f8a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_NAME = "telemetry_events"


def _table_exists() -> bool:
    bind = op.get_bind()
    return inspect(bind).has_table(TABLE_NAME)


def upgrade() -> None:
    if _table_exists():
        return

    op.create_table(
        TABLE_NAME,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("event_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("service", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("level", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "tags",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column(
            "context",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_telemetry_events_event_id"),
        TABLE_NAME,
        ["event_id"],
        unique=True,
    )
    op.create_index(
        "ix_telemetry_events_event_type",
        TABLE_NAME,
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_telemetry_events_tags_gin",
        TABLE_NAME,
        ["tags"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_telemetry_events_timestamp",
        TABLE_NAME,
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    if not _table_exists():
        return

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = {idx["name"] for idx in inspector.get_indexes(TABLE_NAME)}

    for index_name in (
        "ix_telemetry_events_timestamp",
        "ix_telemetry_events_tags_gin",
        "ix_telemetry_events_event_type",
        "ix_telemetry_events_event_id",
    ):
        if index_name in existing_indexes:
            if index_name == "ix_telemetry_events_tags_gin":
                op.drop_index(
                    index_name,
                    table_name=TABLE_NAME,
                    postgresql_using="gin",
                )
            else:
                op.drop_index(index_name, table_name=TABLE_NAME)

    op.drop_table(TABLE_NAME)
