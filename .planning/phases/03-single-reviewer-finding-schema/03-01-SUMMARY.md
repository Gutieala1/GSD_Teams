---
phase: 03-single-reviewer-finding-schema
plan: "01"
subsystem: schema
tags: [finding-schema, json, severity-rubric, review-pipeline, reviewer, synthesizer]

# Dependency graph
requires:
  - phase: 02-sanitizer-artifact-schema
    provides: ARTIFACT.md format that reviewer agents consume
provides:
  - schemas/finding-schema.md — 7-field Finding JSON schema with severity rubric, tie-breaking rule, routing destinations, empty findings case, and ID generation rule
affects:
  - 03-02 (gsd-reviewer.md embeds this schema's field definitions and severity rubric)
  - 04-parallel-reviewer-synthesis (gsd-review-synthesizer.md consumes findings conforming to this schema)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Schema-as-document: standalone finding-schema.md serves as shared contract reference for reviewer and synthesizer agents"
    - "Evidence-grounded findings: evidence field requires character-for-character quote, not paraphrase"
    - "Severity rubric with anti-inflation check: tie-breaking rule anchors calibration"

key-files:
  created:
    - schemas/finding-schema.md
  modified: []

key-decisions:
  - "7-field schema (id, reviewer, domain, severity, evidence, description, suggested_routing) — minimum sufficient set from REVR-02/REVR-06, no SARIF overhead"
  - "Severity enum uses exact REVR-05 strings: critical/high/medium/low/info — 5 levels not 4"
  - "Evidence field requires character-for-character quote from ARTIFACT.md — paraphrase is explicitly not valid"
  - "Tie-breaking rule: when in doubt, go lower — anti-inflation check before finalizing any critical finding"
  - "Empty findings case (findings: []) documented as valid expected output, not reviewer failure"
  - "ID prefix derived from first 3-4 uppercase characters of role name: SEC, LAW, PERF for starter roles"

patterns-established:
  - "Schema document in schemas/ directory at repo root — alongside agents/, workflows/, templates/"
  - "All 4 routing destinations explicitly defined with usage guidance"

# Metrics
duration: 1min
completed: 2026-02-26
---

# Phase 3 Plan 01: Finding JSON Schema Summary

**7-field Finding JSON schema with 5-level severity rubric, tie-breaking anti-inflation rule, and routing destination reference — standalone contract document for reviewer and synthesizer agents**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-02-26T01:58:49Z
- **Completed:** 2026-02-26T01:59:51Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `schemas/finding-schema.md` as a standalone reference document at repo root
- Defined 7-field JSON schema (id, reviewer, domain, severity, evidence, description, suggested_routing) with full field-by-field constraints table
- Embedded 5-level severity rubric (critical/high/medium/low/info) with concrete examples per level and tie-breaking anti-inflation check
- Documented all 4 routing destinations with usage guidance
- Documented empty findings case as valid expected output
- Documented ID generation rule with role prefix derivation (SEC, LAW, PERF for starter roles)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create schemas/finding-schema.md** - `cfc3f96` (feat)

**Plan metadata:** (docs commit — recorded below)

## Files Created/Modified

- `schemas/finding-schema.md` - Standalone Finding JSON schema reference document with 8 sections: header, full schema example, field reference table, severity rubric, tie-breaking rule, routing destinations, empty findings case, ID generation rule

## Decisions Made

- **7-field schema subset:** Used minimum sufficient fields from REVR-02/REVR-06. Full SARIF-inspired schema from REVIEW-PIPELINE-DESIGN.md was available but Phase 3 scope is the 7-field subset only.
- **Exact REVR-05 severity strings:** Used `critical/high/medium/low/info` — 5 levels. The research confirmed REVR-05 specifies 5 levels (not the 4-level enum in REVIEW-PIPELINE-DESIGN.md).
- **Evidence field as hard requirement:** Character-for-character quote enforced by field constraints documentation — paraphrase explicitly declared invalid.
- **Anti-inflation check verbatim from plan:** Included the exact anti-inflation check language ("If you would not personally stop a production deploy for it, downgrade to high") as specified.
- **schemas/ directory created:** No `schemas/` directory existed at repo root — created alongside agents/, workflows/, templates/ as a deviation (Rule 3 - blocking issue resolved automatically).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created missing schemas/ directory**
- **Found during:** Task 1 (Create schemas/finding-schema.md)
- **Issue:** The plan specified `schemas/finding-schema.md` at repo root but the `schemas/` directory did not exist
- **Fix:** Created `schemas/` directory with `mkdir -p` before writing the file
- **Files modified:** schemas/ (new directory)
- **Verification:** File written successfully to schemas/finding-schema.md
- **Committed in:** cfc3f96 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix necessary for task completion. No scope creep — directory creation is a prerequisite for the file specified in the plan.

## Issues Encountered

None beyond the missing directory (handled as deviation Rule 3 above).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `schemas/finding-schema.md` is the contract reference for Plan 03-02 (gsd-reviewer.md) — schema fields and severity rubric will be embedded in the reviewer agent
- ID prefix convention (SEC, LAW, PERF) is established and documented — reviewer agent can reference this
- Empty findings case documented — review-team.md workflow update in Plan 03-03 must handle `{"findings": []}` gracefully
- Phase 4 (gsd-review-synthesizer.md) can use this schema as the contract for consuming reviewer output

---
*Phase: 03-single-reviewer-finding-schema*
*Completed: 2026-02-26*

## Self-Check: PASSED

- FOUND: schemas/finding-schema.md
- FOUND: commit cfc3f96
