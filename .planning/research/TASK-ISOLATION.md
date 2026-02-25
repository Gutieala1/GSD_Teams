# Task() Isolation and Multi-Agent Patterns

**Project:** GSD Review Team
**Researched:** 2026-02-25
**Research mode:** Feasibility + Ecosystem
**Overall confidence:** MEDIUM (training data through August 2025; web access and Context7 were denied by environment permissions during this session — findings could not be verified against live documentation)

---

## Research Constraints

WebSearch, WebFetch, and Bash tools were denied by environment permissions during this session. All findings below are based on training data (August 2025 cutoff) plus direct analysis of the PROJECT.md specification. Confidence levels reflect this limitation.

**What this means for the roadmap:**
- Treat HIGH confidence findings as established behavior unlikely to have changed
- Treat MEDIUM findings as correct-direction but worth a spot-check during implementation
- Treat LOW findings as hypotheses that must be verified in a live environment before depending on them

---

## 1. Context Inheritance: What Does a Task() Subagent Receive?

**Confidence: HIGH** — This is fundamental SDK behavior documented in Anthropic's multi-agent guides and consistent across Claude Code releases.

### What IS inherited

A subagent spawned via `Task()` receives exactly what the parent explicitly constructs for it:

- **The `description` field** — the prompt the parent writes for the subagent. This is the primary input.
- **The `prompt` field** — inline task prompt text (used instead of or alongside description depending on API version).
- **Tool grants** — the parent controls which tools the subagent can use; ungranted tools are not available.
- **The system prompt of the subagent type** — when `subagent_type` is set, the corresponding agent's system prompt is loaded. This is the agent's role definition, not a copy of the parent's system prompt.

### What is NOT inherited

This is the core isolation guarantee:

| Item | Inherited? | Notes |
|------|-----------|-------|
| Parent's conversation history | NO | Subagent starts a fresh context window |
| Parent's in-memory reasoning | NO | Reasoning chains do not transfer |
| Parent's tool call results | NO | Unless explicitly copied into the prompt |
| Parent's system prompt | NO | Subagent gets its own type's system prompt |
| Files the parent read | NO | Unless parent passes content in the prompt |
| SUMMARY.md content | NO | Unless the parent reads it and embeds it |
| Prior subagent outputs | NO | Unless explicitly forwarded |
| Parent's working memory | NO | Each agent is a fully independent API call |

**Key insight for the GSD Review Team:** The isolation is real and automatic. A reviewer spawned via `Task()` cannot see the executor's reasoning. The concern is not "will the reviewer accidentally inherit executor bias?" — it won't. The concern is "did the parent inadvertently pass contaminating content in the prompt string?"

### The Contamination Risk

The only way a reviewer can be anchored is if the parent embeds executor reasoning into the prompt. This means the **Sanitizer** is the critical isolation gate, not the Task() call itself. Task() guarantees isolation of the context window; the Sanitizer guarantees isolation of the content passed in.

---

## 2. `subagent_type` — What It Controls

**Confidence: MEDIUM** — The mechanics are well established; specific named types beyond `claude-code` may have changed.

### How subagent_type works

`subagent_type` selects a pre-configured agent template that sets:
- The system prompt for the subagent
- Default tool access
- Behavioral constraints (scope of action, verbosity, etc.)

Common types in the Claude Code ecosystem:
- `claude-code` — general-purpose coding agent with full tool access
- No-value / default — bare model call with minimal system prompt

### Implications for reviewer agents

For the GSD Review Team, reviewer agents should:
1. Use a minimal subagent type (or a custom system prompt injected via the description field) that constrains the reviewer to analysis-only behavior
2. NOT be granted file-write tools, bash execution, or other action tools — reviewers should be read-only reasoning agents
3. Have their role definition (from TEAM.md) embedded in the prompt, not rely on a shared subagent_type file

**Recommended approach:**
```markdown
Task(
  description: """
  You are a [Role Name] reviewer. Your role:
  [role definition from TEAM.md]

  Review this artifact:
  [sanitized artifact from Sanitizer]

  Return a structured JSON verdict.
  """,
  subagent_type: "claude-code"  # or minimal type
)
```

The system prompt from subagent_type sets baseline behavior; the description field carries all role-specific context.

---

## 3. Ensuring Reviewers See ONLY Explicitly Passed Content

**Confidence: HIGH** — This is deterministic: Task() creates an isolated API call.

### The isolation model

Each `Task()` call is functionally a new Claude API request with:
- A fresh context window (no conversation history)
- Only the text you put in `description`/`prompt` as input
- No filesystem access to files the parent has read (unless the subagent is given filesystem tools and reads them independently)

### Design rules for guaranteed isolation

**Rule 1: The Sanitizer output is the only input.**
The orchestrator must pass ONLY the Sanitizer's output to reviewer Tasks. It must not pass:
- The original SUMMARY.md
- The plan text
- Prior reviewer findings
- Any reasoning about what the sanitizer removed

**Rule 2: Do not pass filenames that invite the reviewer to read files.**
If the reviewer has filesystem tools (Read, Glob), giving it a path like "here is the SUMMARY.md at `.planning/phases/01-setup/SUMMARY.md`" invites it to read raw file contents. Either:
- Strip filesystem tools from reviewers entirely (recommended), or
- Pass content inline without paths

**Rule 3: The orchestrator must not editorialize.**
"Here is the artifact. Note that the executor mentioned concerns about X." is contamination. The prompt should be mechanically constructed from the sanitized artifact — no orchestrator commentary.

**Rule 4: Role definitions must be statically defined.**
The reviewer's role (from TEAM.md) is safe to pass — it is authored before execution, not derived from the executor's reasoning. This is not contamination.

### Concrete construction pattern

```markdown
[Task() prompt construction]

SAFE:
- Sanitized artifact (Sanitizer output only)
- Role definition from TEAM.md (pre-authored, not derived from execution)
- Return format specification
- Severity threshold definitions

UNSAFE:
- Any content from SUMMARY.md before sanitization
- Orchestrator reasoning about the execution
- Other reviewers' findings (inter-reviewer contamination)
- File paths that point to execution artifacts
```

---

## 4. Parallel Task() Calls — True Parallelism and Ordering

**Confidence: MEDIUM** — Parallel execution is documented; exact scheduling semantics are less precisely specified.

### Do parallel Task() calls actually run in parallel?

**Yes, with important caveats.**

Claude Code's Task() tool is designed for concurrent execution. When the parent calls multiple Task() instances in a single response (i.e., the parent issues multiple tool calls in one turn), Claude Code initiates them concurrently. The parent then waits for all to complete before proceeding.

### How to request parallel execution

The parent must issue multiple Task() calls in the SAME model turn — not sequentially. The pattern looks like:

```
Parent turn:
  Task(reviewer_A_prompt)   ← issued simultaneously
  Task(reviewer_B_prompt)   ← issued simultaneously
  Task(reviewer_C_prompt)   ← issued simultaneously
```

If instead the parent issues one Task(), waits for the result, then issues the next — they run sequentially. Sequential is slower but sometimes necessary (e.g., when Task B needs Task A's output).

### Ordering guarantees

**There are no ordering guarantees.** Parallel Tasks may complete in any order depending on:
- API response times
- Token counts in each subagent's response
- Infrastructure scheduling

The synthesizer must be designed to collect all findings without assuming order. A natural pattern is: collect all reviewer outputs into a list, then synthesize the full list.

### The GSD Review Team architecture matches the parallel model correctly

The pipeline as documented in PROJECT.md is:
1. Sanitizer runs (sequential — its output feeds reviewers)
2. All reviewers run (parallel — independent, no shared state)
3. Synthesizer runs (sequential — needs all reviewer outputs)

This is the correct execution model. Steps 1 and 3 must be sequential gating steps around the parallel fan-out.

### Practical limit on parallel Tasks

**Confidence: LOW** — No firm number found in training data.

There is likely a practical limit on concurrent subagents, but the specific number is not documented in my training data. For the GSD Review Team use case (typically 2-6 reviewers), this is unlikely to be a concern. For safety, treat it as "up to ~10 concurrent Tasks are safe; beyond that, verify."

---

## 5. Task() Failure Handling

**Confidence: MEDIUM** — Error propagation behavior is partially documented; exact exception types require live testing.

### How failures surface

When a Task() subagent fails, the parent receives an error result rather than a normal return. The parent can:
1. Inspect the error and decide how to handle it
2. Retry the Task with modified parameters
3. Continue with partial results (if one reviewer fails, continue with others)
4. Escalate to the user

### Failure modes to design for

| Failure Mode | Cause | Recommended Handling |
|--------------|-------|---------------------|
| Task timeout | Subagent takes too long | Retry once with simpler prompt; on second failure, log and continue |
| Task error (model-side) | API error, rate limit | Retry with exponential backoff |
| Malformed output | Reviewer did not return expected JSON | Re-prompt once with stricter format instructions; on failure, log raw output |
| Empty output | Reviewer returned nothing | Treat as "no findings" with a note in the report |
| Task refused | Content policy triggered | Log and continue; surface to user if repeated |

### Recommended approach for the GSD Review Team

The Synthesizer should handle partial reviewer results gracefully. If reviewer B fails, the Synthesizer should:
- Note the failure in the REVIEW-REPORT.md
- Continue synthesizing findings from A and C
- Not block the pipeline on one reviewer failure

The orchestrator should implement a **collect-with-timeout** pattern: issue all reviewer Tasks, wait for all to resolve (success or failure), then pass the full result set (including errors) to the Synthesizer.

---

## 6. Agent Return Values — What Can a Task() Return?

**Confidence: MEDIUM** — Return value mechanics are established; specific size limits require live verification.

### What a Task() can return

A Task() subagent returns whatever text it produces as its final output. This is:
- The text of the agent's final response turn
- Everything after its last tool call (if it used tools)
- Structured or unstructured — the parent receives raw text

There is no native "return value type" — everything comes back as a string. The parent must parse structured data out of that string.

### Practical return size

**Confidence: LOW** — Specific limits not found in training data.

The return value is bounded by the subagent's output token limit, which is a model-level constraint (typically 4K-8K output tokens for standard Claude models). For a structured review verdict with findings, this is more than sufficient.

Avoid designing reviewer output that requires exhaustive verbosity. A reviewer should return:
- Structured findings (JSON or markdown table)
- Severity ratings
- Specific locations (file/line if applicable)
- One-sentence justification per finding

This easily fits in 1K-2K tokens, well within limits.

### Recommended return format

For reliable parsing by the Synthesizer, reviewers should return JSON:

```json
{
  "reviewer": "Security Auditor",
  "verdict": "findings",
  "findings": [
    {
      "severity": "major",
      "category": "authentication",
      "description": "JWT tokens stored in localStorage expose them to XSS",
      "location": "src/auth/token-storage.ts",
      "routing_hint": "send_for_rework"
    }
  ],
  "summary": "One critical and one major finding. Execution should not proceed."
}
```

Or if clean:
```json
{
  "reviewer": "Security Auditor",
  "verdict": "clean",
  "findings": [],
  "summary": "No security issues found."
}
```

---

## 7. Patterns for Structured Verdict/Findings

**Confidence: HIGH** — These are general multi-agent design patterns well established in the literature and in Claude Code usage.

### Pattern 1: JSON-first return contract

Define the return schema in the reviewer's prompt. Be explicit about required fields. Example:

```markdown
Return your findings as JSON with this exact structure:
{
  "reviewer": "[your role name]",
  "verdict": "clean" | "findings" | "critical",
  "findings": [
    {
      "severity": "critical" | "major" | "minor",
      "description": "...",
      "routing_hint": "block_and_escalate" | "send_for_rework" | "send_to_debugger" | "log_and_continue"
    }
  ],
  "summary": "One sentence summary for the report"
}

Return ONLY the JSON. No preamble. No explanation outside the JSON.
```

The "return ONLY the JSON" instruction significantly improves parse reliability.

### Pattern 2: Verdict-first design

Use a top-level `verdict` field that the Synthesizer can check before parsing `findings`. This allows fast routing:
- `"clean"` → log_and_continue immediately
- `"findings"` → examine individual findings for routing
- `"critical"` → block_and_escalate immediately

This avoids the Synthesizer needing to iterate all findings just to determine the overall severity.

### Pattern 3: Synthesizer as a structured merge tool

The Synthesizer should not re-evaluate the findings — it should aggregate and route them. Its job:
1. Collect all reviewer JSON outputs
2. Identify the highest-severity verdict across all reviewers
3. Apply routing rules (per TEAM.md routing hints, per finding severity)
4. Output a merged routing decision and REVIEW-REPORT.md row

The Synthesizer should be a deterministic router, not a reasoning agent. Give it explicit routing rules in its prompt so its behavior is predictable.

### Pattern 4: Fail-safe return format

The reviewer prompt should specify what to return on uncertainty:
```markdown
If you are uncertain whether a finding is critical or major, classify it as major.
If you find nothing to report, return a clean verdict — do not invent findings.
If you cannot parse the artifact, return:
{"reviewer": "[name]", "verdict": "error", "findings": [], "summary": "Could not parse artifact."}
```

This prevents the Synthesizer from receiving malformed output that crashes the pipeline.

### Pattern 5: Role-binding in the prompt

Because subagent isolation is complete, the reviewer has no idea who it is unless you tell it. Open your reviewer prompt with an unambiguous role declaration:

```markdown
You are a [Role Name]. Your sole job is to review the artifact below from the perspective of [domain].
You are NOT the executor. You did NOT create this artifact. Your job is to find problems, not justify decisions.

Your review criteria:
[checklist from TEAM.md]

Severity thresholds:
- Critical: [definition]
- Major: [definition]
- Minor: [definition]
```

The "You are NOT the executor" framing actively counteracts sycophancy toward the artifact.

---

## 8. Critical Isolation Anti-Patterns for GSD Review Team

### Anti-Pattern 1: Passing SUMMARY.md directly to reviewers

```
[WRONG]
Task(description: f"Review this summary: {read(SUMMARY.md)}")
```

SUMMARY.md contains executor reasoning. Pass only the Sanitizer's output.

### Anti-Pattern 2: Including the plan in the reviewer prompt

```
[WRONG]
Task(description: f"The plan was: {plan_text}. The execution produced: {sanitized_artifact}")
```

Including the plan gives the reviewer context about what the executor intended, anchoring their review toward validating intent rather than evaluating outcome.

### Anti-Pattern 3: Passing prior reviewer findings to later reviewers

```
[WRONG]
reviewer_a_result = Task(reviewer_a_prompt)
reviewer_b_prompt = f"Reviewer A found: {reviewer_a_result}. Now you review..."
Task(reviewer_b_prompt)
```

This creates a cascade where B is influenced by A. Run all reviewers in parallel with no cross-visibility.

### Anti-Pattern 4: Orchestrator commentary in the prompt

```
[WRONG]
Task(description: f"The executor seemed uncertain about the auth approach. Review this: {artifact}")
```

Any orchestrator editorializing leaks executor context. The prompt should be mechanically assembled.

### Anti-Pattern 5: Giving reviewers write-tool access

If reviewers have `Write`, `Edit`, or `Bash` access, they might modify files during review, creating side effects. Reviewers should be analysis-only: `Read` (if needed for specific lookups), no write tools.

---

## 9. Implementation Architecture Recommendations

### Sanitizer → clean boundary

The Sanitizer is a subagent (or direct call) that:
1. Receives SUMMARY.md content
2. Applies stripping rules (defined in PROJECT.md)
3. Returns ONLY the clean artifact text

The clean artifact is then stored as a variable in the orchestrator — never written to disk before reviewer distribution (writing to disk and then having reviewers read the file would work, but creates coupling and a potential injection point).

### Orchestrator structure for the review pipeline

```
[Orchestrator]
1. Read SUMMARY.md → pass to Sanitizer Task
2. Receive clean artifact from Sanitizer
3. Read TEAM.md → extract reviewer role definitions
4. For each reviewer role:
   - Construct prompt: role_definition + clean_artifact + return_format_spec
   - No cross-reviewer content
5. Issue ALL reviewer Tasks in one turn (parallel)
6. Collect all results (success + failure)
7. Pass full result set to Synthesizer Task
8. Receive routing decision from Synthesizer
9. Execute routing actions
```

### Synthesizer receives a collection, not a stream

The Synthesizer's prompt:
```markdown
You are a review synthesizer. Your job is to classify and route findings.

Routing rules:
- "critical" verdict from ANY reviewer → block_and_escalate
- "major" severity in findings → send_for_rework (unless routing_hint overrides)
- ...

Reviewer findings:
[JSON array of all reviewer outputs]

Return a routing decision as JSON:
{
  "overall_verdict": "clean" | "findings" | "critical",
  "routing": "block_and_escalate" | "send_for_rework" | "send_to_debugger" | "log_and_continue",
  "report_rows": [...],
  "rationale": "..."
}
```

---

## 10. Summary: What This Means for GSD Review Team Design

| Design Decision | Recommendation | Confidence |
|----------------|---------------|-----------|
| Isolation model | Task() isolation is complete — reviewers cannot inherit executor context unless you put it in the prompt | HIGH |
| Contamination prevention | Sanitizer is the critical gate; Task() itself guarantees context window isolation | HIGH |
| Parallel execution | Issue all reviewer Tasks in a single parent turn for true parallelism | MEDIUM |
| Return format | JSON with explicit schema in the prompt; "return ONLY JSON" instruction | HIGH |
| Failure handling | Collect all results including errors; Synthesizer handles partial sets | MEDIUM |
| Tool access for reviewers | No write tools; no bash; optionally no file-read tools at all | HIGH |
| Role definition | Embed full role from TEAM.md in the prompt; do not rely on subagent_type for role | HIGH |
| Anti-anchoring framing | Explicit "You are NOT the executor" in reviewer system prompt | MEDIUM |
| Synthesizer role | Deterministic router with explicit rules, not a reasoning agent | HIGH |
| Return size limits | Reviewer output well under 2K tokens; no risk at typical finding volumes | MEDIUM |

---

## 11. Open Questions Requiring Live Verification

These could not be answered without web access:

1. **Does `subagent_type` support custom values?** Can you define a named reviewer type, or must role context always travel in the prompt? (Current assumption: role travels in prompt — safe regardless of answer)

2. **What is the exact concurrent Task() limit?** Training data does not specify. Verify before designing systems with >10 parallel reviewers.

3. **Is there a maximum prompt size for Task()?** If a sanitized artifact is very large, can it be passed entirely in the description field? What happens at the token limit?

4. **Does the parent receive partial output on Task() timeout?** Or is it all-or-nothing? This affects how the failure handler should be designed.

5. **Are Task() calls truly async or is there a synchronization overhead** that makes sequential calls only marginally slower than parallel for small counts (2-4 reviewers)?

6. **What is the current recommended pattern** for injecting a custom system prompt into a Task() call? Can the description field override the subagent_type's system prompt, or do they concatenate?

---

## Sources

**Note:** No external sources were accessible in this session. All findings are derived from:

- Training data through August 2025 (Anthropic Claude Code documentation, multi-agent design guides, Claude Code SDK release documentation)
- Direct analysis of `/d/GSDteams/.planning/PROJECT.md`

For live verification, consult:
- `https://docs.anthropic.com/en/docs/claude-code/sdk` — Task() API reference
- `https://docs.anthropic.com/en/docs/build-with-claude/agents` — Multi-agent patterns
- `https://github.com/anthropics/claude-code` — SDK source and changelog
- Context7 library lookup: `@anthropic-ai/claude-code` or `claude-code-sdk`
