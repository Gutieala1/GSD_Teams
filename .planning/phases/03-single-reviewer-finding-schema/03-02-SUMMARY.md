---
phase: 03-single-reviewer-finding-schema
plan: "02"
subsystem: agents
tags: [reviewer, agent, gsd-reviewer, role-injection, finding-schema, isolation, evidence-grounded, severity-rubric]

# Dependency graph
requires:
  - phase: 03-single-reviewer-finding-schema
    provides: schemas/finding-schema.md — 7-field Finding JSON schema with severity rubric and routing destinations
  - phase: 02-sanitizer-artifact-schema
    provides: gsd-review-sanitizer.md — GSD agent convention reference (6-part structure, tools, color)
provides:
  - agents/gsd-reviewer.md — Parameterized reviewer agent serving all roles via role injection at spawn time
affects:
  - 03-03 (review-team.md workflow update — spawns gsd-reviewer via Task() with role injection)
  - 04-parallel-reviewer-synthesis (gsd-review-synthesizer.md consumes findings produced by this agent)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Parameterized agent: single agent file serves all reviewer roles via <role_definition> tag injection at spawn time — no per-role files needed"
    - "Isolation enforcement in agent instructions: Step 1 explicitly prohibits reading any file except ARTIFACT.md"
    - "Evidence-first finding policy: character-for-character quote required — no quote = no finding"
    - "Domain confinement via not_responsible_for guard in <role> block and critical_rule #3"
    - "Severity anti-inflation: tie-breaking rule + production-deploy test embedded in Step 3"

key-files:
  created:
    - agents/gsd-reviewer.md
  modified: []

key-decisions:
  - "Single parameterized agent file serves all reviewer roles — role name, domain, checklist, not_responsible_for, and ID prefix all extracted from <role_definition> tags at spawn time"
  - "Tools: Read and Write only — no Bash, no Grep, no codebase inspection (content analyst, not code inspector)"
  - "Step 0 extracts ID prefix from role name (first 3-4 uppercase chars) — enables collision-free IDs in Phase 4 parallel execution"
  - "not_responsible_for guard in <role> block + critical_rule #3 creates two-layer domain confinement (behavioral instruction + hard rule)"
  - "Empty findings array ({\"findings\": []}) documented as valid output in both <output> block and Step 4 — not an error signal"

patterns-established:
  - "6-part GSD agent structure: YAML frontmatter + <role> + <core_principle> + Steps 0-N + <output> + <critical_rules>"
  - "Role injection pattern: Task() prompt injects <role_definition> tags; agent reads them in Step 0"
  - "ARTIFACT.md isolation: reviewer agents read only the sanitized artifact, never SUMMARY.md, PLAN.md, or STATE.md"

# Metrics
duration: 3min
completed: 2026-02-26
---

# Phase 3 Plan 02: GSD Reviewer Agent Summary

**Parameterized gsd-reviewer.md agent with role injection via <role_definition> tags, ARTIFACT.md-only isolation, evidence-grounded findings, 5-level severity rubric with anti-inflation check, and pure JSON output — one agent file serves all reviewer roles**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-26T02:02:25Z
- **Completed:** 2026-02-26T02:06:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `agents/gsd-reviewer.md` as a complete, spawnable GSD agent following the 6-part convention from gsd-review-sanitizer.md
- Implemented role parameterization: Step 0 extracts role name, domain, checklist, not_responsible_for list, ID prefix, and routing hints from `<role_definition>` tags injected at spawn time — no agent file modification needed for different reviewer roles
- Enforced ARTIFACT.md isolation in Step 1: explicit "DO NOT read any other file" instruction covering PLAN.md, STATE.md, SUMMARY.md, TEAM.md
- Embedded evidence-first policy in Step 2: character-for-character quote required in evidence field; paraphrase explicitly declared invalid
- Embedded 5-level severity rubric in Step 3 with tie-breaking rule (choose lower) and anti-inflation check (production deploy test)
- Set `<output>` to enforce pure JSON output — no prose before or after the JSON code block
- Documented empty findings array as valid expected output in both `<output>` and Step 4
- Created 5 DO NOT guards in `<critical_rules>`: isolation, evidence, domain confinement, prose wrapping, severity inflation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create agents/gsd-reviewer.md** - `de020bb` (feat)

**Plan metadata:** (docs commit — recorded below)

## Files Created/Modified

- `agents/gsd-reviewer.md` - Parameterized GSD reviewer agent with 6-part structure: YAML frontmatter (name: gsd-reviewer, tools: Read Write, color: green), `<role>` block with not_responsible_for guard, `<core_principle>` evidence-grounded finding policy, Step 0 role extraction, Step 1 ARTIFACT.md read with isolation enforcement, Step 2 role criteria application with evidence rule, Step 3 5-level severity rubric with tie-breaking and anti-inflation check, Step 4 JSON compilation, `<output>` pure JSON instruction, and `<critical_rules>` with 5 DO NOT guards

## Decisions Made

- **Single parameterized agent:** Role content is never hardcoded in the agent file. All role-specific content (name, domain, checklist, not_responsible_for, severity thresholds) is extracted from `<role_definition>` tags at spawn time. This means the review-team workflow can spawn any role by injecting different role definitions without modifying gsd-reviewer.md.
- **Read and Write tools only:** gsd-reviewer.md is a content analyst agent, not a code inspector. No Bash, no Grep, no filesystem enumeration. The agent reads one file (ARTIFACT.md) and writes nothing — return is via response text (JSON), not disk write.
- **Two-layer domain confinement:** The `<role>` block provides behavioral instruction ("You are NOT responsible for: ...") and critical_rule #3 provides a hard constraint ("DO NOT include findings outside your declared domain"). Defense in depth.
- **ID prefix from role name:** Deriving the prefix from the first 3-4 uppercase characters of the `name:` YAML field (SEC, LAW, PERF) is deterministic and collision-free. Established in 03-01 finding schema; embedded in Step 0 extraction instructions.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `agents/gsd-reviewer.md` is ready to be spawned by the review-team workflow (Plan 03-03)
- The workflow's Task() call must inject a `<role_definition>` block from TEAM.md and an `<inputs>` block with `artifact_path`
- The 7-field JSON output from gsd-reviewer.md conforms to `schemas/finding-schema.md` — Phase 4 synthesizer can consume it directly
- Phase 4 (gsd-review-synthesizer.md) will consume the `findings` arrays from all parallel reviewer instances — each reviewer's unique ID prefix (SEC-001, LAW-001, PERF-001) prevents ID collisions

---
*Phase: 03-single-reviewer-finding-schema*
*Completed: 2026-02-26*

## Self-Check: PASSED

- FOUND: agents/gsd-reviewer.md
- FOUND: .planning/phases/03-single-reviewer-finding-schema/03-02-SUMMARY.md
- FOUND: commit de020bb
