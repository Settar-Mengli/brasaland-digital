<!-- BEGIN:incident-manager-agent-rules -->
# Brasaland Incident Manager UI — Agent Rules

This is Next.js 16.2.6 with React 19 and Tailwind v4.

**API:** All incident `fetch` calls go through `lib/incidents.ts` only — never from components directly. Same-origin proxy via `next.config.ts` rewrites to `services/incident-manager`. Canonical ports: [../../docs/standards/project-context.md](../../docs/standards/project-context.md#port-assignments). Set `NEXT_PUBLIC_INCIDENTS_API_URL` in `.env.local`.

**Auth:** The incident API requires a valid Bearer JWT. This standalone UI is deprecated and intentionally has no login, guards, or `Authorization` headers, so its API calls receive HTTP 401. Do not reactivate or add authentication to this UI unless that work is explicitly scoped.

**Vocabulary:** Category codes, statuses, origins, and branches must match `services/incident-manager/CONTEXT-brasaland.md` exactly.

**Routes:** `/register`, `/incidents`, `/summary` are retained as unsupported legacy routes; see `README.md` for the deprecation status.
<!-- END:incident-manager-agent-rules -->
