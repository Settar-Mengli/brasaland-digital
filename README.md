# brasaland-digital

The digital platform for Brasaland, a 14-location grilled-food restaurant chain across Colombia and the United States.

Brasaland Digital is a TypeScript monorepo containing three independent workspaces: a public marketing site, an operations utility library, and an internal talent pipeline tracker. Each workspace is a separately deployable unit, structured to reflect a real product-team architecture — shared tooling and conventions without shared runtime dependencies.

## Live demos

- Marketing site (M1) — [brasaland-public-website.vercel.app](https://brasaland-public-website.vercel.app)
- Talent pipeline tracker (M3) — not yet started

## Workspaces

| Workspace | Role | Stack | Status |
| --- | --- | --- | --- |
| `@brasaland/public-website` | Customer-facing marketing site and Brasa Points sign-up | HTML5, Tailwind CSS (CDN), vanilla JavaScript | Complete (pending deployment) |
| `@brasaland/operations-toolkit` | Pure TypeScript utility library for restaurant operations data | TypeScript, Vitest | Complete |
| `@brasaland/talent-pipeline-tracker` | Internal HR app for managing candidate pipelines | Next.js (App Router), React, Tailwind CSS | Not started |

## Repository structure

```
brasaland-digital/
├── apps/
│   ├── public-website/          # M1 — landing page + Brasa Points form
│   ├── operations-toolkit/      # M2 — pure TypeScript library (no UI)
│   └── talent-pipeline-tracker/ # M3 — Next.js HR app (not yet started)
├── docs/
│   └── brand-tokens.md          # Shared visual identity for M1 and M3
├── package.json                 # npm workspaces root
└── README.md
```

## Tech stack

- **Language:** TypeScript (strict mode with `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`)
- **Public website:** HTML5, Tailwind CSS via CDN, vanilla JavaScript
- **Operations toolkit:** Pure TypeScript, Vitest for testing
- **Talent tracker (planned):** Next.js (App Router), React, Tailwind CSS
- **Tooling:** npm workspaces, Prettier, EditorConfig
- **Deployment (planned):** Vercel (separate projects per app)

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
| M3 talent-pipeline-tracker | All components | Not started |

## License

All rights reserved.
