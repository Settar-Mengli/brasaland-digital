<!-- BEGIN:backoffice-agent-rules -->
# Brasaland Backoffice — Agent Rules

This is Next.js 16.2.6 with React 19 and Tailwind v4.

**Dashboard and Locations** (`app/page.tsx`, `app/locations/page.tsx`): business logic is in `@brasaland/operations-toolkit` — never copy or reimplement it here. Data comes from the M2 fixture dataset. No API calls. Server Components only.

**Inventory** (`app/inventory/*`, `app/login`, `lib/inventory.ts`, `lib/auth.ts`): uses the **live** `/inventory` API from `services/inventory` via same-origin Next.js rewrites. JWT auth via `services/auth`. Protected pages wrap `InventoryAuthGuard`. All inventory `fetch` calls must go through `lib/inventory.ts` — never from components directly.
<!-- END:backoffice-agent-rules -->
