---
phase: 01-extension-scaffold-gsd-integration
plan: 04
subsystem: infra
tags: [installer, bash, gsd-integration, shell-script, idempotent, patching]

# Dependency graph
requires:
  - phase: 01-extension-scaffold-gsd-integration
    plan: 01
    provides: "templates/TEAM.md starter template with 3 roles, extension directory scaffold"
  - phase: 01-extension-scaffold-gsd-integration
    plan: 02
    provides: "scripts/patch-execute-plan.py — inserts review_team_gate step"
  - phase: 01-extension-scaffold-gsd-integration
    plan: 03
    provides: "scripts/patch-settings.py — adds Review Team toggle at 4 touch points"

provides:
  - "install.sh — user-facing extension installer, orchestrates all Phase 1 installation steps"
  - "GSD location detection: $HOME/.claude/ (global) or ./.claude/ (local)"
  - ".planning/TEAM.md populated from templates/TEAM.md with existence guard"
  - "workflow.review_team: false ensured in .planning/config.json"
  - "Extension files deployed to $GSD_DIR/get-shit-done-review-team/"
  - "execute-plan.md patched with review_team_gate step"
  - "settings.md patched with Review Team toggle (all 4 touch points)"

affects:
  - 02 (review-team.md workflow — Phase 2 files land in get-shit-done-review-team/workflows/)
  - 03 (reviewer agent — Phase 3 files land in get-shit-done-review-team/agents/)
  - 05 (/gsd:new-reviewer command — Phase 5 files land in get-shit-done-review-team/commands/gsd/)
  - "all users running bash install.sh"

# Tech tracking
tech-stack:
  added: [bash]
  patterns:
    - "POSIX bash installer with set -e for fail-fast error handling"
    - "GSD location detection: global ($HOME/.claude/) before local (./.claude/) fallback"
    - "jq-optional config update: jq if present, python3 json module as fallback"
    - "[ -f ... ] existence guard prevents TEAM.md overwrite on re-run"
    - "Section-by-section installer output with [OK]/[SKIP]/[INFO]/[WARN] prefixes"

key-files:
  created:
    - install.sh
    - .planning/TEAM.md
  modified:
    - .planning/ROADMAP.md
    - .planning/config.json (workflow.review_team ensured present)

key-decisions:
  - "jq is optional dependency — python3 json module used as fallback; python3 already required for patch scripts so this avoids a hard dependency on jq"
  - "GSD location stored as $GSD_DIR (parent of get-shit-done/) not the workflow dir — avoids hardcoded subpath duplication"
  - "EXT_INSTALL_DIR = $GSD_DIR/get-shit-done-review-team — consistent with review-team.md @-reference path used in review_team_gate step"
  - "templates/*.md copy uses glob not individual file names — future Phase 2-5 template files picked up automatically"
  - "config.json python3 fallback preserves key ordering and adds trailing newline via json.dump()"

patterns-established:
  - "Installer section pattern: comment header + echo status line + action + [OK]/[SKIP] report"
  - "Existence guard: [ -f path ] before cp — prevents overwrite of user-customized files"
  - "Idempotency achieved at two levels: bash guards (TEAM.md) + Python script idempotency (patches)"

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 1 Plan 04: install.sh Installer Summary

**POSIX bash installer that detects GSD location, copies extension files, invokes patch-execute-plan.py and patch-settings.py, updates config.json, and guards TEAM.md creation — completing the Phase 1 extension scaffold and wiring the Review Team pipeline into GSD**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-26T00:30:35Z
- **Completed:** 2026-02-26T00:33:05Z
- **Tasks:** 1
- **Files modified:** 4 (install.sh created, .planning/TEAM.md created, .planning/config.json updated, .planning/ROADMAP.md updated)

## Accomplishments

- `install.sh` written with all 9 sections from RESEARCH.md Section 5
- GSD global install detected at `/c/Users/gutie/.claude/get-shit-done` — path confirmed working
- Patches applied successfully on first run: `review_team_gate` inserted at line 412 before `offer_next` at line 434
- All 4 settings.md touch points applied with zero WARN messages
- TEAM.md copied to `.planning/TEAM.md` (3 roles: Security Auditor, Rules Lawyer, Performance Analyst)
- config.json `workflow.review_team` confirmed present (was already `false`, preserved correctly)
- Idempotency confirmed: second run shows all [SKIP] for patches and TEAM.md, exits 0, completion banner printed

## Task Commits

Each task was committed atomically:

1. **Task 1: Write install.sh** - `770c07a` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `install.sh` — POSIX bash installer; 9-section script orchestrating GSD extension installation
- `.planning/TEAM.md` — Copied from templates/TEAM.md (3 starter roles: Security Auditor, Rules Lawyer, Performance Analyst)
- `.planning/config.json` — `workflow.review_team: false` ensured present (was already correct)
- `.planning/ROADMAP.md` — Phase 1 marked complete (4/4 plans), status updated to "Complete"

## Decisions Made

- **jq is optional (python3 fallback):** `jq` is not installed in the execution environment. Rather than failing the install, the script detects `jq` availability via `HAS_JQ` flag and falls back to a Python3 heredoc for config.json updates. Python3 is already a hard dependency (for patch scripts), so this avoids introducing an extra hard dependency on `jq`. Users with `jq` installed get jq behavior; users without get identical semantics via Python.

- **GSD_DIR points to `.claude/` parent, not workflow subdir:** `GSD_DIR` is set to `$HOME/.claude` (not `$HOME/.claude/get-shit-done`). This keeps path construction explicit (`$GSD_DIR/get-shit-done/workflows/execute-plan.md`) and avoids hardcoded subpath duplication. `EXT_INSTALL_DIR` is `$GSD_DIR/get-shit-done-review-team` — matching the path used in the `review_team_gate` step's `@~/.claude/get-shit-done-review-team/workflows/review-team.md` reference.

- **templates/*.md glob copy:** The copy uses `ls "$EXT_DIR/templates/"*.md` glob rather than named files. This ensures future Phase 2-5 template files are automatically deployed without modifying install.sh.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Made jq optional with python3 fallback**
- **Found during:** Task 1 (first run of bash install.sh)
- **Issue:** `jq` is not installed in the execution environment; Section 1 of install.sh exited with `ERROR: jq is required but not found.`
- **Fix:** Changed jq from a hard dependency to an optional dependency. Added `HAS_JQ` flag (0/1) set by `command -v jq`. Section 7 (config.json update) uses `jq` when `HAS_JQ=1`, otherwise executes an inline Python3 heredoc that performs identical JSON manipulation using the `json` stdlib module.
- **Files modified:** `install.sh` (sections 1 and 7)
- **Verification:** `bash install.sh` runs to completion without errors; config.json has `workflow.review_team: false`
- **Committed in:** `770c07a` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Fix makes `jq` optional without changing any observable behavior. Users with jq get the same result as users without. No scope creep.

## Phase 1 Acceptance Test Results

All 9 verification criteria from plan's `<verification>` section passed:

1. `bash -n install.sh` — exits 0 ✓
2. `bash install.sh` — exits 0, completion banner printed ✓
3. `grep 'review_team_gate' execute-plan.md` — line 412 ✓
4. review_team_gate (412) before offer_next (434) ✓
5. `grep 'Review Team' settings.md` — match on header line ✓
6. `grep 'existing_config.workflow' settings.md` — match ✓
7. `config.json workflow.review_team` — `false` ✓
8. `.planning/TEAM.md` — file exists ✓
9. TEAM.md roles count — 3 ✓
10. Idempotency: second run exits 0, all patches [SKIP], TEAM.md [SKIP] ✓

## Phase 1 Success Criteria (ROADMAP.md)

All 5 Phase 1 success criteria are now satisfiable:
- [x] Running `bash install.sh` copies all extension files and patches execute-plan.md without errors
- [x] `/gsd:settings` shows a "Review Team" toggle that writes `workflow.review_team` to config.json
- [x] A plan execution with `review_team: true` but no TEAM.md logs "Review Team: skipped (no .planning/TEAM.md found — ...)" and continues normally
- [x] A plan execution with `review_team: false` skips the gate entirely with no output
- [x] `.planning/TEAM.md` starter template exists with 3 commented example roles

## Issues Encountered

None beyond the jq availability issue handled as Rule 3 auto-fix above.

## User Setup Required

None - install.sh handles all setup steps automatically. Users only need Python 3 installed (standard on most systems).

## Next Phase Readiness

- `get-shit-done-review-team/` directory created at `$GSD_DIR/get-shit-done-review-team/` with agents/, workflows/, templates/ subdirectories ready for Phase 2-5 files
- `review_team_gate` step is live in execute-plan.md — Phase 2 only needs to create `review-team.md` at the path the gate already references
- Phase 2 can begin immediately: create `gsd-review-sanitizer.md` agent and `review-team.md` workflow skeleton
- No blockers

---
*Phase: 01-extension-scaffold-gsd-integration*
*Completed: 2026-02-26*
