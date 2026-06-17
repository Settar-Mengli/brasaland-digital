# brasaland-digital

The digital platform for Brasaland, a 14-location grilled-food restaurant chain across Colombia and the United States.

Brasaland Digital is primarily a TypeScript monorepo, now extended with Python backend services under `services/`, containing five independent workspaces: a public marketing site, an operations utility library, an internal talent pipeline tracker, a Next.js rebuild of the public website, and an internal operations dashboard. Each workspace is a separately deployable unit, structured to reflect a real product-team architecture — shared tooling and conventions without shared runtime dependencies.

## Live demos

### M1 — Brasaland public website
**Live:** https://brasaland-public-website.vercel.app

<img src="docs/screenshots/m1-landing.png" alt="Brasaland public website landing page" width="800">

---

### M3 — Talent Pipeline Tracker
**Live:** https://brasaland-talent-pipeline.vercel.app

<img src="docs/screenshots/m3-list.png" alt="Talent Pipeline Tracker candidate list" width="800">

---

### M4 — Website (Next.js rebuild)
**Live:** [URL TBD — add after Vercel deployment]

<img src="docs/screenshots/m4-website.png" alt="Brasaland website rebuild landing page" width="800">

---

### M4 — Backoffice (Operations Dashboard)
**Live:** [URL TBD — add after Vercel deployment]

<img src="docs/screenshots/m4-backoffice.png" alt="Brasaland backoffice operations dashboard" width="800">

## Workspaces

| Workspace | Role | Stack | Status |
| --- | --- | --- | --- |
| `@brasaland/public-website` | Customer-facing marketing site and Brasa Points sign-up | HTML5, Tailwind CSS (CDN), vanilla JavaScript | Complete |
| `@brasaland/operations-toolkit` | Pure TypeScript utility library for restaurant operations data | TypeScript, Vitest | Complete |
| `@brasaland/talent-pipeline-tracker` | Internal HR app for managing candidate pipelines | Next.js (App Router), React, Tailwind CSS | Complete |
| `@brasaland/website` | Next.js rebuild of the public website | Next.js 16, React 19, Tailwind v4, TypeScript | In progress |
| `@brasaland/backoffice` | Internal operations dashboard with M2 integration | Next.js 16, React 19, Tailwind v4, TypeScript | In progress |

## Repository structure

```
brasaland-digital/
├── apps/
│   ├── public-website/          # M1 — landing page + Brasa Points form (live)
│   ├── operations-toolkit/      # M2 — pure TypeScript library (no UI)
│   └── talent-pipeline-tracker/ # M3 — Next.js HR app (live)
├── uis/
│   ├── website/                 # M4 — Next.js rebuild of public website (port 3002)
│   └── backoffice/              # M4 — Operations dashboard with M2 integration (port 3003)
├── services/
│   ├── incident-analysis/       # Python incident-analysis utility (CLI, FastAPI, web UI)
│   └── supplier-directory/      # Python supplier directory (FastAPI, TinyDB, web UI)
├── memory-bank/                 # Agent context files (projectbrief, techContext, progress)
├── .agents/                     # Agent rules and skills
├── docs/
│   ├── brand-tokens.md          # Shared visual identity — colors, typography, tokens
│   └── screenshots/             # Live demo screenshots
├── AGENTS.md                    # Root agent rules
├── package.json                 # npm workspaces root
└── README.md
```

## Tech stack

- **Language:** TypeScript (strict mode with `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`)
- **Public website (M1):** HTML5, Tailwind CSS via CDN, vanilla JavaScript
- **Operations toolkit (M2):** Pure TypeScript, Vitest for testing
- **Talent tracker (M3, live):** Next.js (App Router), React, Tailwind CSS
- **Website rebuild + Backoffice (M4):** Next.js 16 (App Router), React 19, Tailwind v4 (CSS-first), TypeScript strict
- **Tooling:** npm workspaces, Prettier, EditorConfig
- **Deployment:** Vercel (separate projects per workspace)

## Getting started

**Prerequisites:** Node.js 20+, npm 10+

```bash
npm install
```

**Run the public website locally:**

```bash
npm run dev --workspace @brasaland/public-website
```

Serves at `http://localhost:3000`.

**Run operations-toolkit tests:**

```bash
npm run test --workspace @brasaland/operations-toolkit
```

**Run the M4 website rebuild locally (port 3002):**

```bash
npm run dev --workspace @brasaland/website
```

**Run the M4 backoffice dashboard locally (port 3003):**

```bash
npm run dev --workspace @brasaland/backoffice
```

## Engineering decisions

**M2 is a standalone library, not inline code.** Business logic (filtering, ranking, financial
calculations) is isolated in `@brasaland/operations-toolkit` so it can be tested independently
of any UI framework. The backoffice imports it at runtime via npm workspace references — no code
is copied or duplicated.

**M4 uses React Server Components by default.** Every page and section component is a Server
Component unless interactivity explicitly requires `'use client'`. This keeps the client bundle
minimal and reflects how production Next.js applications are structured.

**TypeScript strictness is layered by workspace.** The backoffice adds `noUncheckedIndexedAccess`
and `exactOptionalPropertyTypes` on top of base strict mode — the same flags M2 enforces — because
it imports M2 types and must satisfy the same contracts.

**The operations toolkit ships TypeScript source, not compiled output.** It has no `dist/`
directory. Consumers resolve it through npm workspace symlinks directly to `src/index.ts`, which
works because all consuming workspaces use bundler-aware TypeScript resolution.

## Conventions

- Commits follow the Conventional Commits specification with workspace scopes (e.g., `feat(public-website): ...`)
- Linear `main` history; no long-lived branches
- Code style enforced by Prettier (`printWidth: 100`, single quotes, semi)
- TypeScript strict flags on; no `any`, no `!` assertions, no `as` casts in production code

## Project status

| Milestone | Component | Status |
| --- | --- | --- |
| M1 public-website | Landing page (header, hero, story, features, locations, Brasa Points, contact, footer) | Complete |
| M1 public-website | Brasa Points registration form (4 fieldsets, 11 fields) | Complete |
| M1 public-website | Dependent dropdowns (Country → City → Favorite Location) | Complete |
| M1 public-website | Client-side form validation | Complete |
| M1 public-website | Mobile navigation (hamburger toggle, Escape-to-close) | Complete |
| M1 public-website | SVG favicon and social meta cleanup | Complete |
| M1 public-website | Vercel deployment | Live |
| M2 operations-toolkit | Domain types | Complete |
| M2 operations-toolkit | Collection utilities | Complete |
| M2 operations-toolkit | Search utilities | Complete |
| M2 operations-toolkit | Financial transformations | Complete |
| M2 operations-toolkit | Performance scoring | Complete |
| M2 operations-toolkit | Aggregation reports and country comparison | Complete |
| M2 operations-toolkit | Entity validation layer | Complete |
| M2 operations-toolkit | Test suite (115 tests, 4 test files) | Complete |
| M3 talent-pipeline-tracker | All components | Live |
| M4 uis/website | Next.js scaffold + M1 content migration | Complete |
| M4 uis/website | All 7 sections as React Server Components | Complete |
| M4 uis/website | Brasa Points form with TypeScript validators | Complete |
| M4 uis/website | Mobile navigation (hamburger, Escape-to-close) | Complete |
| M4 uis/website | Vercel deployment | Pending |
| M4 uis/backoffice | Next.js scaffold | Complete |
| M4 uis/backoffice | M2 operations-toolkit integration | Complete |
| M4 uis/backoffice | Operations dashboard (4 sections, M2 fixture data) | Complete |
| M4 uis/backoffice | Vercel deployment | Pending |
| M4 repo | Agent infrastructure (AGENTS.md, memory-bank/, .agents/) | Complete |

## License

All rights reserved.
