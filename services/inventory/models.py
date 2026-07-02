from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Ingredient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(unique=True)
    unit: str
    category: str
    country: str


class IngredientEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id")
    quantity: float
    supplier_name: str
    location_id: int
    created_at: datetime = Field(default_factory=_utc_now)
    user_uuid: str


class IngredientExit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id")
    quantity: float
    reason: str
    location_id: int
    created_at: datetime = Field(default_factory=_utc_now)
    user_uuid: str
