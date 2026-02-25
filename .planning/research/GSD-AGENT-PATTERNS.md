# GSD Agent Patterns Research

**Project:** GSD Review Team
**Researched:** 2026-02-25
**Sources:** gsd-verifier.md, gsd-executor.md, gsd-plan-checker.md, gsd-planner.md,
gsd-debugger.md, execute-phase.md, execute-plan.md, questioning.md
**GSD Version:** 1.19.2

---

## 1. Standard Structure of a GSD Agent File

Every GSD agent file is a YAML-frontmatted Markdown file that Claude Code loads as a
subagent type. The structure is consistent across all agents.

### 1.1 YAML Frontmatter (required, first block)

```yaml
---
name: gsd-{role}
description: One sentence. What it does, how it's triggered, what it produces.
tools: Read, Write, Bash, Grep, Glob   # only what the agent needs
color: green | yellow | orange         # green=quality gate, yellow=execution, orange=debug
---
```

**Observed tool sets by agent type:**

| Agent | Tools | Rationale |
|-------|-------|-----------|
| gsd-verifier | Read, Write, Bash, Grep, Glob | Needs to inspect codebase |
| gsd-plan-checker | Read, Bash, Glob, Grep | Read-only analysis |
| gsd-planner | Read, Write, Bash, Glob, Grep, WebFetch, mcp__context7__* | Creates files + needs research |
| gsd-executor | Read, Write, Edit, Bash, Grep, Glob | Full execution |
| gsd-debugger | Read, Write, Edit, Bash, Grep, Glob, WebSearch | Needs external research |
| gsd-phase-researcher | Read, Write, Bash, Glob, Grep, WebFetch | Research + file creation |

**Color convention:**
- `green` = quality-gate agents (plan-checker, verifier, integration-checker)
- `yellow` = execution agents (executor)
- `orange` = investigation/repair agents (debugger)

**Implication for Review Team:**
- gsd-review-sanitizer: `color: green`, tools: `Read, Write` (input transform, minimal)
- gsd-reviewer: `color: green`, tools: `Read, Write` (analysis only, no bash)
- gsd-review-synthesizer: `color: green`, tools: `Read, Write` (classification + routing decision)

### 1.2 `<role>` Section (required, immediately after frontmatter)

Every agent opens with a `<role>` block that answers four questions:

1. **What am I?** — one-sentence identity
2. **Who spawns me?** — named caller(s)
3. **What is my job?** — the one thing I'm responsible for
4. **What is my critical mindset?** — the philosophical constraint that prevents the most common failure

```xml
<role>
You are a GSD [role]. You [do X].

Spawned by `/gsd:[command]` orchestrator.

Your job: [the one outcome you must deliver].

**Critical mindset:** [The thing you must NOT do / must always remember.]
</role>
```

**Examples of critical mindset lines observed:**

- gsd-verifier: "Do NOT trust SUMMARY.md claims. SUMMARYs document what Claude SAID it did. You verify what ACTUALLY exists."
- gsd-plan-checker: "Plans describe intent. You verify they deliver."
- gsd-executor: "Execute the plan completely... report: plan name, tasks, SUMMARY path, commit hash"
- gsd-debugger: "Treat your code as foreign — Read it as if someone else wrote it"

### 1.3 `<core_principle>` or `<philosophy>` Section (common)

A named concept block that articulates the fundamental insight driving the agent's behavior.
Named consistently: `<core_principle>`, `<philosophy>`, or domain-specific (e.g., `<verification_process>`).

This is distinct from `<role>` — role is identity, principle is the intellectual framework.

### 1.4 Process / Verification Sections

The main body. Agents use two patterns:

**Pattern A: Named Steps (executor, execute-plan)**

```xml
<step name="load_context" priority="first">
...content...
</step>

<step name="execute_tasks">
...content...
</step>
```

Steps can have `priority="first"` to signal order. XML tags for step boundaries.

**Pattern B: Numbered Markdown Steps (verifier, plan-checker)**

```markdown
## Step 0: Check for Previous Verification
## Step 1: Load Context
## Step 2: Establish Must-Haves
...
## Step 9: Determine Overall Status
## Step 10: Structure Gap Output
```

Both patterns end in an output/returns section.

### 1.5 `<output>` or `<structured_returns>` Section (required)

Defines exactly what the agent writes (files) and what it says back (return format).
Always has two subsections:

1. **File creation** — what to Write, where, in what format (with full template)
2. **Return to orchestrator** — the exact text/markdown structure to return

### 1.6 `<critical_rules>` Section (common in quality-gate agents)

Bold, imperative statements. These are the "DO NOT" guards. Always at end, just before
success criteria.

### 1.7 `<success_criteria>` Section (always last)

A checkbox list (`- [ ] item`). This serves as:
- The agent's own completion checklist before returning
- The orchestrator's specification of what "done" means

---

## 2. How GSD Agents Communicate Status Back to the Orchestrator

### 2.1 Structured Markdown Return Blocks

Agents do NOT return free-form prose. They return structured Markdown that orchestrators
can parse predictably. The header line signals the outcome type.

**Pattern: Status-first header**

```markdown
## VERIFICATION PASSED
## VERIFICATION COMPLETE
## ISSUES FOUND
## RESEARCH COMPLETE
## RESEARCH BLOCKED
## Verification Complete
```

The status word comes first and is machine-scannable. Orchestrators grep for these headers.

### 2.2 The Standard Return Structure (observed in gsd-verifier)

```markdown
## Verification Complete

**Status:** {passed | gaps_found | human_needed}
**Score:** {N}/{M} must-haves verified
**Report:** .planning/phases/{phase_dir}/{phase_num}-VERIFICATION.md

{Conditional body based on status — each status gets its own prose block}
```

Three parts: **status line**, **location of artifact**, **conditional detail block**.

### 2.3 gsd-plan-checker Return Structure

Two named return blocks for the two outcome states:

```markdown
## VERIFICATION PASSED
**Phase:** {phase-name}
**Plans verified:** {N}
**Status:** All checks passed

### Coverage Summary
| Requirement | Plans | Status |
...

Plans verified. Run `/gsd:execute-phase {phase}` to proceed.
```

```markdown
## ISSUES FOUND
**Phase:** {phase-name}
**Plans checked:** {N}
**Issues:** {X} blocker(s), {Y} warning(s), {Z} info

### Blockers (must fix)
**1. [{dimension}] {description}**
- Plan: {plan}
- Fix: {fix_hint}

### Structured Issues
(YAML issues list...)

### Recommendation
{N} blocker(s) require revision. Returning to planner with feedback.
```

### 2.4 YAML Frontmatter in Output Files as Secondary Return Channel

Agents that create files embed machine-readable data in YAML frontmatter of those files.
The orchestrator reads the file's frontmatter rather than only parsing the agent's return text.

```yaml
---
phase: XX-name
verified: YYYY-MM-DDTHH:MM:SSZ
status: passed | gaps_found | human_needed
score: N/M must-haves verified
gaps:
  - truth: "..."
    status: failed
    reason: "..."
    artifacts:
      - path: "src/..."
        issue: "..."
    missing:
      - "..."
---
```

The orchestrator then reads this with:
```bash
grep "^status:" "$PHASE_DIR"/*-VERIFICATION.md | cut -d: -f2 | tr -d ' '
```

**This is the two-channel return pattern:** agent says the status, file contains the data.

### 2.5 Status Values Are Closed Enumerations

Every agent uses a fixed set of status strings. Never prose, never free text.

| Agent | Status Values |
|-------|--------------|
| gsd-verifier | `passed`, `gaps_found`, `human_needed` |
| gsd-plan-checker | `passed`, `issues_found` (+ severity: `blocker`, `warning`, `info`) |
| gsd-executor | checkpoint state via structured return |

Review agents must follow this — closed enum of routing decisions, not prose.

---

## 3. How gsd-verifier Structures Its Findings

### 3.1 The VERIFICATION.md Template

The verifier creates `.planning/phases/{phase_dir}/{phase_num}-VERIFICATION.md` using this structure:

**Frontmatter (machine-readable):**
```yaml
---
phase: XX-name
verified: YYYY-MM-DDTHH:MM:SSZ
status: passed | gaps_found | human_needed
score: N/M must-haves verified
re_verification:       # only if second pass
  previous_status: gaps_found
  gaps_closed: [...]
  gaps_remaining: []
  regressions: []
gaps:                  # only if status: gaps_found
  - truth: "..."
    status: failed | partial
    reason: "..."
    artifacts:
      - path: "..."
        issue: "..."
    missing:
      - "specific thing to add/fix"
human_verification:    # only if status: human_needed
  - test: "..."
    expected: "..."
    why_human: "..."
---
```

**Body (human-readable):**
```markdown
# Phase {X}: {Name} Verification Report

**Phase Goal:** ...
**Verified:** ...
**Status:** ...

## Goal Achievement

### Observable Truths
| # | Truth | Status | Evidence |
|---|-------|--------|----------|

### Required Artifacts
| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|

### Key Link Verification
| From | To | Via | Status | Details |

### Requirements Coverage
| Requirement | Status | Blocking Issue |

### Anti-Patterns Found
| File | Line | Pattern | Severity | Impact |

### Human Verification Required
{detailed items}

### Gaps Summary
{narrative}
```

### 3.2 Three-Level Artifact Verification

The verifier applies three levels to each artifact:

| Level | Check | Tool |
|-------|-------|------|
| Level 1 | File exists | gsd-tools verify artifacts |
| Level 2 | File is substantive (not stub) | min_lines check, pattern check |
| Level 3 | File is wired (imported + used) | grep imports, grep usage |

Final status matrix:
```
Exists + Substantive + Wired = VERIFIED
Exists + Substantive + not Wired = ORPHANED (warning)
Exists + not Substantive = STUB (failure)
not Exists = MISSING (failure)
```

### 3.3 Gap YAML Structure for Downstream Consumption

Gaps use a specific YAML format in frontmatter so `/gsd:plan-phase --gaps` can consume them:

```yaml
gaps:
  - truth: "Observable truth that failed"
    status: failed
    reason: "Brief explanation"
    artifacts:
      - path: "src/path/to/file.tsx"
        issue: "What's wrong"
    missing:
      - "Specific thing to add/fix"
```

Each gap maps to a `truth` (user-observable behavior), not an implementation detail. This
keeps gap-closure plans user-oriented, not code-oriented.

---

## 4. How gsd-plan-checker Structures Its Issues

### 4.1 Seven Verification Dimensions (Named)

Plan-checker organizes all findings under seven named dimensions:

1. `requirement_coverage` — does every requirement have a task?
2. `task_completeness` — does every task have Files/Action/Verify/Done?
3. `dependency_correctness` — valid, acyclic dependency graph?
4. `key_links_planned` — are artifacts wired together in plans?
5. `scope_sanity` — within context budget (2-3 tasks/plan max)?
6. `verification_derivation` — are must_haves user-observable?
7. `context_compliance` — do plans honor CONTEXT.md decisions?

### 4.2 Issue YAML Format

Each issue follows a consistent YAML structure:

```yaml
issue:
  plan: "16-01"               # which plan
  dimension: "task_completeness"  # which dimension
  severity: "blocker"         # blocker | warning | info
  description: "Task 2 missing <verify> element"
  task: 2                     # task number if applicable
  fix_hint: "Add verification command for build output"
```

**Severity definitions:**
- `blocker` — must fix before execution can proceed
- `warning` — should fix, execution may work but quality degrades
- `info` — suggestions, not blocking

### 4.3 Return Format Groups Issues by Severity

Issues are returned under `### Blockers (must fix)` and `### Warnings (should fix)` headers,
then also provided as raw YAML in a `### Structured Issues` section.

This dual format serves two audiences: human reading the return, and orchestrator parsing it.

---

## 5. Conventions for gsd-review-sanitizer, gsd-reviewer, gsd-review-synthesizer

### 5.1 Frontmatter Conventions

All three must follow the observed pattern exactly:

**gsd-review-sanitizer:**
```yaml
---
name: gsd-review-sanitizer
description: Strips executor reasoning from SUMMARY.md. Produces clean artifact description for reviewers. Spawned by review-team workflow.
tools: Read, Write
color: green
---
```

**gsd-reviewer:**
```yaml
---
name: gsd-reviewer
description: Reviews sanitized execution output against assigned role criteria. Returns structured findings. Spawned in parallel by review-team workflow.
tools: Read, Write
color: green
---
```

**gsd-review-synthesizer:**
```yaml
---
name: gsd-review-synthesizer
description: Classifies reviewer findings, determines routing (block_and_escalate, send_for_rework, send_to_debugger, log_and_continue). Spawned by review-team workflow.
tools: Read, Write
color: green
---
```

**Why `tools: Read, Write` only (no Bash)?**
These agents are content processors, not code inspectors. They receive structured text and
produce structured text. They do not need to inspect the codebase, run commands, or make
system calls. Bash access would expand attack surface without benefit.

### 5.2 Role Section Conventions

Each role block must name:
- What the agent is ("You are a GSD review sanitizer")
- Who spawns it ("Spawned by `review-team` workflow")
- What its single job is
- Its critical mindset (the failure mode it is built to prevent)

**Critical mindsets by agent:**

- **Sanitizer:** "Your job is to destroy reasoning, not summarize it. If in doubt, strip it out."
- **Reviewer:** "You received this artifact with no prior context. You have no access to the plan that produced it, the executor's reasoning, or any prior summaries. Review only what you can observe."
- **Synthesizer:** "You classify; you do not re-review. Trust the reviewer findings as given. Your job is routing decisions, not second-guessing the analysis."

### 5.3 Isolation Guarantee is a First-Class Constraint

The reviewer's role section must explicitly state the information it does NOT have:

```xml
<role>
You are a GSD reviewer assigned the role: {ROLE_NAME}.

Spawned by the review-team workflow in a fresh context.

**What you have:**
- The sanitized artifact description
- Your role definition from TEAM.md

**What you do NOT have (by design):**
- The PLAN.md that produced this output
- The executor's SUMMARY.md (raw)
- Any prior phase summaries or reasoning chains
- Knowledge of what the executor "intended"

Your job: Review the artifact against your role's criteria. Report findings.

**Critical mindset:** Fresh eyes are your value. If you find yourself speculating about
intent or assuming context you weren't given, you are drifting out of your lane.
</role>
```

### 5.4 Closed Routing Enum for Synthesizer

The synthesizer must use a closed enum for routing decisions, matching the PROJECT.md spec:

```
block_and_escalate   — Critical severity. Halt execution, surface to user.
send_for_rework      — Major severity. Create targeted fix task, re-execute.
send_to_debugger     — Bug outside current scope. Route to gsd-debugger.
log_and_continue     — Minor / informational. Append to REVIEW-REPORT.md, continue.
```

This matches the pattern of `passed | gaps_found | human_needed` in gsd-verifier — closed
set of machine-parseable strings, never free-form routing prose.

### 5.5 Output Files and Return Format

**gsd-review-sanitizer** produces one file and returns status:

File: `.planning/phases/{phase_dir}/SANITIZED-ARTIFACT.md` (or inline return)
Return:
```markdown
## SANITIZATION COMPLETE

**Source:** {path to SUMMARY.md}
**Artifact:** {path to sanitized output}
**Stripped:** {count} reasoning blocks removed
```

**gsd-reviewer** produces findings in a structured return (no file — synthesizer receives it):

```markdown
## REVIEW COMPLETE

**Role:** {role name from TEAM.md}
**Phase/Plan:** {identifier}

### Findings

| Severity | Finding | Criterion |
|----------|---------|-----------|
| critical | ... | ... |
| major    | ... | ... |
| minor    | ... | ... |

**Finding count:** {N} critical, {N} major, {N} minor
```

If no findings: `**Finding count:** 0 — No issues found.`

**gsd-review-synthesizer** produces two outputs:
1. Routing decision return (for orchestrator to act on)
2. REVIEW-REPORT.md append (for log_and_continue findings)

Return:
```markdown
## SYNTHESIS COMPLETE

**Routing decision:** {block_and_escalate | send_for_rework | send_to_debugger | log_and_continue}

### Critical Findings (block_and_escalate)
{findings, or "None"}

### Major Findings (send_for_rework)
{findings, or "None"}

### Logged Findings (log_and_continue)
{findings, or "None"}

**Report:** .planning/phases/{phase_dir}/REVIEW-REPORT.md
```

---

## 6. How Agents Handle `--include` and Context Injection

### 6.1 The `--include` Pattern via gsd-tools

Agents receive their context through two mechanisms:

**Mechanism 1: Init call with `--include` flag**

```bash
INIT=$(node ~/.claude/get-shit-done/bin/gsd-tools.cjs init execute-phase "${PHASE}" --include state,config)
```

The `--include` flag bundles file contents into the JSON response. The agent then extracts:

```bash
STATE_CONTENT=$(echo "$INIT" | jq -r '.state_content // empty')
CONFIG_CONTENT=$(echo "$INIT" | jq -r '.config_content // empty')
```

This avoids multiple Read calls and keeps context loading in one atomic operation.

**Mechanism 2: Orchestrator-injected content in Task() prompt**

The execute-phase orchestrator passes content directly in the Task() prompt:

```
Task(
  subagent_type="gsd-verifier",
  model="{verifier_model}",
  prompt="Verify phase {phase_number} goal achievement.
Phase directory: {phase_dir}
Phase goal: {goal from ROADMAP.md}
..."
)
```

Structured data (phase number, goal, file paths) is embedded directly in the prompt string.
The agent reads referenced files itself using the Read tool.

**Mechanism 3: `@`-reference in prompt for shared context files**

```
<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
@~/.claude/get-shit-done/references/checkpoints.md
</execution_context>
```

`@`-references tell Claude Code to automatically load those files into the agent's context.
Used for stable reference files (templates, conventions) that don't change per run.

### 6.2 Content Tags for Structured Injection

When orchestrators need to pass variable content to agents (e.g., role definition from
TEAM.md, sanitized artifact), the pattern is XML-like content tags in the prompt:

```
<role_definition>
{content of role from TEAM.md}
</role_definition>

<sanitized_artifact>
{output from sanitizer}
</sanitized_artifact>
```

The agent's process section references these tags: "Parse role from `<role_definition>` tags."

This is the pattern the review-team workflow should use when passing role context to
reviewer agents and passing sanitized artifact to both reviewers and synthesizer.

### 6.3 Pass Paths, Not Contents Where Possible

From execute-phase.md:

> "Pass paths only — executors read files themselves with their fresh 200k context.
> This keeps orchestrator context lean (~10-15%)."

For large content (sanitized artifact, multiple reviewer findings), prefer:
- Write to a file first
- Pass the file path in the prompt
- Let the agent Read the file

For small content (role definition, routing hints), inject directly into the prompt via tags.

---

## 7. What a Well-Formed Agent Return Looks Like

### 7.1 Properties of a Parseable Return

From studying all agents, a well-formed return has these properties:

**1. Status-first header** — The outcome type is the H2 header. Orchestrator greps for it.
```markdown
## VERIFICATION PASSED
## ISSUES FOUND
## RESEARCH COMPLETE
## SYNTHESIS COMPLETE
```

**2. Bold key-value pairs for scalar metadata** — The critical facts are bold labels.
```markdown
**Status:** gaps_found
**Score:** 3/5 must-haves verified
**Report:** .planning/phases/03-auth/03-VERIFICATION.md
```

**3. Conditional blocks with clear section headers** — Each outcome path has its own
Markdown section. Orchestrator reads the relevant section based on the status header.

**4. Tables for multi-item data** — Never bullet lists for tabular data.
```markdown
| Requirement | Plans | Status |
|-------------|-------|--------|
| User can log in | 01 | Covered |
```

**5. YAML for structured data meant for downstream consumption** — When the next agent or
command needs to parse the data programmatically, use a YAML code block:
```yaml
issues:
  - dimension: scope_sanity
    severity: blocker
    description: "..."
```

**6. Actionable closing line** — Ends with the command/action the user or orchestrator
should take next.
```markdown
Plans verified. Run `/gsd:execute-phase {phase}` to proceed.
```
or
```markdown
Structured gaps in VERIFICATION.md frontmatter for `/gsd:plan-phase --gaps`.
```

**7. DO NOT COMMIT instruction** — Every quality-gate agent explicitly ends its output
section with "DO NOT commit" because the orchestrator bundles artifacts.

### 7.2 What Parseable Returns Enable

The orchestrator in execute-phase.md reads the verifier's VERIFICATION.md frontmatter:

```bash
grep "^status:" "$PHASE_DIR"/*-VERIFICATION.md | cut -d: -f2 | tr -d ' '
```

Then routes:
```
passed → update_roadmap step
human_needed → present items for human testing
gaps_found → present gap summary, offer /gsd:plan-phase --gaps
```

The orchestrator's routing is a simple string-match against a closed enum. This only works
because agents return closed enums, not prose. "Everything looks good" vs "passed" — the
former cannot be parsed, the latter can.

### 7.3 The Two-Channel Return Pattern (Summary)

GSD agents use two output channels in combination:

| Channel | What it carries | How orchestrator reads it |
|---------|-----------------|--------------------------|
| Agent return text | Status + human summary | Grep for status header, read aloud to user |
| Written file frontmatter | Machine-readable data | `grep "^status:"`, `jq`, gsd-tools parse |

Review agents should follow this. The synthesizer's routing decision goes in the return
text (for the orchestrator to act on), and the REVIEW-REPORT.md carries the logged findings
(for persistence).

---

## 8. GSD Questioning Pattern (for /gsd:new-reviewer)

The `questioning.md` reference defines how GSD commands do guided conversations. Key
conventions for `/gsd:new-reviewer`:

### 8.1 AskUserQuestion for Structured Choices

GSD uses `AskUserQuestion` (a Claude Code built-in) with this schema:

```
AskUserQuestion(
  header: "Short label (≤12 chars — hard limit)",
  question: "The actual question",
  options: ["Option 1", "Option 2", "Let me explain"]  // 2-4 options max
)
```

Options should be interpretations of what the user might mean, not generic categories.
Always include an escape hatch: "Let me explain" or "Something else".

### 8.2 Philosophy: Thinking Partner, Not Interviewer

> "The user often has a fuzzy idea. Your job is to help them sharpen it. Ask questions that
> make them think 'oh, I hadn't considered that' or 'yes, that's exactly what I mean.'"

For `/gsd:new-reviewer`, this means:
- Don't lead with "What tools do you want this reviewer to check?" (interrogation)
- Lead with "What kind of problems have you seen slip through that this reviewer would catch?"
- Follow energy — if they say "I keep shipping insecure code", dig into that before moving to criteria

### 8.3 Context Checklist (background, not script)

Four things to establish before writing to TEAM.md:
1. What the reviewer's focus area is (concrete enough to explain to a stranger)
2. What specific things to look for (checklist items)
3. What counts as critical vs major vs minor for this role
4. How findings from this role should be routed

### 8.4 Decision Gate Pattern

```
AskUserQuestion(
  header: "Ready?",
  question: "I think I have enough to create this reviewer. Ready?",
  options: ["Create reviewer", "Keep refining", "Start over"]
)
```

Loop until "Create reviewer" — never write TEAM.md without explicit approval.

### 8.5 Anti-Patterns to Avoid

- Checklist walking — asking every domain question regardless of context
- Corporate speak — "What are your success criteria for this role?"
- Shallow acceptance — accepting "it checks security" without drilling into what that means
- Premature constraints — asking about severity thresholds before understanding what the role reviews

---

## 9. Key Patterns Summary

### The Six Structural Laws of GSD Agents

1. **Frontmatter declares identity** — `name`, `description`, `tools`, `color`. Color signals agent class.

2. **`<role>` names the caller and the job** — "Spawned by X. Your job: Y." No ambiguity about who owns this agent.

3. **Critical mindset names the core failure mode** — Not aspirational ("be accurate") but
   protective ("do NOT trust SUMMARY.md claims").

4. **Process sections are ordered and named** — Steps 0 through N, or `<step name="...">` tags.
   Numbering enables the orchestrator to route resumption ("Skip to Step 3").

5. **Returns use closed enums and status-first headers** — Machine-parseable by design, not
   by accident. The header IS the routing signal.

6. **Success criteria are checkboxes** — Both the agent's self-check and the orchestrator's
   acceptance criteria. The agent ticks them before returning.

### What Makes the Review Agents Different from Existing Agents

Existing GSD agents are all **codebase-aware** — they read files, run commands, check real
artifacts. The review agents are **output-aware** — they receive a description of what was
built and reason about it textually. This changes the tool set (no Bash needed) but the
structural conventions stay identical.

The key differentiation: reviewer agents are **context-isolated by design**. Existing agents
like gsd-verifier explicitly load ROADMAP.md, STATE.md, SUMMARY.md — they accumulate context.
Reviewer agents must NOT do this. Their isolation is the feature. This must be enforced in
the `<role>` section's "What you do NOT have" list and in `<critical_rules>`.

---

## 10. Files That Should Be Created for the Review Team

Based on the GSD agent conventions observed:

```
agents/
  gsd-review-sanitizer.md
    - tools: Read, Write
    - color: green
    - core job: strip reasoning from SUMMARY.md → SANITIZED-ARTIFACT.md
    - returns: SANITIZATION COMPLETE + path to artifact + strip count

  gsd-reviewer.md
    - tools: Read, Write
    - color: green
    - core job: review sanitized artifact against role criteria from TEAM.md
    - receives role via <role_definition> tag injection in prompt
    - returns: REVIEW COMPLETE + findings table (severity / finding / criterion)
    - critical mindset: no context beyond what was given — fresh eyes are the value

  gsd-review-synthesizer.md
    - tools: Read, Write
    - color: green
    - core job: classify findings, output routing decision (closed enum)
    - routing enum: block_and_escalate | send_for_rework | send_to_debugger | log_and_continue
    - returns: SYNTHESIS COMPLETE + routing decision + finding breakdown
    - writes: REVIEW-REPORT.md append for log_and_continue findings
    - critical mindset: classify, do not re-review

workflows/
  review-team.md
    - orchestrates sanitize → parallel review → synthesize
    - passes sanitized artifact path to reviewers via prompt injection
    - collects reviewer returns, passes to synthesizer
    - acts on synthesizer routing decision

  new-reviewer.md
    - uses questioning.md pattern
    - AskUserQuestion with ≤12-char headers
    - decision gate: "Create reviewer" | "Keep refining" | "Start over"
    - writes role block to .planning/TEAM.md

commands/gsd/
  new-reviewer.md
    - entry point for /gsd:new-reviewer
    - guards: check .planning/ exists, check TEAM.md exists or offer to create it
```

---

## Sources

- `get-shit-done-1.19.2/agents/gsd-verifier.md` — HIGH confidence (primary source)
- `get-shit-done-1.19.2/agents/gsd-executor.md` — HIGH confidence (primary source)
- `get-shit-done-1.19.2/agents/gsd-plan-checker.md` — HIGH confidence (primary source)
- `get-shit-done-1.19.2/agents/gsd-planner.md` — HIGH confidence (primary source, frontmatter)
- `get-shit-done-1.19.2/agents/gsd-debugger.md` — HIGH confidence (primary source, frontmatter + role)
- `get-shit-done-1.19.2/get-shit-done/workflows/execute-phase.md` — HIGH confidence (Task() invocation patterns)
- `get-shit-done-1.19.2/get-shit-done/workflows/execute-plan.md` — HIGH confidence (orchestrator conventions)
- `get-shit-done-1.19.2/get-shit-done/references/questioning.md` — HIGH confidence (primary source)
- `D:/GSDteams/.planning/PROJECT.md` — HIGH confidence (project spec, constraint reference)
