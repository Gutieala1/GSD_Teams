<purpose>
Guides the user through creating a new agent role and writes it to `.planning/TEAM.md`.
If the agent is autonomous, also creates `agents/gsd-agent-{slug}.md` with a structured prompt template.

Steps: check_team_md → gather_purpose → gather_mode → gather_trigger → gather_output_type
       → gather_advisory_details (advisory only) → gather_scope (autonomous only)
       → decision_gate → write_agent

Called by: `commands/gsd/new-agent.md` via the `/gsd:new-agent` slash command.
</purpose>

<inputs>
No inputs required. The workflow reads `.planning/TEAM.md` directly.
</inputs>

<step name="check_team_md" priority="first">
## Step 1: Check TEAM.md

Announce: "Let's create a new agent role for your team."

Check whether `.planning/TEAM.md` exists:

```bash
[ -f ".planning/TEAM.md" ] && echo "exists" || echo "missing"
```

If the file exists: read it with the Read tool. Note how many roles already exist (count `## Role:` headers). Also read the existing `roles:` list from the YAML frontmatter — store it as `existing_slugs` for the collision check in write_agent.

Announce the current state: "Found N existing role(s) in .planning/TEAM.md." (or 0 if none).

If the file does not exist: do NOT create it yet. Note this — it will be created in the write_agent step.
Announce: "No .planning/TEAM.md found — it will be created when we write the role."
Set `existing_slugs` to an empty list.
</step>

<step name="gather_purpose">
## Step 2: Gather Purpose

Ask the user what problem this agent should solve or what artifact it should produce.

```
AskUserQuestion([
  {
    question: "What problem should this agent catch, or what artifact should it produce?",
    header: "Purpose",
    multiSelect: false,
    options: [
      { label: "Catch a class of issues", description: "Advisory: finds and flags problems in code or plans" },
      { label: "Produce a document", description: "Autonomous: writes docs, changelogs, reports automatically" },
      { label: "Transform or update files", description: "Autonomous: updates existing files after phase completes" },
      { label: "Describe my own purpose", description: "I'll explain what this agent does" }
    ]
  }
])
```

If the user selects "Describe my own purpose": accept their free-text response via the "Other" path.

From the purpose answer, derive a suggested display name and slug:
- "Catch a class of issues" → prompt for domain specifics (see next question if they haven't provided them)
- "Produce a document" → suggest "Doc Writer" / "doc-writer"
- "Transform or update files" → suggest name based on their description
- Free text → derive: lowercase key noun(s), join with hyphens (e.g., "Dependency Checker" → "dependency-checker")

Ask a follow-up to capture the specific purpose sentence if the pre-defined option didn't provide enough detail:

```
AskUserQuestion([
  {
    question: "In one sentence: what does this agent do?",
    header: "Purpose",
    multiSelect: false,
    options: [
      { label: "Type your description above", description: "Example: Flags missing test coverage after each plan" }
    ]
  }
])
```

Store: `purpose_sentence` (one sentence), `display_name` (suggested), `role_slug` (derived).

Announce: "I'll name this agent '{display_name}' (slug: `{role_slug}`)."

Ask the user to confirm or change:

```
AskUserQuestion([
  {
    question: "Confirm the agent name:",
    header: "Agent Name",
    multiSelect: false,
    options: [
      { label: "Use suggested name", description: "{display_name} / {role_slug}" },
      { label: "Change it", description: "I'll provide a different name" }
    ]
  }
])
```

If "Change it": ask for the display name, then derive slug (lowercase, replace spaces with hyphens, strip special chars).
</step>

<step name="gather_mode">
## Step 3: Gather Mode

Ask whether the agent advises or acts autonomously.

```
AskUserQuestion([
  {
    question: "Should this agent advise (produce findings or notes) or act autonomously (produce artifacts)?",
    header: "Agent Mode",
    multiSelect: false,
    options: [
      { label: "Advisory", description: "Produces findings or notes — read-only, never writes files directly" },
      { label: "Autonomous", description: "Produces artifacts — writes files, optionally commits them" }
    ]
  }
])
```

Store: `mode` = "advisory" | "autonomous"
</step>

<step name="gather_trigger">
## Step 4: Gather Trigger

Ask when this agent should fire.

If `mode == "advisory"`:
```
AskUserQuestion([
  {
    question: "When should this agent fire?",
    header: "Trigger",
    multiSelect: false,
    options: [
      { label: "Pre-plan",   description: "Before each plan is created — notes only (output injected into planner)" },
      { label: "Post-plan",  description: "After each plan executes — review findings or notes" },
      { label: "Post-phase", description: "After all plans in a phase complete — phase-level review" },
      { label: "On-demand",  description: "Manual only — run via /gsd:team" }
    ]
  }
])
```

If `mode == "autonomous"`:
```
AskUserQuestion([
  {
    question: "When should this agent fire?",
    header: "Trigger",
    multiSelect: false,
    options: [
      { label: "Post-plan",  description: "After each plan executes — artifact produced per plan" },
      { label: "Post-phase", description: "After all plans in a phase complete — artifact produced per phase" },
      { label: "On-demand",  description: "Manual only — run via /gsd:team" }
    ]
  }
])
```

Note: Pre-plan trigger is only offered for advisory agents. Autonomous agents at pre-plan would fire before any artifacts exist — not useful.

Store: `trigger` = "pre-plan" | "post-plan" | "post-phase" | "on-demand"
</step>

<step name="gather_output_type">
## Step 5: Gather Output Type

Branch on mode:

**If mode == "advisory":**
```
AskUserQuestion([
  {
    question: "What type of output does this advisory agent produce?",
    header: "Output Type",
    multiSelect: false,
    options: [
      { label: "Notes",    description: "Structured markdown injected into the planner context (pre-plan only)" },
      { label: "Findings", description: "JSON findings routed through the review pipeline (post-plan)" }
    ]
  }
])
```

Note: If `trigger == "pre-plan"` and user selects "Findings": warn them that findings agents are skipped at pre-plan (no SUMMARY.md exists). Suggest switching to "Notes" or changing trigger to "post-plan". Re-ask if they want to adjust.

Store: `output_type` = "notes" | "findings"

**If mode == "autonomous":**
No question needed. Set `output_type` = "artifact" automatically.
Announce: "Autonomous agents produce artifacts. output_type set to: artifact."
</step>

<step name="gather_advisory_details">
## Step 6: Advisory Details (advisory mode only)

**Skip this step entirely if mode == "autonomous". Proceed directly to gather_scope.**

Ask what this advisory agent should check (review criteria).

```
AskUserQuestion([
  {
    question: "What should this agent check or capture? (choose a starting set)",
    header: "Criteria",
    multiSelect: false,
    options: [
      { label: "Domain-specific issues", description: "Security, performance, requirements — I'll describe the domain" },
      { label: "Plan vs. implementation", description: "Does implementation match stated requirements?" },
      { label: "Cross-cutting concerns",  description: "Error handling, logging, test coverage" },
      { label: "I'll list my own",        description: "I'll describe the specific criteria" }
    ]
  }
])
```

If "Domain-specific issues": ask a follow-up to capture the domain and derive 3-5 criteria from the description.

If "I'll list my own": accept free-text via the "Other" path.

For pre-defined selections, expand into 3-5 full criterion sentences as markdown list items.

Store: `criteria_list` (3-5 items as "- criterion text")

If `output_type == "findings"`: ask about severity thresholds and routing.

```
AskUserQuestion([
  {
    question: "What makes a finding critical in this domain?",
    header: "Severity",
    multiSelect: false,
    options: [
      { label: "Deploy-stopper bugs",    description: "Data loss or outage if shipped" },
      { label: "Security breach risk",   description: "Exploitable vulnerability or credential exposure" },
      { label: "Requirement violated",   description: "A stated requirement is directly contradicted" },
      { label: "I'll define thresholds", description: "I'll describe critical/major/minor myself" }
    ]
  }
])
```

If "I'll define thresholds": ask for each level via follow-up questions.

Based on selection, store `severity_critical`, `severity_major`, `severity_minor` as example strings.

```
AskUserQuestion([
  {
    question: "Use standard routing for findings?",
    header: "Routing",
    multiSelect: false,
    options: [
      { label: "Standard (recommended)", description: "critical → block, major → rework, minor → log" },
      { label: "Customize routing",      description: "I'll set routing per severity level" }
    ]
  }
])
```

Store: `routing_critical`, `routing_major`, `routing_minor`

If `output_type == "notes"`: skip severity and routing questions. Notes agents do not produce findings.
Store: `severity_critical` = "N/A — notes agent does not produce findings", `severity_major` = "N/A", `severity_minor` = "N/A", `routing_critical` = "N/A", `routing_major` = "N/A", `routing_minor` = "N/A"
</step>

<step name="gather_scope">
## Step 7: Scope (autonomous mode only)

**Skip this step entirely if mode == "advisory". Proceed directly to decision_gate.**

Ask what filesystem paths this agent may read or write.

```
AskUserQuestion([
  {
    question: "What filesystem paths may this agent read or write? (glob patterns)",
    header: "Scope Paths",
    multiSelect: false,
    options: [
      { label: "Docs only",           description: "docs/**, *.md, .planning/**/*.md" },
      { label: "Source + docs",       description: "src/**, docs/**, *.md" },
      { label: "Planning files only", description: ".planning/**/*.md" },
      { label: "I'll specify",        description: "I'll enter the glob patterns" }
    ]
  }
])
```

If "I'll specify": accept free-text glob patterns (comma or newline separated).

Store: `scope_allowed_paths` as a YAML list of quoted glob strings.

Ask what tools this agent needs.

```
AskUserQuestion([
  {
    question: "What tools does this agent need?",
    header: "Tools",
    multiSelect: false,
    options: [
      { label: "Read + Write",         description: "File reading and writing (most common for artifact producers)" },
      { label: "Read + Write + Bash",  description: "File I/O plus shell commands" },
      { label: "Read + Write + Grep",  description: "File I/O plus content search" },
      { label: "All standard tools",   description: "Read, Write, Bash, Grep, Glob" }
    ]
  }
])
```

Store: `scope_allowed_tools` as a YAML list of tool names.

Ask whether this agent should commit its output.

```
AskUserQuestion([
  {
    question: "Should this agent commit its produced artifact?",
    header: "Commit",
    multiSelect: false,
    options: [
      { label: "Yes — commit automatically", description: "Agent runs gsd-tools.cjs commit after writing" },
      { label: "No — just write the file",   description: "User commits manually" }
    ]
  }
])
```

Store: `commit` = true | false

If `commit == true`: ask for the commit message template.

```
AskUserQuestion([
  {
    question: "Enter a commit message template (use {phase} for the phase identifier):",
    header: "Commit Msg",
    multiSelect: false,
    options: [
      { label: "Type the message template above", description: "Example: docs(auto): update docs after phase {phase}" }
    ]
  }
])
```

Store: `commit_message` (string, may contain {phase} placeholder)

Show a scope preview to the user and allow editing:

Display:
```
Scope for {display_name}:
  allowed_paths: {scope_allowed_paths}
  allowed_tools: {scope_allowed_tools}
  commit: {commit}
  {commit_message if commit == true}
```

```
AskUserQuestion([
  {
    question: "Confirm the scope settings:",
    header: "Scope",
    multiSelect: false,
    options: [
      { label: "Looks good",      description: "Proceed to preview" },
      { label: "Change paths",    description: "Re-enter the allowed paths" },
      { label: "Change tools",    description: "Re-select the tools" },
      { label: "Change commit",   description: "Change commit settings" }
    ]
  }
])
```

If any "Change" option selected: re-ask the relevant sub-question and return to this preview.
</step>

<step name="decision_gate">
## Step 8: Decision Gate — Preview and Confirm

Assemble the complete agent definition from all collected values. Display it to the user before writing anything.

**For advisory agents (mode == "advisory"):**

Assemble the role block:

```
## Role: {display_name}

```yaml
name: {role_slug}
focus: {purpose_sentence}
mode: advisory
trigger: {trigger}
output_type: {output_type}
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

**For autonomous agents (mode == "autonomous"):**

Assemble the role block:

```
## Role: {display_name}

```yaml
name: {role_slug}
focus: {purpose_sentence}
mode: autonomous
trigger: {trigger}
output_type: artifact
commit: {commit}
{if commit == true: commit_message: "{commit_message}"}
enabled: true

scope:
  allowed_paths:
{scope_allowed_paths as indented YAML list items: "    - "{path}""}
  allowed_tools:
{scope_allowed_tools as indented YAML list items: "    - {tool}"}
```

**What this role produces:**
{purpose_sentence}

**Severity thresholds:** N/A — autonomous agent does not produce findings

**Routing hints:** N/A — output_type: artifact
```

Also show the agent file content that will be created at `agents/gsd-agent-{role_slug}.md`:

```
---
name: gsd-agent-{role_slug}
description: {purpose_sentence}. Triggered at {trigger}. Produces artifact.
tools: {scope_allowed_tools as comma-separated list}
color: green
---

<role>
You are a GSD autonomous agent: {display_name}.

Spawned by the agent-dispatcher workflow at trigger: {trigger}.

Your job: {purpose_sentence}

**Critical mindset:** Produce a complete, non-stub artifact. Never write placeholder content.
</role>

<process>
[TODO: Add your agent's specific implementation steps here]

Step 1: Read the relevant files using the Read tool.
Step 2: Process and transform content according to your role definition.
Step 3: Write the output artifact to its target path.
{if commit == true: Step 4: Commit via gsd-tools.cjs commit "{commit_message}" --files {output_path}}
</process>

<output>
**File produced:** [declare your output path here]

**Return to dispatcher:**
## AGENT COMPLETE

**Agent:** {display_name}
**Trigger:** {trigger}
**Artifact:** [output path]
</output>

<success_criteria>
- [ ] Artifact written to declared path
- [ ] Artifact is complete (not a stub)
{if commit == true: - [ ] Committed via gsd-tools.cjs}
</success_criteria>
```

Display both the role block and (for autonomous) the agent file content to the user:

"Here is the agent definition that will be written:

**TEAM.md role block:**
[show role block]

{if autonomous: **Agent file** (`agents/gsd-agent-{role_slug}.md`):
[show agent file content]}

This will be appended to `.planning/TEAM.md`.{if autonomous: An agent prompt file will also be created at `agents/gsd-agent-{role_slug}.md`.}"

Then ask for confirmation:

```
AskUserQuestion([
  {
    question: "Ready to create this agent?",
    header: "Confirm",
    multiSelect: false,
    options: [
      { label: "Create agent",  description: "Write role to TEAM.md{if autonomous: and create agents/gsd-agent-{role_slug}.md}" },
      { label: "Edit details",  description: "Go back and change something before writing" },
      { label: "Cancel",        description: "Discard — nothing will be written" }
    ]
  }
])
```

If "Cancel": announce "Agent creation cancelled. No files were written." and exit the workflow.
If "Edit details": return to step 2 (gather_purpose) to restart the conversation. Do NOT write anything.
If "Create agent": proceed to write_agent.
</step>

<step name="write_agent">
## Step 9: Write Agent to TEAM.md (and agent file if autonomous)

**IMPORTANT: This is the ONLY step that writes to disk. Steps 1-8 are read-only.**

**Slug collision check:**

Before writing, verify `role_slug` does not already exist in `existing_slugs` (read in check_team_md step).

If collision detected:
- Announce: "A role with slug '{role_slug}' already exists in TEAM.md."
- Offer slug with numeric suffix: `{role_slug}-2`, `{role_slug}-3`, etc. (increment until no collision)
- Ask user to confirm the new slug or provide their own.

**If .planning/TEAM.md EXISTS:**

1. Read the current content with the Read tool.
2. Parse the YAML frontmatter: extract the `roles:` list.
3. Add `{role_slug}` to the list.
4. Append a `---` separator and the full role block to the end of the file body.
5. Write the full updated content back to `.planning/TEAM.md` with the Write tool.

The appended block follows this exact format:

```
---

## Role: {display_name}

```yaml
name: {role_slug}
focus: {purpose_sentence}
mode: {mode}
trigger: {trigger}
output_type: {output_type}
{if mode == "autonomous": commit: {commit}}
{if mode == "autonomous" and commit == true: commit_message: "{commit_message}"}
enabled: true
{if mode == "autonomous":
scope:
  allowed_paths:
    - "{path_1}"
    - "{path_2}"
  allowed_tools:
    - {tool_1}
    - {tool_2}}
```

**What this role {if advisory: reviews}{if autonomous: produces}:**
{criteria_list if advisory, or purpose_sentence if autonomous}

**Severity thresholds:**
{if advisory: - `critical`: {severity_critical}
- `major`: {severity_major}
- `minor`: {severity_minor}}
{if autonomous: - `critical`: N/A — autonomous agent does not produce findings
- `major`: N/A
- `minor`: N/A}

**Routing hints:**
{if advisory: - Critical findings: `{routing_critical}`
- Major findings: `{routing_major}`
- Minor findings: `{routing_minor}`}
{if autonomous: N/A — output_type: artifact}
```

**If .planning/TEAM.md does NOT EXIST:**

Create it with `version: 2` in the frontmatter (CRITICAL: use version: 2, NOT version: 1 — new TEAM.md files must use v2 schema to avoid normalizeRole shim overriding explicit field values):

```
---
version: 2
roles:
  - {role_slug}
---

# Agent Team

Define your agent roles below. Run `/gsd:new-agent` to create additional roles through a guided conversation.
Run `/gsd:new-reviewer` to create a post-plan advisory reviewer role.

---

[role block as above]
```

**If mode == "autonomous": Create the agent file**

Write `agents/gsd-agent-{role_slug}.md` using the Write tool with the content assembled in the decision_gate step.

Announce: "Agent file created at `agents/gsd-agent-{role_slug}.md`. Edit the `<process>` section to add your agent's specific implementation steps."

**Commit:**

Commit via gsd-tools.cjs. Use the installed path (not the source path):

If advisory:
```bash
node ~/.claude/get-shit-done/bin/gsd-tools.cjs commit \
  "feat(agents): add {role_slug} advisory agent" \
  --files ".planning/TEAM.md"
```

If autonomous:
```bash
node ~/.claude/get-shit-done/bin/gsd-tools.cjs commit \
  "feat(agents): add {role_slug} autonomous agent" \
  --files ".planning/TEAM.md" "agents/gsd-agent-{role_slug}.md"
```

**Announce completion:**

"Agent '{display_name}' created successfully.

- Role block written to `.planning/TEAM.md`
{if autonomous: - Agent prompt created at `agents/gsd-agent-{role_slug}.md` — edit the `<process>` section to add your agent's specific steps}
- Run `/gsd:team` to see it in the roster."
</step>
