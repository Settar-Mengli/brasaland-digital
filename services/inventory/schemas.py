from __future__ import annotations

import math
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

PositiveQuantity = Annotated[float, Field(gt=0)]


def _validate_finite_positive_quantity(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("quantity must be a finite number greater than 0")
    return value


class IngredientCreate(BaseModel):
    name: str
    sku: str
    unit: str
    category: str
    country: str


class IngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    unit: str
    category: str
    country: str
    current_stock: float


class IngredientEntryCreate(BaseModel):
    ingredient_id: int
    quantity: PositiveQuantity
    unit_cost: float | None = Field(default=None, ge=0)
    supplier_name: str
    location_id: int

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: float) -> float:
        return _validate_finite_positive_quantity(value)


class IngredientEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    unit_cost: float | None = None
    supplier_name: str
    location_id: int
    created_at: datetime
    user_uuid: str


class IngredientExitCreate(BaseModel):
    ingredient_id: int
    quantity: PositiveQuantity
    reason: str
    location_id: int

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: float) -> float:
        return _validate_finite_positive_quantity(value)


class IngredientExitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    reason: str
    location_id: int
    created_at: datetime
    user_uuid: str


class IngredientInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    unit: str
    category: str
    country: str


class IngredientEntryWithIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    unit_cost: float | None = None
    supplier_name: str
    location_id: int
    created_at: datetime
    user_uuid: str
    ingredient: IngredientInfo


class IngredientExitWithIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    reason: str
    location_id: int
    created_at: datetime
    user_uuid: str
    ingredient: IngredientInfo


class OrdersListResponse(BaseModel):
    entries: list[IngredientEntryWithIngredientResponse]
    exits: list[IngredientExitWithIngredientResponse]
