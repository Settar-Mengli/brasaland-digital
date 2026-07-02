from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlmodel import Session

from database import get_db
from dependencies import get_current_user_uuid
from models import Ingredient, IngredientEntry, IngredientExit
from schemas import IngredientCreate, IngredientResponse

router = APIRouter(prefix="/inventory")


def _entry_totals_subquery() -> object:
    return (
        select(
            IngredientEntry.ingredient_id.label("ingredient_id"),
            func.coalesce(func.sum(IngredientEntry.quantity), 0.0).label(
                "entries_total"
            ),
        )
        .group_by(IngredientEntry.ingredient_id)
        .subquery()
    )


def _exit_totals_subquery() -> object:
    return (
        select(
            IngredientExit.ingredient_id.label("ingredient_id"),
            func.coalesce(func.sum(IngredientExit.quantity), 0.0).label(
                "exits_total"
            ),
        )
        .group_by(IngredientExit.ingredient_id)
        .subquery()
    )


def _ingredients_with_stock_stmt(ingredient_id: int | None = None) -> object:
    entry_totals = _entry_totals_subquery()
    exit_totals = _exit_totals_subquery()
    current_stock = (
        func.coalesce(entry_totals.c.entries_total, 0.0)
        - func.coalesce(exit_totals.c.exits_total, 0.0)
    ).label("current_stock")
    stmt = (
        select(Ingredient, current_stock)
        .select_from(Ingredient)
        .outerjoin(entry_totals, Ingredient.id == entry_totals.c.ingredient_id)
        .outerjoin(exit_totals, Ingredient.id == exit_totals.c.ingredient_id)
    )
    if ingredient_id is not None:
        stmt = stmt.where(Ingredient.id == ingredient_id)
    return stmt


def _to_response(ingredient: Ingredient, current_stock: float) -> IngredientResponse:
    if ingredient.id is None:
        raise RuntimeError("Ingredient must have an id")
    return IngredientResponse(
        id=ingredient.id,
        name=ingredient.name,
        sku=ingredient.sku,
        unit=ingredient.unit,
        category=ingredient.category,
        country=ingredient.country,
        current_stock=float(current_stock),
    )


def _fetch_ingredients_with_stock(
    session: Session, ingredient_id: int | None = None
) -> list[tuple[Ingredient, float]]:
    stmt = _ingredients_with_stock_stmt(ingredient_id)
    rows = session.exec(stmt).all()
    return [(ingredient, float(stock)) for ingredient, stock in rows]


@router.get("/products", response_model=list[IngredientResponse])
def list_products(
    session: Annotated[Session, Depends(get_db)],
) -> list[IngredientResponse]:
    return [
        _to_response(ingredient, stock)
        for ingredient, stock in _fetch_ingredients_with_stock(session)
    ]


@router.get("/products/{ingredient_id}", response_model=IngredientResponse)
def get_product(
    ingredient_id: int,
    session: Annotated[Session, Depends(get_db)],
) -> IngredientResponse:
    rows = _fetch_ingredients_with_stock(session, ingredient_id=ingredient_id)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found",
        )
    ingredient, stock = rows[0]
    return _to_response(ingredient, stock)


@router.post("/products", response_model=IngredientResponse)
def create_product(
    payload: IngredientCreate,
    session: Annotated[Session, Depends(get_db)],
    _user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> IngredientResponse:
    ingredient = Ingredient.model_validate(payload)
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)
    return _to_response(ingredient, 0.0)
