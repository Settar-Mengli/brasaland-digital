# Brasaland Website

Next.js rebuild of the Brasaland public website (customer-facing marketing site).

## Scripts

```powershell
npm run dev
```

Serves on port **3002** (`next dev -p 3002`).

```powershell
npm start
```

Production start via Next (`next start`). Uses Next's default port **3000** unless you pass `-p`.

## Guest FAQ chat (Path 2 demo)

When `NEXT_PUBLIC_PUBLIC_CHAT_ENABLED=true`, the homepage mounts an accessible guest chat widget. The browser calls same-origin `POST /api/chat`; the Route Handler acquires a service token (`WEBSITE_KNOWLEDGE_CLIENT_*` → `POST /auth/service-token`) and proxies to `POST /public/knowledge/query` on the knowledge service. Guests never receive staff JWTs or direct knowledge URLs.

Copy `uis/website/.env.example` and set server-only `AUTH_API_ORIGIN`, `PUBLIC_KNOWLEDGE_API_ORIGIN`, and website client credentials. Turnstile verification is optional (`TURNSTILE_ENABLED`); leave off for local demo.

See `services/knowledge/README.md` for indexing the public corpus and enabling `PUBLIC_KNOWLEDGE_ENABLED`.
