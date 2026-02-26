---
phase: 05-new-reviewer-starter-roles-docs
plan: "02"
subsystem: workflow
tags: [slash-command, guided-conversation, team-md, reviewer-role, new-reviewer]

# Dependency graph
requires:
  - phase: 05-new-reviewer-starter-roles-docs
    provides: Phase 5 plan 01 context (starter roles in TEAM.md)
provides:
  - /gsd:new-reviewer slash command backed by 7-step guided workflow
  - workflows/new-reviewer.md (7-step role creation workflow with decision gate)
  - commands/gsd/new-reviewer.md (slash command entry point)
affects: [install.sh, review-team workflow validate_team step, TEAM.md consumers]

# Tech tracking
tech-stack:
  added: []
  patterns: [GSD XML workflow steps with AskUserQuestion interaction, decision gate before file write, Read-then-Write append for TEAM.md]

key-files:
  created:
    - workflows/new-reviewer.md
    - commands/gsd/new-reviewer.md
  modified: []

key-decisions:
  - "7-step flow: check_team_md → gather_domain → gather_name → gather_criteria → gather_severity → decision_gate → write_role"
  - "All AskUserQuestion headers capped at 12 characters (Custom Focus and Display Name use exactly 12)"
  - "Decision gate (step 6) shows full role preview before writing — satisfies ROLE-02 requirement"
  - "write_role handles both TEAM.md exists (append + update frontmatter roles list) and does-not-exist (create stub header + role)"
  - "execution_context in command file uses installed path (~/.claude/get-shit-done-review-team/) not source path"
  - "allowed-tools: Read, Write, Bash, AskUserQuestion — no Glob or Grep (workflow doesn't use them)"

patterns-established:
  - "GSD workflow format: XML <step> blocks, no YAML frontmatter, <purpose>/<inputs> preamble"
  - "Command file format: YAML frontmatter (name/description/allowed-tools) + <objective>/<execution_context>/<process>"
  - "AskUserQuestion header 12-char limit enforced across all interaction steps"

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 5 Plan 02: New Reviewer Summary

**Guided `/gsd:new-reviewer` command and 7-step workflow that collects domain, name, criteria, severity, and routing through AskUserQuestion prompts before writing a valid TEAM.md role after explicit confirmation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T03:35:34Z
- **Completed:** 2026-02-26T03:38:02Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created `workflows/new-reviewer.md` with all 7 steps, AskUserQuestion interaction at each data-gathering step, domain-specific criteria options (Security/Performance/Requirements/Custom), and a decision gate that previews the full role before any disk write
- Created `commands/gsd/new-reviewer.md` as the slash command entry point with correct name, allowed-tools list, and installed-path execution_context reference
- Both files are ready for inclusion in the install.sh copy step

## Task Commits

Each task was committed atomically:

1. **Task 1: Create workflows/new-reviewer.md** - `03b3867` (feat)
2. **Task 2: Create commands/gsd/new-reviewer.md** - `4484e68` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `workflows/new-reviewer.md` - 7-step guided role creation workflow (360 lines)
- `commands/gsd/new-reviewer.md` - /gsd:new-reviewer slash command entry point (27 lines)

## Decisions Made
- Decision gate (step 6) shows assembled role preview and uses `header: "Confirm"` (7 chars) — satisfies ROLE-02 write-after-confirmation requirement
- `Custom Focus` header uses all 12 allowed characters; design allows free-text follow-up via Other path when user selects Custom domain
- Command file references installed path `~/.claude/get-shit-done-review-team/` so the command works after install.sh copies it to `~/.claude/commands/gsd/`
- write_role step explicitly updates YAML frontmatter `roles:` list when TEAM.md already exists (not just appends markdown) — keeps TEAM.md machine-readable for validate_team

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `/gsd:new-reviewer` command is complete and ready for install.sh copy step
- Plan 03 (starter roles docs or install.sh updates) can reference `commands/gsd/new-reviewer.md` and `workflows/new-reviewer.md` directly
- validate_team step in review-team.md already handles the TEAM.md format that write_role produces

---
*Phase: 05-new-reviewer-starter-roles-docs*
*Completed: 2026-02-26*
