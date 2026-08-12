# Project context index

Thin index only. Domain narrative and token definitions live in the linked documents — do not duplicate them here.

## Brand

- [docs/brand-tokens.md](../brand-tokens.md) — colors, typography, spacing, tone

## Domain CONTEXT files

- [services/incident-manager/CONTEXT-brasaland.md](../../services/incident-manager/CONTEXT-brasaland.md)
- [services/inventory/CONTEXT-brasaland.md](../../services/inventory/CONTEXT-brasaland.md)
- [services/supplier-directory/CONTEXT-brasaland.md](../../services/supplier-directory/CONTEXT-brasaland.md)
- [services/incident-analysis/CONTEXT-brasaland.md](../../services/incident-analysis/CONTEXT-brasaland.md)
- [data/pipelines/CONTEXT-brasaland-pipeline.md](../../data/pipelines/CONTEXT-brasaland-pipeline.md)
- [data/raw/CONTEXT-brasaland-rag.md](../../data/raw/CONTEXT-brasaland-rag.md)
- [data/raw/CONTEXT-company.md](../../data/raw/CONTEXT-company.md)
- [data/raw/CONTEXT-rfp.md](../../data/raw/CONTEXT-rfp.md)

## Port assignments

Authoritative local port table for this monorepo:

| Surface | Port |
| --- | ---: |
| Auth API | 8002 |
| Supplier directory | 8001 |
| Incident analysis | 8000 |
| Incident manager API | 8011 |
| Inventory API | 8012 |
| Telemetry API | 8013 |
| Reporting API | 8014 |
| Knowledge API | 8015 |
| RFP API | 8017 |
| Company Tools MCP | 8016 |
| Public website (M1 http-server) | 3000 |
| Talent pipeline tracker | 3001 |
| Website (Next.js) | 3002 |
| Backoffice (Next.js) | 3003 |
| Incident manager UI (Next.js) | 3004 |
| Redis (Celery broker) | 6379 |
| Flower (Celery monitor) | 5555 |
| Qdrant (REST) | 6333 |
| Qdrant (gRPC) | 6334 |

Reporting API (8014) ships in `services/reporting/` (FastAPI + Celery worker + Compose); backoffice exposes /reporting. Knowledge API (8015) ships in `services/knowledge/` with Qdrant; backoffice exposes /knowledge. RFP API (8017) ships in `services/rfp/` (FastAPI + Celery worker); `POST /rfp/tickets` and `GET /rfp/tickets/{id}`; backoffice exposes /rfp. Company Tools MCP (8016) ships in `mcps/company-tools/` (Streamable HTTP + mcpauth); the support agent reaches incidents/inventory only through it.

## Live deployments

| Surface | URL |
| --- | --- |
| M1 — Public website | https://brasaland-public-website.vercel.app |
| M3 — Talent Pipeline Tracker | https://brasaland-talent-pipeline.vercel.app |
| M4 — Website (Next.js rebuild) | https://brasaland-website.vercel.app |
| M4 — Backoffice | https://brasaland-backoffice.vercel.app |
