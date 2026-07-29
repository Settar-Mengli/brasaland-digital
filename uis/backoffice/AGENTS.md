<!-- BEGIN:backoffice-agent-rules -->
# Brasaland Backoffice — Agent Rules

This is Next.js 16.2.6 with React 19 and Tailwind v4.

**Dashboard and Locations** (`app/page.tsx`, `app/locations/page.tsx`): business logic is in `@brasaland/operations-toolkit` — never copy or reimplement it here. Data comes from the M2 fixture dataset. No API calls. Server Components only.

**Inventory** (`app/inventory/*`, `app/login`, `lib/inventory.ts`, `lib/auth.ts`): uses the **live** `/inventory` API from `services/inventory` via same-origin Next.js rewrites. JWT auth via `services/auth`. Protected pages wrap `InventoryAuthGuard`. All inventory `fetch` calls must go through `lib/inventory.ts` — never from components directly.

**Reporting** (`app/reporting/page.tsx`, `lib/reporting.ts`, `lib/reporting-types.ts`): uses the **live** reporting API from `services/reporting` via same-origin Next.js rewrites (`/api/reporting/*`). All reporting `fetch` calls must go through `lib/reporting.ts` — never from components directly.

**Knowledge** (`app/knowledge/page.tsx`, `lib/rag.ts`, `lib/rag-types.ts`): uses the **live** knowledge API from `services/knowledge` via same-origin rewrites (`/api/knowledge/*`). JWT required (metered LLM). Wrap with `InventoryAuthGuard`. All knowledge `fetch` calls go through `lib/rag.ts` — never from components directly.
<!-- END:backoffice-agent-rules -->