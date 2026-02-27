# Phase 11: Agent Creation /gsd:new-agent — Research

**Researched:** 2026-02-26
**Domain:** GSD workflow authoring — guided conversation, TEAM.md mutation, agent file creation, review pipeline bypass
**Confidence:** HIGH — all findings verified directly from source files in the repository

---

## Summary

Phase 11 delivers `/gsd:new-agent`, the guided conversation that creates a complete agent definition and writes it into the system. The command is the agent-authoring counterpart to `/gsd:new-reviewer` — it extends the same conversation pattern to cover the full v2 TEAM.md schema: mode, trigger, output_type, scope (autonomous only), and commit behavior. The resulting artifacts are a role block appended to `.planning/TEAM.md` and, if the agent requires a custom prompt, an agent markdown file at `agents/gsd-agent-{slug}.md`.

The phase does not use the plan+execute internal model described in ARCHITECTURE.md (`new-agent.md` Step Sequence). That was an earlier architectural exploration. The requirements (CREA-01 through CREA-04) and the ROADMAP success criteria specify a direct conversation + write pattern — the same pattern used by `new-reviewer.md` — with a decision gate before any file is written. Agent creation plans must carry `skip_review: true` in their frontmatter so DISP-03 bypass fires and no reviewer runs against agent definition files.

The two deliverables for Phase 11 are: (1) `workflows/new-agent.md` — the guided conversation workflow; and (2) `commands/gsd/new-agent.md` — the slash command entry point. Both follow the same file layout and convention as their `new-reviewer` counterparts. The team-studio `add_agent` step already contains a placeholder that routes to `/gsd:new-agent` — Phase 11 makes that route real.

**Primary recommendation:** Model `new-agent.md` directly on `new-reviewer.md`, extend the conversation to cover v2 fields, add autonomous-only scope questions, and gate writing on explicit user confirmation. The DISP-03 bypass applies to any GSD plan created _during_ the execution of this workflow — not to the workflow itself.

---

## Standard Stack

This phase is pure workflow and markdown authoring. There are no npm packages, no external libraries, and no new Python scripts. The "stack" is the existing GSD extension infrastructure.

### Core

| Component | Version/Location | Purpose | Why Standard |
|-----------|-----------------|---------|--------------|
| `workflows/new-agent.md` | New file | Guided conversation workflow | Same pattern as `new-reviewer.md` |
| `commands/gsd/new-agent.md` | New file | Slash command entry point | Same pattern as `commands/gsd/new-reviewer.md` |
| `.planning/TEAM.md` | Existing, v1 or v2 | Role block append target | Established schema from Phase 6 |
| `agents/gsd-agent-{slug}.md` | New file (conditional) | Custom agent prompt for autonomous agents | Follows `agents/gsd-*.md` naming convention |
| `gsd-tools.cjs commit` | Already installed | Commit all written files | CREA-04 requirement |

### Supporting

| Component | Location | Purpose | When to Use |
|-----------|---------|---------|-------------|
| `AskUserQuestion` | Claude Code built-in | Guided conversation UI | All decision points |
| `skip_review: true` | PLAN.md frontmatter | DISP-03 bypass signal | Any plan written during agent creation |
| `normalizeRole` algorithm | `agent-dispatcher.md`, `team-studio.md` | v2 defaults — new roles must be valid v2 | Role blocks must have all v2 fields |

### No New External Dependencies

```bash
# No npm install required — zero new dependencies
```

---

## Architecture Patterns

### Recommended File Structure (Phase 11 deliverables)

```
D:/GSDteams/
├── commands/gsd/
│   └── new-agent.md          # NEW: slash command entry point
├── workflows/
│   └── new-agent.md          # NEW: guided conversation workflow
└── agents/
    └── gsd-agent-{slug}.md   # NEW per agent (conditional — autonomous agents only)
```

### Pattern 1: Slash Command Entry Point (commands/gsd/new-agent.md)

**What:** A thin YAML-frontmatted markdown file that declares `name`, `description`, `allowed-tools`, and an `<execution_context>` that references the installed workflow path.

**When to use:** This is the only pattern used by all GSD extension commands.

**Example (from `commands/gsd/new-reviewer.md`):**
```markdown
---
name: gsd:new-agent
description: Create a new agent role through a guided conversation
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
Create a new agent role in `.planning/TEAM.md` through a guided conversation.

Walks through: purpose → domain → mode → trigger → output type → scope (autonomous only)
→ confirmation → write.

**Creates or updates:** `.planning/TEAM.md` and `agents/gsd-agent-{slug}.md` (if autonomous)
</objective>

<execution_context>
@~/.claude/get-shit-done-review-team/workflows/new-agent.md
</execution_context>

<process>
Follow the new-agent workflow end-to-end.
Preserve all gates including the decision gate before writing.
Do not write to .planning/TEAM.md or agents/ until the user confirms in the decision_gate step.
</process>
```

**Source:** `D:/GSDteams/commands/gsd/new-reviewer.md` (HIGH confidence — direct analog)

### Pattern 2: Guided Conversation Workflow (workflows/new-agent.md)

**What:** A `<purpose>` / `<inputs>` / `<step>` structured workflow that uses `AskUserQuestion` at every decision point, collects all fields needed for a v2 TEAM.md role block and optional agent file, shows a decision gate preview, and writes only on explicit confirmation.

**Step sequence (verified against new-reviewer.md and ARCHITECTURE.md):**

```
Step 1: check_team_md
  Check .planning/TEAM.md exists → read + count roles | note missing (create on write)

Step 2: gather_purpose
  "What problem should this agent catch or artifact should it produce?"
  Accept free-text via AskUserQuestion "Other" path
  Derive display name and slug from answer

Step 3: gather_mode
  "Should this agent advise or act autonomously?"
  Options: Advisory (produces findings/notes), Autonomous (produces artifacts)
  Store: mode = "advisory" | "autonomous"

Step 4: gather_trigger
  "When should this agent fire?"
  Options: pre-plan (before each plan is created), post-plan (after each plan executes),
           post-phase (after all plans in a phase complete), on-demand (manual only)
  Store: trigger = "pre-plan" | "post-plan" | "post-phase" | "on-demand"

Step 5: gather_output_type
  Conditional on mode:
    Advisory → "What type of output?" → notes (for pre-plan injection) | findings (review pipeline)
    Autonomous → "What artifact does this produce?" → artifact description
  Store: output_type = "notes" | "findings" | "artifact"

Step 6: gather_advisory_details  (mode == "advisory" only)
  Mirrors new-reviewer.md steps gather_criteria + gather_severity:
  - Review criteria checklist (domain-appropriate starter options)
  - Severity thresholds critical/major/minor
  - Routing hints standard vs. custom

Step 7: gather_scope  (mode == "autonomous" only)
  "What filesystem paths may this agent read or write?"
  → glob patterns for scope.allowed_paths
  "What tools does this agent need?"
  → tool names for scope.allowed_tools (Read, Write, Bash, Grep, Glob options)
  "Should this agent commit its own output?"
  → commit: true | false
  If commit: true → gather commit_message template
  Show scope preview and allow edit before proceeding

Step 8: decision_gate
  Assemble complete agent definition (role block + agent file if autonomous)
  Display to user: "Here is the agent definition that will be written:"
  [show full role block YAML + agent file content if applicable]
  AskUserQuestion: "Create this agent?" → Create | Edit details | Cancel

Step 9: write_agent
  If TEAM.md exists: Read → append role block → update frontmatter roles: list → Write
  If TEAM.md missing: create with version: 2 frontmatter + role block → Write
  If autonomous: write agents/gsd-agent-{slug}.md with agent prompt template
  Commit via gsd-tools.cjs
  Announce: "Agent '{display_name}' created. Run /gsd:team to see it in the roster."
```

### Pattern 3: TEAM.md Role Block Format (v2)

**What:** The exact YAML and markdown structure to append to TEAM.md for a new v2 agent. Derived from `templates/TEAM.md` Doc Writer example.

**Full role block for advisory agent:**
```markdown
---

## Role: {display_name}

```yaml
name: {slug}
focus: {focus_sentence}
mode: advisory
trigger: {trigger}
output_type: {notes | findings}
enabled: true
```

**What this role reviews:**
{criteria_list}

**Severity thresholds:**
- `critical`: {severity_critical}
- `major`: {severity_major}
- `minor`: {severity_minor}

**Routing hints:**
- Critical findings: `{routing_critical}`
- Major findings: `{routing_major}`
- Minor findings: `{routing_minor}`
```

**Full role block for autonomous agent:**
```markdown
---

## Role: {display_name}

```yaml
name: {slug}
focus: {focus_sentence}
mode: autonomous
trigger: {trigger}
output_type: artifact
commit: {true | false}
commit_message: "{commit_message_template}"
enabled: true

scope:
  allowed_paths:
    - "{glob_pattern_1}"
    - "{glob_pattern_2}"
  allowed_tools:
    - Read
    - Write
```

**What this role produces:**
{description_of_artifact}

**Severity thresholds:** N/A — autonomous agent does not produce findings

**Routing hints:** N/A — output_type: artifact
```

**Source:** `D:/GSDteams/templates/TEAM.md` Doc Writer role (HIGH confidence — canonical v2 example)

### Pattern 4: Autonomous Agent Prompt File (agents/gsd-agent-{slug}.md)

**What:** A new agent markdown file in `agents/` following the GSD agent file conventions from `GSD-AGENT-PATTERNS.md`. Contains YAML frontmatter + `<role>` + process steps + `<output>` + `<success_criteria>`.

**When to create:** Only for autonomous agents that need a custom prompt. Advisory agents use `gsd-reviewer.md` (parameterized via role injection) — no new file needed.

**Minimal template:**
```markdown
---
name: gsd-agent-{slug}
description: {one sentence — what it does, when triggered, what it produces}
tools: Read, Write    # expand based on scope.allowed_tools declared in TEAM.md
color: green          # green = quality-gate/content agent
---

<role>
You are a GSD autonomous agent: {display_name}.

Spawned by the agent-dispatcher workflow at trigger: {trigger}.

Your job: {purpose sentence from creation conversation}.

**Critical mindset:** {the one failure mode this agent must avoid}
</role>

<process>
[Agent-specific steps for producing the artifact]
</process>

<output>
**File produced:** {artifact path(s)}

**Return to dispatcher:**
```markdown
## AGENT COMPLETE

**Agent:** {display_name}
**Trigger:** {trigger}
**Artifact:** {path to produced file}
```
</output>

<success_criteria>
- [ ] Artifact written to declared path
- [ ] Artifact is complete (not a stub)
- [ ] Committed (if commit: true in TEAM.md)
</success_criteria>
```

**Source:** `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` sections 1.1–1.7 (HIGH confidence — synthesized from all existing GSD agent files)

### Pattern 5: DISP-03 Bypass via skip_review in PLAN.md frontmatter

**What:** Any PLAN.md generated during agent creation must include `skip_review: true` in its YAML frontmatter. The dispatcher's `check_bypass_and_config` step reads this flag and exits before spawning any reviewers.

**How the bypass works (from agent-dispatcher.md):**
```bash
SKIP_REVIEW=$(grep -m1 "^skip_review:" "$PLAN_PATH" 2>/dev/null | awk '{print $2}' || echo "false")
```
If SKIP_REVIEW is "true": dispatcher logs `Agent Dispatcher: skipped (agent creation plan — bypass active)` and returns immediately.

**CREA-04 implication:** The `new-agent.md` workflow itself does not create or execute GSD plans. It directly writes to TEAM.md and agents/. The bypass is therefore needed for plans that *describe* agent creation — i.e., a plan whose `task` is "run the `/gsd:new-agent` workflow." Such plans are out of scope for Phase 11 (Phase 12 may generate them during new-project setup), but the mechanism is already live from Phase 7.

**Key insight for planner:** CREA-04 says "Agent creation committed via gsd-tools.cjs. Review pipeline bypass (DISP-03) applies to the creation plan." The "creation plan" refers to any GSD PLAN.md that has agent creation as its task — not to the new-agent workflow itself. The workflow commits directly via gsd-tools; it does not route through the execute-plan pipeline.

### Pattern 6: TEAM.md Frontmatter Update (roles: list)

**What:** When appending a new role, the frontmatter `roles:` list must be updated. This requires Read-then-Write (never Write-only).

**Implementation pattern (from new-reviewer.md write_role step):**
```
1. Read current .planning/TEAM.md
2. Parse YAML frontmatter: extract roles: list
3. Add new slug to the list
4. Append --- separator + new role block to body
5. Write full updated content back
```

**Edge case — TEAM.md missing:** Create with `version: 2` frontmatter (not version: 1 — new agents always use v2 schema).

### Anti-Patterns to Avoid

- **Asking mode before purpose:** Users don't know if they want "advisory" or "autonomous" until they've articulated the problem. Gather purpose first, then mode.
- **Asking scope too early:** Scope questions (allowed_paths, allowed_tools) are only meaningful after the user understands what the agent does. Ask last, right before the decision gate.
- **Using version: 1 for new TEAM.md:** If TEAM.md doesn't exist, create it with `version: 2`. Version 1 triggers the compatibility shim which sets mode=advisory/trigger=post-plan defaults — wrong for newly created agents that may be autonomous.
- **Creating agent file for advisory agents:** Advisory agents use the parameterized `gsd-reviewer.md` agent (role block injected at spawn time). No separate agent file needed unless the advisory agent has highly specialized behavior.
- **Writing TEAM.md before decision gate:** The decision gate in step 8 is the only write gate. Nothing is written before the user selects "Create".
- **Using plan+execute internally:** ARCHITECTURE.md describes a "plan+execute inside new-agent" approach (Step 4: plan_agent_definition, Step 5: execute_agent_definition). The REQUIREMENTS and ROADMAP do not specify this — they specify a direct write pattern matching new-reviewer.md. Do not introduce plan+execute complexity.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| AskUserQuestion UI | Custom text input parsing | AskUserQuestion built-in | Standard GSD pattern; options + free-text "Other" path |
| Slug generation | Custom regex parser | Derive from display name: lowercase + hyphenate | All existing agents use this — security-auditor, rules-lawyer, doc-writer |
| TEAM.md append | Complex markdown parser | Read-then-Write with string append | Existing pattern in new-reviewer.md write_role step |
| Git commit | Direct `git add && git commit` | `gsd-tools.cjs commit "{message}" --files {paths}` | CREA-04 explicit requirement; gsd-tools handles path resolution |
| Bypass detection | New flag or config key | `skip_review: true` in PLAN.md frontmatter | Already implemented in DISP-03 (Phase 7); dispatcher reads it |
| Role validation | Schema validator | Inline checks before decision gate | Small data, not worth a library |

**Key insight:** All infrastructure exists. Phase 11 is workflow authoring, not new mechanism building. The hardest part is the conversation design — getting the right questions in the right order.

---

## Common Pitfalls

### Pitfall 1: Symmetric Question Sets for Advisory vs Autonomous

**What goes wrong:** The workflow asks all fields for all agents regardless of mode. Advisory agents don't need scope/commit fields. Autonomous agents don't need severity thresholds or routing hints. Users get confused by irrelevant questions.

**Why it happens:** Trying to handle all cases with a single linear question flow.

**How to avoid:** Branch after mode is determined (step 3). `gather_advisory_details` (step 6) fires only when `mode == "advisory"`. `gather_scope` (step 7) fires only when `mode == "autonomous"`.

**Warning signs:** If the workflow asks "What are your severity thresholds?" to a user who answered "autonomous," it has branched incorrectly.

### Pitfall 2: Writing Before Decision Gate

**What goes wrong:** Workflow writes to TEAM.md or creates agents/ files before the user confirms at the decision gate. CREA-02 is violated.

**Why it happens:** Trying to show "progress" by writing incrementally.

**How to avoid:** All writes happen in step 9 (`write_agent`) after the user selects "Create" at the decision gate. Steps 1-8 are read-only (except reading TEAM.md to check existence).

**Warning signs:** Any Write tool call before the decision_gate step is wrong.

### Pitfall 3: Incorrect TEAM.md Version on Creation

**What goes wrong:** When TEAM.md doesn't exist and new-agent creates it, using `version: 1` means the normalizeRole shim will override all explicit v2 fields with defaults. The newly created autonomous agent gets mode=advisory, trigger=post-plan defaults injected.

**Why it happens:** Copying the new-reviewer.md stub header which uses `version: 1`.

**How to avoid:** When new-agent.md creates a new TEAM.md, use `version: 2` in the frontmatter.

**Warning signs:** An autonomous agent appearing as advisory in /gsd:team after creation.

### Pitfall 4: Agent File for Advisory Agents

**What goes wrong:** Creating `agents/gsd-agent-{slug}.md` for advisory agents that use the standard findings/notes output types. This file is never called — the dispatcher uses `gsd-reviewer.md` parameterized with role injection for advisory agents.

**Why it happens:** Symmetry temptation — "both advisory and autonomous should have agent files."

**How to avoid:** Only create the agent file when `mode == "autonomous"`. Advisory agents are fully specified by their TEAM.md role block + the existing gsd-reviewer.md.

**Exception:** An advisory agent with highly specialized behavior (custom prompt, non-standard review logic) might need its own file — but this is an edge case not required for Phase 11.

**Warning signs:** `agents/gsd-agent-{slug}.md` exists for a role with `mode: advisory`.

### Pitfall 5: Missing or Wrong install.sh Registration

**What goes wrong:** The `commands/gsd/new-agent.md` file is in the source tree but never copied to `~/.claude/commands/gsd/` because install.sh isn't updated.

**Why it happens:** Section 5 of install.sh copies `commands/gsd/*.md` via glob — if new-agent.md is added to the source dir, it IS automatically picked up. No explicit install.sh change is needed.

**Why it matters:** This is actually a non-issue IF new-agent.md is placed in `commands/gsd/`. Verify this is the case. No additional patch script needed.

**Warning signs:** `/gsd:new-agent` command not found after running `bash install.sh`.

### Pitfall 6: Slug Collisions with Existing Roles

**What goes wrong:** User creates an agent with a slug that already exists in TEAM.md. Appending a duplicate `## Role: {slug}` section breaks the dispatcher's parser (it finds the first match only).

**Why it happens:** No collision check before writing.

**How to avoid:** In `write_agent` step, check that the derived slug does not already exist in TEAM.md's frontmatter `roles:` list before writing. If collision: offer slug with numeric suffix (e.g., `doc-writer-2`) or ask user to choose a different name.

**Warning signs:** `/gsd:team` shows two agents with the same name.

### Pitfall 7: Scope Fields for Advisory Agents Leaking into TEAM.md

**What goes wrong:** The scope section (allowed_paths, allowed_tools) appears in a TEAM.md role block for an advisory agent. This is valid YAML but misleading — the dispatcher never uses scope for advisory agents.

**Why it happens:** Generating the role block with all fields regardless of mode.

**How to avoid:** Only include scope fields when `mode == "autonomous"`. Advisory role blocks should not contain a `scope:` key.

---

## Code Examples

Verified patterns from source files:

### TEAM.md Append with Frontmatter Update

```markdown
<!-- Source: D:/GSDteams/workflows/new-reviewer.md write_role step -->
1. Read current .planning/TEAM.md with the Read tool
2. Parse YAML frontmatter: find the roles: list
3. Add {slug} to the roles: list
4. Append this to end of file body:
---

## Role: {display_name}

```yaml
name: {slug}
focus: {focus_sentence}
mode: {advisory | autonomous}
trigger: {trigger}
output_type: {findings | notes | artifact}
enabled: true
```

[additional fields per mode]
```
5. Write full updated TEAM.md using the Write tool
```

### gsd-tools.cjs Commit Call

```bash
# Source: D:/GSDteams/.planning/research/GSD-EXTENSION-ARCH.md
# Commit new TEAM.md + optional agent file
node ~/.claude/get-shit-done/bin/gsd-tools.cjs commit \
  "feat(agents): add {slug} agent role" \
  --files ".planning/TEAM.md" "agents/gsd-agent-{slug}.md"

# If only TEAM.md (advisory agent, no separate file):
node ~/.claude/get-shit-done/bin/gsd-tools.cjs commit \
  "feat(agents): add {slug} advisory agent" \
  --files ".planning/TEAM.md"
```

### DISP-03 Bypass in a Plan's YAML Frontmatter

```yaml
# Source: D:/GSDteams/workflows/agent-dispatcher.md check_bypass_and_config step
# Any PLAN.md describing agent creation work should include:
---
plan: 11-01
phase: 11-agent-creation-new-agent
skip_review: true    # DISP-03: dispatcher skips review pipeline for agent creation plans
---
```

### AskUserQuestion Mode Selection Pattern

```
# Source: D:/GSDteams/workflows/new-reviewer.md gather_domain step (adapted for mode)
AskUserQuestion([{
  question: "Should this agent advise (produce findings/notes) or act autonomously (produce artifacts)?",
  header: "Agent Mode",
  multiSelect: false,
  options: [
    { label: "Advisory",   description: "Produces findings or notes — read-only, never writes files" },
    { label: "Autonomous", description: "Produces artifacts — writes files, optionally commits" }
  ]
}])
```

### AskUserQuestion Trigger Selection Pattern

```
AskUserQuestion([{
  question: "When should this agent fire?",
  header: "Trigger",
  multiSelect: false,
  options: [
    { label: "Pre-plan",   description: "Before each plan is created — advisory notes only" },
    { label: "Post-plan",  description: "After each plan executes — review or findings" },
    { label: "Post-phase", description: "After all plans in a phase complete — docs, changelog" },
    { label: "On-demand",  description: "Manual only — run via /gsd:team" }
  ]
}])
```

### Decision Gate Preview Format

```
# Source: D:/GSDteams/workflows/new-reviewer.md decision_gate step (adapted for v2 fields)
AskUserQuestion([{
  question: "Ready to create this agent in .planning/TEAM.md?",
  header: "Confirm",
  multiSelect: false,
  options: [
    { label: "Create agent",  description: "Write the role definition (and agent file if autonomous)" },
    { label: "Edit details",  description: "Change something before writing" },
    { label: "Cancel",        description: "Discard — nothing will be written" }
  ]
}])
```

### Slug Derivation Pattern

```
# Derived from existing agent naming: security-auditor, rules-lawyer, doc-writer
slug = display_name
       .toLowerCase()
       .replace(/[^a-z0-9\s-]/g, '')  # strip special chars
       .trim()
       .replace(/\s+/g, '-')           # spaces to hyphens
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `new-reviewer.md` only for v1 advisory roles | `new-agent.md` for full v2 schema | Phase 11 (this phase) | All modes, triggers, output types, scope |
| `add_agent` in team-studio routes to `/gsd:new-reviewer` | `add_agent` routes to `/gsd:new-agent` | Phase 11 (this phase) | Full agent creation, not just reviewer roles |
| ARCHITECTURE.md describes plan+execute inside new-agent | Requirements specify direct-write pattern (same as new-reviewer) | Architecture research vs. CREA requirements | Simpler implementation — no nested plan creation |

**Important: team-studio.md already expects new-agent exists:**
The `add_agent` step in `D:/GSDteams/workflows/team-studio.md` currently tells users:
```
"For a full agent role (any mode, trigger, or output type): /gsd:new-agent is available
in a future update (Phase 11)"
```
Phase 11 must update this text to be a live route. This is an additional artifact in the plan.

---

## Open Questions

1. **Does team-studio.md need updating to route to /gsd:new-agent?**
   - What we know: `add_agent` step currently tells users `/gsd:new-agent` is in Phase 11
   - What's unclear: Whether the update is an explicit task in Phase 11's plan or falls naturally out of Phase 12
   - Recommendation: Include it in Phase 11 — the add_agent step text should be updated to actually route to `/gsd:new-agent` once it exists. This is a 2-3 line change to `team-studio.md`.

2. **What should gsd-agent-{slug}.md contain for autonomous agents?**
   - What we know: Autonomous agents need a custom prompt with their specific task logic
   - What's unclear: How much guidance can the creation workflow give? The user defines what the agent does.
   - Recommendation: Generate a template with the standard GSD agent structure (frontmatter + `<role>` + `<process>` stub + `<output>`) populated with the information gathered in conversation. Leave `<process>` as a structured stub the user can fill in later. Note in the success announcement: "Edit `agents/gsd-agent-{slug}.md` to add your agent's specific instructions."

3. **Should advisory agents with output_type:notes get a custom agent file?**
   - What we know: Notes agents currently use generic Task() prompts from the dispatcher; the advisor's TEAM.md block provides focus/domain context
   - What's unclear: Whether a custom file would improve notes agent quality
   - Recommendation: No custom file for Phase 11. Notes agents run via Task() with the role block injected — same as findings agents. If quality is a concern, that's Phase 12+ territory.

4. **Does CREA-04 require skip_review in a PLAN.md, or does it refer to the workflow's commit?**
   - What we know: DISP-03 bypass is triggered by `skip_review: true` in PLAN.md frontmatter. The new-agent workflow doesn't create a PLAN.md — it directly writes files.
   - What's unclear: "Agent creation committed via gsd-tools.cjs. Review pipeline bypass (DISP-03) applies to the creation plan." — does "creation plan" mean a PLAN.md that describes the agent creation task, or is it describing the internal behavior of the workflow?
   - Recommendation: CREA-04 is fully satisfied by: (a) committing via gsd-tools.cjs in write_agent step, and (b) ensuring any PLAN.md files generated by the planner during this phase carry `skip_review: true`. The workflow verification plan for Phase 11 should have `skip_review: true`. The workflow itself does not route through execute-plan, so no bypass is needed at runtime.

---

## Sources

### Primary (HIGH confidence)

All sources read directly from the repository. No WebSearch used — all domain knowledge is internal to the codebase.

- `D:/GSDteams/commands/gsd/new-reviewer.md` — slash command entry point pattern; `allowed-tools`, `execution_context`, `process` structure
- `D:/GSDteams/workflows/new-reviewer.md` — 7-step guided conversation; AskUserQuestion conventions; decision gate pattern; write_role Read-then-Write; TEAM.md append format
- `D:/GSDteams/workflows/team-studio.md` — `add_agent` step; confirms Phase 11 placeholder exists and needs live routing
- `D:/GSDteams/templates/TEAM.md` — v2 schema: Doc Writer role block with mode/trigger/output_type/commit/scope.allowed_paths/scope.allowed_tools
- `D:/GSDteams/workflows/agent-dispatcher.md` — DISP-03 bypass: `skip_review` flag extraction; `check_bypass_and_config` step
- `D:/GSDteams/install.sh` — Section 5 glob copy: `commands/gsd/*.md` copied automatically; no install.sh change needed for new-agent.md
- `D:/GSDteams/.planning/research/ARCHITECTURE.md` — `new-agent.md` step sequence; file structure; `agents/gsd-agent-{slug}.md` naming; TEAM.md append pattern; `gsd-tools.cjs commit` pattern
- `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` — GSD agent file structure: frontmatter, `<role>`, `<process>`, `<output>`, `<success_criteria>`; AskUserQuestion conventions; questioning philosophy
- `D:/GSDteams/.planning/REQUIREMENTS.md` — CREA-01 through CREA-04; DISP-03; v2 schema fields
- `D:/GSDteams/.planning/ROADMAP.md` — Phase 11 success criteria (verbatim); Plan count TBD; depends on Phase 6 and Phase 8
- `D:/GSDteams/.planning/STATE.md` — Phase 10 complete; Phase 11 next; all relevant decisions from phases 6-10 documented

### Secondary (MEDIUM confidence)

- `D:/GSDteams/.planning/TEAM.md` (live project file) — current v1 format with 3 roles; confirms slug naming convention; confirms write_role append pattern works
- `D:/GSDteams/.planning/phases/10-advisory-output-to-planner/10-VERIFICATION.md` — Phase 10 verified complete; all dispatcher wiring confirmed live

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all patterns exist in prior phases
- Architecture: HIGH — new-reviewer.md is the direct analog; v2 schema from templates/TEAM.md is the exact format; step sequence derived from requirements
- Pitfalls: HIGH — all pitfalls derived from reading actual source code and schema constraints, not speculation

**Research date:** 2026-02-26
**Valid until:** Stable — this domain changes only when TEAM.md schema or dispatcher changes (next relevant change would be Phase 12)

---

## Plan Count Recommendation

Based on the deliverables:

| Plan | Scope | Tasks |
|------|-------|-------|
| 11-01 | `workflows/new-agent.md` — full guided conversation workflow | 1 task: write new-agent.md workflow |
| 11-02 | `commands/gsd/new-agent.md` + `team-studio.md` `add_agent` update | 2 tasks: slash command entry point + team-studio routing update |

**Rationale:** Two plans match the established phase rhythm (prior phases all used 2 plans for workflow work). Plan 01 is the core workflow (the real work); Plan 02 is the wiring (command entry point + team-studio update). Both can be verified independently.

The `agents/gsd-agent-{slug}.md` template file is generated dynamically by the workflow at runtime — it is not a static file written in the plan. No separate plan for it.
