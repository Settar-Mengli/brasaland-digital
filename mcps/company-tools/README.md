# Company Tools MCP Server

OAuth-protected MCP server exposing Brasaland **incident** and **read-only inventory** tools. Lives under top-level `mcps/` (not `services/`).

## Transport

**Streamable HTTP** on port **8016**, path `/mcp`.

stdio is not used: MCP Playground validation requires a public Codespaces forwarded URL, and Bearer auth needs an HTTP transport. Compose: `http://company-tools-mcp:8016/mcp`. Native: `http://localhost:8016/mcp`.

## Auth (mcpauth — not FastMCP built-in auth)

1. RS256 verify via `brasaland_auth_verify` + `JWT_PUBLIC_KEY`
2. Reject tokens where JWT claim `type` is present (refresh/reset)
3. **Scopes are injected at this resource server** (not minted by `services/auth`):

| Rule | Scopes |
| --- | --- |
| Any valid access token | `tickets:read`, `inventory:read` |
| `user_id` in `MCP_TICKETS_WRITE_ALLOWLIST` | also `tickets:write` |
| Anyone | **never** `inventory:write` (not grantable) |

**Limitation:** scopes live on the MCP resource server, not in the JWT.

Distinct error codes: `AUTH_REQUIRED`, `AUTH_INVALID`, `AUTHZ_SCOPE_DENIED`, `VALIDATION_ERROR`, `NOT_FOUND`, `UPSTREAM_ERROR`, `INVENTORY_WRITE_FORBIDDEN`.

Protected Resource Metadata: `GET /.well-known/oauth-protected-resource`.

## Tools

| Tool | Scope | Notes |
| --- | --- | --- |
| `check_ticket_status` | `tickets:read` | Dual id / `source_incident_id` resolution |
| `create_ticket` | `tickets:write` | All CONTEXT `REQUIRED_FIELDS` required |
| `update_ticket_status` | `tickets:write` | `PATCH /api/incidents/{id}/status` only |
| `check_stock` | `inventory:read` | Returns `current_stock` at required `location_id` (1–14) by `ingredient_id` or `sku` |
| `create_ingredient` | `inventory:read` | Always `INVENTORY_WRITE_FORBIDDEN` |
| `record_inbound` | `inventory:read` | Always `INVENTORY_WRITE_FORBIDDEN` |
| `record_outbound` | `inventory:read` | Always `INVENTORY_WRITE_FORBIDDEN` |

## Run

```powershell
cd mcps/company-tools
uv sync
uv run company-tools-mcp
```

Or via Compose (`company-tools-mcp` service). Env: see `.env.example` and root `.env.example`.

## Tests

```powershell
cd mcps/company-tools
uv run pytest
```

## MCP Playground (Codespaces)

1. Forward port **8016** publicly.
2. Open MCP Playground against the **public forwarded URL** (not localhost), path `/mcp`.
3. Obtain a Bearer from `POST /auth/login` on the auth service; paste as Authorization.
4. Call `check_ticket_status` / `check_stock`.
5. Call `create_ingredient` (or inbound/outbound) and confirm tool result `INVENTORY_WRITE_FORBIDDEN`.
6. Confirm a non-allowlisted user gets `AUTHZ_SCOPE_DENIED` on `create_ticket`.

## Agent consumer

The knowledge support agent forwards the inbound `/agent/query` Bearer via LangGraph `config["configurable"]["access_token"]` (never checkpointed AgentState) and calls only `check_ticket_status` through this server. Create/update tools are for Playground / external agents in this release.
