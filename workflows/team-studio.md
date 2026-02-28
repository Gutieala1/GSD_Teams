<purpose>
Team Studio — the interactive roster management workflow for /gsd:team. Displays all agents
from .planning/TEAM.md in a formatted table, then presents an action menu that loops until
the user selects "Done". Supports: view/edit agent prompt, enable/disable toggle, remove with
confirmation gate, on-demand invocation against a specified artifact (logged to AGENT-REPORT.md),
history view, and add-agent fallback to /gsd:new-agent.

Source path:    D:/GSDteams/workflows/team-studio.md
Installed path: ~/.claude/get-shit-done-review-team/workflows/team-studio.md
Calling point:  /gsd:team command (commands/gsd/team.md)
</purpose>

<inputs>
No explicit inputs required. The workflow reads .planning/TEAM.md directly.

Internal state maintained across steps:
- `roster`: list of parsed + normalized role objects from TEAM.md
- `selected_agent`: the role object chosen in an action sub-step
- `phase_id`: derived from artifact path or most-recent phase directory
</inputs>

<step name="show_roster" priority="first">
Load and display the agent roster from .planning/TEAM.md.

**1. Check TEAM.md exists**

```bash
[ -f .planning/TEAM.md ] || echo "MISSING"
```

If the output is "MISSING":
  Inform the user: "No TEAM.md found at .planning/TEAM.md. Run `/gsd:new-agent` to create
  your first agent role."
  Exit the workflow.

**2. Read and parse TEAM.md**

Use the Read tool to read `.planning/TEAM.md`.

Extract from the YAML frontmatter:
- `version`: the version field value. Default to 1 (integer) if absent.
  CRITICAL: version is a numeric integer. Comparison is `version < 2`, not string comparison.
- `roles`: the list of role slugs (e.g. ["security-auditor", "rules-lawyer"])

For each slug in the roles list:
  - Find the `## Role: {slug}` section in the TEAM.md body
  - Extract the YAML config block: content between the first triple-backtick yaml fence and
    its closing triple-backtick fence within that section
  - Parse these fields: `name`, `focus`, `mode`, `trigger`, `output_type`, `commit`, `enabled`
  - Store the slug alongside the parsed fields

**3. Apply normalizeRole defaults**

Apply this algorithm to each role after parsing (same as dispatcher normalizeRole shim):

```
normalizeRole(role, version):
  if version < 2:
    role.mode        = role.mode        ?? "advisory"
    role.trigger     = role.trigger     ?? "post-plan"
    role.output_type = role.output_type ?? "findings"
  return role
```

For `enabled`: if the field is absent or null → treat as `true` (default enabled).

Store the full list as `roster` for use by subsequent steps.

**4. Display the roster table**

```
## Agent Team

**{N} agent(s) configured**

| # | Agent | Mode | Trigger | Output | Status |
|---|-------|------|---------|--------|--------|
| 1 | Security Auditor | advisory | post-plan | findings | active |
| 2 | Doc Writer | autonomous | post-phase | artifact | **DISABLED** |
```

Rules:
- `#` column: sequential number starting at 1
- `Agent` column: the role `name` field
- `Mode` column: advisory or autonomous
- `Trigger` column: post-plan, pre-plan, post-phase, or on-demand
- `Output` column: the `output_type` field
- `Status` column: enabled agents → `active`; disabled agents → `**DISABLED**` (bold)

After the table, show a trigger-count summary line:
"post-plan: N | post-phase: N | pre-plan: N | on-demand: N"

Count each trigger value across all roles (enabled + disabled) for the summary line.

Proceed to present_actions.
</step>

<step name="present_actions">
Present the action menu and route to the appropriate sub-step.

AskUserQuestion has a max of 4 options per question. Use TWO questions to cover all actions:

```
AskUserQuestion([
  {
    question: "What would you like to do?",
    header: "Team Roster",
    multiSelect: false,
    options: [
      { label: "View / Edit prompt", description: "Inspect or change an agent's definition" },
      { label: "Enable / Disable",   description: "Toggle an agent on or off" },
      { label: "Remove agent",       description: "Delete a role from TEAM.md (with confirmation)" },
      { label: "Done",               description: "Exit the team roster" }
    ]
  },
  {
    question: "Or:",
    header: "More",
    multiSelect: false,
    options: [
      { label: "Run agent now",  description: "Invoke an agent on-demand against a file" },
      { label: "View history",   description: "Show AGENT-REPORT.md entries for an agent" },
      { label: "Add agent",      description: "Create a new agent role via /gsd:new-agent" },
      { label: "Nothing here",   description: "Use the first question above" }
    ]
  }
])
```

Route based on user selection (first non-"Nothing here" answer wins):
- "View / Edit prompt" → view_edit_prompt step
- "Enable / Disable"   → toggle_enabled step
- "Remove agent"       → remove_agent step
- "Done"               → exit the workflow
- "Run agent now"      → invoke_on_demand step
- "View history"       → view_history step
- "Add agent"          → add_agent step
- "Nothing here"       → re-present the action menu (user chose neither question)

After each sub-step completes, return here and present the action menu again.
Only "Done" exits the loop.
</step>

<step name="view_edit_prompt">
View an agent's full prompt definition and optionally edit it in place.

**1. Present agent selection**

Use AskUserQuestion with one option per agent in the roster, plus Cancel:

```
AskUserQuestion([{
  question: "Which agent do you want to view or edit?",
  header: "View / Edit",
  multiSelect: false,
  options: [
    // one entry per agent:
    { label: "{agent.name}", description: "{agent.mode} · {agent.trigger} · {status}" },
    // plus:
    { label: "Cancel", description: "Return to roster without changes" }
  ]
}])
```

If Cancel: return to present_actions.

**2. Display the full prompt**

Read `.planning/TEAM.md` with the Read tool.

Extract the full `## Role: {slug}` section:
  - Start: the line `## Role: {slug}`
  - End: the next `---` separator line, OR end of file if no subsequent separator
  - Include the heading line; do NOT include the trailing `---`

Display the extracted block verbatim as a fenced markdown code block so the user can
read every field: name, focus, mode, trigger, output_type, enabled, what it reviews,
severity thresholds, and routing hints.

**3. Ask view-only or edit**

```
AskUserQuestion([{
  question: "What do you want to do with this agent?",
  header: "View / Edit",
  multiSelect: false,
  options: [
    { label: "Edit prompt",  description: "Change one or more sections of this agent's definition" },
    { label: "Done viewing", description: "Return to the roster" }
  ]
}])
```

If "Done viewing": return to present_actions.

**4. Edit prompt — section selection**

```
AskUserQuestion([{
  question: "Which section do you want to edit?",
  header: "Edit Section",
  multiSelect: false,
  options: [
    { label: "Focus / purpose",     description: "The one-line focus field in the YAML block" },
    { label: "What it reviews",     description: "The bullet list of review criteria" },
    { label: "Severity thresholds", description: "critical / major / minor definitions" },
    { label: "Routing hints",       description: "block_and_escalate / send_for_rework / log_and_continue rules" }
  ]
}])
```

**5. Show current content and ask for new content**

Display the current content of the selected section clearly.

Then ask the user (inline text, NOT AskUserQuestion — just a plain text prompt):
"Enter the new content for this section. Type it out and press Enter when done."

Accept the user's free-text response as `new_content`.

**6. Write updated TEAM.md (Read-then-Write)**

1. Read current `.planning/TEAM.md` with the Read tool (re-read for latest content)
2. Locate the `## Role: {slug}` section
3. Find the targeted section within it:
   - "Focus / purpose" → update the `focus:` value in the YAML config block
   - "What it reviews" → replace the entire `**What this role reviews:**` bullet block
   - "Severity thresholds" → replace the entire `**Severity thresholds:**` bullet block
   - "Routing hints" → replace the entire `**Routing hints:**` bullet block
4. Apply the replacement using the Edit tool (targeted string replace, not full file rewrite)
5. Announce: "Updated '{section}' for agent '{agent.name}'."

**7. Offer to edit another section**

```
AskUserQuestion([{
  question: "Edit another section of this agent?",
  header: "Edit Section",
  multiSelect: false,
  options: [
    { label: "Yes, edit another section", description: "Choose a different section to update" },
    { label: "No, done editing",          description: "Return to the roster" }
  ]
}])
```

If "Yes": return to step 4 (section selection) for the same agent.
If "No": return to present_actions.
</step>

<step name="toggle_enabled">
Toggle the enabled/disabled state for a selected agent.

**1. Present agent selection**

Use AskUserQuestion:

```
AskUserQuestion([{
  question: "Which agent do you want to toggle?",
  header: "Toggle",
  multiSelect: false,
  options: [
    // one entry per agent:
    { label: "{agent.name}", description: "currently active" },      // if enabled
    { label: "{agent.name}", description: "currently disabled" },    // if disabled
    // plus:
    { label: "Cancel", description: "Return to roster without changes" }
  ]
}])
```

If Cancel: return to present_actions without modifying TEAM.md.

**2. Update the enabled field**

Read the current `enabled` value for the selected role from the parsed `roster`.

Determine the new value:
- If currently enabled (true or absent/null): new value = `false`
- If currently disabled (false): new value = `true`

**3. Write updated TEAM.md (Read-then-Write)**

1. Read current `.planning/TEAM.md` with the Read tool (re-read for latest content)
2. Find the `## Role: {slug}` section
3. Locate its YAML config block (between the triple-backtick yaml fences)
4. Update or add the `enabled:` line:
   - If `enabled:` line already exists: replace its value with the new boolean
   - If `enabled:` line does not exist: add `enabled: {new_value}` as the last field
     inside the YAML block, on the line before the closing triple-backtick fence
5. Write the full updated TEAM.md using the Write tool

**4. Announce the change**

If new value is `true`:
  Announce: "Agent '{name}' enabled. The dispatcher will resume this agent on the next trigger."

If new value is `false`:
  Announce: "Agent '{name}' disabled. The dispatcher will skip this agent on the next trigger."

**5. Update in-memory roster**

Update the `roster` list to reflect the new enabled state for this agent.

Return to present_actions.
</step>

<step name="remove_agent">
Remove an agent role from TEAM.md with a confirmation gate.

**1. Present agent selection**

Use AskUserQuestion:

```
AskUserQuestion([{
  question: "Which agent do you want to remove?",
  header: "Remove",
  multiSelect: false,
  options: [
    // one entry per agent:
    { label: "{agent.name}", description: "{agent.mode} · {agent.trigger}" },
    // plus:
    { label: "Cancel", description: "Return to roster without changes" }
  ]
}])
```

If Cancel: return to present_actions.

**2. Show the role block**

Read `.planning/TEAM.md` with the Read tool.
Extract the full role block for the selected slug:
  - Start: the `---` separator line immediately before `## Role: {slug}`
  - End: the next `---` separator line, OR end of file if no subsequent separator exists
  - Include both boundary lines in the extracted block

Display the extracted role block to the user so they can see what will be deleted.

**3. Confirmation gate**

Use AskUserQuestion:

```
AskUserQuestion([{
  question: "Remove '{role_name}' from TEAM.md? This cannot be undone.",
  header: "Remove",
  multiSelect: false,
  options: [
    { label: "Remove", description: "Delete role block and remove from roles list" },
    { label: "Cancel", description: "Return to roster without changes" }
  ]
}])
```

If Cancel: return to present_actions without modifying TEAM.md.

**4. Delete the role (if Remove confirmed)**

1. Read current `.planning/TEAM.md` with the Read tool (re-read for latest content)
2. Remove the slug from the frontmatter `roles:` list
3. Remove the role block: find the `---` separator before `## Role: {slug}` and delete
   from that separator through the next `---` separator (or EOF), inclusive of both
   separator lines
4. Write the full updated TEAM.md using the Write tool
5. Announce: "Agent '{role_name}' removed from TEAM.md."

**5. Update in-memory roster**

Remove the deleted role from the `roster` list.

Re-display the updated roster table (repeat the show_roster display logic inline — do not
call back to show_roster step, just render the table from the updated `roster` list).

Return to present_actions.
</step>

<step name="invoke_on_demand">
Invoke a selected enabled agent against a specified artifact. Display result inline and log
to AGENT-REPORT.md.

**1. Present agent selection (enabled agents only)**

Disabled agents cannot be invoked on-demand and must not appear in this list.

Filter `roster` to only `active_roles` where `enabled != false`.

Use AskUserQuestion:

```
AskUserQuestion([{
  question: "Which agent do you want to run?",
  header: "Run Agent",
  multiSelect: false,
  options: [
    // one entry per enabled agent:
    { label: "{agent.name}", description: "{agent.mode} · {agent.trigger} · {agent.output_type}" },
    // plus:
    { label: "Cancel", description: "Return to roster without changes" }
  ]
}])
```

If Cancel: return to present_actions.

**2. Present artifact selection**

Find the 3 most recently modified plan/summary files in .planning/phases/ (excluding AGENT-REPORT.md):

```bash
find .planning/phases -name "*.md" -not -name "AGENT-REPORT.md" | xargs ls -t 2>/dev/null | head -3
```

Use TWO questions (4-option limit per question):

```
AskUserQuestion([
  {
    question: "What artifact should this agent run against?",
    header: "Select File",
    multiSelect: false,
    options: [
      // one entry per file found (up to 3):
      { label: "{filename}", description: "{file path}" },
      // always last in question 1:
      { label: "Review recent git changes", description: "Run against a git diff — for ad-hoc changes made outside a plan" }
    ]
  },
  {
    question: "Or:",
    header: "Select File",
    multiSelect: false,
    options: [
      { label: "Enter path manually", description: "Specify a custom file path" },
      { label: "Sweep all files",     description: "Run agent across all workflow, script, or phase files" },
      { label: "Cancel",              description: "Return to roster without changes" },
      { label: "Nothing here",        description: "Use the first question above" }
    ]
  }
])
```

Route (first non-"Nothing here" answer wins):
- A file name → use that file as the artifact; proceed to step 3
- "Review recent git changes" → proceed to step 2b
- "Sweep all files"           → proceed to step 2c
- "Enter path manually" → ask the user for the path as a follow-up question; proceed to step 3
- "Cancel" → return to present_actions

**2b. Git diff selection**

Only reached if "Review recent git changes" was selected.

First, show context so the user knows what's available:

```bash
git log --oneline -3 2>/dev/null
echo "---"
git status --short 2>/dev/null | head -10
```

Then ask which scope to diff:

```
AskUserQuestion([{
  question: "Which changes should the agent review?",
  header: "Git Diff",
  multiSelect: false,
  options: [
    { label: "Last commit",      description: "Changes in the most recent commit (git diff HEAD~1 HEAD)" },
    { label: "Unstaged changes", description: "Current working tree changes not yet staged (git diff)" },
    { label: "Staged changes",   description: "Changes staged for next commit (git diff --staged)" },
    { label: "All uncommitted",  description: "Everything since last commit — staged + unstaged (git diff HEAD)" }
  ]
}])
```

Run the selected diff:

```bash
# map selection to git command:
# "Last commit"      → git diff HEAD~1 HEAD
# "Unstaged changes" → git diff
# "Staged changes"   → git diff --staged
# "All uncommitted"  → git diff HEAD

git diff {scope} --stat 2>/dev/null
echo "---DIFF---"
git diff {scope} 2>/dev/null
```

Store the full output (stat + diff) as `diff_output`.

**If diff_output is empty or contains no `---DIFF---` content:**
  Announce: "No changes found for '{scope}'. Nothing to review."
  Return to present_actions.

**If diff_output exceeds 300 lines:**
  Display only the `--stat` section (file names + line counts).

  Then ask:

  ```
  AskUserQuestion([{
    question: "The diff is large. How should the agent review it?",
    header: "Large Diff",
    multiSelect: false,
    options: [
      { label: "Use full diff",       description: "Pass all changes — agent will prioritize top findings" },
      { label: "Workflow files only", description: "Filter to .md files (workflows, commands, templates)" },
      { label: "Script files only",   description: "Filter to .py, .sh, .js, .cjs files" },
      { label: "Cancel",              description: "Return to roster without running the agent" }
    ]
  }])
  ```

  - "Use full diff"       → use `diff_output` as-is
  - "Workflow files only" → re-run: `git diff {scope} -- "*.md" 2>/dev/null`; use that as `diff_output`
  - "Script files only"   → re-run: `git diff {scope} -- "*.py" "*.sh" "*.js" "*.cjs" 2>/dev/null`; use that as `diff_output`
  - "Cancel"              → return to present_actions

Set:
- `artifact_content` = `diff_output`
- `artifact_path` = `"git diff {scope}"`

Proceed to step 3.

**2c. Sweep all files**

Only reached if "Sweep all files" was selected.

Ask which file scope to sweep:

```
AskUserQuestion([{
  question: "Which files should the agent sweep?",
  header: "Sweep Scope",
  multiSelect: false,
  options: [
    { label: "Workflow files (.md)", description: "All .md files in workflows/ and commands/" },
    { label: "Script files",        description: "All .py, .sh, .cjs files in scripts/" },
    { label: "Phase files",         description: "All PLAN.md and SUMMARY.md across .planning/phases/" },
    { label: "Cancel",              description: "Return to artifact selection" }
  ]
}])
```

If Cancel: return to present_actions.

Collect files based on selection:

```bash
# Workflow files:
find workflows/ commands/ -name "*.md" 2>/dev/null | sort

# Script files:
find scripts/ -name "*.py" -o -name "*.sh" -o -name "*.cjs" 2>/dev/null | sort

# Phase files:
find .planning/phases/ \( -name "*PLAN.md" -o -name "*SUMMARY.md" \) 2>/dev/null | sort
```

Show the user a count and the full file list.

**If 0 files found:**
  Announce: "No {scope} files found."
  Return to present_actions.

**If >10 files found:**
  Warn: "Found N files — this will be a large artifact."

  ```
  AskUserQuestion([{
    question: "N files found — how would you like to proceed?",
    header: "Sweep Size",
    multiSelect: false,
    options: [
      { label: "Run anyway",                description: "Concatenate all N files — agent prioritizes top findings" },
      { label: "Most recently modified 10", description: "Limit sweep to the 10 newest files" },
      { label: "Cancel",                    description: "Return without running the agent" }
    ]
  }])
  ```

  - "Run anyway"                → proceed with all N files as collected
  - "Most recently modified 10" → re-run the find command, pipe through `| xargs ls -t | head -10`,
                                   use those 10 files as the file list
  - "Cancel"                    → return to present_actions

**Build the combined artifact:**

Read each file in the file list with the Read tool.

Concatenate all content with file headers:

```
--- {relative/path/to/file.md} ---

{file content}

```

Repeat for every file in the list, separated by a blank line.

Set:
- `artifact_content` = the full concatenated string
- `artifact_path` = `"sweep: {scope label} ({N} files)"`

Proceed to step 3.

**3. Determine phase_id for AGENT-REPORT.md**

- If the artifact path contains `.planning/phases/{slug}/`: extract `{slug}` as the phase_id
- Otherwise: use the most-recently-modified phase directory:
  ```bash
  ls -td .planning/phases/*/ | head -1 | xargs basename
  ```

**4. Load agent role definition**

Read `.planning/TEAM.md` with the Read tool.
Extract the full `## Role: {slug}` section as `role_block` for use in the Task() prompt.

Read the artifact file content with the Read tool.

**5. Spawn the agent via Task()**

For advisory agents:
  Spawn a Task() with this structured prompt:

  ```
  <objective>
  You are {role.name}, an advisory agent running on-demand via /gsd:team.

  Your job: Review the artifact below and return structured findings or notes
  based on your declared role definition.

  Your declared domain: {role.focus}
  </objective>

  <role_definition>
  {role_block — the full ## Role: {slug} section from TEAM.md}
  </role_definition>

  <artifact>
  Path: {artifact_path}

  {artifact_content}
  </artifact>

  <methodology>
  Step 1 — Read the artifact above carefully in full before forming any observations.

  Step 2 — For each item in your "What this role reviews" list (and any "Patterns to flag"
           if present), check whether the artifact contains relevant evidence.

  Step 3 — For each observation, find the specific text in the artifact that grounds it.
           If you cannot find a direct quote or reference, do not raise the observation.

  Step 4 — Assign a confidence level:
           HIGH   = direct evidence in the artifact
           MEDIUM = strong inference from multiple artifact signals
           LOW    = plausible concern with limited supporting evidence

  Step 5 — Apply your scope constraint: suppress any observation outside your declared
           domain ({role.focus}). Do not mention out-of-scope concerns.

  Step 6 — Format your output exactly as specified below.
  </methodology>

  <output_format>
  Return ONLY the following markdown structure. No preamble, no summary after.

  ## Advisory Notes: {role.name}

  ### Observation 1
  **Finding:** [one sentence — what you observed]
  **Evidence:** [direct quote or specific reference from the artifact above]
  **Recommendation:** [one actionable suggestion]
  **Confidence:** HIGH | MEDIUM | LOW

  ### Observation 2
  [repeat — maximum 5 observations]

  ---
  **Domain:** {role.focus}
  **Trigger:** on-demand (/gsd:team)
  **Artifact:** {artifact_path}
  </output_format>

  <critical_rules>
  1. Every observation MUST have an Evidence field with a direct quote or specific reference.
     Observations without evidence must be omitted.
  2. Maximum 5 observations. Prioritize by impact.
  3. Do not address anything outside your declared domain ({role.focus}).
  4. If you find no relevant observations, return exactly one observation:
     Finding: "No concerns identified for domain: {role.focus}."
     Evidence: "Artifact reviewed — no evidence found relevant to this domain."
     Confidence: HIGH
  </critical_rules>
  ```

For autonomous agents:
  Spawn a Task() with this prompt:
  "You are acting as the following agent role:\n\n{role_block}\n\nArtifact path: {artifact_path}\n\nTrigger context: on-demand\n\nProcess the artifact according to your role definition."

Display the Task() result inline in the conversation.

**6. Log to AGENT-REPORT.md**

Determine the report path: `.planning/phases/{phase_id}/AGENT-REPORT.md`

Check if the file exists:

```bash
[ -f ".planning/phases/{phase_id}/AGENT-REPORT.md" ] && echo "EXISTS" || echo "NEW"
```

If NEW: create the file with the Write tool using this content:
```
# Agent Report — Phase {phase_id}

---

```

If EXISTS: read the current content with the Read tool.

Append this section to the file content (Read-then-Write for existing, Write-new for new):

```
## On-Demand: {agent-slug} — {ISO timestamp}

**Agent:** {agent display name}
**Mode:** {advisory | autonomous}
**Artifact:** {artifact path}
**Invoked by:** on-demand (/gsd:team)

### Result

{agent output}

---
```

Write the updated file using the Write tool.

**7. Announce**

Announce: "Result logged to `.planning/phases/{phase_id}/AGENT-REPORT.md`"

Return to present_actions.
</step>

<step name="view_history">
Display historical AGENT-REPORT.md entries for a selected agent or all agents.

**1. Present agent selection**

Use AskUserQuestion:

```
AskUserQuestion([{
  question: "Which agent's history do you want to view?",
  header: "History",
  multiSelect: false,
  options: [
    { label: "All agents", description: "Show history for every agent" },
    // one entry per agent in roster:
    { label: "{agent.name}", description: "{agent.mode} · {agent.trigger}" },
    // plus:
    { label: "Cancel", description: "Return to roster without changes" }
  ]
}])
```

If Cancel: return to present_actions.

**2. Find AGENT-REPORT.md files**

```bash
find .planning/phases -name "AGENT-REPORT.md" 2>/dev/null
```

If no files found:
  Announce: "No agent history found. Run an agent on-demand to create history."
  Return to present_actions.

**3. Display matching entries**

For each found AGENT-REPORT.md file: read its content with the Read tool.

If "All agents" selected:
  Display all entries from all AGENT-REPORT.md files inline.

If a specific agent selected (slug = the selected role's slug):
  Filter to only sections matching `## On-Demand: {slug}` in each file.
  Display only those matching sections.

If no matching entries found for the specific agent:
  Announce: "No history found for '{agent.name}'. Run this agent on-demand to create history."

Return to present_actions.
</step>

<step name="add_agent">
Read project context, generate smart agent suggestions tailored to this project, then route
to creation. Falls back to blank-slate /gsd:new-agent if no project context is found.

**1. Read project context**

Check for and read these files with the Read tool:

```bash
[ -f ".planning/PROJECT.md" ] && echo "EXISTS" || echo "MISSING"
[ -f ".planning/ROADMAP.md" ] && echo "EXISTS" || echo "MISSING"
```

If both are MISSING:
  Announce: "No project context found — falling back to blank-slate agent creation."
  Inform the user: "Run `/gsd:new-agent` to create a new agent through the guided conversation."
  Return to present_actions.

If at least one exists: read whichever files are present. Store the combined content as
`project_context`.

**2. Analyze and generate suggestions**

With `project_context` and the in-memory `roster` in hand, derive up to 3 agent suggestions
tailored to THIS specific project. For each suggestion, generate ALL fields — no placeholders:

- `display_name` and `role_slug` (kebab-case)
- `purpose` — one sentence describing what this agent does
- `mode` — advisory (most cases) or autonomous
- `trigger` — post-phase, post-plan, pre-plan, or on-demand
- `output_type` — findings or notes (advisory), artifact (autonomous)
- `criteria_list` — 3–5 specific criteria as bullet points
- `patterns_list` — 2–3 specific matchable patterns with concrete examples
  Format: `- {pattern name}: {concrete example}`
- `severity_critical`, `severity_major`, `severity_minor` — for findings agents
- `calibration_critical`, `calibration_major`, `calibration_minor` — one concrete example each
- `routing_critical` = `block_and_escalate`, `routing_major` = `send_for_rework`,
  `routing_minor` = `log_and_continue` (use standard routing unless domain demands otherwise)
- `why` — one sentence explaining why this agent is relevant to THIS project specifically

**Derivation signals — use ALL of these:**

- **Domain/stack**: What technology, language, or framework does this project use?
  → Domain-specific reviewers (e.g. TypeScript type safety checker, SQL query auditor)
- **Upcoming phases**: What work is coming up in the roadmap phases?
  → Phase-aligned agents (e.g. auth phase → security-focused reviewer)
- **Project goals**: What does the project care about (reliability, speed, compliance, UX)?
  → Goal-aligned agents (e.g. reliability → error handling checker)
- **Existing roster**: What agents already exist?
  → DO NOT suggest agents with the same or overlapping focus as existing `roster` entries.
  → Look for coverage GAPS instead.

Generate 1–3 suggestions. Every suggestion must be concrete and grounded in the actual
project context — no generic "Security Auditor" unless the project context supports it.

**3. Present suggestions**

```
AskUserQuestion([{
  question: "Based on your project, here are agents that could help — pick one to create:",
  header: "Suggestions",
  multiSelect: false,
  options: [
    // one entry per suggestion (up to 3):
    { label: "{display_name}", description: "{why}" },
    // always last:
    { label: "Create from scratch", description: "Open /gsd:new-agent with no pre-fill" }
  ]
}])
```

If "Create from scratch":
  Inform the user: "Run `/gsd:new-agent` to create a new agent through the guided conversation."
  Return to present_actions.

**4. Show suggestion preview and confirm**

For the selected suggestion, display the full role block:

```
## Role: {display_name}

```yaml
name: {role_slug}
focus: {purpose}
mode: {mode}
trigger: {trigger}
output_type: {output_type}
enabled: true
```

**What this role reviews:**
{criteria_list}

**Patterns to flag:**
{patterns_list}

**Severity thresholds:**
- `critical`: {severity_critical}
- `major`: {severity_major}
- `minor`: {severity_minor}

**Calibration examples:**
- `critical`: {calibration_critical}
- `major`: {calibration_major}
- `minor`: {calibration_minor}

**Routing hints:**
- Critical findings: `{routing_critical}`
- Major findings: `{routing_major}`
- Minor findings: `{routing_minor}`
```

Then ask for confirmation:

```
AskUserQuestion([{
  question: "Create '{display_name}' as shown?",
  header: "Confirm",
  multiSelect: false,
  options: [
    { label: "Create agent",        description: "Write this role to TEAM.md now" },
    { label: "Customize first",     description: "Run /gsd:new-agent to adjust details" },
    { label: "Back to suggestions", description: "See the other suggestions" },
    { label: "Cancel",              description: "Return to roster without adding an agent" }
  ]
}])
```

- "Create agent"        → proceed to step 5
- "Customize first"     → announce "Run `/gsd:new-agent`. Starting point: {purpose},
                          mode: {mode}, trigger: {trigger}." → return to present_actions
- "Back to suggestions" → return to step 3 (re-present suggestion menu)
- "Cancel"              → return to present_actions

**5. Write the suggested agent to TEAM.md**

Slug collision check: if `role_slug` already exists in `roster`, append `-2` suffix and
announce: "Slug '{role_slug}' already exists — using '{role_slug}-2'."

1. Read current `.planning/TEAM.md` with the Read tool (re-read for latest content)
2. Add `{role_slug}` to the `roles:` frontmatter list
3. Append this block to the end of the file body:

```
---

## Role: {display_name}

```yaml
name: {role_slug}
focus: {purpose}
mode: {mode}
trigger: {trigger}
output_type: {output_type}
enabled: true
```

**What this role reviews:**
{criteria_list}

**Patterns to flag:**
{patterns_list}

**Severity thresholds:**
- `critical`: {severity_critical}
- `major`: {severity_major}
- `minor`: {severity_minor}

**Calibration examples:**
- `critical`: {calibration_critical}
- `major`: {calibration_major}
- `minor`: {calibration_minor}

**Routing hints:**
- Critical findings: `{routing_critical}`
- Major findings: `{routing_major}`
- Minor findings: `{routing_minor}`
```

4. Write the full updated TEAM.md with the Write tool.

5. Commit:

```bash
node ~/.claude/get-shit-done/bin/gsd-tools.cjs commit \
  "feat(agents): add {role_slug} advisory agent (project-aware suggestion)" \
  --files ".planning/TEAM.md"
```

6. Announce: "Agent '{display_name}' added to `.planning/TEAM.md`."

Update the in-memory `roster` to include the new agent. Re-display the updated roster table
inline (render from updated `roster` — do not call back to show_roster).

Return to present_actions.
</step>
