<purpose>
Agent Dispatcher — the single routing layer between GSD core workflow trigger points and
downstream execution paths. Reads .planning/TEAM.md, applies the normalizeRole algorithm
to all roles (version-independent normalization), filters by the current trigger context,
then routes to the appropriate execution path.

For advisory roles: routes output_type:notes to direct return (<agent_notes> block);
routes output_type:findings to review-team.md (post-plan only). Preserving identical
REVIEW-REPORT.md output and all four routing paths (block_and_escalate, send_for_rework,
send_to_debugger, log_and_continue) for the findings path.

For no-match trigger: exits immediately with zero Task() spawns (DISP-02).

For bypass flag: exits before touching any pipeline when skip_review: true is detected in
the current PLAN.md frontmatter (DISP-03).

For autonomous roles: logs a named stub message and no-ops safely — no Task() spawns until
Phase 9 implements the autonomous execution path.

Source path:    D:/GSDteams/workflows/agent-dispatcher.md
Installed path: ~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
Calling point:  pre_plan_agent_gate step in plan-phase.md (pre-plan trigger) and
                review_team_gate step in execute-plan.md (post-plan trigger)
</purpose>

<inputs>
- `trigger_type`: string — the trigger context for this dispatch call
    Values: "post-plan" | "pre-plan" | "post-phase" | "on-demand"
    Phase 7 wires only "post-plan"; other values accepted but no calling point exists yet.

- `summary_path`: string — path to the current plan's SUMMARY.md
    Example: ".planning/phases/07-agent-dispatcher/07-01-SUMMARY.md"

- `phase_id`: string — phase identifier
    Example: "07-agent-dispatcher"

- `plan_num`: string — plan number
    Example: "01"

- `plan_path`: string (optional) — explicit path to the current PLAN.md for bypass flag
    extraction. If not provided, derived from summary_path by replacing -SUMMARY.md with
    -PLAN.md. Example: ".planning/phases/07-agent-dispatcher/07-01-PLAN.md"

NOTE: CONFIG_CONTENT is already in scope from the calling execute-plan.md workflow — no
re-read of config.json is needed. The dispatcher reads AGENT_STUDIO_ENABLED from it directly.
</inputs>

<step name="check_bypass_and_config" priority="first">
Check the bypass flag and agent_studio config before any TEAM.md parsing.

**1. Determine PLAN.md path**

Use `plan_path` input if provided. Otherwise derive it from `summary_path`:

```
PLAN_PATH = summary_path.replace("-SUMMARY.md", "-PLAN.md")
```

For example: ".planning/phases/07-agent-dispatcher/07-01-SUMMARY.md"
becomes:      ".planning/phases/07-agent-dispatcher/07-01-PLAN.md"

**2. Check bypass flag**

```bash
SKIP_REVIEW=$(grep -m1 "^skip_review:" "$PLAN_PATH" 2>/dev/null | awk '{print $2}' || echo "false")
```

If `SKIP_REVIEW` is `"true"`:
  Log: `Agent Dispatcher: skipped (agent creation plan — bypass active)`
  Return immediately. Do NOT proceed to subsequent steps. Do NOT read TEAM.md.
  Do NOT call review-team.md. Do NOT spawn any Task(). (DISP-03)

**3. Check agent_studio config**

Read from CONFIG_CONTENT already in scope (do NOT re-read config.json):

```bash
AGENT_STUDIO_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.agent_studio // false')
```

If `AGENT_STUDIO_ENABLED` is not `"true"`:
  Log: `Agent Dispatcher: agent_studio disabled — no-op`
  Return immediately. Do NOT proceed to subsequent steps.

  Note: When agent_studio is disabled, the v1 review path (review_team: true calling
  review-team.md directly) is handled in the calling review_team_gate step — the dispatcher
  is not in that path. No action needed here.

If both checks pass (bypass is false, agent_studio is enabled): proceed to step 2.
</step>

<step name="read_and_parse_team_md">
Read .planning/TEAM.md and normalize all roles to the 8-field canonical form.

**1. Read TEAM.md**

Use the Read tool to read `.planning/TEAM.md`.

Extract from the YAML frontmatter:
- `version`: the version field value. Default to 1 (integer) if the field is absent.
  CRITICAL: version is a numeric integer, not a string. Version comparison is `version < 2`,
  not `version == "2"` or `version == "1"`.
- `roles`: the list of role slugs (e.g. ["security-auditor", "rules-lawyer", "performance-analyst"])

**2. Parse each role section**

For each slug in the roles list:
  - Find the `## Role: {slug}` section in the TEAM.md body
  - Extract the YAML config block: the content between the first triple-backtick yaml fence
    and its closing triple-backtick fence within that section
  - Parse these fields from the config block:
    - `name`           (string — display name)
    - `focus`          (string — domain description)
    - `mode`           (string — "advisory" or "autonomous")
    - `trigger`        (string — "post-plan", "pre-plan", "post-phase", "on-demand")
    - `tools`          (list — tool names the agent may use)
    - `output_type`    (string — "findings", "document", etc.)
    - `commit`         (boolean — whether agent commits output)
    - `commit_message` (string or null — commit message template)
    - `scope`          (object — contains allowed_paths and allowed_tools)

  Store the slug alongside the parsed fields for logging purposes.

**3. Apply normalizeRole to every role**

Apply this algorithm to each role immediately after parsing it. This is the Phase 6
normalizeRole shim — it applies when version < 2 (numeric comparison):

```
normalizeRole(role, version):
  if version < 2:
    role.mode             = role.mode             ?? "advisory"
    role.trigger          = role.trigger          ?? "post-plan"
    role.tools            = role.tools            ?? []
    role.output_type      = role.output_type      ?? "findings"
    role.commit           = role.commit           ?? false
    role.commit_message   = role.commit_message   ?? null
    role.scope            = role.scope            ?? {}
    role.scope.allowed_paths  = role.scope.allowed_paths  ?? []
    role.scope.allowed_tools  = role.scope.allowed_tools  ?? []
  return role
```

The `??` operator means "use existing value if present and non-null, else use the default".
Fields that ARE present in the YAML block (even for v1 roles) keep their parsed values.
Fields that are ABSENT or null receive the defaults listed above.

For v2 TEAM.md (version >= 2): normalizeRole is a no-op — all fields are already defined.

Result: `normalized_roles` — a list where every role has all 8 fields populated regardless
of which schema version the TEAM.md uses.

**4. Apply enabled default and filter active roles**

After applying normalizeRole to all roles, inject the `enabled` default and produce the
`active_roles` list:

```
For each role in normalized_roles:
  role.enabled = role.enabled ?? true
  # ?? means: use existing value if present and non-null, else use the default
  # This ensures v1 roles (no enabled field) and new v2 roles (enabled field absent) are
  # treated as enabled. Only an explicit enabled: false disables a role.

active_roles = [role for role in normalized_roles if role.enabled == true]
```

Pass `active_roles` (not `normalized_roles`) to the filter_by_trigger step.

If `active_roles` is empty (all roles disabled):
  Log: `Agent Dispatcher: all roles disabled — no-op`
  Return immediately. Do NOT proceed to filter_by_trigger.
</step>

<step name="filter_by_trigger">
Filter active_roles to only those relevant to the current trigger context, then group by mode.

**1. Filter by trigger_type**

```
matched_roles = [role for role in active_roles if role.trigger == trigger_type]
```

Where `trigger_type` is the input passed by the calling review_team_gate step
(e.g. "post-plan").

**2. Handle no-match (DISP-02)**

If `matched_roles` is empty:
  Log: `Agent Dispatcher: no agents configured for trigger '{trigger_type}' — continuing`
  Return immediately. Do NOT call review-team.md. Do NOT spawn any Task().
  This is DISP-02: zero spawns, zero latency. Not an error — a normal no-op exit.

For example: if all TEAM.md roles have trigger "post-plan" and the current trigger_type is
"pre-plan", the dispatcher exits here with a single log line.

**3. Group by mode**

If matched_roles is non-empty, group into two lists:

```
advisory_roles   = [role for role in matched_roles if role.mode == "advisory"]
autonomous_roles = [role for role in matched_roles if role.mode == "autonomous"]
```

Both lists are passed to the route_by_mode step.
</step>

<step name="route_by_mode">
Route matched roles to their execution paths by output_type. Notes agents return structured
markdown directly. Findings agents route to the review pipeline (post-plan only).
Autonomous roles are logged as stubs.

**Split advisory roles by output_type**

```
advisory_notes_roles    = [r for r in advisory_roles if r.output_type == "notes"]
advisory_findings_roles = [r for r in advisory_roles if r.output_type != "notes"]
```

**Handle advisory findings roles (output_type: findings or default)**

If `advisory_findings_roles` is non-empty:

  If `trigger_type` == "post-plan":
    Call the review pipeline (unchanged behavior):

    ```
    @~/.claude/get-shit-done-review-team/workflows/review-team.md
    ```

    Pass these inputs:
    - SUMMARY_PATH = summary_path input
    - PHASE_ID     = phase_id input
    - PLAN_NUM     = plan_num input

    IMPORTANT: Do NOT pass a filtered role list. review-team.md reads .planning/TEAM.md
    itself and performs its own role validation. The dispatcher does not pre-filter.

  If `trigger_type` != "post-plan" (e.g. "pre-plan"):
    Log: `Agent Dispatcher: {N} advisory findings agent(s) ignored for trigger '{trigger_type}' — output_type: findings requires post-plan trigger. Use output_type: notes for pre-plan agents.`
    Do NOT call review-team.md. Do NOT spawn any Task(). Continue to notes handling below.

**Handle advisory notes roles (output_type: notes)**

If `advisory_notes_roles` is non-empty:

  Initialize: `collected_notes = []`

  For each role in advisory_notes_roles (spawn ALL in a single message — true parallelism,
  same pattern as spawn_reviewers in review-team.md):

    Spawn a Task() with this prompt:
    ```
    You are {role.name}.

    {role definition block from TEAM.md — the full ## Role: {slug} section}

    Your task: Review the current phase context and return structured advisory notes.
    These notes will be passed to the GSD planner as input before planning begins.
    The planner may incorporate or explicitly disregard your notes — always provide notes.

    Phase context:
    - Phase ID: {phase_id}
    - Phase goal and requirements: read from .planning/ROADMAP.md and .planning/phases/{phase_id}/
    - Available context files: .planning/STATE.md, .planning/ROADMAP.md

    Return structured markdown with:
    ## Advisory Notes: {brief topic}

    **Key observation:** {finding relevant to the plan}

    **Recommendation:** {specific, actionable suggestion for the planner}

    **Confidence:** HIGH | MEDIUM | LOW

    ---

    Focus on your declared domain: {role.focus}
    Do not address areas outside your domain.
    ```

  Collect all Task() return values. For each: append the role name and the returned markdown
  to `collected_notes`.

  Build the `<agent_notes>` block:
  ```
  AGENT_NOTES_BLOCK = "<agent_notes>\n"
  AGENT_NOTES_BLOCK += "Advisory agents ran before this plan was created. These notes are INPUT — "
  AGENT_NOTES_BLOCK += "incorporate them where relevant, or explicitly disregard with a brief note. "
  AGENT_NOTES_BLOCK += "Always produce a plan.\n\n"
  for (role_name, notes_markdown) in collected_notes:
    AGENT_NOTES_BLOCK += f"## {role_name}\n\n{notes_markdown}\n\n"
  AGENT_NOTES_BLOCK += "</agent_notes>"
  ```

  Return `AGENT_NOTES_BLOCK` as part of the dispatcher output text. The calling gate step
  (pre_plan_agent_gate in plan-phase.md) extracts this block from the dispatcher's return
  value by looking for the `<agent_notes>` ... `</agent_notes>` span.

  Log: `Agent Dispatcher: {N} advisory notes agent(s) fired. <agent_notes> block returned.`

If `advisory_notes_roles` is empty: do not include any `<agent_notes>` block in output.
Log only if notes agents were expected but none matched (e.g. zero notes roles for pre-plan).

**Handle autonomous roles (stub — Phase 9)**

If `autonomous_roles` is non-empty:

  For each role in autonomous_roles:
    Log: `Agent Dispatcher: autonomous agent '{role.name}' — autonomous execution not yet implemented (Phase 9). Skipping.`

  Do NOT spawn any Task(). Do NOT crash. Do NOT call any pipeline.

**Return**

After handling all role groups, the dispatcher returns normally to the calling gate step.
For pre-plan calls with notes agents: the return text includes the `<agent_notes>` block.
For post-plan calls: flow returns to offer_next in execute-plan.md (unchanged).
</step>
