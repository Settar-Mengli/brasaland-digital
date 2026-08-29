"""inventory_quantity_check_and_location_indexes

Revision ID: e4f8a1b2c3d4
Revises: d38c62feec63
Create Date: 2026-08-29 05:55:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "e4f8a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d38c62feec63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_ingrediententry_quantity_positive",
        "ingrediententry",
        "quantity > 0",
    )
    op.create_check_constraint(
        "ck_ingredientexit_quantity_positive",
        "ingredientexit",
        "quantity > 0",
    )
    op.create_index(
        "ix_ingrediententry_ingredient_location",
        "ingrediententry",
        ["ingredient_id", "location_id"],
    )
    op.create_index(
        "ix_ingredientexit_ingredient_location",
        "ingredientexit",
        ["ingredient_id", "location_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ingredientexit_ingredient_location", table_name="ingredientexit")
    op.drop_index(
        "ix_ingrediententry_ingredient_location", table_name="ingrediententry"
    )
    op.drop_constraint(
        "ck_ingredientexit_quantity_positive", "ingredientexit", type_="check"
    )
    op.drop_constraint(
        "ck_ingrediententry_quantity_positive", "ingrediententry", type_="check"
    )
