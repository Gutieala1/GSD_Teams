# Requirements: GSD Agent Studio

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

## v2 Requirements (v2.0 Agent Studio)

### Agent Model (TEAM.md v2 Schema)

- **AGNT-01**: TEAM.md role definitions gain new optional fields: `mode`, `triggers`, `output_type`, `scope`, `tools`. v1.0 definitions without new fields work unchanged — defaults preserve existing behavior (`advisory`, `[post-plan]`, `findings`, no scope, no tools override).
- **AGNT-02**: `config.json` gains `workflow.agent_studio: false` toggle distinct from `workflow.review_team`. Both can be true simultaneously — v1.0 reviewers are treated as advisory post-plan agents when agent_studio is also active.
- **AGNT-03**: Autonomous agents declare `allowed_paths` (glob list) and `allowed_tools` (tool name list) at creation time. Scope is stored in TEAM.md and surfaced explicitly during agent creation.

### Agent Dispatcher

- **DISP-01**: New `agent-dispatcher.md` workflow is the single routing layer for all trigger types. GSD core patches call the dispatcher; dispatcher reads TEAM.md, filters by trigger context, routes: advisory post-plan → existing review-team.md pipeline; advisory pre-plan → inject into planner; autonomous → autonomous execution path.
- **DISP-02**: If TEAM.md has no agents matching the current trigger context, dispatcher exits immediately (no-op). Zero spawned tasks, zero latency added.
- **DISP-03**: Agent creation plans skip the review pipeline. Bypass signaled by a flag in plan context so dispatcher can detect and skip. Rationale: agent definition files produce near-empty sanitized artifacts.

### Team Roster (/gsd:team)

- **ROST-01**: `/gsd:team` command reads TEAM.md and displays all configured agents: name, mode, triggers, output_type, enabled status, last activation if known.
- **ROST-02**: From the roster, user can: add agent (→ `/gsd:new-agent`), remove agent (confirm then delete role block), enable/disable agent (toggle `enabled` field), invoke on-demand (fire agent against specified artifact), view history (show AGENT-REPORT.md entries for that agent).
- **ROST-03**: Disabled agents (`enabled: false`) appear in the roster but are never invoked by the dispatcher.

### Lifecycle Triggers

- **LIFE-01**: Post-plan trigger (`review_team_gate` in execute-plan.md) redirected to call `agent-dispatcher.md` instead of `review-team.md` directly. For advisory post-plan agents, dispatcher calls the unchanged v1.0 pipeline.
- **LIFE-02**: `pre_plan_agent_gate` step patched into plan-phase.md before plan creation. Fires advisory pre-plan agents, collects output, injects as `<agent_notes>` block into planner Task() prompt. **Always fail-open** — pre-plan agents cannot block plan creation under any circumstances.
- **LIFE-03**: `post_phase_agent_gate` step patched into execute-phase.md after all plans in a phase complete. Advisory output written to `.planning/phases/XX-name/AGENT-REPORT.md`. Autonomous agents commit artifacts directly.
- **LIFE-04**: On-demand invocation via `/gsd:team` → "Invoke on-demand". User selects agent and artifact. Result displayed inline and logged to AGENT-REPORT.md.

### Advisory Output to Planner

- **ADVY-01**: Pre-plan advisory agent output injected into planner Task() prompt as `<agent_notes>` block containing structured markdown notes from each advisory agent. Planner may incorporate or disregard — it always produces a plan.
- **ADVY-02**: Advisory agents with `output_type: notes` return structured markdown (not findings JSON). Advisory agents with `output_type: findings` continue through the existing synthesizer pipeline.

### Agent Creation (/gsd:new-agent)

- **CREA-01**: `/gsd:new-agent` command: guided conversation capturing purpose, domain, mode, triggers, scope (autonomous only), output type, with a decision gate showing the full agent definition preview before any write occurs.
- **CREA-02**: Decision gate shows the complete agent definition to the user and requires explicit confirmation before writing. No files written until confirmed.
- **CREA-03**: On confirmation: role block appended to `.planning/TEAM.md` (YAML frontmatter `roles:` list updated), agent markdown file created at `agents/gsd-agent-{slug}.md` if the agent requires a custom prompt.
- **CREA-04**: Agent creation committed via gsd-tools.cjs. Review pipeline bypass (DISP-03) applies to the creation plan.

### New-Project Integration

- **INIT-01**: After `/gsd:new-project` completes and PROJECT.md is committed, one question is asked: "Do you want to set up an agent team?" Options: "Set up now", "Set up later (/gsd:team)", "Skip". This is the only addition to the new-project flow.
- **INIT-02**: If "Set up now": read PROJECT.md goals/stack/domain, propose 2–3 tailored agents. Show each proposal (name, purpose, mode, triggers) before creating anything. User approves, modifies, or skips each individually.
- **INIT-03**: Agent creation during new-project setup delegates to the same `/gsd:new-agent` workflow — no special-case path.

### Non-Requirements (Explicit Exclusions for v2.0)

| Excluded Feature | Reason |
|-----------------|--------|
| Auto-creating agents | Always deliberate — ask, propose, confirm |
| Agent history database | AGENT-REPORT.md markdown files are the history |
| Multi-level autonomy (semi-autonomous) | Mode is binary: advisory or autonomous |
| Agents reviewing agents during creation | Review pipeline bypassed for agent creation plans (DISP-03) |
| Global/community agent library | Deferred — out of scope for v2.0 |
| Pre-plan blocking | Pre-plan agents are advisory only, always fail-open (LIFE-02) |
| Agents spawning other agents | Dispatcher spawns agents; agents execute their task only |

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
| AGNT-01 | Phase 6 | Pending |
| AGNT-02 | Phase 6 | Pending |
| AGNT-03 | Phase 6 | Pending |
| DISP-01 | Phase 7 | Pending |
| DISP-02 | Phase 7 | Pending |
| DISP-03 | Phase 7 | Pending |
| ROST-01 | Phase 8 | Pending |
| ROST-02 | Phase 8 | Pending |
| ROST-03 | Phase 8 | Pending |
| LIFE-01 | Phase 9 | Pending |
| LIFE-02 | Phase 9 | Pending |
| LIFE-03 | Phase 9 | Pending |
| LIFE-04 | Phase 9 | Pending |
| ADVY-01 | Phase 10 | Pending |
| ADVY-02 | Phase 10 | Pending |
| CREA-01 | Phase 11 | Pending |
| CREA-02 | Phase 11 | Pending |
| CREA-03 | Phase 11 | Pending |
| CREA-04 | Phase 11 | Pending |
| INIT-01 | Phase 12 | Pending |
| INIT-02 | Phase 12 | Pending |
| INIT-03 | Phase 12 | Pending |

**v1 Coverage:**
- v1 requirements: 37 total — all delivered ✓

**v2 Coverage:**
- v2 requirements: 20 total (AGNT-01..03, DISP-01..03, ROST-01..03, LIFE-01..04, ADVY-01..02, CREA-01..04, INIT-01..03)
- Mapped to phases: Phase 6–12 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-25 (v1), 2026-02-26 (v2)*
*Last updated: 2026-02-26 — v2.0 Agent Studio requirements added; traceability mapped to phases 6-12*
