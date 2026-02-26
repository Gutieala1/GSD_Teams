<purpose>
Guides the user through creating a new reviewer role and appends it to `.planning/TEAM.md`.

Steps: check_team_md → gather_domain → gather_name → gather_criteria → gather_severity → decision_gate → write_role

Called by: `commands/gsd/new-reviewer.md` via the `/gsd:new-reviewer` slash command.
</purpose>

<inputs>
No inputs required. The workflow reads `.planning/TEAM.md` directly.
</inputs>

<step name="check_team_md" priority="first">
## Step 1: Check TEAM.md

Announce: "Let's create a new reviewer role for your team."

Check whether `.planning/TEAM.md` exists:

```bash
[ -f ".planning/TEAM.md" ] && echo "exists" || echo "missing"
```

If the file exists: read it with the Read tool. Note how many roles already exist (count `## Role:` headers).
Announce the current state: "Found N existing role(s) in .planning/TEAM.md." (or 0 if none).

If the file does not exist: do NOT create it yet. Note this — it will be created in the write_role step.
Announce: "No .planning/TEAM.md found — it will be created when we write the role."
</step>

<step name="gather_domain">
## Step 2: Gather Domain

Ask the user what domain this reviewer should focus on.

```
AskUserQuestion([
  {
    question: "What domain will this reviewer focus on?",
    header: "Domain",
    multiSelect: false,
    options: [
      { label: "Security", description: "Auth, injection, secrets, input validation" },
      { label: "Performance", description: "N+1 queries, unbounded loops, blocking calls" },
      { label: "Requirements", description: "Spec compliance, conventions, API contracts" },
      { label: "Custom", description: "I'll describe my own focus area" }
    ]
  }
])
```

If the user selects "Custom": ask a follow-up free-text question:
```
AskUserQuestion([
  {
    question: "Describe the focus area for this reviewer (one sentence):",
    header: "Custom Focus",
    multiSelect: false,
    options: [
      { label: "Type your focus area above", description: "Press enter when done" }
    ]
  }
])
```
(The user will use the "Other" / free-text path here — accept their free-text response as the focus area.)

Store: `domain_label` (e.g., "Security"), `focus_sentence` (one sentence description, e.g., "Security vulnerabilities and unsafe patterns").

Suggest a display name and slug:
- "Security" → display: "Security Auditor", slug: "security-auditor"
- "Performance" → display: "Performance Analyst", slug: "performance-analyst"
- "Requirements" → display: "Requirements Checker", slug: "requirements-checker"
- Custom → derive from the user's description: lowercase the key noun(s), join with hyphens

Announce the suggestion: "I'll name this role '[Display Name]' (slug: `[slug]`)."
</step>

<step name="gather_name">
## Step 3: Confirm Role Name

Ask the user to confirm or change the suggested role name.

```
AskUserQuestion([
  {
    question: "Confirm the role name (or select 'Change it' to use a different name):",
    header: "Role Name",
    multiSelect: false,
    options: [
      { label: "Use suggested name", description: "[Display Name] / [slug]" },
      { label: "Change it", description: "I'll provide a different name" }
    ]
  }
])
```

If "Change it": ask for the display name and derive slug (lowercase, replace spaces with hyphens).
```
AskUserQuestion([
  {
    question: "Enter the display name for this role (e.g., 'API Auditor'):",
    header: "Display Name",
    multiSelect: false,
    options: [
      { label: "Type the name above", description: "Example: API Auditor" }
    ]
  }
])
```

Store: `role_display_name`, `role_slug` (lowercase hyphenated version of display name).
</step>

<step name="gather_criteria">
## Step 4: Gather Review Criteria

Ask what this reviewer should check. Present domain-appropriate starter suggestions.

Build the options based on `domain_label`:

**If Security:**
```
AskUserQuestion([
  {
    question: "What should this reviewer check? (choose a starting set)",
    header: "Criteria",
    multiSelect: false,
    options: [
      { label: "Auth + injection + secrets", description: "Auth/authz, SQL injection, XSS, hardcoded secrets" },
      { label: "Input validation focus", description: "All user inputs, boundary checks, sanitization" },
      { label: "Dependencies + config", description: "Dep vulns, insecure defaults, misconfigs" },
      { label: "I'll list my own", description: "I'll describe my criteria" }
    ]
  }
])
```

**If Performance:**
```
AskUserQuestion([
  {
    question: "What should this reviewer check? (choose a starting set)",
    header: "Criteria",
    multiSelect: false,
    options: [
      { label: "N+1 + pagination + loops", description: "Query patterns, unbounded loops, missing pagination" },
      { label: "Async + blocking calls", description: "Sync where async needed, blocking main thread" },
      { label: "Memory + allocation", description: "Large in-memory collections, unbounded growth" },
      { label: "I'll list my own", description: "I'll describe my criteria" }
    ]
  }
])
```

**If Requirements or Custom:**
```
AskUserQuestion([
  {
    question: "What should this reviewer check? (choose a starting set)",
    header: "Criteria",
    multiSelect: false,
    options: [
      { label: "Plan vs. implementation", description: "Does implementation match stated requirements?" },
      { label: "API contracts + conventions", description: "API contracts honored, coding conventions followed" },
      { label: "Error handling patterns", description: "Error patterns consistent with existing codebase" },
      { label: "I'll list my own", description: "I'll describe my criteria" }
    ]
  }
])
```

If the user selects "I'll list my own": ask them to describe the criteria (accept free-text via "Other").

Based on the selection, store a `criteria_list` of 3-5 items as markdown list items (`- item text`).
For pre-defined options, expand the label into full criterion sentences. For example:
- "Auth + injection + secrets" → 4 items: Authentication and authorization logic / Input validation and sanitization / Secrets and credentials handling / SQL injection, XSS, and injection patterns
</step>

<step name="gather_severity">
## Step 5: Gather Severity Thresholds

Ask what qualifies as critical for this reviewer's domain.

```
AskUserQuestion([
  {
    question: "What makes a finding critical in this domain?",
    header: "Severity",
    multiSelect: false,
    options: [
      { label: "Deploy-stopper bugs", description: "Something that would cause data loss or outage if shipped" },
      { label: "Security breach risk", description: "Exploitable vulnerability or credential exposure" },
      { label: "Requirement violated", description: "A stated requirement is directly contradicted" },
      { label: "I'll define thresholds", description: "I'll describe critical/major/minor myself" }
    ]
  }
])
```

If the user selects "I'll define thresholds": accept free-text for each level via follow-up questions.

Based on the selection, store `severity_critical`, `severity_major`, `severity_minor` as example strings:

For pre-defined selections, map to domain-appropriate defaults:
- "Deploy-stopper bugs" → critical: "Logic error causing data loss or service outage", major: "Incorrect behavior that ships broken functionality", minor: "Suboptimal approach that still works"
- "Security breach risk" → critical: "Hardcoded secrets, SQL injection, missing auth on sensitive routes", major: "Missing input validation, insecure defaults, weak session handling", minor: "Missing security headers, verbose error messages, deprecated methods"
- "Requirement violated" → critical: "Implementation directly contradicts a stated requirement", major: "Missing required behavior, wrong API contract", minor: "Style deviation, naming inconsistency, missing doc comment"

```
AskUserQuestion([
  {
    question: "Use standard routing for findings?",
    header: "Routing",
    multiSelect: false,
    options: [
      { label: "Standard (recommended)", description: "critical → block, major → rework, minor → log" },
      { label: "Customize routing", description: "I'll set routing per severity level" }
    ]
  }
])
```

If "Standard (recommended)": use defaults — critical: block_and_escalate, major: send_for_rework, minor: log_and_continue.

If "Customize routing": ask for each level (3 separate questions or accept free-text).

Store: `routing_critical`, `routing_major`, `routing_minor`.
</step>

<step name="decision_gate">
## Step 6: Decision Gate — Preview and Confirm

Assemble the complete role definition markdown block from all collected values:

```
## Role: {role_display_name}

```yaml
name: {role_slug}
focus: {focus_sentence}
```

**What this role reviews:**
{criteria_list items, each as "- item"}

**Severity thresholds:**
- `critical`: {severity_critical}
- `major`: {severity_major}
- `minor`: {severity_minor}

**Routing hints:**
- Critical findings: `{routing_critical}`
- Major findings: `{routing_major}`
- Minor findings: `{routing_minor}`
```

Display the assembled role definition to the user:
"Here is the role definition that will be written to `.planning/TEAM.md`:"
[show the full markdown block]

Then ask for confirmation:

```
AskUserQuestion([
  {
    question: "Ready to write this role to .planning/TEAM.md?",
    header: "Confirm",
    multiSelect: false,
    options: [
      { label: "Create role", description: "Write the role definition to TEAM.md" },
      { label: "Start over", description: "Restart the conversation from the beginning" }
    ]
  }
])
```

If "Start over": restart from Step 2 (gather_domain). Do NOT write anything to disk.
If "Create role": proceed to write_role step.
</step>

<step name="write_role">
## Step 7: Write Role to TEAM.md

**If .planning/TEAM.md EXISTS:**

Read the current content. Then write the updated file with the new role appended:

1. Parse the YAML frontmatter `roles:` list. Add `{role_slug}` to the list.
2. Append a `---` separator and the new role definition to the end of the file.
3. Write the full updated content back to `.planning/TEAM.md`.

The appended block must follow this exact format (note the `---` separator and trailing newline):

```
---

## Role: {role_display_name}

```yaml
name: {role_slug}
focus: {focus_sentence}
```

**What this role reviews:**
{criteria_list}

**Severity thresholds:**
- `critical`: {severity_critical}
- `major`: {severity_major}
- `minor`: {severity_minor}

**Routing hints:**
- Critical findings: `{routing_critical}`
- Major findings: `{routing_major}`
- Minor findings: `{routing_minor}`
```

**If .planning/TEAM.md does NOT EXIST:**

Create it with this minimal content (stub header + the new role only):

```
---
version: 1
roles:
  - {role_slug}
---

# Review Team

Add reviewer roles below. Run `/gsd:new-reviewer` to create additional roles through a guided conversation.

---

## Role: {role_display_name}

```yaml
name: {role_slug}
focus: {focus_sentence}
```

**What this role reviews:**
{criteria_list}

**Severity thresholds:**
- `critical`: {severity_critical}
- `major`: {severity_major}
- `minor`: {severity_minor}

**Routing hints:**
- Critical findings: `{routing_critical}`
- Major findings: `{routing_major}`
- Minor findings: `{routing_minor}`
```

**After writing:**

Announce: "Role '{role_display_name}' written to `.planning/TEAM.md`."
Announce: "Run `/gsd:execute-phase` to use this reviewer in your next review pipeline."
</step>
