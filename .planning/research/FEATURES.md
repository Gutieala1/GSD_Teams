# Feature Research

**Domain:** Agent Studio — CLI/chat-based agent lifecycle management for Claude Code extension
**Researched:** 2026-02-26
**Confidence:** HIGH (Claude Code subagent docs verified directly; ecosystem patterns from multiple current sources)

---

## Context: What v1.0 Already Built

Do not re-research or re-implement these. They are the foundation this milestone extends:

| Built in v1.0 | Location |
|---------------|----------|
| Post-execution review pipeline (sanitize → parallel review → synthesize → route) | `workflows/review-team.md` |
| Four routing destinations (block_and_escalate, send_for_rework, send_to_debugger, log_and_continue) | `gsd-review-synthesizer.md` |
| Reviewer role definitions in TEAM.md (Security Auditor, Rules Lawyer, Performance Analyst) | `.planning/TEAM.md` |
| REVIEW-REPORT.md written on all routing paths | Per-phase directories |
| /gsd:new-reviewer guided 7-step workflow | `commands/gsd/new-reviewer.md` |

The v2.0 question: what does it take to turn these post-execution reviewers into full project collaborators that span planning, execution, and verification?

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that any credible "agent studio" must have. Missing these means the system feels half-finished or unusable.

| Feature | Why Expected | Complexity | v1.0 Dependency | Notes |
|---------|--------------|------------|-----------------|-------|
| **Agent mode toggle (advisory vs autonomous)** | Every agent framework distinguishes "suggests" from "acts". Users need to set this at agent creation time. | LOW | TEAM.md schema must add `mode` field | Advisory = passes recommendations back; autonomous = takes action within defined scope. Binary, not a spectrum — spectrum creates ambiguous behavior. |
| **Configurable trigger points** | Agents that only fire post-execution are limited. Industry pattern (pre-hooks, post-hooks) is universal across frameworks. | MEDIUM | `execute-plan.md` patch already exists; `plan-phase.md` patch needed | Triggers: `pre_plan`, `post_plan`, `post_phase`, `on_demand`. Must be per-agent, not global. |
| **Agent roster command (/gsd:team)** | Users need to see what agents exist, what mode they're in, what triggers they have. Without a roster view, the team is invisible. | LOW | Reads TEAM.md; no new infra needed | CLI list view only — not a visual dashboard. Shows: name, mode, triggers, last activation. |
| **Consistent TEAM.md v2 schema** | New fields (mode, triggers, output_type, tools) must follow the existing TEAM.md format conventions or the file becomes inconsistent and hard to maintain. | LOW | TEAM.md v1 schema exists and ships | Schema extension, not replacement. Backward compatible with v1 roles. |
| **Agent creation via /gsd:new-agent** | Already have /gsd:new-reviewer for the old model. The new agent model needs its own creation workflow that captures mode, triggers, and tools — not just review criteria. | MEDIUM | Builds on new-reviewer.md patterns (7-step guided, AskUserQuestion, decision gate) | Replaces or extends new-reviewer.md. The v2 agent is a superset of a reviewer. |
| **Config toggle for agent_studio** | Following GSD's pattern: new workflow features live behind `workflow.*` flags in config.json. Users must be able to enable/disable the studio. | LOW | `workflow.review_team` pattern already established | Add `workflow.agent_studio: false` to config.json; `/gsd:settings` gets a new toggle. |

### Differentiators (What Makes This v2.0)

These are the features that make GSD Agent Studio different from generic agent frameworks. The v1.0 differentiator was "fresh-context isolated reviewers." The v2.0 differentiator is "deliberate, lifecycle-spanning project collaborators."

| Feature | Value Proposition | Complexity | v1.0 Dependency | Notes |
|---------|-------------------|------------|-----------------|-------|
| **Lifecycle-spanning triggers** | Agents active at `pre_plan` can shape what gets planned. Agents at `post_phase` see the full phase outcome, not just one plan. This is fundamentally different from reviewers who only see post-plan output. | HIGH | Requires patches to `plan-phase.md` (pre_plan trigger), `execute-phase.md` (post_phase trigger), and the existing `execute-plan.md` patch (post_plan trigger) | The `post_plan` trigger already exists via the review_team_gate. `pre_plan` and `post_phase` are net-new integration points. `on_demand` is a /gsd:team invoke command. |
| **Advisory output surfaced to planner** | When an advisory agent fires `pre_plan`, its recommendations must reach the planner's context. This creates a genuine planning loop — agents inform plans, not just evaluate them. | HIGH | Requires orchestrator logic to inject advisory output into the planner Task() prompt | This is the core v2.0 capability. Without it, agents are still just post-execution reviewers with new names. |
| **Project-aware agent initialization** | When a user runs `/gsd:new-project`, the wizard asks about agent team setup and proposes agents tailored to the project type. A "security-critical API" project gets a Security Auditor proposed. A "data pipeline" project gets a Data Quality Monitor proposed. | HIGH | Integrates with `new-project.md` workflow (Step 5 — Workflow Preferences) | Requires a project-type detection heuristic + a proposal mapping (project type → suggested agents). Not automatic — proposed, not auto-created. Deliberate GSD-native workflow. |
| **Autonomous agent artifact output** | An autonomous agent doesn't just return findings — it writes artifacts (files, updates, reports) directly and may trigger commits. This is how agents become collaborators, not just reporters. | HIGH | Builds on executor/verifier patterns for file writing; the gsd commit tool handles commits | Autonomous agents need: defined output_type (report, file_update, plan_update), a defined scope (which directories/files they can touch), and a DO NOT escalate unless severity=critical constraint. |
| **Agent history per-agent log** | `/gsd:team` shows not just what agents exist but what they found and did. Each agent has a log of findings/actions across phases. | MEDIUM | REVIEW-REPORT.md is per-phase; agent history requires a per-agent aggregate view | `.planning/TEAM-HISTORY.md` or per-agent files in `.planning/agents/`. Simple append log keyed by phase+plan. |
| **On-demand agent invocation** | `/gsd:team invoke <agent-name>` runs a specific agent on-demand against the current state. Useful for "run the Security Auditor now" without waiting for execution to complete. | MEDIUM | Agent files exist; the review-team pipeline can be extended with an on-demand mode | Requires knowing what context to pass — on-demand gets current phase context, no ARTIFACT.md assumed. |
| **GSD-native creation workflow for agents** | Agents aren't auto-generated from project context. They're created through a deliberate conversation (like /gsd:new-reviewer) that captures purpose, triggers, mode, scope, and output. This is the "studio" part of Agent Studio — a production line for agents, not a random agent soup. | HIGH | Extends new-reviewer.md; adds trigger selection, mode selection, output_type selection | This is a significant expansion of the 7-step new-reviewer workflow. New questions: What triggers this agent? What mode? What tools? What does it produce? |

### Anti-Features (Do Not Build)

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| **Auto-generate agents from project context** | "Just analyze my project and create the right agents" sounds convenient | Agents created without deliberate owner intent become noise. Nobody owns them. Nobody knows what they do. They accumulate silently. | Propose agents based on project type, let the user choose which to create via a deliberate workflow. Proposal ≠ auto-creation. |
| **Visual dashboard for agent management** | "Studios" imply a visual interface | GSD is CLI/chat-native. A "dashboard" in this context would be markdown tables plus AskUserQuestion — no better than a well-formatted `/gsd:team` output, and significantly more code. | /gsd:team command with formatted roster view. All the info, zero GUI complexity. |
| **Agent-to-agent messaging / shared memory** | Agents that can talk to each other seem more powerful | Cross-agent communication destroys isolation — the core v1.0 guarantee. Once agents share context, they inherit each other's reasoning biases. The review pipeline's value comes from isolation. | Agents communicate through the orchestrator (GSD workflows), not directly. Synthesizer already handles the aggregation pattern. |
| **Agent versioning system** | "I want to version my agents" | TEAM.md is already in git. Git IS the versioning system. A separate versioning layer adds complexity with no new capability. | Document that TEAM.md is tracked in git. Encourage meaningful commit messages when modifying agent definitions. |
| **Autonomous agents with unconstrained tool access** | "Let the agent do whatever it needs to do" | Autonomous agents with no tool/scope constraints are a security and reliability risk. An autonomous agent that can rewrite any file is a one-bug-away disaster. | Autonomous agents declare their `scope` (directories/files they can touch) and `tools` explicitly in TEAM.md. The GSD agent framework already enforces tool restrictions via frontmatter. |
| **Agent marketplace / sharing registry** | "I want to share my agents with others" | Premature. The TEAM.md schema is not yet stable enough to be an exchange format. A sharing mechanism before the format is settled creates future breaking changes. | Ship agent templates as starter roles in the extension repo (already doing this with v1.0 starter roles). Community sharing happens via GitHub, not a formal registry. |
| **Real-time agent monitoring** | "Show me what agents are doing as they run" | Claude Code subagents return on completion. There is no streaming agent status in the GSD task model — the orchestrator blocks until Task() returns. Real-time monitoring would require a fundamentally different execution model. | Color-coded agent type in Claude Code UI (already supported via `color:` frontmatter field) plus post-run TEAM-HISTORY.md logs. |
| **Agent A/B testing** | "Run two versions of an agent and compare" | Complexity far exceeds value for this milestone. A/B testing implies a quality metrics system, which is a separate milestone. | If users want to compare agents, they can temporarily swap TEAM.md roles and run both. Document this as a manual workflow. |

---

## Feature Dependencies

```
[TEAM.md v2 Schema]
    └──required by──> [Agent mode toggle]
    └──required by──> [Configurable trigger points]
    └──required by──> [Agent history per-agent log]
    └──required by──> [Autonomous agent artifact output]

[Agent mode toggle] + [Configurable trigger points]
    └──required by──> [Lifecycle-spanning triggers]

[Lifecycle-spanning triggers]
    └──required by──> [Advisory output surfaced to planner]
    └──required by──> [On-demand agent invocation]

[/gsd:new-agent creation workflow]
    └──required by──> [Project-aware agent initialization]

[Agent roster command (/gsd:team)]
    └──enhanced by──> [Agent history per-agent log]
    └──enhanced by──> [On-demand agent invocation]

[Config toggle for agent_studio]
    └──gates──> all other features (must be true for any agent to activate)
```

### Dependency Notes

- **TEAM.md v2 Schema requires design-first:** All other features depend on the schema. The schema must be finalized before any agent can be created, any trigger wired, or any history logged. This is Phase 1 of any roadmap.

- **Lifecycle triggers depend on GSD workflow patches:** `pre_plan` requires patching `plan-phase.md`. `post_phase` requires patching `execute-phase.md`. These are separate from the existing `execute-plan.md` patch (which handles `post_plan`). Each patch must handle the same "check config + check TEAM.md + check trigger" guard pattern.

- **Advisory output surfaced to planner is the hardest feature:** It requires the orchestrator to (1) fire an advisory agent before the planner, (2) collect the advisory output, and (3) inject it into the planner's Task() prompt. This is a three-step orchestration change, not a single patch.

- **/gsd:new-agent is a prerequisite for project-aware initialization:** The initialization wizard can only propose agents if it knows how to create them. The creation workflow must exist before initialization can offer it.

- **On-demand invocation depends on lifecycle triggers being wired:** If triggers aren't working, on-demand is the only way to test agents. But on-demand as a feature is most valuable after automatic triggers are proven — otherwise it becomes the only way to run agents.

---

## MVP Definition

This is a subsequent milestone — v1.0 is shipped. The MVP here is the minimum needed to deliver the v2.0 headline: "agents woven through the full lifecycle."

### Launch With (v2.0 MVP)

- [ ] **TEAM.md v2 schema** — Adds `mode`, `triggers`, `output_type`, `scope` fields. Backward compatible with v1.0 roles. This is the foundation everything else builds on.
- [ ] **Agent mode toggle (advisory vs autonomous)** — Set at the role level. Advisory: passes findings/recommendations to the caller. Autonomous: writes artifacts, may trigger actions.
- [ ] **Configurable trigger points** — `pre_plan`, `post_plan`, `post_phase`, `on_demand`. Per-agent, not global. `post_plan` already exists via review_team_gate — extend it.
- [ ] **Lifecycle-spanning trigger wiring** — Patch `plan-phase.md` for `pre_plan`, patch `execute-phase.md` for `post_phase`. The `post_plan` patch already exists.
- [ ] **Advisory output surfaced to planner** — When a `pre_plan` advisory agent fires, its output reaches the planner's context. This is the core v2.0 differentiator.
- [ ] **/gsd:new-agent creation workflow** — Extends new-reviewer.md. Captures: purpose, mode, triggers, scope, output_type.
- [ ] **Config toggle for agent_studio** — `workflow.agent_studio: false` in config.json. `/gsd:settings` gets the toggle.
- [ ] **Agent roster command (/gsd:team)** — Shows all agents: name, mode, triggers, last activation. Invoke on-demand from here.

### Add After Validation (v2.x)

- [ ] **Agent history per-agent log** — Aggregate TEAM-HISTORY.md across phases. Add once the trigger/activation pattern is stable and generating real data.
- [ ] **Project-aware agent initialization** — `/gsd:new-project` wizard proposes agents. Add once /gsd:new-agent workflow is proven and the proposal mapping is researched.
- [ ] **Autonomous agent artifact output** — Full autonomous action with defined scope and commit integration. Add once advisory mode is stable — autonomous builds on advisory patterns.

### Future Consideration (v3+)

- [ ] **On-demand agent invocation** — `/gsd:team invoke <agent>`. Useful but not blocking MVP — automatic triggers handle the main use case.
- [ ] **Starter agent templates for v2 mode** — Pre-built agents using the new schema (Pre-Plan Scope Guard, Post-Phase Health Reporter, etc.). Add once the schema is stable.
- [ ] **Agent performance metrics** — "Agent X has fired 12 times, found 3 critical issues." Requires history log to be mature.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| TEAM.md v2 schema | HIGH | LOW | P1 |
| Config toggle (agent_studio) | HIGH | LOW | P1 |
| Agent mode toggle | HIGH | LOW | P1 |
| /gsd:new-agent creation workflow | HIGH | MEDIUM | P1 |
| Configurable trigger points | HIGH | MEDIUM | P1 |
| Lifecycle-spanning trigger wiring | HIGH | HIGH | P1 |
| Advisory output surfaced to planner | HIGH | HIGH | P1 |
| /gsd:team roster command | MEDIUM | LOW | P2 |
| Agent history per-agent log | MEDIUM | MEDIUM | P2 |
| Project-aware initialization | HIGH | HIGH | P2 |
| Autonomous agent artifact output | HIGH | HIGH | P2 |
| On-demand agent invocation | MEDIUM | MEDIUM | P3 |
| Starter agent templates v2 | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for v2.0 launch — defines the milestone
- P2: Should have — add after P1 features validated
- P3: Nice to have — future milestone

---

## Ecosystem Context

### How Claude Code Subagents Work (HIGH confidence — verified from official docs, February 2026)

This is the actual platform GSD runs on. Key facts that directly shape feature design:

**Trigger model:** Claude Code subagents are invoked by the orchestrator via `Task()` — there is no native "fire on event X" hook in subagents themselves. GSD's lifecycle triggers must be implemented as orchestrator patches (the existing `review_team_gate` pattern), not as subagent-internal triggers. Source: [Claude Code subagent docs](https://code.claude.com/docs/en/sub-agents)

**Background vs foreground:** Subagents can run as `background: true` (concurrent with main conversation) or foreground (blocking). Advisory agents at `pre_plan` should be foreground — the plan must wait for recommendations. Post-phase agents could be background. This is a per-agent configuration choice.

**Hooks on subagents:** Claude Code supports `PreToolUse` and `PostToolUse` hooks within subagent frontmatter. This is distinct from GSD's trigger model. GSD triggers = when in the project lifecycle the agent fires. Claude Code hooks = what happens before/after each tool call within the agent's execution.

**Persistent memory:** Claude Code subagents support `memory: project` scope — agent-specific memory that persists across conversations and is stored in `.claude/agent-memory/<agent-name>/`. This could support "agent learns from previous phases" without GSD building a separate history system. HIGH potential for agent history feature.

**Permission modes:** `permissionMode: plan` gives an agent read-only access. This is exactly right for advisory agents — they read the state, return recommendations, cannot take action. Autonomous agents need `permissionMode: default` or `acceptEdits`.

**Scope/isolation control:** `tools` field restricts what a subagent can access. `isolation: worktree` runs the subagent in a git worktree. For autonomous agents with a defined scope, `tools` restriction is the right mechanism — not a custom scope system.

**AGENTS.md emerging standard:** A cross-tool configuration standard for AI agents. GSD's TEAM.md serves a similar purpose but is GSD-native. The ecosystem is converging on markdown-based agent configuration. GSD's approach is on the right side of this trend. Source: [AGENTS.md standard](https://skywork.ai/blog/agent/agents-md-configuration-standardizing-ai-agent-instructions-across-teams/)

### How Industry Agent Studios Handle Advisory vs Autonomous (MEDIUM confidence — WebSearch)

**The supervised/autonomous distinction is now standard:** GitHub Agentic Workflows, Azure Logic Apps, and n8n all distinguish "Supervised" (asks permission) from "Autonomous" (acts without asking). The binary is the right UX — avoid a multi-level spectrum that creates ambiguous agent behavior.

**Human-in-the-loop as default:** The industry has converged on advisory/supervised as the safe default with autonomous as opt-in. This matches GSD's existing pattern (reviewer agents are always advisory; autonomous is the new capability).

**Lifecycle hooks are universal:** Agno, OpenAI Agents SDK, LangGraph, and others all support pre/post hooks around agent execution steps. The pattern of "trigger before X, trigger after Y" is table stakes for any agent framework. GSD needs named lifecycle triggers (pre_plan, post_plan, etc.) mapped to hook injection points.

**Agent-generated recommendations reaching planners:** The pattern of "advisory agent output → planner context injection" is described in multi-agent literature as the "Society of Mind" pattern (AutoGen) or "critic-then-revise" pattern (multiple frameworks). The hard part is not the advisory output — it's the injection into the planner's context without contaminating isolation.

### What the v1.0 Architecture Enables (and Constrains)

The existing review pipeline is a critical dependency, not just context:

**Enablers:**
- `review_team_gate` in `execute-plan.md` is the `post_plan` trigger. It already works. v2.0 extends it, doesn't replace it.
- The GSD agent file format (YAML frontmatter + role block + process steps + output) is proven. All new agents follow this pattern.
- The Task() isolation model is validated. Advisory and autonomous agents both spawn via Task().
- AskUserQuestion guided workflows are proven (new-reviewer). New agent creation follows the same pattern.

**Constraints:**
- v1.0 reviewers are hardcoded as `post_plan`, advisory-only. The schema doesn't have `mode` or `triggers` fields yet.
- TEAM.md v1 format (`roles: [security-auditor, rules-lawyer, performance-analyst]` list + markdown role blocks) must be extended, not replaced, to preserve v1.0 functionality.
- The `review_team_gate` logic checks `workflow.review_team`, not `workflow.agent_studio`. The v2.0 toggle may need to subsume or gate on both, or migrate to a unified flag.
- Reviewers currently run only at `post_plan`. Wiring `pre_plan` requires a different workflow patch point — `plan-phase.md`, not `execute-plan.md`.

---

## Confidence Assessment

| Area | Confidence | Source |
|------|------------|--------|
| Claude Code subagent capabilities (triggers, hooks, memory, permissions) | HIGH | Official docs verified February 2026 |
| Advisory vs autonomous distinction pattern | HIGH | Multiple current sources converge |
| Lifecycle hook patterns (pre/post hooks) | HIGH | Multiple frameworks, OpenAI SDK docs |
| Project-aware initialization patterns | MEDIUM | WebSearch; pattern exists but no direct GSD-equivalent found |
| TEAM.md v2 schema design | MEDIUM | Inferred from v1.0 structure + what new features require |
| Autonomous agent action scope/safety | MEDIUM | Industry patterns; specific GSD implementation is novel |
| Agent history / persistent memory integration | MEDIUM | Claude Code memory feature is documented; GSD integration is new |

---

## Sources

- [Claude Code Subagent Documentation](https://code.claude.com/docs/en/sub-agents) — February 2026, HIGH confidence, official docs
- [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — MEDIUM confidence, patterns
- [AGENTS.md Configuration Standard](https://skywork.ai/blog/agent/agents-md-configuration-standardizing-ai-agent-instructions-across-teams/) — MEDIUM confidence
- [GitHub Agentic Workflows Technical Preview](https://github.blog/changelog/2026-02-13-github-agentic-workflows-are-now-in-technical-preview/) — February 2026, HIGH confidence
- [OpenAI Agents SDK Hooks](https://medium.com/@abdulkabirlive1/customize-ai-agent-behavior-with-hooks-in-openai-agents-sdk-05270e590cbe) — MEDIUM confidence
- [Agno Pre/Post Hooks Documentation](https://docs.agno.com/hooks/overview) — MEDIUM confidence
- [Agent Lifecycle Management (DevOps.com)](https://devops.com/the-developers-guide-to-agentic-ai-the-five-stages-of-agent-lifecycle-management/) — MEDIUM confidence
- [Google ADK Agent Team Tutorial](https://google.github.io/adk-docs/tutorials/agent-team/) — MEDIUM confidence
- `D:/GSDteams/.planning/PROJECT.md` — HIGH confidence, authoritative project spec
- `D:/GSDteams/.planning/ROADMAP.md` — HIGH confidence, v1.0 completion record
- `D:/GSDteams/.planning/TEAM.md` — HIGH confidence, v1.0 schema reference
- `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` — HIGH confidence, v1.0 research
- `D:/GSDteams/.planning/research/GSD-EXTENSION-ARCH.md` — HIGH confidence, extension architecture
- `C:/Users/gutie/.claude/get-shit-done/workflows/new-project.md` — HIGH confidence, integration point

---

*Feature research for: GSD Agent Studio v2.0*
*Researched: 2026-02-26*
