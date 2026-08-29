# @brasaland/public-website

Brasaland's customer-facing marketing site.

## Overview

This workspace is the public marketing site for Brasaland, a grilled-food restaurant chain with 14 locations across Colombia and the United States. It presents the brand, communicates the restaurant's story, and provides a Brasa Points loyalty program registration form for prospective members. The site is built with vanilla HTML5, Tailwind CSS via CDN, and vanilla JavaScript — no build step required.

## Status

Canonical live URLs: [../../docs/standards/project-context.md](../../docs/standards/project-context.md#live-deployments).

**Superseded:** This M1 workspace is legacy. Use [`uis/website`](../../uis/website/) (M4 `@brasaland/website`) as the canonical public marketing site and for the local full-stack demo (`docker compose` UI on port 3002). This deployment remains live on Vercel and is not deleted.

<img src="../../docs/screenshots/m1-landing.png" alt="Brasaland public website landing page" width="800">

## Tech Stack

- HTML5 semantic markup
- Tailwind CSS via CDN
- Vanilla JavaScript
- Schema.org structured data

## Features

- Landing page with 8 semantic sections (header, hero, story, features, locations, Brasa Points, contact, footer)
- Brasa Points registration form with 11 fields across 4 fieldsets
- Dependent dropdowns: Country → City → Favorite Location
- Client-side validation with exact M1-spec error messages
- Mobile navigation with hamburger toggle and Escape-to-close
- Schema.org Restaurant JSON-LD on the landing page

## Accessibility

- Skip-link as first body child on every page
- ARIA-labelledby on every section heading
- aria-controls + aria-expanded on the mobile nav button
- aria-describedby linking inputs to their error messages
- role="alert" + aria-live on every error slot and the success message
- Visible focus rings on every interactive element
- Semantic landmarks: header, nav, main, footer, fieldset, dl
- `hidden` attribute (not display:none) for stateful UI to keep the accessibility tree honest

## Scripts

| Script   | Command                               | Description                              |
| -------- | ------------------------------------- | ---------------------------------------- |
| `dev`    | `http-server . -p 3000 -a 0.0.0.0 -c-1` | Serve the site locally on port 3000   |
| `format` | `prettier --write .`                  | Format all source files with Prettier    |

## Project Structure

```
apps/public-website/
├── index.html         # Landing page
├── application.html   # Brasa Points sign-up form
├── validation.js      # Form validation behavior
├── nav.js             # Mobile navigation toggle
├── assets/
│   └── favicon.svg
├── package.json
└── README.md
```

## Local Development

Install dependencies from the repo root, then run the dev server:

```bash
npm install
npm run dev --workspace @brasaland/public-website
```

The site is served at `http://localhost:3000`. The `-c-1` flag disables `http-server`'s default caching so changes are reflected immediately on refresh.

## Conventions

- Semantic HTML5 — use appropriate landmark elements (`<header>`, `<main>`, `<footer>`, `<nav>`, `<section>`, `<article>`)
- Accessible — all interactive elements include ARIA attributes and are keyboard-navigable
- Responsive — mobile-first layout; Tailwind breakpoints drive all responsive behaviour
- Tailwind utility classes only — no custom CSS classes unless strictly necessary
- No inline event handlers — all JavaScript is attached via `addEventListener` in `validation.js` and `nav.js`
