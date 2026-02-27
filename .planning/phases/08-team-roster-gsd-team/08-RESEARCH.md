# Phase 8: Team Roster /gsd:team - Research

**Researched:** 2026-02-26
**Domain:** GSD slash command conventions, TEAM.md v2 schema, interactive roster management, AGENT-REPORT.md design
**Confidence:** HIGH — all findings verified directly from GSD source files and prior phase artifacts on disk

---

## Summary

Phase 8 delivers `/gsd:team` — the conversational command for viewing and managing the agent
roster in TEAM.md. The command follows an identical structural pattern to `/gsd:new-reviewer`:
a thin command file in `commands/gsd/` that delegates to a workflow file in
`get-shit-done-review-team/workflows/`. The workflow is conversational, using `AskUserQuestion`
for all user interaction, and reads/writes `.planning/TEAM.md` directly via Read and Write tools.

The `enabled` field is new to Phase 8. It is not yet in the TEAM.md schema (the v2 template
in `templates/TEAM.md` has no `enabled` field). Phase 8 must add it as a per-role YAML field
alongside `mode`, `trigger`, etc. The dispatcher (Phase 7) has no `enabled` check — ROST-03
requires Phase 8 to patch the dispatcher to filter out `enabled: false` roles before routing.
This is a Phase 8 dispatcher patch, not a Phase 7 change.

`AGENT-REPORT.md` does not exist in any phase directory or in the codebase. Phase 8 must define
its format from scratch, analogous to `REVIEW-REPORT.md`. The requirement (ROST-02, LIFE-04) says
results are logged to `AGENT-REPORT.md`; LIFE-03 in REQUIREMENTS.md says it lives at
`.planning/phases/XX-name/AGENT-REPORT.md` (per-phase, same convention as REVIEW-REPORT.md).
On-demand invocation means the user picks an agent and an artifact path; the agent fires against
that artifact in the current session and the result is displayed inline and logged to AGENT-REPORT.md.

The install path for `/gsd:team` is `commands/gsd/team.md` in the source repo, which gets copied
by install.sh Section 5 (`cp "$EXT_DIR/commands/gsd/"*.md "$GSD_DIR/commands/gsd/"`) — the same
copy mechanism that already handles `new-reviewer.md`. No new install.sh logic is needed for the
command file. The workflow file (`team-studio.md`) is copied via the `workflows/*.md` glob in
Section 5 — also automatic.

**Primary recommendation:** Build Phase 8 as three independent deliverables: (1) `team-studio.md`
workflow (roster display + all roster actions), (2) `commands/gsd/team.md` entry point, and
(3) an `enabled` field patch to the dispatcher. All three are pattern-following with no new
dependencies.

---

## Standard Stack

### Core (no new dependencies)

| Component | Version/Tool | Purpose | Why Standard |
|-----------|-------------|---------|--------------|
| GSD command file (`commands/gsd/team.md`) | GSD conventions | Entry point for `/gsd:team` slash command | Same pattern as `commands/gsd/new-reviewer.md`; YAML frontmatter + `@` workflow reference |
| GSD workflow file (`team-studio.md`) | GSD conventions | Full roster display and management logic | Same pattern as `new-reviewer.md`, `review-team.md`, `agent-dispatcher.md` |
| `AskUserQuestion` | Claude Code built-in | Interactive user selection for all roster actions | Required for slash command interactivity; all GSD conversational commands use it |
| Claude `Read` + `Write` tools | Claude Code built-in | TEAM.md parsing and updating | jq cannot parse YAML; Read tool + in-context text parsing is the GSD standard |
| Claude `Bash` tool | Claude Code built-in | File existence checks, grep for last-activation timestamps | Standard GSD pattern |

### No New Dependencies

This phase introduces zero new npm packages, zero new Python libraries, zero new tools. All
operations use patterns already proven in prior phases.

---

## Architecture Patterns

### Pattern 1: GSD Slash Command File Structure

Source: `D:/GSDteams/commands/gsd/new-reviewer.md` (verified — exact current format)

```markdown
---
name: gsd:new-reviewer
description: Add a reviewer role to TEAM.md through a guided conversation
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
[One-line description of what the command does]

[Key walkthrough summary]

**Creates or updates:** `.planning/TEAM.md`
</objective>

<execution_context>
@~/.claude/get-shit-done-review-team/workflows/new-reviewer.md
</execution_context>

<process>
Follow the [workflow name] workflow end-to-end.
[One or two key constraints, e.g. "Do not write until user confirms"]
</process>
```

**For `/gsd:team`:**
- `name: gsd:team`
- `description: View and manage the agent team roster`
- `allowed-tools`: Read, Write, Bash, AskUserQuestion
- `execution_context`: `@~/.claude/get-shit-done-review-team/workflows/team-studio.md`

### Pattern 2: GSD Workflow File Structure

Source: `D:/GSDteams/workflows/agent-dispatcher.md` (verified — Phase 7 output)

```xml
<purpose>
[Description of what the workflow does]
[Source path and installed path]
[Calling point]
</purpose>

<inputs>
[All inputs the workflow receives, with examples]
</inputs>

<step name="step_name" priority="first">
[Step content in structured prose with bash code blocks]
</step>

<step name="step_name_2">
[Step content]
</step>
```

The workflow is a GSD `.md` file with `<purpose>`, `<inputs>`, and `<step name="...">` XML
blocks. Steps use structured prose interspersed with bash code blocks. No YAML frontmatter on
the workflow file itself (unlike command files which have YAML frontmatter).

### Pattern 3: TEAM.md Roster Read and Parse

The `AskUserQuestion` loop pattern in `new-reviewer.md` is the reference for the roster command:

1. Check TEAM.md exists (`bash: [ -f .planning/TEAM.md ]`)
2. Read it with the Read tool
3. Parse frontmatter: `version`, `roles` list
4. Parse each role section: find `## Role: {slug}`, extract YAML config block
5. Apply `normalizeRole(role, version)` to get all 8 fields (same as dispatcher)
6. Display the roster
7. Present action menu via `AskUserQuestion`
8. Handle selection and loop back or exit

### Pattern 4: AskUserQuestion Conventions

Source: `C:/Users/gutie/.claude/get-shit-done-review-team/workflows/new-reviewer.md` (verified)

```
AskUserQuestion([
  {
    question: "Question text here",
    header: "Short Header",          # ≤12 characters (established convention, Phase 05-02)
    multiSelect: false,
    options: [
      { label: "Option Label", description: "Longer description" },
      { label: "Another Option", description: "What it does" }
    ]
  }
])
```

**Constraints established in prior phases:**
- Headers capped at 12 characters (Phase 05-02 decision — applies to all roster action headers)
- 2-4 options per question (Phase 05 ROLE-02 requirement)
- Decision gate before any write action (prevents accidental mutations)

### Pattern 5: TEAM.md Write and Frontmatter Update

When toggling `enabled`, removing a role, or writing any change:

1. **Read current content** (Read tool)
2. **Modify in-context** (parse → mutate → serialize back to markdown)
3. **Write full file** (Write tool) — always overwrite the complete file, not append
4. **For role removal:** Also update the `roles:` frontmatter list to remove the slug

The YAML frontmatter `roles:` list is the authoritative index. Every role slug in the list must
have a matching `## Role: {slug}` block. When removing a role: remove slug from frontmatter list
AND remove the `---\n## Role: ...` block body.

Pattern source: `C:/Users/gutie/.claude/get-shit-done-review-team/workflows/new-reviewer.md`
write_role step — reads → parses frontmatter roles list → appends block → writes full file back.

### Pattern 6: REVIEW-REPORT.md Format (reference for AGENT-REPORT.md)

Source: `D:/GSDteams/.planning/phases/01-extension-scaffold-gsd-integration/REVIEW-REPORT.md`
(verified — actual output from review pipeline)

```markdown
# Review Report — Phase {phase-id}

---

## Plan {plan_num} — {ISO timestamp}

**Reviewers:** {comma-separated role names}
**Findings:** {N} | **Deduped:** {N}
**Action:** {routing_outcome}

| ID | Reviewer | Severity | Description | Evidence | Routing |
|----|----------|----------|-------------|----------|---------|
| SYNTH-001 | {reviewer} | {severity} | {description} | {evidence snippet} | {routing} |

---
```

**Location:** `.planning/phases/{phase-id}/REVIEW-REPORT.md` (per-phase, append-only)
**Write pattern:** Read-then-Write append — existing content preserved; each plan adds a new
`## Plan N` section (Phase 04-03 decision)

### Pattern 7: Recommended team-studio.md Step Sequence

Based on ARCHITECTURE.md's `team-studio.md` specification (HIGH confidence — verified from
`D:/GSDteams/.planning/research/ARCHITECTURE.md` line 417-438):

```
Step 1: show_roster (priority="first")
  - Check TEAM.md exists
  - Read and parse TEAM.md
  - Apply normalizeRole to all roles
  - Check each role's enabled status (default: true if field absent)
  - Display formatted roster table (enabled agents normal; disabled visually distinct)
  - Show summary counts by trigger type

Step 2: present_actions (AskUserQuestion)
  - "Add agent"          → route to /gsd:new-agent (launch workflow or inform user)
  - "Remove agent"       → select from roster, confirmation gate, delete role block
  - "Enable / Disable"   → select from roster, toggle enabled field, write back
  - "Run agent now"      → on-demand: select agent, select artifact, fire, log result
  - "View history"       → show AGENT-REPORT.md entries for agent (or all)
  - "Done"               → exit

Step 3: handle_selection
  - Route based on user choice
  - Loop back to Step 2 on completion (except "Done")
```

### Recommended File Layout After Phase 8

```
D:/GSDteams/
├── workflows/
│   ├── agent-dispatcher.md          UPDATED: enabled field check added
│   └── team-studio.md               NEW: /gsd:team roster + management workflow
├── commands/
│   └── gsd/
│       ├── new-reviewer.md          UNCHANGED
│       └── team.md                  NEW: entry point for /gsd:team
│
~/.claude/get-shit-done-review-team/
└── workflows/
    ├── review-team.md               UNCHANGED
    ├── new-reviewer.md              UNCHANGED
    ├── agent-dispatcher.md          UPDATED (copied by install.sh)
    └── team-studio.md               NEW (copied by install.sh)
~/.claude/commands/gsd/
    ├── new-reviewer.md              UNCHANGED
    └── team.md                      NEW (copied by install.sh)
```

### Anti-Patterns to Avoid

- **Parsing TEAM.md with jq or sed:** jq cannot parse YAML. Use the Read tool + in-context
  text parsing (established in Phase 6 and 7).

- **Making `enabled` a global config flag:** Per-agent enable/disable lives in the TEAM.md
  per-role YAML block as `enabled: false`. It is NOT a config.json flag. Per-role control is
  the only sensible design (you want to disable one agent, not all agents).

- **Requiring enabled field to be present:** Default is `enabled: true` (absent = enabled).
  Only `enabled: false` explicitly disables. This preserves all existing v1/v2 TEAM.md files
  without migration.

- **Calling the dispatcher from team-studio for on-demand:** On-demand invocation is
  orchestrated by `team-studio.md` directly. The dispatcher handles lifecycle triggers from
  GSD workflow steps. On-demand from the roster is a direct invocation pattern, not a trigger.

- **AGENT-REPORT.md as project-level file:** LIFE-03 specifies
  `.planning/phases/XX-name/AGENT-REPORT.md` (per-phase). The on-demand result goes to the
  current phase's AGENT-REPORT.md. This follows the same convention as REVIEW-REPORT.md.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing of TEAM.md | Custom awk/sed role extractor | Read tool + in-context text parsing | jq cannot parse YAML; bash YAML parsers are fragile; established GSD pattern from Phases 6/7 |
| Role block deletion | Line-number-based file surgery | In-context parse → rebuild without the role → Write full file | Line numbers change with edits; content-based rebuild is reliable |
| Interactive menu | Custom input loop | AskUserQuestion | Claude Code's built-in interactive UI; GSD convention for all conversational commands |
| Enabled field detection | Separate config.json toggle | Per-role `enabled` field in TEAM.md YAML block | Dispatcher already reads TEAM.md; per-role enables are co-located with role definition |
| AGENT-REPORT.md formatting | Custom markdown builder | Hand-written table following REVIEW-REPORT.md format | REVIEW-REPORT.md format is verified and readable; match it for consistency |

**Key insight:** Every operation in this phase is pattern-following. The entire phase is
"apply the patterns established in Phases 5-7 to a new command."

---

## Common Pitfalls

### Pitfall 1: Forgetting the Dispatcher `enabled` Check

**What goes wrong:** Phase 8 adds `enabled: false` to TEAM.md and the roster shows the agent
as disabled, but the dispatcher (Phase 7's `agent-dispatcher.md`) does not check `enabled`.
On the next `/gsd:execute-plan` run, the disabled agent fires anyway. ROST-03 fails.

**Why it happens:** The dispatcher was built in Phase 7 without the `enabled` field (it did
not exist yet). Phase 8 must patch the dispatcher to add an `enabled` check after normalizeRole
and before `filter_by_trigger`. Specifically: in the `read_and_parse_team_md` step, after
applying `normalizeRole`, filter out roles where `enabled == false`.

**How to avoid:** Phase 8 must update `D:/GSDteams/workflows/agent-dispatcher.md` to add:
```
enabled_roles = [role for role in normalized_roles if role.enabled != false]
```
Then pass `enabled_roles` (not `normalized_roles`) to the filter_by_trigger step.

**Warning signs:** After Phase 8, a disabled agent still shows up in REVIEW-REPORT.md output
on the next plan execution.

### Pitfall 2: `enabled` Default Value Must Be `true` (not absence-based logic)

**What goes wrong:** The dispatcher checks `if role.enabled == false` but the field is absent
for all existing v1/v2 roles. If `normalizeRole` does not inject `enabled: true` as the default,
the check `role.enabled != false` would be `undefined != false` = `true` (correct by accident
in JavaScript but wrong in GSD workflow prose-logic where absence is ambiguous).

**How to avoid:** Add `enabled` to the normalizeRole shim defaults:
```
if version < 2:
  ...
  role.enabled = role.enabled ?? true
```
And add the same default for v2 roles when the field is absent (even v2 roles may omit `enabled`).
Better: the normalizeRole shim should inject `enabled: true` for ALL roles regardless of version,
since enabled/disabled is a management state, not a schema version concern.

**Warning signs:** Newly added v2 agents (with all fields) are incorrectly treated as disabled.

### Pitfall 3: Remove Agent Without Confirmation Gate

**What goes wrong:** User accidentally removes the wrong agent. No undo mechanism exists.

**Why it happens:** Remove is a destructive operation. The `new-reviewer.md` pattern uses a
decision gate before any write. Remove must do the same.

**How to avoid:** Remove flow: (1) Show list of agents, user selects one. (2) Show full role
block preview. (3) AskUserQuestion: "Remove [Agent Name]?" with options "Remove" / "Cancel".
Only write after explicit "Remove" confirmation. Follow the `decision_gate` step pattern from
`new-reviewer.md`.

**Warning signs:** Remove writes to TEAM.md before the user confirmation step.

### Pitfall 4: On-Demand Invocation Does Not Log to AGENT-REPORT.md

**What goes wrong:** The on-demand result is displayed inline in the conversation but not
written to AGENT-REPORT.md. ROST-02 and LIFE-04 both require logging.

**Why it happens:** The inline display is visible; writing to disk is easy to skip.

**How to avoid:** After the agent fires and returns its result, always write an entry to
`.planning/phases/{current_phase_id}/AGENT-REPORT.md`. The format follows REVIEW-REPORT.md
conventions: a section header with timestamp, agent name, artifact path, and the result.
If AGENT-REPORT.md does not exist: create it. If it exists: append the new section (Read-then-Write).

**Warning signs:** Running `/gsd:team` → "Run agent now" produces output inline but
`.planning/phases/XX/AGENT-REPORT.md` is empty or does not exist after the run.

### Pitfall 5: `team-studio.md` Does Not Loop Back to the Action Menu

**What goes wrong:** After enabling/disabling an agent or viewing history, the workflow exits
instead of returning to the action menu. User must re-run `/gsd:team`.

**Why it happens:** Single-shot AskUserQuestion without a loop.

**How to avoid:** The `present_actions` step always loops: after each operation completes,
return to `present_actions` (Step 2) and re-show the updated roster. Only "Done" exits.
This is the pattern used in ARCHITECTURE.md: "Each sub-workflow returns to Step 2 on completion
(loop until 'Done')."

**Warning signs:** After enabling an agent, the command exits without giving the user further
options.

### Pitfall 6: Install.sh Needs No New Section for team.md Command

**What goes wrong:** A separate copy step is added to install.sh for `commands/gsd/team.md`,
duplicating what the existing Section 5 glob already handles.

**Why it happens:** Forgetting that Section 5 already copies `commands/gsd/*.md` via:
```bash
cp "$EXT_DIR/commands/gsd/"*.md "$GSD_DIR/commands/gsd/"
```

**How to avoid:** Do NOT add a special case in install.sh. `commands/gsd/team.md` is picked up
automatically. Same applies to `team-studio.md` — covered by the `workflows/*.md` glob. No
install.sh changes needed for Phase 8's command and workflow files.

**Warning signs:** install.sh has a redundant explicit copy for `team.md` or `team-studio.md`.

### Pitfall 7: Assuming `new-agent` Workflow Exists

**What goes wrong:** Phase 8's "Add agent" action tries to call `@~/.claude/get-shit-done-review-team/workflows/new-agent.md` but that file is Phase 11 scope. The call fails.

**Why it happens:** ROST-02 says "add agent → /gsd:new-agent". But `/gsd:new-agent` is built
in Phase 11, not Phase 8.

**How to avoid:** The "Add agent" action in Phase 8 should inform the user: "To add an agent,
run `/gsd:new-reviewer` for a review role (available now) or `/gsd:new-agent` when it becomes
available (Phase 11)." OR route "Add agent" to `/gsd:new-reviewer` for Phase 8 (which is the
only agent creation path currently available). The planner must make this decision explicitly.

**Warning signs:** Phase 8 workflow contains `@~/.claude/get-shit-done-review-team/workflows/new-agent.md`.

---

## Code Examples

Verified patterns from existing source files:

### Command File Structure (for team.md)

```markdown
<!-- Source: D:/GSDteams/commands/gsd/new-reviewer.md -->
---
name: gsd:team
description: View and manage the agent team roster
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
View and manage all configured agents in .planning/TEAM.md.

Displays a formatted roster with name, mode, triggers, output_type, and enabled status.
From the roster: add an agent, remove an agent with confirmation, enable or disable an agent,
invoke an agent on-demand against a specified artifact, or view agent history.

**Reads and writes:** `.planning/TEAM.md`
**Logs on-demand results to:** `.planning/phases/{current_phase}/AGENT-REPORT.md`
</objective>

<execution_context>
@~/.claude/get-shit-done-review-team/workflows/team-studio.md
</execution_context>

<process>
Follow the team-studio workflow end-to-end.
Do not write to .planning/TEAM.md until the user confirms any destructive action.
</process>
```

### Roster Display Format (from ARCHITECTURE.md — verified)

```markdown
<!-- Source: D:/GSDteams/.planning/research/ARCHITECTURE.md line 441-454 -->

## Agent Team — [project name]

**3 agents configured** | post-plan: 2 | post-phase: 1

| Agent | Mode | Trigger | Output | Status |
|-------|------|---------|--------|--------|
| Security Auditor | advisory | post-plan | findings | active |
| Rules Lawyer     | advisory | post-plan | findings | active |
| Doc Writer       | autonomous | post-phase | artifact | **disabled** |
```

Disabled agents appear in the table but are visually distinguished: bold, strikethrough, or
`disabled` status label. In markdown, `**disabled**` (bold) is the most portable visual marker
since strikethrough (`~~text~~`) is not standard CommonMark.

### `enabled` Field in TEAM.md YAML Block (new for Phase 8)

```yaml
<!-- Per-role YAML block — enabled field is optional, defaults to true if absent -->
name: doc-writer
focus: Keeps documentation in sync with implementation
mode: autonomous
trigger: post-phase
output_type: artifact
commit: true
commit_message: "docs(auto): update docs after phase {phase}"
enabled: false           # NEW: add this field to disable/enable the agent
scope:
  allowed_paths:
    - "docs/**"
    - "*.md"
```

### Dispatcher `enabled` Check (Phase 8 patch to agent-dispatcher.md)

```
<!-- In read_and_parse_team_md step — AFTER applying normalizeRole to all roles -->

Apply enabled default:
  For each role in normalized_roles:
    if role.enabled field is absent or null:
      role.enabled = true
    # (this ensures existing roles without the field are treated as enabled)

Then filter out disabled roles:
  active_roles = [role for role in normalized_roles if role.enabled == true]

Pass active_roles (not normalized_roles) to filter_by_trigger step.
```

### AGENT-REPORT.md Format (new — derived from REVIEW-REPORT.md pattern)

```markdown
<!-- Source: D:/GSDteams/.planning/phases/01-extension-scaffold-gsd-integration/REVIEW-REPORT.md -->
<!-- AGENT-REPORT.md follows the same per-phase append pattern -->

# Agent Report — Phase {phase-id}

---

## On-Demand: {agent-slug} — {ISO timestamp}

**Agent:** {agent display name}
**Mode:** {advisory | autonomous}
**Artifact:** {path to artifact the agent ran against}
**Invoked by:** on-demand (/gsd:team)

### Result

{Agent output — findings table (for advisory) or artifact path (for autonomous)}

---
```

**Location:** `.planning/phases/{phase-id}/AGENT-REPORT.md` (per-phase — same convention as
REVIEW-REPORT.md). Created on first on-demand invocation. Subsequent invocations append.

### Remove Role Flow (prose pattern from new-reviewer.md decision_gate)

```
Step: remove_agent

1. Present current role list as AskUserQuestion options (each agent is one option, plus "Cancel")
2. User selects an agent slug to remove
3. Read TEAM.md, extract the full role block for that slug
4. Show the role block to the user
5. AskUserQuestion:
   {
     question: "Remove this agent from TEAM.md? This cannot be undone.",
     header: "Remove",
     multiSelect: false,
     options: [
       { label: "Remove", description: "Delete role block and remove from roles list" },
       { label: "Cancel", description: "Return to roster" }
     ]
   }
6. If "Remove":
   - Remove slug from frontmatter roles: list
   - Remove the --- separator + ## Role: {slug} block through the next ---
   - Write full updated TEAM.md
   - Announce: "Agent '{role_display_name}' removed from TEAM.md."
7. If "Cancel": return to present_actions
```

### On-Demand Invocation Flow (from ARCHITECTURE.md + LIFE-04 requirement)

```
Step: invoke_on_demand

1. AskUserQuestion: select which agent to invoke (show only enabled agents + mode/trigger)
2. AskUserQuestion: "What artifact should this agent run against?"
   - Options: recent SUMMARY.md files (list them), or "Enter path manually"
3. Derive current phase_id from the artifact path or from .planning/phases/ directory listing
4. Run the agent:
   - For advisory agents: similar to Task() spawning in review pipeline
     Pass: artifact content + role definition from TEAM.md
   - For autonomous agents: spawn Task() with role definition + artifact context
5. Display result inline in the conversation
6. Log to AGENT-REPORT.md:
   Read .planning/phases/{phase_id}/AGENT-REPORT.md (or start fresh if missing)
   Append: ## On-Demand: {agent-slug} — {timestamp} section with result
   Write back
7. Announce: "Result logged to .planning/phases/{phase_id}/AGENT-REPORT.md"
8. Return to present_actions
```

---

## Research Answers: Phase 8 Questions

### Q1: What does /gsd:new-reviewer look like structurally?

**Answer (HIGH confidence):** The command file is at `D:/GSDteams/commands/gsd/new-reviewer.md`
(source) and `C:/Users/gutie/.claude/commands/gsd/new-reviewer.md` (installed). It has:
- YAML frontmatter: `name`, `description`, `allowed-tools`
- `<objective>` block: one-line description + key walkthrough summary
- `<execution_context>` block: `@~/.claude/get-shit-done-review-team/workflows/new-reviewer.md`
- `<process>` block: one or two behavioral constraints

The workflow file at `C:/Users/gutie/.claude/get-shit-done-review-team/workflows/new-reviewer.md`
contains the full step-by-step logic with `<step name="...">` blocks and `AskUserQuestion` calls.

`/gsd:team` follows this exact same split: thin command file delegates to workflow file.

### Q2: Where are GSD skill/command files installed?

**Answer (HIGH confidence):** Slash command `.md` files live at:
- Source: `D:/GSDteams/commands/gsd/*.md`
- Installed: `~/.claude/commands/gsd/*.md`

Install.sh Section 5 copies them:
```bash
cp "$EXT_DIR/commands/gsd/"*.md "$GSD_DIR/commands/gsd/"
```

The `GSD_DIR` is `~/.claude` (the directory containing `get-shit-done/`). The command file name
is the part after `gsd:` in the slash command — `team.md` for `/gsd:team`.

### Q3: How does `enabled` field get added to TEAM.md?

**Answer (HIGH confidence):** The `enabled` field is added ONLY at the per-role YAML block
level. It is NOT in the frontmatter. The YAML frontmatter `roles:` list still contains all
roles (both enabled and disabled). Only the dispatcher checks `enabled` status at dispatch time.

The field is purely optional — absent means enabled (default: true). When the user disables an
agent via `/gsd:team`, the workflow writes `enabled: false` into the role's YAML config block.
When re-enabling, it either removes the field or sets `enabled: true`.

No template update required to add the field — it's optional and self-describing.

### Q4: How does the dispatcher check `enabled`?

**Answer (HIGH confidence):** This is a Phase 8 change. The dispatcher (built in Phase 7)
does not currently check `enabled`. Phase 8 must patch `workflows/agent-dispatcher.md` to
add an `enabled` filter in the `read_and_parse_team_md` step, after `normalizeRole` is applied.
The patch is a content edit to `agent-dispatcher.md`, NOT a Python patch script (the dispatcher
is a workflow file, not a GSD core file). Phase 8 directly edits the source file.

Since `agent-dispatcher.md` is a source file in `D:/GSDteams/workflows/`, Phase 8 edits it
directly using the Write tool. install.sh Section 5's glob copy (`workflows/*.md`) will copy
the updated file on next install run.

### Q5: What is the AGENT-REPORT.md format and location?

**Answer (MEDIUM confidence — derived from REVIEW-REPORT.md pattern and REQUIREMENTS.md):**
- Location: `.planning/phases/{phase-id}/AGENT-REPORT.md` (per-phase)
- Format: Same append-with-section-header pattern as REVIEW-REPORT.md
- Created on first on-demand invocation for that phase (not pre-created)
- Section header: `## On-Demand: {agent-slug} — {ISO timestamp}`

The REQUIREMENTS.md LIFE-03 confirms per-phase: "`.planning/phases/XX-name/AGENT-REPORT.md`".
The exact section format for on-demand invocations (LIFE-04) is new to Phase 8.

### Q6: How does on-demand invocation work?

**Answer (MEDIUM confidence — from REQUIREMENTS.md LIFE-04, ROST-02, ARCHITECTURE.md):**
"Fire agent against specified artifact" means:
1. User picks an agent from the roster
2. User specifies an artifact path (a SUMMARY.md, ARTIFACT.md, or any file)
3. The workflow reads the artifact and the agent's role definition
4. For advisory agents: spawn a Task() with the artifact content + role definition as prompt context
5. Display result inline
6. Log to AGENT-REPORT.md

The "artifact" in on-demand context is flexible — it could be any `.md` file the user points to.
The advisory agent receives: (a) the artifact content, (b) its role definition from TEAM.md.
The autonomous agent receives: (a) trigger context `on-demand`, (b) the artifact path, (c) its
role definition.

### Q7: What is the remove agent flow?

**Answer (HIGH confidence — derived from new-reviewer.md pattern):**
1. User selects agent to remove from a list
2. System shows the full role block (preview)
3. Confirmation gate: "Remove this agent? This cannot be undone."
4. On confirm: read TEAM.md, remove slug from `roles:` frontmatter list, remove the role block
   (the `---` separator + `## Role: {slug}` block body through the next `---`)
5. Write full updated TEAM.md
6. Return to present_actions

The role block starts at the `---` separator before the `## Role:` header and extends to the
next `---` separator (or EOF). The frontmatter `roles:` list must be updated too.

### Q8: How should disabled agents appear in the roster?

**Answer (HIGH confidence — from REQUIREMENTS.md + markdown visual conventions):**
"Visually distinguished" in markdown means one of:
- Status column value: `**disabled**` (bold for visual emphasis)
- Row prefix: `~~Agent Name~~` (strikethrough — note: not standard CommonMark, may not render)
- Recommended: Use a Status column with `active` / `**DISABLED**` values

The ARCHITECTURE.md roster example shows a `Status` column with `active`. Phase 8 must use
`active` for enabled agents and a visually distinct value (bold or capitalized) for disabled.

### Q9: Does /gsd:team need special install.sh treatment?

**Answer (HIGH confidence — verified from install.sh Section 5):**
No. install.sh already handles both files automatically:
- `commands/gsd/team.md` → copied by `cp "$EXT_DIR/commands/gsd/"*.md "$GSD_DIR/commands/gsd/"`
- `team-studio.md` → copied by `cp "$EXT_DIR/workflows/"*.md "$EXT_INSTALL_DIR/workflows/"`

The `agent-dispatcher.md` update is also covered by the same workflows glob copy.
No new install.sh sections needed. No new patch scripts needed.

---

## State of the Art

| Old Approach | Current Approach (Phase 8) | Why Changed |
|--------------|---------------------------|-------------|
| Review team roles only in TEAM.md | Full agent roster with mode/trigger/enabled per role | v2 schema adds agent types beyond reviewers |
| No per-agent enable/disable | `enabled: false` in role YAML block | User needs to temporarily disable an agent without deleting it |
| REVIEW-REPORT.md only for findings | AGENT-REPORT.md for on-demand invocation results | LIFE-04 requires separate log for on-demand results |
| No `/gsd:team` command | Conversational roster management | ROST-01/02/03 requirements |

---

## Open Questions

1. **"Add agent" routing in Phase 8 (Phase 11 dependency)**
   - What we know: ROST-02 says "add agent → /gsd:new-agent". `/gsd:new-agent` is Phase 11 scope.
   - What's unclear: Should Phase 8's "Add agent" option route to `/gsd:new-reviewer` (the only
     agent creation path currently available) or inform the user that `/gsd:new-agent` is coming?
   - Recommendation: Route "Add agent" to `/gsd:new-reviewer` for Phase 8 scope. Add a note:
     "This creates a review-team role. Full agent creation (/gsd:new-agent) is available in a
     future update." This satisfies ROST-02 partially without blocking on Phase 11.

2. **How to determine "current phase" for AGENT-REPORT.md path in on-demand context**
   - What we know: On-demand fires from `/gsd:team`, not from within a plan execution. There is
     no `PHASE_ID` in scope the way there is inside `execute-plan.md`.
   - What's unclear: How does team-studio.md know which phase directory to write AGENT-REPORT.md to?
   - Recommendation: Ask the user to select from available phase directories, OR derive from the
     artifact path the user selected (the artifact is likely inside a phase directory). If the
     user enters a path outside any phase directory, default to the most-recently-modified phase
     directory (`ls -t .planning/phases/ | head -1`).

3. **Whether dispatcher patch to agent-dispatcher.md requires a Python script or direct edit**
   - What we know: Phase 7 used a Python patch script for execute-plan.md because that is a
     GSD core file. agent-dispatcher.md is a project source file.
   - What's unclear: Should Phase 8 edit agent-dispatcher.md directly (via the Write tool in
     a plan task) or write a patch script?
   - Recommendation: Direct edit. agent-dispatcher.md is owned by this project. A patch script
     is only needed for GSD core files (execute-plan.md, settings.md) to preserve idempotency
     across GSD version updates. For project-owned workflow files, direct Write is simpler and
     correct.

4. **`enabled` field default in normalizeRole — version-scoped or universal**
   - What we know: normalizeRole currently only injects defaults when `version < 2`. The `enabled`
     field is a management concern, not a schema version concern.
   - What's unclear: Should `enabled: true` default be injected by normalizeRole for all roles
     (regardless of version) or only for version < 2?
   - Recommendation: Inject `enabled: true` default for ALL roles regardless of version (even v2
     roles may omit the field). This is cleaner than version-gating a management field.

---

## Sources

### Primary (HIGH confidence)

- `D:/GSDteams/commands/gsd/new-reviewer.md` — Exact command file structure: YAML frontmatter,
  `<objective>`, `<execution_context>`, `<process>` blocks
- `C:/Users/gutie/.claude/commands/gsd/new-reviewer.md` — Installed command file (same content
  as source); confirms copy mechanism works for `/gsd:team`
- `C:/Users/gutie/.claude/get-shit-done-review-team/workflows/new-reviewer.md` — Full workflow
  file structure: `<purpose>`, `<inputs>`, `<step>` blocks; AskUserQuestion pattern with 12-char
  headers and 2-4 options; decision_gate pattern; write_role Read-then-Write pattern
- `D:/GSDteams/workflows/agent-dispatcher.md` — Current Phase 7 dispatcher; confirmed: no
  `enabled` field check, uses `normalizeRole`, 4 step blocks, `<purpose>/<inputs>/<step>` structure
- `D:/GSDteams/install.sh` — Section 5 glob copy confirmed: `commands/gsd/*.md` and
  `workflows/*.md` are both covered automatically; no new install.sh section needed for Phase 8
- `D:/GSDteams/.planning/TEAM.md` — Live TEAM.md (v1): no `enabled` field; confirms Phase 8
  must add it without breaking backward compatibility (default: true when absent)
- `D:/GSDteams/templates/TEAM.md` — v2 template: no `enabled` field confirmed; Phase 8 adds it
  as optional per-role field
- `D:/GSDteams/.planning/phases/01-extension-scaffold-gsd-integration/REVIEW-REPORT.md` —
  Verified REVIEW-REPORT.md format: per-phase file, per-plan section headers, table format
- `D:/GSDteams/.planning/REQUIREMENTS.md` — ROST-01/02/03 verbatim; LIFE-03 confirms per-phase
  AGENT-REPORT.md location; LIFE-04 confirms on-demand invocation from /gsd:team
- `D:/GSDteams/.planning/research/ARCHITECTURE.md` — team-studio.md step sequence (lines 417-438),
  roster display format (lines 441-454), on-demand trigger description (lines 577-582),
  AGENT-LOG.md reference (line 360)
- `D:/GSDteams/.planning/STATE.md` — All accumulated decisions from Phases 1-7; confirms:
  Phase 05-02 12-char header limit, Phase 06-01 scope fields inside scope: block, Phase 07-01
  dispatcher decisions

### Secondary (MEDIUM confidence)

- `D:/GSDteams/.planning/phases/07-agent-dispatcher/07-01-SUMMARY.md` — Confirmed dispatcher
  decisions; confirms no `enabled` field in dispatcher (Phase 7 did not have the requirement)
- `D:/GSDteams/.planning/phases/07-agent-dispatcher/07-VERIFICATION.md` — Confirmed dispatcher
  has 4 steps; no `enabled` filter step present

---

## Metadata

**Confidence breakdown:**
- Command file structure: HIGH — verified from existing new-reviewer.md source and installed files
- Workflow file structure: HIGH — verified from new-reviewer.md, agent-dispatcher.md
- Install path: HIGH — verified from install.sh Section 5 glob copy
- enabled field design: HIGH (per-role YAML) — derived from schema pattern; no existing example
  (field is new), but design is straightforward
- Dispatcher patch for enabled: HIGH — confirmed Phase 7 has no enabled check; Phase 8 must add it
- AGENT-REPORT.md format: MEDIUM — derived from REVIEW-REPORT.md pattern and REQUIREMENTS.md LIFE-03;
  no existing AGENT-REPORT.md file exists to reference; format is a Phase 8 design decision
- On-demand invocation mechanics: MEDIUM — described in REQUIREMENTS.md LIFE-04 and
  ARCHITECTURE.md but no prior phase has implemented it; Phase 8 is the first implementation

**Research date:** 2026-02-26
**Valid until:** 60 days or until GSD version changes — based on internal project files only.
Phase 8 is the first implementation of on-demand invocation; some design decisions will be made
during planning and are flagged as Open Questions above.
