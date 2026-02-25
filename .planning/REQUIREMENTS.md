# Requirements: GSD Review Team

**Defined:** 2026-02-25
**Core Value:** Catch compounding AI errors at the plan boundary — before they become the foundation for the next plan.

## v1 Requirements

### Pipeline Core

- [ ] **PIPE-01**: Review pipeline fires automatically after each plan in execute-phase when `workflow.review_team: true` and `.planning/TEAM.md` exists
- [ ] **PIPE-02**: Pipeline gracefully no-ops (logs skip reason) when toggle is off or TEAM.md is missing — execution continues normally
- [ ] **PIPE-03**: Pipeline hooks into execute-plan.md between `update_codebase_map` and `offer_next` steps via pattern-based insertion
- [ ] **PIPE-04**: Minor/log findings do not block execution — pipeline logs and continues automatically
- [ ] **PIPE-05**: Critical findings halt execution and surface to user with full finding context for decision

### Sanitization

- [ ] **SAND-01**: Sanitizer strips executor reasoning, internal thought process, confidence language, and alternatives considered from SUMMARY.md
- [ ] **SAND-02**: Sanitizer preserves exact file paths, implemented behavior (what, not why), stack changes, API contracts, key decisions, and config changes
- [ ] **SAND-03**: Sanitized artifact written to disk as `{phase}-{plan}-ARTIFACT.md` in the phase directory for audit trail
- [ ] **SAND-04**: Reviewers receive ONLY the sanitized artifact — never the raw SUMMARY.md, PLAN.md, prior summaries, or any executor context

### Reviewers

- [ ] **REVR-01**: All reviewer agents spawned via Task() in a single orchestrator turn (true parallelism — no sequential chaining)
- [ ] **REVR-02**: Each reviewer receives only two inputs: the sanitized artifact and their own role definition from TEAM.md
- [ ] **REVR-03**: Reviewer agent file (gsd-reviewer.md) includes an explicit `not_responsible_for` list as a DO NOT guard — isolation is enforced, not implied
- [ ] **REVR-04**: Each finding must include a direct quote from the artifact as evidence — no quoted evidence means no finding reported
- [ ] **REVR-05**: Findings use three severity levels (critical / major / minor) with a calibration rubric and tie-breaking rule ("when in doubt, go lower")
- [ ] **REVR-06**: Reviewer output is structured JSON matching the project's finding schema (id, reviewer, domain, severity, evidence, description, suggested_routing)

### Synthesizer

- [ ] **SYNTH-01**: Synthesizer collects all reviewer findings and deduplicates cross-reviewer overlap before routing
- [ ] **SYNTH-02**: Synthesizer is explicitly prohibited from generating new findings — every finding in output must trace to a reviewer source
- [ ] **SYNTH-03**: Routing is deterministic: `critical severity → block_and_escalate` is hardcoded minimum — TEAM.md routing hints may elevate but never lower
- [ ] **SYNTH-04**: All 4 routing destinations implemented: `block_and_escalate`, `send_for_rework`, `send_to_debugger`, `log_and_continue`
- [ ] **SYNTH-05**: All findings (including log-only) written to `{phase-dir}/REVIEW-REPORT.md` with per-plan section headers to prevent collision

### TEAM.md

- [ ] **TEAM-01**: TEAM.md stored at `.planning/TEAM.md` — follows GSD `.planning/` conventions, tracked with planning docs
- [ ] **TEAM-02**: Each role definition captures: name, focus area, review criteria/checklist, severity thresholds (with examples), and routing hints
- [ ] **TEAM-03**: Pipeline validates TEAM.md exists and has at least one reviewer before running — clear error if missing
- [ ] **TEAM-04**: TEAM.md starter template ships with the extension (pre-populated with 3 example roles)

### Role Builder

- [ ] **ROLE-01**: `/gsd:new-reviewer` command guides user through role creation via adaptive AskUserQuestion conversation
- [ ] **ROLE-02**: Role builder follows GSD questioning conventions: ≤12 char headers, 2–4 options per question, decision gate before writing
- [ ] **ROLE-03**: Role builder appends completed role definition to `.planning/TEAM.md` — creates TEAM.md if it doesn't exist
- [ ] **ROLE-04**: 3 built-in starter role templates available as a starting point: Security Auditor, Performance Analyst, Rules Lawyer

### GSD Integration

- [ ] **INT-01**: `workflow.review_team` field added to `.planning/config.json` (default: `false`) — existing projects unaffected until opt-in
- [ ] **INT-02**: `/gsd:settings` shows Review Team as a new toggle alongside existing workflow toggles
- [ ] **INT-03**: execute-plan.md patch uses pattern-based insertion anchored on `<step name="offer_next">` — not line numbers, safe across GSD versions
- [ ] **INT-04**: No modification to gsd-tools.cjs — `workflow.review_team` read via `jq` on existing `config_content` from init JSON
- [ ] **INT-05**: settings.md patch spreads existing workflow keys when writing config — prevents silently dropping `review_team` on `/gsd:settings` run

### Installation

- [ ] **INST-01**: `install.sh` copies all extension files to `~/.claude/get-shit-done/` and applies the execute-plan.md patch
- [ ] **INST-02**: `install.sh` uses pattern-based insertion — no hardcoded line numbers — compatible across GSD v1.19.x minor versions
- [ ] **INST-03**: README.md documents: installation steps, post-`/gsd:update` reapply-patches procedure, TEAM.md setup, and first-run walkthrough
- [ ] **INST-04**: Extension verifies GSD version compatibility range at install time and warns on mismatch

## v2 Requirements

### Extended Role Library

- **RLIB-01**: Built-in role library beyond the 3 starters (Accessibility Auditor, Test Coverage Analyst, Documentation Reviewer)
- **RLIB-02**: Role marketplace / community-contributed roles via GitHub

### Advanced Pipeline

- **ADV-01**: Cross-phase finding correlation — track whether a finding recurs across multiple plans
- **ADV-02**: Finding ID persistence across reviews (e.g., `SEC-001-P2-PL3` format) for traceability
- **ADV-03**: OWASP LLM01 prompt injection detection in sanitizer — sanitize adversarial patterns embedded in reviewed code
- **ADV-04**: Review summary surfaced in `/gsd:progress` output

### Tooling

- **TOOL-01**: `/gsd:review-report` command to view aggregated findings across all phases
- **TOOL-02**: Severity trend analysis — detect if a reviewer is escalating everything (inflation detection)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Modification to gsd-tools.cjs | Unnecessary — jq on config_content is sufficient; avoids maintenance dependency on GSD binary |
| Auto-fixing code based on findings | Pipeline routes findings to the right agent; it does not mutate code itself |
| Real-time review during task execution | Review fires at plan boundary (after SUMMARY.md); intra-task review is out of scope for v1 |
| Web UI for TEAM.md management | File-based, text editor — follows GSD conventions |
| Merge into GSD core | Ships as standalone community extension first; core merge is a GSD maintainer decision |
| Review of .planning/ artifacts | Pipeline reviews execution output only — not plans, roadmaps, or requirements |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INT-01 | Phase 1 | Pending |
| INT-02 | Phase 1 | Pending |
| INT-03 | Phase 1 | Pending |
| INT-04 | Phase 1 | Pending |
| INT-05 | Phase 1 | Pending |
| PIPE-02 | Phase 1 | Pending |
| PIPE-03 | Phase 1 | Pending |
| TEAM-01 | Phase 1 | Pending |
| TEAM-04 | Phase 1 | Pending |
| INST-01 | Phase 1 | Pending |
| INST-02 | Phase 1 | Pending |
| SAND-01 | Phase 2 | Pending |
| SAND-02 | Phase 2 | Pending |
| SAND-03 | Phase 2 | Pending |
| SAND-04 | Phase 2 | Pending |
| TEAM-03 | Phase 2 | Pending |
| REVR-01 | Phase 3 | Pending |
| REVR-02 | Phase 3 | Pending |
| REVR-03 | Phase 3 | Pending |
| REVR-04 | Phase 3 | Pending |
| REVR-05 | Phase 3 | Pending |
| REVR-06 | Phase 3 | Pending |
| PIPE-01 | Phase 4 | Pending |
| PIPE-04 | Phase 4 | Pending |
| PIPE-05 | Phase 4 | Pending |
| SYNTH-01 | Phase 4 | Pending |
| SYNTH-02 | Phase 4 | Pending |
| SYNTH-03 | Phase 4 | Pending |
| SYNTH-04 | Phase 4 | Pending |
| SYNTH-05 | Phase 4 | Pending |
| ROLE-01 | Phase 5 | Pending |
| ROLE-02 | Phase 5 | Pending |
| ROLE-03 | Phase 5 | Pending |
| ROLE-04 | Phase 5 | Pending |
| TEAM-02 | Phase 5 | Pending |
| INST-03 | Phase 5 | Pending |
| INST-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 37 total
- Mapped to phases: 37
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-25*
*Last updated: 2026-02-25 — initial definition*
