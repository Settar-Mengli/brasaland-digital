# Brasaland Knowledge API

JWT-guarded RAG Q&A over company manuals (loyalty, waste, allergens, supplier ordering).

**Port:** 8015 · **Collection:** `brasaland_knowledge` (Qdrant Cosine, 384-dim)

## Why JWT?

`POST /knowledge/query` and `POST /agent/query` call a **metered** LLM gateway. Guarding the endpoints prevents unauthenticated callers from burning the monthly budget on a published port. Manuals themselves are not secret — the auth rationale is cost/abuse control (unlike open reporting GETs). Trace reads are JWT-guarded for the same abuse boundary.

## Architecture

- Retrieval + generation live in `data/pipelines/rag.py` (`retrieve`, `generate_answer`, `query`).
- LangGraph support agent: `data/pipelines/support_agent.py` — separate retrieve / generate nodes, conditional edges, MemorySaver checkpointing (`thread_id` = `run_id`), in-process `TRACES`.
- This service imports `pipelines` via `config.py` sys.path / Docker `PYTHONPATH=/app/data` (same pattern as `services/reporting`).
- Indexing is **operator-run**, not app lifespan: `scripts/index_knowledge_base.py`.

## Endpoints

| Method | Path | Auth | Body / response |
| --- | --- | --- | --- |
| `GET` | `/` | no | `{"service":"knowledge"}` |
| `POST` | `/knowledge/query` | Bearer JWT | `{"question":"..."}` → `{"answer":"..."}` only |
| `POST` | `/agent/query` | Bearer JWT | `{"question":"..."}` → `{"run_id","answer"}`; errors → `{"detail"}` |
| `GET` | `/agent/trace/{run_id}` | Bearer JWT | structured trace; `404` if unknown |

Empty question and no-context paths do not force generation. No-context refusal copy:

`I don't have information about that in the official Brasaland manuals.`

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

uv run --directory data --python 3.13 pytest
```

## Live grounding recon (gateway required — not CI)

CI asserts KB facts on the agent **trace context** (Path B). To verify real generation locally with gateway env set:

```powershell
cd data
uv run --python 3.13 python -c @"
from pipelines.rag import generate_answer
chunks = [{
    'text': 'Gold (50+ points): 15% permanent discount and early access to the seasonal menu before the general public.',
    'source_document': 'loyalty-program',
    'section': 'Program tiers',
}]
answer = generate_answer('How many points for Gold?', chunks)
assert '50+' in answer and '15%' in answer, answer
print('live grounding ok:', answer)
"@
```
