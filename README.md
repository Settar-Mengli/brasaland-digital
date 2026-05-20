# brasaland-digital

The digital platform for Brasaland — a 14-location grilled-food restaurant chain across Colombia and the U.S.

## Overview

Brasaland Digital is a TypeScript monorepo containing all customer-facing and internal software for the Brasaland brand. It brings together the company's public marketing site, an internal operations utility library, and a talent acquisition tracker under a single repository, sharing tooling and deployment infrastructure via Vercel.

## Repository Structure

```
brasaland-digital/
├── apps/
│   ├── public-website/          # Static marketing site (HTML + Tailwind + vanilla JS)
│   ├── operations-toolkit/      # Pure TypeScript utility library for internal operations
│   └── talent-pipeline-tracker/ # Next.js 14 frontend for tracking talent acquisition
└── docs/                        # Shared documentation and architecture notes
```

## Tech Stack

- **Language:** TypeScript, HTML, vanilla JavaScript
- **Frameworks:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Tooling:** npm workspaces, Prettier, EditorConfig
- **Deployment:** Vercel (separate projects per app)

## Apps

### Public Website

🚧 Planned

A static marketing site built with HTML, Tailwind CSS, and vanilla JavaScript. Serves as the primary customer-facing touchpoint for the Brasaland brand — communicating the restaurant's identity, locations, and menu across the Colombia and U.S. markets. Designed for fast load times with no JavaScript framework dependency.

_See `apps/public-website/README.md` for details._

### Operations Toolkit

🚧 Planned

A pure TypeScript utility library containing shared logic and helpers used across Brasaland's internal tooling. Designed to be consumed as a workspace package by other apps in this monorepo. Contains no runtime framework dependencies.

_See `apps/operations-toolkit/README.md` for details._

### Talent Pipeline Tracker

🚧 Planned

An internal Next.js 14 (App Router) frontend for managing Brasaland's talent acquisition pipeline. Built with TypeScript and Tailwind CSS, and deployed as a standalone Vercel project. Provides structured visibility into candidate status across all locations.

_See `apps/talent-pipeline-tracker/README.md` for details._

## Getting Started

```bash
# Clone the repository
git clone https://github.com/Settar-Mengli/brasaland-digital.git
cd brasaland-digital

# Install dependencies for all workspaces
npm install
```

Each app has its own `README.md` with setup instructions, environment variable requirements, and local development steps.
