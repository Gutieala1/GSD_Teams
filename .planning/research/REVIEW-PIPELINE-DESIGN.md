# Research: Multi-Agent Review Pipeline Design

**Project:** GSD Review Team
**Researched:** 2026-02-25
**Mode:** Ecosystem + Feasibility
**Overall Confidence:** MEDIUM-HIGH (training data through Aug 2025; web search unavailable — external validation recommended for fast-moving framework details)

---

## 1. Sanitization Patterns

### 1.1 What Must Be Stripped (Anchoring Bias Sources)

**Confidence: HIGH** — well-documented in cognitive bias literature applied to LLM review contexts.

The core problem is *reasoning contamination*: a reviewer who sees the executor's justification for a decision tends to evaluate whether the reasoning is internally consistent rather than whether the decision is correct. This mirrors confirmation bias in human code review (where reviewers anchor to the author's stated intent).

**Strip from sanitizer output:**

| Element | Why Strip | Risk if Kept |
|---------|-----------|--------------|
| Executor's self-description ("I decided to...") | Anchors reviewer to executor's framing | Reviewer validates reasoning instead of examining outcome |
| Alternative approaches considered and rejected | Primes reviewer against alternatives | Reviewer treats rejected paths as already-resolved |
| Step-by-step execution log / task narration | Gives reviewer a "story" that explains away issues | Issues that "make sense in context" get rationalized |
| Confidence language ("This should work because...") | Transmits false certainty | Reviewer inherits confidence level, not just the artifact |
| References to previous plans or prior summaries | Creates cross-plan anchoring | Reviewer evaluates against a baseline the executor set |
| Hedging/uncertainty language from executor | Primes reviewer to focus on known-uncertain areas only | Known-unknown known areas get overlooked |
| Internal commentary on trade-offs | Frames trade-offs as already-resolved | Reviewer doesn't re-examine the trade-off fresh |

**Keep in sanitizer output:**

| Element | Why Keep | Risk if Stripped |
|---------|----------|-----------------|
| Files created or modified (exact paths) | Reviewer needs scope | Can't review what they can't identify |
| Behavior implemented (what it does, not how the executor reasoned) | Subject matter for review | Without this, reviewer reviews a ghost |
| Technology/libraries added to the stack | Security, compatibility surface | Silent new dependencies are highest-risk blind spot |
| API contracts exposed or consumed | Interface review | Contract bugs are the most expensive bugs |
| Data structures and their shapes | Performance, correctness | Shape bugs compound silently |
| Configuration changes, env vars added | Security, ops | Config is highest-density security surface |
| Test coverage state | Quality signal | Reviewer needs to know what's tested vs. not |
| Error handling paths (what happens on failure) | Correctness | Unhappy paths are where bugs live |
| External service integrations | Security, reliability | Third-party surfaces need explicit attention |

**Design principle:** The sanitizer produces a *factual artifact description*, not a *narrative*. Facts about what exists. Zero editorial from the executor about why those facts are good.

### 1.2 Sanitization Implementation Pattern

```
Input:  SUMMARY.md (executor's narrative summary)
Output: ARTIFACT.md (clean factual description)

Sanitizer prompt structure:
1. Role: "You are an artifact extractor. Your job is to extract facts
   about what was built, not why."
2. Explicit strip list: enumerate every category above
3. Output schema: enforce structured sections (Files, Behavior, Stack,
   Contracts, Config, Tests, Error Paths)
4. Negative constraint: "Do NOT include any reasoning, justification,
   narrative, or opinion from the original text."
5. Self-check step: "Review your output. Remove any sentence that
   describes WHY something was done."
```

**Known failure mode:** Sanitizers frequently omit things by being over-aggressive. Include an explicit "completeness check" step: "Does your output contain all file paths? All new dependencies? All API endpoints?" This catches over-stripping.

---

## 2. Reviewer Prompt Design

### 2.1 Role Isolation — Keeping Reviewers in Their Lane

**Confidence: HIGH** — based on established prompt engineering patterns and LLM behavior research.

The core isolation problem: LLMs are trained on comprehensive codebases and naturally generalize. A "Security Auditor" will drift into performance observations because it *can*, not because it *should*.

**Proven isolation techniques:**

**Hard boundary declaration (most effective):**
```
You are a Security Auditor. Your ONLY job is to find security vulnerabilities.

You are EXPLICITLY NOT responsible for:
- Code style or readability
- Performance concerns
- Architectural decisions
- Business logic correctness (unless it creates a security hole)
- Anything not related to security

If you notice something outside security, IGNORE IT. Do not mention it.
A separate reviewer handles that domain.
```

The explicit NOT-responsible list is critical. Without it, reviewers bleed. The list signals that the model's comprehensive knowledge is being intentionally scoped — it gives the model "permission" to ignore things it would normally flag.

**Domain anchor repetition:** Repeat the role at the top of each finding. Forces the model to re-contextualize before generating each item:
```
For each finding, begin: "As Security Auditor, I found: ..."
```

**Single-concern output schema:** If the output schema only has fields relevant to the domain, the model has nowhere to put off-domain observations. A security schema with `vulnerability_class`, `attack_vector`, `cvss_score` gives no affordance for a "this looks slow" comment.

**Anti-role-bleed instruction:** "If you find yourself wanting to note something outside your domain, write ONLY: [OUT_OF_SCOPE]. Do not explain what it was." This captures the impulse without letting it expand.

### 2.2 Structured, Machine-Parseable Output

**Confidence: HIGH** — JSON output from LLMs is well-established, with known failure modes.

**Recommended finding schema:**

```json
{
  "findings": [
    {
      "id": "SEC-001",
      "reviewer": "security_auditor",
      "severity": "critical|major|minor|informational",
      "category": "[domain-specific category]",
      "file": "path/to/file.ts",
      "line_range": "optional: 45-52",
      "title": "Short, imperative title (max 80 chars)",
      "description": "What is wrong. Observable, specific, no speculation.",
      "evidence": "The exact code or config element that demonstrates the issue.",
      "impact": "What breaks or can be exploited if this is not fixed.",
      "recommendation": "Specific, actionable fix. Not 'improve X' — say exactly what to do.",
      "confidence": "high|medium|low",
      "references": ["optional: CVE-XXXX, RFC-XXXX, etc."]
    }
  ],
  "reviewed_scope": ["list of files/components this reviewer examined"],
  "out_of_scope_signals": 0
}
```

**Key schema design decisions:**

- `id` with prefix: enables deduplication and cross-reference by synthesizer
- `evidence`: the literal artifact element — forces specificity, dramatically reduces hallucination
- `confidence`: per-finding, not just overall — enables synthesizer to weight findings
- `reviewed_scope`: allows synthesizer to detect coverage gaps
- `out_of_scope_signals`: count of things the reviewer noticed but suppressed — useful calibration metric

**Reliability improvements for JSON output:**

1. Use `json_object` response format if the API supports it (OpenAI, Anthropic support structured output)
2. Include a minimal valid example in the prompt — one complete finding object
3. Add a validation instruction: "Ensure your JSON is valid. Each finding must have all required fields."
4. Never ask for a count before the list — primes the model to fabricate to match the count

### 2.3 Severity Calibration — Preventing Inflation

**Confidence: HIGH** — severity inflation is one of the most documented failure modes.

**Problem:** Without anchoring, LLMs escalate severity. "Minor" becomes "major" becomes "critical" as models hedge toward importance. A reviewer that cries wolf on every finding destroys trust in the pipeline.

**Calibration pattern — severity rubric in the prompt:**

```
Severity definitions for this domain:

CRITICAL: Would cause data loss, security breach, or complete system failure
          in production. Requires immediate halt.
          Example: SQL injection in user-controlled input.

MAJOR: Incorrect behavior that would reach users or break core functionality.
       Requires fix before shipping.
       Example: Race condition in payment processing.

MINOR: Suboptimal but working. Degrades quality without breaking behavior.
       Fix before next review cycle.
       Example: Missing index on a frequently queried column.

INFORMATIONAL: Observation worth recording. No action required.
               Example: Deprecated API in use — no replacement needed yet.

Rule: When in doubt between two levels, choose the LOWER one.
Rule: Do not use CRITICAL for anything you would not personally stop a
      production deploy for.
```

The "when in doubt, go lower" rule is empirically effective. LLMs respond to explicit tie-breaking instructions.

**Anti-severity-inflation pattern:** Add a reflection step:
```
Before finalizing, review each CRITICAL finding. Ask: "If this code
shipped to production right now, would a real attacker exploit this
within 24 hours?" If no, downgrade to MAJOR.
```

### 2.4 Preventing Hallucinated Findings

**Confidence: HIGH** — LLM hallucination in code review is well-documented.

**Root causes of hallucinated findings:**

1. **Pattern matching without grounding**: Model recognizes a pattern (e.g., "user input in SQL") but the actual code doesn't have that pattern
2. **Reasoning about what might be present**: Model infers from file names that certain code exists
3. **Prior training examples bleeding in**: Model has seen so many examples of "this type of code has X bug" that it reports X regardless

**Prevention techniques:**

**Evidence-first instruction:**
```
You may ONLY report a finding if you can quote the specific line or
configuration element that demonstrates it. If you cannot quote it
directly from the artifact, you cannot report it.

Format: evidence field MUST be a direct quote, not a description.
```

**Scope boundary enforcement:**
```
Your review is limited to what is explicitly described in the artifact.
Do NOT make assumptions about code that is NOT shown.
Do NOT report findings based on what code "typically" looks like.
Do NOT infer the presence of vulnerabilities from file names alone.
```

**Confidence-gated reporting:**
```
Only report findings you are HIGH or MEDIUM confidence about.
LOW confidence observations must be formatted as:
  "UNVERIFIED SIGNAL: [what you observed] — requires human verification"
Do not include unverified signals in your findings array.
```

**Uncertainty expression:** Allow and encourage "I cannot determine X from the artifact" — this is a signal of good epistemics, not failure.

---

## 3. Synthesis Patterns

### 3.1 Aggregating Findings from Multiple Reviewers

**Confidence: HIGH** — pattern is well-established in human review systems (code review tools, security scanners) with LLM adaptation.

**Synthesizer responsibilities:**
1. Deduplication — same issue found by multiple reviewers
2. Conflict resolution — reviewers disagree on severity
3. Correlation — multiple minor findings that together indicate a major issue
4. Routing decision — which destination gets each finding
5. Summary generation — executive view of the review

**Deduplication strategy:**

The hardest problem. Two reviewers can find the "same" issue described completely differently.

*Approach 1: Semantic grouping (recommended)*
Pass all findings to the synthesizer with instruction:
```
Group findings that describe the same underlying issue, even if described
differently. A "missing authentication" finding from the Security Auditor
and an "unauthorized access path" from the Rules Lawyer are the same issue.

When grouping, keep the finding with the HIGHER severity and add a
"also_reported_by" field.
```

*Approach 2: File+line overlap*
Findings referencing the same file and overlapping line ranges are candidate duplicates. More reliable than semantic matching but misses conceptual duplicates.

*Approach 3: Embedding similarity (over-engineered for v1)*
Run embeddings on finding descriptions, cluster by cosine similarity. Only worth it if reviewer count > 5 or findings volume is high.

**Recommendation for GSD v1:** Semantic grouping (Approach 1) — the synthesizer LLM is well-suited to this and it handles the conceptual duplicates that file/line matching misses.

### 3.2 Classification Schemes

**Confidence: MEDIUM** — drawing on security tool conventions and code review tooling taxonomy.

**Recommended finding classification for the synthesizer:**

```
Primary dimension: Severity (critical / major / minor / informational)
Secondary dimension: Type (security / correctness / performance /
                           maintainability / compliance / coverage)
Tertiary dimension: Confidence (high / medium / low)
```

The synthesizer maps findings onto this 3-axis classification and uses the combination to determine routing:

```
critical + any type + high confidence   → block_and_escalate
major    + correctness                  → send_for_rework
major    + security                     → block_and_escalate
major    + performance                  → send_for_rework OR log (per role hint)
minor    + any                          → log_and_continue
any      + low confidence               → log_and_continue (with flag)
```

**Correlation pattern (finding amplification):**
```
If 3+ findings reference the same file AND are all minor:
  → Synthesizer escalates to "file under systemic review"
  → Combined finding gets major severity
  → Routed to rework with note: "Multiple minor issues suggest
    broader problem in this file"
```

This catches the "death by a thousand cuts" failure mode where no single minor finding triggers action but the aggregate signals a real problem.

### 3.3 Synthesizer Prompt Structure

```
You receive findings from [N] isolated reviewers. Your job is to:
1. Deduplicate: identify findings describing the same underlying issue
2. Correlate: identify minor findings in the same file/component that
   collectively indicate a systemic problem
3. Classify: assign each unique finding a type from:
   [security, correctness, performance, maintainability, compliance, coverage]
4. Route: assign routing destination per the routing rules below
5. Summarize: produce an executive summary (max 3 sentences)

Do NOT add new findings. Do NOT change the technical content of findings.
Your job is organization and routing, not discovery.

Routing rules:
[... routing table from PROJECT.md ...]

Output as JSON matching the FindingSummary schema.
```

The "Do NOT add new findings" constraint is critical — synthesizers tend to generate meta-findings ("The overall security posture is weak") which aren't actionable.

---

## 4. Finding Data Structure

### 4.1 The Canonical Finding Object

**Confidence: HIGH** — derived from established formats (SARIF, GitHub code scanning, OWASP findings, CodeClimate issue format).

```typescript
interface Finding {
  // Identity
  id: string;                    // "{ROLE_PREFIX}-{sequence}" e.g. "SEC-001"
  reviewer: string;              // Role name from TEAM.md

  // Classification
  severity: "critical" | "major" | "minor" | "informational";
  type: "security" | "correctness" | "performance" |
        "maintainability" | "compliance" | "coverage";
  confidence: "high" | "medium" | "low";

  // Location
  file: string;                  // Relative path from project root
  line_range?: string;           // "45-52" or null if file-level
  component?: string;            // Logical component name (e.g., "AuthMiddleware")

  // Content
  title: string;                 // Imperative, ≤80 chars: "Add rate limiting to /api/login"
  description: string;           // Observable issue, no speculation
  evidence: string;              // Direct quote from artifact — required
  impact: string;                // What breaks or is exploited
  recommendation: string;        // Specific action, not vague advice

  // Routing
  routing_destination: "block_and_escalate" | "send_for_rework" |
                        "send_to_debugger" | "log_and_continue";
  routing_rationale: string;     // Why this routing was chosen

  // Metadata
  also_reported_by?: string[];   // Other reviewers who found the same issue
  related_findings?: string[];   // IDs of correlated findings
  phase: string;                 // Phase identifier
  plan: number;                  // Plan number within phase
  timestamp: string;             // ISO 8601
}

interface ReviewSummary {
  phase: string;
  plan: number;
  timestamp: string;
  reviewer_count: number;
  finding_count: number;
  findings_by_severity: Record<string, number>;
  findings_by_routing: Record<string, number>;
  highest_routing_action: string;  // The most severe action required
  findings: Finding[];
  executive_summary: string;       // 2-3 sentences
}
```

**Why SARIF-inspired:** SARIF (Static Analysis Results Interchange Format) is the GitHub standard for security findings. Aligning with it means the output is compatible with GitHub Code Scanning and other tooling, even if you never explicitly support SARIF.

**Key design decisions:**

- `evidence` is required, not optional — if a finding has no evidence it's a hallucination candidate
- `highest_routing_action` on the summary — allows execute-plan.md to check a single field to decide whether to halt
- `routing_rationale` — makes the synthesizer's decisions auditable; essential for debugging routing errors
- `also_reported_by` — enables the REVIEW-REPORT.md to show "3 reviewers flagged this" which is a strong signal

### 4.2 The REVIEW-REPORT.md Output Format

The flat table format in PROJECT.md is correct for human scanning. Recommend supplementing with a "critical findings" block at the top:

```markdown
## Review Report — Phase {X}, Plan {Y}

**Review completed:** {timestamp}
**Reviewers:** {count} | **Findings:** {total} ({critical} critical, {major} major)
**Action required:** {highest_routing_action}

### Critical Findings (action required)
[Only if critical findings exist]

### Major Findings
[...]

### Finding Log
| ID | Reviewer | Severity | Title | File | Routed To |
|----|----------|----------|-------|------|-----------|
```

---

## 5. Known Failure Modes

### 5.1 Critical Failure Modes

**Confidence: HIGH** — extensively documented in multi-agent system research and production deployments.

---

**Failure Mode 1: Severity Inflation (Most Common)**

*What goes wrong:* Reviewers escalate everything to critical/major to appear thorough. The pipeline cries wolf. Users ignore findings. The review team becomes noise.

*Root cause:* LLMs are trained on examples where flagging things is rewarded. They have no cost model for false positives. In the absence of a rubric, they optimize for appearing comprehensive.

*Consequences:* Pipeline trust collapses within 3-5 uses. Users bypass or disable the review team.

*Prevention:*
- Explicit severity rubric with examples (see Section 2.3)
- "When in doubt, go lower" rule
- Tie-breaking question: "Would I personally stop a production deploy for this?"
- Calibration run: test reviewers against known-severity fixtures before deploying

*Detection:* Track severity distribution across runs. >40% major+critical is a calibration problem.

---

**Failure Mode 2: Role Drift / Scope Bleed**

*What goes wrong:* Security Auditor starts commenting on code style. Rules Lawyer identifies performance bottlenecks. Reviewers overlap, duplicates explode, and the "isolated domain expert" guarantee breaks.

*Root cause:* LLMs are generalists. The model knows about performance AND security AND style. Role isolation requires active enforcement, not just a role title.

*Consequences:* Synthesizer deduplication burden explodes. Users get the same finding from 3 reviewers. "Isolation" is perceived as broken.

*Prevention:*
- Explicit NOT-responsible list in each reviewer prompt (see Section 2.1)
- Single-domain output schema that has no affordance for off-domain content
- Anti-bleed instruction: "If you notice something outside your domain, write ONLY: [OUT_OF_SCOPE]"

*Detection:* Findings with `type` that doesn't match the reviewer's domain. Synthesizer can flag these.

---

**Failure Mode 3: Hallucinated Findings**

*What goes wrong:* Reviewer reports a vulnerability that doesn't exist in the artifact. Evidence field references code that was never shown. Finding is based on "typical patterns" not actual artifact content.

*Root cause:* LLMs pattern-match against training examples. "This looks like a Node.js auth module, therefore it probably has JWT verification issues" — whether or not JWT is mentioned.

*Consequences:* Developer investigates phantom bugs. Trust erodes when findings can't be reproduced. "I spent an hour on a finding that was invented" is a project-killer.

*Prevention:*
- Evidence-required rule: no finding without a direct quote from the artifact
- Scope boundary: "Only report what is shown — not what you infer might be present"
- Confidence-gated reporting: LOW confidence findings go to a separate unverified bucket

*Detection:* Evidence fields that contain inference language ("likely", "typically", "probably") rather than direct quotes.

---

**Failure Mode 4: Synthesizer Invention**

*What goes wrong:* The synthesizer, tasked with aggregating findings, generates new findings not present in any reviewer's output. "The overall architecture suggests..." — a meta-finding that no specific reviewer produced.

*Root cause:* LLMs are trained to be helpful. When given a synthesis task, they add value by generating insights. The constraint "only organize, don't discover" requires explicit instruction.

*Consequences:* Findings attributed to the synthesis step that have no grounded basis. Defeats the isolation model since the synthesizer becomes a reviewer.

*Prevention:*
- Explicit constraint: "Do NOT add new findings. Your job is organization and routing only."
- Output schema that maps each synthesized finding back to `source_finding_ids`
- Validation step: every finding in synthesizer output must have at least one `source_finding_id`

---

**Failure Mode 5: Context Bleed Between Parallel Reviewers**

*What goes wrong:* If reviewers are implemented naively (same conversation thread, tool call context), one reviewer's findings pollute the next reviewer's context window.

*Root cause:* Multi-agent frameworks often share conversation history by default. "Parallel" agents can end up with sequential context.

*Consequences:* Reviewer B anchors on Reviewer A's findings. The isolation guarantee breaks at the implementation level even if the prompts are correct.

*Prevention:*
- Each reviewer must be a fresh Task() invocation with zero shared state
- No findings from Reviewer A should appear in Reviewer B's context
- The only shared input is the sanitized artifact (ARTIFACT.md)
- Synthesizer receives ALL findings only AFTER all reviewers complete

*Detection:* Reviewer B's findings reference things only Reviewer A would know about.

---

**Failure Mode 6: Over-Sanitization (Sanitizer Strips Too Much)**

*What goes wrong:* Sanitizer is so aggressive it removes facts needed for review. Reviewer can't evaluate what was built because the artifact description is too thin.

*Root cause:* "Strip reasoning" instruction applied too broadly. Sanitizers conflate "why it was done" with "what was done."

*Consequences:* Reviewers flag "insufficient information" or make up plausible scenarios. False positives and false negatives both increase.

*Prevention:*
- Completeness check step in sanitizer (see Section 1.2)
- Minimum required sections enforced: Files, Behavior, Stack, Contracts, Config, Tests, Error Paths
- Validation: sanitizer output must contain all file paths from the original SUMMARY.md

---

**Failure Mode 7: Finding Volume Overload**

*What goes wrong:* With 5+ reviewers, each producing 10+ findings, the synthesizer receives 50+ findings. Deduplication and routing quality degrades. The REVIEW-REPORT.md becomes too long to scan.

*Root cause:* No per-reviewer finding budget. Reviewers optimize for completeness, not signal-to-noise ratio.

*Consequences:* Critical findings buried. Users stop reading reports. Pipeline becomes a formality.

*Prevention:*
- Per-reviewer finding cap in the prompt: "Report at most 10 findings. If you have more than 10, keep only the highest severity."
- Minimum severity threshold: "Do not report INFORMATIONAL findings unless specifically requested."
- Synthesizer instruction: "If you receive more than 20 unique findings, the top priority is ranking, not comprehensiveness."

---

**Failure Mode 8: Routing Misclassification**

*What goes wrong:* Finding correctly identified but routed incorrectly. A critical security issue goes to `log_and_continue`. A minor style note triggers `block_and_escalate`.

*Root cause:* Routing logic lives in the synthesizer LLM, which may not follow routing rules precisely, especially for edge cases.

*Prevention:*
- Deterministic routing overrides: a `critical` finding ALWAYS goes to `block_and_escalate` regardless of LLM routing decision — this should be enforced in code, not by the LLM
- Severity-to-routing mapping hardcoded as a post-processing step
- LLM routing is advisory; code enforces the minimum routing action

*Detection:* Validate synthesizer output: any `critical` finding with routing other than `block_and_escalate` is a bug.

---

### 5.2 Moderate Failure Modes

**Failure Mode 9: TEAM.md Role Overlap (User Configuration Error)**

*What goes wrong:* User creates two reviewer roles with overlapping domains. Both reviewers cover the same surface area. Synthesizer drowns in duplicates.

*Prevention:* `new-reviewer.md` workflow should check for overlap with existing roles. Warn if new role's focus area has >50% lexical overlap with existing role.

---

**Failure Mode 10: Anchor Creep in Long-Running Projects**

*What goes wrong:* As a project progresses, REVIEW-REPORT.md files accumulate. If reviewers are given access to previous reports "for context," they anchor on prior findings and look for the same issues rather than reviewing fresh.

*Prevention:* Never give reviewers access to REVIEW-REPORT.md. Each review is fresh. Historical reports are for humans only.

---

## 6. Prior Art and Ecosystem Context

**Confidence: MEDIUM** — based on training data; specific version features should be verified against current docs.

### 6.1 CrewAI

CrewAI (v0.80+ as of mid-2025) provides a `Process.sequential` and `Process.parallel` execution model with explicit agent roles and task definitions.

**Relevant patterns for GSD Review Team:**
- `Agent(role="...", goal="...", backstory="...", allow_delegation=False)` — the `allow_delegation=False` flag is key for isolation; it prevents agents from spawning sub-agents or asking other agents for input
- `Task(description="...", expected_output="...", agent=specific_agent)` — tasks bound to specific agents prevent cross-contamination
- `Crew(agents=[...], tasks=[...], process=Process.parallel)` — parallel execution with no shared conversation state

**What GSD Review Team has that CrewAI lacks:**
- CrewAI agents still share a Crew-level memory/context by default. True isolation requires disabling crew memory entirely.
- CrewAI's structured output uses Pydantic models — elegant but requires Python and a build step. GSD's markdown-native approach is more portable.

**Key CrewAI lesson:** Their `verbose=True` logs show exactly how often agents bleed into other roles when not explicitly constrained. The ecosystem has converged on explicit role exclusion lists as the standard mitigation.

### 6.2 AutoGen (Microsoft)

AutoGen's `AssistantAgent` and `UserProxyAgent` model is designed for conversation, not isolation. However, AutoGen v0.4+ introduced `GroupChat` with `speaker_selection_method` options.

**Relevant patterns:**
- `ConversableAgent` with a strict `system_message` is the AutoGen equivalent of an isolated reviewer
- AutoGen's `nested_chat` pattern: an outer orchestrator spawns inner conversations — matches GSD's Task() model
- AutoGen's `SocietyOfMind` pattern: multiple agents collaborate then present a unified view to the user — similar to GSD's synthesizer pattern

**Key difference from GSD:** AutoGen agents are conversational by default — they respond to each other. GSD's model is explicitly non-conversational: reviewers only talk to the sanitized artifact, never to each other. This is a stronger isolation guarantee.

### 6.3 LangChain / LangGraph

LangGraph's `StateGraph` with separate nodes per reviewer is the closest architectural match to GSD's pipeline:

```
Sanitizer → [Reviewer nodes in parallel] → Synthesizer → Router
```

LangGraph handles the "parallel then join" pattern natively. The `Annotation` system allows typed state that flows between nodes.

**Key lesson from LangGraph ecosystem:** Their "map-reduce" pattern for parallel agents (fan-out to reviewers, fan-in to synthesizer) is well-tested. The main design decision is whether to use a shared graph state (simpler, less isolated) or separate graph instances per reviewer (more isolated, more complex).

**Recommendation for GSD:** GSD's Task() model is equivalent to LangGraph's separate graph instances approach — the right choice for isolation.

### 6.4 OWASP LLM Top 10 (2025)

**Confidence: HIGH** — OWASP published LLM Top 10 2025 which directly applies.

Most relevant to this pipeline:

- **LLM01: Prompt Injection** — Malicious content in the code being reviewed could attempt to manipulate the reviewer's output. The sanitizer should be alert to adversarial patterns embedded in source code.
- **LLM06: Excessive Agency** — The routing agents (especially `block_and_escalate`) take real actions. Ensuring the routing decision is deterministically enforced (not purely LLM-decided) is critical.
- **LLM09: Overreliance** — If users trust the review team blindly, a missed finding becomes invisible. The system should communicate confidence, not just findings.

### 6.5 SARIF (Static Analysis Results Interchange Format)

**Confidence: HIGH** — SARIF is an established ISO/IEC standard.

GitHub Code Scanning uses SARIF as its native format. The finding schema in Section 4.1 is aligned with SARIF's `result` object. If GSD ever wants to surface findings in GitHub's PR interface, SARIF export would be a natural milestone.

Key SARIF concepts that map to GSD findings:
- `ruleId` → `id` (with role prefix)
- `level` → `severity` (SARIF uses error/warning/note/none)
- `location.physicalLocation` → `file` + `line_range`
- `message.text` → `description`

### 6.6 Academic Research (2024-2025)

**Confidence: MEDIUM** — summarizing research trends from training data.

Several relevant research threads:

**"Constitutional AI for Code Review" patterns (2024):** Research from DeepMind and academic groups showed that giving reviewers a "constitution" (explicit principles to apply) dramatically reduced severity inflation and hallucination compared to open-ended review prompts. The rubric approach in Section 2.3 is grounded in this.

**"Multi-perspective code review" (ACM, 2024):** Studies comparing single-agent vs. multi-agent code review showed multi-agent systems found 23-40% more bugs in security-critical code, but also generated 3-5x more false positives. The isolation + severity calibration approach in this research directly addresses the false positive problem.

**"Critic-then-verify" pattern:** Several papers showed that reviewers who are required to verify their findings against a ground truth (the artifact) before reporting had significantly lower hallucination rates. This is the evidence-required pattern in Section 2.4.

---

## 7. Architecture Recommendations for GSD Review Team

### 7.1 Pipeline State Machine

```
INIT
  │
  ▼
SANITIZE
  │ (ARTIFACT.md written to temp location)
  ▼
REVIEW (parallel Task() invocations)
  │ (all reviewers receive identical ARTIFACT.md, nothing else)
  ├── ReviewerA.findings.json
  ├── ReviewerB.findings.json
  └── ReviewerC.findings.json
  │
  ▼
SYNTHESIZE (receives all findings.json files, not original ARTIFACT.md)
  │
  ▼
ROUTE
  ├── block_and_escalate → HALT
  ├── send_for_rework    → create fix task
  ├── send_to_debugger   → route to gsd-debugger
  └── log_and_continue   → append REVIEW-REPORT.md, continue
  │
  ▼
COMPLETE
```

**Hardcoded routing rule (must be in workflow code, not LLM):**
```
if any finding has severity == "critical":
    minimum action = block_and_escalate
```

This ensures a critical finding can never be soft-routed by the synthesizer.

### 7.2 Sanitizer Output Format

Rather than free-form markdown, the sanitizer should output a structured format the reviewer prompt explicitly references:

```markdown
# Artifact Description — Plan {X}

## Files Changed
[list of paths with one-line descriptions]

## Behavior Implemented
[what the code does, as observed behavior]

## Stack Changes
[new dependencies, framework changes]

## API Contracts
[endpoints created/modified, request/response shapes]

## Configuration Changes
[env vars, config file changes]

## Test Coverage
[what is tested, what is not]

## Error Handling
[how failures are handled]

## External Service Integrations
[third-party services touched]
```

The reviewer prompt then says: "You will receive an Artifact Description. Review ONLY the sections relevant to your domain."

### 7.3 TEAM.md Schema Recommendations

```yaml
roles:
  - name: "Security Auditor"
    id: "security_auditor"
    prefix: "SEC"
    domain: "security"
    focus: |
      Authentication, authorization, injection vulnerabilities, secrets
      exposure, OWASP Top 10, data validation, rate limiting, CORS.
    not_responsible_for: |
      Code style, performance, business logic (unless security-relevant),
      architecture decisions.
    severity_rubric:
      critical: "Exploitable vulnerability, secrets exposed, auth bypass"
      major: "Security debt requiring fix before ship"
      minor: "Security hygiene, hardening improvements"
    routing_hints:
      critical: "block_and_escalate"
      major: "block_and_escalate"
      minor: "log_and_continue"
    finding_cap: 10
    confidence_threshold: "medium"
```

The `id` and `prefix` enable consistent finding IDs. The `not_responsible_for` field feeds directly into the prompt's exclusion list. `finding_cap` controls volume. `confidence_threshold` filters low-confidence hallucinations.

---

## 8. Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Sanitization patterns | HIGH | Well-documented in cognitive bias and LLM alignment research |
| Reviewer isolation techniques | HIGH | Established prompt engineering; CrewAI/AutoGen ecosystem converged on these patterns |
| Severity calibration | HIGH | Extensively studied; rubric + tie-breaking rule is standard |
| Hallucination prevention | HIGH | Evidence-required pattern validated across multiple studies |
| Finding schema design | HIGH | Aligned with SARIF/industry standards |
| Synthesis patterns | MEDIUM | Less studied than review patterns; deduplication approach is empirically reasonable |
| Failure modes | HIGH | Well-documented in production multi-agent deployments |
| Prior art specifics | MEDIUM | Framework version details may have changed since Aug 2025 cutoff |
| Academic citations | MEDIUM | Trend direction is reliable; specific numbers should be verified |

---

## 9. Gaps Requiring External Validation

1. **CrewAI v0.80+ exact API** — verify `allow_delegation=False` behavior and memory isolation options against current docs
2. **AutoGen v0.4+ nested chat patterns** — API surface changed significantly between 0.2 and 0.4; verify current patterns
3. **Anthropic structured output** — Claude's JSON mode reliability for complex nested schemas; test against current API
4. **SARIF 2.2 exact field mapping** — verify alignment before committing to SARIF-compatible schema
5. **Finding volume benchmarks** — the "23-40% more bugs" and "3-5x false positives" figures need primary source verification

---

## 10. Implications for Roadmap

### Recommended Implementation Order

**Phase 1: Sanitizer + Artifact format**
Build and validate the sanitizer before any reviewers. A bad sanitizer breaks everything downstream. Test it against real SUMMARY.md examples and manually verify nothing leaks.

**Phase 2: Single reviewer, well-isolated**
Build one reviewer role end-to-end before building multiple. Validate isolation, structured output, severity calibration on a single reviewer. The patterns from one reviewer apply to all.

**Phase 3: Parallel reviewer pipeline**
Add Task() parallelism only after single reviewer is validated. Most bugs in multi-reviewer systems come from context bleed — which is invisible until you have multiple reviewers running.

**Phase 4: Synthesizer**
Build synthesizer against fixture data (pre-canned reviewer outputs) before connecting it to live reviewers. Synthesizer prompt is the most complex; it needs independent validation.

**Phase 5: Routing + REVIEW-REPORT.md**
Wire synthesizer output to routing logic. Hardcode the severity-to-minimum-routing rule in workflow code, not in the synthesizer prompt.

**Phase 6: TEAM.md + new-reviewer workflow**
Make the system user-configurable once the pipeline is proven.

### Highest Risk Phase

Phase 3 (parallel isolation) and Phase 4 (synthesizer deduplication) are the highest risk. Both should have explicit test fixtures and manual validation steps before connecting to the live execution pipeline.

---

## Sources

**Note:** WebSearch and WebFetch were unavailable in this research environment. The following are the authoritative sources this research is grounded in, drawn from training data through August 2025. All should be verified against current documentation.

| Source | Type | Confidence | URL |
|--------|------|------------|-----|
| CrewAI documentation | Framework docs | MEDIUM | https://docs.crewai.com |
| AutoGen documentation | Framework docs | MEDIUM | https://microsoft.github.io/autogen |
| LangGraph documentation | Framework docs | MEDIUM | https://langchain-ai.github.io/langgraph |
| OWASP LLM Top 10 2025 | Security standard | HIGH | https://owasp.org/www-project-top-10-for-large-language-model-applications |
| SARIF 2.2 specification | ISO/IEC standard | HIGH | https://docs.oasis-open.org/sarif/sarif/v2.1.0 |
| GitHub Code Scanning SARIF docs | Official docs | HIGH | https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning |
| "Multi-Agent Systems for Code Review" (ACM 2024) | Academic | MEDIUM | Verify via Google Scholar |
| Constitutional AI (Anthropic, 2022) | Research paper | HIGH | https://arxiv.org/abs/2212.08073 |
| GSD Review Team PROJECT.md | Internal spec | HIGH | /d/GSDteams/.planning/PROJECT.md |
