---
phase: 04-parallel-pipeline-synthesizer-routing
plan: "03"
subsystem: review-pipeline
tags: [synthesizer, routing, review-report, findings, deduplication, block-and-escalate, gsd-workflow]

# Dependency graph
requires:
  - phase: 04-01
    provides: spawn_reviewers parallel Task() dispatch + combined_findings JSON built in workflow
  - phase: 04-02
    provides: agents/gsd-review-synthesizer.md — deduplication + routing synthesis agent
provides:
  - workflows/review-team.md synthesize step — full 5-part implementation replacing placeholder
  - REVIEW-REPORT.md append writer on all routing paths
  - Four routing destinations: block_and_escalate, send_for_rework, send_to_debugger, log_and_continue
affects:
  - Phase 5 (patch reapply) — synthesize step is now stable and complete in review-team.md
  - All future plan executions that trigger the review pipeline

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deterministic routing override — workflow checks critical severity BEFORE reading synthesizer.overall_routing (hardcoded minimum)"
    - "Read-then-Write append for REVIEW-REPORT.md — prevents overwrite on second and later plan sections"
    - "REVIEW-REPORT.md written on ALL routing paths including block_and_escalate (before acting on route)"
    - "source_finding_ids validation in workflow code as authoritative traceability check (independent of agent self-check)"
    - "block_and_escalate overrides auto_advance mode — AskUserQuestion gate always required"
    - "Fallback routing on validation failure — use raw combined_findings.all_findings un-deduplicated"

key-files:
  created: []
  modified:
    - workflows/review-team.md

key-decisions:
  - "REVIEW-REPORT.md uses Read-then-Write append — not overwrite. Existing content preserved on second and later plans."
  - "Critical severity check BEFORE reading synthesizer.overall_routing — deterministic workflow-level override, not agent judgment"
  - "block_and_escalate always requires user decision via AskUserQuestion — overrides auto_advance mode"
  - "return_status only reached after log_and_continue or after user responds to block_and_escalate — send_for_rework and send_to_debugger halt without reaching it"
  - "source_finding_ids validation in workflow performs independent traceability check from agent self-check — defense in depth"
  - "Fallback on validation failure uses raw combined_findings.all_findings (un-deduplicated) with severity-based routing"

patterns-established:
  - "Pattern: Write-before-act — REVIEW-REPORT.md written before acting on FINAL_ROUTING, ensuring findings are logged even if execution halts"
  - "Pattern: Severity-minimum enforcement — workflow code independently checks critical before delegating routing to synthesizer output"
  - "Pattern: Fail-safe fallback — validation failure degrades gracefully to raw findings rather than failing the pipeline"

# Metrics
duration: ~2min
completed: 2026-02-25
---

# Phase 4 Plan 03: Synthesize Step + Routing + REVIEW-REPORT.md Summary

**Synthesize step replacing Phase 4 placeholder: synthesizer spawn via Task(), source_finding_ids traceability validation, deterministic critical-severity routing override, REVIEW-REPORT.md Read-then-Write append on all 4 routing paths**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-25T00:00:00Z
- **Completed:** 2026-02-25T00:02:00Z
- **Tasks:** 1 (+ checkpoint verification)
- **Files modified:** 1

## Accomplishments

- Replaced the `[Phase 4 -- not yet implemented]` placeholder in `workflows/review-team.md` synthesize step with the full 5-part implementation
- Part A: Synthesizer spawned via `Task(subagent_type="gsd-review-synthesizer")` with `<combined_findings>` injection (not a file path)
- Part B: source_finding_ids validation loop — workflow performs independent traceability check before routing, with fallback to raw combined_findings on failure
- Part C: Deterministic routing override — `any unique_finding.severity == "critical"` checked BEFORE reading `synthesizer.overall_routing`; critical always forces `block_and_escalate`
- Part D: REVIEW-REPORT.md written on ALL routing paths (including block_and_escalate) before acting on route, using Read-then-Write append pattern
- Part E: All four routing destinations implemented — `block_and_escalate` (AskUserQuestion gate), `send_for_rework` (halt + guidance), `send_to_debugger` (halt + /gsd:debug guidance), `log_and_continue` (no halt)
- Phase 4 pipeline complete end-to-end: parallel reviewer dispatch → synthesis → routing → REVIEW-REPORT.md

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement synthesize step — synthesizer spawn, validation, routing enforcement, REVIEW-REPORT.md write, routing actions** - `06b5fae` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `workflows/review-team.md` — synthesize step (Step 4) fully implemented, replacing `[Phase 4 -- not yet implemented]` placeholder. Contains all 5 parts: synthesizer spawn, source_finding_ids validation, deterministic routing override, REVIEW-REPORT.md append writer, and 4 routing action handlers.

## Decisions Made

- **Read-then-Write append for REVIEW-REPORT.md** — The implementation reads the existing file first (if present), appends the new plan section, then writes back in full. This prevents overwriting prior plan sections when REVIEW-REPORT.md already exists from an earlier plan run. Critical for SYNTH-05 correctness.

- **Critical severity check BEFORE synthesizer.overall_routing** — The workflow performs `HAS_CRITICAL = any unique_finding where severity == "critical"` independently before reading the synthesizer's routing suggestion. This is a hardcoded workflow-level minimum, not a synthesizer judgment call. Matches the SYNTH-03 design requirement.

- **block_and_escalate requires user decision — always** — AskUserQuestion gate is used and execution does NOT continue until user responds. This overrides any auto_advance workflow mode. The routing is too consequential to bypass.

- **return_status only after log_and_continue or user-decided block_and_escalate** — send_for_rework and send_to_debugger halt in the synthesize step and do NOT call return_status. The step-5 return_status block documents this contract explicitly.

- **Fallback on source_finding_ids validation failure** — When the workflow detects any traceability violation (empty source_finding_ids, or source_id not in input_ids), it falls back to using combined_findings.all_findings directly (un-deduplicated) and routes based on highest severity in raw findings. This keeps the pipeline recoverable when the synthesizer produces invalid output.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 4 is complete. The full review pipeline is implemented end-to-end:
  - Phase 1: GSD hook integration + review_team_gate in execute-plan.md
  - Phase 2: Sanitizer agent + sanitize step in review-team.md
  - Phase 3: Single-reviewer gsd-reviewer.md + spawn_reviewers (single)
  - Phase 4: Parallel reviewer dispatch, gsd-review-synthesizer.md agent, synthesize step with routing
- Phase 5 (patch reapply workflow) can now reference a stable synthesize step in review-team.md
- REVIEW-REPORT.md will be created per-phase at `.planning/phases/${PHASE_ID}/REVIEW-REPORT.md` on first plan completion

---
*Phase: 04-parallel-pipeline-synthesizer-routing*
*Completed: 2026-02-25*

## Self-Check: PASSED

- FOUND: workflows/review-team.md (synthesize step implementation verified)
- FOUND: commit 06b5fae (feat(04-03): implement synthesize step)
- FOUND: .planning/phases/04-parallel-pipeline-synthesizer-routing/04-03-SUMMARY.md
