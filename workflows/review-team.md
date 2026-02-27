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

Run `/gsd:new-agent` to create your first reviewer role.
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
## Step 3: Spawn All Reviewers in Parallel (Phase 4)

Phase 4 spawns ALL valid roles from TEAM.md in a single orchestrator message — true parallelism.

### Part A — Extract All Role Definition Texts

Read `.planning/TEAM.md` using the Read tool.

For EACH role_name in `roles_list` (populated by validate_team):
- Find the `## Role: {role_name}` header (case-insensitive match on the name from the YAML `name:` field)
- Extract all text from that header to the NEXT `## Role:` header (exclusive), or to EOF if no next role exists
- Store as `role_definitions[role_name]`

This single TEAM.md read populates ALL role definitions before any spawning begins.

If the re-read TEAM.md produces a different roles list than validate_team produced, log a WARNING:
`WARNING: TEAM.md roles changed between validate_team and spawn_reviewers — using re-read list as authoritative`
Use the re-read list going forward.

### Part B — Spawn All Reviewers — Single Message

Issue ALL of the following Task() calls in a SINGLE MESSAGE — do not await between them.
All reviewers run simultaneously. Execution does not advance to collection until ALL complete.

For each role_name in roles_list, issue one Task() block:

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
    ${role_definitions[role_name]}
    </role_definition>

    <execution_context>
    @~/.claude/get-shit-done-review-team/agents/gsd-reviewer.md
    </execution_context>
  "
)
```

In practice this means writing out one Task() block per role in a single message.
For 3 starter roles: 3 Task() blocks issued together.

Note: `${ARTIFACT_PATH}` is the value computed in the sanitize step. Do not recompute it — reuse the same path.

### Part C — Collect and Merge Findings

After ALL reviewer Tasks complete:

For each reviewer return:
1. Parse JSON to extract the `findings` array
2. Log: `Review Team: {role_name}: {N} finding(s)`
3. If findings array is empty: log `Review Team: {role_name}: 0 findings (clean domain)` — not an error
4. If findings are present: log each finding's id, severity, and description for audit:
   `  [{id}] [{severity}] {description}`
5. Append all findings to combined_findings array (each finding already has a `reviewer` field)

Build the combined_findings structure:
```json
{
  "phase": "${PHASE_ID}",
  "plan": "${PLAN_NUM}",
  "reviewer_count": N,
  "all_findings": [ ... merged flat array of all findings from all reviewers ... ],
  "per_reviewer": {
    "{role_name}": { "finding_count": N }
  }
}
```

### Part D — Early Exit for Zero Findings

If combined all_findings is empty (ALL reviewers returned 0 findings):
- Log: `Review Team: all reviewers — 0 findings, routing to log_and_continue`
- Write empty plan section to REVIEW-REPORT.md at path: `.planning/phases/${PHASE_ID}/REVIEW-REPORT.md`
  - Check if file exists (Read tool):
    - If it does NOT exist: write the file with header `# Review Report — Phase ${PHASE_ID}` followed by the plan section
    - If it EXISTS: Read the existing file, append new plan section to end, Write back
  - Empty plan section format:
    ```
    ## Plan ${PLAN_NUM} — {ISO timestamp}

    **Reviewers:** {comma-separated role names}
    **Findings:** 0
    **Action:** log_and_continue

    No findings — all reviewers returned clean.

    ---
    ```
- Proceed directly to return_status with `routing: log_and_continue, findings: 0`
- SKIP the synthesize step — no synthesis needed for empty findings

If combined all_findings is non-empty:
- Proceed to the synthesize step with combined_findings JSON
</step>

<step name="synthesize">
## Step 4: Synthesize and Route Findings (Phase 4)

### Part A — Spawn Synthesizer

Spawn the synthesizer agent with the combined findings JSON injected directly in the prompt (not written to a file first):

```
Task(
  subagent_type="gsd-review-synthesizer",
  prompt="
    <objective>
    Deduplicate cross-reviewer findings. Assign routing for each unique finding.
    Return structured synthesis JSON.
    </objective>

    <inputs>
    Phase: ${PHASE_ID}
    Plan: ${PLAN_NUM}
    </inputs>

    <combined_findings>
    ${combined_findings_json}
    </combined_findings>

    <execution_context>
    @~/.claude/get-shit-done-review-team/agents/gsd-review-synthesizer.md
    </execution_context>
  "
)
```

`combined_findings_json` is the combined findings JSON built at the end of the spawn_reviewers step.
The combined findings JSON is passed directly in the prompt — NOT written to a file first.

---

### Part B — Validate No-New-Findings (before acting on routing)

After synthesizer returns:

1. Parse synthesizer JSON to extract `unique_findings` and `synthesis_errors`
2. Check `synthesis_errors` array — if non-empty, log each error as WARNING:
   `Review Team: WARNING — synthesis error: {error}`
3. Build input_ids set from `combined_findings.all_findings` (all reviewer finding IDs):
   `input_ids = {f.id for f in combined_findings.all_findings}`
4. For each unique_finding in synthesizer output:
   a. If `source_finding_ids` is empty or null:
      log `Review Team: WARNING — finding {id} has no source_finding_ids (pipeline violation)`
   b. For each source_id in `source_finding_ids`:
      if source_id NOT in input_ids:
      log `Review Team: WARNING — finding {id} has invalid source_finding_id {source_id}`
5. If ANY validation failure detected:
   log `Review Team: WARNING — synthesizer validation failed, using reviewer findings directly (fallback)`
   Fallback: treat combined_findings.all_findings as-is (un-deduplicated), determine routing based on
   highest severity in the raw findings using the same severity-to-routing mapping (critical →
   block_and_escalate, high → send_for_rework, medium → send_to_debugger or send_for_rework, low/info
   → log_and_continue).

---

### Part C — Apply Deterministic Routing Override (severity minimum)

This check runs BEFORE reading `synthesizer.overall_routing`:

```
Step 1: HAS_CRITICAL = any unique_finding where severity == "critical"

Step 2:
  if HAS_CRITICAL:
    FINAL_ROUTING = "block_and_escalate"
    Log: "Review Team: critical finding detected — routing overridden to block_and_escalate (hardcoded minimum)"
  else:
    FINAL_ROUTING = synthesizer.overall_routing
    Log: "Review Team: routing → {FINAL_ROUTING}"

Step 3: If FINAL_ROUTING != synthesizer.overall_routing (and not the critical override case):
    Log: "Review Team: routing override — synthesizer suggested {synthesizer.overall_routing}, enforced {FINAL_ROUTING}"
```

This enforcement applies even if the synthesizer assigned `block_and_escalate` to a critical finding
in its own `final_routing` — the workflow does the check independently as a safety layer.

Note: block_and_escalate overrides auto_advance mode — user input is always required regardless of
workflow execution settings.

---

### Part D — Write REVIEW-REPORT.md (ALL routing paths, before acting on route)

Write before acting on FINAL_ROUTING — the finding is logged even if execution halts.

Path: `.planning/phases/${PHASE_ID}/REVIEW-REPORT.md`

Append logic (Read-then-Write):
1. Attempt to Read `.planning/phases/${PHASE_ID}/REVIEW-REPORT.md`
2. If file does NOT exist: build content = `# Review Report — Phase ${PHASE_ID}\n\n---\n\n` + plan section
3. If file EXISTS: build content = existing_content + `\n\n` + plan section (append, do NOT overwrite)
4. Write the full content back

Plan section format:
```markdown
## Plan ${PLAN_NUM} — {ISO timestamp, e.g. 2026-02-26T03:15:00Z}

**Reviewers:** {comma-separated from synthesizer.reviewer_coverage}
**Findings:** {len(unique_findings)} | **Deduped:** {synthesizer.dedup_count}
**Action:** {FINAL_ROUTING}

| ID | Reviewer | Severity | Description | Evidence | Routing |
|----|----------|----------|-------------|----------|---------|
{one row per unique_finding: | {id} | {reviewer} | {severity} | {description (truncated to 80 chars)} | {evidence (truncated to 60 chars)} | {final_routing} |}

---
```

If 0 unique_findings (fallback from validation failure used raw findings with no findings, or
synthesizer returned empty):
```markdown
## Plan ${PLAN_NUM} — {ISO timestamp}

**Reviewers:** {comma-separated}
**Findings:** 0
**Action:** log_and_continue

No findings — all reviewers returned clean.

---
```

---

### Part E — Act on FINAL_ROUTING

All four routing destinations:

**block_and_escalate:**
Present to user using AskUserQuestion (halt — execution does not proceed until user responds):

```
## REVIEW TEAM: EXECUTION BLOCKED

**Phase:** ${PHASE_ID}
**Plan:** ${PLAN_NUM}

Critical finding(s) require your decision before execution continues.

### Critical Findings

| ID | Reviewer | Severity | Finding | Evidence |
|----|----------|----------|---------|----------|
{rows for unique_findings where severity == "critical"}

---

Findings logged to REVIEW-REPORT.md.

**Options:**
- "Continue" — acknowledge finding, continue with next plan
- "Fix first" — stop execution, address finding manually
- "Rework" — re-execute this plan with the finding as context

Execution will NOT continue until you respond.
```

Wait for user response. Do NOT call return_status until user decides.

**send_for_rework:**
Present findings and halt:

```
## REVIEW TEAM: REWORK REQUIRED

**Phase:** ${PHASE_ID}
**Plan:** ${PLAN_NUM}
**Findings requiring rework:** {count of high-severity findings}

{Table of high-severity findings}

Findings logged to REVIEW-REPORT.md.
Execution halted. Suggested action: address the finding(s) above, then re-execute this plan.
```

Halt. Do NOT call return_status.

**send_to_debugger:**
Present findings and halt:

```
## REVIEW TEAM: DEBUGGER RECOMMENDED

**Phase:** ${PHASE_ID}
**Plan:** ${PLAN_NUM}

{Table of medium findings with send_to_debugger routing}

Findings logged to REVIEW-REPORT.md.
Suggested action: run /gsd:debug with the finding context above.
```

Halt. Do NOT call return_status.

**log_and_continue:**
```
Log: "Review Team: {N} finding(s) logged to REVIEW-REPORT.md — continuing execution"
Proceed to return_status immediately. No halt. No user presentation.
```
</step>

<step name="return_status">
## Step 5: Return Pipeline Status

This step is reached only after the user has made a decision in block_and_escalate, or after
routing is log_and_continue. For send_for_rework and send_to_debugger, execution halts in the
synthesize step before reaching return_status.

Return the following status block:

```markdown
## REVIEW PIPELINE: PIPELINE COMPLETE

**Phase:** ${PHASE_ID}
**Plan:** ${PLAN_NUM}
**Reviewers fired:** {N} ({comma-separated role names})
**Artifact:** ${ARTIFACT_PATH}
**Findings (pre-synthesis):** {total finding count across all reviewers}
**Final routing:** {FINAL_ROUTING}
**REVIEW-REPORT.md:** .planning/phases/${PHASE_ID}/REVIEW-REPORT.md

{If FINAL_ROUTING is log_and_continue:}
{N} finding(s) logged. Execution continues.

{If FINAL_ROUTING is block_and_escalate:}
Execution halted — user decision required. See findings above.

{If FINAL_ROUTING is send_for_rework:}
Execution halted — rework required. Address findings and re-execute this plan.

{If FINAL_ROUTING is send_to_debugger:}
Execution halted — debugger recommended. Run /gsd:debug with finding context.
```
</step>
