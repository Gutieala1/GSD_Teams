---
phase: 04-parallel-pipeline-synthesizer-routing
plan: "01"
subsystem: workflows
tags: [parallel-spawning, reviewer-pipeline, findings-collection, review-team]
dependency_graph:
  requires:
    - 03-03-SUMMARY.md (Phase 3 single-reviewer spawn_reviewers baseline)
    - schemas/finding-schema.md (7-field finding JSON schema)
  provides:
    - Parallel reviewer spawning for all TEAM.md roles in a single orchestrator message
    - combined_findings JSON structure consumed by synthesize step (04-03)
    - Zero-findings early exit path with REVIEW-REPORT.md write
    - Phase 4 PIPELINE COMPLETE return_status format
  affects:
    - workflows/review-team.md (spawn_reviewers and return_status steps updated)
tech_stack:
  added: []
  patterns:
    - Parallel Task() spawning in a single orchestrator message (PIPE-01 compliance)
    - combined_findings flat array merge with per_reviewer count tracking
    - Zero-findings early exit via REVIEW-REPORT.md write and synthesize skip
    - Pitfall 7 guard: WARNING log if TEAM.md roles differ between validate_team and spawn_reviewers re-read
key_files:
  created: []
  modified:
    - workflows/review-team.md
decisions:
  - "[04-01]: spawn_reviewers reads ALL TEAM.md roles in a single Read before issuing any Task() — single source of truth for role_definitions"
  - "[04-01]: Explicit 'SINGLE MESSAGE' instruction in spawn_reviewers to enforce PIPE-01 parallel execution guarantee"
  - "[04-01]: combined_findings uses flat all_findings array (not nested-by-reviewer) — synthesizer semantic dedup easier on flat structure"
  - "[04-01]: Zero-findings early exit writes REVIEW-REPORT.md and skips synthesize entirely — log_and_continue is correct for 0 findings with no synthesis overhead"
  - "[04-01]: return_status updated to PIPELINE COMPLETE — removes all Phase 3 placeholder language, adds FINAL_ROUTING + REVIEW-REPORT.md path + routing-conditional outcome messaging"
  - "[04-01]: REVIEW-REPORT.md written by spawn_reviewers (zero-findings path) and synthesize step (non-zero path) — not by gsd-review-synthesizer.md agent"
metrics:
  duration: "~2 min"
  completed: "2026-02-26"
  tasks: 2
  files: 1
---

# Phase 4 Plan 01: Parallel Reviewer Spawning + Combined Findings Summary

**One-liner:** Replaced Phase 3 single-reviewer spawn with full parallel Task() spawning of all TEAM.md roles in a single orchestrator message, collecting merged combined_findings JSON for synthesis, with zero-findings early exit and Phase 4 PIPELINE COMPLETE return_status format.

## What Was Done

### Task 1: Replace spawn_reviewers with Parallel Task() Spawning

Replaced the entire `<step name="spawn_reviewers">` block in `workflows/review-team.md`. The Phase 3 step selected only `roles_list[0]` (single reviewer). The Phase 4 step:

**Part A — Extract All Role Definitions:**
- Reads `.planning/TEAM.md` once using the Read tool
- For each role_name in `roles_list`, extracts the full section from `## Role: {role_name}` header to next `## Role:` header (or EOF)
- Stores as `role_definitions[role_name]` — all definitions populated before any spawning begins
- Pitfall 7 guard: if re-read TEAM.md produces different roles list, logs WARNING and uses re-read list as authoritative

**Part B — Parallel Spawn:**
- Explicit instruction: "Issue ALL of the following Task() calls in a SINGLE MESSAGE — do not await between them."
- One Task() block per role_name in roles_list, each receiving only ARTIFACT_PATH + its own role_definition
- Note: "For 3 starter roles: 3 Task() blocks issued together."

**Part C — Collect and Merge Findings:**
- After ALL reviewer Tasks complete: parse each JSON return, log per-reviewer count
- Append all findings to combined_findings flat array
- Build combined_findings structure: `{ phase, plan, reviewer_count, all_findings: [...], per_reviewer: { role_name: { finding_count } } }`

**Part D — Zero Findings Early Exit:**
- If all_findings empty: log "all reviewers — 0 findings, routing to log_and_continue"
- Write empty plan section to `.planning/phases/${PHASE_ID}/REVIEW-REPORT.md` (create-or-append pattern)
- Proceed to return_status, skip synthesize step entirely

### Task 2: Update return_status to Phase 4 PIPELINE COMPLETE Format

Replaced the `<step name="return_status">` block. The Phase 3 step said "REVIEWER COMPLETE" with "[Phase 4 not yet implemented]" markers. The Phase 4 step:

- Uses "PIPELINE COMPLETE" header
- Fields: Phase, Plan, Reviewers fired (N + comma-separated names), Artifact, Findings (pre-synthesis total), Final routing, REVIEW-REPORT.md path
- Routing-conditional outcome messaging for all 4 routing destinations
- Documents: return_status is only reached after log_and_continue or after user responds to block_and_escalate; send_for_rework and send_to_debugger halt in synthesize before reaching return_status
- All "[Phase 4 not yet implemented]" language removed from this step

## Files Modified

| File | Change |
|------|--------|
| `workflows/review-team.md` | spawn_reviewers step replaced (Phase 3 → Phase 4 parallel); return_status step updated to PIPELINE COMPLETE format |

## Unchanged (Verified)

- `validate_team` step: unchanged
- `sanitize` step: unchanged
- `synthesize` step: "[Phase 4 -- not yet implemented]" placeholder intact for 04-03

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] `workflows/review-team.md` contains "Issue ALL of the following Task() calls in a SINGLE MESSAGE"
- [x] spawn_reviewers loops over `roles_list` (no `roles_list[0]`)
- [x] combined_findings structure with `all_findings` flat array is present
- [x] Zero-findings early exit with REVIEW-REPORT.md write is documented
- [x] synthesize step still contains "[Phase 4 -- not yet implemented]"
- [x] return_status uses "PIPELINE COMPLETE" (not "REVIEWER COMPLETE")
- [x] return_status includes FINAL_ROUTING, Reviewers fired count, REVIEW-REPORT.md path
- [x] No "[Phase 4 not yet implemented]" text in return_status
- [x] validate_team and sanitize steps are unchanged
- [x] Task 1 commit: 49f40f5
- [x] Task 2 commit: 3c616f6
