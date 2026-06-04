# Brasaland Backend Architecture Proposal

## 1. Executive Summary

This document defines a backend architecture proposal for Brasaland that aligns with the current monorepo, existing frontend consumers, and the operational realities of a multi-city restaurant chain. It presents a domain-centered FastAPI design, a migration path from fixture-driven backoffice data to API-driven data, and the governance decisions needed to keep architecture work structured and low risk.

- This document covers architecture decisions, domain module boundaries, API route design, FastAPI conventions, migration sequencing, and risk management.
- This document covers planning guidance for future implementation, including execution checklist items and validation gates.
- This document does not include application code.
- This document does not include deployment execution.
- This document does not include database execution or migration execution.

## 2. Brasaland Business Context and Architecture Drivers

Brasaland was founded in Medellin in 2008 and operates 14 locations across Colombia (Medellin, Bogota, Cali) and the United States (Miami, Orlando). The business runs across two countries and two currencies (COP and USD), so backend contracts and analytics need to support multi-currency operational reporting without ambiguity. The domain vocabulary already exists in the operations toolkit: menu, locations, sales, and waste. On top of those operations domains, Brasaland also runs a talent workflow in the tracker application.

Current frontend consumers are already established and must remain stable:

- `apps/talent-pipeline-tracker` consumes external API data today.
- `uis/backoffice` currently consumes fixture-backed data from `@brasaland/operations-toolkit`.
- `uis/website` and `apps/public-website` are public-facing properties that should not be disrupted by backend architecture rollout.

Architecture drivers for this proposal:

- Preserve business continuity for live properties while backend capability is introduced.
- Keep domain language consistent across operations and talent.
- Support clean evolution from fixture-driven analytics to service-backed analytics.
- Avoid unnecessary operational overhead at current company scale.

## 3. Recommended Architecture Pattern

The recommended pattern is a domain-modular FastAPI monolith.

Why this pattern fits Brasaland now:

- It provides strong domain separation inside one deployable unit, which matches current team and repo scale.
- It keeps routing, schemas, and services clear by business domain while minimizing infrastructure complexity.
- It supports incremental migration from existing frontends without forcing immediate service decomposition.

Alternative considered: microservices

- Rejected for this stage because operational overhead would be disproportionate: more deployments, more service-to-service contracts, and higher observability and release complexity.

Alternative considered: flat CRUD API

- Rejected because it weakens domain clarity and encourages endpoint sprawl without business ownership boundaries.

Decision summary:

- A domain-modular monolith gives Brasaland the right balance of delivery speed, maintainability, and future extensibility.

## 4. Domain and Module Responsibility Model

The proposed backend is organized by domain modules with one cross-cutting analytics module.

| Module | Core Entities | Responsibility | Consumer Focus |
|---|---|---|---|
| menu | `MenuItem` | Manage menu catalog, category/status views, and item-level retrieval | backoffice |
| locations | `Location` | Manage location inventory, status, capacity, and country-based views | backoffice |
| sales | `SaleTransaction` | Record and query sales transactions by location, date, and payment method | backoffice, analytics |
| waste | `WasteRecord` | Record and query waste events and costs by reason and location | backoffice, analytics |
| talent | Candidate and Note entities used by tracker | Candidate lifecycle, notes, and state transitions for hiring workflow | talent tracker |
| analytics (cross-cutting) | Aggregates from menu, locations, sales, waste | KPI and derived metrics endpoints that compose across raw domains | backoffice leadership views |

Why analytics is separated from raw CRUD:

- Raw CRUD modules own canonical records and validation at entity level.
- Analytics endpoints compose data across multiple domains and represent derived read models.
- This separation prevents CRUD concerns from being overloaded with reporting logic and keeps KPI evolution isolated.

## 5. FastAPI Project Conventions and Sources

This proposal follows standard FastAPI conventions and explicitly references the source guidance below:

- Bigger Applications - Multiple Files: `https://fastapi.tiangolo.com/tutorial/bigger-applications/`
- APIRouter: `https://fastapi.tiangolo.com/reference/apirouter/`
- CORS (Cross-Origin Resource Sharing): `https://fastapi.tiangolo.com/tutorial/cors/`
- Settings and Environment Variables: `https://fastapi.tiangolo.com/advanced/settings/`
- Metadata and Docs URLs: `https://fastapi.tiangolo.com/tutorial/metadata/`

Proposed future API workspace structure:

```text
apps/operations-api/
  app/
    main.py
    core/          (config, cors)
    routers/       (one file per domain)
    schemas/       (Pydantic models)
    services/      (business logic)
    repositories/  (data access)
  tests/
  pyproject.toml
  .env.example
```

Conventions to apply:

- `main.py` wires app metadata, docs URLs, middleware, and router registration.
- `routers/` handles transport concerns: path operations, request/response mapping, status codes.
- `services/` handles domain logic and orchestration independent of HTTP transport.
- `repositories/` handles persistence access and query details.
- `schemas/` defines Pydantic models and response contracts.
- `core/` centralizes settings loading and CORS policy.

## 6. Router and Endpoint Design by Domain

### system_router purpose

The system router exposes operational health signals needed by local development, CI checks, and deployment health probes.

### menu_router purpose

The menu router provides menu catalog access for operational dashboards, with filtering and item-level lookups tied to the `MenuItem` domain.

### locations_router purpose

The locations router provides location inventory and detail access tied to the `Location` domain, including country/status segmentation.

### sales_router purpose

The sales router owns creation and querying of `SaleTransaction` records used by operational reporting and downstream analytics.

### waste_router purpose

The waste router owns creation and querying of `WasteRecord` entries so waste cost and quality signals remain first-class operational data.

### analytics_router purpose

The analytics router provides derived KPI views that compose data across menu, locations, sales, and waste domains.

### talent_records_router purpose

The talent records router covers candidate list/create/read/update workflows already used by the talent tracker.

### talent_notes_router purpose

The talent notes router owns nested note resources for candidate collaboration workflows.

### admin_router purpose

The admin router provides controlled operational utilities for non-production seed workflows used during migration and parity validation.

Full endpoint table:

| Router | Method | Path | Description |
|---|---|---|---|
| system_router | GET | /health | Service liveness check |
| system_router | GET | /ready | Service readiness check |
| menu_router | GET | /api/v1/menu-items | List menu items with optional filters |
| menu_router | GET | /api/v1/menu-items/{item_id} | Get menu item by id |
| locations_router | GET | /api/v1/locations | List locations with optional filters |
| locations_router | GET | /api/v1/locations/{location_id} | Get location by id |
| sales_router | GET | /api/v1/sales | List sales transactions with filters |
| sales_router | POST | /api/v1/sales | Create sales transaction |
| waste_router | GET | /api/v1/waste-records | List waste records with filters |
| waste_router | POST | /api/v1/waste-records | Create waste record |
| analytics_router | GET | /api/v1/analytics/country-comparison | Compare KPIs by country |
| analytics_router | GET | /api/v1/analytics/location-rankings | Rank locations by performance score |
| analytics_router | GET | /api/v1/analytics/top-selling-items | Return top-selling menu items |
| analytics_router | GET | /api/v1/analytics/payment-breakdown | Return payment-method sales split |
| analytics_router | GET | /api/v1/analytics/average-ticket | Return average ticket metrics |
| talent_records_router | GET | /api/v1/talent/records | List candidates with filters and pagination |
| talent_records_router | POST | /api/v1/talent/records | Create candidate record |
| talent_records_router | GET | /api/v1/talent/records/{record_id} | Get candidate detail |
| talent_records_router | PATCH | /api/v1/talent/records/{record_id} | Update candidate status/stage |
| talent_notes_router | GET | /api/v1/talent/records/{record_id}/notes | List notes for candidate |
| talent_notes_router | POST | /api/v1/talent/records/{record_id}/notes | Create candidate note |
| talent_notes_router | DELETE | /api/v1/talent/records/{record_id}/notes/{note_id} | Delete candidate note |
| admin_router | POST | /api/v1/admin/seed-fixtures | Seed non-production fixture dataset |

## 7. Frontend and Backend Separation Strategy

### CORS strategy

Use an explicit allowlist only. Do not use wildcard origin matching.

Allowlist targets for current topology:

- `http://localhost:3001` (talent tracker local)
- `http://localhost:3002` (website local)
- `http://localhost:3003` (backoffice local)
- `https://brasaland-website.vercel.app`
- `https://brasaland-backoffice.vercel.app`
- `https://brasaland-talent-pipeline.vercel.app`

### API client pattern

Use the existing client model in `apps/talent-pipeline-tracker/lib/api/client.ts` as the baseline pattern for future workspace API clients:

- Typed fetch wrapper for consistent request handling.
- `ApiError` discriminated error handling for business/schema/network conditions.
- Shared response parsing and non-2xx behavior in one boundary.

### Versioning and contract style

- All business endpoints are versioned with `/api/v1/`.
- API response and request payload contracts use `snake_case` JSON field naming.
- Frontend adapters can map wire contracts to local view models as needed without changing API semantics.

## 8. Migration Path: Backoffice Fixtures to FastAPI

Migration method: strangler pattern with parity gates.

1. Add API client boundary in backoffice (`lib/api/`) and keep fixture imports as fallback.
2. Migrate locations and sales endpoints first because they carry lower metric-composition risk.
3. Migrate menu and analytics endpoints after baseline data paths stabilize.
4. Migrate waste-linked rankings last due to higher KPI sensitivity.
5. Remove `@brasaland/operations-toolkit` fixture imports only after parity sign-off; keep the library for shared types.

Parity gates required before each fixture removal:

- Metric-by-metric comparison between fixture-driven outputs and API-driven outputs.
- Comparison scope includes country comparison, location rankings, top sellers, payment breakdown, and average ticket.
- Gate fails if any KPI tolerance threshold is exceeded.

## 9. Environment Variable Matrix

Important continuity rule: the current talent tracker value for `NEXT_PUBLIC_API_URL` is `https://playground.4geeks.com/tracker/api/v1` and must remain unchanged until explicit cutover.

| Workspace | Variable | Current or Example Value | Purpose |
|---|---|---|---|
| `apps/public-website` | None | n/a | Static site, no backend runtime dependency |
| `apps/operations-toolkit` | None | n/a | Library workspace, no runtime env required |
| `apps/talent-pipeline-tracker` | `NEXT_PUBLIC_API_URL` | `https://playground.4geeks.com/tracker/api/v1` | Current external API base URL (do not break) |
| `apps/talent-pipeline-tracker` | `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1/talent` | Planned local value after explicit migration cutover |
| `uis/website` | None | n/a | No backend API required in this proposal scope |
| `uis/backoffice` | `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Planned base URL for operations API integration |
| `apps/operations-api` | `API_PORT` | `8000` | FastAPI service port |
| `apps/operations-api` | `CORS_ALLOW_ORIGINS` | `http://localhost:3001,http://localhost:3002,http://localhost:3003,https://brasaland-website.vercel.app,https://brasaland-backoffice.vercel.app,https://brasaland-talent-pipeline.vercel.app` | Explicit CORS allowlist |
| `apps/operations-api` | `DATABASE_URL` | `postgresql+psycopg://user:pass@host:5432/brasaland` | Persistence connection string |
| `apps/operations-api` | `ENVIRONMENT` | `development` or `production` | Runtime profile selection |

## 10. ADR Appendix

### ADR-001: Domain-modular FastAPI monolith

- Decision: Adopt a domain-modular FastAPI monolith as the backend baseline.
- Context: Brasaland has multiple frontend consumers in one monorepo and needs low-friction delivery with clear domain boundaries.
- Rationale: This pattern balances maintainability and speed while avoiding early distributed-system overhead.
- Consequences: Operational complexity remains low now; future service extraction remains possible if scale demands it.

### ADR-002: Snake_case versioned API contracts

- Decision: Use `/api/v1/` endpoints and `snake_case` JSON contracts.
- Context: Current monorepo constraints already expect snake_case API contracts and typed client boundaries.
- Rationale: Versioned, consistent wire contracts improve integration safety across frontends.
- Consequences: Adapters may be needed where UI models differ from wire names.

### ADR-003: Strangler migration for backoffice

- Decision: Migrate backoffice from fixture imports to API data gradually with fallback and parity gates.
- Context: Backoffice currently depends on fixture-backed toolkit flows and cannot tolerate KPI regressions.
- Rationale: Controlled replacement lowers migration risk while preserving user-facing behavior.
- Consequences: Temporary hybrid data flow exists during transition; parity checkpoints become mandatory release gates.

## 11. OpenAPI and Documentation Strategy

FastAPI auto-generates interactive documentation endpoints:

- `/docs` (Swagger UI)
- `/redoc` (ReDoc)

These docs provide a shared contract surface between backend and Next.js frontends. They reduce ambiguity during integration by exposing request schemas, response schemas, parameters, and status codes in one place.

For documentation quality to remain useful, each route must include:

- Clear path operation summary and description.
- Accurate request and response models.
- Explicit status code behavior for success and error responses.

## 12. Risks and Points of Attention

### Risk 1

- Risk: KPI parity drift during fixture-to-API migration.
- Mitigation: Enforce parity gates with metric-by-metric comparisons before each fixture removal.
- Early Warning Signal: Country totals or ranking order diverges between fixture and API runs.

### Risk 2

- Risk: CORS and environment misconfiguration across five workspaces and Vercel deployments.
- Mitigation: Keep explicit origin allowlists and environment matrix versioned with the proposal.
- Early Warning Signal: Browser preflight failures or runtime API base URL errors in any frontend.

### Risk 3

- Risk: Domain data mismatch because fixtures include New York while the real footprint includes Orlando.
- Mitigation: Define and validate a canonical location reference set before production data ingestion.
- Early Warning Signal: Reports or dashboards show city entries outside approved operational footprint.

## 13. Execution Checklist

1. Scaffold `apps/operations-api/` with the documented folder structure.
2. Implement `system_router` endpoints (`/health`, `/ready`) first for service observability.
3. Add CORS middleware with the explicit allowlist from this proposal.
4. Implement `locations_router` and `sales_router` endpoints before analytics endpoints.
5. Introduce `uis/backoffice/lib/api/` client boundary while retaining fixture fallback paths.
6. Execute parity checks for locations and sales metrics, then proceed to menu and analytics.
7. Implement waste-linked ranking endpoints and run final parity verification.
8. Remove fixture imports in backoffice only after parity sign-off.
9. Keep `@brasaland/operations-toolkit` as shared type and logic reference during transition.
10. Review docs quality in `/docs` and `/redoc` to confirm route metadata and schemas are complete.