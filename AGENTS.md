<!-- BEGIN:monorepo-agent-rules -->
# Brasaland Digital — Agent Rules

## Read First
Before touching any file, read these in order:
1. memory-bank/projectbrief.md
2. memory-bank/techContext.md
3. memory-bank/progress.md

## Mandatory Pre-Commit Workflow
You must complete all four steps before every commit:
1. Run npx prettier --check on every file you modified
2. Run npm run build --workspace <affected-workspace> and confirm zero errors
3. Run npm run test --workspace @brasaland/operations-toolkit and confirm 115 passing
4. Run git diff --stat and confirm no out-of-scope paths and no .env.local

## Protected Paths — Do Not Modify Without Explicit Developer Confirmation
- apps/public-website/ (live Vercel deployment — M1)
- apps/talent-pipeline-tracker/ (live Vercel deployment — M3)
- uis/website/ (live Vercel deployment — M4)
- uis/backoffice/ (live Vercel deployment — M4)
- package-lock.json (modify only when explicitly told to run npm install)
- .env.local (never touch)
- Any file not within the scope of the current task

## Attribution Rules
- No Co-Authored-By trailers in any commit
- No "Generated with" or "Created by AI" comments in any file
- No AI tool credited anywhere in code, docs, READMEs, or commit messages
- Sole author: Settar Mengli <263843543+Settar-Mengli@users.noreply.github.com>

## Standards documents

Read the matching doc before non-trivial work:

| Task type | Read |
| --- | --- |
| Agent process, commits, schema/RLS, ops scripts, PowerShell | [docs/standards/agent-workflow.md](docs/standards/agent-workflow.md) |
| TypeScript or Python style, tests, env discipline | [docs/standards/coding.md](docs/standards/coding.md) |
| Service layout, UI↔API pattern, secrets, Path A, Supabase pointer | [docs/standards/architecture.md](docs/standards/architecture.md) |
| Brand, CONTEXT files, ports, live URLs | [docs/standards/project-context.md](docs/standards/project-context.md) |

New workspaces still use the CLAUDE.md → @AGENTS.md redirect pattern.
<!-- END:monorepo-agent-rules -->
