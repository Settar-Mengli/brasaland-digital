# RFP vertical slice — deploy runbook

One 24/7 host: backoffice + auth + RFP API + rfp-worker + Redis + Caddy, talking to hosted Postgres (brasaland-m5). Laptop off. Recruiter hits one TLS hostname.

This is **not** the full monorepo Compose file. Local full stack remains [`docker-compose.yml`](../../docker-compose.yml). The slice file is [`docker-compose.slice.yml`](../../docker-compose.slice.yml).

## Topology

- Caddy terminates TLS on **80/443 only** and reverse-proxies to `backoffice:3003`.
- Browser uses same-origin `/api/auth` and `/api/rfp` (no backend CORS). Next.js rewrites to Docker DNS `http://auth:8002` and `http://rfp:8017`.
- Auth/rfp/rfp-worker/redis are **not** published on `0.0.0.0`.
- Password reset is **off**. Caddy does not route `/reset-password` or `/forgot-password`. Demo login is bootstrap admin with `AUTH_ALLOW_SELF_REGISTER=false`.

```
recruiter --HTTPS--> Caddy --> backoffice (next start :3003)
                              |-- rewrite /api/auth --> auth
                              |-- rewrite /api/rfp  --> rfp -- Redis (Celery)
                                                         |-- Postgres (brasaland-m5)
                                                         |-- rfp_checkpoint (SqliteSaver)
                                                         |-- rfp_uploads (/app/data/raw)
auth --> auth_data (TinyDB)
rfp-worker --pool=solo -Q rfp  (same Redis, Postgres, checkpoint, PDFs)
```

## Volumes (do not `down -v` on a host you care about)

| Volume | Mount | What it holds |
| --- | --- | --- |
| `auth_data` | `/app/services/auth/data` | TinyDB users + refresh tokens |
| `rfp_checkpoint` | `/app/checkpoint` | LangGraph SqliteSaver (in-flight approval interrupts) |
| `rfp_uploads` | `/app/data/raw` **only** | Uploaded PDFs (never mount over all of `/app/data`) |
| `redis_data` | `/data` | Celery broker persistence |
| `caddy_data` | `/data` | TLS certificates |

`docker compose -f docker-compose.slice.yml down -v` **wipes** in-flight interrupts, PDFs, sessions, and Redis.

Named volumes created as root may not be writable by uid 1000. One-time on a fresh host (operator):

```powershell
docker compose -f docker-compose.slice.yml run --rm --user 0 --no-deps auth chown -R 1000:1000 /app/services/auth/data
docker compose -f docker-compose.slice.yml run --rm --user 0 --no-deps rfp chown -R 1000:1000 /app/checkpoint /app/data/raw
```

The generic [`services/Dockerfile`](../../services/Dockerfile) is also used by out-of-slice services in the full Compose file; existing local named volumes may need the same `chown`.

## Single-replica / SqliteSaver

**One** `rfp` replica and **one** `rfp-worker` replica on the same host. Worker is `--pool=solo` (not Celery prefork). Do not scale either service. Checkpoint and PDFs are shared Docker volumes on this host; they do not port to replica-only platforms.

## Health and Free-tier keepalive

- `GET /livez` — process up (no dependencies). Not access-logged.
- `GET /readyz` — auth: TinyDB writable; rfp: `SELECT 1` + Redis `PING` + checkpoint parent writable (2s bound).
- Compose healthchecks hit both probes about every 30s. **rfp `/readyz` `SELECT 1` is what keeps Supabase Free from pausing** (~7 days with no queries). If brasaland-m5 is already Pro, keep the probe anyway.

Access logs (auth + rfp) are one JSON line per request (`brasaland.access`): `method`, `path`, `status`, `duration_ms`, `request_id`. Uvicorn's default access log is disabled. No query strings, bodies, tokens, or secrets.

## Caddy / TLS

[`deploy/Caddyfile`](../../deploy/Caddyfile): `{$SLICE_HOST}` → `backoffice:3003`. Set `SLICE_HOST` in `.env` to the public hostname. Local smoke can use `localhost` (HTTP :80).

## Operator sequence (Phase H — not agent-run)

1. **Provision** a single VM (plan: Hetzner CX22, Ubuntu 24.04, Docker Engine + Compose).
2. **Tier check** — brasaland-m5 Free vs Pro. If Pro, skip keepalive/pg_dump anxiety; still keep `/readyz`. If Free, rfp healthcheck is the keepalive; install a daily `pg_dump` via the `:6543` pooler to a directory Compose does not wipe.
3. **RLS enable** — operator-run DDL. Enumerate all public tables (`pg_tables.rowsecurity`), confirm `DATABASE_URL` role `rolbypassrls` (script assumes table-owner `postgres`, zero policies, **no FORCE**). Run [`scripts/enable_rls.py --dry-run`](../../scripts/enable_rls.py) then real. **Do not advertise the URL until RLS shows ENABLED** on the full public-table list. Do not author policies in this slice.
4. **DNS** A record → VM IPv4. Set `SLICE_HOST`.
5. **Deploy** `docker compose -f docker-compose.slice.yml up -d --build`. Confirm `https://$SLICE_HOST/login`.
6. **Hosted non-mutating readiness** — `/livez` and `/readyz` 200 (docker exec; do not publish 8002/8017). Login as bootstrap admin.
7. **Laptop-off E2E** — one ticket: upload → `intake_complete` → generate response → per-department approval → CEO → final document.
8. **Advertise** only after step 7 is green **and** RLS is ENABLED.

Deployed at `<URL>` — fill after the Phase H E2E.

## Local slice up (operator smoke, not the hosted gate)

```powershell
docker compose -f docker-compose.slice.yml up --build
```

Login at `http://localhost/login`. Inside this network, `REDIS_URL` is `redis://redis:6379/0`.
