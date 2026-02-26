# Phase 3: Single Reviewer + Finding Schema - Research

**Researched:** 2026-02-25
**Domain:** GSD agent design (reviewer), JSON finding schema, severity rubric, domain isolation, workflow spawning
**Confidence:** HIGH

---

## Summary

Phase 3 is the first time any reviewer agent actually fires. It adds three artifacts to the project: a finding JSON schema definition (03-01), the `gsd-reviewer.md` agent (03-02), and an updated `review-team.md` workflow that implements the `spawn_reviewers` placeholder for a single reviewer (03-03).

The central design challenges are all about output discipline and isolation enforcement. The reviewer must produce pure JSON (no prose wrapping), include a direct quote from ARTIFACT.md in every `evidence` field (no evidence = no finding), stay inside its declared domain via an explicit `not_responsible_for` list, and assign severity using a rubric with a tie-breaking rule. The single-reviewer constraint in Phase 3 (picking the first valid role from TEAM.md) deliberately validates the pattern end-to-end before Phase 4 multiplies to parallel.

The REVIEW-PIPELINE-DESIGN.md research (from project initialization) is the highest-trust source for this phase. It documents the finding schema, severity calibration approach, hallucination prevention, and domain isolation techniques — all directly applicable to Phase 3. Everything in this research is grounded in that internal research plus direct inspection of the Phase 2 artifacts (gsd-review-sanitizer.md, review-team.md) and the TEAM.md starter template.

**Primary recommendation:** The `gsd-reviewer.md` agent is parameterized via `<role_definition>` tag injection in the Task() prompt — one agent file serves all roles. The finding schema is simpler than the full SARIF-inspired schema in REVIEW-PIPELINE-DESIGN.md; Phase 3 uses a 7-field subset that satisfies the requirements exactly (`id, reviewer, domain, severity, evidence, description, suggested_routing`) and no more. The JSON output format is enforced by a JSON fenced code block instruction combined with an explicit "no prose before or after" constraint in `<critical_rules>`.

---

## Standard Stack

### Core

| Component | Type | Purpose | Why Standard |
|-----------|------|---------|--------------|
| `agents/gsd-reviewer.md` | GSD agent | Reviews ARTIFACT.md against injected role definition, returns JSON findings | Core reviewer — parameterized to serve all roles |
| `workflows/review-team.md` | GSD workflow | Updated to implement spawn_reviewers for first valid role | Phase 2 placeholder becomes Phase 3 implementation |
| Finding JSON schema | Design artifact | Contract between reviewer and synthesizer | Required by REVR-02, REVR-06 |
| Severity rubric | Design artifact embedded in agent | Calibration guard for finding severity assignment | Required by REVR-05 |

### Supporting

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| TEAM.md role parsing (from Phase 2) | Extract first valid role + its definition text | In spawn_reviewers step |
| ARTIFACT.md path convention (from Phase 2) | Locate the sanitized artifact for the reviewer | In spawn_reviewers step |
| `<role_definition>` tag injection | Pass role content from TEAM.md to reviewer agent | Every reviewer Task() spawning |
| `not_responsible_for` list | Enforce domain isolation in reviewer role block | Embedded in reviewer agent, sourced from TEAM.md role |

### No External Dependencies

Phase 3 requires zero external libraries. All three artifacts are pure GSD markdown agents/workflows. The only tools needed are Read and Write (built into Claude Code).

---

## Architecture Patterns

### Recommended File Layout (Phase 3 additions)

```
get-shit-done-review-team/
  agents/
    gsd-review-sanitizer.md       # Phase 2 COMPLETE
    gsd-reviewer.md               # Plan 03-02 -- THIS PHASE
  workflows/
    review-team.md                # Updated in Plan 03-03 -- spawn_reviewers implemented
```

After install, these land at:
- `~/.claude/get-shit-done-review-team/agents/gsd-reviewer.md`
- `~/.claude/get-shit-done-review-team/workflows/review-team.md` (updated)

### Pattern 1: Parameterized Agent via Role Injection

**What:** A single `gsd-reviewer.md` agent file serves ALL roles. The role definition from TEAM.md is injected at spawn time via `<role_definition>` tags in the Task() prompt. The agent reads its assigned role from those tags, not from hardcoded content.

**When to use:** Every reviewer Task() spawning. REVR-06 requires reviewers to be spawnable without modification.

**Why this works:** GSD workflows already use XML-like content tags for structured injection (documented in GSD-AGENT-PATTERNS.md Section 6.2). The agent's process section references `<role_definition>` tags explicitly. The role content (name, focus, what this role reviews, severity thresholds, routing hints, not_responsible_for) is extracted from the role section in TEAM.md and injected verbatim.

```
Task(
  subagent_type="gsd-reviewer",
  prompt="
    <objective>
    Review the sanitized artifact against your assigned role criteria.
    Return structured findings as JSON.
    </objective>

    <inputs>
    Artifact path: {artifact_path}
    Phase: {phase_id}
    Plan: {plan_num}
    </inputs>

    <role_definition>
    {full text of the role section from TEAM.md, verbatim}
    </role_definition>

    <execution_context>
    @~/.claude/get-shit-done-review-team/agents/gsd-reviewer.md
    </execution_context>
  "
)
```

Source: GSD-AGENT-PATTERNS.md Section 6.2 (content tag injection pattern)

### Pattern 2: GSD Agent 6-Part Structure for gsd-reviewer.md

**What:** The reviewer agent follows the exact 6-part GSD agent convention — identical to gsd-review-sanitizer.md from Phase 2.
**When to use:** Always — this is the GSD agent contract.

```yaml
---
name: gsd-reviewer
description: Reviews sanitized execution output against assigned role criteria. Returns structured findings as JSON. Spawned in parallel by review-team workflow.
tools: Read, Write
color: green
---
```

**Rationale for `tools: Read, Write` only:** The reviewer is a content analyst. It reads one file (ARTIFACT.md), produces structured text (JSON findings). No codebase inspection, no bash, no grep. Minimal tool surface is a security practice.

Source: GSD-AGENT-PATTERNS.md Section 5.1 (gsd-reviewer frontmatter conventions)

### Pattern 3: Explicit `not_responsible_for` List in `<role>` Block

**What:** The reviewer's `<role>` block contains an explicit "What you are NOT responsible for" list extracted from the TEAM.md role definition. This is the primary domain isolation mechanism.

**When to use:** Every reviewer invocation. REVR-03 (actual requirement number from REQUIREMENTS.md) requires the `not_responsible_for` list as a DO NOT guard in the `<role>` block.

**Why an explicit list works:** LLMs are generalists and will drift into adjacent domains without permission to ignore them. The NOT-responsible list gives the model explicit permission to ignore off-domain observations. Without it, reviewers bleed — a Security Auditor starts commenting on code style because it *can*, not because it *should*.

```xml
<role>
You are a GSD reviewer assigned the role: {ROLE_NAME}.

Spawned by the review-team workflow. You run in a fresh, isolated context.

**What you have:**
- The sanitized artifact description (ARTIFACT.md)
- Your role definition (below)

**What you do NOT have (by design):**
- The PLAN.md that produced this output
- The executor's raw SUMMARY.md
- Any prior phase summaries or reasoning chains
- Knowledge of what the executor "intended"
- Other reviewers' findings

**Your domain:**
{focus from role definition}

**You are NOT responsible for:**
{not_responsible_for from role definition}

If you find yourself wanting to note something outside your domain, suppress it. Write ONLY: [OUT_OF_SCOPE] if you must acknowledge it. Do not explain what it was. Do not include it in your findings.

Your job: Review ARTIFACT.md against your role criteria. Return findings as JSON.

**Critical mindset:** Fresh eyes are your value. If you find yourself speculating about intent or context you were not given, stop. You review only what is in the artifact.
</role>
```

Source: REVIEW-PIPELINE-DESIGN.md Section 2.1 (role isolation techniques); GSD-AGENT-PATTERNS.md Section 5.2, 5.3

### Pattern 4: Evidence-First Finding Policy

**What:** No finding is reportable without a direct quote from ARTIFACT.md in the `evidence` field. This is the primary hallucination prevention mechanism.

**When to use:** Enforced in `<critical_rules>` for every finding.

**Evidence enforcement instruction:**
```
You may ONLY report a finding if you can quote the specific text from ARTIFACT.md
that demonstrates it. The `evidence` field MUST be a direct quote — not a
paraphrase, not a description of what you inferred, not a reference to what code
"typically" looks like.

If you cannot find a direct quote that grounds the finding, do not report it.
```

Source: REVIEW-PIPELINE-DESIGN.md Section 2.4 (evidence-first instruction)

### Pattern 5: Severity Rubric with Tie-Breaking Rule

**What:** A severity rubric embedded in the reviewer agent defines exactly what `critical`, `high`, `medium`, `low`, and `info` mean — with a tie-breaking rule ("when in doubt, go lower").

**REVR-05 severity levels:** The requirements specify: `info`, `low`, `medium`, `high`, `critical`. This is a 5-level enum (not the 4-level enum in REVIEW-PIPELINE-DESIGN.md). The agent must use these exact strings.

**Why a rubric matters:** Without anchoring, LLMs escalate severity (Severity Inflation — Failure Mode 1 in REVIEW-PIPELINE-DESIGN.md Section 5.1). Reviewers optimize for appearing thorough. The rubric plus the "when in doubt, go lower" rule is empirically effective at calibrating output.

**Rubric structure:**
```
CRITICAL: Would cause data loss, security breach, or complete system failure in production.
          No reasonable person would ship code with this finding unresolved.
          Example: Hardcoded credentials, SQL injection, auth bypass.

HIGH: Incorrect behavior that would reach users or break core functionality.
      Fix required before shipping.
      Example: Race condition in payment processing, missing authentication on a route.

MEDIUM: Behavior that deviates from stated requirements or established patterns.
        Should fix before next plan executes.
        Example: Missing input validation on an API field, wrong error code returned.

LOW: Suboptimal but working. Degrades quality without breaking behavior.
     Fix before the phase completes.
     Example: Missing index on a queried column, deprecated API in use.

INFO: Observation worth recording. No action required.
      Example: Unused env var, style deviation with no behavioral impact.

Tie-breaking rule: When you are deciding between two levels, choose the LOWER one.
Tie-breaking question: "Would I personally halt a production deploy for this finding?"
  YES → critical or high
  NO  → medium, low, or info
```

Source: REVIEW-PIPELINE-DESIGN.md Section 2.3 (severity calibration); REQUIREMENTS.md REVR-05

### Pattern 6: Pure JSON Output Enforcement

**What:** The reviewer returns its findings as a JSON code block with no prose before or after it. The workflow parses this JSON directly.

**Why pure JSON:** REVR-06 requires reviewer output to parse cleanly as JSON. LLMs naturally wrap JSON in prose ("Here are my findings:"). The enforcement requires: (1) an explicit instruction that the ENTIRE response is a JSON code block, (2) a concrete example of the expected structure, and (3) a `<critical_rules>` guard that says "DO NOT write any text before or after the JSON block."

**Enforcement instruction:**
```
Your entire response MUST be a single JSON code block. No prose before it. No prose after it.
No "Here are my findings:" or "I reviewed the artifact and found:". Nothing.

Start your response with:
```json
and end with:
```

Source: REVIEW-PIPELINE-DESIGN.md Section 2.2 (structured machine-parseable output)

### Pattern 7: Single-Reviewer Spawning in spawn_reviewers Step

**What:** Phase 3 updates the `spawn_reviewers` placeholder in review-team.md to spawn exactly ONE reviewer — the first valid role found in TEAM.md during the `validate_team` step.

**When to use:** This is Phase 3's implementation of REVR-01 (but for a single reviewer, not parallel — Phase 4 adds parallelism).

**Implementation:**
1. Take the role names list from the `validate_team` step
2. Select the FIRST valid role (index 0)
3. Read the full section text for that role from TEAM.md
4. Construct the ARTIFACT_PATH from phase/plan variables (already computed in sanitize step)
5. Spawn Task() with gsd-reviewer, injecting the role section text via `<role_definition>` tags
6. Capture the reviewer's JSON return
7. Parse the JSON to extract findings array
8. Store findings for Phase 4 synthesis (in Phase 3, log findings and return)

**Phase 3 explicitly does NOT implement:** Parallel spawning (Phase 4), synthesis (Phase 4), routing (Phase 4). The spawn_reviewers step in Phase 3 spawns ONE reviewer and collects its structured JSON return. That's the full scope.

Source: Phase 3 requirements REVR-01, REVR-06; review-team.md Phase 3 placeholder; ROADMAP.md Phase 3 plan descriptions

### Anti-Patterns to Avoid

- **Hardcoding a role in gsd-reviewer.md:** The agent must be parameterized. Role content comes from the Task() prompt via `<role_definition>` tags, not from the agent file itself. (Violates REVR-06)
- **Prose-wrapped JSON:** Do not allow the reviewer to write "Here are my findings:" before the JSON block. The entire response must be the JSON code block. (Violates REVR-06 parseable output requirement)
- **Evidence-less findings:** A finding without a direct quote in `evidence` is a hallucination candidate. The `<critical_rules>` must make this a hard stop. (Violates REVR-03/REVR-04)
- **Scope bleed without suppression:** Without the `not_responsible_for` list AND the "suppress it, write only [OUT_OF_SCOPE]" instruction, reviewers will add off-domain findings. (Violates REVR-04)
- **Implementing parallel spawning in Phase 3:** Phase 4 handles parallelism. Phase 3 spawns exactly one reviewer. Adding parallel spawning here adds risk before the single-reviewer pattern is validated.
- **Inventing a role schema beyond TEAM.md:** The reviewer reads its role from the injected `<role_definition>` text — the same TEAM.md format established in Phase 1. Do not create a separate YAML schema for Phase 3.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON output validation | Runtime JSON parser in workflow | Instruction enforcement in agent + workflow existence check | No code runtime available in GSD workflows; enforcement is prompt-based |
| Role injection mechanism | Custom template engine | `<role_definition>` XML tags in Task() prompt + agent reads them | GSD pattern already established (GSD-AGENT-PATTERNS.md 6.2) |
| Domain isolation | Code that filters findings post-hoc | `not_responsible_for` list + [OUT_OF_SCOPE] instruction in agent | Prevention in prompt is more effective than post-hoc filtering |
| Severity enforcement | Post-processing severity adjuster | Rubric + tie-breaking rule embedded in agent | LLMs respond to explicit calibration instructions |
| Finding schema validation | JSON Schema validator | Required fields in example + "all fields required" instruction | No runtime JSON schema validation available; example-based enforcement works |
| TEAM.md role text extraction | YAML parser | String extraction from first `## Role:` section (reuse Phase 2 pattern) | TEAM.md uses minimal YAML in code blocks — regex extraction is sufficient and already established |

**Key insight:** Phase 3 produces two markdown files and one design schema document. There is no code to build, no libraries to import. The "standard stack" is GSD agent conventions plus the patterns documented in REVIEW-PIPELINE-DESIGN.md.

---

## Finding JSON Schema (03-01 Deliverable)

### The 7-Field Schema (REVR-02, REVR-06)

The requirements specify exactly: `{id, reviewer, domain, severity, evidence, description, suggested_routing}`.

```json
{
  "findings": [
    {
      "id": "SEC-001",
      "reviewer": "security-auditor",
      "domain": "security",
      "severity": "critical|high|medium|low|info",
      "evidence": "exact quote from ARTIFACT.md",
      "description": "What is wrong. Observable, specific.",
      "suggested_routing": "block_and_escalate|send_for_rework|send_to_debugger|log_and_continue"
    }
  ]
}
```

**Field-by-field rationale:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | YES | Format: `{ROLE_PREFIX}-{sequence}` e.g. `SEC-001`. Role prefix enables deduplication in Phase 4. Sequence is zero-padded 3 digits. |
| `reviewer` | string | YES | Role name from TEAM.md YAML `name:` field (e.g., `security-auditor`). Machine-readable, not display name. |
| `domain` | string | YES | Domain this reviewer owns (e.g., `security`, `correctness`, `performance`). From role `focus:` field. Enables Phase 4 synthesizer to detect scope bleed. |
| `severity` | string enum | YES | One of: `critical`, `high`, `medium`, `low`, `info`. Exact strings from REVR-05. |
| `evidence` | string | YES | Direct quote from ARTIFACT.md. NOT a description. NOT a paraphrase. The literal text string that grounds the finding. |
| `description` | string | YES | Observable issue. No speculation. No "might", "could", "probably". |
| `suggested_routing` | string enum | YES | One of the 4 routing destinations. Reviewer suggests; Phase 4 synthesizer/workflow enforces the minimum. |

### Empty Findings Case

When the reviewer has no findings in its domain:
```json
{
  "findings": []
}
```

This is a valid, expected output. The workflow must handle an empty findings array gracefully (log "Reviewer X: 0 findings" and continue).

### ID Generation Rule

The reviewer generates IDs sequentially within its response:
- Security Auditor role: `SEC-001`, `SEC-002`, `SEC-003`, ...
- Rules Lawyer role: `LAW-001`, `LAW-002`, ...
- Performance Analyst role: `PERF-001`, `PERF-002`, ...

The role prefix is derived from the role name. The reviewer must generate consistent IDs. In Phase 3 (single reviewer), ID collisions are impossible. In Phase 4 (parallel), each reviewer's prefix prevents collision.

**The reviewer agent must include a prefix derivation rule.** The simplest approach: first 3-4 uppercase characters of the role name. But edge cases exist (two roles starting with the same letters). The preferred approach: the role definition in TEAM.md should include the prefix, or the role name should be descriptive enough that the first 3-4 characters are unique across the 3 starter roles (SEC, LAW, PERF).

Source: REVIEW-PIPELINE-DESIGN.md Section 4.1 (finding ID design)

---

## Common Pitfalls

### Pitfall 1: Prose-Wrapped JSON (Most Likely Failure)

**What goes wrong:** The reviewer produces:
```
Based on my review of the artifact, here are the findings:

```json
{ "findings": [...] }
```

I noticed several issues in the security domain.
```

This is not parseable as raw JSON. The workflow's JSON collection step fails.

**Why it happens:** LLMs default to conversational framing. Without an explicit "your entire response IS the JSON block" instruction, they wrap it in prose.

**How to avoid:** The reviewer's `<output>` section must state: "Your ENTIRE response is a JSON code block. Nothing before it. Nothing after it." The `<critical_rules>` must add: "DO NOT write any text before or after the JSON block. No introduction. No conclusion. No summary."

**Warning signs:** Reviewer return contains the word "findings:" in plain text before a code fence, or any text after the closing code fence.

### Pitfall 2: Paraphrase Evidence Instead of Direct Quote

**What goes wrong:** The `evidence` field contains:
```json
"evidence": "The artifact mentions that JWT tokens are used without expiry settings"
```
instead of:
```json
"evidence": "JWT tokens use 15-minute expiry with 7-day refresh tokens"
```

**Why it happens:** The model paraphrases rather than quotes when it is summarizing or when the evidence is spread across multiple sentences.

**How to avoid:** The evidence instruction must say: "The `evidence` field MUST be a character-for-character quote from ARTIFACT.md. Copy-paste the exact text. Do not paraphrase, summarize, or describe it." The `<critical_rules>` guard should flag any evidence containing "the artifact mentions" or similar meta-language as invalid.

**Warning signs:** Evidence fields that describe the artifact's content rather than quoting it. Evidence fields using second-order language ("the code appears to", "this suggests").

### Pitfall 3: Domain Bleed Without Suppression

**What goes wrong:** The Security Auditor finds a performance issue and includes it in findings (as `SEC-003: Performance concern in database query`). The domain is wrong, the finding ID prefix is misleading, and Phase 4's synthesizer receives cross-domain findings from a single reviewer.

**Why it happens:** LLMs are generalists. Without the `not_responsible_for` list AND an explicit suppression instruction, the model includes whatever it notices.

**How to avoid:** Two defenses: (1) The `<role>` block must include the `not_responsible_for` list extracted from the TEAM.md role definition. (2) The instruction "if you notice something outside your domain, write ONLY: [OUT_OF_SCOPE] — do not include it in the findings array" gives the model a valid outlet that doesn't contaminate the JSON.

**Warning signs:** Findings where the implied type doesn't match the reviewer's declared domain. A Security Auditor finding that references "performance" or "code style."

### Pitfall 4: Severity Inflation

**What goes wrong:** Reviewer outputs 8 `critical` findings where a human reviewer would rate 2 `critical` and 6 `low`. Pipeline cries wolf. Users stop trusting it.

**Why it happens:** LLMs optimize for appearing thorough. Without a calibration anchor, "critical" means "I want this to be noticed" not "I would halt a production deploy."

**How to avoid:** The severity rubric must include concrete examples. The tie-breaking question ("would I personally halt a production deploy?") is empirically effective. The rubric should include an anti-inflation check: "Before finalizing, review each `critical` finding. If you would not personally halt a production deploy for it, downgrade to `high`."

**Warning signs:** >30% of findings rated `critical` or `high`. All findings in a single plan rated above `medium`.

### Pitfall 5: Role Definition Extraction Breaks on Edge Cases

**What goes wrong:** The `spawn_reviewers` step extracts the role definition text from TEAM.md but the extraction logic produces an incomplete or malformed `<role_definition>` block. The reviewer agent receives partial role content.

**Why it happens:** TEAM.md role sections end at the next `## Role:` header or at end-of-file. The extraction logic must handle both cases correctly.

**How to avoid:** The extraction algorithm from Phase 2 (`split on ## Role: headers`) already handles this. The full text of the first role section (from `## Role: {name}` to the next `## Role:` or EOF) is injected verbatim. The reviewer reads the entire section as its role definition.

**Warning signs:** Reviewer output references role criteria that don't match the TEAM.md role. Reviewer uses "none" or "unknown" as its domain.

### Pitfall 6: Empty Findings Treated as Error

**What goes wrong:** The workflow's JSON collection step receives `{"findings": []}` and treats it as a reviewer failure (parsing error or unexpected format).

**Why it happens:** The workflow implementation doesn't explicitly handle the empty case.

**How to avoid:** The spawn_reviewers step must explicitly check for empty findings array and log "Reviewer {name}: 0 findings" rather than failing. Zero findings is a valid outcome — the artifact may genuinely have no issues in a given domain.

**Warning signs:** Pipeline fails or produces an error when a reviewer finds no issues.

### Pitfall 7: Reviewer Reads PLAN.md or STATE.md

**What goes wrong:** The reviewer agent, trying to be thorough, uses the Read tool to read PLAN.md, STATE.md, or prior SUMMARY.md files. This breaks isolation and introduces anchoring bias.

**Why it happens:** The agent has the Read tool available and may try to gather "more context." Without an explicit prohibition, it will use available tools.

**How to avoid:** The `<critical_rules>` must include: "DO NOT use the Read tool to read any file other than ARTIFACT.md. You have one input. Reading other files breaks isolation and defeats the review pipeline design." The reviewer's role block must also state the information it explicitly does NOT have.

**Warning signs:** Reviewer findings reference details from PLAN.md that are not in ARTIFACT.md. Reviewer output contains references to the plan's "intent" or the executor's "goal."

---

## Code Examples

### Example 1: Full gsd-reviewer.md Structure

Source: GSD-AGENT-PATTERNS.md conventions + REVIEW-PIPELINE-DESIGN.md patterns + gsd-review-sanitizer.md as structural template

```markdown
---
name: gsd-reviewer
description: Reviews sanitized execution output against assigned role criteria. Returns structured findings as JSON. Spawned by review-team workflow.
tools: Read, Write
color: green
---

<role>
You are a GSD reviewer assigned the role: {role name from <role_definition>}.

Spawned by the review-team workflow. You run in a fresh, isolated context.

**What you have:**
- The sanitized artifact description (ARTIFACT.md) — your only input
- Your role definition (in <role_definition> tags below)

**What you do NOT have (by design):**
- The PLAN.md that produced this output
- The executor's raw SUMMARY.md
- Any prior phase summaries or reasoning chains
- Knowledge of what the executor "intended"
- Other reviewers' findings

**Your domain:** [read from <role_definition>]

**You are NOT responsible for:** [read from <role_definition> not_responsible_for list]

If you find yourself wanting to note something outside your domain, suppress it entirely.
Do not include it in your findings. Do not mention it.

Your job: Review ARTIFACT.md against your role's criteria. Return structured findings as JSON.

**Critical mindset:** Fresh eyes are your value. If you find yourself speculating about
intent or context you were not given, stop. Review only what is explicitly in the artifact.
</role>

<core_principle>
## Evidence Grounds Every Finding

You review a description of what was built, not the code itself. Your findings must be grounded
in what is explicitly written in the artifact. If you cannot quote the exact text that
demonstrates a finding, the finding does not exist.

"This type of code typically has X problem" is not a finding — it is a pattern match
against your training data. A finding requires: observable evidence in the artifact + your
domain expertise applied to that evidence.
</core_principle>

## Step 0: Load Role Definition

Read your role definition from the `<role_definition>` tags in your prompt. Extract:
- Role name (for the `reviewer` field in findings)
- Domain / focus area (for the `domain` field)
- What this role reviews (your review checklist)
- Severity thresholds for this role (from the role's severity thresholds section)
- not_responsible_for list (your domain exclusions)
- ID prefix (derive from role name: first 3-4 uppercase characters)
- Routing hints (for the `suggested_routing` field)

## Step 1: Read ARTIFACT.md

Use the Read tool to read ARTIFACT.md from the path provided in `<inputs>`.

DO NOT read any other file. Your review is limited to the artifact's contents.

Confirm the file exists and is non-empty before proceeding.

## Step 2: Apply Role Criteria

Work through each item in your role's "What this role reviews" checklist. For each item:

1. Look for relevant content in ARTIFACT.md (Files Changed, Behavior Implemented, Stack Changes, API Contracts, Configuration Changes, Key Decisions, Test Coverage, Error Handling)
2. Apply your domain expertise to what you observe
3. If you find an issue: verify you can quote specific text from ARTIFACT.md as evidence
4. If no direct quote exists: do NOT report the finding

## Step 3: Severity Assessment

For each candidate finding, assign severity using this rubric:

[EMBED SEVERITY RUBRIC — see Pattern 5 above]

## Step 4: Compile JSON Output

...

<output>
Your ENTIRE response is a single JSON code block. Nothing before it. Nothing after it.

```json
{
  "findings": [
    {
      "id": "{ROLE_PREFIX}-001",
      "reviewer": "{role name}",
      "domain": "{domain}",
      "severity": "critical|high|medium|low|info",
      "evidence": "exact quote from ARTIFACT.md",
      "description": "observable issue, no speculation",
      "suggested_routing": "block_and_escalate|send_for_rework|send_to_debugger|log_and_continue"
    }
  ]
}
```

If no findings: return `{"findings": []}` — this is a valid, expected output.

DO NOT commit.
</output>

<critical_rules>
1. DO NOT read any file except ARTIFACT.md. Reading PLAN.md, STATE.md, SUMMARY.md, or any other file breaks isolation.
2. DO NOT report a finding without a direct quote from ARTIFACT.md in the `evidence` field. Paraphrase is not evidence.
3. DO NOT include findings outside your declared domain. If you notice something off-domain, suppress it.
4. DO NOT write any text before or after the JSON code block. No introduction. No conclusion.
5. DO NOT use severity levels higher than the rubric warrants. When in doubt, go lower.
</critical_rules>

<success_criteria>
- [ ] Role definition loaded from <role_definition> tags
- [ ] ARTIFACT.md read from provided path (only file read)
- [ ] Every finding has a direct quote in the evidence field
- [ ] All findings are within the declared domain
- [ ] Severity assigned using the rubric with tie-breaking rule applied
- [ ] Output is a valid JSON code block with no prose before or after
- [ ] Empty findings array returned if no findings (not an error)
</success_criteria>
```

### Example 2: spawn_reviewers Step (Phase 3 Implementation)

Source: review-team.md spawn_reviewers placeholder + REVR-06 requirements + Pattern 7 above

```markdown
<step name="spawn_reviewers">
## Step 3: Spawn Reviewer (Phase 3 — Single Reviewer)

Phase 3 implements this step for exactly ONE reviewer — the first valid role from TEAM.md.

### Select First Valid Role

Use the valid roles list from the validate_team step. Take the first role:
```
first_role_name = roles_list[0]
```

Read `.planning/TEAM.md` again. Extract the full text of the section for `first_role_name`:
- Find the `## Role: {first_role_name}` header (case-insensitive match on the role name from YAML)
- Extract all text from that header to the next `## Role:` header (or end of file)
- This text is the `role_definition` to inject

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
    Artifact path: ${ARTIFACT_PATH}
    Phase: ${PHASE_ID}
    Plan: ${PLAN_NUM}
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

### Collect JSON Return

After the reviewer returns:
1. Parse the return as JSON
2. Extract the `findings` array
3. Log: `Reviewer {first_role_name}: {N} finding(s)`
4. If the findings array is empty: log "0 findings" and continue (not an error)
5. Log each finding's id, severity, and description for audit

Phase 3 stops here — Phase 4 adds synthesis and routing.
</step>
```

### Example 3: Finding JSON with Direct Quote Evidence

Source: REVIEW-PIPELINE-DESIGN.md Section 2.2 + requirements REVR-03, REVR-04

```json
{
  "findings": [
    {
      "id": "SEC-001",
      "reviewer": "security-auditor",
      "domain": "security",
      "severity": "high",
      "evidence": "JWT_SECRET | required env var | .env",
      "description": "JWT_SECRET stored in .env with no indication of secret rotation policy or minimum entropy requirement. Secret length and complexity are not validated.",
      "suggested_routing": "send_for_rework"
    },
    {
      "id": "SEC-002",
      "reviewer": "security-auditor",
      "domain": "security",
      "severity": "medium",
      "evidence": "Login endpoint accepts email + password, returns JWT token",
      "description": "No rate limiting mentioned on the login endpoint. Credential stuffing attacks are possible without rate limiting.",
      "suggested_routing": "send_for_rework"
    }
  ]
}
```

Note: Both `evidence` fields are verbatim text from a hypothetical ARTIFACT.md — not paraphrase.

### Example 4: Severity Rubric Embedded in Agent

Source: REVIEW-PIPELINE-DESIGN.md Section 2.3 + REVR-05 severity levels

```markdown
## Step 3: Severity Assessment

Assign severity from this rubric. Use your role's specific severity thresholds from
`<role_definition>` to calibrate these general definitions:

**CRITICAL:** Would cause data loss, security breach, or complete system failure in production.
  No reasonable person would ship code with this finding unresolved.
  Production deploy must halt.

**HIGH:** Incorrect behavior that would reach users or break core functionality.
  Fix required before shipping. Does not warrant halting a deploy if a workaround exists.

**MEDIUM:** Deviates from stated requirements or established patterns.
  Should fix before next plan executes. Acceptable risk for a hotfix deploy.

**LOW:** Suboptimal but working. Degrades quality without breaking behavior.
  Fix before the phase completes. Fine to ship with a tracking issue.

**INFO:** Observation worth recording. No action required.
  For awareness only.

**Tie-breaking rule:** When deciding between two levels, choose the LOWER one.
**Tie-breaking question:** "Would I personally halt a production deploy for this finding?"
  YES → critical or high
  NO  → medium, low, or info

**Anti-inflation check:** Review each `critical` finding before finalizing.
  If you would not personally stop a production deploy for it, downgrade to `high`.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Reviewer reads raw SUMMARY.md | Reviewer reads only sanitized ARTIFACT.md | Phase 2 | Eliminates anchoring bias |
| No finding schema | 7-field JSON schema with required evidence | Phase 3 | Structured, parseable, hallucination-resistant |
| Severity by feel | Severity rubric with tie-breaking rule | Phase 3 | Calibrated, inflation-resistant |
| Single agent serves one hardcoded role | Parameterized agent via role injection | Phase 3 | One agent file, all roles |
| spawn_reviewers placeholder | Single-reviewer spawn implemented | Phase 3 | Pipeline fires end-to-end for first time |

**Deferred to Phase 4:**
- Parallel multi-reviewer spawning (Phase 3 is single reviewer only)
- Synthesis and deduplication
- Deterministic routing (critical → block_and_escalate hardcoded in workflow code)
- REVIEW-REPORT.md population

---

## Open Questions

1. **Where should the `not_responsible_for` content come from in TEAM.md?**
   - What we know: The TEAM.md starter template (templates/TEAM.md) has `**Severity thresholds:**` and `**Routing hints:**` sections per role, but does NOT have a `not_responsible_for` section.
   - What's unclear: Should Plan 03-01 also define that a `not_responsible_for` list should be added to TEAM.md roles? Or should the reviewer agent derive the not_responsible_for list from the other roles in TEAM.md?
   - Recommendation: The reviewer agent derives the exclusion list from the role's `focus:` field — what the role IS responsible for implies what it is not. For the 3 starter roles (security/correctness/performance), the agent can construct: "not responsible for: performance, correctness" for the Security Auditor. This avoids requiring TEAM.md format changes in Phase 3. A formal `not_responsible_for:` field in TEAM.md can be added in Phase 5 when the role builder is built.
   - Alternative: The agent uses a generic not_responsible_for: "anything outside {focus domain}." Simpler, slightly less precise.

2. **How does the reviewer derive its ID prefix?**
   - What we know: The 3 starter roles have names: `security-auditor`, `rules-lawyer`, `performance-analyst`. Prefixes would be: `SEC`, `LAW`, `PERF`.
   - What's unclear: For user-defined roles, the prefix derivation needs to be deterministic and unique. The reviewer must know its prefix to generate IDs.
   - Recommendation: Derive prefix as first 3 uppercase characters of the role `name:` field from TEAM.md YAML. This is deterministic. The `<role_definition>` injection includes the YAML block, so the reviewer can read the `name:` field directly. In Phase 5 (role builder), a `prefix:` field can be added explicitly. For now, first-3-uppercase is sufficient.

3. **What does the workflow do with findings in Phase 3?**
   - What we know: Phase 4 adds synthesis and routing. Phase 3 collects findings from one reviewer.
   - What's unclear: Does Phase 3 log findings somewhere? Return them to the orchestrator? Write them to a file?
   - Recommendation: Phase 3 logs findings to the review-team.md return block (human-readable summary) but does NOT write REVIEW-REPORT.md (that's Phase 4's job). The spawn_reviewers step's return includes the raw findings JSON for audit. The return_status step includes a summary. No routing decisions are made — that's Phase 4.

4. **Should the finding schema be in a separate schema file or embedded in the agent?**
   - What we know: Plan 03-01 is "Finding JSON schema + severity rubric definition." This implies a schema document.
   - What's unclear: Is this a standalone file (like a SCHEMA.md) or just the design artifact captured in the plan?
   - Recommendation: Create a `schemas/finding-schema.md` file in the extension repo that documents the schema. This serves as (a) the 03-01 artifact, (b) reference for both gsd-reviewer.md and gsd-review-synthesizer.md, and (c) documentation for future contributors. The agent embeds a subset (the example JSON structure) inline.

---

## Sources

### Primary (HIGH confidence)

- `D:/GSDteams/.planning/research/REVIEW-PIPELINE-DESIGN.md` — Section 2 (reviewer prompt design, isolation, severity calibration, hallucination prevention), Section 4 (finding data structure), Section 5 (failure modes). This is the highest-trust source for Phase 3 design decisions.
- `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` — Section 5 (review agent conventions: gsd-reviewer frontmatter, role section, critical mindset), Section 6 (role injection via content tags, path-passing pattern)
- `D:/GSDteams/agents/gsd-review-sanitizer.md` — Phase 2 agent, directly observed structural template for gsd-reviewer.md (6-part convention applied to content-transform agents)
- `D:/GSDteams/workflows/review-team.md` — Phase 2 workflow with spawn_reviewers placeholder — Phase 3 implements this step
- `D:/GSDteams/templates/TEAM.md` — Actual TEAM.md format: role sections, YAML blocks, review criteria, severity thresholds, routing hints
- `D:/GSDteams/.planning/REQUIREMENTS.md` — REVR-01 through REVR-06 (exact requirement text)
- `D:/GSDteams/.planning/ROADMAP.md` — Phase 3 success criteria and plan descriptions
- `D:/GSDteams/.planning/STATE.md` — Prior architectural decisions (all Init + 01-xx + 02-xx decisions)
- `D:/GSDteams/.planning/phases/02-sanitizer-artifact-schema/02-RESEARCH.md` — Phase 2 research, patterns established, architectural context

### Secondary (MEDIUM confidence)

- `D:/GSDteams/.planning/PROJECT.md` — Architecture overview, routing destinations, pipeline design
- Phase 2 SUMMARY files (02-01, 02-02) — Confirmed decisions from actual Phase 2 execution

### Tertiary (LOW confidence)

- None — all findings verified against primary sources above

---

## Metadata

**Confidence breakdown:**

- Finding JSON schema: HIGH — derived directly from REVR-02/REVR-06 requirements + REVIEW-PIPELINE-DESIGN.md Section 4.1 (SARIF-inspired schema), scoped to the 7 required fields
- gsd-reviewer.md structure: HIGH — follows confirmed GSD 6-part convention (gsd-review-sanitizer.md as structural template) + REVIEW-PIPELINE-DESIGN.md isolation patterns
- Domain isolation mechanism: HIGH — `not_responsible_for` list pattern documented in REVIEW-PIPELINE-DESIGN.md Section 2.1, GSD-AGENT-PATTERNS.md Section 5.3
- Evidence enforcement: HIGH — evidence-first pattern in REVIEW-PIPELINE-DESIGN.md Section 2.4; directly maps to REVR-04
- Severity rubric: HIGH — REVIEW-PIPELINE-DESIGN.md Section 2.3; REVR-05 specifies exact severity level strings
- JSON output enforcement: HIGH — established LLM prompt engineering pattern; REVR-06 parseable output requirement
- spawn_reviewers step: HIGH — extends Phase 2 TEAM.md parsing pattern + GSD Task() invocation pattern
- not_responsible_for sourcing from TEAM.md: MEDIUM — TEAM.md starter template does not have an explicit `not_responsible_for` field; derivation approach is a recommendation

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (stable — no external dependencies)
