---
version: 1
roles:
  - security-auditor
  - rules-lawyer
  - performance-analyst
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
