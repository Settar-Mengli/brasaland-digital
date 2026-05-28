# Brasaland Digital — Project Brief

## Company
Brasaland is a Brazilian community and cultural platform operating across multiple cities. It connects the Brazilian diaspora through events, services, and a professional network.

## What We Are Building
A monorepo-based digital platform with three production workspaces and two new UI applications:
- apps/public-website — M1: static corporate site (HTML/CDN, deployed on Vercel)
- apps/operations-toolkit — M2: pure TypeScript business logic library (strict mode, 115 tests)
- apps/talent-pipeline-tracker — M3: Next.js 16 candidate tracking app (deployed on Vercel)
- uis/website — M4: Next.js + TypeScript rebuild of M1 (in progress)
- uis/backoffice — M4: Next.js + TypeScript internal tool with M2 integration (in progress)

## Problem It Solves
Replaces disconnected manual tools with a unified, AI-ready monorepo that any agent can navigate without ambiguity.

## Non-Negotiables
- No AI attribution anywhere in the repo (no Co-Authored-By, no tool credits, no generated-by comments)
- Solo author: Settar Mengli <settar.mengli@gmail.com>
- TypeScript strict mode, no any, no non-null assertions
- All three live Vercel deployments must remain unbroken at all times
