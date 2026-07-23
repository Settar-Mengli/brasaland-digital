# Brasaland Digital — Project Brief

## Company
Brasaland is a grilled-food restaurant chain with 14 locations across Colombia and the United States, founded in Medellín in 2008. It serves Latin American cuisine crafted on the grill, operating across multiple cities in two countries.

## What We Are Building
A monorepo-based digital platform with six npm workspaces under `apps/` and `uis/`:
- apps/public-website — M1: static corporate site (HTML/CDN, deployed on Vercel)
- apps/operations-toolkit — M2: pure TypeScript business logic library (strict mode, 115 tests)
- apps/talent-pipeline-tracker — M3: Next.js 16 candidate tracking app (deployed on Vercel)
- uis/website — M4: Next.js + TypeScript rebuild of M1 (live on Vercel)
- uis/backoffice — M4: Next.js + TypeScript internal tool with M2 integration (live on Vercel)
- uis/incident-manager — Incident manager UI (Next.js, port 3004)

## Problem It Solves
Replaces disconnected manual tools with a unified, AI-ready monorepo that any agent can navigate without ambiguity.

## Non-Negotiables
- No AI attribution anywhere in the repo (no Co-Authored-By, no tool credits, no generated-by comments)
- Solo author: Settar Mengli <263843543+Settar-Mengli@users.noreply.github.com>
- TypeScript strict mode, no any, no non-null assertions
- All four live Vercel deployments must remain unbroken at all times
