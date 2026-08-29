from __future__ import annotations

from contextlib import asynccontextmanager

from brasaland_auth_verify.surface import fastapi_docs_kwargs
from fastapi import FastAPI
from sqlmodel import SQLModel

import models  # noqa: F401
from database import engine
from routers.inventory import router as inventory_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if engine.dialect.name != "postgresql":
        SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Brasaland Inventory API",
    lifespan=lifespan,
    **fastapi_docs_kwargs(),
)
app.include_router(inventory_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "inventory"}
