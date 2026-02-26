# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** Catch compounding AI errors at the plan boundary — before they become the foundation for the next plan.
**Current focus:** Phase 3 in progress — 03-02 gsd-reviewer agent complete, ready for 03-03 review-team workflow update

## Current Position

Phase: 3 of 5 (Single Reviewer + Finding Schema)
Plan: 3 of 3 in current phase
Status: 03-02 complete — gsd-reviewer parameterized agent created
Last activity: 2026-02-26 — Completed 03-02 gsd-reviewer agent

Progress: [███████░░░] 67%

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: ~1.5 min
- Total execution time: ~10 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-extension-scaffold-gsd-integration | 4 | ~5 min | ~1.25 min |
| Phase 01-extension-scaffold-gsd-integration P01 | 8 | 2 tasks | 5 files |
| Phase 01-extension-scaffold-gsd-integration P02 | 8 | 2 tasks | 4 files |
| Phase 01-extension-scaffold-gsd-integration P03 | 2 | 1 task | 1 file |
| Phase 01-extension-scaffold-gsd-integration P04 | 2 | 1 task | 4 files |
| Phase 02-sanitizer-artifact-schema P01 | 2 | 1 task | 1 file |
| Phase 02-sanitizer-artifact-schema P02 | 2 | 1 task | 1 file |
| Phase 03-single-reviewer-finding-schema P01 | 1 | 1 tasks | 1 files |
| Phase 03-single-reviewer-finding-schema P02 | 3 | 1 task | 1 file |

## Accumulated Context

### Decisions

Key architectural decisions from project initialization:

- **Init**: Hook point confirmed — `review_team_gate` step between `update_codebase_map` and `offer_next` in execute-plan.md
- **Init**: No gsd-tools.cjs modification needed — `workflow.review_team` readable via `jq` on existing `config_content`
- **Init**: Sanitizer is the real isolation gate — Task() isolation is automatic, but the only contamination vector is the orchestrator passing executor content into reviewer prompts
- **Init**: Routing is deterministic in workflow code — `critical → block_and_escalate` is hardcoded minimum, not a synthesizer judgment call
- **Init**: Synthesizer prohibited from generating new findings — every finding must trace to a reviewer source
- **Init**: Pattern-based patch insertion anchored on `<step name="offer_next">` — safe across GSD version updates
- **01-01**: Roles fully visible (not HTML-commented) in TEAM.md for easier onboarding
- **01-01**: YAML fenced code blocks inside role sections are machine-readable anchors for Phase 2 parser
- **01-01**: Three starter roles ship: Security Auditor, Rules Lawyer, Performance Analyst — covers security/correctness/performance review lanes
- **01-02**: Anchor `<step name="offer_next">` confirmed unique and stable — str.replace() with count=1 is safe
- **01-02**: Idempotency guard uses content check (`name="review_team_gate"`) — not line numbers, resilient to file changes
- **01-02**: review_team_gate reads CONFIG_CONTENT already in scope — no re-read, no gsd-tools.cjs changes needed
- **01-02**: Three-branch gate logic: disabled (silent no-op) | TEAM.md missing (log+continue) | TEAM.md present (load @workflow)
- **01-03**: Touch point 1 anchor covers full closing block (Per Milestone line + closing brackets + ])) to ensure correct insertion before AskUserQuestion closing
- **01-03**: Two distinct spread variable names — update_config uses existing_config.workflow, save_as_defaults uses existing_workflow (different execution contexts in settings.md)
- **01-03**: WARN on anchor not found (not ERROR) — allows partial application when settings.md has evolved, informs operator which touch points need attention
- **01-04**: jq is optional — python3 json module fallback used for config.json update; avoids hard dependency since python3 already required
- **01-04**: GSD_DIR = $HOME/.claude (parent of get-shit-done/) for clean subpath construction in all references
- **01-04**: EXT_INSTALL_DIR = $GSD_DIR/get-shit-done-review-team — matches @-reference path in review_team_gate step
- **02-01**: Sanitizer uses Read + Write tools only — minimal tool surface for content-transform agent
- **02-01**: ARTIFACT.md includes YAML frontmatter (phase, plan, source, generated) for machine parsing and audit trail
- **02-01**: Mixed fact+reasoning sentences split at reasoning boundary — factual prefix preserved, reasoning suffix stripped
- **02-01**: Completeness check runs before write: file path audit, section population, stack change audit, reasoning leak scan
- **02-01**: Inputs passed via `<inputs>` tags (summary_path, artifact_path, phase, plan, plan_name)
- **02-02**: Workflow uses GSD workflow conventions (purpose/inputs/step blocks), not agent YAML frontmatter
- **02-02**: Three-condition role validation: ## Role: header + YAML name: field + review criteria items
- **02-02**: Sanitizer @-reference uses canonical extension path: @~/.claude/get-shit-done-review-team/agents/gsd-review-sanitizer.md
- **02-02**: ARTIFACT.md path follows {phase}-{plan}-ARTIFACT.md convention matching SUMMARY.md naming
- **02-02**: Phase 3/4 steps are documented placeholders with clear '[not yet implemented]' markers
- [Phase 03-01]: 7-field schema (id, reviewer, domain, severity, evidence, description, suggested_routing) — minimum sufficient set from REVR-02/REVR-06, no SARIF overhead
- [Phase 03-01]: Severity enum uses exact REVR-05 strings: critical/high/medium/low/info — 5 levels, not the 4-level enum in REVIEW-PIPELINE-DESIGN.md
- [Phase 03-01]: Evidence field requires character-for-character quote from ARTIFACT.md — paraphrase is explicitly not valid
- [Phase 03-01]: Tie-breaking rule: when in doubt, go lower — anti-inflation check before finalizing any critical finding
- [Phase 03-01]: ID prefix derived from first 3-4 uppercase characters of role name: SEC, LAW, PERF for starter roles
- [Phase 03-02]: Single parameterized agent file serves all reviewer roles — role name, domain, checklist, not_responsible_for, and ID prefix extracted from <role_definition> tags at spawn time
- [Phase 03-02]: Tools: Read and Write only for gsd-reviewer — content analyst, not code inspector (no Bash, no Grep)
- [Phase 03-02]: Two-layer domain confinement — not_responsible_for in <role> block + DO NOT in critical_rule #3
- [Phase 03-02]: Empty findings array ({"findings": []}) is valid output, documented in both <output> and Step 4

### Pending Todos

None yet.

### Blockers/Concerns

- **Open**: Does AI merge in `reapply-patches` handle XML `<step>` blocks reliably across GSD version changes? (Test during Phase 1 — deferred: reapply-patches workflow is Phase 5)
- **Resolved (02-01)**: ARTIFACT.md written to disk at `.planning/phases/{phase_dir}/{phase}-{plan}-ARTIFACT.md` — audit trail, context efficiency, debuggability
- **Open**: REVIEW-REPORT.md per-phase vs. global — product decision for Phase 4

## Session Continuity

Last session: 2026-02-26
Stopped at: Completed 03-02-PLAN.md — gsd-reviewer parameterized agent (Phase 3, Plan 2 of 3)
Resume file: None
