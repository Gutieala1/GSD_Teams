# Roadmap: GSD Review Team

## Overview

Five phases building from the outside in: first wire the extension into GSD cleanly, then
build the sanitizer (the real isolation gate), then prove a single reviewer works before
multiplying to parallel, then add the synthesizer and routing, and finally open the system
to user configuration via /gsd:new-reviewer. Each phase validates the foundation before
the next phase builds on it — the order is not arbitrary.

## Phases

- [x] **Phase 1: Extension Scaffold + GSD Integration** — Install cleanly, toggle appears in settings, pipeline activates/no-ops correctly
- [x] **Phase 2: Sanitizer + Artifact Schema** — Zero executor reasoning leaks past the isolation gate
- [x] **Phase 3: Single Reviewer + Finding Schema** — One reviewer fires, produces structured evidence-backed findings, stays in its lane
- [x] **Phase 4: Parallel Pipeline + Synthesizer + Routing** — All reviewers run in parallel, synthesizer routes deterministically, REVIEW-REPORT.md populated
- [x] **Phase 5: /gsd:new-reviewer + Starter Roles + Docs** — Users can build roles, 3 starters ship, README documents everything

## Phase Details

### Phase 1: Extension Scaffold + GSD Integration
**Goal**: The extension installs cleanly into a GSD project. `workflow.review_team` toggle appears in `/gsd:settings`. The `review_team_gate` step is live in `execute-plan.md` — it activates when the toggle is on and TEAM.md exists, and gracefully no-ops with a logged reason when either is missing.
**Depends on**: Nothing (first phase)
**Requirements**: INT-01, INT-02, INT-03, INT-04, INT-05, PIPE-02, PIPE-03, TEAM-01, TEAM-04, INST-01, INST-02
**Success Criteria** (what must be TRUE):
  1. Running `bash install.sh` copies all extension files and patches execute-plan.md without errors
  2. `/gsd:settings` shows a "Review Team" toggle that writes `workflow.review_team` to config.json
  3. A plan execution with `review_team: true` but no TEAM.md logs "Review Team: skipped (no TEAM.md)" and continues normally
  4. A plan execution with `review_team: false` skips the gate entirely with no output
  5. `.planning/TEAM.md` starter template exists with 3 commented example roles
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Extension repo scaffold + templates/TEAM.md starter template (3 example roles)
- [x] 01-02-PLAN.md — scripts/patch-execute-plan.py (review_team_gate step, pattern-based insertion)
- [x] 01-03-PLAN.md — scripts/patch-settings.py (7th toggle + spread-safe config write, 4 touch points)
- [x] 01-04-PLAN.md — install.sh (GSD detection, file copy, patch invocation, TEAM.md guard, config update)

### Phase 2: Sanitizer + Artifact Schema
**Goal**: After each plan executes with review_team enabled and a TEAM.md present, a sanitized artifact is written to `{phase-dir}/{phase}-{plan}-ARTIFACT.md`. The artifact contains zero executor reasoning — only observable facts about what was built.
**Depends on**: Phase 1
**Requirements**: SAND-01, SAND-02, SAND-03, SAND-04, TEAM-03
**Success Criteria** (what must be TRUE):
  1. `gsd-review-sanitizer` agent reads SUMMARY.md and produces ARTIFACT.md with no reasoning language ("I decided", "I chose", "alternatively", confidence phrases)
  2. ARTIFACT.md contains all file paths, implemented behaviors, stack changes, and API contracts from SUMMARY.md
  3. `review-team.md` workflow reads TEAM.md, validates it has at least one reviewer, then spawns sanitizer
  4. If TEAM.md exists but has zero valid roles, pipeline halts with a clear error before sanitization
  5. ARTIFACT.md is readable as a standalone document — no references to SUMMARY.md or PLAN.md required
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md — gsd-review-sanitizer.md agent (6-part GSD structure, strip/preserve schema, completeness checks, DO NOT guards)
- [x] 02-02-PLAN.md — review-team.md workflow skeleton (TEAM.md validation + sanitizer Task() spawning + Phase 3/4 placeholders)

### Phase 3: Single Reviewer + Finding Schema
**Goal**: One reviewer role from TEAM.md fires successfully. It receives only the sanitized artifact and its own role definition. It produces at least one finding with a direct quote as evidence, assigns severity using the rubric, and stays strictly within its declared domain.
**Depends on**: Phase 2
**Requirements**: REVR-01, REVR-02, REVR-03, REVR-04, REVR-05, REVR-06
**Success Criteria** (what must be TRUE):
  1. Finding JSON schema defined: `{id, reviewer, domain, severity, evidence, description, suggested_routing}`
  2. `gsd-reviewer.md` agent includes `not_responsible_for` list as a DO NOT guard in its `<role>` block
  3. Reviewer output parses cleanly as JSON — no prose wrapping, no schema deviation
  4. Every finding in output contains a direct quote from ARTIFACT.md in the `evidence` field
  5. Severity rubric with tie-breaking rule ("when in doubt, go lower") is embedded in the reviewer agent
  6. `review-team.md` workflow spawns single reviewer via Task(), collects structured JSON return
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — schemas/finding-schema.md (7-field JSON schema + 5-level severity rubric + tie-breaking rule)
- [x] 03-02-PLAN.md — agents/gsd-reviewer.md (parameterized via role injection, isolation enforcement, evidence requirement, JSON output)
- [x] 03-03-PLAN.md — workflows/review-team.md update (spawn_reviewers implemented for single reviewer + JSON collection)

### Phase 4: Parallel Pipeline + Synthesizer + Routing
**Goal**: All reviewer roles in TEAM.md fire in a single Task() turn (true parallelism). The synthesizer collects findings, deduplicates, routes deterministically — critical findings block execution, major findings route to rework or debugger, minor findings log and continue. REVIEW-REPORT.md is populated after every reviewed plan.
**Depends on**: Phase 3
**Requirements**: PIPE-01, PIPE-04, PIPE-05, SYNTH-01, SYNTH-02, SYNTH-03, SYNTH-04, SYNTH-05
**Success Criteria** (what must be TRUE):
  1. All roles in TEAM.md are spawned in a single orchestrator turn — findings arrive as a set, not a stream
  2. `gsd-review-synthesizer.md` deduplicates cross-reviewer findings before routing
  3. A finding with severity `critical` always routes to `block_and_escalate` regardless of TEAM.md hints — hardcoded minimum
  4. `block_and_escalate` halts execute-plan and presents finding to user; execution does not continue until user decides
  5. `log_and_continue` appends finding to `{phase-dir}/REVIEW-REPORT.md` with per-plan section header and continues
  6. `send_for_rework` and `send_to_debugger` routing destinations are implemented and reachable
  7. Synthesizer output contains zero findings not traceable to a reviewer (no synthesizer-invented findings)
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — spawn_reviewers replacement: all TEAM.md roles in parallel (single-message Task() pattern) + combined findings collection
- [x] 04-02-PLAN.md — agents/gsd-review-synthesizer.md (dedup, no-new-findings guard via source_finding_ids, routing enum output)
- [x] 04-03-PLAN.md — synthesize step implementation: synthesizer spawn + validation + deterministic routing enforcement + REVIEW-REPORT.md writer + all 4 routing actions

### Phase 5: /gsd:new-reviewer + Starter Roles + Docs
**Goal**: Users can run `/gsd:new-reviewer` and get a working reviewer role written to TEAM.md through a guided conversation. Three production-ready starter roles ship with the extension. README documents installation, usage, and the post-update workflow.
**Depends on**: Phase 4
**Requirements**: ROLE-01, ROLE-02, ROLE-03, ROLE-04, TEAM-02, INST-03, INST-04
**Success Criteria** (what must be TRUE):
  1. `/gsd:new-reviewer` walks through questioning (domain → criteria → severity → routing hints) and writes a valid role to TEAM.md
  2. Role builder follows GSD questioning conventions: headers ≤12 chars, 2–4 options, decision gate before writing
  3. Security Auditor, Performance Analyst, and Rules Lawyer starter roles are complete and usable with no modification
  4. README.md contains: installation steps, post-`/gsd:update` reapply-patches procedure, TEAM.md format reference, first-run walkthrough
  5. `install.sh` checks GSD version and warns if outside the tested compatibility range
**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md — Fix 3 starter roles: remove "Example role" callouts, generalize Rules Lawyer criterion (both templates/TEAM.md and .planning/TEAM.md)
- [x] 05-02-PLAN.md — workflows/new-reviewer.md (7-step guided workflow) + commands/gsd/new-reviewer.md (slash command entry point)
- [x] 05-03-PLAN.md — README.md (installation, post-update, TEAM.md format, first-run) + install.sh version check + commands/gsd copy

## Progress

**Execution Order:** 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Extension Scaffold + GSD Integration | 4/4 | Complete | 2026-02-26 |
| 2. Sanitizer + Artifact Schema | 2/2 | Complete | 2026-02-26 |
| 3. Single Reviewer + Finding Schema | 3/3 | Complete | 2026-02-26 |
| 4. Parallel Pipeline + Synthesizer + Routing | 3/3 | Complete | 2026-02-25 |
| 5. /gsd:new-reviewer + Starter Roles + Docs | 3/3 | Complete | 2026-02-25 |
