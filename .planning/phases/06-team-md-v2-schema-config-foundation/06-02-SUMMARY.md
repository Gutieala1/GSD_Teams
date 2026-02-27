---
phase: 06-team-md-v2-schema-config-foundation
plan: "02"
subsystem: infra
tags: [python, patch-script, install, settings, config, agent-studio]

# Dependency graph
requires:
  - phase: 06-team-md-v2-schema-config-foundation
    provides: Research confirming anchor strings in post-review-team-patched settings.md
  - phase: 01-extension-scaffold-gsd-integration
    provides: patch-settings.py (4-touch-point pattern this script mirrors), install.sh (Sections 6 and 7 being extended)

provides:
  - scripts/patch-settings-agent-studio.py — idempotent 4-touch-point patcher for Agent Studio toggle in settings.md
  - install.sh extended — Section 6 invokes new patch script, Section 7 writes workflow.agent_studio to config.json atomically

affects: [07-agent-studio-dispatcher, all phases using agent_studio config key, downstream settings.md consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - 4-touch-point idempotent Python3 patch script (SKIP/WARN/OK) — established by patch-settings.py, extended here for agent_studio
    - Single jq pipe filter for atomic multi-key config.json update (avoids race condition from split commands)

key-files:
  created:
    - scripts/patch-settings-agent-studio.py
  modified:
    - install.sh

key-decisions:
  - "Anchors target the post-review-team-patch state of settings.md (not the original un-patched version) — Touch point 1 anchors on the Review Team closing block"
  - "jq filter chains both null-conditional checks in a single invocation using pipe — avoids race condition from two separate tmp file operations"
  - "Touch point 3 save_as_defaults uses review_team: <current> as the last-line anchor — same pattern as patch-settings.py touch point 3 but for the next key"
  - "Section 8 TEAM.md existence guard explicitly preserved unchanged — installer re-run safety maintained"

patterns-established:
  - "Chained jq filter: 'if .workflow.X == null then .X = false else . end | if .workflow.Y == null then .Y = false else . end' — pattern for adding multiple config.json keys atomically"
  - "Patch script anchor selection: always anchor on the CURRENT patched state, not the original file content"

# Metrics
duration: 2min
completed: 2026-02-27
---

# Phase 06 Plan 02: Agent Studio Settings Patch + install.sh Extension Summary

**Idempotent 4-touch-point patch script adds Agent Studio toggle to settings.md after Review Team, and install.sh atomically writes workflow.agent_studio to config.json alongside workflow.review_team**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-27T01:18:34Z
- **Completed:** 2026-02-27T01:20:26Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created scripts/patch-settings-agent-studio.py following exact patch-settings.py 4-touch-point structure (SKIP/WARN/OK messages, patches_applied/patches_skipped counters, write-only-if-changed)
- Extended install.sh Section 6 to invoke the new patch script after patch-settings.py on the same $SETTINGS target
- Extended install.sh Section 7 with chained jq pipe for atomic review_team + agent_studio config.json update, plus Python3 fallback with both null-checks

## Task Commits

Each task was committed atomically:

1. **Task 1: Create scripts/patch-settings-agent-studio.py** - `89f818d` (feat)
2. **Task 2: Extend install.sh for agent_studio patch invocation and config.json key** - `01dc6e0` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `scripts/patch-settings-agent-studio.py` - 4-touch-point idempotent patcher: adds Agent Studio AskUserQuestion entry, adds agent_studio to update_config and save_as_defaults workflow objects, updates success_criteria count 7→8
- `install.sh` - Section 6: +1 line for patch-settings-agent-studio.py invocation; Section 7: jq chained pipe + Python3 fallback extended with agent_studio check; Section 9: completion message updated

## Decisions Made

- Anchors target post-review-team-patch state: Touch point 1 anchors on the closing two option lines + `]\n  }\n])` of the Review Team question block, which is the current last entry in the AskUserQuestion array.
- Single jq pipe invocation for Section 7 (not two separate mktemp/mv sequences) to avoid race condition on concurrent runs.
- Touch point 3 save_as_defaults anchor uses `"review_team": <current>\n  }` (last key before closing brace) matching the pattern established by patch-settings.py.
- Section 9 completion message updated to "Review Team toggle + Agent Studio toggle" to accurately reflect both patches.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- workflow.agent_studio will be written to config.json on next `bash install.sh` run
- settings.md will present 8 settings (including Agent Studio toggle) after the patch is applied
- Both workflow.review_team and workflow.agent_studio are independent boolean flags in config.json
- Phase 06 Plan 03 (TEAM.md v2 schema template) and downstream dispatcher phases can now read workflow.agent_studio from config.json

## Self-Check: PASSED

- FOUND: scripts/patch-settings-agent-studio.py
- FOUND: install.sh
- FOUND: 06-02-SUMMARY.md
- FOUND commit 89f818d: feat(06-02): create patch-settings-agent-studio.py
- FOUND commit 01dc6e0: feat(06-02): extend install.sh for agent_studio patch and config key

---
*Phase: 06-team-md-v2-schema-config-foundation*
*Completed: 2026-02-27*
