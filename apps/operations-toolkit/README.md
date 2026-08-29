# @brasaland/operations-toolkit

Pure TypeScript utility library for Brasaland restaurant operations data.

## Overview

This package contains the domain types and utility functions that model Brasaland's core restaurant operations — including menu items, sales records, location data, and waste tracking. It is a pure logic library with no runtime framework dependencies, and is consumed internally by other workspaces in this monorepo.

## Status

Complete

## Scripts

| Script      | Command               | Description                              |
| ----------- | --------------------- | ---------------------------------------- |
| `typecheck`  | `tsc --noEmit`        | Run the TypeScript compiler without emit |
| `format`     | `prettier --write .`  | Format all source files with Prettier    |
| `test`       | `vitest run`          | Run all tests once (CI mode)             |
| `test:watch` | `vitest`              | Run tests in interactive watch mode      |

From the monorepo root:

```bash
npm run test --workspace @brasaland/operations-toolkit
```

Expect **115** passed.

## Project Structure

```
apps/operations-toolkit/
├── src/
│   ├── types/     # Domain type definitions
│   ├── utils/     # Pure utility functions
│   └── index.ts   # Public export barrel
├── package.json
├── tsconfig.json
└── README.md
```

## Conventions

- Strict TypeScript — all compiler strict flags enabled, including `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`
- Pure functions — all utilities are stateless and side-effect-free
- No mutations — inputs are never modified; return new values
- Explicit types — no inferred `any`, no type assertions without justification
- No `any` — use `unknown` at boundaries, then narrow explicitly
