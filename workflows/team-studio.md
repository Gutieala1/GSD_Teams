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
  Inform the user: "No TEAM.md found at .planning/TEAM.md. Run `/gsd:new-reviewer` to create
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

Find the 5 most recently modified plan/summary files in .planning/phases/ (excluding AGENT-REPORT.md):

```bash
find .planning/phases -name "*.md" -not -name "AGENT-REPORT.md" | xargs ls -t 2>/dev/null | head -5
```

Use AskUserQuestion:

```
AskUserQuestion([{
  question: "What artifact should this agent run against?",
  header: "Select File",
  multiSelect: false,
  options: [
    // one entry per file found (up to 5):
    { label: "{filename}", description: "{file path}" },
    // plus:
    { label: "Enter path manually", description: "Specify a custom file path" },
    { label: "Cancel", description: "Return to roster without changes" }
  ]
}])
```

If Cancel: return to present_actions.

If "Enter path manually": ask the user for the path as a follow-up question.

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
Route the user to the correct agent creation command based on what they want to create.

Inform the user:

"To add an agent:
- For a **full agent role** (any mode, trigger, or output type): run `/gsd:new-agent`
- For a **review-team role only** (advisory, post-plan reviewer, shortcut flow): run `/gsd:new-reviewer`

`/gsd:new-agent` supports all modes (advisory and autonomous), all triggers (pre-plan, post-plan,
post-phase, on-demand), and all output types (findings, notes, artifact). Use it for any new agent.

`/gsd:new-reviewer` is a shortcut for post-plan advisory reviewers only.

Run `/gsd:new-agent` to create your agent."

Return to present_actions.
</step>
