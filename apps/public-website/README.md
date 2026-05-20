# @brasaland/public-website

Brasaland's customer-facing marketing site.

## Overview

This workspace is the public marketing site for Brasaland, a grilled-food restaurant chain with 14 locations across Colombia and the United States. It presents the brand, communicates the restaurant's story, and provides a Brasa Points loyalty program registration form for prospective members. The site is built with vanilla HTML5, Tailwind CSS via CDN, and vanilla JavaScript — no build step required.

## Status

🚧 In development

## Tech Stack

- HTML5 semantic markup
- Tailwind CSS via CDN
- Vanilla JavaScript
- Schema.org structured data

## Scripts

| Script   | Command                               | Description                              |
| -------- | ------------------------------------- | ---------------------------------------- |
| `dev`    | `http-server . -p 3000 -a 0.0.0.0 -c-1` | Serve the site locally on port 3000   |
| `format` | `prettier --write .`                  | Format all source files with Prettier    |

## Project Structure

```
apps/public-website/
├── index.html        # Main marketing page
├── application.html  # Brasa Points loyalty program registration
├── validation.js     # Client-side form validation
├── assets/           # Favicon and static images
├── styles/           # Any supplemental CSS (non-Tailwind)
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
- No inline event handlers — all JavaScript is attached via `addEventListener` in `validation.js`
