# Backend Architecture Proposal — Planning Record

## 1. Objective

Produce a complete backend architecture proposal document that defines the recommended FastAPI architecture pattern, domain boundaries, endpoint design, migration sequencing, and architecture governance decisions for Brasaland.

## 2. Scope Included

- Architecture recommendation and rationale tied to Brasaland business context.
- Proposed API workspace folder structure and FastAPI conventions with explicit source references.
- Router-by-router endpoint catalog and environment variable matrix.
- Migration path from backoffice fixture data to API data with parity gates.
- ADR appendix and risk register for proposal-level decisions.

## 3. Scope Excluded

- Backend source code implementation.
- Deployment execution and infrastructure provisioning.
- Database migration execution and data backfill execution.
- Frontend refactors beyond architectural planning guidance.

## 4. Deliverables

- Primary deliverable: `docs/ARCHITECTURE_PROPOSAL.md`.
- Planning record: `memory-bank/PLANNING.md`.
- Session progress update appended in `memory-bank/progress.md`.

## 5. Decision Log

- Selected architecture pattern: domain-modular FastAPI monolith.
- Selected contract policy: versioned `/api/v1/` endpoints with `snake_case` JSON contracts.
- Selected migration method: strangler path for backoffice fixture replacement with explicit parity gates.

## 6. Dependency and Sequencing Plan

1. Finalize architecture proposal sections and route inventory.
2. Validate proposal against required rubric and safe-improvement criteria.
3. Prepare planning and progress records.
4. Run repository verification commands in required order.
5. Commit all documentation changes atomically.

## 7. Verification Plan

1. Run `npx prettier --check` on modified markdown files.
2. Skip build verification because no workspace code is changed.
3. Run `npm run test --workspace @brasaland/operations-toolkit` and confirm toolkit tests pass — Canonical toolkit tests: [../apps/operations-toolkit/README.md](../apps/operations-toolkit/README.md).
4. Run `git diff --stat` and verify only in-scope files changed.

## 8. Risks and Mitigations

- KPI parity risk during fixture-to-API migration: mitigate with gate-based metric comparisons.
- Cross-workspace configuration risk (CORS/env): mitigate with explicit allowlist policy and matrix.
- Canonical domain data mismatch risk: mitigate by reconciling location reference set before migration rollout.

## 9. Next Action

Proceed with implementation only after review approval of `docs/ARCHITECTURE_PROPOSAL.md`, then scaffold the API workspace and execute migration steps in checklist order.