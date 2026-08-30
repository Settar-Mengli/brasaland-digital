# Brasaland Knowledge API

JWT-guarded RAG Q&A over company manuals (loyalty, waste, allergens, supplier ordering).

**Port:** 8015 · **Collection:** `brasaland_knowledge` (Qdrant Cosine, 384-dim)

## Why JWT?

`POST /knowledge/query` and `POST /agent/query` call a **metered** LLM gateway. Guarding the endpoints prevents unauthenticated callers from burning the monthly budget on a published port. Manuals themselves are not secret — the auth rationale is cost/abuse control (unlike open reporting GETs). Trace reads are JWT-guarded for the same abuse boundary.

## Architecture

- Retrieval + generation live in `data/pipelines/rag.py` (`retrieve`, `generate_answer`, `generate_answer_structured`, `query`).
- LangGraph support agent: `data/pipelines/support_agent.py` — heuristic `route_sources` (ticket vs RAG vs both from the question alone; LLM router is a later swap), RAG retrieve/generate/refuse, ticket tool node, and `compose_answer` for all tool and both-route finalization. Guardrails: `input_guardrails` (pre-route) and `output_guardrails` (pre-END) via `data/pipelines/guardrails.py`; session extraction ledger for §3 piece-by-piece defense. **Agent memory (M8):** `resolve_memory` + `attach_memory_proposal`; pending proposal on `SESSION_GUARD[session_id].pending_memory`; approved entries in Redis (`REDIS_URL`) via `data/pipelines/memory_store.py` (location+category upsert); audit log with scrubbed `originating_message`. Structured single-call output (`answer` + optional `memory_proposal`). MemorySaver (`thread_id` = `run_id`); in-process `TRACES`. Inbound Bearer and optional `session_id` are forwarded via `configurable` only (never AgentState / checkpoint / trace).
- Ticket tool: `data/pipelines/tools/ticket_lookup.py` — calls company-tools MCP `check_ticket_status` (langchain-mcp-adapters over Streamable HTTP). No direct incident-manager path from the agent. Dual id / `source_incident_id` resolution lives on the MCP server. Deterministic formatter for ticket fields. Honest fallback when unavailable/unknown; malformed tool payloads → structural guardrail + fallback.
- This service imports `pipelines` via `config.py` sys.path / Docker `PYTHONPATH=/app/data` (same pattern as `services/reporting`).
- Production image runs as non-root `app` (uid/gid 1000); see `services/knowledge/Dockerfile`.
- Indexing is **operator-run**, not app lifespan: `scripts/index_knowledge_base.py`.

## Endpoints

| Method | Path | Auth | Body / response |
| --- | --- | --- | --- |
| `GET` | `/` | no | `{"service":"knowledge"}` |
| `POST` | `/knowledge/query` | Bearer JWT (rate-limited) | `{"question":"..."}` → `{"answer":"..."}` only (`RATE_LIMIT_KNOWLEDGE_QUERY`, default `20/minute`) |
| `POST` | `/public/knowledge/query` | Bearer JWT with `svc: website-knowledge` (rate-limited) | `{"question":"..."}` → `{"answer":"..."}` only; gated by `PUBLIC_KNOWLEDGE_ENABLED` (`RATE_LIMIT_PUBLIC_KNOWLEDGE_QUERY`, default `5/minute`) |
| `POST` | `/agent/query` | Bearer JWT (rate-limited) | `{"question":"...","session_id"?}` → `{"run_id","answer","memory_proposal"?}`; errors → `{"detail"}`. Optional `session_id` is the guardrail + pending-memory key (via configurable only, never checkpointed). If omitted, an ephemeral per-call UUID is used — not the JWT user id. User id for memory/trace ownership comes from JWT via `configurable` only (never AgentState). (`RATE_LIMIT_AGENT_QUERY`, default `10/minute`) |
| `GET` | `/agent/trace/{run_id}` | Bearer JWT (owner or admin) | structured trace for runs owned by the caller; cross-user → **403**; `404` if unknown |
| `GET` | `/agent/guardrails/summary` | Bearer JWT | optional `?session_id=`; with `session_id` returns that session's counters; **omitting `session_id` yields process-wide counters** across all sessions in the worker |
| `GET` | `/agent/memory` | Bearer JWT (caller-scoped) | optional `?location=` / `?category=` — approved memory entries for the **caller’s** Redis key prefix only |
| `GET` | `/agent/memory/audit` | Admin JWT | recent proposal audit events (scrubbed originating messages; retained on reject); non-admin → **403** |

Docs/OpenAPI only when `EXPOSE_DOCS=1`. **Parked:** Redis `EXPIRE` / `LTRIM` hygiene on memory + audit keys (user-prefix scoping shipped; TTL/trim stayed out).

Trace shape: `nodes[]` records attempt order (including failed tool calls and guardrail blocks with `failure_type` in `{structural, content, security}`). `final.sources_ran` lists **contributing** sources only (`ticket_lookup` only if `tool_result.ok`; `retrieve_context` only if RAG context contributed). Also `final.route` and optional `matched_by`.

Empty question and no-context RAG paths do not force generation. No-context refusal copy:

`I don't have information about that in the official Brasaland manuals.`

Ticket tool failure / unknown ticket fallback:

`I couldn't confirm that ticket's status right now.`

Personal-use redirect (CONTEXT-guardrails):

`I'm here to help with Brasaland's procedures and recipes. Do you have a question about your shift or preparation?`

Guardrail injection tests: `tests/pipelines/test_agent_guardrails.py` (CONTEXT §4 cases; fail the build on obedience).
## Env

Copy the repo-root `.env.example` → `.env` (never commit secrets). Required for live answers:

- `QDRANT_URL`; generation failover `GEN_1_*` / `GEN_2_*` / `GEN_3_*` (`BASE_URL`, `API_KEY`, `MODEL` — at least one non-empty `GEN_i_API_KEY`); optional `GENERATION_TIMEOUT_SECONDS` (default `30`)
- `EMBED_MODEL_ID` (default `BAAI/bge-small-en-v1.5`)
- `KNOWLEDGE_CORPUS_PATH` (optional; default repo `docs/company-knowledge-base`)
- `JWT_PUBLIC_KEY`, `JWT_ALGORITHM`
- `EXPOSE_DOCS` — when `1`/`true`, serves `/docs` and OpenAPI; default off
- `RATE_LIMIT_AGENT_QUERY` / `RATE_LIMIT_KNOWLEDGE_QUERY` — SlowAPI overrides (defaults `10/minute` / `20/minute`)
- `RATE_LIMIT_PUBLIC_KNOWLEDGE_QUERY` — public guest route (default `5/minute`)
- `PUBLIC_KNOWLEDGE_ENABLED` — when `1`/`true`, enables `POST /public/knowledge/query`; otherwise **503**
- `PUBLIC_KNOWLEDGE_CORPUS_PATH` — optional; default repo `docs/public-knowledge-base` for public indexing
- `WEBSITE_KNOWLEDGE_SVC_CLAIM` — expected `svc` claim on website service tokens (default `website-knowledge`)
- `PUBLIC_DAILY_CAPS_ENABLED` — deferred Redis daily caps (`public_usage.py` stub when off)
- Optional `GEN_PUBLIC_1_*` … tiers for isolated public generation (falls back to `GEN_*` when unset)
- `REDIS_URL` — approved agent memory + audit (Compose redis:6379; in-memory fallback when unset for offline tests); keys are user-prefixed
- `MCP_SERVER_URL` — company-tools MCP Streamable HTTP URL (native `http://localhost:8016/mcp`; Compose `http://company-tools-mcp:8016/mcp`). The inbound user Bearer from `/agent/query` is forwarded to MCP; no service-login secret.

## Index the corpus

```powershell
uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py
```

Compose mounts manuals read-only at `/app/docs/company-knowledge-base` and sets `KNOWLEDGE_CORPUS_PATH` accordingly.

Public guest corpus (website chat):

```powershell
uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py --profile public
```

Compose mounts `docs/public-knowledge-base` at `/app/docs/public-knowledge-base` when using the public route.

### Local guest-chat demo

1. Provision auth user for `WEBSITE_KNOWLEDGE_SERVICE_USER_EMAIL` (non-admin, all 14 locations).
2. Set `WEBSITE_KNOWLEDGE_CLIENT_ID/SECRET` in auth and website server env.
3. Index public corpus (`--profile public`).
4. Set `PUBLIC_KNOWLEDGE_ENABLED=true` and `NEXT_PUBLIC_PUBLIC_CHAT_ENABLED=true`.
5. Open website on port 3002; widget calls same-origin `POST /api/chat` (BFF acquires service token).
6. Leave `TURNSTILE_ENABLED=false` for local demo.

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

## Live ticket-tool smoke (MCP + incident-manager — not CI)

1. Ensure `company-tools-mcp` (:8016) and incident-manager are up; set `MCP_SERVER_URL=http://localhost:8016/mcp` (or use Compose).
2. `POST /agent/query` with a Bearer JWT and a tool-only question using a real numeric `id` or alphanumeric `source_incident_id` (e.g. `MANUAL-98`).
3. Confirm live status fields in the answer (dual resolution is on the MCP server).
4. `GET /agent/trace/{run_id}` — `nodes[]` shows attempt order; `sources_ran` lists only contributing sources; answer fields match the API; Bearer never appears in the trace.
5. Stop the MCP server or point `MCP_SERVER_URL` at a closed port — confirm the fallback sentence; `sources_ran` omits `ticket_lookup`.
