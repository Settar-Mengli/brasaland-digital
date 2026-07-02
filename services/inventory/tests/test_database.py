from __future__ import annotations

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from models import Ingredient, IngredientEntry


def test_tables_exist(engine: Engine) -> None:
    table_names = set(inspect(engine).get_table_names())
    assert table_names == {"ingredient", "ingrediententry", "ingredientexit"}


@pytest.fixture
def engine() -> Engine:
    import database

    return database.engine


def test_ingredient_entry_foreign_key_enforced(session: Session) -> None:
    entry = IngredientEntry(
        ingredient_id=999,
        quantity=10.0,
        supplier_name="Carnes del Valle S.A.",
        location_id=1,
        user_uuid="supervisor-uuid-1",
    )
    session.add(entry)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_ingredient_entry_accepts_valid_ingredient(session: Session) -> None:
    ingredient = Ingredient(
        name="Beef brisket",
        sku="BRS-BEEF-001",
        unit="kg",
        category="meat",
        country="CO",
    )
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)
    assert ingredient.id is not None

    entry = IngredientEntry(
        ingredient_id=ingredient.id,
        quantity=50.0,
        supplier_name="Carnes del Valle S.A.",
        location_id=1,
        user_uuid="supervisor-uuid-1",
    )
    session.add(entry)
    session.commit()
