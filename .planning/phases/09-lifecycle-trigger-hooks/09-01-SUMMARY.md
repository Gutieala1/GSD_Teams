---
phase: 09-lifecycle-trigger-hooks
plan: "01"
subsystem: infra
tags: [python, patch-script, plan-phase, lifecycle, agent-dispatcher, pre-plan-gate]

# Dependency graph
requires:
  - phase: 07-agent-dispatcher
    provides: agent-dispatcher.md workflow and patch script pattern
  - phase: 08-team-roster-gsd-team
    provides: enabled field and dispatcher routing infrastructure
provides:
  - "scripts/patch-plan-phase.py: idempotent Python patch script that inserts pre_plan_agent_gate into plan-phase.md"
  - "plan-phase.md: ## 13. Pre-Plan Agent Gate step wired to agent-dispatcher.md with fail-open contract"
affects: [10-advisory-agent-injection, install.sh, plan-phase.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Insert-before patch pattern: anchor on old heading, replacement includes new heading + new body + renamed old heading"
    - "Fail-open gate contract: ALWAYS fail-open prose — any error proceeds silently to next step"
    - "Idempotency via unique string check: pre_plan_agent_gate as HTML comment marker in inserted section"

key-files:
  created:
    - D:/GSDteams/scripts/patch-plan-phase.py
  modified:
    - C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md

key-decisions:
  - "Idempotency string pre_plan_agent_gate embedded as HTML comment <!-- step: pre_plan_agent_gate --> inside inserted section — heading uses hyphens/spaces which don't match the underscore identifier"
  - "Second str.replace renames ## 14. Auto-Advance Check -> ## 15. Auto-Advance Check after first replace inserts new ## 13 and renames old ## 13 -> ## 14"
  - "Arrow character (→) replaced with ASCII -> in print statements to avoid Windows cp1252 console UnicodeEncodeError"
  - "TEAM.md existence check (step 1) included before dispatcher call — matches plan spec and review_team_gate pattern"
  - "Phase 10 (ADVY-01) scope boundary enforced: gate fires and displays output but does NOT inject notes into planner Task() prompt"

patterns-established:
  - "Step renumber patch: anchor = \\n## N. Old Name\\n, replacement = new_section + ## N+1. Old Name\\n, second replace renames N+1 -> N+2 for subsequent steps"

# Metrics
duration: 2min
completed: 2026-02-27
---

# Phase 9 Plan 01: Pre-Plan Agent Gate Patch Script Summary

**Python patch script (patch-plan-phase.py) that inserts a fail-open pre_plan_agent_gate step into GSD's plan-phase.md, renaming steps 13-14 to 14-15 and wiring agent-dispatcher.md for LIFE-02**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-27T03:09:32Z
- **Completed:** 2026-02-27T03:12:05Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Created `scripts/patch-plan-phase.py` following exact pattern of `patch-execute-plan-dispatcher.py`
- Patch inserts "## 13. Pre-Plan Agent Gate" before "## 13. Present Final Status", renaming old 13 -> 14 and old 14 -> 15
- Applied patch to installed `plan-phase.md` — gate now fires with trigger=pre-plan before final status presentation
- Gate is explicitly fail-open: TEAM.md missing, dispatcher error, or config absent all log and proceed silently
- Idempotency verified: second run prints [SKIP] immediately

## Task Commits

Each task was committed atomically:

1. **Task 1: Write scripts/patch-plan-phase.py** - `2f50708` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `D:/GSDteams/scripts/patch-plan-phase.py` - Idempotent Python 3 patch script that inserts pre_plan_agent_gate into plan-phase.md
- `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md` - Gained ## 13. Pre-Plan Agent Gate step; old 13/14 renumbered to 14/15

## Decisions Made
- **Idempotency string:** `pre_plan_agent_gate` embedded as HTML comment `<!-- step: pre_plan_agent_gate -->` inside the inserted section. The heading "## 13. Pre-Plan Agent Gate" uses hyphens/spaces — the exact underscore identifier must appear somewhere in the body for idempotency check to work.
- **Second replace:** Added `## 14. Auto-Advance Check` -> `## 15. Auto-Advance Check` rename after the primary anchor replace, matching the plan requirement to check for existing step 14 and rename it.
- **Arrow character fix:** Used ASCII `->` instead of Unicode `→` in print statements to avoid Windows cp1252 console encoding error (the file writes UTF-8 correctly; only terminal output was affected).
- **TEAM.md check:** Included step 1 (check TEAM.md exists) before calling dispatcher, per plan spec and consistent with review_team_gate pattern.
- **Phase 10 boundary:** Gate fires dispatcher and displays output inline; does NOT modify the planner Task() call in step 8. That injection is ADVY-01 (Phase 10).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Unicode arrow character causing cp1252 console error on Windows**
- **Found during:** Task 1 verification (first run of patch script)
- **Issue:** Print statements used `→` (U+2192) which Windows cp1252 terminal encoding cannot encode, causing UnicodeEncodeError on exit (though file write succeeded)
- **Fix:** Replaced `→` with ASCII `->` in two print statements
- **Files modified:** D:/GSDteams/scripts/patch-plan-phase.py
- **Verification:** Second run prints clean [SKIP] with no encoding errors
- **Committed in:** 2f50708 (same task commit, fix applied before staging)

**2. [Rule 1 - Bug] Fixed missing idempotency string in inserted section body**
- **Found during:** Task 1 idempotency verification
- **Issue:** The idempotency check looks for `pre_plan_agent_gate` (underscores) in content, but the inserted heading "## 13. Pre-Plan Agent Gate" uses hyphens/spaces — the string was absent, causing SKIP to never trigger and second run to hit ERROR on anchor not found
- **Fix:** Added `<!-- step: pre_plan_agent_gate -->` HTML comment as first line after the heading in both the script's new_section string and the installed plan-phase.md
- **Files modified:** D:/GSDteams/scripts/patch-plan-phase.py, C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md
- **Verification:** Second run prints [SKIP], Python confirms `pre_plan_agent_gate in content: True`
- **Committed in:** 2f50708 (same task commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes required for correct idempotency behavior. No scope creep.

## Issues Encountered
None beyond the two auto-fixed bugs documented above.

## User Setup Required
None - no external service configuration required. Run `bash install.sh` in the project directory to apply the patch to the installed plan-phase.md if this is a fresh install.

## Next Phase Readiness
- Phase 9 Plan 01 (LIFE-02) complete: pre_plan_agent_gate wired into plan-phase.md
- Phase 9 Plan 02 (LIFE-03) ready: patch-execute-phase.py for post_phase_agent_gate in execute-phase.md
- install.sh Section 6 additions for both new scripts (Plan 03 scope)

---
*Phase: 09-lifecycle-trigger-hooks*
*Completed: 2026-02-27*

## Self-Check: PASSED

- FOUND: D:/GSDteams/scripts/patch-plan-phase.py
- FOUND: D:/GSDteams/.planning/phases/09-lifecycle-trigger-hooks/09-01-SUMMARY.md
- FOUND: commit 2f50708
- plan-phase.md: all 9 patch verification checks passed
- pre_plan_agent_gate present, ## 13. Pre-Plan Agent Gate, ## 14. Present Final Status, ## 15. Auto-Advance Check confirmed
