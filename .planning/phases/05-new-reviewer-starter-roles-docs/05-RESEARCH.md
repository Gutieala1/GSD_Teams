# Phase 5: /gsd:new-reviewer + Starter Roles + Docs — Research

**Researched:** 2026-02-25
**Domain:** GSD command/workflow authoring, TEAM.md role format, install.sh extension patterns
**Confidence:** HIGH

---

## Summary

Phase 5 has three distinct deliverables: (1) production-ready starter roles in TEAM.md, (2) a `/gsd:new-reviewer` guided workflow that writes new roles to TEAM.md, and (3) README.md documentation plus a GSD version compatibility check in install.sh.

All source material was read directly from the existing codebase. The TEAM.md format, parser contract, command file structure, workflow conventions, AskUserQuestion patterns, and install.sh structure are all fully understood from first-party sources. No ambiguity remains on any critical implementation question. The one open concern from STATE.md — whether `reapply-patches` handles XML `<step>` blocks reliably — is addressed in the README documentation scope rather than requiring code investigation, since reapply-patches is a GSD built-in (not something this extension ships).

**Primary recommendation:** Treat the three plans as strictly independent deliverables: 05-01 upgrades TEAM.md/templates, 05-02 builds the new-reviewer command+workflow, 05-03 writes README + adds version check to install.sh. No shared state between plans.

---

## Standard Stack

### What This Phase Produces (not libraries)

This phase authors five new text files and modifies two existing files. There are no npm dependencies to add. All "libraries" are GSD conventions already in use.

| File | Type | Creates / Modifies |
|------|------|--------------------|
| `templates/TEAM.md` | Markdown | Modify — upgrade 3 roles from "example" to production-ready |
| `.planning/TEAM.md` | Markdown | Same upgrade (both copies must match) |
| `commands/gsd/new-reviewer.md` | GSD command | Create new |
| `workflows/new-reviewer.md` | GSD workflow | Create new |
| `README.md` | Markdown | Create new |
| `install.sh` | Bash | Modify — add version compatibility check |

### GSD Command File Format

Sourced from: `C:/Users/gutie/.claude/commands/gsd/new-project.md`, `settings.md`, `reapply-patches.md`

A GSD command file is a Markdown file with YAML frontmatter and execution_context references:

```markdown
---
name: gsd:new-reviewer
description: [short description]
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
[What this command does — shown to user at invocation]
</objective>

<execution_context>
@~/.claude/get-shit-done-review-team/workflows/new-reviewer.md
</execution_context>

<process>
Follow the new-reviewer workflow end-to-end.
Preserve all gates.
</process>
```

Key rules:
- `name:` must match the slash command (gsd:new-reviewer)
- `allowed-tools:` is an explicit allowlist — every tool used in the workflow must appear here
- `execution_context` uses `@` references to load workflow files — the path must resolve at Claude runtime
- The extension installs to `~/.claude/get-shit-done-review-team/` so the `@` reference path is `@~/.claude/get-shit-done-review-team/workflows/new-reviewer.md`
- Command files for this extension belong in `D:/GSDteams/commands/gsd/` and get copied to `C:/Users/gutie/.claude/commands/gsd/` by install.sh (currently install.sh does NOT copy commands/ — this is a gap to address in 05-03 or in 05-02 plan)

**CRITICAL GAP FOUND:** The current `install.sh` copies `agents/`, `workflows/`, and `templates/` — but does NOT copy `commands/gsd/`. The `new-reviewer.md` command file must be added to install.sh's copy logic. This is a 05-03 concern (or late 05-02).

### GSD Workflow File Format

Sourced from: `D:/GSDteams/workflows/review-team.md`, `C:/Users/gutie/.claude/get-shit-done/workflows/settings.md`

Workflow files use XML-tagged blocks, not YAML frontmatter:

```markdown
<purpose>
[What this workflow does — one paragraph]
</purpose>

<inputs>
[Parameters this workflow receives — documented as a list]
</inputs>

<step name="step_name" priority="first">
## Step N: [Title]

[Prose instructions + code blocks]
</step>

<step name="next_step">
## Step N+1: [Title]
...
</step>
```

Key rules:
- No YAML frontmatter (that's agent files, not workflow files)
- Steps use `<step name="...">` XML tags
- `priority="first"` on first step is a GSD convention for mandatory-first execution
- AskUserQuestion is called inline in step prose — not as pseudocode, as literal instruction
- Bash blocks use triple-backtick bash for shell commands
- The workflow file is loaded via `@` reference — it executes in the calling agent's context

### AskUserQuestion Convention

Sourced from: `C:/Users/gutie/.claude/get-shit-done/workflows/settings.md`, `discuss-phase.md`, `references/questioning.md`

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

Hard rules from `references/questioning.md`:
- Headers: **12 character maximum** (hard limit — "validation will reject them")
- Options per question: **2–4 options** (plus "Other" is added automatically)
- Decision gate before writing: must ask "Ready to create role?" before writing to TEAM.md
- `multiSelect: false` for single-choice questions (role builder never needs multiSelect)

---

## Architecture Patterns

### TEAM.md Role Format (Parser Contract)

Sourced from: `D:/GSDteams/workflows/review-team.md` — `validate_team` step + `spawn_reviewers` step

The parser (in `review-team.md` validate_team step) requires ALL THREE of these for a role to be valid:

1. A `## Role:` section header (the display name after the colon)
2. A YAML fenced code block containing a `name:` field (machine-readable slug)
3. At least one list item under `**What this role reviews:**`

Extraction in spawn_reviewers: the full text from `## Role: {name}` to the NEXT `## Role:` header (or EOF) is passed as `role_definition_text` to the reviewer agent.

The reviewer agent (gsd-reviewer.md Step 0) extracts these fields from `<role_definition>` tags:
- `name:` — YAML field → used as `reviewer` in findings + ID prefix derivation
- `focus:` — YAML field → used as `domain` in findings
- `**What this role reviews:**` list — the review checklist
- `**Severity thresholds:**` section — calibrates the 5-level rubric
- `**Routing hints:**` section — informs `suggested_routing` field
- `not_responsible_for` (optional) — scope exclusions; if absent, derived as "anything outside {focus domain}"
- ID prefix — first 3-4 uppercase characters of `name:` (SEC, LAW, PERF for starters)

### Complete Role Definition Template

This is the exact format the parser and reviewer agent expect:

```markdown
## Role: [Display Name]

```yaml
name: [slug-with-dashes]
focus: [One sentence domain description]
```

**What this role reviews:**
- [Checklist item 1]
- [Checklist item 2]
- [Checklist item 3]

**Severity thresholds:**
- `critical`: [Example that warrants stopping a deploy]
- `major`: [Example requiring fix before next plan]
- `minor`: [Example worth tracking but shippable]

**Routing hints:**
- Critical findings: `block_and_escalate`
- Major findings: `send_for_rework`
- Minor findings: `log_and_continue`
```

**Severity note from gsd-reviewer.md:** The reviewer uses 5 levels (critical/high/medium/low/info) but TEAM.md roles conventionally map to 3 threshold bands (critical/major/minor) with examples. The `major` threshold maps to `high` severity, and the examples guide the reviewer's calibration. This is an intentional design — TEAM.md is human-readable while the JSON schema uses the 5-level enum.

### Current State of TEAM.md Starter Roles

The current `templates/TEAM.md` and `.planning/TEAM.md` are identical and contain the "example" marker:

```markdown
> Example role — customize before use. Remove this callout when your role is ready.
```

Phase 5 Plan 01 must remove this callout from all 3 roles and verify each role is fully production-ready as-is — meaning a user can run the extension without editing TEAM.md and get useful findings.

### new-reviewer Workflow Structure

Based on ROLE-01, ROLE-02, ROLE-03, and GSD workflow patterns observed in discuss-phase.md and settings.md:

```
<step name="check_team_md" priority="first">
  - Check if .planning/TEAM.md exists; create from template if not
  - Announce: "Let's create a new reviewer role for your team."
</step>

<step name="gather_domain">
  - AskUserQuestion: "What domain?" (header: "Domain", ≤12 chars)
  - Options: Security | Performance | Requirements | Custom
  - If Custom: free-text input for focus area
</step>

<step name="gather_criteria">
  - AskUserQuestion: "What should this reviewer check?" (header: "Criteria")
  - Options: [2-4 domain-appropriate starters] | "I'll list my own"
  - Collect 3-5 review criteria items
</step>

<step name="gather_severity">
  - AskUserQuestion: "What's critical for this domain?" (header: "Severity")
  - Options: examples appropriate to chosen domain
  - Map to critical/major/minor thresholds
</step>

<step name="gather_routing">
  - Use defaults (critical → block_and_escalate, major → send_for_rework, minor → log_and_continue)
  - AskUserQuestion: "Routing preferences?" (header: "Routing")
  - Options: "Use defaults" | "Customize routing"
  - Most users will use defaults
</step>

<step name="decision_gate">
  - Display role preview (the markdown that will be written)
  - AskUserQuestion: "Ready to create this role?" (header: "Confirm")
  - Options: "Create role" | "Edit it first"
  - ROLE-02 requires this gate before writing
</step>

<step name="write_role">
  - Check if TEAM.md exists; create if not (ROLE-03)
  - Append role definition to TEAM.md
  - Update YAML frontmatter roles: list if present
  - Confirm: "Role written to .planning/TEAM.md"
</step>
```

### Role Name (slug) Generation

From gather_domain step, the workflow must derive a machine-readable slug for the YAML `name:` field. Convention from existing roles: lowercase, hyphen-separated (security-auditor, rules-lawyer, performance-analyst).

Workflow should suggest a slug based on the domain and let the user confirm or edit it.

### install.sh Version Compatibility Check

Sourced from: `D:/GSDteams/install.sh` (Section 2 = GSD detection), `C:/Users/gutie/.claude/get-shit-done/VERSION` = `1.19.2`

The current GSD version is 1.19.2. The extension was built and tested against this version.

GSD VERSION file location: `$GSD_DIR/get-shit-done/VERSION`

Bash version detection:

```bash
GSD_VERSION=$(cat "$GSD_DIR/get-shit-done/VERSION" 2>/dev/null || echo "unknown")
```

Semver comparison in bash without external tools (using sort -V):

```bash
version_in_range() {
  local ver="$1" min="$2" max="$3"
  local lowest
  lowest=$(printf '%s\n' "$min" "$ver" | sort -V | head -1)
  [ "$lowest" = "$min" ] || return 1
  local highest
  highest=$(printf '%s\n' "$ver" "$max" | sort -V | tail -1)
  [ "$highest" = "$max" ] || return 1
  return 0
}
```

Target compatibility range: 1.19.x (current tested version). A reasonable conservative range is `>= 1.19.0, < 2.0.0` to catch major version breaks. Warn (not error) on mismatch — INST-04 says "warns on mismatch", not "exits on mismatch".

Where to add the check: After Section 2 (GSD location detection), before Section 3 (project root detection). The check reads VERSION and emits a warning if outside range — it does NOT call exit.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Semver comparison in bash | Custom awk/grep parser | `sort -V` (GNU coreutils, available everywhere) | sort -V handles semver correctly; regex approaches fail on edge cases |
| Role name slug from display name | Complex string transform | Simple lowercase+hyphen substitution inline in workflow prose | The workflow instructs Claude to derive it — no code needed |
| Appending to TEAM.md | File parsing/rebuilding | Read-then-Write append (same pattern as REVIEW-REPORT.md in Phase 4) | Already proven pattern in this codebase |
| Creating TEAM.md from scratch | Custom template string in workflow | Copy from `templates/TEAM.md` via `cp` OR write a minimal role-only stub | Templates directory already exists |
| Command file installation | New install logic | Add one `cp` line to install.sh Section 5 | Minor addition to proven pattern |

**Key insight:** The role builder is a guided conversation workflow — Claude does the synthesis from user answers. There is no parsing or template engine to build. The workflow instructs Claude to format the collected information as a role definition markdown block.

---

## Common Pitfalls

### Pitfall 1: TEAM.md Frontmatter Roles List Drift

**What goes wrong:** The YAML frontmatter at the top of TEAM.md contains a `roles:` list that names all role slugs. If `new-reviewer` only appends the `## Role:` section but forgets to update the frontmatter, the roles list falls out of sync.

**Why it happens:** The parser (validate_team) does NOT read the frontmatter `roles:` list — it splits on `## Role:` headers. But the frontmatter exists for other purposes (version tracking, potentially future tooling). If new roles are added without updating frontmatter, the file looks inconsistent.

**How to avoid:** The write_role step should read the existing TEAM.md, parse the frontmatter, add the new slug to the `roles:` list, and rewrite the full file. Alternatively, accept frontmatter drift as a known limitation and document it.

**Recommendation:** Update frontmatter in the write_role step — it's a simple string append to the YAML list. The Read-then-Write pattern handles this.

### Pitfall 2: Role Display Name vs. YAML name Field Mismatch

**What goes wrong:** `## Role: Security Auditor` (display name) vs. `name: security-auditor` (YAML slug). The reviewer agent uses the YAML `name:` field for findings output. If the workflow asks for display name only and auto-derives slug incorrectly, findings will have wrong `reviewer` field values.

**Why it happens:** Two representations of the same thing. The workflow needs to capture both and confirm the slug with the user.

**How to avoid:** Decision gate step shows both the display name and the derived slug. User can edit before writing.

### Pitfall 3: Starter Roles Still Have "Example" Callout

**What goes wrong:** Current TEAM.md has `> Example role — customize before use.` in all 3 roles. If Phase 5 Plan 01 doesn't explicitly remove these callouts, they ship to users and undermine confidence in the starters.

**Why it happens:** Phase 1 created the template as examples intentionally. Phase 5 is the moment to graduate them to production-ready.

**How to avoid:** Plan 01 must explicitly remove the callout blockquotes from all 3 roles in BOTH `templates/TEAM.md` and `.planning/TEAM.md`. These are two separate files — both must be updated.

### Pitfall 4: Command File Install Missing

**What goes wrong:** install.sh Section 5 does not copy `commands/gsd/` files. The `new-reviewer.md` command file lives in `D:/GSDteams/commands/gsd/` but never reaches `C:/Users/gutie/.claude/commands/gsd/`.

**Why it happens:** Phase 1 set up the install.sh before any commands existed. The copy logic covers agents/, workflows/, templates/ — commands/ was not in scope then.

**How to avoid:** Plan 05-03 (install.sh update) must add a `commands/gsd/` copy block analogous to the existing agents/workflows copy blocks. The target is `$GSD_DIR/commands/gsd/` (same install location as existing GSD commands).

### Pitfall 5: AskUserQuestion Header Exceeds 12 Characters

**What goes wrong:** GSD validation rejects AskUserQuestion headers longer than 12 characters. This is a hard limit from `references/questioning.md`.

**Why it happens:** Developers write natural-language headers ("Domain Focus", "Review Criteria") without checking the limit.

**How to avoid:** Every AskUserQuestion in new-reviewer.md must have headers of 12 chars or less. Examples: "Domain" (6), "Criteria" (8), "Severity" (8), "Routing" (7), "Role Name" (9), "Confirm" (7).

### Pitfall 6: reapply-patches Reliability (STATE.md Open Concern)

**What goes wrong:** STATE.md flags: "Does AI merge in reapply-patches handle XML `<step>` blocks reliably across GSD version changes?"

**Why it matters for Phase 5:** The README must document the post-update procedure. The open concern is about whether `reapply-patches` reliably handles the `review_team_gate` step block that patch-execute-plan.py inserted.

**Resolution for Phase 5:** This is a documentation concern, not a code concern. The README should document the reapply-patches procedure but also note that patch verification is the user's responsibility. The `reapply-patches` workflow is a GSD built-in — this extension cannot improve it. Document it clearly and close the concern.

---

## Code Examples

### Complete Production-Ready Security Auditor Role

```markdown
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
```

(Remove the `> Example role — customize before use.` callout. This is the only change needed to make this role production-ready — the content is already complete and specific.)

### Complete Production-Ready Rules Lawyer Role

The Rules Lawyer role needs one improvement beyond callout removal: "Are coding conventions from CONVENTIONS.md followed?" is project-specific. Rephrase to "Are coding conventions followed (as observable from what was built)?" to be universally applicable.

```markdown
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
```

### Complete Production-Ready Performance Analyst Role

Content is already solid. Remove callout only.

```markdown
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
```

### GSD Command File for new-reviewer

```markdown
---
name: gsd:new-reviewer
description: Add a reviewer role to TEAM.md through a guided conversation
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
Add a new reviewer role to `.planning/TEAM.md` through a guided conversation.

Walks through: domain → review criteria → severity thresholds → routing → confirmation → write.

**Creates or updates:** `.planning/TEAM.md`
</objective>

<execution_context>
@~/.claude/get-shit-done-review-team/workflows/new-reviewer.md
</execution_context>

<process>
Follow the new-reviewer workflow end-to-end.
Preserve all gates including the decision gate before writing.
</process>
```

### install.sh Version Check (Section 2.5 — after GSD detection)

```bash
# ------------------------------------------------------------------------------
# Section 2.5: GSD version compatibility check
# ------------------------------------------------------------------------------
GSD_MIN_VERSION="1.19.0"
GSD_MAX_VERSION="1.99.99"

GSD_VERSION=$(cat "$GSD_DIR/get-shit-done/VERSION" 2>/dev/null || echo "unknown")

if [ "$GSD_VERSION" = "unknown" ]; then
  echo "  [WARN] Could not read GSD VERSION file — skipping compatibility check"
else
  # Use sort -V (version sort) for semver comparison
  # In range if: min <= version AND version <= max
  LOWEST=$(printf '%s\n' "$GSD_MIN_VERSION" "$GSD_VERSION" | sort -V | head -1)
  HIGHEST=$(printf '%s\n' "$GSD_VERSION" "$GSD_MAX_VERSION" | sort -V | tail -1)

  if [ "$LOWEST" = "$GSD_MIN_VERSION" ] && [ "$HIGHEST" = "$GSD_MAX_VERSION" ]; then
    echo "  [OK] GSD version: $GSD_VERSION (compatible range: $GSD_MIN_VERSION – $GSD_MAX_VERSION)"
  else
    echo ""
    echo "  [WARN] GSD version $GSD_VERSION is outside the tested range ($GSD_MIN_VERSION – $GSD_MAX_VERSION)"
    echo "         The extension may still work, but has not been tested with this version."
    echo "         Proceeding with installation..."
    echo ""
  fi
fi
```

### install.sh Commands Copy (missing, must add to Section 5)

```bash
# Copy commands/gsd/*.md if any exist
if ls "$EXT_DIR/commands/gsd/"*.md >/dev/null 2>&1; then
  mkdir -p "$GSD_DIR/commands/gsd"
  cp "$EXT_DIR/commands/gsd/"*.md "$GSD_DIR/commands/gsd/"
  echo "  [OK] commands/gsd/*.md copied"
else
  echo "  [SKIP] No commands/gsd/*.md files found"
fi
```

---

## TEAM.md Starter Roles — Complete Field Analysis

What each field must contain for the starter roles to be immediately usable (no user editing required):

### Security Auditor
- **name:** `security-auditor`
- **focus:** `Security vulnerabilities and unsafe patterns`
- **ID prefix** (auto-derived): `SEC`
- **What this role reviews:** 5 items covering auth, input validation, secrets, injection, dependency vulns — all observable in ARTIFACT.md without code access
- **Severity calibration:** All 3 thresholds have concrete examples that map to deploy-stopping vs. shippable
- **Status:** READY — only change is removing the "Example role" callout

### Rules Lawyer
- **name:** `rules-lawyer`
- **focus:** `Consistency with stated requirements and project conventions`
- **ID prefix** (auto-derived): `LAW`
- **What this role reviews:** 4 items — needs minor edit: "CONVENTIONS.md" reference should be generalized
- **Severity calibration:** All 3 thresholds have concrete examples
- **Status:** NEARLY READY — one criterion needs minor rewrite for universal applicability

### Performance Analyst
- **name:** `performance-analyst`
- **focus:** `Performance implications of new code and architectural decisions`
- **ID prefix** (auto-derived): `PERF`
- **What this role reviews:** 5 items covering N+1, O(n²), pagination, blocking, memory — all observable in ARTIFACT.md
- **Severity calibration:** All 3 thresholds have concrete, specific examples
- **Status:** READY — only change is removing the "Example role" callout

---

## Plan Boundaries (What Each Plan Delivers)

### Plan 05-01: Starter Roles + Role Template Format
**Scope:** Upgrade TEAM.md to production-ready in both `templates/TEAM.md` and `.planning/TEAM.md`
- Remove "Example role — customize before use." callout from all 3 roles
- Fix Rules Lawyer criterion (CONVENTIONS.md reference → generalized)
- Verify all 3 roles pass validate_team logic (## Role: header + YAML name: + criteria items)
- No new files. Two files modified.

**Decision:** Both `templates/TEAM.md` and `.planning/TEAM.md` must be updated — they are separate copies and must stay in sync.

### Plan 05-02: new-reviewer Workflow + Command File
**Scope:** Create `workflows/new-reviewer.md` + `commands/gsd/new-reviewer.md`
- 6-step workflow: check_team_md → gather_domain → gather_criteria → gather_severity → gather_routing → decision_gate → write_role
- AskUserQuestion at each step (headers ≤12 chars, 2-4 options)
- Decision gate before writing (ROLE-02)
- Appends to TEAM.md; creates it if absent (ROLE-03)
- Updates YAML frontmatter roles: list when appending
- Command file with correct allowed-tools list

**Note:** Command file path at runtime is `@~/.claude/get-shit-done-review-team/workflows/new-reviewer.md` (installed extension path, not D:/GSDteams source path).

### Plan 05-03: README.md + Version Check in install.sh
**Scope:** Create `README.md` + modify `install.sh`
- Add Section 2.5 version check to install.sh (warn, not error, on mismatch)
- Add commands/gsd copy block to install.sh Section 5
- Create README.md covering: installation, post-update reapply-patches procedure, TEAM.md format reference, first-run walkthrough
- README addresses INST-03 requirement and closes the reapply-patches open concern from STATE.md

---

## README.md Required Sections (INST-03)

The README must document:
1. **Installation** — `bash install.sh` from project root, prerequisites (python3), GSD compatibility range
2. **Post-`/gsd:update` procedure** — Run `bash install.sh` again (re-patches execute-plan.md) OR run `/gsd:reapply-patches` if the user manually modified GSD files. Clarify that `/gsd:update` wipes `commands/gsd/` and extension files must be reinstalled.
3. **TEAM.md setup** — What TEAM.md is, how the parser validates roles, role format reference
4. **First-run walkthrough** — Enable in `/gsd:settings`, verify TEAM.md, run a plan, see REVIEW-REPORT.md

**Post-update nuance:** `/gsd:update` wipes `commands/gsd/` and `get-shit-done/`. This extension's files land in `commands/gsd/` (the new-reviewer command) and `get-shit-done-review-team/` (agents/workflows). The `get-shit-done-review-team/` directory is NOT wiped by GSD update (GSD only wipes its own directories). However, the patched `execute-plan.md` IS wiped. So: after `/gsd:update`, re-run `bash install.sh` to reapply the execute-plan patch and restore the new-reviewer command. The `/gsd:reapply-patches` command handles GSD files that were directly modified — this extension uses a different mechanism (re-run install.sh).

---

## Open Questions

1. **Should new-reviewer create TEAM.md from scratch or only append?**
   - What we know: ROLE-03 says "creates TEAM.md if it doesn't exist"
   - What's clear: When creating from scratch, write a minimal header + the new role (not the full 3-role template)
   - Recommendation: On create-from-scratch, write a minimal TEAM.md with just the header boilerplate and the new role. Do not copy all 3 starters (user might not want them). Reference: "Run `/gsd:new-reviewer` to add a role" → implies an empty TEAM.md is valid.

2. **Does the new-reviewer command need `Glob` or `Grep` tools?**
   - What we know: The workflow only reads TEAM.md (Read) and writes to it (Write). No file searching needed.
   - Recommendation: allowed-tools = Read, Write, Bash (for date/timestamp), AskUserQuestion. No Glob or Grep needed.

3. **Should gather_routing be skippable?**
   - What we know: All 3 starter roles use identical routing (critical→block_and_escalate, major→send_for_rework, minor→log_and_continue). This is the logical default.
   - Recommendation: Present routing step with "Use standard routing (recommended)" as the first option. Only ask for customization if user selects "Customize". This satisfies ROLE-02's "2-4 options" constraint while not forcing unnecessary questions.

---

## Sources

### Primary (HIGH confidence)
- `D:/GSDteams/workflows/review-team.md` — validate_team and spawn_reviewers steps: parser contract (3-field validation), role extraction logic, how role_definition_text is assembled
- `D:/GSDteams/agents/gsd-reviewer.md` — Step 0 field extraction: all 5 fields (name, focus, checklist, not_responsible_for, ID prefix), how role definitions are consumed at review time
- `D:/GSDteams/schemas/finding-schema.md` — Full field reference, severity rubric, routing destinations, ID prefix table (SEC/LAW/PERF confirmed)
- `D:/GSDteams/templates/TEAM.md` and `.planning/TEAM.md` — Current role format, confirmed identical content
- `D:/GSDteams/install.sh` — Current install structure: 9 sections, GSD detection pattern, file copy logic, missing commands/ copy
- `C:/Users/gutie/.claude/commands/gsd/new-project.md` — Command file format (frontmatter, allowed-tools, execution_context, process)
- `C:/Users/gutie/.claude/commands/gsd/settings.md` — Minimal command file pattern
- `C:/Users/gutie/.claude/get-shit-done/workflows/settings.md` — AskUserQuestion multi-question format
- `C:/Users/gutie/.claude/get-shit-done/workflows/discuss-phase.md` — Adaptive questioning loop, decision gate pattern, 12-char header constraint in practice
- `C:/Users/gutie/.claude/get-shit-done/references/questioning.md` — 12-char header hard limit, 2-4 options rule, decision gate pattern
- `C:/Users/gutie/.claude/get-shit-done/VERSION` — Current GSD version: 1.19.2
- `D:/GSDteams/.planning/STATE.md` — Accumulated decisions, open concern about reapply-patches

### Secondary (MEDIUM confidence)
- `C:/Users/gutie/.claude/commands/gsd/reapply-patches.md` — Post-update procedure; how reapply-patches works (backs up user patches, merges after update). Informs README documentation.
- `C:/Users/gutie/.claude/get-shit-done/workflows/update.md` — What /gsd:update wipes (commands/gsd/, get-shit-done/ directories). Informs README post-update section.

---

## Metadata

**Confidence breakdown:**
- TEAM.md role format: HIGH — read directly from the parser source (validate_team step) and consumer source (gsd-reviewer.md Step 0)
- Command file format: HIGH — read 3 real examples from the installed GSD commands directory
- Workflow file format: HIGH — review-team.md is the canonical example in this codebase
- AskUserQuestion conventions: HIGH — read from references/questioning.md (the authoritative source) + 3 workflow examples
- install.sh structure: HIGH — read the actual install.sh; gap identified (commands/ not copied)
- Version compatibility range: MEDIUM — 1.19.2 is confirmed current; `>= 1.19.0, < 2.0.0` is a reasonable range, not tested exhaustively
- Starter role content quality: HIGH — content verified against 5-field reviewer contract from gsd-reviewer.md Step 0
- Post-update behavior: MEDIUM — inferred from update.md and reapply-patches.md content; not empirically tested

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (stable GSD conventions; GSD version check range may need update if GSD releases 2.x)
