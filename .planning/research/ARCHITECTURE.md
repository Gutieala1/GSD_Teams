# Architecture Research: Agent Studio v2.0

**Domain:** GSD extension — agent lifecycle management and multi-trigger orchestration
**Researched:** 2026-02-26
**Confidence:** HIGH — all findings verified directly from GSD source code and installed extension files

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GSD Core Workflows (patched)                     │
│  new-project.md   plan-phase.md   execute-plan.md   execute-phase.md │
│       │                │                │                 │          │
│       ▼                ▼                ▼                 ▼          │
│  [agent_team_   [pre_plan_        [post_plan_       [post_phase_     │
│   hook] NEW     gate] NEW         gate] EXISTS      gate] NEW        │
└───────┬────────────────┬────────────────┬─────────────────┬──────────┘
        │                │                │                 │
        └────────────────┴────────────────┴─────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Agent Studio Dispatcher   │
                    │  team-studio.md (NEW)       │
                    │  + agent-dispatcher.md (NEW)│
                    └─────────────┬──────────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           ▼                      ▼                       ▼
   ┌──────────────┐      ┌───────────────┐      ┌────────────────┐
   │  Review      │      │  Advisory     │      │  Autonomous    │
   │  Pipeline    │      │  Agents       │      │  Agents        │
   │  (v1.0)      │      │  (read-only   │      │  (commit own   │
   │  unchanged   │      │   findings)   │      │   artifacts)   │
   └──────────────┘      └───────────────┘      └────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    TEAM.md v2 Schema        │
                    │    (backwards compatible)   │
                    │    .planning/TEAM.md        │
                    └─────────────────────────────┘
```

---

## Component Responsibilities

| Component | Responsibility | Status |
|-----------|---------------|--------|
| `TEAM.md` v2 | Agent roster: mode, trigger, tools, output_type per agent | Schema evolution (backwards compat required) |
| `team-studio.md` | `/gsd:team` roster display + conversational agent management | New workflow |
| `agent-dispatcher.md` | Reads TEAM.md, routes agents by trigger type | New workflow |
| `review-team.md` | Post-plan review pipeline (v1.0) | Unchanged |
| `new-reviewer.md` | Guided role creation for review-team roles | Unchanged (v1.0); extended for v2 agent creation |
| `new-agent.md` | GSD-native agent creation via plan+execute | New workflow |
| Patches: `execute-plan.md` | Existing `review_team_gate` step | No change to step; dispatcher replaces direct call |
| Patches: `plan-phase.md` | New `pre_plan_agent_gate` step | New patch anchor: after `present_final_status` / step 13 |
| Patches: `execute-phase.md` | New `post_phase_agent_gate` step | New patch anchor: after `aggregate_results` / before `verify_phase_goal` |
| Patches: `new-project.md` | New `agent_team_hook` step | New patch anchor: after Step 5 (config written) |

---

## TEAM.md v2 Schema

### Design Principle: Additive Evolution

v1.0 roles have no `mode`, `trigger`, `tools`, or `output_type` fields. The v2 parser must treat
their absence as `mode: advisory`, `trigger: post-plan`, `tools: []`, `output_type: findings`.
This makes every v1.0 role valid in v2 without any file edits.

### v2 Frontmatter

```yaml
---
version: 2
roles:
  - security-auditor      # v1.0 role — implicit defaults apply
  - rules-lawyer          # v1.0 role — implicit defaults apply
  - performance-analyst   # v1.0 role — implicit defaults apply
  - doc-writer            # v2 role — explicit fields present
agents:
  - doc-writer            # agents list mirrors roles list; duplicated for clarity
---
```

The `version: 2` sentinel enables the dispatcher to apply the full v2 parsing path.
`version: 1` (or absent) triggers the v1 compatibility shim.

### v2 Role Block (full fields)

```yaml
## Role: Doc Writer

```yaml
name: doc-writer
focus: Keeps documentation in sync with implementation
mode: autonomous           # advisory | autonomous
trigger: post-phase        # pre-plan | post-plan | post-phase | on-demand
tools:                     # subset of: Read, Write, Bash, Grep, Glob, WebSearch
  - Read
  - Write
  - Grep
output_type: artifact      # findings | artifact | advisory
commit: true               # autonomous only — whether agent commits its own output
commit_message: "docs(auto): update API reference after phase {phase}"
```

**What this role reviews:**
[unchanged from v1 — used by review-team pipeline when trigger: post-plan]

**Severity thresholds:**
[only present if mode: advisory — used by synthesizer]

**Routing hints:**
[only present if mode: advisory — used by synthesizer]
```

### Field Definitions

| Field | Values | Default (absent) | Required for |
|-------|--------|-----------------|--------------|
| `mode` | `advisory`, `autonomous` | `advisory` | All v2 agents |
| `trigger` | `pre-plan`, `post-plan`, `post-phase`, `on-demand` | `post-plan` | All v2 agents |
| `tools` | Any Claude Code tool name | `[]` (no filesystem access) | Autonomous agents |
| `output_type` | `findings`, `artifact`, `advisory` | `findings` | Routing logic |
| `commit` | `true`, `false` | `false` | Autonomous agents |
| `commit_message` | String with `{phase}`, `{plan}` tokens | None | Autonomous with commit |

### Backwards Compatibility: v1 Role Defaults

When `version: 1` or version field absent, all roles get these defaults injected by the parser:

```
mode:        advisory
trigger:     post-plan
tools:       []
output_type: findings
commit:      false
```

This means v1.0 roles flow unchanged into the v1.0 review pipeline via `review-team.md`.
No TEAM.md edits required. No migration step needed.

### TEAM.md v2 Parsing Algorithm

The dispatcher (`agent-dispatcher.md`) applies this logic to every role:

```
1. Read version from frontmatter (default: 1)
2. For each role in roles list:
   a. Find its ## Role: section
   b. Extract YAML config block
   c. If any v2 fields (mode/trigger/tools/output_type) are absent:
      inject version-appropriate defaults
   d. Classify: advisory+post-plan = review-team pipeline
              advisory+other-trigger = advisory agent path
              autonomous = autonomous agent path
3. Filter by current trigger context (passed by calling workflow)
4. Return filtered role list to dispatcher
```

---

## New Files Required

### Extension Files (new)

```
~/.claude/get-shit-done-review-team/
├── workflows/
│   ├── review-team.md           # EXISTS — unchanged
│   ├── new-reviewer.md          # EXISTS — unchanged
│   ├── team-studio.md           # NEW: /gsd:team roster + management
│   ├── agent-dispatcher.md      # NEW: reads TEAM.md, routes by trigger
│   └── new-agent.md             # NEW: GSD-native agent creation (plan+execute)
├── agents/
│   ├── gsd-reviewer.md          # EXISTS — unchanged
│   ├── gsd-review-sanitizer.md  # EXISTS — unchanged
│   ├── gsd-review-synthesizer.md # EXISTS — unchanged
│   └── gsd-agent-builder.md     # NEW: agent used in new-agent.md workflow
├── commands/gsd/
│   ├── new-reviewer.md          # EXISTS (in ~/.claude/commands/gsd/) — unchanged
│   └── team.md                  # NEW: entry point for /gsd:team
```

### GSD Core Files Modified (cumulative patches)

| File | Existing Patch | v2.0 Addition |
|------|---------------|---------------|
| `execute-plan.md` | `review_team_gate` step (after `update_codebase_map`, before `offer_next`) | No change — dispatcher replaces direct call |
| `plan-phase.md` | None | New `pre_plan_agent_gate` step |
| `execute-phase.md` | None | New `post_phase_agent_gate` step |
| `new-project.md` | None | New `agent_team_hook` step |
| `settings.md` | Review Team toggle | No new toggles (agent studio managed via /gsd:team) |

---

## Patch Anchor Points (named step anchors in GSD workflows)

### Patch 1 (already applied): `execute-plan.md` — `review_team_gate`

**Current state:** Already installed between `update_codebase_map` and `offer_next`.

**v2.0 change:** The step body changes from calling `review-team.md` directly to calling
`agent-dispatcher.md` with `trigger: post-plan`. The dispatcher decides whether to route to
the v1 review pipeline or a v2 autonomous/advisory agent.

```
BEFORE (v1): review_team_gate → calls review-team.md directly
AFTER (v2):  review_team_gate → calls agent-dispatcher.md with trigger=post-plan
             agent-dispatcher reads TEAM.md, filters by trigger=post-plan
             → advisory roles go to review-team.md (unchanged)
             → autonomous roles execute their own agent definition
```

This is a change to the **step body**, not the step name or location. The patch anchor
(`<step name="offer_next">`) does not move. Install.sh idempotency check remains valid.

### Patch 2 (new): `plan-phase.md` — `pre_plan_agent_gate`

**Anchor:** Insert BEFORE the `<offer_next>` block (or Step 13: "Present Final Status") in plan-phase.md.

**Why this location:** PLAN.md files have been written and verified by gsd-plan-checker.
Pre-plan agents receive the complete plan set before execution begins.

**Step body:**

```xml
<step name="pre_plan_agent_gate">
Check whether any pre-plan agents are configured:

AGENT_STUDIO_ENABLED=$(jq -r '.workflow.agent_studio // false' .planning/config.json 2>/dev/null || echo "false")

If AGENT_STUDIO_ENABLED is not "true": skip this step entirely.

If AGENT_STUDIO_ENABLED is "true":
- Check that .planning/TEAM.md exists with at least one role with trigger: pre-plan
- If no pre-plan agents configured: skip silently
- If pre-plan agents found: load and execute dispatcher:
  @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
  Pass: trigger=pre-plan, phase identifier, plan directory path
</step>
```

**Config flag:** `workflow.agent_studio` (distinct from `workflow.review_team` for backwards compat).
Both flags can be true simultaneously. `review_team` controls v1 post-plan behavior independently.

### Patch 3 (new): `execute-phase.md` — `post_phase_agent_gate`

**Anchor:** Insert AFTER `aggregate_results` step, BEFORE `verify_phase_goal` step.

Why: All plans in the phase have executed. SUMMARY.md files exist for every plan. This is
the "all plans complete" moment. Post-phase agents see the complete phase output.

**Step body:**

```xml
<step name="post_phase_agent_gate">
Check whether any post-phase agents are configured:

AGENT_STUDIO_ENABLED=$(jq -r '.workflow.agent_studio // false' .planning/config.json 2>/dev/null || echo "false")

If AGENT_STUDIO_ENABLED is not "true": skip this step entirely.

If AGENT_STUDIO_ENABLED is "true":
- Check that .planning/TEAM.md exists with at least one role with trigger: post-phase
- If no post-phase agents configured: skip silently
- If post-phase agents found: load and execute dispatcher:
  @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
  Pass: trigger=post-phase, phase identifier, phase directory path, list of SUMMARY.md paths
</step>
```

### Patch 4 (new): `new-project.md` — `agent_team_hook`

**Anchor:** Insert AFTER Step 5 "Workflow Preferences" (after config.json is written and committed).
Specifically after the `commit config.json` bash block and before "Note: Run /gsd:settings anytime".

Why: config.json exists (agent_studio flag can be read), PROJECT.md exists (project goals
are known), research may exist (informs agent proposals).

**Step body:**

```
## 5.6. Agent Team Setup

Check if agent_studio is already in config (from global defaults):

AGENT_STUDIO=$(jq -r '.workflow.agent_studio // false' .planning/config.json 2>/dev/null || echo "false")

If AGENT_STUDIO is already "true": skip this section.

Ask the user:
AskUserQuestion([{
  header: "Agent Team",
  question: "Set up an agent team for this project?",
  multiSelect: false,
  options: [
    { label: "Yes — propose agents", description: "I'll suggest agents based on your project goals" },
    { label: "Later", description: "Set up via /gsd:team at any time" }
  ]
}])

If "Later": skip.

If "Yes — propose agents":
  Read .planning/PROJECT.md to extract core goals and stack.
  Read .planning/research/FEATURES.md if it exists (research output).

  Based on project goals, propose 2-3 relevant agents inline (not via AskUserQuestion):
  Show the proposals as a markdown block, then:

  AskUserQuestion([{
    header: "Team Setup",
    question: "Start with these proposed agents?",
    multiSelect: false,
    options: [
      { label: "Set up now", description: "Walk through each agent definition" },
      { label: "Skip — I'll use /gsd:team later", description: "Continue without agent setup" }
    ]
  }])

  If "Set up now": invoke /gsd:team --setup for each proposed agent (guided creation).
  If "Skip": continue.

  Enable agent_studio in config:
  jq '.workflow.agent_studio = true' .planning/config.json > tmp.json && mv tmp.json .planning/config.json
```

---

## Agent Dispatcher: Data Flow

```
Trigger Context (from calling workflow)
  trigger_type: pre-plan | post-plan | post-phase | on-demand
  phase_id: "03-authentication"
  plan_num: "02"  (for post-plan only)
  phase_dir: ".planning/phases/03-authentication/"
        │
        ▼
agent-dispatcher.md
  1. Read .planning/TEAM.md
  2. Parse version (1 or 2)
  3. Apply defaults for version
  4. Filter roles: keep where trigger == trigger_type
  5. Group by mode: advisory | autonomous
        │
        ├──── advisory roles ──────────────────────────────────────┐
        │     (post-plan advisory = v1.0 review-team pipeline)     │
        │     call review-team.md with filtered role list          │
        │                                                           │
        └──── autonomous roles ────────────────────────────────────┘
              For each autonomous role:
                Read role's agent definition file (from role.agent_file field)
                Spawn Task() with role definition + trigger context
                Collect return
                If commit: true → agent commits its own artifact
                Log output to .planning/phases/{phase_id}/AGENT-LOG.md
```

### Autonomous Agent Execution Contract

Autonomous agents differ from advisory agents in one key way: they produce artifacts, not
findings. An autonomous Doc Writer produces updated `*.md` files. An autonomous Changelog
Agent produces `CHANGELOG.md` updates. These are commits, not review findings.

**Autonomous agent Task() prompt structure:**

```
Task(
  subagent_type="{agent_file_slug}",  # points to ~/.claude/agents/{slug}.md
  prompt="
    <objective>
    {agent's defined objective from TEAM.md}
    </objective>

    <trigger_context>
    trigger: {trigger_type}
    phase: {phase_id}
    plan: {plan_num}  (if post-plan)
    phase_dir: {phase_dir}
    summary_paths: {list of SUMMARY.md paths}
    </trigger_context>

    <role_definition>
    {full role block from TEAM.md}
    </role_definition>
  "
)
```

**Commit pattern for autonomous agents:**

Autonomous agents with `commit: true` commit their own output using gsd-tools:

```bash
node ~/.claude/get-shit-done/bin/gsd-tools.cjs commit "{commit_message}" --files {artifact_paths}
```

The `commit_message` field in TEAM.md supports `{phase}` and `{plan}` token substitution.
The dispatcher performs token substitution before passing context to the agent.

---

## `/gsd:team` Command and `team-studio.md` Workflow

### Entry Point

```
~/.claude/commands/gsd/team.md
  allowed-tools: Read, Write, AskUserQuestion, Bash
  execution_context: @~/.claude/get-shit-done-review-team/workflows/team-studio.md
```

### `team-studio.md` Step Sequence

```
Step 1: show_roster
  Read .planning/TEAM.md (or inform if missing)
  Display formatted roster: each agent with mode, trigger, status (active/disabled)
  Count by trigger type: pre-plan: N, post-plan: N, post-phase: N, on-demand: N

Step 2: present_actions (AskUserQuestion)
  header: "Team"
  options:
    - "Add agent" → route to new-agent.md workflow
    - "Edit agent" → select from roster, open conversational edit
    - "Disable/enable" → toggle an agent without deleting
    - "Run agent now" → on-demand trigger for a specific agent
    - "View history" → show AGENT-LOG.md for this phase
    - "Done" → exit

Step 3: handle_selection
  Route to appropriate sub-workflow based on selection.
  Each sub-workflow returns to Step 2 on completion (loop until "Done").
```

### Roster Display Format

```markdown
## Agent Team — [project name]

**3 agents configured** | post-plan: 2 | post-phase: 1

| Agent | Mode | Trigger | Status |
|-------|------|---------|--------|
| Security Auditor | advisory | post-plan | active |
| Rules Lawyer | advisory | post-plan | active |
| Doc Writer | autonomous | post-phase | active |

Run `/gsd:team` to manage. Run `/gsd:execute-phase` for agents to fire automatically.
```

---

## GSD-Native Agent Creation: `new-agent.md`

### Philosophy

Agent creation is deliberate, not automatic. The `/gsd:team add` path routes through a
guided workflow that uses the GSD plan+execute model internally to build each agent definition.
This ensures the agent definition is well-specified, tested against a fixture, and commitable.

### `new-agent.md` Step Sequence

```
Step 1: gather_intent (AskUserQuestion loop)
  What problem should this agent catch / artifact should it produce?
  What trigger should it fire on?
  Should it advise (findings) or act (autonomous artifact)?

Step 2: classify_mode
  Based on answers, classify: advisory | autonomous
  Present back to user for confirmation.

Step 3: gather_details (mode-specific)
  Advisory: focus area, criteria, severity thresholds, routing hints
             (identical flow to new-reviewer.md Step 4-5)
  Autonomous: artifact it produces, tools it needs, commit behavior,
               commit message template

Step 4: plan_agent_definition
  Spawn gsd-planner to write a PLAN.md for building the agent definition.
  The plan covers:
    - Agent file: ~/.claude/agents/{slug}.md
    - Role block content
    - TEAM.md update
  This is a single-plan phase (micro-phase).

Step 5: execute_agent_definition
  Spawn gsd-executor to execute the plan:
    - Write the agent definition file
    - Append role to TEAM.md
    - Commit both

Step 6: validate_agent
  Present the written agent definition for user review.
  AskUserQuestion: "Activate this agent?" → yes | edit | discard

Step 7: activate_or_iterate
  Yes → done; announce agent is live
  Edit → return to Step 3 with current values pre-filled
  Discard → delete written files, return to Step 1
```

### Why Plan+Execute Internally

The plan+execute model produces auditable, commitable output. The agent definition file is
not written speculatively — it's the output of an executed plan. This means:
1. The agent definition is in git (traceable)
2. The creation process itself can be reviewed
3. Failed agent definitions can be debugged like any other execution artifact

For a tool that builds agents, eating its own cooking is architecturally consistent.

---

## Trigger Data Flow

### Pre-Plan Trigger (hooks into `plan-phase.md`)

```
plan-phase.md Step 8 (planner complete) → Step 9 (handle planner return) → Step 13 (present final status)
                                                                                    │
                                                                    [pre_plan_agent_gate] ← INSERT HERE
                                                                                    │
                                                                              <offer_next>
```

**What pre-plan agents receive:**
- Phase identifier
- Phase goal (from ROADMAP.md)
- All PLAN.md file paths (plans are written but not executed)
- RESEARCH.md content (if phase research ran)
- CONTEXT.md content (if discuss-phase ran)

**Typical pre-plan advisory use:** A "Plan Quality Auditor" that checks plans for scope creep
or missing requirements coverage — separate from the built-in gsd-plan-checker.

**Typical pre-plan autonomous use:** Not recommended (plans not yet executed; no artifacts to write).

### Post-Plan Trigger (hooks into `execute-plan.md`) — EXISTING

```
execute-plan.md: update_codebase_map → [review_team_gate] → offer_next
```

The existing `review_team_gate` step body is updated to call `agent-dispatcher.md` instead
of `review-team.md` directly. The dispatcher routes advisory post-plan roles to the review
pipeline; autonomous post-plan roles to their agent definitions.

**What post-plan agents receive:**
- SUMMARY.md path (current plan)
- Phase identifier, plan number
- ARTIFACT.md path (after sanitizer runs for advisory roles)

### Post-Phase Trigger (hooks into `execute-phase.md`)

```
execute-phase.md: aggregate_results → [post_phase_agent_gate] → verify_phase_goal
```

**What post-phase agents receive:**
- Phase identifier
- Phase directory path
- List of all SUMMARY.md paths (one per plan)
- Phase goal (from ROADMAP.md)

**Typical post-phase advisory use:** Cross-plan consistency check — does the phase as a whole
tell a coherent story?

**Typical post-phase autonomous use:** Doc Writer updates API docs, Changelog Agent appends
to CHANGELOG.md, Test Coverage Reporter writes a coverage summary.

### On-Demand Trigger (via `/gsd:team`)

Dispatched manually from team-studio.md. User selects an agent, dispatcher calls it with
the current phase context. No workflow patch required — fully contained in the extension.

---

## Architectural Patterns

### Pattern 1: Trigger-Scoped Filtering

**What:** The dispatcher reads TEAM.md once and filters by the current trigger context.
Advisory post-plan roles flow to the existing review pipeline. All other roles flow to
their mode-specific execution path.

**Why:** Single dispatch entry point prevents N separate patch steps in GSD workflows.
Each workflow patch calls the dispatcher; the dispatcher handles all routing internally.

**Example:**
```
execute-plan.md calls: agent-dispatcher(trigger=post-plan)
agent-dispatcher finds:
  - security-auditor (advisory, post-plan) → review-team pipeline
  - rules-lawyer (advisory, post-plan)     → review-team pipeline
  - doc-writer (autonomous, post-phase)    → filtered out (wrong trigger)
  - pre-plan-checker (advisory, pre-plan)  → filtered out (wrong trigger)
```

### Pattern 2: Version Shim Before Processing

**What:** The parser applies version-specific defaults before any processing. Code downstream
of the parser never sees a "partially specified" role — every role has all fields.

**Why:** Prevents scattered `if version == 1 else` branches throughout the dispatcher,
studio, and any future consumers of TEAM.md.

**Implementation:**
```
function normalizeRole(role, version):
  if version < 2:
    role.mode = role.mode ?? "advisory"
    role.trigger = role.trigger ?? "post-plan"
    role.tools = role.tools ?? []
    role.output_type = role.output_type ?? "findings"
    role.commit = role.commit ?? false
  return role
```

### Pattern 3: Autonomous Agent Commit Isolation

**What:** Autonomous agents commit their own artifacts using gsd-tools. The dispatcher does
NOT commit on the agent's behalf. The agent file itself contains the commit logic.

**Why:** Agents have domain-specific knowledge about what constitutes a complete artifact.
A Doc Writer knows which markdown files it updated; the dispatcher doesn't. Keeping commit
logic inside the agent definition file makes each agent self-contained and auditable.

**Risk:** An autonomous agent that commits incorrectly cannot be easily undone by the dispatcher.
Mitigation: `commit: true` agents should be validated against a fixture before activation.

### Pattern 4: Advisory → Review Pipeline Passthrough

**What:** Advisory post-plan agents route to the existing `review-team.md` pipeline unchanged.
The review pipeline is not modified in v2.0. The dispatcher is an adapter, not a replacement.

**Why:** The v1.0 review pipeline is proven, tested, and working. Breaking changes to
review-team.md would require re-testing the entire sanitizer → reviewer → synthesizer chain.
The clean separation keeps v1.0 stable while v2.0 adds new paths around it.

---

## Anti-Patterns

### Anti-Pattern 1: Patching `execute-phase.md` for Post-Plan Triggers

**What people do:** Try to insert the post-plan agent gate into `execute-phase.md` (the phase
orchestrator) rather than `execute-plan.md` (the per-plan executor).

**Why it's wrong:** `execute-phase.md` runs once per phase. `execute-plan.md` runs once per
plan. Post-plan trigger fires after each plan — it must be in `execute-plan.md`.

**Do this instead:** Post-plan gate stays in `execute-plan.md` at `review_team_gate`.
Post-phase gate goes in `execute-phase.md` at `post_phase_agent_gate`.

### Anti-Pattern 2: New Config Flag per Agent Type

**What people do:** Add `workflow.advisory_agents`, `workflow.autonomous_agents`,
`workflow.pre_plan_agents` as separate flags.

**Why it's wrong:** Each new flag is another patch to `settings.md`, another gsd-tools concern,
another default to manage. Flags multiply; documentation falls behind.

**Do this instead:** Single `workflow.agent_studio` flag enables all agent types.
Per-agent activation is managed in TEAM.md itself (roles can be commented out to disable).

### Anti-Pattern 3: Breaking the Review Pipeline for Autonomous Routes

**What people do:** Modify `review-team.md` to also handle autonomous agents.

**Why it's wrong:** The review pipeline is sanitize → review → synthesize → route. Autonomous
agents don't produce findings — they produce artifacts. Mixing these into the review pipeline
forces the synthesizer to handle non-finding outputs, breaking its closed routing enum.

**Do this instead:** Dispatcher routes autonomous agents entirely outside the review pipeline.
Review pipeline stays advisory-only. Autonomous path is a parallel branch in the dispatcher.

### Anti-Pattern 4: Storing Agent Definitions in TEAM.md

**What people do:** Embed the full agent prompt/instructions in TEAM.md role blocks.

**Why it's wrong:** TEAM.md grows to thousands of lines. The `## Role:` parser becomes
complex. Version control diffs become unreadable.

**Do this instead:** TEAM.md stores configuration (mode, trigger, tools, output_type).
Agent instructions live in `~/.claude/agents/{slug}.md`. TEAM.md references the slug.
The dispatcher loads the agent file when spawning the Task().

---

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|--------------|-------|
| GSD workflow → dispatcher | Step body calls `@~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md` | Same `@` pattern as v1.0 |
| dispatcher → review-team pipeline | Direct workflow call with filtered role list | Unchanged v1.0 path |
| dispatcher → autonomous agent | `Task(subagent_type="{slug}", prompt=...)` | Standard Task() isolation |
| autonomous agent → git | `gsd-tools.cjs commit` | Agent commits own output |
| team-studio → new-agent | Direct workflow invocation | Contained within extension |
| new-agent → TEAM.md | Read-then-Write via gsd-tools pattern | Idempotent append |

### External Service Integrations

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| GSD patch system (reapply-patches) | Verbatim file backup + AI merge | Three new GSD workflow files modified; maintain small patch surface |
| gsd-tools.cjs | Read config.json directly via jq (no gsd-tools changes) | `workflow.agent_studio` readable via jq same as `workflow.review_team` |
| Claude Code Task() | Isolation boundary — each agent is a fresh API call | Autonomous agents must not receive previous agents' outputs |

---

## Build Order and Dependencies

This section maps architecture decisions to build sequence.

```
Phase 1: TEAM.md v2 schema + parser
  → Must complete before dispatcher can route
  → Validates backwards compatibility with installed v1.0 TEAM.md

Phase 2: agent-dispatcher.md
  → Depends on: TEAM.md v2 schema (Phase 1)
  → Post-plan path verifiable immediately (connects to existing review-team.md)

Phase 3: team-studio.md + /gsd:team command
  → Depends on: dispatcher (Phase 2), TEAM.md v2 (Phase 1)
  → On-demand trigger path requires dispatcher

Phase 4: Pre-plan trigger patch (plan-phase.md)
  → Depends on: dispatcher (Phase 2)
  → New GSD workflow patch; test with advisory agent only first

Phase 5: Post-phase trigger patch (execute-phase.md)
  → Depends on: dispatcher (Phase 2)
  → New GSD workflow patch; autonomous agents tested here

Phase 6: new-agent.md workflow (GSD-native creation)
  → Depends on: TEAM.md v2 schema (Phase 1), team-studio (Phase 3)
  → Plan+execute internal model is self-contained

Phase 7: new-project.md hook (agent_team_hook)
  → Depends on: team-studio (Phase 3), new-agent.md (Phase 6)
  → Last patch; only fires on project init, easy to test in isolation
```

---

## Scaling Considerations

This system runs in a developer tooling context — "scale" means teams/projects, not API traffic.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-5 agents | Current TEAM.md single-file approach works; dispatcher reads once |
| 5-15 agents | TEAM.md parse time negligible; consider role grouping in file for readability |
| 15+ agents | Split into per-agent files under `.planning/agents/`; TEAM.md becomes an index |

The 15+ agent split is not needed for v2.0. Design the TEAM.md parser to handle a future
`agent_file` field that references external files — enables the split without schema redesign.

---

## Sources

All findings derived directly from source code and installed files. No WebSearch required
for this architecture analysis.

| Source | Confidence | Artifact |
|--------|------------|----------|
| `~/.claude/get-shit-done-review-team/workflows/review-team.md` | HIGH | Step names, input contract, routing enum |
| `~/.claude/get-shit-done-review-team/workflows/new-reviewer.md` | HIGH | AskUserQuestion patterns, TEAM.md write format |
| `~/.claude/get-shit-done/workflows/execute-plan.md` | HIGH | All step names, `review_team_gate` location and body |
| `~/.claude/get-shit-done/workflows/execute-phase.md` | HIGH | All step names; `aggregate_results` and `verify_phase_goal` anchor |
| `~/.claude/get-shit-done/workflows/plan-phase.md` | HIGH | Step sequence (numbered), planner → checker → offer_next flow |
| `~/.claude/get-shit-done/workflows/new-project.md` | HIGH | Step 5 location, config.json write, Step 5.5 model resolution |
| `D:/GSDteams/.planning/TEAM.md` | HIGH | v1.0 schema: version, roles list, ## Role: format, YAML block fields |
| `D:/GSDteams/.planning/PROJECT.md` | HIGH | v2.0 requirements and vision |
| `.planning/research/GSD-EXTENSION-ARCH.md` | HIGH | Patch mechanism, config.json schema, `@` reference pattern |
| `.planning/research/GSD-AGENT-PATTERNS.md` | HIGH | Task() isolation, tool grants, structured return conventions |

---
*Architecture research for: GSD Agent Studio v2.0*
*Researched: 2026-02-26*
