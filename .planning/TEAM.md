---
version: 2
roles:
  - security-auditor
  - rules-lawyer
  - performance-analyst
  - code-quality-checker
  - efficiency-auditor
---

# Review Team

Define your reviewer roles below. Each role runs in isolation — it sees only the sanitized
execution artifact, never the plan, executor reasoning, or prior summaries.

Run `/gsd:new-reviewer` to add a role through a guided conversation, or customize the
starter roles below directly.

---

## Role: Security Auditor

```yaml
name: security-auditor
focus: Security vulnerabilities and unsafe patterns
enabled: false
```

**What this role reviews:**
- Authentication and authorization logic
- Input validation and sanitization
- Secrets and credentials handling
- SQL injection, XSS, and injection patterns
- Dependency vulnerabilities introduced by stack changes

**Severity thresholds:**
- `critical`: Hardcoded secrets, SQL injection, missing auth on sensitive routes
- `major`: Missing input validation, insecure defaults, weak session handling
- `minor`: Missing security headers, verbose error messages, deprecated methods

**Routing hints:**
- Critical findings: `block_and_escalate`
- Major findings: `send_for_rework`
- Minor findings: `log_and_continue`

---

## Role: Rules Lawyer

```yaml
name: rules-lawyer
focus: Consistency with stated requirements and project conventions
enabled: false
```

**What this role reviews:**
- Do implemented behaviors match the plan's stated requirements?
- Are coding conventions followed consistently with the existing codebase?
- Are error handling patterns consistent with existing patterns?
- Are API contracts honored as specified?

**Severity thresholds:**
- `critical`: Implementation directly contradicts a stated requirement
- `major`: Missing required behavior, wrong API contract
- `minor`: Style deviation, naming inconsistency, missing doc comment

**Routing hints:**
- Critical findings: `block_and_escalate`
- Major findings: `send_for_rework`
- Minor findings: `log_and_continue`

---

## Role: Performance Analyst

```yaml
name: performance-analyst
focus: Performance implications of new code and architectural decisions
```

**What this role reviews:**
- N+1 query patterns in new database interactions
- Unbounded loops or O(n²) operations on large datasets
- Missing pagination on list endpoints
- Synchronous blocking calls where async is appropriate
- Memory allocation patterns (large in-memory collections)

**Severity thresholds:**
- `critical`: O(n²) on unbounded production data, blocking main thread
- `major`: Missing pagination, N+1 query pattern, sync where async required
- `minor`: Suboptimal algorithm choice on small/bounded data

**Routing hints:**
- Critical findings: `block_and_escalate`
- Major findings: `send_for_rework`
- Minor findings: `log_and_continue`

---

## Role: Code Quality Checker

```yaml
name: code-quality-checker
focus: Flags code quality issues and reports them for fixing
mode: advisory
trigger: post-phase
output_type: findings
enabled: true
```

**What this role reviews:**
- Does the implementation match the plan's stated requirements and tasks?
- Are coding conventions consistent with the existing codebase?
- Is error handling present and consistent with existing patterns?
- Are logging patterns used appropriately (not missing, not excessive)?
- Are there obvious gaps in test coverage for new code paths?

**Patterns to flag:**
- Missing requirement implementation: A task listed in PLAN.md is absent from the SUMMARY.md completion list or from actual code changes (e.g. PLAN says "add rate limiting to /login" but no rate limiter code appears in the diff)
- Unhandled error path: A function that can throw or return an error has no try/catch or error-return check (e.g. `fs.readFileSync(path)` called without a try/catch in a module with no upstream error boundary)
- Silent test gap: A new code path branches on a condition (if/switch) with no corresponding test case (e.g. a function with 3 branches where only 2 are exercised in the test file)

**Severity thresholds:**
- `critical`: Deploy-stopper bugs, requirement violated, or security breach risk
- `major`: Missing required behavior, inconsistent conventions, poor error handling
- `minor`: Minor style deviation, suboptimal logging, small coverage gap

**Calibration examples:**
- `critical`: PLAN.md requires email verification on signup, but the implemented registration handler marks the user immediately active without sending a verification email — a stated requirement is directly violated
- `major`: The `createOrder()` function is missing the input validation step described in the plan's task list; it accepts arbitrary product IDs without existence checks, inconsistent with the validation pattern used in `updateOrder()`
- `minor`: `parseConfig()` uses `console.log()` for debug output rather than the project's `logger` utility, inconsistent with the logging pattern used in the rest of the codebase

**Routing hints:**
- Critical findings: `block_and_escalate`
- Major findings: `send_for_rework`
- Minor findings: `log_and_continue`

---

## Role: Efficiency Auditor

```yaml
name: efficiency-auditor
focus: Flags prompt bloat and code inefficiencies that waste tokens or processing without improving output
mode: advisory
trigger: post-plan
output_type: findings
enabled: true
```

**What this role reviews:**
- Are workflow instruction blocks concise — do they contain redundant sentences or verbose rules that could be shortened without losing meaning?
- Are new code functions free of unnecessary intermediate variables, redundant conditionals, or over-abstracted logic that adds complexity without benefit?
- Are agent prompts free of duplicated context — do they repeat information the agent will already have in its role definition or phase context?
- Are new dependencies and imports justified — do they avoid duplicating built-in functionality or existing project utilities?
- Are loop and data transformation patterns efficient — do they avoid re-processing the same data multiple times when a single pass would suffice?

**Patterns to flag:**
- Duplicated context in prompt: The same information appears in more than one section of an agent prompt, causing the model to process identical tokens twice (e.g., the agent's `focus` is stated in `<objective>` and then repeated verbatim in the opening line of `<role_definition>`)
- Redundant single-use variable: A variable is assigned once and immediately returned/used on the next line with no intervening logic (e.g., `const result = compute(); return result;` where `return compute()` is equivalent)
- Repeated data traversal: The same collection is iterated in separate passes when all operations could combine into one (e.g., `items.filter(...).map(...)` as two sequential operations on the same input when one pass would suffice)

**Severity thresholds:**
- `critical`: Functional regression risk, prompt exceeds context limits, or blocking performance issue
- `major`: Significant redundancy that degrades quality without breaking it — e.g. prompts 30%+ longer than needed
- `minor`: Minor verbosity or small optimization opportunity with negligible impact

**Calibration examples:**
- `critical`: The `phase_context_content` block includes full ROADMAP.md verbatim (8,000+ tokens), pushing the spawned Task() past context limit — agent silently truncates inputs and produces a degraded result
- `major`: A workflow step repeats the full 12-line sanitization rules block in both step instructions and Task() prompt; removing duplication cuts each prompt by ~400 tokens with no information loss
- `minor`: A variable is constructed by string concatenation then immediately returned with no further use — could be inlined directly

**Routing hints:**
- Critical findings: `block_and_escalate`
- Major findings: `send_for_rework`
- Minor findings: `log_and_continue`
