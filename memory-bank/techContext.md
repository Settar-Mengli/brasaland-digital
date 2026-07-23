# Brasaland Digital — Technical Context

## Monorepo
- Root: brasaland-digital/
- Package manager: npm workspaces (node >=20.0.0)
- Workspaces: apps/*, uis/* (uis/* added in M4)
- Windows/OneDrive — be aware of EPERM file-lock issues on .next cache

## Workspace Inventory

Canonical workspace list: [../README.md](../README.md#workspaces). Canonical ports: [../docs/standards/project-context.md](../docs/standards/project-context.md#port-assignments). Canonical live URLs: [../docs/standards/project-context.md](../docs/standards/project-context.md#live-deployments).

## Key Technical Constraints
- TypeScript: strict mode, no any, no ! assertions, snake_case API types, import type for type-only imports
- Architecture: Server Components by default, use client only when needed, Server Actions in _actions.ts
- Accessibility: aria-labelledby on every section, scope="col" on th, role="status" for pending, role="alert" for errors
- Date formatting: Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }), module-level instantiation
- M2 import path: @brasaland/operations-toolkit resolves to apps/operations-toolkit/src/index.ts via workspace reference

## Brand Tokens
- Ember: #C24A2B | Charcoal: #1C1C1C | Cream: #F5EFE6 | Ivory: #FAFAF8
- Success: #27AE60 | Error: #E74C3C
- Display font: Playfair | Body font: Inter
- Tailwind v4 @theme block + next/font/google CSS variables

## Agent File Convention (established in M3)
- CLAUDE.md in each workspace = single line: @AGENTS.md
- AGENTS.md = actual rules, wrapped in <!-- BEGIN:<scope>-agent-rules --> sentinel
- Root AGENTS.md = repo-wide rules (this is new in M4)

## Verification Baseline (must pass on every commit)
1. npx prettier --check <workspace>/
2. npm run build --workspace <workspace>
3. Canonical toolkit tests: [../apps/operations-toolkit/README.md](../apps/operations-toolkit/README.md).
4. git diff --stat — no out-of-scope paths, no .env.local
