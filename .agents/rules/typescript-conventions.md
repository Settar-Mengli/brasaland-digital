<!-- BEGIN:always-active -->
# Rule: TypeScript Conventions
Scope: always-active — applies to every file in every workspace

## Rules
1. Strict mode must be enabled in every tsconfig.json (strict: true)
2. No any type — use unknown and narrow with type guards
3. No ! non-null assertions — use explicit null checks or optional chaining
4. No loose as casts — only inside documented type guards
5. snake_case for types that map to API wire format
6. camelCase for internal application types
7. import type for all type-only imports
8. JSDoc required on every exported function and interface
9. Record<Union, string> for exhaustive label maps
10. Discriminated unions preferred over optional fields for error states

## Acceptance Criteria
- tsc --noEmit passes with zero errors
- No ESLint disable comments suppressing type errors
<!-- END:always-active -->
