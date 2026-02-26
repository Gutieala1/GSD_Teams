---
phase: 04-parallel-pipeline-synthesizer-routing
plan: "02"
subsystem: review-pipeline
tags: [synthesizer, deduplication, routing, findings, gsd-agent]

# Dependency graph
requires:
  - phase: 03-single-reviewer-finding-schema
    provides: finding-schema.md (7-field JSON contract), gsd-reviewer.md (structural template for synthesizer)
provides:
  - agents/gsd-review-synthesizer.md — deduplication + routing synthesis agent
affects:
  - 04-03-PLAN (synthesize step in review-team.md invokes this agent)
  - workflows/review-team.md (spawns synthesizer via Task())

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Source traceability via source_finding_ids array — every synthesized finding traces to at least one reviewer input finding ID"
    - "synthesis_note field as sanctioned outlet for cross-finding pattern observations (not as new findings)"
    - "SYNTH-NNN sequential ID format for synthesizer output findings"
    - "Semantic deduplication — same root cause across different domain framings collapsed into one unique finding"
    - "Higher-severity-wins merge rule — when deduplicating, keep the higher severity of the merged pair"
    - "synthesis_errors self-reporting array — synthesizer flags its own traceability violations for workflow enforcement"

key-files:
  created:
    - agents/gsd-review-synthesizer.md
  modified: []

key-decisions:
  - "Synthesizer prohibited from reading files — ONLY input is combined_findings in prompt tags (no file I/O)"
  - "No-new-findings guard appears in both role block AND critical_rules — double enforcement at agent level"
  - "synthesis_note field is the sanctioned outlet for cross-finding observations — never add them as unique_findings"
  - "synthesis_errors array for self-reporting traceability violations — workflow catches and handles"
  - "SYNTH-NNN uniform ID format for all synthesizer output regardless of whether finding was deduped or pass-through"
  - "Overall routing computed as highest-priority across all unique_findings routing_summary — deterministic cascade"

patterns-established:
  - "Pattern: GSD 6-part agent structure (frontmatter, role, core_principle, numbered steps, output, critical_rules + success_criteria)"
  - "Pattern: Combined findings injected via <combined_findings> prompt tags — no intermediate file writes"
  - "Pattern: Self-validate step (Step 4) inside agent — agent checks its own output integrity before returning"

# Metrics
duration: 1min
completed: 2026-02-26
---

# Phase 4 Plan 02: gsd-review-synthesizer.md Summary

**GSD review synthesizer agent with semantic deduplication, source_finding_ids traceability guard, and severity-based routing cascade for cross-reviewer findings**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-26T02:49:59Z
- **Completed:** 2026-02-26T02:51:06Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `agents/gsd-review-synthesizer.md` following the full GSD 6-part agent convention (same structure as `gsd-reviewer.md`)
- No-new-findings guard enforced at two levels: `<role>` block critical mindset and `<critical_rules>` rule 1
- Four-step synthesis process: parse input → semantic dedup → per-finding routing → self-validate traceability
- `synthesis_note` field documented as the sanctioned outlet for pattern observations that must not become new findings
- `synthesis_errors` self-reporting array for traceability violations the workflow will catch

## Task Commits

Each task was committed atomically:

1. **Task 1: Create agents/gsd-review-synthesizer.md with 6-part GSD agent structure** - `bec950e` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `agents/gsd-review-synthesizer.md` — Deduplication + routing synthesis agent spawned by review-team workflow after all parallel reviewers complete

## Decisions Made

- **Synthesizer is read-only from prompt context only** — ONLY input is `<combined_findings>` tags, no file reads. Keeps synthesizer isolated from any file system state, matching the spirit of reviewer isolation.
- **No-new-findings guard in both role block and critical_rules** — Double enforcement at the agent instruction level ensures the constraint is visible at the top of the agent (role mindset) and at the enforcement layer (critical rules).
- **synthesis_note as the safety valve** — Rather than suppressing cross-finding patterns entirely, the `synthesis_note` field on the root output gives the synthesizer a structured outlet that the workflow can surface without creating traceability problems.
- **Self-validate step (Step 4) inside agent** — The agent asserts its own traceability before returning, populating `synthesis_errors` if violations found. The workflow performs the authoritative check independently, but the agent-level check catches obvious errors.
- **SYNTH-NNN uniform IDs** — All synthesizer output findings use SYNTH-NNN regardless of whether they were deduplicated or passed through unchanged. Source traceability is preserved via `source_finding_ids`, not ID format.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `agents/gsd-review-synthesizer.md` is ready to be spawned by the `synthesize` step in `workflows/review-team.md`
- Plan 04-03 implements that synthesize step, invoking this agent via Task() with `<combined_findings>` injection
- The agent's output JSON schema (unique_findings, routing_summary, overall_routing, reviewer_coverage, dedup_count, synthesis_note, synthesis_errors) is the contract Plan 04-03 must parse and act on

---
*Phase: 04-parallel-pipeline-synthesizer-routing*
*Completed: 2026-02-26*

## Self-Check: PASSED

- FOUND: agents/gsd-review-synthesizer.md
- FOUND: commit bec950e
- FOUND: .planning/phases/04-parallel-pipeline-synthesizer-routing/04-02-SUMMARY.md
