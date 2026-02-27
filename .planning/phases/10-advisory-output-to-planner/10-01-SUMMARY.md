---
phase: 10-advisory-output-to-planner
plan: 01
subsystem: infra
tags: [patch-script, plan-phase, agent-studio, advisory-notes, planner-injection]

# Dependency graph
requires:
  - phase: 09-lifecycle-trigger-hooks
    provides: pre_plan_agent_gate at step 13 in plan-phase.md (Phase 9 placeholder position)
provides:
  - Gate moved to step 8 (before planner), AGENT_NOTES collected and injected into planner prompt
  - patch-plan-phase-p10.py — idempotent Phase 10 patch script
  - plan-phase.md patched with gate at step 8, planner at step 9, {AGENT_NOTES} in planning_context
  - install.sh updated to invoke patch-plan-phase-p10.py in Section 6
affects: [10-advisory-output-to-planner, plan-phase-workflow, agent-dispatcher]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Three-anchor patch strategy (remove old, insert new before, inject into template)
    - Net-zero step renumbering (add step 8 + remove step 13 = steps 14/15 unchanged)
    - AGENT_NOTES fail-open gate: defaults to empty string on any error, harmless whitespace in template

key-files:
  created:
    - D:/GSDteams/scripts/patch-plan-phase-p10.py
    - D:/GSDteams/.planning/phases/10-advisory-output-to-planner/10-01-SUMMARY.md
  modified:
    - C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md
    - D:/GSDteams/install.sh

key-decisions:
  - "Net-zero step count: adding new step 8 and removing old step 13 cancel out — steps 14 and 15 stay unchanged"
  - "Anchor A removes old gate body by slicing gate_start to step14_start, preserving step 14 heading unchanged"
  - "Cross-references updated in script: Handle Planner Return 'skip to step 13' -> 'step 14', Revision Loop ref 'step 12' -> 'step 13', Spawn Checker ref 'step 10' -> 'step 11'"
  - "AGENT_NOTES idempotency string in patch script (not pre_plan_agent_gate) — AGENT_NOTES is unique to Phase 10"
  - "Empty AGENT_NOTES renders as harmless whitespace — no conditional omission needed in planner template"

patterns-established:
  - "Pattern: Net-zero renumbering — count insertions and removals before deciding which step numbers shift"
  - "Pattern: Patch script anchors verified character-for-character against installed file before writing"

# Metrics
duration: 4min
completed: 2026-02-27
---

# Phase 10 Plan 01: Advisory Output to Planner Summary

**Gate moved from step 13 (post-planner) to step 8 (pre-planner) with {AGENT_NOTES} injection into the planner Task() prompt, enabling advisory agent notes to influence plan creation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-27T04:00:33Z
- **Completed:** 2026-02-27T04:04:50Z
- **Tasks:** 2
- **Files modified:** 3 (plan-phase.md, install.sh, patch-plan-phase-p10.py)

## Accomplishments

- Phase 9 gate position (step 13, after planner) corrected to step 8 (before planner), enabling AGENT_NOTES collection before planner spawn
- `{AGENT_NOTES}` interpolation injected into planner Task() prompt at `</planning_context>` boundary — advisory notes reach the planner when non-empty
- patch-plan-phase-p10.py written with three-anchor strategy (remove old gate, insert new gate, inject template variable), idempotent on re-run
- install.sh Section 6 wired to invoke patch-plan-phase-p10.py after patch-plan-phase.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Write patch-plan-phase-p10.py** - `327510c` (feat)
2. **Task 2: Apply patch to plan-phase.md + wire install.sh** - `3c12db5` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `D:/GSDteams/scripts/patch-plan-phase-p10.py` - Phase 10 patch script: three-anchor strategy, AGENT_NOTES idempotency, fail-open gate at step 8
- `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md` - Patched: gate at step 8, planner at step 9, {AGENT_NOTES} in planning_context, sequential steps 1-15
- `D:/GSDteams/install.sh` - Section 6: patch-plan-phase-p10.py added after patch-plan-phase.py; Section 9 message updated

## Decisions Made

- **Net-zero step count**: Adding new step 8 and removing old step 13 cancel each other out. Steps 14 (Present Final Status) and 15 (Auto-Advance Check) are unchanged. Only steps 8-13 shift.
- **Anchor A slicing, not renaming**: The script removes the old gate block by slicing `content[:gate_start] + content[step14_start:]` — keeping `## 14. Present Final Status` as-is rather than renaming it to 13.
- **AGENT_NOTES as idempotency string**: The Phase 10 patch uses `AGENT_NOTES` (not `pre_plan_agent_gate`) as the idempotency check string — `pre_plan_agent_gate` was already present from Phase 9, so a new unique string is needed.
- **Cross-references updated in script**: Handle Planner Return "skip to step 13" becomes "skip to step 14", Revision Loop continuation reference updated from step 12 to step 13, Spawn Checker cross-reference updated from step 10 to step 11.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect Anchor A logic that created duplicate step 13**
- **Found during:** Task 2 (Apply patch to plan-phase.md)
- **Issue:** Original Anchor A renamed old step 14 -> step 13 and step 15 -> step 14, but Anchor B simultaneously renumbered old step 12 -> step 13 (Revision Loop). This produced two "## 13." headings.
- **Fix:** Removed the step 14/15 renaming from Anchor A entirely. Net-zero logic: adding step 8 and removing step 13 cancel out — steps 14/15 stay as 14/15. Anchor A now just removes the old gate body by slicing content at gate_start to step14_start.
- **Files modified:** `D:/GSDteams/scripts/patch-plan-phase-p10.py`, `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md`
- **Verification:** `grep "^## [0-9]*\." plan-phase.md` shows sequential 1-15 with no duplicates
- **Committed in:** `3c12db5` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Fix was essential for correctness — duplicate step numbers would break plan-phase.md step references. No scope creep.

## Issues Encountered

- Duplicate step 13 discovered after first patch application. Root cause: Anchor A incorrectly renamed step 14 to 13 while Anchor B also renumbered step 12 to 13. Fixed inline by correcting the Anchor A logic (net-zero step count insight) and applying the fix directly to plan-phase.md.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- plan-phase.md now collects AGENT_NOTES at step 8 (before planner) and injects them into the planner prompt
- When `agent_studio` is enabled and advisory agents return notes, the planner receives them via `{AGENT_NOTES}` in the `<planning_context>` block
- When `AGENT_NOTES` is empty (gate disabled, no TEAM.md, or no advisory agents fired), the template renders harmless whitespace — no planner behavior change
- install.sh idempotent: second run shows `[SKIP]` for both Phase 9 and Phase 10 patches

---
*Phase: 10-advisory-output-to-planner*
*Completed: 2026-02-27*

## Self-Check: PASSED

- scripts/patch-plan-phase-p10.py: FOUND
- C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md: FOUND
- D:/GSDteams/install.sh: FOUND
- 10-01-SUMMARY.md: FOUND
- Commit 327510c: FOUND
- Commit 3c12db5: FOUND
- AGENT_NOTES in patch script: FOUND
- {AGENT_NOTES} in plan-phase.md: FOUND
- patch-plan-phase-p10 in install.sh: FOUND
