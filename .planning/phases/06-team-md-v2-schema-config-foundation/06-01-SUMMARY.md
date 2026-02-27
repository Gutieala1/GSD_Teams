---
phase: 06-team-md-v2-schema-config-foundation
plan: "01"
subsystem: schema
tags: [team-md, yaml, schema, parser, backwards-compat, v2, agent-studio]

# Dependency graph
requires:
  - phase: 05-new-reviewer-starter-roles-docs
    provides: "v1 TEAM.md format (three starter roles, version: 1 sentinel)"
provides:
  - "templates/TEAM.md with version: 2 sentinel and four roles (three v1 unchanged, one v2 Doc Writer)"
  - "Parser specification with normalizeRole algorithm and defaults table in ARCHITECTURE.md"
  - "Authoritative reference for Phase 7 dispatcher implementation"
affects:
  - 07-agent-dispatcher
  - 08-team-studio
  - any future consumer of TEAM.md

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Version sentinel pattern: integer version field in YAML frontmatter drives shim behavior"
    - "normalizeRole algorithm: inject defaults at parse time, never downstream"
    - "v1/v2 coexistence: v1 role blocks valid in v2 TEAM.md, shim applies at parse time"

key-files:
  created: []
  modified:
    - templates/TEAM.md
    - .planning/research/ARCHITECTURE.md

key-decisions:
  - "allowed_tools: used inside scope: to distinguish from hypothetical top-level tools: field — matches success criteria naming explicitly"
  - "agents: list omitted from v2 template frontmatter — dispatcher uses roles: exclusively; agents: is informational only"
  - "v1 role blocks (Security Auditor, Rules Lawyer, Performance Analyst) unchanged — demonstrates v1 compatibility, no new fields added"
  - "normalizeRole applies shim when version < 2 (numeric comparison), not version == '2' (string)"
  - "scope fields (allowed_paths, allowed_tools) default to [] when absent — no path or tool restrictions by default"

patterns-established:
  - "Parser spec in ARCHITECTURE.md: single authoritative reference, Phase 7 implements against this, not against template inference"
  - "Additive schema evolution: every v1 role block is valid v2 — no migration required for existing TEAM.md files"
  - "Separation of concerns: scope.allowed_paths (filesystem) vs scope.allowed_tools (Claude Code tools) are distinct fields"

# Metrics
duration: 2min
completed: 2026-02-27
---

# Phase 6 Plan 01: TEAM.md v2 Schema Foundation Summary

**TEAM.md v2 schema with version: 2 sentinel, Doc Writer autonomous role demonstrating scope.allowed_paths and scope.allowed_tools, plus authoritative normalizeRole parser spec appended to ARCHITECTURE.md**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-27T01:18:29Z
- **Completed:** 2026-02-27T01:20:13Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Updated `templates/TEAM.md` from v1 to v2: version sentinel changed from 1 to 2 (integer), fourth role (doc-writer) added to frontmatter, complete v2 Doc Writer role block with mode, trigger, output_type, commit, commit_message, and scope constraints
- Three v1 starter roles (Security Auditor, Rules Lawyer, Performance Analyst) preserved exactly unchanged — they demonstrate that v1 role blocks are valid in a v2 TEAM.md
- Appended "## Parser Specification (Phase 6 deliverable)" section to ARCHITECTURE.md with version detection rule, 8-field defaults table, normalizeRole pseudocode algorithm, behavioral guarantee, and field name disambiguation

## Task Commits

Each task was committed atomically:

1. **Task 1: Update templates/TEAM.md to v2 schema** - `932257c` (feat)
2. **Task 2: Add parser specification to ARCHITECTURE.md** - `6c417ee` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `templates/TEAM.md` - Version sentinel updated to 2, Doc Writer v2 role added with scope.allowed_paths and scope.allowed_tools, three v1 roles unchanged
- `.planning/research/ARCHITECTURE.md` - Parser Specification section appended with normalizeRole algorithm, defaults table, version detection rule, and field disambiguation

## Decisions Made
- `allowed_tools:` used inside `scope:` block (not top-level `tools:`) per plan instruction — distinguishes filesystem tool access constraint from a hypothetical top-level tool-call whitelist
- `agents:` list omitted from frontmatter — research confirmed dispatcher uses `roles:` exclusively; `agents:` is informational only, per plan instruction to omit it
- Three v1 roles kept unchanged by design — demonstrates v1 compatibility shim; no `mode:`, `trigger:`, or `scope:` fields added to v1 role blocks
- normalizeRole defaults inject on `version < 2` numeric comparison — integer sentinel is the contract, string comparison explicitly rejected in spec prose

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Parser specification is complete and committed — Phase 7 dispatcher has a single authoritative reference to implement against
- `templates/TEAM.md` is the reference implementation: shows v1 compatibility and v2 autonomous role in one file
- The live `.planning/TEAM.md` remains at v1 (version: 1, three starter roles) — no changes made, backwards-compat shim will handle it when dispatcher is built in Phase 7
- No blockers for Phase 6 Plan 02 (settings patch for agent_studio toggle)

---
*Phase: 06-team-md-v2-schema-config-foundation*
*Completed: 2026-02-27*
