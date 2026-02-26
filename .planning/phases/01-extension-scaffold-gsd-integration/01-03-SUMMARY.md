---
phase: 01-extension-scaffold-gsd-integration
plan: 03
subsystem: infra
tags: [python, patch, settings, gsd-extension, idempotent]

# Dependency graph
requires:
  - phase: 01-extension-scaffold-gsd-integration
    provides: Research findings — exact anchor strings for all 4 settings.md touch points (01-RESEARCH.md Section 2)

provides:
  - scripts/patch-settings.py — idempotent Python patcher adding Review Team toggle to GSD settings.md
  - 7th question in AskUserQuestion array (header "Review Team", 11 chars, INT-02 compliant)
  - Spread-safe update_config workflow object (preserves unknown workflow keys, INT-05 compliant)
  - Spread-safe save_as_defaults workflow object (same spread pattern)
  - Updated success_criteria count (6 -> 7 settings)

affects: [01-04-install.sh, settings-workflow, review_team_gate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Idempotent text patching: per-touch-point check before replacement, SKIP/WARN/OK reporting"
    - "Spread-safe config write: ...existing_config.workflow spread preserves unknown extension keys"
    - "Two-variable spread pattern: update_config uses ...existing_config.workflow, save_as_defaults uses ...existing_workflow"

key-files:
  created:
    - scripts/patch-settings.py
  modified: []

key-decisions:
  - "Touch point 1 anchor covers full closing block (Per Milestone line + closing brackets + ])) rather than just the Per Milestone line alone, ensuring correct insertion point"
  - "Idempotency checks: tp1 checks for 'Review Team', tp2 for '...existing_config.workflow', tp3 for '...existing_workflow', tp4 for '7 settings'"
  - "Two distinct variable names: update_config uses existing_config.workflow spread, save_as_defaults uses existing_workflow spread — different variable names per GSD source"
  - "WARN on anchor not found (not ERROR) — script skips that touch point rather than crashing, allows partial application"

patterns-established:
  - "Multi-touch-point patcher: each touch point is independently idempotent with its own check/anchor/old/new variables"
  - "Script CLI convention: takes target file path as argv[1], prints [OK]/[SKIP]/[WARN] prefix per touch point"

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 1 Plan 03: patch-settings.py Summary

**Python patcher adding Review Team as 7th GSD settings toggle with spread-safe config writes at all four touch points in settings.md**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T00:26:26Z
- **Completed:** 2026-02-26T00:27:46Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `scripts/patch-settings.py` — self-contained Python 3 script for patching GSD settings.md
- All 4 touch points confirmed working against live settings.md (GSD v1.19.2): Review Team question added, update_config and save_as_defaults both spread-safe, success_criteria updated to 7
- Idempotency verified: second run prints 4 [SKIP] lines and makes no changes
- Zero WARN messages — all anchor strings matched exactly

## Task Commits

Each task was committed atomically:

1. **Task 1: Write scripts/patch-settings.py** - `fbced3f` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `scripts/patch-settings.py` - Python patcher that adds Review Team toggle to GSD settings.md via four idempotent str.replace() operations

## Decisions Made

- **Touch point 1 anchor strategy:** The anchor for TP1 covers the full closing sequence (`Per Milestone` line + `]`, `}`, `])`) rather than just the unique `Per Milestone` line. This ensures the new Review Team question is inserted before the `])` that closes the AskUserQuestion call, not just after the option line. Using the full closing block as anchor makes the replacement position unambiguous.

- **Two distinct spread variable names:** The update_config step uses `...existing_config.workflow` (referencing the full config object's workflow property) while the save_as_defaults step uses `...existing_workflow` (referencing a local variable named `existing_workflow`). These are different because they occur in different execution contexts within settings.md — this distinction was preserved exactly from the RESEARCH.md specifications.

- **WARN vs ERROR on missing anchor:** When an anchor is not found, the script prints WARN (to stderr) and skips that touch point rather than exiting with an error. This allows partial application when settings.md has evolved from the expected v1.19.2 structure, and informs the operator which touch points need manual attention.

## Deviations from Plan

None - plan executed exactly as written. All 4 anchor strings matched the live settings.md without adjustment.

## Issues Encountered

None — all anchor strings from RESEARCH.md Section 2 matched exactly against the live GSD v1.19.2 settings.md. No whitespace or quoting discrepancies found.

## User Setup Required

None - no external service configuration required. The patch script is applied by install.sh (Plan 04) against the user's GSD installation.

## Next Phase Readiness
- `scripts/patch-settings.py` is complete and ready for use by `install.sh` (Plan 04)
- Script takes settings.md path as argument: `python3 scripts/patch-settings.py <path-to-settings.md>`
- install.sh (Plan 04) will call this script as: `python3 scripts/patch-settings.py "$GSD_DIR/get-shit-done/workflows/settings.md"`
- No blockers for Plan 04

## Self-Check: PASSED

- FOUND: `scripts/patch-settings.py` (116 lines, Python 3, passes py_compile)
- FOUND: commit `fbced3f` — feat(01-03): add scripts/patch-settings.py
- FOUND: `01-03-SUMMARY.md` (this file)
- Verification: all 4 touch points applied to /tmp/test-settings.md with zero WARN messages
- Idempotency: second run produced 4 [SKIP] lines, no file modification

---
*Phase: 01-extension-scaffold-gsd-integration*
*Completed: 2026-02-26*
