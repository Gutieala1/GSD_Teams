---
phase: 01-extension-scaffold-gsd-integration
plan: 01
subsystem: infra
tags: [extension, scaffold, team-review, template, gitkeep]

# Dependency graph
requires: []
provides:
  - Extension repo directory structure with agents/, workflows/, commands/gsd/, scripts/ directories
  - templates/TEAM.md starter template with 3 fully-specified example roles (security-auditor, rules-lawyer, performance-analyst)
  - Machine-parseable role sections split on "## Role:" headers for Phase 2 parser
affects:
  - 01-02 (install.sh — copies templates/TEAM.md to .planning/TEAM.md with existence guard)
  - 02 (review-team.md workflow — uses ## Role: as split anchors to load reviewer definitions)
  - 05 (commands/gsd/ directory — Phase 5 /gsd:new-reviewer command lands here)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Role definition format: YAML block (name+focus) + review criteria list + severity thresholds + routing hints"
    - "Visible example callouts (not HTML comments) to teach role format to users"
    - "## Role: header as machine-parseable split anchor for Phase 2 parser"

key-files:
  created:
    - templates/TEAM.md
    - agents/.gitkeep
    - workflows/.gitkeep
    - commands/gsd/.gitkeep
    - scripts/.gitkeep
  modified: []

key-decisions:
  - "Roles are fully visible (not HTML-commented out) — easier for users to understand the format immediately"
  - "Each role has a visible callout '> Example role — customize before use' so users know to edit before activating"
  - "YAML fenced code blocks inside role sections are the machine-readable anchor for Phase 2 parser"
  - "Three starter roles ship: Security Auditor, Rules Lawyer, Performance Analyst — covers security/correctness/performance lanes"
  - "No .gitkeep in templates/ — that directory has real content (TEAM.md) immediately"

patterns-established:
  - "Role section format: ## Role: [Name] header + blockquote callout + yaml code block + criteria list + severity thresholds + routing hints"
  - "Routing hint values: block_and_escalate | send_for_rework | log_and_continue (deterministic, not synthesizer judgment)"

# Metrics
duration: 8min
completed: 2026-02-26
---

# Phase 1 Plan 01: Extension Scaffold + TEAM.md Starter Template Summary

**Extension repo scaffold created with 4 placeholder directories and TEAM.md starter template delivering 3 fully-specified reviewer roles (Security Auditor, Rules Lawyer, Performance Analyst) with YAML blocks, severity thresholds, and routing hints parseable by Phase 2 workflow.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-02-26T00:26:21Z
- **Completed:** 2026-02-26T00:34:00Z
- **Tasks:** 2
- **Files modified:** 5 (4 .gitkeep + 1 TEAM.md)

## Accomplishments
- Directory scaffold created matching PROJECT.md Extension File Layout architecture
- templates/TEAM.md written with 3 complete roles: Security Auditor, Rules Lawyer, Performance Analyst
- Each role has YAML block (name + focus), review criteria list, severity thresholds, and routing hints
- File splits cleanly on `## Role:` headers — ready for Phase 2 parser to use as split anchors
- Visible example callouts on each role guide users to customize before activating

## Task Commits

Each task was committed atomically:

1. **Task 1: Create extension repo directory scaffold** - `93c3c82` (chore)
2. **Task 2: Write templates/TEAM.md starter template with 3 example roles** - `8e851d2` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `templates/TEAM.md` — Starter team template with 3 example roles; install.sh copies to .planning/TEAM.md in user's GSD project
- `agents/.gitkeep` — Placeholder for Phase 2-4 agent files (sanitizer, reviewer, synthesizer)
- `workflows/.gitkeep` — Placeholder for Phase 2 and 5 workflow files
- `commands/gsd/.gitkeep` — Placeholder for Phase 5 /gsd:new-reviewer command entry point
- `scripts/.gitkeep` — Placeholder for Phase 1 Python patch scripts

## Decisions Made
- **Visible roles, not HTML-commented:** Users can immediately see the full role format without needing to uncomment anything. Makes onboarding faster.
- **Blockquote callout per role:** `> Example role — customize before use.` is visually prominent and clearly signals the roles need editing before they mean anything to a specific project.
- **YAML fenced code blocks as machine anchor:** Phase 2 parser will extract `name:` and `focus:` from these blocks. Using a fenced block (not prose) makes the structure unambiguous.
- **Three roles cover three orthogonal review lanes:** Security (vulnerabilities), correctness (requirements), performance (efficiency) — this is the minimal viable team for most projects.
- **Routing hint values are deterministic strings:** `block_and_escalate`, `send_for_rework`, `log_and_continue` — synthesizer routes on these exact strings, not on free-text judgment.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Directory scaffold is ready for Phase 2-5 agent/workflow/command files to land in correct locations
- templates/TEAM.md is ready for install.sh (01-04) to copy to .planning/TEAM.md with existence guard
- `## Role:` split pattern confirmed: `^## Role:` matches all three role headers
- Phase 2 can parse roles by splitting TEAM.md on `## Role:` and extracting YAML blocks from each section

---
*Phase: 01-extension-scaffold-gsd-integration*
*Completed: 2026-02-26*

## Self-Check: PASSED

All files verified present on disk:
- FOUND: agents/.gitkeep
- FOUND: workflows/.gitkeep
- FOUND: commands/gsd/.gitkeep
- FOUND: scripts/.gitkeep
- FOUND: templates/TEAM.md
- FOUND: .planning/phases/01-extension-scaffold-gsd-integration/01-01-SUMMARY.md

All commits verified in git log:
- FOUND: 93c3c82 (chore: directory scaffold)
- FOUND: 8e851d2 (feat: TEAM.md template)
