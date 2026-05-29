# Skill: prettier-check

## Objective
Run Prettier in check mode on a target workspace and report any formatting violations before committing.

## Scope
agent-requested — invoke this skill whenever you are about to commit changes to any workspace.

## Inputs
- TARGET_WORKSPACE: the workspace directory path (e.g., uis/website)

## Steps
1. Run: npx prettier --check <TARGET_WORKSPACE>/
2. If output is "All matched files use Prettier code style!" — report PASS
3. If output lists files — run: npx prettier --write <TARGET_WORKSPACE>/ and re-run check
4. Report final status: PASS or FAIL with file list

## Acceptance Criteria
- npx prettier --check exits with code 0
- No files listed as needing formatting
- This check must pass before any commit is made
