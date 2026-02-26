---
phase: 02-sanitizer-artifact-schema
plan: 02
subsystem: review-pipeline
tags: [workflow, pipeline, team-validation, sanitizer-spawn, orchestration]

# Dependency graph
requires:
  - phase: 02-sanitizer-artifact-schema
    plan: 01
    provides: "gsd-review-sanitizer.md agent for Task() spawning"
  - phase: 01-extension-scaffold-gsd-integration
    provides: "review_team_gate hook in execute-plan.md, TEAM.md template"
provides:
  - "review-team.md workflow skeleton -- TEAM.md validation + sanitizer Task() spawning"
  - "Phase 3/4 placeholder steps for reviewer spawning and synthesis"
  - "TEAM-03 satisfaction: zero-role validation halt with actionable error"
affects: [03-single-reviewer-finding-schema, 04-parallel-pipeline-synthesizer-routing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "GSD workflow convention (<purpose>, <inputs>, <step name=''> blocks)"
    - "TEAM.md role parsing: split on ## Role: headers, extract YAML name: field, validate review criteria"
    - "Per-plan artifact path convention: {phase}-{plan}-ARTIFACT.md"
    - "Defensive double-check pattern: workflow re-validates TEAM.md even though gate already confirmed"

key-files:
  created:
    - "workflows/review-team.md"
  modified: []

key-decisions:
  - "Workflow follows GSD workflow conventions (purpose/inputs/step blocks), not agent frontmatter (no YAML name/tools/color)"
  - "Three-condition role validation: ## Role: header + YAML name: field + review criteria items"
  - "Sanitizer @-reference uses canonical extension path: @~/.claude/get-shit-done-review-team/agents/gsd-review-sanitizer.md"
  - "ARTIFACT.md path follows {phase}-{plan}-ARTIFACT.md convention matching SUMMARY.md naming"
  - "Phase 3/4 steps are documented placeholders with clear '[not yet implemented]' markers"

patterns-established:
  - "review-team.md step sequence: validate_team -> sanitize -> spawn_reviewers -> synthesize -> return_status"
  - "TEAM.md validation halt pattern: structured error block with actionable fix command (/gsd:new-reviewer)"
  - "Artifact path construction from PHASE_ID and PLAN_NUM variables"

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 2 Plan 2: Review Team Workflow Skeleton Summary

**Review-team.md pipeline workflow with TEAM.md role validation, sanitizer Task() spawning, and Phase 3/4 placeholder steps**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T01:16:27Z
- **Completed:** 2026-02-26T01:18:16Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `review-team.md` workflow following GSD workflow conventions with `<purpose>`, `<inputs>`, and `<step>` blocks
- Implemented TEAM.md validation logic: splits on `## Role:` headers, validates three conditions per role (section header, YAML name: field, review criteria items)
- Built zero-role halt condition with structured error message naming requirements and suggesting `/gsd:new-reviewer` (satisfies TEAM-03)
- Implemented sanitizer spawning step with correct Task() invocation pattern and `@~/.claude/get-shit-done-review-team/agents/gsd-review-sanitizer.md` reference
- Added ARTIFACT.md path construction following `{phase}-{plan}-ARTIFACT.md` per-plan convention (satisfies SAND-03)
- Added ARTIFACT.md existence verification after sanitizer returns
- Created documented placeholder steps for Phase 3 (spawn_reviewers) and Phase 4 (synthesize)
- Defined REVIEW PIPELINE: SANITIZE COMPLETE return format for orchestrator consumption

## Task Commits

Each task was committed atomically:

1. **Task 1: Create review-team.md workflow skeleton** - `f175d4e` (feat)

## Files Created/Modified
- `workflows/review-team.md` - Review pipeline workflow: validates TEAM.md roles, spawns sanitizer via Task(), verifies ARTIFACT.md output, with Phase 3/4 placeholders

## Decisions Made
- Workflow uses GSD workflow conventions (`<purpose>`, `<inputs>`, `<step>` blocks) not agent YAML frontmatter -- this is a workflow, not an agent
- Three-condition role validation ensures downstream Phase 3 reviewer spawning will never encounter structurally invalid roles
- Sanitizer @-reference uses the canonical extension install path from Phase 1 (`@~/.claude/get-shit-done-review-team/agents/...`)
- ARTIFACT.md path mirrors SUMMARY.md naming for consistency and discoverability
- Phase 3/4 steps are present as documented placeholders -- they describe what will be implemented but do not execute

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- review-team.md workflow ready for the review_team_gate step to load via @-reference
- Sanitizer spawning wired: Task() invocation with correct inputs (SUMMARY_PATH, ARTIFACT_PATH, PHASE_ID, PLAN_NUM)
- Phase 3 can extend spawn_reviewers step to read validated role names and spawn gsd-reviewer agents
- Phase 4 can extend synthesize step to collect findings and route via gsd-review-synthesizer
- TEAM-03 (validation halt), SAND-03 (disk write path), SAND-04 (artifact-only passing design) all satisfied

## Self-Check: PASSED

- FOUND: workflows/review-team.md
- FOUND: 02-02-SUMMARY.md
- FOUND: commit f175d4e

---
*Phase: 02-sanitizer-artifact-schema*
*Completed: 2026-02-26*
