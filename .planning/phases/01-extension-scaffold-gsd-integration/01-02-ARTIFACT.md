---
phase: 01-extension-scaffold-gsd-integration
plan: 02
source: .planning/phases/01-extension-scaffold-gsd-integration/01-02-SUMMARY.md
generated: 2026-02-25T00:00:00Z
---

# Artifact: Phase 01 Plan 02 - patch-execute-plan.py

**Phase:** 01-extension-scaffold-gsd-integration
**Plan:** 02
**Generated:** 2026-02-25T00:00:00Z

## Files Changed

| Path | Action | Purpose |
|------|--------|---------|
| scripts/patch-execute-plan.py | created | Python 3 patcher script that inserts `review_team_gate` step into execute-plan.md |

## Behavior Implemented

- `scripts/patch-execute-plan.py` inserts a `review_team_gate` step immediately before the `<step name="offer_next">` anchor in execute-plan.md
- Insertion ordering in patched file: update_codebase_map (line 397) → review_team_gate (line 412) → offer_next (line 434)
- Script checks for `name="review_team_gate"` in file content before any write; if found, prints [SKIP] and exits 0 without modifying the file
- On second run with patch already applied: prints [SKIP], occurrence count remains at 1, no duplication occurs
- `review_team_gate` step contains three-branch logic: `REVIEW_TEAM_ENABLED != true` (silent no-op), TEAM.md missing (log and continue), TEAM.md present (load workflow)
- `review_team_gate` step reads CONFIG_CONTENT variable from scope (set by init_context step) via `jq -r '.workflow.review_team // false'`

## Stack Changes

| Dependency | Version | Purpose |
|------------|---------|---------|
| python3 | (version not specified) | Runtime for patch-execute-plan.py |

## API Contracts

None

## Configuration Changes

| Config | Value | Location |
|--------|-------|----------|
| None | | |

## Key Decisions

- Anchor string `<step name="offer_next">` selected as insertion point
- Idempotency guard uses content check for `name="review_team_gate"` rather than line numbers
- `review_team_gate` step reads CONFIG_CONTENT variable already in scope from init_context — no additional file reads performed by the gate step
- Three branches implemented: `REVIEW_TEAM_ENABLED != true` → silent no-op; TEAM.md missing → log and continue; TEAM.md present → load workflow
- Python str.replace() pattern used for inserting XML step blocks
- Idempotency check executes before any file mutation

## Test Coverage

- Idempotency verified: second run of patch script prints [SKIP] and does not modify the file

## Error Handling

- If `name="review_team_gate"` is already present in file content: script prints [SKIP] and exits 0 without writing
