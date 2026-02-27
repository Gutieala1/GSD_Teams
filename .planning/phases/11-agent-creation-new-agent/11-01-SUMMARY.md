---
phase: 11-agent-creation-new-agent
plan: "11-01"
subsystem: agent-studio
tags: [workflow, agent-creation, guided-conversation, new-agent, TEAM.md]

# Dependency graph
requires:
  - phase: 07-agent-dispatcher
    provides: agent-dispatcher.md that routes agent triggers and modes
  - phase: 06-team-md-v2-schema-config-foundation
    provides: TEAM.md v2 schema with mode/trigger/scope/output_type fields
  - phase: 05-new-reviewer-starter-roles-docs
    provides: new-reviewer.md workflow (pattern reference for new-agent.md)
  - phase: 08-team-roster-gsd-team
    provides: /gsd:team roster display that shows created agents

provides:
  - 9-step guided conversation workflow for creating any agent (advisory or autonomous)
  - Mode-branched conversation: advisory path (gather_advisory_details) vs autonomous path (gather_scope)
  - Decision gate with full role block preview before writing — satisfies CREA-03 requirement
  - write_agent step that creates version: 2 TEAM.md and commits via gsd-tools.cjs

affects:
  - 11-agent-creation-new-agent (plan 02 — command file that calls this workflow)
  - any phase that creates or documents the /gsd:new-agent command

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "9-step GSD workflow pattern: purpose/inputs/step blocks with conditional branching"
    - "Mode-branched step execution: steps skip via inline 'Skip this step entirely if mode == X' guard"
    - "Decision gate pattern: assemble full preview, show Cancel/Edit/Create, write only on confirm"
    - "Slug collision check: compare derived slug against existing_slugs before writing"
    - "Read-then-Write TEAM.md update: frontmatter roles list + appended role block"

key-files:
  created:
    - workflows/new-agent.md
  modified: []

key-decisions:
  - "9-step sequence chosen over 7-step (new-reviewer pattern) to accommodate mode branching — advisory and autonomous paths require different detail gathering (criteria/severity vs scope/commit)"
  - "Conditional skip guards embedded inline in each branching step ('Skip this step entirely if mode == X') — avoids goto-style step redirects, makes branching self-documenting"
  - "gather_advisory_details fires only for advisory; gather_scope fires only for autonomous — strict mutual exclusion, not both"
  - "decision_gate shows full agent file content (agents/gsd-agent-{slug}.md) for autonomous agents in addition to role block — user sees complete artifact before confirming"
  - "write_agent creates version: 2 TEAM.md (not version: 1) — prevents normalizeRole shim from overriding explicit v2 fields like mode/trigger/scope"
  - "Cancel option in decision_gate exits with no writes — 'No files were written' announced explicitly"
  - "Commit uses ~/.claude/get-shit-done/bin/gsd-tools.cjs (installed path) not source path — consistent with new-reviewer.md convention"
  - "Advisory agents in write_agent get N/A severity and routing fields — makes it explicit that advisory agents without findings output do not participate in routing pipeline"

patterns-established:
  - "Mode-branched workflow: use inline skip guards rather than step-level conditionals"
  - "Scope block in TEAM.md entry is autonomous-only — never added to advisory role blocks"
  - "Severity/routing fields in TEAM.md entry are advisory-only — never added to autonomous role blocks"
  - "New TEAM.md always created with version: 2 header"

# Metrics
duration: 2min
completed: 2026-02-27
---

# Phase 11 Plan 01: New Agent Workflow Summary

**9-step guided conversation workflow for `/gsd:new-agent` that branches on mode (advisory vs autonomous), previews full role definition at decision gate, and writes only on explicit confirmation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-27T04:39:24Z
- **Completed:** 2026-02-27T04:41:49Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `workflows/new-agent.md` — the core deliverable for Phase 11 plan 01
- Implemented mode-branched conversation: advisory agents reach `gather_advisory_details` (criteria + severity + routing questions), autonomous agents reach `gather_scope` (paths + tools + commit questions) — never both
- Decision gate (step 8) assembles and displays full role block plus agent file content before any write; provides Cancel/Edit/Create options
- `write_agent` (step 9) is the only step that writes to disk; handles TEAM.md exists vs not-exists; creates version: 2 on new file; commits via gsd-tools.cjs

## Task Commits

Each task was committed atomically:

1. **Task 1: Write workflows/new-agent.md — 9-step guided conversation workflow** - `5378631` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified

- `workflows/new-agent.md` - Complete 9-step guided conversation workflow for /gsd:new-agent

## Decisions Made

- 9-step sequence chosen over 7-step (new-reviewer pattern) to accommodate mode branching
- Conditional skip guards embedded inline in each branching step for self-documenting conditional flow
- `gather_advisory_details` fires only for advisory; `gather_scope` fires only for autonomous — strict mutual exclusion
- `decision_gate` shows full agent file content for autonomous agents in addition to role block
- `write_agent` creates `version: 2` TEAM.md (not version: 1) to prevent normalizeRole shim override
- Cancel option in `decision_gate` explicitly announces "No files were written" and exits
- Commit uses `~/.claude/get-shit-done/bin/gsd-tools.cjs` (installed path, not source path)
- Severity/routing fields in TEAM.md entry are advisory-only; scope block is autonomous-only

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `workflows/new-agent.md` is complete and ready for use
- Phase 11 plan 02 can now create the `/gsd:new-agent` command file that calls this workflow
- The workflow follows the same `<purpose>`/`<inputs>`/`<step>` pattern as `new-reviewer.md` — consistent interface for the command layer

---
*Phase: 11-agent-creation-new-agent*
*Completed: 2026-02-27*

## Self-Check: PASSED

- FOUND: `workflows/new-agent.md` (648 lines, 9 steps)
- FOUND: `.planning/phases/11-agent-creation-new-agent/11-01-SUMMARY.md`
- FOUND: commit `5378631` (feat: create workflows/new-agent.md)
- FOUND: commit `fa47e69` (docs: complete new-agent workflow plan)
