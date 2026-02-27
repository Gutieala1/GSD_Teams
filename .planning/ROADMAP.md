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

---

# Roadmap: GSD Agent Studio v2.0

## Overview

Seven phases building the full agent lifecycle platform on top of the proven v1.0 review
pipeline. The order is dictated by strict architectural dependencies: schema must precede
dispatcher; dispatcher must precede all trigger hooks and the management UI; lifecycle hooks
must precede advisory injection; agent creation must precede new-project integration. Every
phase delivers a coherent, verifiable capability — nothing is wired halfway.

v1.0 reviewers are preserved unchanged throughout. The dispatcher routes advisory post-plan
roles to the existing review-team.md pipeline without modification. Each phase extends rather
than replaces.

## Phases

- [ ] **Phase 6: TEAM.md v2 Schema + Config Foundation** — v2 schema fields parse correctly, v1.0 TEAM.md files work unchanged, agent_studio toggle appears in settings
- [ ] **Phase 7: Agent Dispatcher** — Single routing layer live, post-plan path wired through dispatcher to existing review pipeline, no-op on empty match
- [ ] **Phase 8: Team Roster /gsd:team** — Users can view, enable/disable, and invoke agents from the roster command
- [ ] **Phase 9: Lifecycle Trigger Hooks** — Pre-plan and post-phase agent gates patched into GSD core workflows, on-demand invoke path live
- [ ] **Phase 10: Advisory Output to Planner** — Pre-plan advisory agent notes injected into planner Task() context, planner always produces a plan
- [ ] **Phase 11: Agent Creation /gsd:new-agent** — Users can create agents through guided conversation, definition written to TEAM.md and agents/ directory
- [ ] **Phase 12: New-Project Integration** — Single question at project init, project-aware agent proposals, delegates to /gsd:new-agent

## Phase Details

### Phase 6: TEAM.md v2 Schema + Config Foundation
**Goal**: TEAM.md gains a v2 schema with additive optional fields (mode, triggers, output_type, scope, tools) and a version sentinel. Every v1.0 TEAM.md file loaded through the new parser produces identical behavior to v1.0 — no user migration required. The `workflow.agent_studio` toggle appears in `/gsd:settings` and is written to config.json.
**Depends on**: Phase 5 (v1.0 complete)
**Requirements**: AGNT-01, AGNT-02, AGNT-03
**Success Criteria** (what must be TRUE):
  1. A v1.0 TEAM.md file (no new fields, no version sentinel) loaded through the v2 parser produces defaults: mode advisory, trigger post-plan, output_type findings — behavior identical to v1.0
  2. A v2 TEAM.md role with `mode: autonomous` and explicit `allowed_paths` and `allowed_tools` fields is parsed correctly and scope constraints are stored and readable
  3. `/gsd:settings` shows an "Agent Studio" toggle that writes `workflow.agent_studio` to config.json without dropping any existing workflow keys
  4. Both `workflow.review_team: true` and `workflow.agent_studio: true` can be active simultaneously in config.json — they are independent flags
**Plans**: 2 plans

Plans:
- [ ] 06-01-PLAN.md — TEAM.md v2 template (version: 2, Doc Writer example with scope.allowed_paths/allowed_tools) + parser spec in ARCHITECTURE.md
- [ ] 06-02-PLAN.md — scripts/patch-settings-agent-studio.py (4-touch-point patcher) + install.sh extended for agent_studio config key

### Phase 7: Agent Dispatcher
**Goal**: `agent-dispatcher.md` is the single routing layer for all agent trigger types. When called with a trigger context, it reads TEAM.md, applies version defaults, filters agents by trigger match, and routes: advisory post-plan agents to the unchanged review-team.md pipeline; advisory pre-plan agents to advisory output collection; autonomous agents to autonomous execution. When no agents match the trigger context, it exits with zero latency added.
**Depends on**: Phase 6
**Requirements**: DISP-01, DISP-02, DISP-03
**Success Criteria** (what must be TRUE):
  1. The existing post-plan path (review_team_gate calling review-team.md) is redirected through agent-dispatcher.md — advisory post-plan agents reach the same review pipeline, producing identical REVIEW-REPORT.md output
  2. When TEAM.md has no agents matching the current trigger context, dispatcher exits immediately with no Task() spawns and no observable latency
  3. Agent creation plans are skipped by the dispatcher — the bypass flag in plan context is detected and the review pipeline does not fire on agent definition artifacts
**Plans**: 2 plans

Plans:
- [ ] 07-01-PLAN.md — workflows/agent-dispatcher.md (4-step dispatcher: bypass check, TEAM.md parse + normalizeRole, trigger filter, mode routing)
- [ ] 07-02-PLAN.md — scripts/patch-execute-plan-dispatcher.py (review_team_gate body replacement) + install.sh updated

### Phase 8: Team Roster /gsd:team
**Goal**: Users can run `/gsd:team` to see all configured agents: name, mode, triggers, output_type, and enabled status. From the roster, users can add an agent (routed to /gsd:new-agent), remove an agent with confirmation, enable or disable an agent, and invoke an agent on-demand against a specified artifact.
**Depends on**: Phase 7
**Requirements**: ROST-01, ROST-02, ROST-03
**Success Criteria** (what must be TRUE):
  1. `/gsd:team` displays a formatted table of all agents in TEAM.md with name, mode, triggers, output_type, and enabled status — disabled agents appear in the table but are visually distinguished
  2. From the roster, a user can disable an agent and confirm that subsequent dispatcher calls with a matching trigger context do not invoke the disabled agent
  3. From the roster, a user can invoke an agent on-demand against a specified artifact — result is displayed inline and logged to AGENT-REPORT.md
**Plans**: TBD

### Phase 9: Lifecycle Trigger Hooks
**Goal**: Three GSD core workflows are patched to call agent-dispatcher.md at the correct trigger points: plan-phase.md gains `pre_plan_agent_gate` (fires before plan creation, always fail-open); execute-phase.md gains `post_phase_agent_gate` (fires after all plans in a phase complete); the on-demand invoke path through /gsd:team is live. All patches are idempotent and safe on systems already patched with v1.0.
**Depends on**: Phase 7
**Requirements**: LIFE-01, LIFE-02, LIFE-03, LIFE-04
**Success Criteria** (what must be TRUE):
  1. The post-plan trigger (LIFE-01) calls agent-dispatcher.md instead of review-team.md directly — advisory post-plan agents reach the same review pipeline with no change in output
  2. The pre-plan trigger (LIFE-02) fires after the plan-checker step and before plan creation — a pre-plan agent failure or timeout never blocks plan creation; the planner always proceeds
  3. The post-phase trigger (LIFE-03) fires after all plans in a phase complete — advisory agent output is written to `.planning/phases/XX-name/AGENT-REPORT.md`
  4. Running install.sh on a system already patched with v1.0 applies the new patches without duplicating or corrupting existing patch blocks
**Plans**: TBD

### Phase 10: Advisory Output to Planner
**Goal**: Pre-plan advisory agent output is injected into the GSD planner's Task() context as an `<agent_notes>` block. Agents that fire at pre-plan genuinely inform what gets planned. The planner always produces a plan — advisory notes are input, not a gate. Advisory agents with `output_type: notes` return structured markdown; advisory agents with `output_type: findings` continue through the synthesizer pipeline.
**Depends on**: Phase 9
**Requirements**: ADVY-01, ADVY-02
**Success Criteria** (what must be TRUE):
  1. A pre-plan advisory agent with `output_type: notes` fires before plan creation and its structured markdown output appears in the planner's Task() prompt as an `<agent_notes>` block — the planner produces a plan that reflects or explicitly disregards the notes
  2. A pre-plan advisory agent with `output_type: findings` fires before plan creation and its output routes through the existing synthesizer pipeline — it does not appear as `<agent_notes>` and does not block plan creation
**Plans**: TBD

### Phase 11: Agent Creation /gsd:new-agent
**Goal**: Users can run `/gsd:new-agent` and create a new agent through a guided conversation that captures purpose, domain, mode, triggers, scope (for autonomous agents), and output type. A decision gate shows the complete agent definition before any file is written. On confirmation, the role block is appended to TEAM.md and an agent markdown file is created at `agents/gsd-agent-{slug}.md` if the agent requires a custom prompt. Agent creation plans bypass the review pipeline.
**Depends on**: Phase 6, Phase 8
**Requirements**: CREA-01, CREA-02, CREA-03, CREA-04
**Success Criteria** (what must be TRUE):
  1. `/gsd:new-agent` walks through a guided conversation (purpose, domain, mode, triggers, scope for autonomous, output type) and shows a complete agent definition preview before writing anything
  2. No files are written until the user explicitly confirms at the decision gate — cancellation at the gate leaves TEAM.md and agents/ directory unchanged
  3. On confirmation, the new role block appears in `.planning/TEAM.md` under `roles:` and the agent file is created at `agents/gsd-agent-{slug}.md` — the created agent is immediately visible in `/gsd:team` roster
  4. Plans executed during agent creation do not trigger the review pipeline — the artifact type bypass declared in DISP-03 prevents code-oriented reviewers from running on agent definition files
**Plans**: TBD

### Phase 12: New-Project Integration
**Goal**: After `/gsd:new-project` completes and PROJECT.md is committed, one question is asked: "Do you want to set up an agent team?" The options are "Set up now", "Set up later (/gsd:team)", and "Skip". Choosing "Set up now" reads PROJECT.md goals and stack, proposes 2-3 tailored agents, and delegates each creation to `/gsd:new-agent`. Choosing "Set up later" or "Skip" produces an outcome identical to v1.0. Agent configuration is never inlined into the new-project flow.
**Depends on**: Phase 8, Phase 11
**Requirements**: INIT-01, INIT-02, INIT-03
**Success Criteria** (what must be TRUE):
  1. After `/gsd:new-project` completes, exactly one question is asked about agent team setup — no additional questions about agent configuration appear in the new-project flow
  2. Choosing "Set up now" produces 2-3 agent proposals derived from PROJECT.md goals and stack — each proposal is shown individually and the user approves, modifies, or skips each one before anything is written
  3. Choosing "Set up later" or "Skip" produces an outcome identical to a v1.0 new-project run — no TEAM.md changes, no agent files created, new-project timing is effectively unchanged
**Plans**: TBD

## Progress

**Execution Order:** 6 → 7 → 8 → 9 → 10 → 11 → 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 6. TEAM.md v2 Schema + Config Foundation | 0/2 | Not started | - |
| 7. Agent Dispatcher | 0/2 | Not started | - |
| 8. Team Roster /gsd:team | 0/TBD | Not started | - |
| 9. Lifecycle Trigger Hooks | 0/TBD | Not started | - |
| 10. Advisory Output to Planner | 0/TBD | Not started | - |
| 11. Agent Creation /gsd:new-agent | 0/TBD | Not started | - |
| 12. New-Project Integration | 0/TBD | Not started | - |

## v2 Coverage

**v2 requirements: 20 total — all mapped**

| Requirement | Phase |
|-------------|-------|
| AGNT-01 | Phase 6 |
| AGNT-02 | Phase 6 |
| AGNT-03 | Phase 6 |
| DISP-01 | Phase 7 |
| DISP-02 | Phase 7 |
| DISP-03 | Phase 7 |
| ROST-01 | Phase 8 |
| ROST-02 | Phase 8 |
| ROST-03 | Phase 8 |
| LIFE-01 | Phase 9 |
| LIFE-02 | Phase 9 |
| LIFE-03 | Phase 9 |
| LIFE-04 | Phase 9 |
| ADVY-01 | Phase 10 |
| ADVY-02 | Phase 10 |
| CREA-01 | Phase 11 |
| CREA-02 | Phase 11 |
| CREA-03 | Phase 11 |
| CREA-04 | Phase 11 |
| INIT-01 | Phase 12 |
| INIT-02 | Phase 12 |
| INIT-03 | Phase 12 |
