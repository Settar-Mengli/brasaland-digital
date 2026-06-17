from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from supplier_directory import (
    SupplierValidationError,
    create,
    delete_supplier,
    get_supplier,
    list_suppliers,
    update_rate,
    update_status,
)
from supplier_directory.types import SupplierInput, SupplierRecord
from supplier_directory.constants import VALID_CATEGORIES

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Brasaland Supplier Directory")


class SupplierCreate(BaseModel):
    name: str
    country: Literal["Colombia", "USA"]
    categories: list[str] = Field(min_length=1)
    rate_per_unit: float = Field(gt=0)
    currency: Literal["COP", "USD"]
    status: Literal["active", "suspended"]
    contact_email: str | None = None
    notes: str | None = None


class SupplierRateUpdate(BaseModel):
    rate_per_unit: float = Field(gt=0)


class SupplierStatusUpdate(BaseModel):
    status: Literal["active", "suspended"]


class SupplierResponse(BaseModel):
    id: int
    name: str
    country: Literal["Colombia", "USA"]
    categories: list[str]
    rate_per_unit: float
    currency: Literal["COP", "USD"]
    rate_updated_at: datetime
    status: Literal["active", "suspended"]
    contact_email: str | None
    notes: str | None


# Stored records enter the DB only via validated write paths; Literal casts are runtime-safe.
def _to_response(record: SupplierRecord) -> SupplierResponse:
    return SupplierResponse(
        id=record["id"],
        name=record["name"],
        country=record["country"],  # type: ignore[arg-type]
        categories=list(record["categories"]),
        rate_per_unit=record["rate_per_unit"],
        currency=record["currency"],  # type: ignore[arg-type]
        rate_updated_at=datetime.fromisoformat(record["rate_updated_at"]),
        status=record["status"],  # type: ignore[arg-type]
        contact_email=record.get("contact_email"),
        notes=record.get("notes"),
    )


def _create_payload(body: SupplierCreate) -> SupplierInput:
    return {
        "name": body.name,
        "country": body.country,
        "categories": list(body.categories),
        "rate_per_unit": body.rate_per_unit,
        "currency": body.currency,
        "status": body.status,
        "contact_email": body.contact_email,
        "notes": body.notes,
    }


@app.post("/suppliers", response_model=SupplierResponse, status_code=201)
def create_supplier(body: SupplierCreate) -> SupplierResponse:
    try:
        record = create(_create_payload(body))
    except SupplierValidationError as error:
        raise HTTPException(status_code=422, detail=list(error.failures)) from error
    return _to_response(record)


@app.get("/suppliers", response_model=list[SupplierResponse])
def list_all_suppliers(
    country: Literal["Colombia", "USA"] | None = Query(default=None),
    category: str | None = Query(default=None),
) -> list[SupplierResponse]:
    if category is not None and category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=["category must be a valid category value"],
        )
    records = list_suppliers(country=country, category=category)
    return [_to_response(record) for record in records]


@app.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier_by_id(supplier_id: int) -> SupplierResponse:
    record = get_supplier(supplier_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _to_response(record)


@app.patch("/suppliers/{supplier_id}/rate", response_model=SupplierResponse)
def patch_supplier_rate(
    supplier_id: int,
    body: SupplierRateUpdate,
) -> SupplierResponse:
    try:
        record = update_rate(supplier_id, body.rate_per_unit)
    except SupplierValidationError as error:
        raise HTTPException(status_code=422, detail=list(error.failures)) from error
    if record is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _to_response(record)


@app.patch("/suppliers/{supplier_id}/status", response_model=SupplierResponse)
def patch_supplier_status(
    supplier_id: int,
    body: SupplierStatusUpdate,
) -> SupplierResponse:
    try:
        record = update_status(supplier_id, body.status)
    except SupplierValidationError as error:
        raise HTTPException(status_code=422, detail=list(error.failures)) from error
    if record is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _to_response(record)


@app.delete("/suppliers/{supplier_id}", status_code=204)
def remove_supplier(supplier_id: int) -> Response:
    if not delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return Response(status_code=204)


@app.get("/")
async def read_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
