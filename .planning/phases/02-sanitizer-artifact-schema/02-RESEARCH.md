# Phase 2: Sanitizer + Artifact Schema - Research

**Researched:** 2026-02-25
**Domain:** GSD agent design (sanitizer), ARTIFACT.md schema, TEAM.md validation, review-team.md workflow skeleton
**Confidence:** HIGH

## Summary

Phase 2 builds two files that bring the review pipeline from "wired but empty" to "sanitizer runs and produces artifacts." The `review_team_gate` step (Phase 1) already references `@~/.claude/get-shit-done-review-team/workflows/review-team.md` -- Phase 2 creates what lives at that path plus the sanitizer agent it spawns.

The sanitizer is the real isolation gate. Task() guarantees context window isolation automatically, but the sanitizer controls what *content* enters that window. Every downstream component (reviewers, synthesizer) depends on the sanitizer's output being clean. This makes the sanitizer the highest-stakes agent in the pipeline, and it must be built with both completeness checks (don't over-strip) and contamination guards (don't under-strip).

The review-team.md workflow is a skeleton in Phase 2 -- it validates TEAM.md, spawns the sanitizer, and writes ARTIFACT.md to disk. Reviewer spawning (Phase 3) and synthesis (Phase 4) are added later. The skeleton must be designed with those future steps in mind but must not implement them.

**Primary recommendation:** Write ARTIFACT.md to disk (not passed inline). The artifact is the audit trail, and reviewers in Phase 3 will read it by path. The sanitizer agent follows exact GSD agent conventions (frontmatter, `<role>`, process steps, `<output>`, `<critical_rules>`, `<success_criteria>`). The workflow skeleton uses `## Role:` header splitting to parse TEAM.md and validates at least one role exists before proceeding.

---

## Standard Stack

### Core

| Component | Type | Purpose | Why Standard |
|-----------|------|---------|--------------|
| `gsd-review-sanitizer.md` | GSD agent | Strips reasoning from SUMMARY.md, produces ARTIFACT.md | Core isolation gate for the review pipeline |
| `review-team.md` | GSD workflow | Orchestrates sanitize step, validates TEAM.md | Pipeline controller loaded by review_team_gate |

### Supporting

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| Read tool | built-in | Sanitizer reads SUMMARY.md | Always -- input acquisition |
| Write tool | built-in | Sanitizer writes ARTIFACT.md to disk | Always -- output persistence |
| `## Role:` split pattern | regex | TEAM.md role extraction | Workflow TEAM.md validation |
| YAML code block extraction | regex | Role name/focus from TEAM.md | Workflow role enumeration |

### No External Dependencies

Phase 2 requires zero external libraries. Both files are pure GSD markdown agents/workflows. The only tools needed are Read and Write (built into Claude Code).

---

## Architecture Patterns

### Recommended File Layout (Phase 2 additions)

```
get-shit-done-review-team/
  agents/
    gsd-review-sanitizer.md       # Plan 02-01 -- THIS PHASE
  workflows/
    review-team.md                # Plan 02-02 -- THIS PHASE
```

After install, these land at:
- `~/.claude/get-shit-done-review-team/agents/gsd-review-sanitizer.md`
- `~/.claude/get-shit-done-review-team/workflows/review-team.md`

### Pattern 1: GSD Agent Structure (6-Part Convention)

**What:** Every GSD agent follows a strict 6-part structure. The sanitizer must conform exactly.
**When to use:** Always -- this is not optional.

Source: `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md`

```
1. YAML frontmatter (name, description, tools, color)
2. <role> section (identity, spawner, job, critical mindset)
3. <core_principle> or <philosophy> section (intellectual framework)
4. Process sections (ordered steps with XML or markdown headers)
5. <output> section (file creation + return format)
6. <critical_rules> + <success_criteria> (DO NOT guards + completion checklist)
```

**Sanitizer frontmatter:**
```yaml
---
name: gsd-review-sanitizer
description: Strips executor reasoning from SUMMARY.md. Produces clean artifact description for reviewers. Spawned by review-team workflow.
tools: Read, Write
color: green
---
```

**Rationale for `tools: Read, Write` only:** The sanitizer is a content transformer. It reads one file (SUMMARY.md), processes text, and writes one file (ARTIFACT.md). It does not need Bash, Grep, Glob, or any other tool. Minimal tool surface is a security practice -- it limits what a misbehaving agent can do.

### Pattern 2: Sanitizer Strip/Preserve Schema

**What:** Explicit enumeration of what to strip and what to preserve. This is the sanitizer's core logic.
**When to use:** The sanitizer's process section must contain both lists verbatim as DO NOT and MUST PRESERVE guards.

Source: `D:/GSDteams/.planning/research/REVIEW-PIPELINE-DESIGN.md` Section 1.1

**Strip (reasoning/bias sources):**

| Element | Why Strip |
|---------|-----------|
| "I decided to...", "I chose...", "I considered..." | Anchors reviewer to executor's framing |
| Alternatives considered and rejected | Primes reviewer against alternatives |
| Step-by-step execution narration | Gives reviewer a narrative that explains away issues |
| Confidence language ("This should work because...") | Transmits false certainty |
| References to prior plans or summaries | Creates cross-plan anchoring |
| Hedging/uncertainty language | Primes reviewer to focus only on known-uncertain areas |
| Internal commentary on trade-offs | Frames trade-offs as resolved |
| Rationale for decisions (the "why") | Anchors reviewer to executor's reasoning |

**Preserve (observable facts):**

| Element | Why Preserve |
|---------|-------------|
| Files created or modified (exact paths) | Scope definition |
| Behavior implemented (what it does) | Subject matter for review |
| Technology/libraries added | Security/compatibility surface |
| API contracts exposed or consumed | Interface review |
| Configuration changes, env vars | Security, ops surface |
| Key decisions (the "what", not the "why") | Reviewers need to know what was decided |
| Stack changes (dependencies added/removed) | Dependency review |

### Pattern 3: ARTIFACT.md Structured Output Schema

**What:** The sanitizer outputs a structured document with named sections, not free-form prose.
**When to use:** Always -- the structured sections make reviewer prompts more targeted.

```markdown
# Artifact: Phase {X} Plan {Y} - {Plan Name}

**Phase:** {phase identifier}
**Plan:** {plan number}
**Generated:** {timestamp}

## Files Changed

| Path | Action | Purpose |
|------|--------|---------|
| `src/auth/login.ts` | Created | Login endpoint |
| `prisma/schema.prisma` | Modified | Added Session model |

## Behavior Implemented

- [What the code does, stated as observable behavior]
- [No reasoning about why -- just what]

## Stack Changes

| Dependency | Version | Purpose |
|------------|---------|---------|
| jose | ^5.2.0 | JWT token handling |

## API Contracts

### [Endpoint/Interface Name]
- Method: POST
- Path: /api/auth/login
- Request: { email: string, password: string }
- Response: { token: string, refreshToken: string }

## Configuration Changes

| Config | Value | Location |
|--------|-------|----------|
| JWT_SECRET | required env var | .env |

## Key Decisions

- [Decision stated as fact: "JWT tokens use 15-minute expiry"]
- [No reasoning: NOT "We chose 15 minutes because..."]

## Test Coverage

- [What is tested]
- [What is NOT tested]

## Error Handling

- [How failures are handled, stated as behavior]
```

**Design rationale:** Named sections allow Phase 3 reviewers to focus on their domain. A Security Auditor reads Configuration Changes and API Contracts; a Performance Analyst reads Behavior Implemented and Stack Changes. The structured format also makes the sanitizer's completeness verifiable -- if a section is empty, the sanitizer may have over-stripped.

### Pattern 4: TEAM.md Parsing Pattern

**What:** The workflow extracts roles by splitting TEAM.md on `## Role:` headers and extracting YAML blocks.
**When to use:** In review-team.md validation step.

Source: Phase 1 decisions (01-01-SUMMARY.md)

```
Parsing algorithm:
1. Read .planning/TEAM.md
2. Split content on `## Role:` headers
3. For each section after split:
   a. Extract the role name from the YAML code block (```yaml ... name: {value} ... ```)
   b. Extract the focus from the YAML code block
   c. The full section content IS the role definition
4. Count roles found
5. If count == 0: halt with error
6. If count >= 1: proceed with sanitization
```

The `## Role:` header is the machine-parseable split anchor established in Phase 1 (01-01-SUMMARY.md key decision).

### Pattern 5: Workflow Step Structure

**What:** GSD workflows use `<step name="...">` XML blocks for ordered processing.
**When to use:** review-team.md must follow this convention.

Source: `C:/Users/gutie/.claude/get-shit-done/workflows/execute-plan.md`

```xml
<step name="validate_team" priority="first">
[Content]
</step>

<step name="sanitize">
[Content]
</step>

<step name="spawn_reviewers">
[Content - Phase 3 adds this]
</step>
```

### Anti-Patterns to Avoid

- **Passing SUMMARY.md to reviewers:** The sanitizer exists to prevent this. Never pass raw SUMMARY.md content past the sanitization step. (SAND-04)
- **Free-form artifact output:** Without structured sections, the sanitizer may produce inconsistent output. Use the named-section schema always.
- **Over-stripping:** The sanitizer must have a completeness check step. "Did my output contain all file paths from the input?" is the minimum.
- **Under-stripping:** The sanitizer must scan for reasoning language markers. A single "I decided to" that leaks through contaminates the entire review.
- **Inline artifact passing:** Write ARTIFACT.md to disk. This creates an audit trail (SAND-03), enables Phase 3 reviewers to Read it from a path (avoiding bloated prompts), and makes the pipeline debuggable.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing in TEAM.md | Custom YAML parser | Regex extraction of `name:` and `focus:` from fenced code blocks | TEAM.md uses minimal YAML in code blocks -- full YAML parsing is overkill and fragile |
| Reasoning language detection | Pattern-matching regex engine | Explicit strip list in the sanitizer prompt + LLM judgment | The sanitizer IS an LLM agent -- it uses judgment to identify reasoning, not regex |
| ARTIFACT.md schema validation | JSON schema validator | Structured sections as markdown headers in the agent prompt | ARTIFACT.md is markdown, not JSON. Validation is "does each section have content?" |
| Workflow orchestration framework | Custom state machine | GSD's `<step>` block pattern + sequential execution | GSD workflows are already state machines via ordered steps |

**Key insight:** Phase 2 produces two markdown files. There is no code to build, no libraries to import, no runtime to configure. The "standard stack" is the GSD agent/workflow conventions documented in GSD-AGENT-PATTERNS.md. Following those conventions IS the implementation.

---

## Common Pitfalls

### Pitfall 1: Over-Sanitization (Stripping Facts Along with Reasoning)

**What goes wrong:** The sanitizer is too aggressive and removes factual content along with reasoning. A sentence like "Added bcrypt for password hashing to prevent plaintext storage" gets fully stripped because it contains reasoning ("to prevent plaintext storage"), but the fact ("Added bcrypt for password hashing") should be preserved.
**Why it happens:** The instruction "strip reasoning" is applied to entire sentences instead of clauses. The LLM removes the whole sentence rather than extracting the factual core.
**How to avoid:** The sanitizer prompt must include a two-step process: (1) Extract the fact from the sentence. (2) Remove the reasoning clause. "Added bcrypt for password hashing to prevent plaintext storage" becomes "Added bcrypt for password hashing." The sanitizer should preserve the factual prefix even when the reasoning suffix is stripped.
**Warning signs:** ARTIFACT.md has fewer file paths than the input SUMMARY.md. ARTIFACT.md has empty sections. Behavior section is thin relative to what was built.

### Pitfall 2: Under-Sanitization (Reasoning Language Slipping Through)

**What goes wrong:** Subtle reasoning language passes through the sanitizer. "The team chose a 15-minute token expiry" looks factual but contains "chose" (a reasoning verb). "This approach handles edge cases well" is evaluative, not factual.
**Why it happens:** Reasoning language exists on a spectrum from obvious ("I decided") to subtle ("this handles X well"). The sanitizer must catch the subtle end too.
**How to avoid:** The sanitizer's strip list must include: first-person reasoning verbs (decided, chose, considered, evaluated, opted), confidence/quality language (should work, handles well, robust, elegant), comparative language (better than, preferred over, instead of), and uncertainty hedges (probably, likely, might, hopefully).
**Warning signs:** ARTIFACT.md contains any of: "I", "we", "chose", "decided", "because", "alternatively", "considered", "should", "better", "elegant", "robust".

### Pitfall 3: TEAM.md Validation Misses Edge Cases

**What goes wrong:** TEAM.md exists and has `## Role:` headers, but the roles are structurally invalid (no YAML block, no criteria list). The workflow proceeds to sanitization and then Phase 3 reviewer spawning fails because role definitions are incomplete.
**Why it happens:** Validation only checks role count, not role structure.
**How to avoid:** Validation must check three things: (1) At least one `## Role:` section exists. (2) Each role section contains a YAML code block with a `name:` field. (3) Each role section contains at least one `**What this role reviews:**` item. If any check fails: halt with specific error message naming the failing role.
**Warning signs:** Pipeline crashes in Phase 3 reviewer spawning with "no role definition found."

### Pitfall 4: ARTIFACT.md Written to Wrong Location

**What goes wrong:** ARTIFACT.md is written to the extension directory or the wrong phase directory. Reviewers cannot find it.
**Why it happens:** The file path construction is wrong. Phase directories have a specific naming convention: `.planning/phases/XX-name/`.
**How to avoid:** The workflow passes the exact ARTIFACT.md path to the sanitizer: `.planning/phases/{phase_dir}/{phase}-{plan}-ARTIFACT.md`. The sanitizer receives this path as an input parameter and writes to it. The path follows the same convention as SUMMARY.md and VERIFICATION.md.
**Warning signs:** `ls .planning/phases/XX-name/*-ARTIFACT.md` returns nothing after sanitization completes.

### Pitfall 5: Workflow References Wrong Extension Path

**What goes wrong:** The `review_team_gate` step in execute-plan.md references `@~/.claude/get-shit-done-review-team/workflows/review-team.md` but the workflow file references agents at a different path.
**Why it happens:** Inconsistent path assumptions between install.sh, review_team_gate, and review-team.md.
**How to avoid:** All paths must use the canonical base: `~/.claude/get-shit-done-review-team/`. The workflow references agents as `@~/.claude/get-shit-done-review-team/agents/gsd-review-sanitizer.md`. This matches the install.sh `EXT_INSTALL_DIR` from Phase 1.
**Warning signs:** "Agent file not found" errors when the pipeline tries to load the sanitizer.

### Pitfall 6: Sanitizer Produces Prose Instead of Structured Sections

**What goes wrong:** Despite the ARTIFACT.md schema being specified, the sanitizer produces a narrative paragraph instead of the named sections. This makes Phase 3 reviewer prompts less targeted and harder to parse.
**Why it happens:** The sanitizer prompt allows too much freedom in output format. Without a strict template, the LLM defaults to prose.
**How to avoid:** The sanitizer's `<output>` section must contain the EXACT markdown template with all section headers pre-defined. The agent fills in the sections; it does not choose its own structure. The completeness check step verifies all sections are present and non-empty.
**Warning signs:** ARTIFACT.md does not contain the expected section headers ("## Files Changed", "## Behavior Implemented", etc.).

---

## Code Examples

### Example 1: Sanitizer Agent Frontmatter and Role

Source: GSD-AGENT-PATTERNS.md conventions applied to sanitizer requirements

```markdown
---
name: gsd-review-sanitizer
description: Strips executor reasoning from SUMMARY.md. Produces clean artifact description for reviewers. Spawned by review-team workflow.
tools: Read, Write
color: green
---

<role>
You are a GSD review sanitizer. You transform executor output into clean artifact descriptions.

Spawned by the `review-team` workflow after each plan completes.

Your job: Read SUMMARY.md. Extract every observable fact about what was built. Strip every trace of executor reasoning, internal thought process, and decision justification. Write a structured ARTIFACT.md that a reviewer can evaluate with zero anchoring bias.

**Critical mindset:** Your job is to destroy reasoning, not summarize it. If in doubt, strip it out. A missing fact can be recovered from the codebase. A leaked reasoning chain permanently anchors every reviewer downstream.
</role>
```

### Example 2: Sanitizer Strip List (DO NOT Preserve Section)

```markdown
<strip_list>
## What to Strip (Reasoning/Bias Sources)

Remove ALL instances of the following from the artifact:

**First-person reasoning:**
- "I decided...", "I chose...", "I considered...", "I evaluated..."
- "We opted for...", "We went with..."
- Any sentence where the executor describes their thought process

**Alternatives and comparisons:**
- "Instead of X, we used Y"
- "We considered X but chose Y because..."
- "Alternatively..."
- Any mention of approaches that were NOT taken

**Confidence and quality language:**
- "This should work because...", "This handles X well"
- "Robust", "elegant", "clean", "simple", "straightforward"
- "Hopefully", "probably", "likely", "should be fine"

**Justifications and rationale:**
- "Because...", "The reason is...", "This is necessary for..."
- "To prevent...", "To ensure...", "To avoid..."
- Any clause that explains WHY a decision was made

**Execution narration:**
- "First I created...", "Then I modified...", "Next I added..."
- Task-by-task play-by-play of what the executor did
- References to the plan or plan task numbers

**Cross-plan references:**
- "As established in Phase 1...", "Building on the previous plan..."
- References to PLAN.md, prior SUMMARY.md files, or ROADMAP.md
- Any context from outside this single plan's execution

**Self-evaluation:**
- "The implementation is complete", "All tasks done"
- "Everything works as expected"
- Any assessment of quality or completeness
</strip_list>
```

### Example 3: Sanitizer Preserve List (MUST Keep Section)

```markdown
<preserve_list>
## What to Preserve (Observable Facts)

Your artifact MUST contain ALL of the following from the input:

**Every file path:** All files listed in "Files Created/Modified", key-files frontmatter, and any file paths mentioned in the body. Missing a file path means the reviewer cannot evaluate that file's impact.

**Behavior as observable fact:** What the code does, stated without reasoning.
- KEEP: "Login endpoint accepts email + password, returns JWT token"
- STRIP: "Login endpoint accepts email + password, returns JWT token because stateless auth scales better"

**Stack changes:** Every dependency added, removed, or updated. Include version numbers if stated.

**API contracts:** Every endpoint, request/response shape, method, and path.

**Configuration changes:** Every env var, config file change, or infrastructure change.

**Key decisions as facts:** State what was decided, not why.
- KEEP: "JWT tokens use 15-minute expiry with 7-day refresh tokens"
- STRIP: "JWT tokens use 15-minute expiry because shorter windows limit exposure"

**Error handling behavior:** How failures are handled, stated as behavior.

**Test coverage facts:** What is tested and what is not.
</preserve_list>
```

### Example 4: Sanitizer Completeness Check Step

```markdown
## Step 3: Completeness Check

Before writing ARTIFACT.md, verify your output is complete:

1. **File path audit:** Count file paths in your output. Count file paths in the input SUMMARY.md (from "Files Created/Modified" section and key-files frontmatter). If your count is lower, you have over-stripped. Go back and add the missing paths.

2. **Section population:** Every section in the ARTIFACT.md template MUST have content OR explicitly state "None" if the SUMMARY.md truly contains nothing for that section. Empty sections without "None" are a completeness failure.

3. **Stack change audit:** If the SUMMARY.md mentions any new dependency (in tech-stack.added, Accomplishments, or body text), it MUST appear in your Stack Changes section.

4. **Reasoning leak scan:** Read your output one more time. Flag any sentence containing: "I", "we", "chose", "decided", "because", "alternatively", "considered", "should", "better", "elegant", "robust", "hopefully", "probably". Remove or rewrite any flagged sentence to state only the fact.
```

### Example 5: review-team.md Workflow TEAM.md Validation Step

```markdown
<step name="validate_team" priority="first">
Read `.planning/TEAM.md` and validate it has at least one valid reviewer role.

A valid role requires:
1. A `## Role:` section header
2. A YAML code block containing a `name:` field
3. At least one item under `**What this role reviews:**`

```bash
# Check TEAM.md exists (should already be confirmed by review_team_gate, but double-check)
[ -f .planning/TEAM.md ] || { echo "ERROR: .planning/TEAM.md not found"; exit 1; }
```

Read `.planning/TEAM.md`. Split on `## Role:` headers. For each section:
- Extract `name:` from the YAML code block
- Verify the section has review criteria

If zero valid roles found:
```
## REVIEW PIPELINE HALTED

**Error:** TEAM.md exists but contains zero valid reviewer roles.

Each role requires:
1. A `## Role:` section header
2. A YAML code block with `name:` field
3. At least one review criteria item

Run `/gsd:new-reviewer` to create your first reviewer role.
```

HALT the pipeline. Do NOT proceed to sanitization. This is TEAM-03.

If one or more valid roles found:
- Store role count for later use
- Store role names for later use
- Log: `Review Team: {N} reviewer role(s) found in TEAM.md`
- Proceed to sanitize step
</step>
```

### Example 6: review-team.md Workflow Sanitize Step

```markdown
<step name="sanitize">
Spawn the sanitizer agent to produce ARTIFACT.md from SUMMARY.md.

The sanitizer receives:
- The SUMMARY.md path (to read)
- The ARTIFACT.md output path (to write)
- The phase and plan identifiers (for the artifact header)

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
    Summary path: {summary_path}
    Artifact output path: {artifact_path}
    Phase: {phase_identifier}
    Plan: {plan_number}
    Plan name: {plan_name}
    </inputs>

    <execution_context>
    @~/.claude/get-shit-done-review-team/agents/gsd-review-sanitizer.md
    </execution_context>
  "
)
```

After the sanitizer returns:
- Verify ARTIFACT.md exists at the expected path:
  ```bash
  [ -f "{artifact_path}" ] && echo "ARTIFACT EXISTS" || echo "ARTIFACT MISSING"
  ```
- If ARTIFACT.md is missing: halt pipeline with error
- If ARTIFACT.md exists: log `Review Team: ARTIFACT.md written to {artifact_path}`

The sanitizer's return includes a strip count and status. Log these for audit purposes.
</step>
```

---

## Detailed Design: gsd-review-sanitizer.md

### Agent Identity

| Field | Value | Rationale |
|-------|-------|-----------|
| name | gsd-review-sanitizer | GSD naming: `gsd-{role}` |
| tools | Read, Write | Content transformer -- no codebase inspection needed |
| color | green | Quality-gate agent class |
| spawner | review-team workflow | Single spawner |

### Process Steps

| Step | Name | Purpose |
|------|------|---------|
| 0 | Read input | Read SUMMARY.md from provided path |
| 1 | Extract facts | Parse SUMMARY.md for all preservable content |
| 2 | Strip reasoning | Remove all reasoning language, justifications, narration |
| 3 | Completeness check | Verify file paths, sections, stack changes are all present |
| 4 | Write ARTIFACT.md | Write structured output to disk at provided path |
| 5 | Return status | Return SANITIZATION COMPLETE with artifact path and strip metrics |

### Critical Rules

1. **DO NOT preserve any executor reasoning.** "I chose X because Y" becomes "X was used." If you cannot separate fact from reasoning in a sentence, strip the entire sentence -- a missing fact is recoverable; leaked reasoning is permanent contamination.

2. **DO NOT add content.** You are a filter, not a generator. Every fact in your output must trace to a specific sentence or field in the input SUMMARY.md. Do not infer, speculate, or expand.

3. **DO NOT reference PLAN.md, ROADMAP.md, or any file other than the input SUMMARY.md.** You have one input. Referencing other files introduces context the reviewers should not have.

4. **DO preserve every file path.** A missing file path means a reviewer cannot evaluate that file's contribution. Over-preserving file paths is safe; over-stripping is not.

5. **DO write ARTIFACT.md as a standalone document.** A reader of ARTIFACT.md must understand what was built without reading any other file. No references to "see SUMMARY.md for details" or "as described in PLAN.md."

### Return Format

```markdown
## SANITIZATION COMPLETE

**Source:** {path to SUMMARY.md}
**Artifact:** {path to ARTIFACT.md}
**Stripped:** {count} reasoning elements removed
**Sections populated:** {count}/{total} sections have content
**File paths preserved:** {count} paths in artifact vs {count} paths in source

{If file path counts don't match:}
**WARNING:** File path count mismatch. {N} paths in source, {M} in artifact. Verify completeness.
```

### Success Criteria

```markdown
- [ ] SUMMARY.md read completely from provided path
- [ ] All file paths from SUMMARY.md present in ARTIFACT.md
- [ ] Zero reasoning language in output (no "I decided", "chose", "because", "alternatively")
- [ ] All ARTIFACT.md sections populated or marked "None"
- [ ] ARTIFACT.md is standalone -- no references to SUMMARY.md, PLAN.md, or other files
- [ ] ARTIFACT.md written to disk at the correct path
- [ ] Structured return provided to workflow
```

---

## Detailed Design: review-team.md Workflow

### Workflow Identity

This is a GSD workflow file (not an agent). It follows the `<purpose>`, `<process>`, `<step>` convention used by `execute-plan.md` and `execute-phase.md`.

### Inputs

The workflow receives these values from the `review_team_gate` step in execute-plan.md:
- SUMMARY.md path (current plan's summary)
- Phase identifier (e.g., "01-extension-scaffold-gsd-integration")
- Plan identifier (e.g., "02")

### Step Sequence (Phase 2 Skeleton)

| Step | Name | Purpose | Phase |
|------|------|---------|-------|
| 1 | validate_team | Read TEAM.md, validate >= 1 role, extract role names | Phase 2 |
| 2 | sanitize | Spawn sanitizer, produce ARTIFACT.md | Phase 2 |
| 3 | spawn_reviewers | (Placeholder) Spawn reviewer agents in parallel | Phase 3 |
| 4 | synthesize | (Placeholder) Collect findings, route | Phase 4 |

Phase 2 implements steps 1 and 2. Steps 3 and 4 are documented as placeholders with `[Phase 3/4 — not yet implemented]` markers.

### TEAM.md Validation Logic

```
Read .planning/TEAM.md
Split on "## Role:" headers
For each role section:
  - Look for ```yaml ... name: VALUE ... ``` block
  - Extract VALUE as role_name
  - Check section has "**What this role reviews:**"
  - If valid: add to roles list
  - If invalid: log warning naming the specific role

If roles list is empty:
  HALT with error: "TEAM.md has zero valid roles"
  (This satisfies TEAM-03 and Phase 2 success criterion #4)

If roles list has >= 1 entry:
  Proceed to sanitize step
```

### Artifact Path Convention

The ARTIFACT.md path follows the existing GSD convention for per-plan artifacts:

```
.planning/phases/{phase_dir}/{phase}-{plan}-ARTIFACT.md
```

Examples:
- `.planning/phases/01-extension-scaffold-gsd-integration/01-01-ARTIFACT.md`
- `.planning/phases/02-sanitizer-artifact-schema/02-01-ARTIFACT.md`

This matches the SUMMARY.md naming: `{phase}-{plan}-SUMMARY.md` becomes `{phase}-{plan}-ARTIFACT.md`. (SAND-03)

### Return Format

```markdown
## REVIEW PIPELINE: SANITIZE COMPLETE

**Phase:** {phase}
**Plan:** {plan}
**Roles found:** {N} ({role names})
**Artifact:** {artifact_path}

[Phase 3/4: Reviewer spawning and synthesis not yet implemented]
[Pipeline stops here in Phase 2 -- review-team.md will be extended in later phases]
```

---

## Resolving the Open Concern: Disk vs Inline

**Open concern from STATE.md:** "Does ARTIFACT.md get written to disk vs. passed inline? This is a product decision for Phase 2."

**Decision: Write to disk.** Rationale:

1. **Audit trail (SAND-03):** The requirement explicitly says "written to disk as `{phase}-{plan}-ARTIFACT.md` in the phase directory for audit trail." This is not optional.

2. **Context efficiency:** Phase 3 reviewers will read the artifact from a file path. Passing inline means the workflow must hold the full artifact text in its context and inject it into each reviewer prompt. Passing a path means each reviewer reads it fresh with their own 200k context. This follows the GSD pattern: "Pass paths only -- executors read files themselves with their fresh 200k context."

3. **Debuggability:** When a reviewer produces unexpected findings, the developer can read ARTIFACT.md to see exactly what the reviewer saw. With inline passing, there is no persistent record of the sanitizer's output.

4. **Isolation guarantee (SAND-04):** "Reviewers receive ONLY the sanitized artifact." If the artifact is a file, the workflow passes only that file path to reviewers. If it is inline, the workflow must manually ensure nothing else is in the prompt -- a contamination vector.

---

## SUMMARY.md Input Analysis

The sanitizer processes SUMMARY.md files produced by the GSD executor. Based on analysis of real Phase 1 summaries and the official template:

### What SUMMARY.md Contains

Source: `C:/Users/gutie/.claude/get-shit-done/templates/summary.md` + Phase 1 actual summaries

**Frontmatter (machine-readable):** phase, plan, subsystem, tags, requires/provides/affects, tech-stack (added, patterns), key-files (created, modified), key-decisions, patterns-established, duration, completed

**Body sections:**
1. One-liner summary
2. Performance (duration, timestamps, task/file counts)
3. Accomplishments (bullet list)
4. Task Commits (task names + commit hashes)
5. Files Created/Modified (paths + descriptions)
6. Decisions Made (with rationale)
7. Deviations from Plan (if any)
8. Issues Encountered
9. User Setup Required
10. Next Phase Readiness
11. Self-Check results

### What the Sanitizer Extracts from Each Section

| SUMMARY.md Section | Sanitizer Action |
|--------------------|-----------------|
| Frontmatter (key-files) | EXTRACT file paths to Files Changed table |
| Frontmatter (tech-stack.added) | EXTRACT to Stack Changes table |
| Frontmatter (key-decisions) | EXTRACT, strip rationale |
| Frontmatter (patterns-established) | EXTRACT to Key Decisions as facts |
| One-liner summary | PRESERVE as-is (already factual) |
| Performance | STRIP entirely (meta, not artifact content) |
| Accomplishments | EXTRACT facts, strip reasoning language |
| Task Commits | STRIP entirely (executor process, not artifact) |
| Files Created/Modified | EXTRACT all paths and descriptions |
| Decisions Made | EXTRACT "what" decisions, STRIP "why" rationale |
| Deviations from Plan | EXTRACT what changed, STRIP reasoning for change |
| Issues Encountered | STRIP entirely (executor process) |
| User Setup Required | EXTRACT env vars and config requirements |
| Next Phase Readiness | STRIP entirely (forward-looking, not artifact) |
| Self-Check results | STRIP entirely (executor process) |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Reviewers read raw SUMMARY.md | Sanitizer creates ARTIFACT.md first | This phase | Eliminates anchoring bias from executor reasoning |
| Inline artifact passing | File-based artifact passing | This phase | Audit trail, context efficiency, debuggability |
| Single-reviewer inline | Multi-agent pipeline with file-based handoff | This phase | Scales to N reviewers without context bloat |

**Not applicable for this phase:** There are no deprecated features or version migrations. This is the first implementation of the sanitizer and workflow.

---

## Open Questions

1. **How should the sanitizer handle SUMMARY.md frontmatter?**
   - What we know: Frontmatter contains machine-readable metadata including key-files, tech-stack, and key-decisions.
   - What's unclear: Should the sanitizer parse the YAML frontmatter programmatically, or treat the entire SUMMARY.md as prose and extract facts from body text?
   - Recommendation: The sanitizer should read BOTH the frontmatter and body. Frontmatter key-files are the most reliable source of file paths. Frontmatter tech-stack.added is the most reliable source of dependency changes. Use both as ground truth; body text supplements.

2. **Should ARTIFACT.md have its own YAML frontmatter?**
   - What we know: VERIFICATION.md and SUMMARY.md both have YAML frontmatter for machine parsing.
   - What's unclear: Will any downstream tool need to parse ARTIFACT.md frontmatter?
   - Recommendation: Yes, include minimal frontmatter: `phase`, `plan`, `generated` timestamp, `source` (SUMMARY.md path). This enables the verifier (or future tools) to trace artifacts to their source. Keeps the two-channel return pattern consistent.

3. **How does the workflow know the plan name for the ARTIFACT.md header?**
   - What we know: The review_team_gate step has access to the current plan identifier and SUMMARY.md path.
   - What's unclear: Does the workflow need to read SUMMARY.md to get the plan name, or is it passed by the gate step?
   - Recommendation: The gate step passes the SUMMARY.md path. The sanitizer reads the SUMMARY.md title line (which contains the plan name) as part of its normal processing. The workflow does not need to parse SUMMARY.md separately.

---

## Sources

### Primary (HIGH confidence)
- `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` -- 6-part agent structure, frontmatter conventions, role section patterns, return format patterns, tool conventions
- `D:/GSDteams/.planning/research/REVIEW-PIPELINE-DESIGN.md` -- Strip/preserve schema (Section 1.1), sanitization patterns (Section 1.2), over-sanitization failure mode (Section 5)
- `D:/GSDteams/.planning/research/TASK-ISOLATION.md` -- Task() isolation guarantee, contamination vectors, context inheritance model
- `D:/GSDteams/.planning/research/GSD-EXTENSION-ARCH.md` -- Extension path conventions, config.json schema, @ reference pattern
- `C:/Users/gutie/.claude/agents/gsd-verifier.md` -- Verified agent structure (6-part convention, critical_rules, success_criteria pattern)
- `C:/Users/gutie/.claude/get-shit-done/workflows/execute-plan.md` -- Verified workflow step convention, review_team_gate step text, SUMMARY.md creation step
- `C:/Users/gutie/.claude/get-shit-done/workflows/execute-phase.md` -- Task() invocation pattern, path-passing convention
- `C:/Users/gutie/.claude/get-shit-done/templates/summary.md` -- SUMMARY.md template (sanitizer input format)
- `D:/GSDteams/.planning/phases/01-extension-scaffold-gsd-integration/01-01-SUMMARY.md` -- Real SUMMARY.md example (sanitizer input)
- `D:/GSDteams/.planning/phases/01-extension-scaffold-gsd-integration/01-02-SUMMARY.md` -- Real SUMMARY.md example
- `D:/GSDteams/.planning/phases/01-extension-scaffold-gsd-integration/01-03-SUMMARY.md` -- Real SUMMARY.md example
- `D:/GSDteams/.planning/phases/01-extension-scaffold-gsd-integration/01-04-SUMMARY.md` -- Real SUMMARY.md example
- `D:/GSDteams/templates/TEAM.md` -- Actual TEAM.md format (role parsing target)
- `D:/GSDteams/.planning/PROJECT.md` -- Pipeline architecture, sanitization requirements
- `D:/GSDteams/.planning/REQUIREMENTS.md` -- SAND-01 through SAND-04, TEAM-03
- `D:/GSDteams/.planning/ROADMAP.md` -- Phase 2 success criteria and plan descriptions
- `D:/GSDteams/.planning/STATE.md` -- Accumulated decisions, open concerns

### Secondary (MEDIUM confidence)
- None -- all findings verified against primary sources

### Tertiary (LOW confidence)
- None -- no unverified claims in this research

---

## Metadata

**Confidence breakdown:**
- Sanitizer agent design: HIGH -- follows verified GSD agent conventions (gsd-verifier.md pattern) + strip/preserve schema from REVIEW-PIPELINE-DESIGN.md
- ARTIFACT.md schema: HIGH -- derived from REQUIREMENTS.md SAND-02/SAND-03 + REVIEW-PIPELINE-DESIGN.md Section 7.2
- TEAM.md parsing: HIGH -- split pattern confirmed in Phase 1 execution (01-01-SUMMARY.md key decisions)
- review-team.md workflow: HIGH -- follows verified workflow conventions (execute-plan.md, execute-phase.md patterns)
- Disk vs. inline decision: HIGH -- SAND-03 explicitly requires disk write; GSD path-passing convention confirms

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (stable -- no external dependencies that could change)
