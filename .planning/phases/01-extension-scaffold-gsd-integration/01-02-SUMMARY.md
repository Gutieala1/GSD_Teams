---
phase: 01-extension-scaffold-gsd-integration
plan: 02
subsystem: infra
tags: [python, patching, gsd-integration, execute-plan, review-team]

# Dependency graph
requires:
  - phase: 01-extension-scaffold-gsd-integration
    provides: "Research establishing hook point, anchor string, and step content (01-RESEARCH.md)"
provides:
  - "scripts/patch-execute-plan.py — Python patcher that inserts review_team_gate step into execute-plan.md"
  - "Idempotent patch script safe to run multiple times"
  - "review_team_gate step with three-branch logic (off/missing/present)"
affects:
  - 01-extension-scaffold-gsd-integration
  - install workflow (plan 01-04)

# Tech tracking
tech-stack:
  added: [python3]
  patterns:
    - "str.replace() with anchor string for safe cross-version file patching (INST-02)"
    - "Idempotency via content presence check before modification"

key-files:
  created:
    - scripts/patch-execute-plan.py
  modified: []

key-decisions:
  - "Anchor string '<step name=\"offer_next\">' confirmed as insertion point — stable across GSD version updates"
  - "Idempotency guard uses content check for 'name=\"review_team_gate\"' — not line numbers"
  - "review_team_gate step reads CONFIG_CONTENT variable already in scope from init_context — no re-read needed"
  - "Three branches: REVIEW_TEAM_ENABLED != true -> silent no-op | TEAM.md missing -> log + continue | TEAM.md present -> load workflow"

patterns-established:
  - "Python str.replace() pattern for inserting XML step blocks — avoids sed BSD/GNU compatibility issues"
  - "Idempotency check before any file mutation — exits 0 cleanly on re-run"

# Metrics
duration: 1min
completed: 2026-02-26
---

# Phase 1 Plan 02: patch-execute-plan.py Summary

**Python patcher that inserts review_team_gate step into execute-plan.md anchored on offer_next, with idempotency guard and three-branch CONFIG_CONTENT logic**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-26T00:26:22Z
- **Completed:** 2026-02-26T00:27:31Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `scripts/patch-execute-plan.py` — self-contained Python 3 patcher script
- Script inserts `review_team_gate` step immediately before `<step name="offer_next">` anchor
- Verified insertion ordering: update_codebase_map (397) -> review_team_gate (412) -> offer_next (434)
- Idempotency confirmed: second run prints [SKIP], count stays at 1, no duplication

## Task Commits

Each task was committed atomically:

1. **Task 1: Write scripts/patch-execute-plan.py** - `5e64165` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `scripts/patch-execute-plan.py` - Python 3 patcher: inserts review_team_gate step before offer_next in execute-plan.md

## Decisions Made
- Anchor string `<step name="offer_next">` confirmed — stable, specific, unique in execute-plan.md
- Idempotency guard checks for `name="review_team_gate"` in file content before attempting any write
- `new_step` string ends with a trailing blank line so patched file has one blank line between review_team_gate and offer_next — readable formatting
- CONFIG_CONTENT is already in scope from `init_context` step — the gate step uses it directly via `jq -r '.workflow.review_team // false'` with no additional file reads

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `scripts/patch-execute-plan.py` is ready for use by the install script (plan 01-04)
- Script satisfies all INT-03, INT-04, PIPE-02, PIPE-03, INST-02 requirements from RESEARCH.md
- No blockers for plan 01-03 (review-team.md workflow) or plan 01-04 (install.sh)

## Self-Check: PASSED

- FOUND: scripts/patch-execute-plan.py
- FOUND: 01-02-SUMMARY.md
- COMMIT FOUND: 5e64165 feat(01-02): write scripts/patch-execute-plan.py patcher

---
*Phase: 01-extension-scaffold-gsd-integration*
*Completed: 2026-02-26*
