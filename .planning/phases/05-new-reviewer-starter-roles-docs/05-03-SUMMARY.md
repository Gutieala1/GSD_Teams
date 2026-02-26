---
phase: 05-new-reviewer-starter-roles-docs
plan: "03"
subsystem: docs
tags: [install, readme, documentation, version-check, bash]

# Dependency graph
requires:
  - phase: 05-new-reviewer-starter-roles-docs
    provides: "05-01 (starter roles in TEAM.md), 05-02 (/gsd:new-reviewer workflow and command file)"
  - phase: 04-parallel-pipeline-synthesizer-routing
    provides: "Parallel pipeline, synthesizer, REVIEW-REPORT.md routing — described in README first-run walkthrough"
provides:
  - "README.md — installation guide, post-update procedure, TEAM.md format reference, first-run walkthrough"
  - "install.sh Section 2.5 — GSD version compatibility check (sort -V, warn-only, range 1.19.0–1.99.99)"
  - "install.sh Section 5 — commands/gsd copy block (/gsd:new-reviewer installed to ~/.claude/commands/gsd/)"
  - "install.sh Section 9 — completion message updated to reference README.md (not /gsd:reapply-patches)"
affects: [new-users, onboarding, post-update-procedure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "warn-only version check using sort -V (no custom semver parser)"
    - "re-run installer as post-update restore procedure (no separate reapply-patches command)"

key-files:
  created:
    - README.md
  modified:
    - install.sh

key-decisions:
  - "Post-update procedure uses re-run install.sh — NOT /gsd:reapply-patches; README documents this explicitly"
  - "Version check is warn-only — installer proceeds regardless of GSD version mismatch"
  - "README completion message references README.md so users have a single authoritative source for post-update steps"

patterns-established:
  - "install.sh is idempotent and safe to re-run — the intended restore mechanism after /gsd:update"
  - "README.md is the front door — all post-install, post-update, and first-run instructions live there"

# Metrics
duration: ~10min
completed: 2026-02-25
---

# Phase 5 Plan 03: New Reviewer, Starter Roles, Docs — README + install.sh Updates Summary

**README.md (144 lines) and install.sh updates providing onboarding front door, warn-only GSD version check (sort -V, 1.19.0–1.99.99), commands/gsd copy block, and post-update procedure replacing /gsd:reapply-patches**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-02-25
- **Completed:** 2026-02-25
- **Tasks:** 2 auto + 1 checkpoint (human verify)
- **Files modified:** 2

## Accomplishments

- Created README.md (144 lines) covering installation, post-update procedure, TEAM.md format reference, and first-run walkthrough — the extension's complete front door
- Added Section 2.5 to install.sh: GSD version compatibility check using `sort -V` that warns without blocking installation (range 1.19.0–1.99.99)
- Added commands/gsd copy block in Section 5: copies `/gsd:new-reviewer` to `~/.claude/commands/gsd/` during install
- Updated Section 9 completion message to reference README.md instead of the defunct `/gsd:reapply-patches` workflow

## Task Commits

Each task was committed atomically:

1. **Task 1: Update install.sh — version check + commands/gsd copy + completion message** - `5583559` (feat)
2. **Task 2: Create README.md — installation guide, post-update procedure, TEAM.md format, first-run walkthrough** - `debf42f` (feat)

**Plan metadata:** (this commit — docs: complete README.md + install.sh updates — Phase 5 complete)

## Files Created/Modified

- `README.md` — Extension front door: 4 sections (Installation, Post-/gsd:update Procedure, TEAM.md Format, First-Run Walkthrough), routing outcomes table, troubleshooting guide
- `install.sh` — Section 2.5 added (version check, 16 lines), Section 5 extended (commands/gsd copy block, 6 lines), Section 9 completion message updated (3 lines)

## Decisions Made

- **Post-update uses re-run install.sh, not /gsd:reapply-patches:** The `/gsd:reapply-patches` workflow referenced in the old Section 9 message no longer exists as the primary mechanism. README.md and the updated completion message both direct users to `bash install.sh` as the single restore command.
- **Version check is warn-only:** The version check emits `[WARN]` and proceeds — users on untested GSD versions still get a working install rather than a hard failure. This is the correct behavior for a compatibility hint, not a hard requirement.
- **sort -V for semver comparison:** No custom semver parser needed. GNU coreutils `sort -V` handles the min/max range check cleanly with two `printf | sort -V` calls.

## Deviations from Plan

None — plan executed exactly as written. Human verification at checkpoint confirmed all changes were accurate before finalizing.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Phase 5 is the final phase. All 5 phases are complete:

- Phase 1: Extension scaffold + GSD integration (install.sh, TEAM.md, review_team_gate hook, settings toggle)
- Phase 2: Sanitizer + artifact schema (gsd-review-sanitizer.md, ARTIFACT.md format, spawn-reviewers workflow stub)
- Phase 3: Single reviewer + finding schema (gsd-reviewer.md, 7-field finding schema, spawn_reviewers phase 3 logic)
- Phase 4: Parallel pipeline + synthesizer + routing (parallel spawn, gsd-review-synthesizer.md, REVIEW-REPORT.md write, routing actions)
- Phase 5: Starter roles, /gsd:new-reviewer, README + install.sh (production-ready onboarding)

The GSD Review Team extension is complete and ready for use.

---
*Phase: 05-new-reviewer-starter-roles-docs*
*Completed: 2026-02-25*
