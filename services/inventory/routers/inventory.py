from __future__ import annotations

from typing import Annotated

from database import get_db
from dependencies import get_current_user_uuid, require_authorized_location_id
from fastapi import APIRouter, Depends, HTTPException, status
from models import Ingredient, IngredientEntry, IngredientExit
from schemas import (
    IngredientCreate,
    IngredientEntryCreate,
    IngredientEntryResponse,
    IngredientEntryWithIngredientResponse,
    IngredientExitCreate,
    IngredientExitResponse,
    IngredientExitWithIngredientResponse,
    IngredientInfo,
    IngredientResponse,
    OrdersListResponse,
)
from sqlalchemy import func, select, text
from sqlmodel import Session

router = APIRouter(prefix="/inventory")

INSUFFICIENT_STOCK_MESSAGE = (
    "Insufficient stock for ingredient '{name}'. Available: {available}, requested: {requested}."
)
INGREDIENT_NOT_FOUND_MESSAGE = "Ingredient not found"
VALID_EXIT_REASONS = frozenset({"consumption", "waste"})


def _entry_totals_subquery(location_id: int) -> object:
    return (
        select(
            IngredientEntry.ingredient_id.label("ingredient_id"),
            func.coalesce(func.sum(IngredientEntry.quantity), 0.0).label("entries_total"),
        )
        .where(IngredientEntry.location_id == location_id)
        .group_by(IngredientEntry.ingredient_id)
        .subquery()
    )


def _exit_totals_subquery(location_id: int) -> object:
    return (
        select(
            IngredientExit.ingredient_id.label("ingredient_id"),
            func.coalesce(func.sum(IngredientExit.quantity), 0.0).label("exits_total"),
        )
        .where(IngredientExit.location_id == location_id)
        .group_by(IngredientExit.ingredient_id)
        .subquery()
    )


def _ingredients_with_stock_stmt(location_id: int, ingredient_id: int | None = None) -> object:
    entry_totals = _entry_totals_subquery(location_id)
    exit_totals = _exit_totals_subquery(location_id)
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
    session: Session, location_id: int, ingredient_id: int | None = None
) -> list[tuple[Ingredient, float]]:
    stmt = _ingredients_with_stock_stmt(location_id, ingredient_id)
    rows = session.exec(stmt).all()
    return [(ingredient, float(stock)) for ingredient, stock in rows]


def _get_ingredient_with_stock_or_404(
    session: Session, ingredient_id: int, location_id: int
) -> tuple[Ingredient, float]:
    rows = _fetch_ingredients_with_stock(session, location_id, ingredient_id=ingredient_id)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=INGREDIENT_NOT_FOUND_MESSAGE,
        )
    return rows[0]


def _get_ingredient_or_404(session: Session, ingredient_id: int) -> Ingredient:
    ingredient = session.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=INGREDIENT_NOT_FOUND_MESSAGE,
        )
    return ingredient


def _acquire_location_stock_lock(session: Session, ingredient_id: int, location_id: int) -> None:
    bind = session.get_bind()
    if bind.dialect.name == "postgresql":
        session.execute(
            text("SELECT pg_advisory_xact_lock(:ingredient_id, :location_id)"),
            {"ingredient_id": ingredient_id, "location_id": location_id},
        )


def _to_ingredient_info(ingredient: Ingredient) -> IngredientInfo:
    if ingredient.id is None:
        raise RuntimeError("Ingredient must have an id")
    return IngredientInfo.model_validate(ingredient)


@router.get("/products", response_model=list[IngredientResponse])
def list_products(
    session: Annotated[Session, Depends(get_db)],
    location_id: Annotated[int, Depends(require_authorized_location_id)],
) -> list[IngredientResponse]:
    return [
        _to_response(ingredient, stock)
        for ingredient, stock in _fetch_ingredients_with_stock(session, location_id)
    ]


@router.get("/products/{ingredient_id}", response_model=IngredientResponse)
def get_product(
    ingredient_id: int,
    session: Annotated[Session, Depends(get_db)],
    location_id: Annotated[int, Depends(require_authorized_location_id)],
) -> IngredientResponse:
    ingredient, stock = _get_ingredient_with_stock_or_404(session, ingredient_id, location_id)
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


@router.post("/orders/inbound", response_model=IngredientEntryResponse)
def create_inbound_order(
    payload: IngredientEntryCreate,
    session: Annotated[Session, Depends(get_db)],
    user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> IngredientEntryResponse:
    _get_ingredient_or_404(session, payload.ingredient_id)
    entry = IngredientEntry.model_validate(payload, update={"user_uuid": user_uuid})
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return IngredientEntryResponse.model_validate(entry)


@router.post("/orders/outbound", response_model=IngredientExitResponse)
def create_outbound_order(
    payload: IngredientExitCreate,
    session: Annotated[Session, Depends(get_db)],
    user_uuid: Annotated[str, Depends(get_current_user_uuid)],
) -> IngredientExitResponse:
    if payload.reason not in VALID_EXIT_REASONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='reason must be "consumption" or "waste"',
        )
    _get_ingredient_or_404(session, payload.ingredient_id)
    _acquire_location_stock_lock(session, payload.ingredient_id, payload.location_id)
    ingredient, available = _get_ingredient_with_stock_or_404(
        session, payload.ingredient_id, payload.location_id
    )
    if available - payload.quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INSUFFICIENT_STOCK_MESSAGE.format(
                name=ingredient.name,
                available=available,
                requested=payload.quantity,
            ),
        )
    exit_record = IngredientExit.model_validate(payload, update={"user_uuid": user_uuid})
    session.add(exit_record)
    session.commit()
    session.refresh(exit_record)
    return IngredientExitResponse.model_validate(exit_record)


@router.get("/orders", response_model=OrdersListResponse)
def list_orders(
    session: Annotated[Session, Depends(get_db)],
    location_id: Annotated[int, Depends(require_authorized_location_id)],
) -> OrdersListResponse:
    entry_rows = session.exec(
        select(IngredientEntry, Ingredient)
        .join(Ingredient, IngredientEntry.ingredient_id == Ingredient.id)
        .where(IngredientEntry.location_id == location_id)
    ).all()
    exit_rows = session.exec(
        select(IngredientExit, Ingredient)
        .join(Ingredient, IngredientExit.ingredient_id == Ingredient.id)
        .where(IngredientExit.location_id == location_id)
    ).all()
    return OrdersListResponse(
        entries=[
            IngredientEntryWithIngredientResponse(
                id=entry.id,
                ingredient_id=entry.ingredient_id,
                quantity=entry.quantity,
                unit_cost=entry.unit_cost,
                supplier_name=entry.supplier_name,
                location_id=entry.location_id,
                created_at=entry.created_at,
                user_uuid=entry.user_uuid,
                ingredient=_to_ingredient_info(ingredient),
            )
            for entry, ingredient in entry_rows
            if entry.id is not None
        ],
        exits=[
            IngredientExitWithIngredientResponse(
                id=exit_record.id,
                ingredient_id=exit_record.ingredient_id,
                quantity=exit_record.quantity,
                reason=exit_record.reason,
                location_id=exit_record.location_id,
                created_at=exit_record.created_at,
                user_uuid=exit_record.user_uuid,
                ingredient=_to_ingredient_info(ingredient),
            )
            for exit_record, ingredient in exit_rows
            if exit_record.id is not None
        ],
    )
