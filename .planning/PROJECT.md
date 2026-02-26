# GSD Agent Studio

## Current Milestone: v2.0 Agent Studio

**Goal:** Evolve the review pipeline into a full agent studio — project-aware agents woven through planning, execution, and verification, created through a deliberate GSD-native workflow.

**Target features:**
- Agent model replacing reviewer model: configurable mode (advisory/autonomous), triggers across the full lifecycle (pre-plan, post-plan, post-phase, on-demand)
- GSD-native agent creation: plan+execute workflow builds each agent — deliberate, not automatic
- New-project integration: ask about agent team at project init, propose agents tailored to project goals
- Agent Studio: `/gsd:team` roster command + conversational agent management
- Agents embedded in planning, execution, and verification — not just post-execution review

## Validated (v1.0 — GSD Review Team)

- ✓ Sanitizer strips executor reasoning from SUMMARY.md → clean ARTIFACT.md — Phase 2
- ✓ Parameterized reviewer agent spawns in isolation via Task() with role context — Phase 3
- ✓ Parallel reviewer pipeline with combined_findings deduplication — Phase 4
- ✓ Synthesizer routes findings: block_and_escalate / send_for_rework / send_to_debugger / log_and_continue — Phase 4
- ✓ REVIEW-REPORT.md written on all routing paths before acting — Phase 4
- ✓ /gsd:new-reviewer guided workflow + command — Phase 5
- ✓ Starter roles (Security Auditor, Rules Lawyer, Performance Analyst) production-ready — Phase 5
- ✓ install.sh idempotent with version check, commands/gsd copy, README — Phase 5

## Vision

Open-source GSD extension that evolves from a review pipeline into a full agent studio.
Agents are purpose-built collaborators — defined by project goals, woven through planning,
execution, and verification — that catch errors, surface insights, and take autonomous action
within their defined scope.

## Problem

AI makes small mistakes that look fine individually but compound silently. By the time you
notice, you've built on a cracked foundation and burned tokens rebuilding. Standard
single-agent review fails because the reviewer inherits the executor's reasoning biases —
looking at the same output through the same lens that produced it.

## Solution

A "studio team" model where each reviewer knows their lane and stays in it. Execution output
is sanitized (reasoning stripped), then passed to reviewers in parallel via Task() — each
spawned in a fresh context with only the clean artifact and their own role definition. A
synthesizer classifies findings and routes them to the right destination. Bugs go to the
debugger. Rework goes back to execution. Minor notes get logged. Critical issues surface to
the user.

## Core Concepts

### The Review Pipeline (fires after each plan in execute-phase)

```
SUMMARY.md
    │
    ▼
[Sanitizer]  ──── strips reasoning, exports clean artifact description
    │
    ├──────────────────────────────────────┐
    ▼                                      ▼
[Reviewer A]                         [Reviewer B]      ... (parallel, isolated)
Security Auditor                     Rules Lawyer
fresh context                        fresh context
no shared state                      no shared state
    │                                      │
    └──────────────┬───────────────────────┘
                   ▼
            [Synthesizer]  ──── classifies findings, decides routing
                   │
        ┌──────────┼──────────┬────────────┐
        ▼          ▼          ▼            ▼
    block &    rework     debugger     log &
    escalate   executor               continue
```

### Routing Destinations

| Destination        | Trigger                                   | Action                                      |
|--------------------|-------------------------------------------|---------------------------------------------|
| `block_and_escalate` | Critical findings (security, data loss) | Halt execution, surface full finding to user |
| `send_for_rework`  | Major correctness / architecture issues   | Create targeted fix task, re-execute         |
| `send_to_debugger` | Bugs outside current execution scope      | Route to gsd-debugger                       |
| `log_and_continue` | Minor / informational findings            | Append to REVIEW-REPORT.md, continue         |

Synthesizer decides routing based on finding type and severity. TEAM.md routing hints
override defaults per-role.

### TEAM.md

User-defined reviewer roles stored in `.planning/TEAM.md`. Each role captures:

- **Name + focus area** — who this reviewer is and what domain they cover
- **Review criteria / checklist** — specific things to look for
- **Severity thresholds** — critical / major / minor for this role
- **Routing hints** — how this role's findings should be handled

GSD assists role creation via `/gsd:new-reviewer` — a guided conversation that writes a new
role into TEAM.md.

### Integration Point

Hooks into `execute-plan.md` between `create_summary` and `offer_next` steps.
Guarded by `workflow.review_team: true` in config.json.

**Zero impact on:**
- `/gsd:new-project` — project creation mechanics unchanged
- `/gsd:plan-phase` — planning pipeline unchanged
- Roadmap / requirements creation — untouched

Review Team supplements execution only.

## Success Criteria (v1)

Run a GSD project end-to-end with Review Team active:

- Reviewers fire automatically after each plan in execute-phase
- Each reviewer receives only sanitized output — no executor reasoning, no anchoring bias
- Synthesizer routes findings correctly per TEAM.md routing hints
- Pipeline integrates seamlessly — no manual steps required once configured

## Architecture

### Extension File Layout

```
get-shit-done-review-team/
├── agents/
│   ├── gsd-review-sanitizer.md       # Strips reasoning from SUMMARY.md → clean artifact
│   ├── gsd-reviewer.md               # Reviewer agent template (loaded with role context)
│   └── gsd-review-synthesizer.md     # Classifies findings + routes to destinations
├── commands/gsd/
│   └── new-reviewer.md               # Entry point for /gsd:new-reviewer command
├── workflows/
│   ├── review-team.md                # Pipeline orchestration (sanitize → review → synthesize)
│   └── new-reviewer.md               # Role builder workflow (guided questioning → TEAM.md)
├── templates/
│   ├── TEAM.md                       # Starter TEAM.md with example roles
│   └── review-report.md              # REVIEW-REPORT.md output template
├── install.sh                        # Copies files + patches execute-plan.md
└── README.md
```

### GSD Core Files Modified (via patch)

| File | Change |
|------|--------|
| `~/.claude/get-shit-done/workflows/execute-plan.md` | Adds `review_team_gate` step between `create_summary` and `offer_next` |
| `~/.claude/get-shit-done/workflows/settings.md` | Adds Review Team toggle to config UI |

### New config.json Field

```json
"workflow": {
  "research": true,
  "plan_check": true,
  "verifier": true,
  "auto_advance": false,
  "review_team": false
}
```

### Sanitization (what gets stripped, what passes through)

The sanitizer receives SUMMARY.md and outputs a clean artifact:

| Passed to reviewers | Stripped from reviewers |
|---------------------|-------------------------|
| Files created / modified (paths + purpose) | Internal reasoning ("I decided to...") |
| Key decisions made | Alternative approaches considered |
| What was implemented (behavior) | Task-by-task execution log |
| Tech added to stack | Planner/executor thought process |
| Key integrations / connections | Any reasoning that could anchor the reviewer |

### Review Report

Findings logged to `.planning/phases/XX-name/REVIEW-REPORT.md` per phase. Format:

```markdown
## Review Report — Phase {X}, Plan {Y}

| Reviewer         | Severity | Finding                         | Routed To    |
|------------------|----------|---------------------------------|--------------|
| Security Auditor | minor    | Unused env var STRIPE_LEGACY_KEY | log          |
| Rules Lawyer     | major    | Missing error boundary on /api  | rework       |
```

## Constraints

- **Non-invasive**: No changes to new-project, plan-phase, roadmap, or requirements workflows
- **Minimal core patch**: Single conditional block in execute-plan.md — small, auditable, reapply-patches compatible
- **GSD-native**: Uses Task(), gsd-tools.cjs, config.json toggles, .planning/ conventions throughout
- **Isolation guaranteed**: Reviewers receive ONLY sanitized output — no plan, no prior summaries, no reasoning chains
- **No build step**: Installation is git clone + file copy + patch — no npm install required
- **Backwards compatible**: `workflow.review_team` defaults to `false` — existing GSD users unaffected until they opt in

## Open Questions (v2.0)

- What does the TEAM.md v2 schema look like? New fields: mode, triggers, tools, output_type
- How do autonomous agents commit their artifacts — through GSD's commit tool or directly?
- How does the pre-plan trigger interact with plan-phase — does an agent review PLAN.md before execution begins?
- What does "agent history" look like in /gsd:team — per-agent log of findings/actions?
- Should TEAM.md remain a single file or split into per-agent files as teams grow?

## Resolved (v1.0)

- ✓ Starter roles ship with the repo (Security Auditor, Performance Analyst, Rules Lawyer)
- ✓ /gsd:update: reapply-patches handles core patch; users re-run install.sh after update
- ✓ REVIEW-REPORT.md: per-phase directory (matches SUMMARY.md/ARTIFACT.md naming convention)
- ✓ /gsd:new-reviewer: guided 7-step workflow (no template library needed for v1)

---
*Last updated: 2026-02-26 — Milestone v2.0 Agent Studio started*
