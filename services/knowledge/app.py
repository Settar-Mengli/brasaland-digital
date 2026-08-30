from brasaland_auth_verify.surface import fastapi_docs_kwargs
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import config  # noqa: F401 — sys.path for data/pipelines + .env
from rate_limit import limiter
from routers.agent import router as agent_router
from routers.knowledge import router as knowledge_router
from routers.public_knowledge import router as public_knowledge_router

app = FastAPI(title="Brasaland Knowledge API", **fastapi_docs_kwargs())
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(knowledge_router)
app.include_router(public_knowledge_router)
app.include_router(agent_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "knowledge"}
