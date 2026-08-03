from __future__ import annotations

from fastapi import FastAPI

import config  # noqa: F401 — sys.path for data/pipelines + .env
from routers.agent import router as agent_router
from routers.knowledge import router as knowledge_router

app = FastAPI(title="Brasaland Knowledge API")
app.include_router(knowledge_router)
app.include_router(agent_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "knowledge"}
