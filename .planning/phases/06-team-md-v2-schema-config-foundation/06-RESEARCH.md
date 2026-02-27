# Phase 6: TEAM.md v2 Schema + Config Foundation - Research

**Researched:** 2026-02-26
**Domain:** YAML schema evolution, backwards-compatible parser design, settings patch pattern
**Confidence:** HIGH — all findings verified directly from GSD source files on disk

---

## Summary

Phase 6 establishes the data foundation that every subsequent Agent Studio phase depends on.
It has two independent deliverables: (1) evolving the TEAM.md YAML schema from v1.0 to v2
with additive optional fields and a version sentinel, and (2) adding the `workflow.agent_studio`
toggle to `/gsd:settings` and writing it to config.json. Both deliverables are well-specified,
have verified implementation patterns from the existing codebase, and require zero new runtime
dependencies.

The TEAM.md v2 schema is purely additive. Every v1.0 role block is valid v2 — no migration
required. The version sentinel (`version: 2` in frontmatter) activates full v2 parsing;
`version: 1` or absent triggers a compatibility shim that injects defaults for all missing
fields. The YAML frontmatter in TEAM.md is read by Claude via the Read tool, not by bash YAML
parsers (jq cannot parse YAML). This is a design constraint that must be explicit in implementation.

The settings patch follows the exact same 4-touch-point pattern established in
`patch-settings.py`: add a question to the AskUserQuestion array, add the new key to the
`update_config` workflow object with spread, add the key to the `save_as_defaults` workflow
object with spread, and update the success criteria count. The `agent_studio` toggle is
independent of `review_team` — both can be true simultaneously.

**Primary recommendation:** Implement the TEAM.md v2 schema as a template update + parser
specification document first. Then write `patch-settings.py` for `agent_studio` using the
established 4-touch-point pattern. Together these deliver a testable, committed schema that
all downstream phases can depend on.

---

## Standard Stack

### Core (no new dependencies)

| Component | Version/Tool | Purpose | Why Standard |
|-----------|-------------|---------|--------------|
| TEAM.md (YAML frontmatter) | Markdown + YAML | Agent roster schema | Already the v1.0 config file; users already manage it |
| Python 3 patch scripts | Python 3 (existing) | Idempotent text patches to GSD core files | Proven pattern from patch-execute-plan.py and patch-settings.py |
| jq (in install.sh) | jq (existing) | Config.json writes in install.sh | Used for config.json update; Python3 fallback when absent |
| Claude Read tool | — | YAML parsing in dispatcher | Only reliable YAML parser in GSD workflow context; jq cannot parse YAML |

### No New Dependencies

This phase introduces zero new npm packages, zero new Python libraries, zero new tools. All
implementation uses the patterns already proven in the v1.0 codebase.

---

## Architecture Patterns

### Verified v1.0 TEAM.md Schema (exact current format)

From direct inspection of `D:/GSDteams/.planning/TEAM.md` and `D:/GSDteams/templates/TEAM.md`:

```
---
version: 1
roles:
  - security-auditor
  - rules-lawyer
  - performance-analyst
---

# Review Team

[preamble prose]

---

## Role: Security Auditor

```yaml
name: security-auditor
focus: Security vulnerabilities and unsafe patterns
```

**What this role reviews:**
- [bullet items]

**Severity thresholds:**
- `critical`: [description]
- `major`: [description]
- `minor`: [description]

**Routing hints:**
- Critical findings: `block_and_escalate`
- Major findings: `send_for_rework`
- Minor findings: `log_and_continue`

---

## Role: [Next Role]
...
```

**Key structural facts (HIGH confidence, verified from file):**
- YAML frontmatter delimited by `---` at top of file
- `version: 1` is the sentinel field — currently an integer, not a string
- `roles:` is a YAML list of slug strings; each slug must match the `name:` field in its role block
- Each role body starts with `## Role: [Display Name]` markdown header
- Role YAML config is a fenced code block with triple backticks and `yaml` language tag
- Role block has: `name`, `focus` — both required in v1.0
- Three narrative markdown sections follow: "What this role reviews:", "Severity thresholds:", "Routing hints:"
- Roles are separated by `---` horizontal rule
- The template and the live file are identical in structure

### TEAM.md v2 Schema (from ARCHITECTURE.md — HIGH confidence)

The v2 schema adds to the per-role YAML block. New fields are all optional. When absent, the
parser injects version-appropriate defaults.

**V2 frontmatter additions:**

```yaml
---
version: 2
roles:
  - security-auditor      # v1.0 role — implicit defaults apply
  - rules-lawyer
  - performance-analyst
  - doc-writer            # v2 role — explicit fields present
agents:
  - doc-writer            # optional: separate list distinguishing agents from reviewers
---
```

Note: The `agents:` list is documented in ARCHITECTURE.md as mirroring `roles:` for clarity.
Whether it is strictly required or optional in phase 6 needs to be decided during planning.
The dispatcher uses `roles:` to enumerate all entries; `agents:` appears to be informational.

**V2 role block (full fields):**

```yaml
name: doc-writer
focus: Keeps documentation in sync with implementation
mode: autonomous           # advisory | autonomous
trigger: post-phase        # pre-plan | post-plan | post-phase | on-demand
tools:                     # subset of Claude Code tool names
  - Read
  - Write
  - Grep
output_type: artifact      # findings | artifact | advisory
commit: true               # autonomous only — whether agent commits its own output
commit_message: "docs(auto): update API reference after phase {phase}"
```

**Field definitions table (from ARCHITECTURE.md):**

| Field | Values | Default when absent | Required for |
|-------|--------|---------------------|--------------|
| `mode` | `advisory`, `autonomous` | `advisory` | All v2 agents |
| `trigger` | `pre-plan`, `post-plan`, `post-phase`, `on-demand` | `post-plan` | All v2 agents |
| `tools` | Any Claude Code tool name | `[]` (no filesystem access) | Autonomous agents |
| `output_type` | `findings`, `artifact`, `advisory` | `findings` | Routing logic |
| `commit` | `true`, `false` | `false` | Autonomous agents |
| `commit_message` | String with `{phase}`, `{plan}` tokens | None | Autonomous with commit |

**Scope fields (from ARCHITECTURE.md):**

The additional context mentions `allowed_paths` and `allowed_tools` fields. ARCHITECTURE.md
uses `tools:` (not `allowed_tools:`) in the role block. However, the phase success criterion
explicitly names `allowed_paths` and `allowed_tools` as fields that must parse correctly.
This is an open question: `tools:` in ARCHITECTURE.md vs `allowed_paths`/`allowed_tools` in
the success criteria. See Open Questions section.

### Version Sentinel and Compatibility Shim Pattern

```
function normalizeRole(role, version):
  if version < 2:
    role.mode        = role.mode        ?? "advisory"
    role.trigger     = role.trigger     ?? "post-plan"
    role.tools       = role.tools       ?? []
    role.output_type = role.output_type ?? "findings"
    role.commit      = role.commit      ?? false
  return role
```

This logic lives in the dispatcher (Phase 2), but Phase 6 must document the defaults so the
dispatcher implementer has a single authoritative source. The v2 TEAM.md template and parser
spec must explicitly list these defaults.

**Version detection rule:**
- `version: 2` in frontmatter → full v2 parsing path
- `version: 1` or version field absent → v1 compatibility shim, all roles get injected defaults
- Version is read as an integer (not string) based on current v1.0 format

### settings.md Patch Pattern (verified from patch-settings.py)

The existing patch-settings.py applies exactly 4 touch points. The `agent_studio` patch must
follow the same 4-touch-point pattern:

**Touch point 1: Add a new question to the AskUserQuestion array**

The new question appends after the existing "Review Team" question (which was itself the 7th
question added via touch point 1 of patch-settings.py). The anchor in the current patched
`settings.md` is the closing of the "Review Team" question block:

```
  }\n])
```

But since Review Team is now the last question, the anchor is specifically the closing of the
Review Team question. The new "Agent Studio" question gets appended after it.

**Touch point 2: Add `agent_studio` to `update_config` workflow object**

Current state in settings.md (already patched with Review Team):
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

New state after agent_studio patch:
```json
"workflow": {
  ...existing_config.workflow,
  "research": true/false,
  "plan_check": true/false,
  "verifier": true/false,
  "auto_advance": true/false,
  "review_team": true/false,
  "agent_studio": true/false
}
```

**Touch point 3: Add `agent_studio` to `save_as_defaults` workflow object**

Same additive pattern — append `"agent_studio": <current>` after `"review_team": <current>`.

**Touch point 4: Update success_criteria count**

Current: "7 settings (profile + 5 workflow toggles + git branching)"
New: "8 settings (profile + 6 workflow toggles + git branching)"

**Critical constraint:** The spread pattern (`...existing_config.workflow`) is already in
place from the review_team patch. This means adding `agent_studio` drops in cleanly without
losing any keys. The spread was added specifically to make future additions safe.

### Config.json Patch in install.sh

The install.sh Section 7 currently adds `workflow.review_team = false` if not present. The
agent_studio patch needs to extend this to also ensure `workflow.agent_studio = false` if not
present:

**jq approach (both keys in one command):**
```bash
tmp=$(mktemp)
jq 'if .workflow.agent_studio == null then .workflow.agent_studio = false else . end' "$CONFIG" > "$tmp" && mv "$tmp" "$CONFIG"
```

**Python3 fallback approach:**
```python
workflow = data.setdefault('workflow', {})
if 'review_team' not in workflow:
    workflow['review_team'] = False
if 'agent_studio' not in workflow:
    workflow['agent_studio'] = False
```

The key constraint: adding `agent_studio` to config.json must NOT drop `review_team` or any
other existing keys. The jq command uses `if null then set else . end` which is safe.

### Recommended File Structure for This Phase

```
D:/GSDteams/
├── templates/
│   └── TEAM.md                       # UPDATE: v2 template with new fields annotated
├── scripts/
│   ├── patch-execute-plan.py         # UNCHANGED
│   ├── patch-settings.py             # UNCHANGED (review_team already applied)
│   └── patch-settings-agent-studio.py  # NEW: adds agent_studio toggle
├── install.sh                        # UPDATE: add agent_studio to config section
└── .planning/
    └── TEAM.md                       # NO CHANGE in install — existence guard protects it
```

Note: The existing `D:/GSDteams/.planning/TEAM.md` is NOT updated by the installer (existence
guard prevents overwrite). The updated template only applies to fresh installs. Users with
existing TEAM.md keep their v1 file — the parser handles this via the version shim.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing in bash | Custom awk/sed YAML extractor | Claude Read tool + in-context parsing | jq cannot parse YAML; bash YAML parsers are fragile and non-standard |
| Patch idempotency | String checks inside install.sh | Python3 scripts with named check strings | Proven pattern from patch-execute-plan.py; separates concerns cleanly |
| Config.json merge | Manual JSON string concatenation | jq with `if null then X else . end` pattern | Safe key-preserving update; Python3 fallback available |
| Version migration | TEAM.md migration script | Parser-side defaults injection | Zero user migration required; shim handles it at read time |

**Key insight:** All complex operations in this phase already have proven patterns in the
existing codebase. The implementation is pattern-following, not pattern-inventing.

---

## Common Pitfalls

### Pitfall 1: Overwriting User's TEAM.md on Re-install

**What goes wrong:** install.sh copies the updated v2 TEAM.md template, overwriting a user's
existing v1 TEAM.md with custom reviewer roles.

**Why it happens:** Forgetting the existence guard in Section 8 of install.sh.

**How to avoid:** The existence guard (`if [ -f "$PROJECT_DIR/.planning/TEAM.md" ]; then skip`)
is already in install.sh Section 8. The new `agent_studio` config update must NOT touch this
guard — only the config.json update section (Section 7) gets modified.

**Warning signs:** Test install.sh twice in a row; second run should show `[SKIP] .planning/TEAM.md
already exists` with unchanged file contents.

### Pitfall 2: Patch Anchor Drift After Review Team Patch

**What goes wrong:** The settings.md patch anchor for adding the Agent Studio question is
written to match the un-patched settings.md, but settings.md has already been patched with
Review Team. The old anchor no longer exists.

**Why it happens:** Writing patch anchors based on the original settings.md without verifying
the current state after the v1.0 review_team patch.

**How to avoid:** Read the CURRENT state of settings.md (already patched with review_team)
before writing anchors. The anchor for adding Agent Studio must match text that exists in the
review_team-patched version, not the original. Specifically: the closing of the Review Team
question block (`"No (Default)"` description + `]\n  }\n])`) is the correct current anchor.

**Warning signs:** The patch script prints `[WARN] anchor not found` on first run.

### Pitfall 3: Dropping Existing Workflow Keys in config.json Update

**What goes wrong:** A jq command like `.workflow.agent_studio = false` replaces the entire
`workflow` object with only `agent_studio`, dropping `review_team`, `research`, etc.

**Why it happens:** jq assignment to a nested key without proper null-conditional update.

**How to avoid:** Use `if .workflow.agent_studio == null then .workflow.agent_studio = false
else . end` (from the existing install.sh pattern). The `if null then set else . end` pattern
only adds the key when absent, preserving all existing keys.

**Warning signs:** After install, `cat .planning/config.json | jq .workflow` shows only
`agent_studio` with other keys missing.

### Pitfall 4: Adding `scope` Fields Without Clarifying the Naming Discrepancy

**What goes wrong:** The phase success criteria mention `allowed_paths` and `allowed_tools` as
scope constraint fields. ARCHITECTURE.md uses `tools:` (not `allowed_tools:`) and does not
mention `allowed_paths`. Implementing both without resolving which is authoritative produces
a schema with redundant or mismatched fields.

**Why it happens:** Success criteria were written before ARCHITECTURE.md field definitions
were finalized.

**How to avoid:** Treat `tools:` (from ARCHITECTURE.md) as the field name for tool access
scope. Treat `allowed_paths` as a new scope field not currently in ARCHITECTURE.md — requiring
an explicit decision before implementation. See Open Questions.

**Warning signs:** The v2 template has both `tools:` and `allowed_paths:` without clear
distinction between them.

### Pitfall 5: Version Sentinel as String vs Integer

**What goes wrong:** Writing `version: "2"` (string) when the v1.0 format uses `version: 1`
(integer). Parser comparisons using `== 2` fail for string `"2"`.

**Why it happens:** YAML allows both; the difference is invisible to a human reader.

**How to avoid:** The v1.0 format uses `version: 1` (integer). The v2 template must use
`version: 2` (integer, no quotes). Parser logic should compare `version >= 2` (numeric) not
`version == "2"` (string).

**Warning signs:** A v2 TEAM.md loads as v1 defaults — parser treats version as unknown.

---

## Code Examples

Verified patterns from existing source files:

### Pattern 1: Python3 Idempotent Patch Script (from patch-execute-plan.py)

```python
# Source: D:/GSDteams/scripts/patch-execute-plan.py

def main():
    target = sys.argv[1]

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Idempotency check — named string unique to the patch
    if 'name="review_team_gate"' in content:
        print(f"  [SKIP] {target} already patched (review_team_gate step found)")
        sys.exit(0)

    anchor = '<step name="offer_next">'

    if anchor not in content:
        print(f"ERROR: Anchor string not found in {target}", file=sys.stderr)
        sys.exit(1)

    new_step = '''[patch content here]'''

    patched = content.replace(anchor, new_step + anchor, 1)

    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)

    print(f"  [OK] Patched: {target}")
```

The `patch-settings-agent-studio.py` script follows this same structure with 4 named
touch-point sections.

### Pattern 2: 4-Touch-Point Settings Patch (from patch-settings.py)

```python
# Source: D:/GSDteams/scripts/patch-settings.py

# Touch point pattern:
#   1. Check if already applied (idempotency)
#   2. Check if anchor exists (drift detection)
#   3. Apply replacement
#   4. Report

if tp1_check in content:
    print("  [SKIP] Touch point 1: already patched")
    patches_skipped += 1
elif tp1_anchor_full not in content:
    print("  [WARN] Touch point 1: anchor not found", file=sys.stderr)
    patches_skipped += 1
else:
    content = content.replace(tp1_anchor_full, tp1_new_full, 1)
    print("  [OK]   Touch point 1: added Agent Studio question")
    patches_applied += 1
```

### Pattern 3: install.sh Config.json Safe Update (from install.sh Section 7)

```bash
# Source: D:/GSDteams/install.sh

if [ "$HAS_JQ" -eq 1 ]; then
  tmp=$(mktemp)
  jq 'if .workflow.review_team == null then .workflow.review_team = false else . end' \
    "$CONFIG" > "$tmp" && mv "$tmp" "$CONFIG"
else
  # Python3 fallback
  python3 - "$CONFIG" <<'PYEOF'
import sys, json
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
workflow = data.setdefault('workflow', {})
if 'review_team' not in workflow:
    workflow['review_team'] = False
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
PYEOF
fi
```

The `agent_studio` update extends this block with an additional jq command and additional
Python3 key check.

### Pattern 4: TEAM.md Role Block Write Format (from new-reviewer.md)

```
# Source: C:/Users/gutie/.claude/get-shit-done-review-team/workflows/new-reviewer.md

# When .planning/TEAM.md EXISTS:
# 1. Read current content
# 2. Parse YAML frontmatter roles: list, add new slug
# 3. Append separator + role block
# 4. Write full updated content back

# Appended block format:
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

The v2 TEAM.md template extends this format by adding v2 fields (mode, trigger, tools,
output_type, commit) to the YAML config block inside each role.

### Pattern 5: V2 Role Block Format (from ARCHITECTURE.md)

```yaml
# Source: D:/GSDteams/.planning/research/ARCHITECTURE.md

name: doc-writer
focus: Keeps documentation in sync with implementation
mode: autonomous           # advisory | autonomous
trigger: post-phase        # pre-plan | post-plan | post-phase | on-demand
tools:                     # subset of: Read, Write, Bash, Grep, Glob, WebSearch
  - Read
  - Write
  - Grep
output_type: artifact      # findings | artifact | advisory
commit: true               # autonomous only — whether agent commits its own output
commit_message: "docs(auto): update API reference after phase {phase}"
```

### Pattern 6: settings.md AskUserQuestion — Current Review Team Toggle (verified from settings.md)

```
# Source: C:/Users/gutie/.claude/get-shit-done/workflows/settings.md (patched)

  {
    question: "Spawn Review Team? (multi-agent review after each plan executes)",
    header: "Review Team",
    multiSelect: false,
    options: [
      { label: "No (Default)", description: "Skip review pipeline -- standard execution" },
      { label: "Yes", description: "After each plan: sanitize output, spawn reviewers, synthesize findings" }
    ]
  }
])
```

The Agent Studio question appends after this closing `])`. The new question follows the same
structure. Suggested text:

```
  {
    question: "Enable Agent Studio? (agents fire on plan/phase lifecycle events)",
    header: "Agent Studio",
    multiSelect: false,
    options: [
      { label: "No (Default)", description: "Disable all agent lifecycle hooks" },
      { label: "Yes", description: "Enable agents to run at pre-plan, post-plan, and post-phase triggers" }
    ]
  }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No version sentinel in TEAM.md | `version: 1` integer in frontmatter | v1.0 initial release | Parser can distinguish old files from new |
| No version field → implicit v1 | `version` field absent → parser treats as v1 | Phase 6 (this phase) | Safe default for any pre-existing TEAM.md |
| Only `name` + `focus` in role YAML | v2 adds `mode`, `trigger`, `tools`, `output_type`, `commit` | Phase 6 (this phase) | Schema foundation for dispatcher and studio |
| settings.md: 7 questions | settings.md: 8 questions (adding agent_studio) | Phase 6 (this phase) | `workflow.agent_studio` written to config.json |
| review_team and agent_studio conflict risk | Independent boolean flags, both can be true | Phase 6 (this phase) | v1 review pipeline unchanged when both active |

---

## Open Questions

1. **`allowed_paths` vs `tools:` — naming discrepancy**
   - What we know: ARCHITECTURE.md uses `tools:` as the field for tool access scope (e.g., `- Read`, `- Write`). The phase success criteria say "scope (allowed_paths, allowed_tools) fields is parsed correctly and scope constraints stored and readable."
   - What's unclear: Is `allowed_paths` a new field not yet in ARCHITECTURE.md? Or is it a misname for a `paths:` field that lives alongside `tools:`? Or is the success criterion referring to `tools:` as "allowed_tools"?
   - Recommendation: During planning, treat `tools:` (from ARCHITECTURE.md) as the definitive field name for tool access. Treat `allowed_paths` as a new scope constraint field that needs to be added to the v2 schema if the success criterion is authoritative. Draft both in the v2 template and let the planner decide.

2. **`agents:` list in v2 frontmatter — required or informational?**
   - What we know: ARCHITECTURE.md shows both a `roles:` and an `agents:` list in v2 frontmatter. The text says "agents list mirrors roles list; duplicated for clarity."
   - What's unclear: If the dispatcher uses only `roles:` to enumerate all entries, is `agents:` a required field or documentation-only?
   - Recommendation: Make `agents:` optional in v2. The dispatcher uses `roles:` exclusively. The template can include `agents:` as a comment-annotated example of how to distinguish v2 roles from v1 roles visually.

3. **Whether to update the live `.planning/TEAM.md` to v2 during this phase**
   - What we know: The install.sh existence guard prevents overwriting user TEAM.md. The v2 template is for fresh installs only.
   - What's unclear: Should Phase 6 also update `D:/GSDteams/.planning/TEAM.md` to v2 format as a test/demonstration artifact? Or leave it at v1 to validate the backwards-compat shim?
   - Recommendation: Leave the live TEAM.md at v1 during Phase 6. This validates the backwards-compat shim works correctly. The live TEAM.md can be upgraded to v2 in Phase 2 (dispatcher) or Phase 3 (team studio) when the first v2-specific agent role is actually added.

---

## Deliverables for Phase 6

Based on the research, these are the concrete outputs Phase 6 must produce:

1. **Updated `templates/TEAM.md`** — v2 template with `version: 2`, all new fields annotated with comments, backwards-compatible v1 roles shown alongside a v2 example role block

2. **`scripts/patch-settings-agent-studio.py`** — 4-touch-point idempotent patch script adding Agent Studio toggle to settings.md

3. **Updated `install.sh`** — Section 7 extended to also set `workflow.agent_studio = false` in config.json (jq + Python3 fallback)

4. **Parser specification document** (or inline in ARCHITECTURE.md) — explicit defaults table, normalizeRole algorithm, version detection rule — this is the authoritative reference the dispatcher (Phase 2) implements against

5. **Verification test** — run install.sh on a system with existing v1 TEAM.md, verify TEAM.md unchanged; run /gsd:settings and verify `agent_studio` key appears in config.json alongside `review_team`

---

## Sources

### Primary (HIGH confidence)

- `D:/GSDteams/.planning/TEAM.md` — v1.0 schema verified: version integer, roles list, `## Role:` format, YAML config block fields (`name`, `focus` only), separator pattern, narrative sections
- `D:/GSDteams/templates/TEAM.md` — identical structure to live TEAM.md; confirms template = live format
- `D:/GSDteams/scripts/patch-execute-plan.py` — complete idempotent patch pattern: read, idempotency check, anchor check, string replace, write
- `D:/GSDteams/scripts/patch-settings.py` — complete 4-touch-point pattern: per-touch-point idempotency, anchor drift detection, replacement logic, counters
- `D:/GSDteams/install.sh` — full install flow: Section 7 (config.json update with jq + Python3 fallback), Section 8 (TEAM.md existence guard)
- `C:/Users/gutie/.claude/get-shit-done/workflows/settings.md` — current patched settings.md: exact AskUserQuestion structure, 7 questions including Review Team, update_config spread pattern, save_as_defaults spread pattern
- `C:/Users/gutie/.claude/get-shit-done-review-team/workflows/new-reviewer.md` — TEAM.md write format: frontmatter update pattern, role block append format, separator convention
- `D:/GSDteams/.planning/research/ARCHITECTURE.md` — v2 schema design: field definitions, normalizeRole algorithm, version sentinel design, frontmatter additions
- `D:/GSDteams/.planning/config.json` — current config structure: `workflow.review_team: true`, no `agent_studio` key present

### Secondary (MEDIUM confidence)

- `D:/GSDteams/.planning/research/SUMMARY.md` — Phase 1 build rationale; confirms schema design is fully specified; flags `allowed_paths` / `allowed_tools` as scope fields (source of naming discrepancy question)

---

## Metadata

**Confidence breakdown:**
- Current v1.0 TEAM.md schema: HIGH — read directly from live file and template
- V2 field definitions and defaults: HIGH — from ARCHITECTURE.md (primary research artifact)
- Settings patch pattern: HIGH — from patch-settings.py and current settings.md (both verified)
- Install.sh config update pattern: HIGH — from install.sh directly
- `allowed_paths` / scope field naming: LOW — named in success criteria but not in ARCHITECTURE.md; requires planner decision
- `agents:` list requirement: MEDIUM — mentioned in ARCHITECTURE.md, but "duplicated for clarity" suggests informational

**Research date:** 2026-02-26
**Valid until:** This research is based on internal project files that change only when GSD is updated. Valid for 60 days or until GSD version changes (whichever comes first).
