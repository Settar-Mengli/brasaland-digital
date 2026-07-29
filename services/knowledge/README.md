# Brasaland Knowledge API

JWT-guarded RAG Q&A over company manuals (loyalty, waste, allergens, supplier ordering).

**Port:** 8015 · **Collection:** `brasaland_knowledge` (Qdrant Cosine, 384-dim)

## Why JWT?

`POST /knowledge/query` calls a **metered** LLM gateway. Guarding the endpoint prevents unauthenticated callers from burning the monthly budget on a published port. Manuals themselves are not secret — the auth rationale is cost/abuse control (unlike open reporting GETs).

## Architecture

- Retrieval + generation live in `data/pipelines/rag.py` (`query()` is the sole public generation entry).
- This service imports `pipelines` via `config.py` sys.path / Docker `PYTHONPATH=/app/data` (same pattern as `services/reporting`).
- Indexing is **operator-run**, not app lifespan: `scripts/index_knowledge_base.py`.

## Endpoints

| Method | Path | Auth | Body / response |
| --- | --- | --- | --- |
| `GET` | `/` | no | `{"service":"knowledge"}` |
| `POST` | `/knowledge/query` | Bearer JWT | `{"question":"..."}` → `{"answer":"..."}` only |

## Env

Copy the repo-root `.env.example` → `.env` (never commit secrets). Required for live answers:

- `QDRANT_URL`, `LLM_GATEWAY_API_KEY`, `LLM_GATEWAY_BASE_URL`, `GENERATION_MODEL_ID`
- `EMBED_MODEL_ID` (default `BAAI/bge-small-en-v1.5`)
- `KNOWLEDGE_CORPUS_PATH` (optional; default repo `docs/company-knowledge-base`)
- `JWT_PUBLIC_KEY`, `JWT_ALGORITHM`

## Index the corpus

```powershell
uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py
```

Compose mounts manuals read-only at `/app/docs/company-knowledge-base` and sets `KNOWLEDGE_CORPUS_PATH` accordingly.

## Local run

```powershell
cd services/knowledge
uv sync --python 3.13
uv run uvicorn app:app --host 0.0.0.0 --port 8015 --reload
```

## Tests

```powershell
cd services/knowledge
uv run pytest
```
