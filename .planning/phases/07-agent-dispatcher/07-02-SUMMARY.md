---
phase: 07-agent-dispatcher
plan: "02"
subsystem: infra
tags: [python, patch-script, install-sh, agent-dispatcher, review-team-gate, idempotent]

# Dependency graph
requires:
  - phase: 07-agent-dispatcher-01
    provides: agent-dispatcher.md workflow file (not yet created — depends on future plan)
  - phase: 06-team-md-v2-schema-config-foundation-02
    provides: patch-settings-agent-studio.py and install.sh with agent_studio config key
  - phase: 01-extension-scaffold-gsd-integration-02
    provides: patch-execute-plan.py which inserts the review_team_gate step (prerequisite)
provides:
  - scripts/patch-execute-plan-dispatcher.py — idempotent patch replacing review_team_gate step body with dispatcher routing
  - install.sh updated to invoke dispatcher patch as the 4th patch in Section 6
affects: [install-sh, execute-plan-patching, agent-dispatcher-wiring, post-plan-gate]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dispatcher-aware gate: agent_studio flag routes to agent-dispatcher.md; review_team flag falls back to review-team.md (v1 preserved)"
    - "SKIP_REVIEW bypass flag: PLAN.md frontmatter skip_review: true suppresses dispatcher for agent-creation plans"
    - "Idempotency via content string check: 'agent-dispatcher.md' in content — not line numbers, resilient to file changes"

key-files:
  created:
    - scripts/patch-execute-plan-dispatcher.py
  modified:
    - install.sh

key-decisions:
  - "Anchor uses full review_team_gate step body (from <step> to </step>) — replace entire step, not just insert before anchor"
  - "Idempotency check uses 'agent-dispatcher.md' in content — unique string only present after dispatcher patch applied"
  - "Dispatcher patch is 4th in Section 6 ordering — patch-execute-plan.py must run first (it inserts the step; this replaces the body)"
  - "SKIP_REVIEW bypass uses awk '{print $2}' on grep output — reads directly from PLAN.md frontmatter without gsd-tools"
  - "Section 5 glob copy unchanged — agent-dispatcher.md picked up automatically by workflows/*.md glob when it exists"

patterns-established:
  - "Patch script structure: read → idempotency check → anchor check → str.replace(anchor, new_body, 1) → write → print result"
  - "Two sys.exit failure paths (usage + anchor not found) plus one skip path (idempotent) plus implicit success"

# Metrics
duration: 4min
completed: 2026-02-27
---

# Phase 7 Plan 02: Agent Dispatcher Execute-Plan Wiring Summary

**Idempotent Python3 patch script replacing review_team_gate step body to route post-plan gate through agent-dispatcher.md when agent_studio is enabled, with v1 review-team.md fallback preserved**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-27T01:58:01Z
- **Completed:** 2026-02-27T02:02:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `scripts/patch-execute-plan-dispatcher.py` — idempotent patch script that replaces the review_team_gate step body with dispatcher-aware routing logic
- New step body reads both REVIEW_TEAM_ENABLED and AGENT_STUDIO_ENABLED flags, adds SKIP_REVIEW bypass, routes to agent-dispatcher.md (agent_studio) or review-team.md (review_team only)
- Updated `install.sh` Section 6 to invoke the dispatcher patch as the 4th patch script (after the existing three), and updated Section 9 completion message

## Task Commits

Each task was committed atomically:

1. **Task 1: Create patch-execute-plan-dispatcher.py** - `ddc2892` (feat)
2. **Task 2: Update install.sh for dispatcher patch** - `7da6c9b` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `scripts/patch-execute-plan-dispatcher.py` — New idempotent Python3 patch script; reads execute-plan.md, checks idempotency via 'agent-dispatcher.md' in content, anchors on full current step body, replaces with dispatcher-aware step body
- `install.sh` — Added dispatcher patch invocation in Section 6 (line 175, after lines 172-174); updated Section 9 completion message to include "dispatcher wiring"

## Decisions Made

- **Anchor is the full step body** (`<step name="review_team_gate">` through `</step>`): Replaces the entire step rather than inserting before/after an anchor substring — cleaner and matches the plan spec exactly. Uses `content.replace(anchor, new_step_body, 1)`.
- **Idempotency check: `'agent-dispatcher.md' in content`**: Unique string only in new step body. Not present in original step body, so correctly differentiates pre/post patch state.
- **Patch ordering in install.sh**: patch-execute-plan.py must run first (it inserts the review_team_gate step); patch-execute-plan-dispatcher.py must run after (it replaces that step's body). Correct ordering: lines 172, 173, 174, 175.
- **SKIP_REVIEW extraction via awk**: Uses `grep -m1 "^skip_review:" | awk '{print $2}'` — reads directly from PLAN.md frontmatter without any gsd-tools dependency.
- **Section 5 glob copy unchanged**: `workflows/*.md` glob automatically picks up `agent-dispatcher.md` when it is created in a future plan. No special-case copy needed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `scripts/patch-execute-plan-dispatcher.py` is ready and passes Python3 syntax check
- `install.sh` updated with correct ordering and updated completion message
- When `install.sh` is run after `agent-dispatcher.md` is created (future plan), the dispatcher will be fully wired into execute-plan.md
- Phase 07 remaining plans can proceed to create the agent-dispatcher.md workflow itself

---
*Phase: 07-agent-dispatcher*
*Completed: 2026-02-27*

## Self-Check: PASSED

- FOUND: scripts/patch-execute-plan-dispatcher.py
- FOUND: install.sh
- FOUND commit: ddc2892 (feat(07-02): create patch-execute-plan-dispatcher.py)
- FOUND commit: 7da6c9b (feat(07-02): update install.sh for dispatcher patch)
