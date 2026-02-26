# Stack Research

**Domain:** GSD Agent Studio — v2.0 milestone, adding agent lifecycle, team roster, autonomous agents, agent creation workflow, and new-project integration to the existing GSD Review Team extension
**Researched:** 2026-02-26
**Confidence:** HIGH — all findings verified directly from GSD source files (execute-plan.md, plan-phase.md, verify-work.md, new-project.md, settings.md, gsd-tools.cjs, install.sh, existing agents and workflows)

---

## What This Document Covers

This is a SUBSEQUENT MILESTONE research document. The v1.0 stack (Task() agent spawning, AskUserQuestion conversations, YAML-frontmatter agent files, XML step blocks, install.sh patching, finding-schema.md, TEAM.md format, gsd-tools.cjs commit/init/phase commands) is validated and NOT re-researched here.

This document covers ONLY what is new for v2.0 Agent Studio features:

1. Agent lifecycle triggers beyond post-plan (pre-plan, post-phase, on-demand)
2. `/gsd:team` roster command
3. Autonomous agent mode (file writes + command execution)
4. GSD-native agent creation workflow (plan + execute to build each new agent)
5. new-project integration that proposes agents based on project goals

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| GSD workflow markdown (XML step blocks) | Existing | All new workflows (agent-lifecycle.md, team-roster.md, new-agent.md) | Consistent with entire extension — Claude Code loads .md files natively via `@` references; no new runtime needed |
| YAML frontmatter in TEAM.md | Existing v1 schema + new `triggers:` and `mode:` fields | Declare per-agent trigger configuration and autonomy level | Extending the TEAM.md format keeps all agent configuration in one user-managed file |
| `.planning/config.json` workflow section | Existing schema + new `agent_studio:` subsection | Feature flags for autonomous mode, lifecycle hooks | Direct jq reads on `config_content` (already loaded in every init call) without touching gsd-tools.cjs |
| GSD `@`-reference file loading | Existing | Load new workflows from `~/.claude/get-shit-done-review-team/workflows/` | Extension already uses this pattern to load review-team.md — same mechanism for new workflows |
| Python 3 (install.sh patches) | Existing (3.x, no new version requirement) | New install.sh sections patching plan-phase.md, new-project.md, verify-work.md | Already used and proven for execute-plan.md and settings.md patches |
| bash + jq (trigger reads in patched workflows) | Existing | Read `workflow.agent_studio.*` flags and TEAM.md agent trigger config | Same pattern as `REVIEW_TEAM_ENABLED` check — zero new tooling |

### New File Types Required

| File | Location | Purpose | Why Needed |
|------|----------|---------|------------|
| `agent-lifecycle.md` | `workflows/agent-lifecycle.md` | Orchestrates pre-plan, post-phase, and on-demand trigger dispatch | Lifecycle is complex enough to warrant its own workflow (parallel spawning, per-trigger routing) — embedding it in execute-plan.md or plan-phase.md would bloat those files |
| `team-roster.md` | `workflows/team-roster.md` | Renders `/gsd:team` output — reads TEAM.md and produces formatted roster | Separating roster rendering from commands/gsd entry point keeps the command thin |
| `new-agent.md` | `workflows/new-agent.md` | GSD-native agent creation: gather requirements, write PLAN.md, execute it | Mirrors the new-reviewer.md pattern but targets full agent creation (not just reviewer roles); must output a complete .md agent file |
| `gsd-agent-builder.md` | `agents/gsd-agent-builder.md` | Subagent that writes new agent files from a spec | Needed because agent file generation follows strict GSD conventions (frontmatter, `<role>`, `<step>`, `<output>`, `<success_criteria>`) — a dedicated agent produces higher-quality output than inline generation |
| `team.md` (command entry) | `commands/gsd/team.md` | Entry point for `/gsd:team` slash command | All slash commands need a command entry in `commands/gsd/` |
| `new-agent.md` (command entry) | `commands/gsd/new-agent.md` | Entry point for `/gsd:new-agent` slash command | Same pattern as `/gsd:new-reviewer` command entry |

### TEAM.md Schema Additions

The TEAM.md YAML frontmatter needs two new per-role fields. The rest of the role body format is unchanged.

**Current role YAML block (v1):**
```yaml
name: security-auditor
focus: Security vulnerabilities and unsafe patterns
```

**Extended role YAML block (v2):**
```yaml
name: security-auditor
focus: Security vulnerabilities and unsafe patterns
triggers:
  - post-plan          # existing behavior — fires after each plan execution
  - post-phase         # new — fires after all plans in a phase complete
  - pre-plan           # new — fires before a plan executes
  - on-demand          # new — fires only when explicitly invoked
mode: review           # review | autonomous
autonomous_tools:      # only present when mode: autonomous
  - Read
  - Write
  - Bash
```

Why this extension rather than a separate file:
- All agent configuration stays in one place the user already manages
- Backward compatible — agents without `triggers:` default to `[post-plan]` (existing behavior preserved)
- The `mode:` field drives tool set declarations for autonomous agents, which must be explicit for security

### config.json Schema Addition

Add one new subsection to `.planning/config.json`:

```json
{
  "workflow": {
    "review_team": true,
    "agent_studio": {
      "lifecycle_hooks": false,
      "autonomous_mode": false
    }
  }
}
```

**`lifecycle_hooks`:** When `true`, the patched plan-phase.md, execute-plan.md, and verify-work.md run agent-lifecycle.md at the appropriate integration points. When `false`, nothing changes from v1 behavior.

**`autonomous_mode`:** Gate for enabling agents with `mode: autonomous`. Kept separate from `lifecycle_hooks` so users can enable lifecycle triggers without enabling file-write/command autonomy — those are distinct risk profiles.

Why a new subsection rather than flat `workflow.*` keys: keeps agent studio config grouped and readable; mirrors how `workflow.review_team` is already its own key within `workflow`.

### Integration Points with GSD Core Workflows

These are the specific hooks each new v2 feature requires. Each requires an install.sh Python patch.

| GSD Core File | Hook Location | What Gets Inserted | Feature Served |
|---------------|---------------|-------------------|----------------|
| `execute-plan.md` | Before `<step name="offer_next">` (existing `review_team_gate` already here) | Add `pre_plan_lifecycle` step BEFORE `<step name="load_prompt">` for pre-plan trigger | Pre-plan trigger (#1) |
| `execute-plan.md` | Extend the existing `review_team_gate` step | After review pipeline, also check `lifecycle_hooks` and fire post-plan agents | Post-plan lifecycle trigger (#1) |
| `plan-phase.md` | After planner returns plans (Step 9, after `PLANNING COMPLETE` confirmed) | New `post_phase_lifecycle` step that fires when all plans in a phase are complete | Post-phase trigger (#1) |
| `verify-work.md` | After `complete_session` step | New `on_demand_lifecycle` step | On-demand trigger from verify-work context (#1) |
| `new-project.md` | After Step 6 Research completes (after SUMMARY.md synthesized) | New `propose_agents` step that reads research SUMMARY.md and proposes relevant agent roles | new-project integration (#5) |
| `settings.md` | Existing AskUserQuestion block | Add two new toggles: "Lifecycle Hooks" and "Autonomous Mode" | Config management |

**Why NOT add a new hook to `execute-phase.md`:** execute-phase.md is the per-phase orchestrator; execute-plan.md is the per-plan executor. Post-plan hooks belong in execute-plan.md (already patched). Post-phase hooks belong in plan-phase.md (triggers after the planning + checking loop completes for the whole phase). This mirrors how the review_team_gate already operates.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `jq` (bash) | Existing | Parse `triggers:` and `mode:` from TEAM.md agent blocks | Needed in patched workflow steps to read per-agent configuration before deciding which agents to fire; same pattern as existing `REVIEW_TEAM_ENABLED` reads |
| `python3` | Existing 3.x | New install.sh patch scripts for plan-phase.md and new-project.md | Only needed for multi-line XML insertions; same Python script pattern already proven in patch-execute-plan.py and patch-settings.py |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| install.sh (extended) | Add new patch sections for plan-phase.md, new-project.md, settings.md (new toggles) | Existing install.sh structure: each patch is an idempotent Python3 script invocation anchored on a named `<step>` tag — add 2-3 new scripts following the same pattern |
| patch-plan-phase.py (new) | Insert `post_phase_lifecycle` step into plan-phase.md | Anchor on `<offer_next>` tag in plan-phase.md; same insertion pattern as patch-execute-plan.py |
| patch-new-project.py (new) | Insert `propose_agents` step into new-project.md | Anchor on `## 7. Define Requirements` heading; insert after Step 6 research completion block |

---

## Installation

No new runtime dependencies. All v2 additions use existing tooling.

```bash
# No new npm installs needed — extension is pure markdown workflows + Python patches
# install.sh additions (bash):
python3 "$EXT_DIR/scripts/patch-plan-phase.py"    "$GSD_DIR/get-shit-done/workflows/plan-phase.md"
python3 "$EXT_DIR/scripts/patch-new-project.py"   "$GSD_DIR/get-shit-done/workflows/new-project.md"
# settings.md gets a new patch section in the existing patch-settings.py
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Extend TEAM.md YAML with `triggers:` and `mode:` fields | Separate AGENTS.md file for agent configuration | Use a separate AGENTS.md if the TEAM.md format becomes unreadable (more than ~8 agents, complex configs). For v2 scope, TEAM.md extension is correct — keeps config collocated with role definitions |
| `workflow.agent_studio` subsection in config.json | Flat `workflow.lifecycle_hooks` and `workflow.autonomous_mode` keys | Use flat keys if only one or two new toggles are needed. A subsection is cleaner when multiple related flags exist and prevents key collision with future GSD core additions |
| Single `agent-lifecycle.md` workflow for all triggers | Separate workflow per trigger type (pre-plan-lifecycle.md, post-phase-lifecycle.md) | Use per-trigger workflows if trigger logic diverges significantly. A single workflow with trigger-type branching keeps the dispatch logic centralized and easier to audit |
| Python patch scripts (existing pattern) | Node.js patch scripts | Use Node.js if the patches need to parse JSON config or interact with gsd-tools.cjs. For simple XML insertions in markdown files, Python is sufficient and already proven |
| gsd-agent-builder.md as dedicated agent | Inline agent generation in new-agent.md workflow | Use inline generation only for very simple agents. For GSD-compliant agents (frontmatter + multiple XML sections + success criteria), a dedicated builder agent produces higher-quality output and is easier to test in isolation |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Modifying gsd-tools.cjs for trigger dispatch | Creates a hard runtime dependency on the GSD binary version; any gsd-tools update breaks the extension. v1 already proved this is avoidable | Read `triggers:` from TEAM.md directly via jq in the patched workflow steps |
| New file format (e.g., AGENTS.json) for autonomous agent declarations | A JSON file diverges from GSD's all-markdown convention; users would need to learn two configuration syntaxes | Extend YAML frontmatter in TEAM.md — single config location, same syntax users already know |
| Node.js server or daemon for lifecycle management | GSD runs entirely inside Claude Code; there is no runtime to host a server process | Use GSD `@`-reference loading pattern — agent-lifecycle.md is loaded by the patched workflow steps when needed, not by a persistent process |
| Web UI for agent studio management | Violates GSD's explicit constraint: no web framework; everything is text files in Claude Code | Slash commands (`/gsd:team`, `/gsd:new-agent`) plus direct TEAM.md editing — consistent with GSD conventions |
| Spawning agents from inside gsd-tools.cjs | gsd-tools is a CLI utility, not an orchestrator; Task() spawning must happen in workflow markdown | Keep Task() calls in workflow .md files where they belong |
| Global (cross-project) agent registry | Would require a new file format, a sync mechanism, and versioning — none of which GSD has infrastructure for | Per-project TEAM.md — consistent with how all GSD planning artifacts work |
| Giving autonomous agents unrestricted tool access | Autonomous agents writing files and running commands without declared tool constraints is a security risk | Declare `autonomous_tools:` explicitly in TEAM.md YAML; the `gsd-agent-builder.md` uses this list to set the agent's frontmatter `tools:` field |

---

## Stack Patterns by Variant

**If implementing pre-plan trigger only:**
- Patch execute-plan.md with `pre_plan_lifecycle` step before `load_prompt`
- Check `workflow.agent_studio.lifecycle_hooks` and TEAM.md `triggers: [pre-plan]` flag
- Because pre-plan is the simplest trigger with no dependencies on plan output

**If implementing autonomous mode:**
- Require explicit `autonomous_mode: true` in config.json AND `mode: autonomous` in the agent's TEAM.md YAML block
- Gate on both flags — one is project-level consent, the other is per-agent declaration
- Because autonomous agents can modify files and run commands; two explicit opt-ins prevent accidental enabling

**If implementing new-project agent proposals:**
- Read `research/SUMMARY.md` after the 5-agent parallel research completes (the research synthesizer writes SUMMARY.md)
- Look for domain/pitfall signals that map to known agent types (security domain → security-auditor role, performance domain → performance-analyst role)
- Present as AskUserQuestion multi-select so user can accept all, some, or none
- Because proposal quality depends on research output; running proposal before SUMMARY.md exists produces generic suggestions

**If implementing `/gsd:team` roster:**
- Read `.planning/TEAM.md` and render it as a formatted table of agent roles with their trigger and mode configuration
- Add counts: total agents, agents with lifecycle triggers, agents in autonomous mode
- Because the roster is read-only — it does not need a backing workflow file; the command entry can render directly without spawning a subagent

---

## Version Compatibility

| Component | Compatible With | Notes |
|-----------|-----------------|-------|
| TEAM.md `triggers:` field | GSD v1.19.x+ | Backward compatible — agents without `triggers:` default to `[post-plan]` in the agent-lifecycle.md dispatch logic |
| `workflow.agent_studio` in config.json | GSD v1.19.x+ | Additive — missing keys default to `false` via `// false` jq fallback; no config migration needed |
| plan-phase.md patch (post-phase hook) | GSD v1.19.x (anchor: `<offer_next>`) | Same anchor tag pattern as execute-plan.md patch; stable across minor GSD versions |
| new-project.md patch (propose_agents step) | GSD v1.19.x (anchor: `## 7. Define Requirements`) | Markdown heading anchor is less stable than XML tag anchor — patch script must handle heading text variation |

---

## Sources

- `D:/GSDteams/workflows/review-team.md` — HIGH confidence (verified existing trigger integration point)
- `C:/Users/gutie/.claude/get-shit-done/workflows/execute-plan.md` — HIGH confidence (read full step sequence; identified `review_team_gate` insertion point for pre-plan hook)
- `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md` — HIGH confidence (read full workflow; identified post-phase hook point after Step 9 PLANNING COMPLETE)
- `C:/Users/gutie/.claude/get-shit-done/workflows/verify-work.md` — HIGH confidence (read full workflow; identified `complete_session` as on-demand hook anchor)
- `C:/Users/gutie/.claude/get-shit-done/workflows/new-project.md` — HIGH confidence (read full workflow; identified Step 6 research-complete block as agent proposal insertion point)
- `C:/Users/gutie/.claude/get-shit-done/workflows/settings.md` — HIGH confidence (read AskUserQuestion block; confirmed extension pattern for new toggles)
- `D:/GSDteams/.planning/TEAM.md` — HIGH confidence (verified current TEAM.md YAML schema; confirmed backward-compatible extension approach)
- `D:/GSDteams/install.sh` — HIGH confidence (read full script; confirmed Python patch script pattern and idempotency checks)
- `D:/GSDteams/scripts/patch-execute-plan.py` — HIGH confidence (read implementation; confirmed anchor-based insertion pattern)
- `D:/GSDteams/commands/gsd/new-reviewer.md` — HIGH confidence (verified command entry format for new `/gsd:team` and `/gsd:new-agent` commands)
- `D:/GSDteams/.planning/research/GSD-EXTENSION-ARCH.md` — HIGH confidence (prior research on patch mechanism and config.json schema)
- `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` — HIGH confidence (prior research on agent file structure and Task() conventions)
- `D:/GSDteams/.planning/REQUIREMENTS.md` — HIGH confidence (v1 requirements; confirmed what is NOT in scope for re-research)

---

## Open Questions for Phase Planning

1. **TEAM.md YAML parser in bash:** Reading `triggers:` from TEAM.md requires parsing multi-value YAML arrays from bash. `jq` cannot parse YAML. The safest approach is: the agent-lifecycle.md workflow reads TEAM.md via the Read tool (not bash) and Claude parses the YAML in its reasoning. Flag this for the implementation phase — do NOT use bash YAML parsing.

2. **new-project.md patch anchor stability:** The `## 7. Define Requirements` heading is a markdown heading, not an XML tag. It is more likely to change across GSD versions than an XML `<step name="...">` anchor. The patch script should verify the anchor exists and warn (not fail) if it is missing.

3. **Autonomous agent tool isolation:** When an autonomous agent runs via Task(), its `tools:` frontmatter limits what Claude will do. But this is a trust boundary, not a hard sandbox. Document clearly in the new-agent workflow that `autonomous_tools:` is a declaration of intent, not a security guarantee.

4. **`/gsd:team` command rendering:** The roster command can render without a subagent (read TEAM.md directly in the command entry). Confirm during implementation whether a subagent is needed for formatting quality or if the command entry can render adequately.

---
*Stack research for: GSD Agent Studio v2.0 — agent lifecycle, team roster, autonomous agents, agent creation workflow, new-project integration*
*Researched: 2026-02-26*
