---
phase: 12-new-project-integration
plan: 01
subsystem: infra
tags: [patch-script, python, install, new-project, agent-team, lifecycle]

# Dependency graph
requires:
  - phase: 11-agent-creation-new-agent
    provides: /gsd:new-agent command and team-studio add_agent routing
provides:
  - Idempotent Python patch script inserting ## 8.5 Agent Team Setup into new-project.md
  - install.sh Section 6 invocation of patch-new-project.py with file existence guard
  - Section 9 completion message updated to list new-project.md patch
affects: [install.sh, new-project.md, agent-lifecycle]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Python patch script pattern: CLI arg validation, idempotency check, anchor-based str.replace, exit codes"
    - "Install.sh extension pattern: variable declaration + existence guard + python3 invocation"

key-files:
  created:
    - scripts/patch-new-project.py
  modified:
    - install.sh

key-decisions:
  - "Anchor '\n## 9. Done\n' used for insertion — matches existing numbered step convention and is safe across GSD version updates"
  - "Idempotency string 'agent_team_hook' is unique to the patched state — present in both the step comment and body"
  - "Set up later and Skip paths are identical — both continue to Step 9 with no file writes, preserving v1.0 exit path"
  - "Proposals displayed inline as markdown block (not AskUserQuestion) — display and approval are separate interactions"
  - "No TEAM.md write in new-project.md step — only /gsd:new-agent delegation; agent config is /gsd:new-agent's responsibility"
  - "Section 6 ordering: patch-new-project.py is last (after patch-execute-phase.py) — additive, no ordering dependency"

patterns-established:
  - "Phase 12 patch follows exact same Python structure as all prior patch scripts (patch-plan-phase.py model)"
  - "Per-agent loop: display proposal → AskUserQuestion → branch on response → run /gsd:new-agent if creating"

# Metrics
duration: 2min
completed: 2026-02-27
---

# Phase 12 Plan 01: New-Project Integration Summary

**Python patch script inserting agent team setup hook (## 8.5) into GSD new-project.md, wired into install.sh with idempotency guard and existence check**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-27T05:12:40Z
- **Completed:** 2026-02-27T05:14:56Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `scripts/patch-new-project.py` created: full agent_team_hook step body with auto mode guard, 3-option initial question, Set up later/Skip immediate-continue path, Set up now path with PROJECT.md reading, inline proposals display, per-agent loop delegating to /gsd:new-agent
- `install.sh` updated: Section 6 adds NEW_PROJECT variable, file existence guard, and patch-new-project.py invocation; Section 9 completion message lists new-project.md
- Dry-run verified on real `~/.claude/get-shit-done/workflows/new-project.md`: first run prints `[OK] Patched`, second run prints `[SKIP]` — idempotency confirmed

## Task Commits

Each task was committed atomically:

1. **Task 1: Write scripts/patch-new-project.py with full agent_team_hook step body** - `bfaab0a` (feat)
2. **Task 2: Update install.sh Section 6 and Section 9 for Phase 12 patch** - `491ef7e` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `scripts/patch-new-project.py` - Idempotent Python patch script inserting ## 8.5 Agent Team Setup into new-project.md
- `install.sh` - Section 6: new-project.md patch invocation with existence guard; Section 9: updated patches list

## Decisions Made
- Anchor `'\n## 9. Done\n'` chosen for insertion — matches existing numbered step convention in new-project.md, safe across GSD version updates
- Idempotency string `agent_team_hook` is unique to patched state (appears in HTML comment `<!-- step: agent_team_hook -->` and step body references)
- Set up later and Skip options are semantically identical — both continue to Step 9 with zero file writes, preserving v1.0 exit path completely
- Proposals displayed as inline markdown block (not AskUserQuestion) — user sees all proposals before per-agent approval questions
- No TEAM.md write in the new-project step — full agent creation delegated to /gsd:new-agent exclusively (SC6 requirement)
- Section 6 ordering: patch-new-project.py placed last after all prior patches — purely additive, no ordering dependency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 12 is the final v2.0 phase — all plans complete
- Agent lifecycle loop is closed: new project creation now offers agent team setup informed by PROJECT.md
- To activate: run `bash install.sh` in the GSD Review Team project directory — new-project.md will receive the ## 8.5 Agent Team Setup step
- Running `bash install.sh` a second time is safe — all patches print `[SKIP]`

## Self-Check: PASSED

- FOUND: scripts/patch-new-project.py
- FOUND: install.sh
- FOUND: .planning/phases/12-new-project-integration/12-01-SUMMARY.md
- FOUND: bfaab0a (Task 1 commit)
- FOUND: 491ef7e (Task 2 commit)

---
*Phase: 12-new-project-integration*
*Completed: 2026-02-27*
