from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    quantity: float
    supplier_name: str
    location_id: int


class IngredientEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    supplier_name: str
    location_id: int
    created_at: datetime
    user_uuid: str


class IngredientExitCreate(BaseModel):
    ingredient_id: int
    quantity: float
    reason: str
    location_id: int


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
