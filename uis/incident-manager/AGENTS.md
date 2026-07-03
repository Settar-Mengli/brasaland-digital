<!-- BEGIN:incident-manager-agent-rules -->
# Brasaland Incident Manager UI — Agent Rules

This is Next.js 16.2.6 with React 19 and Tailwind v4.

**API:** All incident `fetch` calls go through `lib/incidents.ts` only — never from components directly. Same-origin proxy via `next.config.ts` rewrites to `services/incident-manager` on port **8011**. Set `NEXT_PUBLIC_INCIDENTS_API_URL` in `.env.local`.

**Auth:** The incident API has **no authentication**. Do not add login, guards, or `Authorization` headers unless the backend changes.

**Vocabulary:** Category codes, statuses, origins, and branches must match `services/incident-manager/CONTEXT-brasaland.md` exactly.
<!-- END:incident-manager-agent-rules -->
