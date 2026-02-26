<purpose>
The review-team workflow orchestrates the review pipeline after each plan completes. It is loaded
by the `review_team_gate` step in `execute-plan.md` via `@~/.claude/get-shit-done-review-team/workflows/review-team.md`.

The workflow receives three inputs from the review_team_gate step:
- SUMMARY_PATH: path to the current plan's SUMMARY.md
- PHASE_ID: phase identifier (e.g., "02-sanitizer-artifact-schema")
- PLAN_NUM: plan number (e.g., "02")

**Phase 2 implemented:** TEAM.md validation and sanitizer spawning (Steps 1 and 2).
**Phase 3 implements:** Single reviewer spawning and JSON findings collection (Step 3).
**Phase 4 adds:** Parallel reviewer spawning, synthesis, and routing (Steps 3 expanded + Step 4).
</purpose>

<inputs>
The review_team_gate step passes these values:

- `SUMMARY_PATH` -- path to the current plan's SUMMARY.md (e.g., `.planning/phases/01-extension-scaffold-gsd-integration/01-02-SUMMARY.md`)
- `PHASE_ID` -- phase identifier (e.g., `01-extension-scaffold-gsd-integration`)
- `PLAN_NUM` -- plan number (e.g., `02`)

These are passed by the review_team_gate step which says: "Pass: current SUMMARY.md path, phase identifier, plan identifier."
</inputs>

<step name="validate_team" priority="first">
## Step 1: Validate TEAM.md

Read `.planning/TEAM.md` and validate it has at least one valid reviewer role.

Even though the review_team_gate step already confirmed TEAM.md exists, double-check defensively:

```bash
[ -f ".planning/TEAM.md" ] || { echo "ERROR: .planning/TEAM.md not found"; exit 1; }
```

Read `.planning/TEAM.md` using the Read tool.

### Validation Logic

A valid role requires ALL THREE of:
1. A `## Role:` section header
2. A YAML code block (triple-backtick yaml) containing a `name:` field
3. At least one item under the `**What this role reviews:**` heading

Split the content on `## Role:` headers. For each section after the first split (the preamble before the first role is skipped):

- Look for a fenced YAML block (lines between triple-backtick yaml and triple-backtick) containing a `name:` field. Extract the value as `role_name`.
- Check the section contains `**What this role reviews:**` with at least one list item (line starting with `- `) below it.
- If BOTH conditions are met: add `role_name` to the valid roles list.
- If the YAML block is missing or has no `name:` field: log a warning:
  `WARNING: Role section missing YAML name: field -- skipped`
- If `**What this role reviews:**` is missing or has no list items: log a warning:
  `WARNING: Role '{role_name}' has no review criteria -- skipped`

### Zero Valid Roles -- HALT

If zero valid roles found after checking all sections, output this error and HALT:

```
## REVIEW PIPELINE HALTED

**Error:** TEAM.md exists but contains zero valid reviewer roles.

Each role requires:
1. A `## Role:` section header
2. A YAML code block with a `name:` field
3. At least one review criteria item under `**What this role reviews:**`

Run `/gsd:new-reviewer` to create your first reviewer role.
```

HALT the pipeline. Do NOT proceed to sanitization. This satisfies TEAM-03.

### Valid Roles Found -- Proceed

If one or more valid roles found:
- Store the role count and role names for later use (Phase 3 will use them for reviewer spawning)
- Log: `Review Team: {N} reviewer role(s) found in TEAM.md: {comma-separated role names}`
- Proceed to the sanitize step
</step>

<step name="sanitize">
## Step 2: Sanitize SUMMARY.md into ARTIFACT.md

### Construct Artifact Path

Build the ARTIFACT.md output path following the GSD per-plan artifact convention:

```
PHASE_PADDED = zero-padded phase number extracted from PHASE_ID
              (e.g., "02" from "02-sanitizer-artifact-schema")

ARTIFACT_PATH = ".planning/phases/${PHASE_ID}/${PHASE_PADDED}-${PLAN_NUM}-ARTIFACT.md"
```

Examples:
- Phase "01-extension-scaffold-gsd-integration", Plan "02" produces:
  `.planning/phases/01-extension-scaffold-gsd-integration/01-02-ARTIFACT.md`
- Phase "02-sanitizer-artifact-schema", Plan "01" produces:
  `.planning/phases/02-sanitizer-artifact-schema/02-01-ARTIFACT.md`

### Spawn Sanitizer Agent

Spawn the sanitizer agent via Task() to produce ARTIFACT.md:

```
Task(
  subagent_type="gsd-review-sanitizer",
  prompt="
    <objective>
    Sanitize the execution summary into a clean artifact description.
    Strip all executor reasoning. Preserve all observable facts.
    Write the artifact to disk.
    </objective>

    <inputs>
    Summary path: ${SUMMARY_PATH}
    Artifact output path: ${ARTIFACT_PATH}
    Phase: ${PHASE_ID}
    Plan: ${PLAN_NUM}
    </inputs>

    <execution_context>
    @~/.claude/get-shit-done-review-team/agents/gsd-review-sanitizer.md
    </execution_context>
  "
)
```

### Verify Artifact Exists

After the sanitizer returns, verify ARTIFACT.md was written to disk:

```bash
[ -f "${ARTIFACT_PATH}" ] && echo "ARTIFACT EXISTS" || echo "ARTIFACT MISSING"
```

**If ARTIFACT.md is missing:**
- Output error: `Review Team: ERROR -- Sanitizer completed but ARTIFACT.md not found at ${ARTIFACT_PATH}`
- HALT the pipeline. Do not proceed.

**If ARTIFACT.md exists:**
- Log: `Review Team: ARTIFACT.md written to ${ARTIFACT_PATH}`
- Parse the sanitizer's return for strip count and section count (from the SANITIZATION COMPLETE block)
- Log strip metrics for audit purposes
</step>

<step name="spawn_reviewers">
## Step 3: Spawn Reviewer (Phase 3 — Single Reviewer)

Phase 3 implements this step for exactly ONE reviewer — the first valid role from TEAM.md.
Phase 4 will expand to parallel spawning of all roles.

### Select First Valid Role

Use the valid roles list from the validate_team step. Take the first role:
```
first_role_name = roles_list[0]
```

### Extract Role Definition Text

Read `.planning/TEAM.md` using the Read tool. Extract the full text of the section for `first_role_name`:

1. Find the line matching `## Role: {first_role_name}` (case-insensitive match on the name from the YAML `name:` field)
2. Extract ALL text from that `## Role:` header line to the NEXT `## Role:` header line (exclusive), or to end-of-file if no next role exists
3. This entire extracted text is the `role_definition_text` to inject

Example: For role name `security-auditor`, find `## Role: Security Auditor` (or equivalent), extract everything until `## Role: Rules Lawyer` begins.

The `role_definition_text` must include the full role section: YAML code block, focus description, review checklist, severity thresholds, and routing hints — everything written for that role.

### Spawn Reviewer

```
Task(
  subagent_type="gsd-reviewer",
  prompt="
    <objective>
    Review the sanitized artifact against your assigned role criteria.
    Return structured findings as JSON.
    </objective>

    <inputs>
    artifact_path: ${ARTIFACT_PATH}
    phase: ${PHASE_ID}
    plan: ${PLAN_NUM}
    </inputs>

    <role_definition>
    ${role_definition_text}
    </role_definition>

    <execution_context>
    @~/.claude/get-shit-done-review-team/agents/gsd-reviewer.md
    </execution_context>
  "
)
```

Note: `${ARTIFACT_PATH}` is the value computed in the sanitize step. Do not recompute it — reuse the same path.

### Collect and Log JSON Return

After the reviewer returns:

1. Parse the reviewer's return as JSON to extract the `findings` array
2. Log: `Review Team: Reviewer {first_role_name}: {N} finding(s)`
3. If the findings array is empty: log `Review Team: Reviewer {first_role_name}: 0 findings (no issues in domain)` and continue — this is valid, not an error
4. If findings are present: log each finding's id, severity, and description for audit:
   `  [{id}] [{severity}] {description}`
5. Store the full findings JSON for the return_status block

Phase 3 stops here — Phase 4 adds synthesis and deterministic routing.
</step>

<step name="synthesize">
## Step 4: Synthesize and Route Findings

[Phase 4 -- not yet implemented]

This step will:
1. Receive all reviewer findings from spawn_reviewers step
2. Spawn synthesizer agent to deduplicate and route findings
3. Act on routing decision: block_and_escalate | send_for_rework | send_to_debugger | log_and_continue
4. Write findings to REVIEW-REPORT.md

See ROADMAP.md Phase 4 for design.
</step>

<step name="return_status">
## Step 5: Return Pipeline Status

After the spawn_reviewers step completes (Phase 3 endpoint), return:

```markdown
## REVIEW PIPELINE: REVIEWER COMPLETE

**Phase:** ${PHASE_ID}
**Plan:** ${PLAN_NUM}
**Roles found:** {N} ({comma-separated role names})
**Artifact:** ${ARTIFACT_PATH}
**Reviewer fired:** {first_role_name}
**Findings:** {finding count} finding(s)

{If findings exist, list each:}
| ID | Severity | Description |
|----|----------|-------------|
| {id} | {severity} | {description} |

{If 0 findings:}
No findings in {first_role_name} domain for this plan.

[Phase 4: Parallel multi-reviewer spawning, synthesis, and routing not yet implemented]
[Pipeline stops here in Phase 3 -- review-team.md will be extended in Phase 4]
```
</step>
