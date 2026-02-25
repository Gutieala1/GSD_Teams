# Phase 1: Extension Scaffold + GSD Integration — Research

**Researched:** 2026-02-25
**Domain:** GSD extension file layout, core file patching, config schema, install scripting
**Confidence:** HIGH — all findings verified directly from GSD v1.19.2 source (zip extraction + existing planning files)

---

## Summary

Phase 1 establishes the extension skeleton and wires it into the GSD execution pipeline. The work is four discrete tasks: repo structure + TEAM.md template, patching `execute-plan.md` with the `review_team_gate` step, patching `settings.md` with the 7th toggle, and writing `install.sh` to deliver and apply everything.

All four tasks operate on known, stable artifacts. The exact text of every insertion point has been extracted directly from GSD v1.19.2. The config schema is fully understood. The only judgment call is the TEAM.md role format design, which this research documents as a recommendation. There are no unknowns that would block planning.

**Primary recommendation:** Pattern-based insertion anchored on `<step name="offer_next">` is the right approach for `install.sh`. Use Python (not sed) for multi-line insertion to avoid shell quoting nightmares. The settings.md patch must spread existing workflow keys — this is a hard requirement from REQUIREMENTS.md (INT-05).

---

## 1. Exact Insertion Point in execute-plan.md

**Confidence:** HIGH — extracted directly from zip

### The Step Sequence (lines 378–427 in v1.19.2)

```
line 378: <step name="issues_review_gate">
line 380: </step>
line 382: <step name="update_roadmap">
line 387: </step>
line 389: <step name="git_commit_metadata">
line 395: </step>
line 397: <step name="update_codebase_map">
line 410: </step>
line 411: (blank)
line 412: <step name="offer_next">     ← INSERT review_team_gate BEFORE THIS LINE
...
line 427: </step>
```

### Exact Text of update_codebase_map Step (lines 397–411)

```xml
<step name="update_codebase_map">
If .planning/codebase/ doesn't exist: skip.

```bash
FIRST_TASK=$(git log --oneline --grep="feat({phase}-{plan}):" --grep="fix({phase}-{plan}):" --grep="test({phase}-{plan}):" --reverse | head -1 | cut -d' ' -f1)
git diff --name-only ${FIRST_TASK}^..HEAD 2>/dev/null
```

Update only structural changes: new src/ dir → STRUCTURE.md | deps → STACK.md | file pattern → CONVENTIONS.md | API client → INTEGRATIONS.md | config → STACK.md | renamed → update paths. Skip code-only/bugfix/content changes.

```bash
node ~/.claude/get-shit-done/bin/gsd-tools.cjs commit "" --files .planning/codebase/*.md --amend
```
</step>
```

### Exact Text of offer_next Step Opening (lines 412–427)

```xml
<step name="offer_next">
If `USER_SETUP_CREATED=true`: display `⚠️ USER SETUP REQUIRED` with path + env/config tasks at TOP.

```bash
ls -1 .planning/phases/[current-phase-dir]/*-PLAN.md 2>/dev/null | wc -l
ls -1 .planning/phases/[current-phase-dir]/*-SUMMARY.md 2>/dev/null | wc -l
```

| Condition | Route | Action |
|-----------|-------|--------|
| summaries < plans | **A: More plans** | Find next PLAN without SUMMARY. Yolo: auto-continue. Interactive: show next plan, suggest `/gsd:execute-phase {phase}` + `/gsd:verify-work`. STOP here. |
| summaries = plans, current < highest phase | **B: Phase done** | Show completion, suggest `/gsd:plan-phase {Z+1}` + `/gsd:verify-work {Z}` + `/gsd:discuss-phase {Z+1}` |
| summaries = plans, current = highest phase | **C: Milestone done** | Show banner, suggest `/gsd:complete-milestone` + `/gsd:verify-work` + `/gsd:add-phase` |

All routes: `/clear` first for fresh context.
</step>
```

### Pattern Anchor for install.sh

The anchor string is the literal text `<step name="offer_next">`. This string appears exactly once in the file. The insertion goes on the line immediately before this anchor.

Confirmed: this anchor is uniquely identifiable in the file — grep returns exactly one match.

---

## 2. Exact Text of settings.md That Needs Patching

**Confidence:** HIGH — extracted directly from zip (full 200-line file)

### Current AskUserQuestion Block (present_settings step)

The settings workflow presents exactly **6 questions** via a single `AskUserQuestion` call:

```
AskUserQuestion([
  { question: "Which model profile for agents?", header: "Model", ... },
  { question: "Spawn Plan Researcher?", header: "Research", ... },
  { question: "Spawn Plan Checker?", header: "Plan Check", ... },
  { question: "Spawn Execution Verifier?", header: "Verifier", ... },
  { question: "Auto-advance pipeline?", header: "Auto", ... },
  { question: "Git branching strategy?", header: "Branching", ... }
])
```

The extension adds a **7th question** after the 6th (Branching). The patch must insert a new object into the array immediately before the closing `])` of the AskUserQuestion call.

**The exact closing line to anchor on:**

```javascript
  }
])
```

...which closes the Branching question object and the array. The new question object goes between the closing `}` of the Branching question and the `])` closing.

However, a safer anchor is the unique string that closes the Branching question's last option:
```
      { label: "Per Milestone", description: "Create branch for entire milestone (gsd/{version}-{name})" }
```

The 7th question to insert:
```javascript
  ,
  {
    question: "Spawn Review Team? (multi-agent review after each plan executes)",
    header: "Review Team",
    multiSelect: false,
    options: [
      { label: "No (Default)", description: "Skip review pipeline — standard execution" },
      { label: "Yes", description: "After each plan: sanitize output, spawn reviewers, synthesize findings" }
    ]
  }
```

**Note:** The `header` field value must be ≤12 chars (GSD questioning convention). "Review Team" is 11 chars — valid.

### Current update_config Step (exact text)

```json
{
  ...existing_config,
  "model_profile": "quality" | "balanced" | "budget",
  "workflow": {
    "research": true/false,
    "plan_check": true/false,
    "verifier": true/false,
    "auto_advance": true/false
  },
  "git": {
    "branching_strategy": "none" | "phase" | "milestone"
  }
}
```

**Critical problem (INT-05):** The current `update_config` step writes a COMPLETE `workflow` object with only the 4 known keys. If a user has `review_team: true` in config and runs `/gsd:settings` with the unpatched version, `review_team` is silently dropped.

**The patched update_config step must write:**

```json
{
  ...existing_config,
  "model_profile": "quality" | "balanced" | "budget",
  "workflow": {
    ...existing_config.workflow,
    "research": true/false,
    "plan_check": true/false,
    "verifier": true/false,
    "auto_advance": true/false,
    "review_team": true/false
  },
  "git": {
    "branching_strategy": "none" | "phase" | "milestone"
  }
}
```

The `...existing_config.workflow` spread preserves any future extension keys. The `review_team` field is then explicitly set from the user's choice in the 7th question.

### Current save_as_defaults Step

The `save_as_defaults` step also writes a `workflow` object to `~/.gsd/defaults.json`. The same spread requirement applies — it must include `review_team` and spread any unknown keys:

```json
{
  "mode": <current>,
  "depth": <current>,
  "model_profile": <current>,
  "commit_docs": <current>,
  "parallelization": <current>,
  "branching_strategy": <current>,
  "workflow": {
    ...existing_workflow,
    "research": <current>,
    "plan_check": <current>,
    "verifier": <current>,
    "auto_advance": <current>,
    "review_team": <current>
  }
}
```

### Current success_criteria (must be updated too)

```
- [ ] User presented with 6 settings (profile + 4 workflow toggles + git branching)
```

Patch changes this to 7 settings. The success_criteria block is the last section in settings.md — easiest to anchor on its known text.

---

## 3. review_team_gate Step Design

**Confidence:** HIGH — based on verified patterns from GSD-EXTENSION-ARCH.md and direct file inspection

### The Step to Insert

This is the complete `review_team_gate` step that install.sh inserts before `<step name="offer_next">`:

```xml
<step name="review_team_gate">
Check whether Review Team pipeline should run:

```bash
REVIEW_TEAM_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.review_team // false')
```

If `REVIEW_TEAM_ENABLED` is not `"true"`: skip this step entirely — no output, no log.

If `REVIEW_TEAM_ENABLED` is `"true"`:
- Check that `.planning/TEAM.md` exists:
  ```bash
  [ -f .planning/TEAM.md ] && echo "EXISTS" || echo "MISSING"
  ```
- If TEAM.md is missing: log `Review Team: skipped (no .planning/TEAM.md found — run /gsd:new-reviewer to create your first role)` and continue to `offer_next`. Do NOT block execution.
- If TEAM.md exists: load and execute the review pipeline:
  ```
  @~/.claude/get-shit-done-review-team/workflows/review-team.md
  ```
  Pass: current SUMMARY.md path, phase identifier, plan identifier.
</step>
```

### Reading CONFIG_CONTENT

`CONFIG_CONTENT` is already available in `execute-plan.md` via the `init_context` step:

```bash
INIT=$(node ~/.claude/get-shit-done/bin/gsd-tools.cjs init execute-phase "${PHASE}" --include state,config)
CONFIG_CONTENT=$(echo "$INIT" | jq -r '.config_content // empty')
```

No gsd-tools changes required. The `review_team_gate` step simply reads `CONFIG_CONTENT` which is already in scope.

### Skip-When-Off Behavior

When `workflow.review_team` is `false` (or absent), the step must produce **zero output** — no banner, no log message, nothing. This is a hard requirement. The toggle must be invisible when off.

When `workflow.review_team` is `true` but TEAM.md is missing, the log message must be:
```
Review Team: skipped (no .planning/TEAM.md found — run /gsd:new-reviewer to create your first role)
```

---

## 4. TEAM.md Format Design

**Confidence:** MEDIUM — no prior GSD TEAM.md exists; design derived from PROJECT.md requirements + GSD file conventions

### Design Principles

1. **Human-readable first** — users edit this file directly; it must be scannable
2. **Machine-parseable second** — review-team.md workflow must extract role definitions programmatically
3. **Markdown with YAML blocks** — consistent with GSD's VERIFICATION.md frontmatter pattern
4. **Fenced sections per role** — each role is self-contained and independently parseable

### Recommended TEAM.md Schema

The TEAM.md file uses a top-level YAML frontmatter for file metadata, followed by one Markdown section per role. Each role section uses a YAML code block for machine-readable data followed by prose description.

```markdown
---
version: 1
team: [project-name]
roles:
  - security-auditor
  - performance-analyst
---

# Review Team

Define your reviewer roles below. Each role runs in isolation — it sees only the sanitized
execution artifact, never the plan, executor reasoning, or prior summaries.

Run `/gsd:new-reviewer` to add a role through a guided conversation.

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
- Are coding conventions from CONVENTIONS.md followed?
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
```

### Machine-Parsing Pattern

The review-team.md workflow (Phase 2) extracts roles by:
1. Splitting on `## Role:` section headers
2. Extracting the YAML code block from each section (the `name` and `focus` fields)
3. Passing the full section content as `<role_definition>` to the reviewer agent

The YAML block inside each role section is the machine-readable anchor. The prose below it is the content passed to the reviewer.

### TEAM.md Validation Rules

A valid TEAM.md must have:
- At least one `## Role:` section
- Each role section must have a YAML block with `name` field
- Each role section must have at least one `**What this role reviews:**` list item

Invalid TEAM.md conditions (cause pipeline to halt with error):
- File exists but has zero `## Role:` sections
- A role section has no YAML block (name cannot be extracted)

### Starter Template Content for Phase 1

The Phase 1 TEAM.md starter template ships with the 3 example roles shown above, but **commented out** with a note directing users to uncomment or run `/gsd:new-reviewer`. This satisfies REQUIREMENTS.md TEAM-04 ("3 commented example roles").

Actually — re-reading ROADMAP.md Phase 1 success criteria: "`.planning/TEAM.md` starter template exists with 3 commented example roles." Commented here means the roles should be present but marked as inactive/example so users know to customize them.

**Implementation choice:** Use a prominent comment block at the top, and wrap each example role with an `<!-- Example: uncomment and customize -->` HTML comment (which renders as invisible in Markdown but is visible in raw text edit). Alternatively, prefix each example role header with `<!-- ` and close with `-->`.

**Simpler approach (recommended):** Ship the roles fully visible but with clear `> Example role — customize before use` blockquote callouts under each role header. HTML comments in Markdown are less discoverable. Visible callouts teach the format better.

---

## 5. install.sh Design

**Confidence:** HIGH — based on GSD-EXTENSION-ARCH.md decisions + verified patterns

### What install.sh Must Do

1. Detect GSD install location (global `~/.claude/` or local `./.claude/`)
2. Copy extension files to correct locations
3. Add `workflow.review_team: false` to `.planning/config.json` if it exists
4. Apply the `review_team_gate` patch to `execute-plan.md`
5. Apply the settings.md patch
6. Warn the user about `/gsd:reapply-patches` requirement after future updates

### File Copy Operations

```bash
# Extension source (wherever the repo is cloned)
EXT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect GSD install location
if [ -d "$HOME/.claude/get-shit-done" ]; then
  GSD_DIR="$HOME/.claude"
elif [ -d ".claude/get-shit-done" ]; then
  GSD_DIR="$(pwd)/.claude"
else
  echo "ERROR: GSD not found. Install GSD first: npx get-shit-done-cc --global"
  exit 1
fi

EXT_INSTALL_DIR="$GSD_DIR/get-shit-done-review-team"

# Create extension directories
mkdir -p "$EXT_INSTALL_DIR/agents"
mkdir -p "$EXT_INSTALL_DIR/workflows"
mkdir -p "$EXT_INSTALL_DIR/templates"

# Copy extension files
cp "$EXT_DIR/agents/"*.md "$EXT_INSTALL_DIR/agents/"
cp "$EXT_DIR/workflows/"*.md "$EXT_INSTALL_DIR/workflows/"
cp "$EXT_DIR/templates/"*.md "$EXT_INSTALL_DIR/templates/"

# Copy command entry point into GSD commands directory
cp "$EXT_DIR/commands/gsd/new-reviewer.md" "$GSD_DIR/commands/gsd/new-reviewer.md"
```

### Pattern-Based Insertion for execute-plan.md

**Use Python, not sed.** Multi-line insertion with sed requires complex quoting that breaks across operating systems and with special characters in the inserted text.

```bash
EXECUTE_PLAN="$GSD_DIR/get-shit-done/workflows/execute-plan.md"

# Check if already patched
if grep -q 'name="review_team_gate"' "$EXECUTE_PLAN"; then
  echo "execute-plan.md already patched — skipping"
else
  python3 << 'PYEOF'
import sys

target = sys.argv[1]
anchor = '<step name="offer_next">'

new_step = '''<step name="review_team_gate">
Check whether Review Team pipeline should run:

```bash
REVIEW_TEAM_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.review_team // false')
```

If `REVIEW_TEAM_ENABLED` is not `"true"`: skip this step entirely — no output, no log.

If `REVIEW_TEAM_ENABLED` is `"true"`:
- Check that `.planning/TEAM.md` exists:
  ```bash
  [ -f .planning/TEAM.md ] && echo "EXISTS" || echo "MISSING"
  ```
- If TEAM.md is missing: log `Review Team: skipped (no .planning/TEAM.md found — run /gsd:new-reviewer to create your first role)` and continue to `offer_next`. Do NOT block execution.
- If TEAM.md exists: load and execute the review pipeline:
  ```
  @~/.claude/get-shit-done-review-team/workflows/review-team.md
  ```
  Pass: current SUMMARY.md path, phase identifier, plan identifier.
</step>

'''

with open(target, 'r', encoding='utf-8') as f:
    content = f.read()

if anchor not in content:
    print(f"ERROR: anchor '{anchor}' not found in {target}", file=sys.stderr)
    sys.exit(1)

patched = content.replace(anchor, new_step + anchor, 1)

with open(target, 'w', encoding='utf-8') as f:
    f.write(patched)

print(f"Patched: {target}")
PYEOF
  python3 -c "..." "$EXECUTE_PLAN"
fi
```

**Note:** The Python heredoc approach above is pseudocode for the structure. The actual `install.sh` will use a Python script file within the extension repo (`scripts/patch-execute-plan.py`) to avoid heredoc quoting complexity. The script takes the target file path as argument.

### Idempotency Check

Before applying any patch, check if already applied:

```bash
# execute-plan.md
if grep -q 'name="review_team_gate"' "$EXECUTE_PLAN"; then
  echo "  [SKIP] execute-plan.md already patched"
else
  # apply patch
fi

# settings.md
if grep -q 'Review Team' "$GSD_DIR/get-shit-done/workflows/settings.md"; then
  echo "  [SKIP] settings.md already patched"
else
  # apply patch
fi
```

### config.json Update

```bash
CONFIG="$PROJECT_DIR/.planning/config.json"
if [ -f "$CONFIG" ]; then
  # Add review_team: false if not present (idempotent — jq handles existing key)
  tmp=$(mktemp)
  jq 'if .workflow.review_team == null then .workflow.review_team = false else . end' "$CONFIG" > "$tmp" && mv "$tmp" "$CONFIG"
  echo "  [OK] config.json updated"
fi
```

### Completion Message

```bash
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " GSD Review Team — Installed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Files installed to: $EXT_INSTALL_DIR"
echo "Commands installed: /gsd:new-reviewer"
echo "Core patches applied:"
echo "  - execute-plan.md (review_team_gate step)"
echo "  - settings.md (Review Team toggle)"
echo ""
echo "IMPORTANT: After running /gsd:update, you must run"
echo "/gsd:reapply-patches to restore the execute-plan.md"
echo "and settings.md patches."
echo ""
echo "Next steps:"
echo "  1. Run /gsd:settings to enable Review Team"
echo "  2. Run /gsd:new-reviewer to create your first reviewer role"
echo "  3. Run /gsd:execute-phase <phase> to see the pipeline in action"
```

---

## 6. Complete File Layout — What the Extension Ships

**Confidence:** HIGH — derived from PROJECT.md architecture section + phase scope

### Extension Repo Structure

```
get-shit-done-review-team/          ← repo root
├── agents/
│   ├── gsd-review-sanitizer.md     ← Phase 2
│   ├── gsd-reviewer.md             ← Phase 3
│   └── gsd-review-synthesizer.md  ← Phase 4
├── commands/gsd/
│   └── new-reviewer.md            ← Phase 5 (entry point for /gsd:new-reviewer)
├── workflows/
│   ├── review-team.md             ← Phase 2 (pipeline orchestrator)
│   └── new-reviewer.md            ← Phase 5 (role builder workflow)
├── templates/
│   ├── TEAM.md                    ← Phase 1 (starter template with 3 example roles)
│   └── review-report.md           ← Phase 4 (REVIEW-REPORT.md output template)
├── scripts/
│   ├── patch-execute-plan.py      ← Phase 1 (Python patcher, called by install.sh)
│   └── patch-settings.py         ← Phase 1 (Python patcher, called by install.sh)
├── install.sh                     ← Phase 1
└── README.md                      ← Phase 5
```

### Phase 1 Deliverables Only

Phase 1 ships these files (a subset of the full layout):

```
get-shit-done-review-team/
├── templates/
│   └── TEAM.md                    ← starter template, 3 example roles
├── scripts/
│   ├── patch-execute-plan.py      ← inserts review_team_gate step
│   └── patch-settings.py         ← adds 7th toggle + spread-safe config write
└── install.sh                     ← orchestrates all install steps
```

The agent files, workflow files, and commands directory will be empty/absent in Phase 1 because they are built in Phases 2–5.

### Where Files Land After Install

| Extension File | Installed To |
|---------------|-------------|
| `templates/TEAM.md` | Copied to `.planning/TEAM.md` in target project (if not already present) |
| `agents/gsd-review-sanitizer.md` | `~/.claude/get-shit-done-review-team/agents/` (Phase 2) |
| `agents/gsd-reviewer.md` | `~/.claude/get-shit-done-review-team/agents/` (Phase 3) |
| `agents/gsd-review-synthesizer.md` | `~/.claude/get-shit-done-review-team/agents/` (Phase 4) |
| `workflows/review-team.md` | `~/.claude/get-shit-done-review-team/workflows/` (Phase 2) |
| `workflows/new-reviewer.md` | `~/.claude/get-shit-done-review-team/workflows/` (Phase 5) |
| `commands/gsd/new-reviewer.md` | `~/.claude/commands/gsd/new-reviewer.md` (Phase 5) |
| `templates/review-report.md` | `~/.claude/get-shit-done-review-team/templates/` (Phase 4) |

### GSD Core Files Modified by install.sh (Phase 1)

| Core File | Modification |
|-----------|-------------|
| `~/.claude/get-shit-done/workflows/execute-plan.md` | Adds `review_team_gate` step before `offer_next` |
| `~/.claude/get-shit-done/workflows/settings.md` | Adds 7th question + review_team to update_config write |

---

## 7. Config Schema

**Confidence:** HIGH — verified from config.json + GSD-EXTENSION-ARCH.md

### Current Project config.json (already has review_team)

```json
{
  "model_profile": "balanced",
  "workflow": {
    "research": true,
    "plan_check": true,
    "verifier": true,
    "auto_advance": false,
    "review_team": false
  },
  "git": {
    "branching_strategy": "none"
  },
  "planning": {
    "commit_docs": true,
    "search_gitignored": false
  }
}
```

The current `D:/GSDteams/.planning/config.json` already has `review_team: false` — this field is already present. For target projects that don't yet have it, `install.sh` adds it via the jq idempotency command above.

### How review_team is Read in the Gate Step

```bash
# CONFIG_CONTENT is already loaded by init_context step via --include config
REVIEW_TEAM_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.review_team // false')
```

Fallback to `false` when the key is absent — safe for projects that haven't run install.sh yet.

---

## 8. Update Compatibility

**Confidence:** HIGH — verified from update.md and reapply-patches.md

### What Happens on /gsd:update

1. `install.js` calls `saveLocalPatches()` — detects SHA256 mismatch between manifest and current `execute-plan.md`/`settings.md`
2. Copies both modified files verbatim to `~/.claude/gsd-local-patches/`
3. Writes `backup-meta.json` with file list
4. Wipes and reinstalls GSD files (execute-plan.md and settings.md revert to unpatched versions)
5. Writes fresh `gsd-file-manifest.json`
6. Prompts: "Run `/gsd:reapply-patches` to merge your modifications"

### /gsd:reapply-patches Behavior

The reapply is **AI-driven merge**, not mechanical patch apply:
- Reads backed-up version (user's patched copy)
- Reads newly installed version (upstream)
- AI identifies user additions, applies them to new version
- If upstream also changed the patched section: AI flags conflict, asks user to choose

The `review_team_gate` step is a discrete, named XML block. The AI merge should handle this cleanly in most GSD version updates. If GSD significantly restructures the `execute-plan.md` step sequence, the AI will flag a conflict — this is acceptable.

### Documentation Requirement

The extension README.md (Phase 5) must document:
> "After running `/gsd:update`, run `/gsd:reapply-patches` to restore the Review Team hooks."

---

## 9. Architecture Patterns

### Pattern: Conditional no-op step

The `review_team_gate` step follows the GSD pattern for conditional workflow steps (observed in `issues_review_gate`):

```xml
<step name="issues_review_gate">
If SUMMARY "Issues Encountered" ≠ "None": yolo → log and continue. Interactive → present issues, wait for acknowledgment.
</step>
```

The review_team_gate follows this same minimal-prose, conditional-inline pattern. The condition check comes first; the skip path is explicit and unconditional.

### Pattern: @ reference for workflow loading

The `review_team_gate` step references the review pipeline via `@`-syntax — the same mechanism `execute-phase.md` uses to load `execute-plan.md` into subagents:

```
@~/.claude/get-shit-done-review-team/workflows/review-team.md
```

This is the correct GSD mechanism for loading an external workflow at runtime.

### Pattern: Spread-safe config write

Settings.md currently overwrites the full `workflow` object. The patch must change this to a spread pattern:

**Before (unsafe — drops unknown keys):**
```json
"workflow": {
  "research": true/false,
  "plan_check": true/false,
  "verifier": true/false,
  "auto_advance": true/false
}
```

**After (spread-safe — preserves unknown keys):**
```json
"workflow": {
  ...existing_config.workflow,
  "research": true/false,
  "plan_check": true/false,
  "verifier": true/false,
  "auto_advance": true/false,
  "review_team": true/false
}
```

This pattern means future extensions can also add workflow keys without risk of settings.md dropping them.

---

## 10. Common Pitfalls

### Pitfall 1: Sed multi-line insertion
**What goes wrong:** Using sed to insert a multi-line block before an anchor fails on macOS (BSD sed) vs Linux (GNU sed). Special characters in the inserted text break quoting.
**How to avoid:** Use Python for all multi-line text insertion. Python's `str.replace()` on file content is portable and handles any special characters without escaping.

### Pitfall 2: settings.md success_criteria not updated
**What goes wrong:** Patching the AskUserQuestion and update_config but forgetting to update the success_criteria at the bottom. The criteria says "6 settings" — after the patch it should say "7 settings".
**How to avoid:** The patch script must update three locations in settings.md: AskUserQuestion array, update_config step, save_as_defaults step. Plus success_criteria. Four touch points total.

### Pitfall 3: CONFIG_CONTENT scope in review_team_gate
**What goes wrong:** Assuming CONFIG_CONTENT is available in the gate step, but the variable is only assigned in `init_context`. In GSD workflows, variables are in scope for the whole workflow — but this must be documented clearly in the step text.
**How to avoid:** The gate step text explicitly references CONFIG_CONTENT as "already loaded by init_context step via --include config". No re-read needed.

### Pitfall 4: TEAM.md copied over user's existing file
**What goes wrong:** install.sh blindly copies `templates/TEAM.md` to `.planning/TEAM.md`, overwriting a user's existing custom team configuration.
**How to avoid:** install.sh checks if `.planning/TEAM.md` already exists before copying. If it does, skip the copy and notify the user.

```bash
if [ -f ".planning/TEAM.md" ]; then
  echo "  [SKIP] .planning/TEAM.md already exists — not overwriting"
else
  cp "$EXT_DIR/templates/TEAM.md" ".planning/TEAM.md"
  echo "  [OK] .planning/TEAM.md created from starter template"
fi
```

### Pitfall 5: install.sh run from wrong directory
**What goes wrong:** install.sh uses relative paths for `.planning/` operations, but is run from the extension repo directory instead of the GSD project directory.
**How to avoid:** install.sh must detect the project root (presence of `.planning/` directory) and fail clearly if not found. All `.planning/` operations use absolute path derived from the detected project root.

---

## 11. Plan-by-Plan Summary for Planner

### Plan 01-01: Repo structure + TEAM.md starter template + config schema

**What to build:**
- The extension repo directory structure (empty agent/workflow/command slots for future phases)
- `templates/TEAM.md` — starter template with 3 example roles (Security Auditor, Rules Lawyer, Performance Analyst)
- `.planning/config.json` already has `review_team: false` — verify it and document the schema

**Key decisions:**
- TEAM.md format: Markdown with YAML blocks per role (see Section 4 above)
- Example roles: visible with `> Example role — customize before use` callout, not commented out
- File naming: follow GSD kebab-case conventions (`gsd-review-sanitizer.md`, not `ReviewSanitizer.md`)

**Verification:** TEAM.md can be parsed to extract at least 3 role names. Repo structure matches PROJECT.md architecture section.

### Plan 01-02: execute-plan.md patch (review_team_gate step)

**What to build:**
- `scripts/patch-execute-plan.py` — Python script that inserts `review_team_gate` before `<step name="offer_next">`
- The gate step content (exact text in Section 3 above)
- Idempotency check (grep for `review_team_gate` before applying)

**Key decisions:**
- Anchor: `<step name="offer_next">` (verified unique in file)
- Insert: `new_step + anchor` (not anchor + new_step — the step goes BEFORE offer_next)
- CONFIG_CONTENT: already in scope from init_context, no re-read
- Skip behavior when disabled: zero output (no log, no banner)
- Skip behavior when TEAM.md missing: single log message, continue to offer_next

**Verification:** Patched execute-plan.md grep shows `review_team_gate` step. Step is positioned between `update_codebase_map` closing tag and `offer_next` opening tag.

### Plan 01-03: settings.md patch (7th toggle, spread-safe config write)

**What to build:**
- `scripts/patch-settings.py` — Python script that modifies settings.md in three places
- 7th question object (Review Team toggle, "Review Team" header = 11 chars, valid)
- Spread-safe update_config step
- Spread-safe save_as_defaults step
- Updated success_criteria count (6 → 7)

**Key decisions:**
- Anchor for question insertion: closing of Branching question's last option line
- Header: "Review Team" (11 chars, within 12-char limit)
- Default in question: "No (Default)" pre-selected (consistent with `false` default in config)
- Both update_config AND save_as_defaults must use spread pattern

**Verification:** Patched settings.md shows 7 questions. update_config step contains `...existing_config.workflow`. Running the settings workflow writes `review_team` to config.json without dropping other workflow keys.

### Plan 01-04: install.sh (pattern-based file copy + patch application)

**What to build:**
- `install.sh` — orchestrates everything
- GSD location detection (global vs local)
- File copy operations (extension files to `~/.claude/get-shit-done-review-team/`)
- Patch application via Python scripts
- config.json update (idempotent jq)
- TEAM.md copy guard (don't overwrite existing)
- Completion message with reapply-patches warning

**Key decisions:**
- Python for patches (not sed) — portability
- Idempotency checks before every operation
- Project root detection (`.planning/` must exist)
- Clear error messages when dependencies (GSD, Python3, jq) are not found

**Verification:** `bash install.sh` completes without errors. Patched files contain expected new content. config.json has `review_team: false`. TEAM.md exists.

---

## Sources

### Primary (HIGH confidence)
- `get-shit-done-1.19.2.zip` → `execute-plan.md` — exact step text, line numbers, anchor string
- `get-shit-done-1.19.2.zip` → `settings.md` — exact AskUserQuestion block, update_config step, save_as_defaults step
- `get-shit-done-1.19.2.zip` → `update.md` — update flow, backup warnings, reapply-patches prompt
- `get-shit-done-1.19.2.zip` → `commands/gsd/reapply-patches.md` — AI merge behavior, cleanup steps
- `D:/GSDteams/.planning/research/GSD-EXTENSION-ARCH.md` — patch mechanism, config schema, init output
- `D:/GSDteams/.planning/research/GSD-AGENT-PATTERNS.md` — agent conventions, AskUserQuestion schema
- `D:/GSDteams/.planning/PROJECT.md` — architecture spec, file layout, constraints
- `D:/GSDteams/.planning/REQUIREMENTS.md` — INT-01 through INT-05, INST-01 through INST-02, TEAM-01, TEAM-04
- `D:/GSDteams/.planning/ROADMAP.md` — Phase 1 success criteria, plan list
- `D:/GSDteams/.planning/config.json` — live config showing review_team already present

---

## Metadata

**Confidence breakdown:**
- Insertion point (execute-plan.md): HIGH — verified line numbers and exact text from zip
- settings.md patch locations: HIGH — full file extracted, all 4 touch points identified
- TEAM.md format design: MEDIUM — no prior examples exist, design derived from PROJECT.md requirements
- install.sh approach: HIGH — Python portability decision is sound, pattern confirmed in GSD-EXTENSION-ARCH.md
- Update compatibility: HIGH — reapply-patches behavior verified from source

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (GSD 1.19.x minor versions unlikely to change step structure)
**GSD version tested against:** 1.19.2
