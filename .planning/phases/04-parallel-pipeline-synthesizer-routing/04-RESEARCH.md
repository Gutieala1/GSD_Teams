# Phase 4: Parallel Pipeline + Synthesizer + Routing — Research

**Researched:** 2026-02-25
**Domain:** GSD workflow orchestration — parallel Task() spawning, synthesizer agent design, deterministic routing, REVIEW-REPORT.md persistence
**Confidence:** HIGH

---

## Summary

Phase 4 completes the review pipeline by replacing the single-reviewer Phase 3 spawn with true parallel spawning of all TEAM.md roles, building the `gsd-review-synthesizer.md` agent that deduplicates and routes findings, and implementing deterministic routing logic in `review-team.md` with REVIEW-REPORT.md persistence.

The dominant constraint is that routing for `critical` findings must be enforced in workflow code — not by the synthesizer LLM — to prevent the synthesizer from soft-routing a critical finding to `log_and_continue`. This is the single most important architectural decision already locked from project initialization: `critical → block_and_escalate` is hardcoded minimum in the `synthesize` step, not a synthesizer judgment call. The synthesizer's job is deduplication and routing suggestion; the workflow's job is enforcement.

The second dominant design challenge is finding collection from parallel reviewers. GSD's execute-phase.md parallel Task() pattern fires multiple Task() calls in a single message and waits for all to complete before proceeding. Each reviewer in Phase 4 returns its findings as a JSON code block (the established Phase 3 pattern). The synthesize step receives these as a combined input and passes them to the synthesizer agent. There is no named output file per reviewer — the return from each Task() carries the JSON inline, matching the established Phase 3 single-reviewer collection pattern.

The REVIEW-REPORT.md per-phase vs. global question is resolved by the requirement text: SYNTH-05 states `{phase-dir}/REVIEW-REPORT.md` explicitly. Per-phase is the correct answer. Each plan reviewed appends a new section under a per-plan header, preventing collision between plans in the same phase.

**Primary recommendation:** Three plans in sequence: (04-01) replace spawn_reviewers with parallel Task() for all roles and collect combined findings JSON; (04-02) build gsd-review-synthesizer.md agent with dedup, no-new-findings guard, and routing enum output; (04-03) implement the synthesize step in review-team.md with hardcoded severity-minimum routing enforcement and REVIEW-REPORT.md writer.

---

## Standard Stack

### Core

| Component | Type | Purpose | Why Standard |
|-----------|------|---------|--------------|
| `agents/gsd-review-synthesizer.md` | GSD agent (new) | Deduplicates cross-reviewer findings, suggests routing, enforces no-new-findings constraint | Required by SYNTH-01 through SYNTH-05 |
| `workflows/review-team.md` | GSD workflow (update) | spawn_reviewers expanded to parallel; synthesize step implemented; return_status advanced | Phase 4 replaces Phase 3 single-reviewer pattern |
| `schemas/finding-schema.md` | Schema reference (existing) | Contract for reviewer output and synthesizer input — 7-field JSON | Phase 3 complete, Phase 4 consumes without modification |
| `agents/gsd-reviewer.md` | GSD agent (existing, unchanged) | Parameterized reviewer — no modification needed | Phase 3 complete |

### No External Dependencies

Phase 4 requires zero external libraries. All artifacts are pure GSD markdown agents/workflows. Tools needed: Read and Write for the synthesizer agent.

---

## Architecture Patterns

### Recommended File Layout (Phase 4 additions)

```
get-shit-done-review-team/
  agents/
    gsd-review-sanitizer.md       # Phase 2 COMPLETE — unchanged
    gsd-reviewer.md               # Phase 3 COMPLETE — unchanged
    gsd-review-synthesizer.md     # Plan 04-02 -- THIS PHASE (new)
  workflows/
    review-team.md                # Updated in Plans 04-01 + 04-03 -- spawn_reviewers parallel + synthesize implemented
```

### Pattern 1: Parallel Task() Spawning (execute-phase.md pattern)

**What:** Multiple Task() calls issued in a single message — all reviewers run simultaneously. The orchestrator does not proceed to synthesis until ALL reviewer Tasks complete. This is identical to the wave-based parallelism in execute-phase.md.

**When to use:** The spawn_reviewers step in review-team.md, Plan 04-01.

**Source:** execute-phase.md `execute_waves` step — "Within a wave: parallel if PARALLELIZATION=true" — multiple Task() calls with the same subagent_type in one message.

**How it works in GSD:** In GSD's Claude Code environment, issuing multiple Task() calls in a single orchestrator response fires them in parallel. The orchestrator's context does not advance until all spawned Tasks return. This is the "single orchestrator turn" guarantee in PIPE-01.

**Critical isolation rule:** Each reviewer Task() receives only:
1. The ARTIFACT_PATH (path to ARTIFACT.md)
2. Its own role_definition_text extracted from TEAM.md

No reviewer sees another reviewer's output. No reviewer sees the raw SUMMARY.md. This is the isolation guarantee from Phase 3 — unchanged.

**Pattern for parallel spawn in spawn_reviewers step:**

```
# Pseudocode — for ALL N roles in TEAM.md valid roles list:

# Read ALL role definition texts before spawning (single TEAM.md read)
role_definitions = {}
for role_name in roles_list:
    role_definitions[role_name] = extract_role_section(TEAM_MD, role_name)

# Spawn ALL reviewers in a single message (true parallelism)
# Issue all Task() calls together — do not await between them

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
    ${role_definitions['security-auditor']}
    </role_definition>
    <execution_context>
    @~/.claude/get-shit-done-review-team/agents/gsd-reviewer.md
    </execution_context>
  "
)

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
    ${role_definitions['rules-lawyer']}
    </role_definition>
    <execution_context>
    @~/.claude/get-shit-done-review-team/agents/gsd-reviewer.md
    </execution_context>
  "
)

# ... one Task() per role — all issued in the same orchestrator message

# After all complete: collect all JSON returns
```

**Key implementation decision for Plan 04-01:** The TEAM.md role count is not known at workflow-write time — it varies by user. The spawn_reviewers step must dynamically construct one Task() call per valid role from the roles_list populated by validate_team. The workflow instructions must make this explicit: "For each role in roles_list, construct and issue a Task() call. All Task() calls are issued in a single message — do not await between them."

### Pattern 2: Combined Findings Collection

**What:** After all reviewer Tasks complete, the workflow collects each reviewer's JSON return and merges all findings arrays into a single combined input for the synthesizer.

**When to use:** spawn_reviewers step, Plan 04-01.

**Combined findings format:**

```json
{
  "phase": "${PHASE_ID}",
  "plan": "${PLAN_NUM}",
  "reviewer_count": 3,
  "all_findings": [
    { "id": "SEC-001", "reviewer": "security-auditor", "domain": "security", "severity": "high", "evidence": "...", "description": "...", "suggested_routing": "send_for_rework" },
    { "id": "LAW-001", "reviewer": "rules-lawyer", "domain": "correctness", "severity": "medium", "evidence": "...", "description": "...", "suggested_routing": "send_for_rework" },
    { "id": "PERF-001", "reviewer": "performance-analyst", "domain": "performance", "severity": "low", "evidence": "...", "description": "...", "suggested_routing": "log_and_continue" }
  ],
  "per_reviewer": {
    "security-auditor": { "finding_count": 1 },
    "rules-lawyer": { "finding_count": 1 },
    "performance-analyst": { "finding_count": 1 }
  }
}
```

**Why flatten to `all_findings`:** The synthesizer's dedup job is semantic — it looks for findings that describe the same underlying issue across different reviewers. A flat array is easier to reason about than a nested-by-reviewer structure. The `reviewer` field on each finding preserves traceability.

**Collection step logic:**
1. For each reviewer Task() return: parse as JSON, extract `findings` array
2. Log per-reviewer finding count: `Review Team: {role}: {N} finding(s)`
3. Append all findings to combined array (tagged by reviewer — already in `reviewer` field)
4. Store combined findings JSON for synthesizer input
5. If ALL reviewers return 0 findings: log `Review Team: all reviewers — 0 findings, no synthesis needed` and route directly to `log_and_continue` (SYNTH-03 minimum enforcement: 0 findings means no critical findings, so log_and_continue is correct)

### Pattern 3: gsd-review-synthesizer.md Agent Design

**What:** A GSD agent (6-part structure, same conventions as gsd-reviewer.md) that receives combined findings JSON, groups semantic duplicates, assigns each unique finding a final routing, and returns a structured synthesis result. It does NOT generate new findings.

**When to use:** Spawned once per plan review, after all reviewers complete.

**Key constraints:**
- SYNTH-02: No new findings — synthesizer output must trace 100% to reviewer input
- SYNTH-03: Routing minimum — critical severity forces block_and_escalate regardless of synthesizer routing suggestion (enforced in WORKFLOW CODE, not here)
- SYNTH-04: Every output finding must include `source_finding_ids` (the reviewer finding IDs that contributed to it)

**Frontmatter:**
```yaml
---
name: gsd-review-synthesizer
description: Deduplicates cross-reviewer findings, assigns routing. Spawned by review-team workflow after all parallel reviewers complete.
tools: Read, Write
color: green
---
```

**Critical mindset:** "You classify; you do not re-review. Trust the reviewer findings as given. Your job is routing decisions and deduplication, not second-guessing the analysis."

**Synthesizer input format:** The workflow passes combined findings JSON directly in the Task() prompt via `<combined_findings>` tags (small enough for direct injection — no file needed for typical 3-reviewer scenarios).

**Synthesizer output format (SYNTHESIS COMPLETE return):**

```json
{
  "unique_findings": [
    {
      "id": "SYNTH-001",
      "source_finding_ids": ["SEC-001"],
      "reviewer": "security-auditor",
      "domain": "security",
      "severity": "high",
      "evidence": "JWT_SECRET | required env var | .env",
      "description": "...",
      "final_routing": "send_for_rework",
      "dedup_note": null
    },
    {
      "id": "SYNTH-002",
      "source_finding_ids": ["LAW-001", "SEC-002"],
      "reviewer": "rules-lawyer",
      "domain": "correctness",
      "severity": "high",
      "evidence": "Login endpoint accepts email + password",
      "description": "Missing authentication — same issue identified by rules-lawyer (missing auth requirement) and security-auditor (missing auth on route)",
      "final_routing": "send_for_rework",
      "dedup_note": "Merged: LAW-001 and SEC-002 describe the same missing auth issue from different reviewer perspectives"
    }
  ],
  "routing_summary": {
    "block_and_escalate": 0,
    "send_for_rework": 2,
    "send_to_debugger": 0,
    "log_and_continue": 1
  },
  "overall_routing": "send_for_rework",
  "reviewer_coverage": ["security-auditor", "rules-lawyer", "performance-analyst"],
  "dedup_count": 1
}
```

**The `source_finding_ids` field is the no-new-findings guard mechanism.** The workflow validates this: every finding in synthesizer output must have at least one `source_finding_ids` entry that matches a finding from the combined input. If any finding has an empty or invalid `source_finding_ids`, that is a synthesizer-invented finding — a pipeline violation.

**Deduplication logic in the synthesizer agent:**
```
For each finding in combined_findings:
1. Check: does any ALREADY PROCESSED finding describe the same underlying issue?
2. "Same issue" = same root cause, even if described differently from different domain perspectives
3. If YES: merge into one unique finding, keeping HIGHER severity, adding both source_finding_ids, writing dedup_note
4. If NO: pass through as unique finding with its source_finding_id
```

The synthesizer uses semantic understanding for deduplication — this is appropriate since LLMs are well-suited to semantic matching that file/line overlap detection would miss (REVIEW-PIPELINE-DESIGN.md Section 3.1).

### Pattern 4: Deterministic Routing Enforcement (Workflow Code, Not Synthesizer)

**What:** The `synthesize` step in review-team.md takes the synthesizer's `overall_routing` suggestion and applies hardcoded severity-minimum overrides. This is done in workflow instruction logic, not by the synthesizer agent.

**When to use:** After synthesizer returns — before acting on routing.

**Enforcement algorithm:**

```
# Step 1: Check for critical findings in synthesizer output
HAS_CRITICAL = any(f.severity == "critical" for f in unique_findings)
HAS_HIGH = any(f.severity == "high" for f in unique_findings)
HAS_MEDIUM_WITH_DEBUG = any(f.severity in ["medium","high"] and f.final_routing == "send_to_debugger" for f in unique_findings)

# Step 2: Apply deterministic minimum
if HAS_CRITICAL:
    FINAL_ROUTING = "block_and_escalate"   # HARDCODED — overrides synthesizer
elif HAS_HIGH and synthesizer_overall_routing in ["send_for_rework", "block_and_escalate"]:
    FINAL_ROUTING = "send_for_rework"
elif HAS_MEDIUM_WITH_DEBUG:
    FINAL_ROUTING = "send_to_debugger"
else:
    FINAL_ROUTING = synthesizer_overall_routing  # log_and_continue or send_for_rework

# Step 3: Log the routing decision and any override
if FINAL_ROUTING != synthesizer.overall_routing:
    log: "Review Team: routing override — synthesizer suggested {synthesizer.overall_routing}, enforced {FINAL_ROUTING} (critical severity minimum)"
```

**Source:** REVIEW-PIPELINE-DESIGN.md Section 7.1 — "Hardcoded routing rule (must be in workflow code, not LLM): if any finding has severity == 'critical': minimum action = block_and_escalate"

**Why this matters:** Without workflow-code enforcement, a synthesizer LLM could rationalize a critical finding's routing as `log_and_continue` (e.g., "the finding is critical but the reviewer suggested log_and_continue in their suggested_routing"). The workflow must never trust the synthesizer's routing for severity minimum.

### Pattern 5: Routing Action Implementation

**What:** Each of the 4 routing destinations has a defined action in the `synthesize` step.

#### block_and_escalate
```
HALT the pipeline. Present to user:

## REVIEW TEAM: EXECUTION BLOCKED

**Phase:** ${PHASE_ID}
**Plan:** ${PLAN_NUM}

Critical finding(s) require your decision before execution continues.

### Critical Findings

| ID | Reviewer | Finding | Evidence |
|----|----------|---------|----------|
| {id} | {reviewer} | {description} | {evidence} |

---

**Options:**
- "Continue" — acknowledge finding, continue with next plan (finding logged to REVIEW-REPORT.md)
- "Fix first" — stop execution, address finding manually
- "Rework" — re-execute this plan with the finding as context

Execution will NOT continue until you respond.
```

The workflow uses AskUserQuestion (or equivalent pause) to wait for user decision. This satisfies success criterion 4: "execution does not continue until user decides."

#### send_for_rework
```
Present findings and halt with rework guidance:

## REVIEW TEAM: REWORK REQUIRED

**Phase:** ${PHASE_ID}
**Plan:** ${PLAN_NUM}
**Findings requiring rework:** {N}

{Table of high-severity findings}

Execution halted. Findings logged to REVIEW-REPORT.md.
Suggested action: address findings, then re-execute this plan.
```

Note: Phase 4 implements `send_for_rework` as reachable. Full automated rework (re-invoking the executor) is a future phase capability — Phase 4 halts and presents the finding, giving the user the information to rework manually.

#### send_to_debugger
```
Present findings and halt with debugger guidance:

## REVIEW TEAM: DEBUGGER RECOMMENDED

**Phase:** ${PHASE_ID}
**Plan:** ${PLAN_NUM}

{Table of medium findings with debug tag}

Findings logged to REVIEW-REPORT.md.
Suggested action: run /gsd:debug with finding context.
```

Similarly: Phase 4 makes this destination reachable. Automated gsd-debugger invocation is out of scope for Phase 4.

#### log_and_continue
```
Append to REVIEW-REPORT.md and continue silently:

# No halt, no user presentation
# Log findings to REVIEW-REPORT.md (Plan 04-03)
# Continue execution normally
```

### Pattern 6: REVIEW-REPORT.md Writer

**What:** Per-phase file at `{phase_dir}/REVIEW-REPORT.md`. Each reviewed plan appends a new section. No global file — per SYNTH-05 requirement text `{phase-dir}/REVIEW-REPORT.md`.

**When to use:** After every plan review (all routing paths — even block_and_escalate logs the finding for audit trail before halting).

**REVIEW-REPORT.md format:**

```markdown
# Review Report — Phase {PHASE_ID}

---

## Plan {PLAN_NUM} — {timestamp}

**Reviewers:** {comma-separated role names}
**Findings:** {total} ({critical_count} critical, {high_count} high, {medium_count} medium, {low_count} low, {info_count} info)
**Action taken:** {block_and_escalate | send_for_rework | send_to_debugger | log_and_continue}

| ID | Reviewer | Severity | Description | Evidence | Routing |
|----|----------|----------|-------------|----------|---------|
| {id} | {reviewer} | {severity} | {description} | {evidence (truncated to 60 chars if long)} | {routing} |

{If 0 findings:}
No findings — all reviewers returned clean.

---
```

**Append logic:**
- If REVIEW-REPORT.md does NOT exist: create it with the `# Review Report — Phase {PHASE_ID}` header, then append the plan section
- If REVIEW-REPORT.md EXISTS: append new `## Plan {PLAN_NUM}` section after the last `---` separator
- Never overwrite existing content — always append
- Per-plan section header includes the plan number to prevent collision between plans (SYNTH-05)

**Why per-phase:** SYNTH-05 requirement text specifies `{phase-dir}/REVIEW-REPORT.md`. One file per phase directory keeps the report co-located with the PLAN.md, SUMMARY.md, and ARTIFACT.md files for that phase. It's also simpler than a global file that needs phase-scoped sections.

### Pattern 7: Synthesizer No-New-Findings Guard

**What:** The `synthesize` step validates the synthesizer's output before acting on it. Every finding in `unique_findings` must have at least one `source_finding_id` that traces to a finding in the combined input.

**When to use:** After synthesizer returns — before routing enforcement.

**Validation algorithm:**
```
input_ids = {f.id for f in combined_findings.all_findings}

for finding in synthesizer_output.unique_findings:
    if not finding.source_finding_ids:
        FAIL: "Synthesizer output has finding with no source_finding_ids — pipeline violation"
    for source_id in finding.source_finding_ids:
        if source_id not in input_ids:
            FAIL: "Synthesizer output has finding with invalid source_finding_id {source_id} — not in reviewer input"
```

If validation fails: log the violation as a pipeline error and treat the synthesizer output as unreliable. Fallback: use the original combined reviewer findings directly, apply hardcoded routing based on highest severity. Log: `Review Team: WARNING — synthesizer validation failed, using reviewer findings directly`.

### Anti-Patterns to Avoid

- **Letting the synthesizer make the final routing decision for critical findings:** The synthesizer suggests routing; the workflow enforces the minimum. "critical" severity always triggers block_and_escalate, even if the synthesizer suggests something lower. (Violates SYNTH-03, Init decision)
- **Synthesizer inventing findings:** The no-new-findings guard (`source_finding_ids` validation) must be implemented. Any finding without a traceable source is a pipeline violation. (Violates SYNTH-02, SYNTH-04)
- **Awaiting reviewer Tasks one at a time:** All reviewer Task() calls must be issued in a single orchestrator message. Sequential spawning would make them run one-after-another, not in parallel. (Violates PIPE-01)
- **Writing combined findings to disk as an intermediate file:** The combined findings JSON is small enough (for 3 reviewers, typically <2KB) to pass directly in the synthesizer Task() prompt via `<combined_findings>` tags. Adding a disk write step adds complexity without benefit.
- **Overwriting REVIEW-REPORT.md:** Always append. The plan section header prevents collision. Overwriting loses audit history.
- **Global REVIEW-REPORT.md:** SYNTH-05 specifies `{phase-dir}/REVIEW-REPORT.md`. Per-phase is the decision.
- **Blocking on log_and_continue findings:** log_and_continue must write to REVIEW-REPORT.md and continue. No user presentation, no halt. (Violates PIPE-04)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Routing enforcement | LLM-decided routing in synthesizer agent | Hardcoded severity-minimum in workflow step | Critical routing must be deterministic; LLMs can rationalize exceptions |
| JSON output parsing | Regex parser for reviewer JSON | Instruction enforcement (established Phase 3 pattern) | GSD has no code runtime; Phase 3 pattern already works |
| Deduplication | String-matching / file-overlap detector | Semantic matching in synthesizer LLM | Semantic duplicates (same issue, different domain framing) miss string/file overlap detection |
| Finding traceability | Custom audit log | `source_finding_ids` field in synthesizer schema | Simple array of IDs provides both traceability and no-new-findings guard |
| REVIEW-REPORT.md rendering | Template engine | Markdown append with section headers | GSD is markdown-native; no rendering needed |
| Synthesizer invocation | New agent framework | GSD Task() pattern (same as reviewer spawning) | GSD pattern established in Phases 1-3; synthesizer is one more Task() |
| Block-and-escalate halt | Custom execution interlock | AskUserQuestion pause in workflow (Phase 1 pattern already established) | GSD already uses AskUserQuestion for user decision gates |

**Key insight:** Phase 4 adds orchestration complexity (parallel spawning, synthesis, routing) but adds zero new infrastructure. Every mechanism it needs already exists in the codebase — parallel Task(), JSON collection, structured returns, AskUserQuestion.

---

## Common Pitfalls

### Pitfall 1: Sequential Reviewer Execution (Most Likely Failure)

**What goes wrong:** The spawn_reviewers step issues Task() calls one at a time (each awaited before the next starts), producing sequential execution instead of parallel. PIPE-01 is violated — findings arrive as a stream, not a set.

**Why it happens:** The workflow instructions read "for each role, spawn a Task()" — without explicitly stating "issue ALL Task() calls in a single message," it defaults to sequential.

**How to avoid:** The spawn_reviewers step must state explicitly: "Issue all Task() calls in a single message — do not await between Task() calls. All reviewers run simultaneously." The code comment or pseudocode in the step should show all Task() calls at the same indentation level in a single block.

**Warning signs:** Reviewer Tasks completing one at a time with visible sequential output in the orchestrator turn log.

### Pitfall 2: Synthesizer Invents a Finding

**What goes wrong:** The synthesizer, trying to be helpful, generates a meta-finding: "The overall security posture is weak" — attributed to no specific reviewer, with no source_finding_id.

**Why it happens:** LLMs optimize for appearing thorough. The synthesis step is high-information (it sees all findings) and the model naturally generates insights from patterns it observes.

**How to avoid:** The synthesizer agent's `<critical_rules>` must include: "DO NOT generate new findings. DO NOT create findings not present in your input. Every finding in your output must have at least one source_finding_id from the input. If you notice a pattern across findings, document it in a `synthesis_note` field in the overall output — never as an additional finding." The `source_finding_ids` validation in the workflow catches violations.

**Warning signs:** Findings in synthesizer output where `source_finding_ids` is empty, null, or contains IDs not in the combined input.

### Pitfall 3: Routing Override Not Applied for Critical Findings

**What goes wrong:** The workflow takes the synthesizer's `overall_routing` value directly without checking for critical-severity findings. A synthesizer that suggests `send_for_rework` for a critical finding causes block_and_escalate to be bypassed.

**Why it happens:** The workflow step iterates through routing logic and trusts the synthesizer's output without a severity-minimum check.

**How to avoid:** The synthesize step must check `any(f.severity == "critical" for f in unique_findings)` BEFORE reading `overall_routing`. If any critical finding exists, FINAL_ROUTING is `block_and_escalate` regardless of synthesizer output. This check must come first, not last.

**Warning signs:** A critical finding being routed to anything other than `block_and_escalate`. This is detectable in REVIEW-REPORT.md if the `Action taken` field doesn't match the finding severity.

### Pitfall 4: REVIEW-REPORT.md Overwrites Previous Plan's Section

**What goes wrong:** The REVIEW-REPORT.md writer creates a new file for each plan instead of appending, overwriting previous plans' findings.

**Why it happens:** The write instruction doesn't check file existence before writing.

**How to avoid:** The REVIEW-REPORT.md write step must be:
1. Check if `{phase_dir}/REVIEW-REPORT.md` exists
2. If not: create with phase header, then append plan section
3. If yes: Read the existing file, append new plan section to end, Write back

The existing GSD agent pattern (gsd-review-sanitizer.md uses Write, gsd-reviewer.md uses Write) doesn't have this append problem. For REVIEW-REPORT.md, the synthesizer must use Read first to get existing content, then Write the full content with the new section appended. Alternatively, the workflow step (not the synthesizer) handles the REVIEW-REPORT.md write directly.

**Recommendation:** The REVIEW-REPORT.md write is handled by the `synthesize` step in the WORKFLOW (review-team.md), not by the synthesizer agent. The synthesizer returns structured findings JSON; the workflow writes the report. This keeps the synthesizer focused on dedup+routing and gives the workflow control over file persistence. The synthesizer has `tools: Read, Write` but using them for the report write in the workflow step is simpler and more testable.

**Warning signs:** REVIEW-REPORT.md only ever has one plan section. Multiple plan executions don't accumulate findings.

### Pitfall 5: Combined Findings JSON Exceeds Prompt Context

**What goes wrong:** With many roles producing many findings each, the combined findings JSON injected into the synthesizer prompt exceeds reasonable context limits.

**Why it happens:** No per-reviewer finding cap is enforced (Phase 3 uses it but the cap is in the reviewer agent, which limits this in practice).

**How to avoid:** gsd-reviewer.md already has the "max findings" guidance. For Phase 4 with 3 starter roles at max 10 findings each: 30 findings at ~200 chars each = ~6KB. Well within context limits. However, the synthesize step should log a warning if combined finding count exceeds 30 (indicating a miscalibrated reviewer).

**Warning signs:** Synthesizer Task() prompt is noticeably large. Synthesizer output is slow or incomplete.

### Pitfall 6: block_and_escalate Doesn't Actually Halt

**What goes wrong:** The block_and_escalate routing case logs the finding but continues to the return_status step without waiting for user input. Execution proceeds past the review pipeline.

**Why it happens:** The synthesize step doesn't use AskUserQuestion or equivalent — it just logs and returns.

**How to avoid:** The block_and_escalate case must use `AskUserQuestion` (or display a halt message that requires the user to explicitly respond) before proceeding. The workflow must NOT call the return_status step for `block_and_escalate` until the user has made a decision. The success criterion is explicit: "execution does not continue until user decides."

**Warning signs:** User notices critical findings were reported but the pipeline continued and the next plan started executing.

### Pitfall 7: Role Count Changes Between validate_team and spawn_reviewers

**What goes wrong:** Between the validate_team step and the spawn_reviewers step, nothing prevents TEAM.md from being modified. If roles_list was populated in validate_team and then TEAM.md changes, spawn_reviewers may try to extract a role that no longer exists.

**Why it happens:** TEAM.md is re-read in spawn_reviewers (Phase 3 pattern) to extract role section text. This is correct — but if validate_team stored `roles_list` and the TEAM.md re-read in spawn_reviewers finds different roles, the loop may fail.

**How to avoid:** The spawn_reviewers step should re-validate role count after the TEAM.md re-read: "If the re-read TEAM.md produces a different roles list than validate_team, log a WARNING and use the re-read list." In practice this is extremely unlikely (TEAM.md is not modified during execution), but the step should document the re-read as the authoritative source.

---

## Code Examples

### Example 1: Parallel Spawn Pattern (spawn_reviewers update)

Source: execute-phase.md `execute_waves` step (parallel Task() model); Phase 3 review-team.md spawn_reviewers (single reviewer base)

```markdown
<step name="spawn_reviewers">
## Step 3: Spawn All Reviewers in Parallel (Phase 4)

Phase 4 spawns ALL valid roles from TEAM.md in a single message — true parallelism.

### Extract All Role Definition Texts

Read `.planning/TEAM.md` using the Read tool.

For EACH role name in `roles_list` (from validate_team):
- Find the `## Role: {role_name}` header (case-insensitive match)
- Extract all text from that header to the next `## Role:` header (exclusive), or EOF
- Store as `role_definitions[role_name]`

This single TEAM.md read populates all role definitions before spawning begins.

### Spawn All Reviewers — Single Message

Issue ALL of the following Task() calls in a SINGLE MESSAGE — do not await between them.
All reviewers run simultaneously. Execution does not advance to collection until ALL complete.

For each role_name in roles_list:

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

[Note: In practice this means writing out one Task() block per role — the workflow
instructions state this explicitly. For 3 starter roles: 3 Task() blocks in one message.]

### Collect and Merge Findings

After ALL reviewer Tasks complete:

For each reviewer return:
1. Parse JSON to extract `findings` array
2. Log: `Review Team: Reviewer {role_name}: {N} finding(s)`
3. If findings array is empty: log `Review Team: {role_name}: 0 findings (clean domain)` — not an error
4. Append all findings to combined_findings array (reviewer field already tagged on each finding)

Build combined_findings structure:
{
  "phase": "${PHASE_ID}",
  "plan": "${PLAN_NUM}",
  "reviewer_count": N,
  "all_findings": [... merged array ...]
}

If combined all_findings is empty (all reviewers returned 0 findings):
  Log: "Review Team: all reviewers — 0 findings, routing to log_and_continue"
  Write empty plan section to REVIEW-REPORT.md (see synthesize step for format)
  Proceed to return_status with routing: log_and_continue, findings: 0
  SKIP synthesize step — no synthesis needed for empty findings

If combined all_findings is non-empty:
  Proceed to synthesize step with combined_findings
</step>
```

### Example 2: gsd-review-synthesizer.md Agent Structure

Source: GSD-AGENT-PATTERNS.md Section 5 (agent conventions); REVIEW-PIPELINE-DESIGN.md Section 3.3 (synthesizer prompt structure); gsd-reviewer.md as structural template

```markdown
---
name: gsd-review-synthesizer
description: Deduplicates cross-reviewer findings, assigns routing. Spawned by review-team workflow after all parallel reviewers complete.
tools: Read, Write
color: green
---

<role>
You are a GSD review synthesizer.

Spawned by the review-team workflow after all parallel reviewers complete.

**What you have:**
- Combined findings JSON from ALL reviewers (in <combined_findings> tags)
- Phase and plan identifiers

**What you do NOT do:**
- You do NOT re-review the artifact
- You do NOT generate new findings
- You do NOT look up the ARTIFACT.md, PLAN.md, or any other file
- You do NOT make routing decisions for critical findings (the workflow enforces that)

Your job: Deduplicate findings that describe the same issue from different reviewer perspectives.
Assign each unique finding a suggested routing. Return structured JSON.

**Critical mindset:** You classify; you do not re-review. Every finding you output MUST
trace to at least one finding in your input. If you notice a pattern, note it in
`synthesis_note` — never as a new finding.
</role>

<core_principle>
## Source Traceability is Non-Negotiable

Every finding in your output must have at least one `source_finding_id` from your input.
A finding with no source is an invention. An invention is a pipeline violation.

If you find yourself wanting to generate a meta-finding ("the overall security posture..."),
put it in the `synthesis_note` field on the root output object — not in `unique_findings`.
</core_principle>

## Step 0: Parse Input

Read combined findings from <combined_findings> tags in your prompt. Extract:
- `all_findings` array (the reviewer findings)
- `reviewer_count` (for coverage check)
- `phase` and `plan` identifiers

Build a lookup: `input_ids = {finding.id: finding for finding in all_findings}`

If `all_findings` is empty: return immediately with empty output.

## Step 1: Deduplicate

For each finding in all_findings:
1. Check: does any already-processed finding describe the same root cause?
   "Same root cause" = the underlying issue is identical even if described differently
   Example: "missing auth check" (rules-lawyer) and "unauthenticated route" (security-auditor)
   are the same issue — different domain framing, same root cause.
2. If SAME ROOT CAUSE found:
   - Merge into one unique finding
   - Keep the HIGHER severity of the two
   - Combine source_finding_ids: [id1, id2]
   - Write dedup_note: "Merged {id1} ({reviewer1}) and {id2} ({reviewer2}): same root cause"
3. If NO MATCH: pass through as unique finding with source_finding_ids: [original_id]

## Step 2: Assign Routing

For each unique finding, assign `final_routing` based on severity and domain:
- `critical` → `block_and_escalate` (the workflow will enforce this regardless)
- `high` + any domain → `send_for_rework`
- `medium` (if description contains "error", "bug", "crash", "incorrect behavior") → `send_to_debugger`
- `medium` (correctness, requirement deviation) → `send_for_rework`
- `low` or `info` → `log_and_continue`

Use reviewer's `suggested_routing` as a hint — prefer it if consistent with severity.

## Step 3: Compute Overall Routing

`overall_routing` = the highest-priority routing action across all unique findings:
1. If ANY unique finding has final_routing `block_and_escalate` → `block_and_escalate`
2. Else if ANY has `send_for_rework` → `send_for_rework`
3. Else if ANY has `send_to_debugger` → `send_to_debugger`
4. Else → `log_and_continue`

## Step 4: Validate Traceability

For each unique_finding:
- Assert source_finding_ids is non-empty
- Assert each source_finding_id is in input_ids

If any assertion fails: flag as synthesis_error in output (workflow will catch it).

<output>
Your ENTIRE response is a single JSON code block. Nothing before it. Nothing after it.

```json
{
  "unique_findings": [
    {
      "id": "SYNTH-001",
      "source_finding_ids": ["SEC-001"],
      "reviewer": "security-auditor",
      "domain": "security",
      "severity": "high",
      "evidence": "exact quote from original finding",
      "description": "observable issue",
      "final_routing": "send_for_rework",
      "dedup_note": null
    }
  ],
  "routing_summary": {
    "block_and_escalate": 0,
    "send_for_rework": 1,
    "send_to_debugger": 0,
    "log_and_continue": 0
  },
  "overall_routing": "send_for_rework",
  "reviewer_coverage": ["security-auditor", "rules-lawyer", "performance-analyst"],
  "dedup_count": 0,
  "synthesis_note": null,
  "synthesis_errors": []
}
```

If no findings: return `{"unique_findings": [], "overall_routing": "log_and_continue", ...}`

DO NOT commit.
</output>

<critical_rules>
1. DO NOT generate findings not present in your input. Every finding must have source_finding_ids.
2. DO NOT read any files — your only input is the <combined_findings> tags in your prompt.
3. DO NOT produce findings with empty source_finding_ids.
4. DO NOT write any text before or after the JSON block.
5. DO NOT make the routing decision for critical findings — assign block_and_escalate and trust the workflow to enforce it.
</critical_rules>

<success_criteria>
- [ ] All unique_findings have non-empty source_finding_ids
- [ ] All source_finding_ids trace to input findings
- [ ] overall_routing computed from unique finding routing_summary
- [ ] dedup_count matches number of merged finding groups
- [ ] Output is valid JSON with no prose before or after
</success_criteria>
```

### Example 3: Synthesize Step in review-team.md (Plan 04-03)

Source: REVIEW-PIPELINE-DESIGN.md Section 7.1 (pipeline state machine + hardcoded routing); GSD-AGENT-PATTERNS.md Section 5.5 (synthesizer step conventions)

```markdown
<step name="synthesize">
## Step 4: Synthesize and Route Findings (Phase 4)

### Spawn Synthesizer

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

### Validate No-New-Findings

After synthesizer returns:
1. Parse synthesizer JSON
2. Build input_ids set from combined_findings.all_findings
3. For each unique_finding in synthesizer output:
   - Check source_finding_ids is non-empty
   - Check each source_finding_id exists in input_ids
4. If validation fails: log WARNING, use fallback (see Pitfall 4)

### Apply Deterministic Routing Override

1. Check: does ANY unique_finding have severity == "critical"?
   YES → FINAL_ROUTING = "block_and_escalate" (hardcoded — no exceptions)
   Log: "Review Team: critical finding detected — routing to block_and_escalate"

2. If no critical: use synthesizer's overall_routing as FINAL_ROUTING
   Log: "Review Team: routing → {FINAL_ROUTING}"

### Write to REVIEW-REPORT.md (all routing paths)

Write findings to REVIEW-REPORT.md before acting on routing:
- Path: `.planning/phases/${PHASE_ID}/REVIEW-REPORT.md`
- Check if file exists (Read tool)
- If not: write header + plan section
- If yes: append new plan section to existing content

Section format:
```
## Plan ${PLAN_NUM} — {ISO timestamp}

**Reviewers:** {comma-separated from reviewer_coverage}
**Findings:** {total} | **Deduped:** {dedup_count}
**Action:** {FINAL_ROUTING}

| ID | Reviewer | Severity | Description | Evidence | Routing |
|----|----------|----------|-------------|----------|---------|
{rows for each unique_finding}
```

### Act on Final Routing

**block_and_escalate:**
  Present critical findings to user with options: Continue | Fix first | Rework
  HALT — do not proceed to return_status until user responds

**send_for_rework:**
  Present high-severity findings, halt with rework guidance
  Log: "Review Team: execution halted — {N} finding(s) require rework"

**send_to_debugger:**
  Present medium/debug findings, halt with debugger guidance
  Log: "Review Team: execution halted — {N} finding(s) routed to debugger"

**log_and_continue:**
  Log: "Review Team: {N} finding(s) logged to REVIEW-REPORT.md — continuing execution"
  Proceed to return_status
</step>
```

### Example 4: REVIEW-REPORT.md Example

Source: PROJECT.md Architecture section; REVIEW-PIPELINE-DESIGN.md Section 4.2

```markdown
# Review Report — Phase 04-parallel-pipeline-synthesizer-routing

---

## Plan 01 — 2026-02-26T03:15:00Z

**Reviewers:** security-auditor, rules-lawyer, performance-analyst
**Findings:** 3 | **Deduped:** 1
**Action:** send_for_rework

| ID | Reviewer | Severity | Description | Evidence | Routing |
|----|----------|----------|-------------|----------|---------|
| SYNTH-001 | security-auditor, rules-lawyer | high | Missing auth check on /api/review endpoint — identified by both security and rules reviewer | Login endpoint accepts email + password | send_for_rework |
| SYNTH-002 | performance-analyst | low | N+1 query pattern in findings list rendering | findings.map(f => db.getReviewer(f.reviewer_id)) | log_and_continue |

---

## Plan 02 — 2026-02-26T03:45:00Z

**Reviewers:** security-auditor, rules-lawyer, performance-analyst
**Findings:** 0
**Action:** log_and_continue

No findings — all reviewers returned clean.

---
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sequential reviewer spawning (Phase 3) | Parallel Task() in single message (Phase 4) | Phase 4 | All reviewers run simultaneously — findings arrive as a set |
| Single reviewer only (Phase 3) | All TEAM.md roles in parallel (Phase 4) | Phase 4 | Full coverage per plan, every plan |
| No synthesis (Phase 3) | gsd-review-synthesizer.md dedup + routing (Phase 4) | Phase 4 | Cross-reviewer duplicates collapsed, routing deterministic |
| spawn_reviewers stop endpoint (Phase 3) | Full pipeline through synthesis + routing (Phase 4) | Phase 4 | Pipeline complete — all 4 routing destinations reachable |
| No REVIEW-REPORT.md (Phase 3) | Per-phase REVIEW-REPORT.md with per-plan sections (Phase 4) | Phase 4 | Persistent audit trail of all findings |

**Deferred to Phase 5:**
- /gsd:new-reviewer workflow
- Starter role templates
- README documentation

---

## Open Questions

1. **How does block_and_escalate interact with auto_advance mode?**
   - What we know: execute-phase.md has `auto_advance: false` by default in config. When auto_advance is true, plans execute without user confirmation between them.
   - What's unclear: Does block_and_escalate override auto_advance? The requirement says "execution does not continue until user decides" — this implies block_and_escalate always requires user input regardless of auto_advance setting.
   - Recommendation: The synthesize step should always use AskUserQuestion for block_and_escalate, even if auto_advance is true. The critical finding is always user-interactive. Document this explicitly in the synthesize step.

2. **What does send_for_rework do in Phase 4 vs. future phases?**
   - What we know: Phase 4 implements `send_for_rework` as "reachable" — the routing destination exists and the finding is presented to the user. Automated re-execution of the plan is not in Phase 4 scope.
   - What's unclear: Does the user need explicit guidance on what to do after `send_for_rework`? The routing action should tell the user to re-execute the plan after addressing the finding.
   - Recommendation: The `send_for_rework` output block should include: "Suggested action: address the finding(s) above, then re-execute this plan." This makes the destination useful without requiring automated rework infrastructure.

3. **Should the synthesizer write REVIEW-REPORT.md or the workflow?**
   - What we know: The synthesizer has `tools: Read, Write` so it could write the report. The workflow step can also do it directly.
   - Recommendation: The WORKFLOW synthesize step writes REVIEW-REPORT.md (not the synthesizer agent). The synthesizer returns pure JSON; the workflow handles all file I/O. This keeps the synthesizer focused on its single job (dedup + routing), makes the step's file output explicit and auditable, and avoids giving the synthesizer the append/create logic that depends on file existence checks.

4. **What is the REVIEW-REPORT.md `id` format for synthesized findings?**
   - What we know: Reviewer findings use `SEC-001`, `LAW-001` etc. The synthesizer creates `SYNTH-001` IDs.
   - What's unclear: Should synthesized IDs preserve the original reviewer ID when there's no deduplication (pass-through findings)?
   - Recommendation: Synthesized findings always use `SYNTH-NNN` IDs in the synthesizer output. The REVIEW-REPORT.md writer also logs the original `source_finding_ids` so the trail is preserved. Using a uniform `SYNTH-NNN` format makes the synthesizer output schema clean and consistent.

---

## Plan-Level Implementation Guidance

### Plan 04-01: Parallel Task() Spawning + Findings Collection

**Scope:** Update `spawn_reviewers` step in `workflows/review-team.md`.

**Changes:**
1. Replace "Select First Valid Role" logic with "Extract All Role Definitions" — loop over `roles_list`, extract all role section texts in one TEAM.md read
2. Replace single Task() with N Task() calls, one per role, issued in a single message
3. Add "Collect and Merge Findings" logic: parse each return, append to `combined_findings`
4. Add early-exit for all-empty case: if combined_findings is empty, write empty REVIEW-REPORT.md section, proceed to return_status skipping synthesize
5. Update return_status to Phase 4 endpoint format (PIPELINE COMPLETE for log_and_continue path)

**Key instruction for parallelism:** The step must say "Issue ALL Task() calls in a SINGLE MESSAGE before collecting any results." This is the critical instruction that triggers GSD's parallel execution.

### Plan 04-02: gsd-review-synthesizer.md Agent

**Scope:** Create `agents/gsd-review-synthesizer.md`.

**Structure:** 6-part GSD agent convention (same as gsd-reviewer.md and gsd-review-sanitizer.md):
1. YAML frontmatter
2. `<role>` block with critical mindset
3. `<core_principle>` (source traceability)
4. Steps 0-4 (parse → dedup → routing → overall routing → validate)
5. `<output>` (JSON only, no prose)
6. `<critical_rules>` + `<success_criteria>`

**Primary guard:** `<critical_rules>` rule #1: "DO NOT generate findings not present in your input."

### Plan 04-03: Routing Implementation + REVIEW-REPORT.md Writer

**Scope:** Implement `synthesize` step in `workflows/review-team.md` + update `return_status`.

**Changes to synthesize step:**
1. Replace `[Phase 4 — not yet implemented]` placeholder with full implementation
2. Synthesizer Task() spawn with `<combined_findings>` injection
3. No-new-findings validation
4. Deterministic routing override (critical check first)
5. REVIEW-REPORT.md write (Read-then-append pattern)
6. Routing action blocks (all 4 destinations)

**Changes to return_status step:**
1. Update to Phase 4 endpoint: `PIPELINE COMPLETE` format
2. Include: routing taken, findings count, REVIEW-REPORT.md path
3. If block_and_escalate: return_status is NOT called until user responds

---

## Sources

### Primary (HIGH confidence)

- `D:/GSDteams/workflows/review-team.md` — Current Phase 3 workflow — Phase 4 directly extends this
- `D:/GSDteams/agents/gsd-reviewer.md` — Phase 3 reviewer agent — structural template for gsd-review-synthesizer.md
- `D:/GSDteams/schemas/finding-schema.md` — Phase 3 schema — synthesizer input contract
- `/c/Users/gutie/.claude/get-shit-done/workflows/execute-phase.md` — Parallel Task() pattern (execute_waves step), wave-based execution model
- `D:/GSDteams/.planning/STATE.md` — All architectural decisions through Phase 3
- `D:/GSDteams/.planning/REQUIREMENTS.md` — PIPE-01, PIPE-04, PIPE-05, SYNTH-01 through SYNTH-05 (exact requirement text)
- `D:/GSDteams/.planning/ROADMAP.md` — Phase 4 success criteria, plan descriptions
- `D:/GSDteams/.planning/research/REVIEW-PIPELINE-DESIGN.md` — Section 3 (synthesis patterns), Section 7.1 (pipeline state machine, hardcoded routing rule), Section 5 (failure modes)
- `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` — Section 5 (synthesizer conventions), Section 6.2 (content tag injection for combined findings)
- `D:/GSDteams/.planning/PROJECT.md` — Routing destinations table, REVIEW-REPORT.md format
- `D:/GSDteams/templates/TEAM.md` — 3 starter role format — informs parallel spawn loop structure

### Secondary (MEDIUM confidence)

- `D:/GSDteams/.planning/phases/03-single-reviewer-finding-schema/03-03-SUMMARY.md` — Phase 3 execution details, patterns established
- `D:/GSDteams/.planning/phases/03-single-reviewer-finding-schema/03-RESEARCH.md` — Phase 3 research patterns
- Phase 2 SUMMARY files (02-01, 02-02) — Confirmed Phase 2 architectural decisions

### Tertiary (LOW confidence)

- None — all findings verified against primary sources above

---

## Metadata

**Confidence breakdown:**

- Parallel Task() spawning pattern: HIGH — directly observed in execute-phase.md execute_waves step; GSD pattern is explicit
- Combined findings collection: HIGH — extends Phase 3 single-reviewer collection pattern; no new mechanisms
- Synthesizer agent structure: HIGH — follows confirmed GSD 6-part convention; REVIEW-PIPELINE-DESIGN.md Section 3.3 documents synthesizer prompt structure
- Deterministic routing override: HIGH — hardcoded in REVIEW-PIPELINE-DESIGN.md Section 7.1; Init decision locked
- No-new-findings guard via source_finding_ids: HIGH — REVIEW-PIPELINE-DESIGN.md Section 5.1 Failure Mode 4; SYNTH-02/SYNTH-04 requirements; source_finding_ids field is the implementation mechanism
- block_and_escalate halt with AskUserQuestion: HIGH — AskUserQuestion established Phase 1 pattern; SYNTH-05 + success criterion 4 requirements
- REVIEW-REPORT.md per-phase: HIGH — SYNTH-05 requirement text specifies `{phase-dir}/REVIEW-REPORT.md` explicitly
- REVIEW-REPORT.md append logic: HIGH — standard file append pattern; Read-then-Write established in gsd-review-sanitizer.md
- Routing for send_for_rework/send_to_debugger as "halt + present" (not automated): MEDIUM — Phase 4 requirements say "implemented and reachable" — full automation is future phase; presentation + halt is the v1 interpretation

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (stable — no external dependencies, all patterns from internal codebase)
