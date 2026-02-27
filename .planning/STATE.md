# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-26)

**Core value:** Catch compounding AI errors at the plan boundary — before they become the foundation for the next plan.
**Current focus:** v2.0 Agent Studio — evolving the review pipeline into a full project-aware agent studio

## Current Position

Phase: 06-team-md-v2-schema-config-foundation
Plan: 02 (complete)
Status: Executing phase 06 — 2 of N plans complete
Last activity: 2026-02-27 — Completed 06-02-PLAN.md (agent_studio patch script + install.sh extension)

Progress: [░░░░░░░░░░] v2.0 — phase 06 in progress

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
| Phase 03-single-reviewer-finding-schema P03 | 1 | 1 task | 1 file |
| Phase 04-parallel-pipeline-synthesizer-routing P01 | 2 | 2 tasks | 1 file |
| Phase 04-parallel-pipeline-synthesizer-routing P02 | 1 | 1 tasks | 1 files |
| Phase 04-parallel-pipeline-synthesizer-routing P03 | 2 | 1 task | 1 file |
| Phase 05-new-reviewer-starter-roles-docs P01 | 1 | 1 tasks | 2 files |
| Phase 05-new-reviewer-starter-roles-docs P02 | 2 | 2 tasks | 2 files |
| Phase 05-new-reviewer-starter-roles-docs P03 | ~10 | 2 tasks | 2 files |
| Phase 06-team-md-v2-schema-config-foundation P01 | ~2 | 2 tasks | 2 files |
| Phase 06-team-md-v2-schema-config-foundation P02 | 2 | 2 tasks | 2 files |

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
- [Phase 03-03]: spawn_reviewers selects first valid role via roles_list[0] — deterministic Phase 3 single-reviewer scope
- [Phase 03-03]: TEAM.md re-read in spawn_reviewers to extract full role section (## Role: header to next ## Role: or EOF) as role_definition_text
- [Phase 03-03]: ARTIFACT_PATH reused from sanitize step in spawn_reviewers — not recomputed (single source of truth)
- [Phase 03-03]: Empty findings handled as valid pipeline exit: log '0 findings (no issues in domain)' and continue — not an error
- [Phase 03-03]: return_status updated to REVIEWER COMPLETE format; Phase 4 synthesize placeholder preserved intact
- [Phase 04-01]: spawn_reviewers reads ALL TEAM.md roles in a single Read before issuing any Task() — single source of truth for role_definitions
- [Phase 04-01]: Explicit 'SINGLE MESSAGE' instruction in spawn_reviewers to enforce PIPE-01 parallel execution guarantee
- [Phase 04-01]: combined_findings uses flat all_findings array (not nested-by-reviewer) — synthesizer semantic dedup easier on flat structure
- [Phase 04-01]: Zero-findings early exit writes REVIEW-REPORT.md and skips synthesize entirely — log_and_continue is correct for 0 findings with no synthesis overhead
- [Phase 04-01]: return_status updated to PIPELINE COMPLETE — removes all Phase 3 placeholder language, adds FINAL_ROUTING + REVIEW-REPORT.md path + routing-conditional outcome messaging
- [Phase 04-01]: REVIEW-REPORT.md written by spawn_reviewers (zero-findings path) and synthesize step (non-zero path) — not by gsd-review-synthesizer.md agent
- [Phase 04-02]: Synthesizer prohibited from reading files — ONLY input is combined_findings in prompt tags (no file I/O)
- [Phase 04-02]: No-new-findings guard appears in both role block AND critical_rules — double enforcement at agent level
- [Phase 04-02]: synthesis_note field is the sanctioned outlet for cross-finding observations — never add them as unique_findings
- [Phase 04-02]: synthesis_errors array for self-reporting traceability violations — workflow catches and handles
- [Phase 04-02]: SYNTH-NNN uniform ID format for all synthesizer output regardless of whether finding was deduped or pass-through
- [Phase 04-03]: REVIEW-REPORT.md uses Read-then-Write append — not overwrite; existing content preserved on second and later plans
- [Phase 04-03]: Critical severity check BEFORE reading synthesizer.overall_routing — deterministic workflow-level override, not agent judgment
- [Phase 04-03]: block_and_escalate always requires user decision via AskUserQuestion — overrides auto_advance mode
- [Phase 04-03]: return_status only reached after log_and_continue or after user responds to block_and_escalate; send_for_rework and send_to_debugger halt without reaching it
- [Phase 04-03]: source_finding_ids validation in workflow performs independent traceability check — defense in depth beyond agent self-check
- [Phase 04-03]: Fallback on validation failure uses raw combined_findings.all_findings (un-deduplicated) with severity-based routing
- [Phase 05-01]: Starter roles are production-ready out of the box — no user editing required after install
- [Phase 05-01]: Rules Lawyer criterion generalized from CONVENTIONS.md to 'coding conventions followed consistently with the existing codebase' — applicable to any GSD project
- [Phase 05-01]: Preamble updated to 'starter roles' to match actual role status (no longer examples)
- [Phase 05-02]: 7-step flow: check_team_md → gather_domain → gather_name → gather_criteria → gather_severity → decision_gate → write_role
- [Phase 05-02]: All AskUserQuestion headers capped at 12 characters (Custom Focus and Display Name use exactly 12)
- [Phase 05-02]: Decision gate (step 6) shows full role preview before writing — satisfies ROLE-02 requirement
- [Phase 05-02]: write_role handles both TEAM.md exists (append + update frontmatter roles list) and does-not-exist (create stub header + role)
- [Phase 05-02]: Command file references installed path (~/.claude/get-shit-done-review-team/) not source path — works after install.sh copies it
- [Phase 05-03]: Post-update procedure uses re-run install.sh — NOT /gsd:reapply-patches; README.md and Section 9 completion message both direct users to `bash install.sh` as the single restore command
- [Phase 05-03]: Version check is warn-only — installer proceeds regardless of GSD version mismatch (hint, not hard requirement)
- [Phase 05-03]: sort -V used for semver range check — no custom semver parser needed; two printf | sort -V calls handle min/max range cleanly
- [Phase 06-01]: allowed_tools: used inside scope: (not top-level tools:) — distinguishes filesystem tool access constraint from a hypothetical top-level tool-call whitelist; matches success criteria naming explicitly
- [Phase 06-01]: agents: list omitted from v2 template frontmatter — dispatcher uses roles: exclusively; agents: is informational only per research open question resolution
- [Phase 06-01]: Three v1 role blocks (Security Auditor, Rules Lawyer, Performance Analyst) unchanged by design — demonstrates v1 compatibility; no mode/trigger/scope added
- [Phase 06-01]: normalizeRole shim triggers on version < 2 (numeric) — integer sentinel is the contract, string comparison explicitly rejected in spec prose
- [Phase 06-01]: scope fields default to [] when absent — no path or tool restrictions for roles that don't declare scope
- [Phase 06-02]: Anchors target post-review-team-patch state of settings.md — Touch point 1 anchors on Review Team closing block (not original un-patched content)
- [Phase 06-02]: Single jq pipe filter for Section 7 multi-key update — avoids race condition from two separate mktemp/mv sequences
- [Phase 06-02]: workflow.agent_studio is an independent boolean flag — does not affect workflow.review_team; both can be true simultaneously

### Pending Todos

None yet.

### Blockers/Concerns

- **Open**: Does AI merge in `reapply-patches` handle XML `<step>` blocks reliably across GSD version changes? (Test during Phase 1 — deferred: reapply-patches workflow is Phase 5)
- **Resolved (02-01)**: ARTIFACT.md written to disk at `.planning/phases/{phase_dir}/{phase}-{plan}-ARTIFACT.md` — audit trail, context efficiency, debuggability
- **Resolved (04-RESEARCH)**: REVIEW-REPORT.md per-phase — SYNTH-05 requirement text specifies {phase-dir}/REVIEW-REPORT.md explicitly; per-phase is the correct answer

## Session Continuity

Last session: 2026-02-27
Stopped at: Completed 06-02-PLAN.md — patch-settings-agent-studio.py created + install.sh extended
Resume file: None
