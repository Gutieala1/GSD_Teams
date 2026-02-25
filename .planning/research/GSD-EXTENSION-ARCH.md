# GSD Extension Architecture Research

**Project:** GSD Review Team
**Source:** GSD v1.19.2 (extracted from get-shit-done-1.19.2.zip, verified against installed files)
**Researched:** 2026-02-25
**Overall Confidence:** HIGH — all findings verified directly from GSD source code

---

## 1. The Patch System: How `reapply-patches` Works

### Mechanism (HIGH confidence — read from install.js and reapply-patches.md)

GSD uses a **SHA256 file manifest + backup-on-update** system. Not traditional Unix diff patches.

**On every install/update:**

1. `install.js` calls `saveLocalPatches(configDir)` BEFORE wiping files
2. `saveLocalPatches` reads `gsd-file-manifest.json` (written after the previous install)
3. For every tracked file, it computes the current SHA256 and compares to the manifest hash
4. Any file whose hash differs from the manifest is considered "user-modified"
5. Modified files are copied verbatim to `~/.claude/gsd-local-patches/{relative-path}`
6. A `backup-meta.json` is written with `backed_up_at`, `from_version`, and `files[]`
7. After installing new files, `writeManifest()` writes a fresh `gsd-file-manifest.json`

**Files tracked by the manifest:**
- `get-shit-done/**` (all workflow, reference, template files)
- `commands/gsd/**` (all command entry points)
- `agents/gsd-*.md` (GSD agent files only — not user agents)

**Key location:** `~/.claude/gsd-file-manifest.json` (global) or `./.claude/gsd-file-manifest.json` (local)
**Patches stored at:** `~/.claude/gsd-local-patches/` or `./.claude/gsd-local-patches/`

### What the patch format actually is

There is NO diff format. Patches are **verbatim file copies** of the user-modified version. The backup is a complete snapshot of the modified file at backup time.

```
gsd-local-patches/
  backup-meta.json                          # metadata: version, file list
  get-shit-done/workflows/execute-plan.md   # full modified file
  get-shit-done/workflows/settings.md       # full modified file
```

### Reapply process (`/gsd:reapply-patches`)

`reapply-patches.md` is an **AI-driven merge** workflow, not a mechanical patch apply:

1. Reads `backup-meta.json` from `gsd-local-patches/`
2. For each backed-up file:
   - Reads the backed-up version (user's old modified copy)
   - Reads the newly installed version (current file after update)
   - **AI compares both, identifies the user's additions/modifications, applies them to the new version**
   - If upstream also changed a section the user modified: AI flags as conflict, asks user which to keep
3. Writes merged result to installed location
4. Offers to clean up patch backups

**Critical implication:** The reapply is intelligent but not guaranteed. If the section of `execute-plan.md` being patched changes significantly in a GSD update, the AI merge will ask the user to resolve the conflict. This is acceptable for a community extension.

---

## 2. What Happens During `/gsd:update`

### Update flow (HIGH confidence — read from update.md and install.js)

```
/gsd:update
  └── show_changes_and_confirm
        └── warn: "commands/gsd/ will be wiped and replaced"
              "get-shit-done/ will be wiped and replaced"
              "agents/gsd-* files will be replaced"
        └── "If you've modified any GSD files directly, they'll be automatically
             backed up to gsd-local-patches/ and can be reapplied with
             /gsd:reapply-patches after the update."
  └── run_update (npx get-shit-done-cc --global/--local)
        └── install.js: saveLocalPatches() BEFORE wipe
        └── install.js: wipe + install new files
        └── install.js: writeManifest() (fresh hashes)
        └── install.js: reportLocalPatches() → instructs user to run /gsd:reapply-patches
  └── check_local_patches
        └── if patches found: "Run /gsd:reapply-patches to merge your modifications"
```

**Answer:** Yes, update DOES overwrite patched files. The installer saves them first and tells the user to reapply. The extension's patched `execute-plan.md` will be overwritten on every GSD update. The user must run `/gsd:reapply-patches` each time.

**Implication for the extension:** The `install.sh` approach (direct file patch) works, but users need to know they must run `/gsd:reapply-patches` after each GSD update. This is documented GSD behavior — not a surprise. Alternatively, the extension could ship as a pure conditional-load approach that doesn't patch core files at all (see Section 6).

---

## 3. The Right Patch Format for `execute-plan.md`

### Where to insert (HIGH confidence — read from execute-plan.md)

The exact insertion point is between the `create_summary` step and the `offer_next` step. Looking at the full step sequence in `execute-plan.md`:

```
create_summary       → line ~322
update_current_position → line ~336
extract_decisions_and_issues → line ~352
update_session_continuity → line ~366
issues_review_gate  → line ~378
update_roadmap      → line ~382
git_commit_metadata → line ~389
update_codebase_map → line ~397
offer_next          → line ~412   ← insert review_team_gate BEFORE this
```

PROJECT.md says "between `create_summary` and `offer_next`" — the exact placement should be after `update_codebase_map` (final metadata step) and before `offer_next`.

### Patch format recommendation

Since GSD patches are verbatim file copies, the "patch" is the full modified `execute-plan.md`. However, for an extension shipped as source, the approach should be:

**Option A: Inline conditional block (recommended)**

Insert a single `<step name="review_team_gate">` XML block before `<step name="offer_next">`. The block conditionally fires based on `workflow.review_team` in config.json:

```xml
<step name="review_team_gate">
If `review_team_enabled` is false (from config_content or direct config.json read): skip this step entirely.

If `review_team_enabled` is true:
Check that `.planning/TEAM.md` exists. If missing: warn and skip.
Load `.claude/get-shit-done-review-team/workflows/review-team.md` and execute the review pipeline.
Pass: SUMMARY.md path, phase, plan number.
</step>
```

The conditional read of `workflow.review_team` from `config_content` (already loaded in `init_context`) makes this zero-cost when disabled.

**Option B: External workflow delegation**

The gate step simply calls into `review-team.md` which reads config itself and short-circuits if disabled. Cleaner but adds one file read.

**Recommended: Option A** — single conditional block, inline, minimal diff surface area.

### The install.sh approach

`install.sh` in the extension repo would:
1. Locate `execute-plan.md` (`~/.claude/get-shit-done/workflows/execute-plan.md` or `./.claude/...`)
2. Insert the `review_team_gate` step using a line-number-aware edit OR pattern-based sed/awk
3. Warn the user that future `/gsd:update` will require `/gsd:reapply-patches`

**Caution:** sed line-number insertion is brittle. Pattern-based insertion on `<step name="offer_next">` as anchor is more robust across GSD version changes.

---

## 4. config.json Schema for New Workflow Toggles

### Existing schema (HIGH confidence — read from gsd-tools.cjs and settings.md)

```json
{
  "mode": "interactive",
  "depth": "standard",
  "model_profile": "balanced",
  "commit_docs": true,
  "parallelization": true,
  "brave_search": false,
  "workflow": {
    "research": true,
    "plan_check": true,
    "verifier": true,
    "auto_advance": false
  },
  "git": {
    "branching_strategy": "none",
    "phase_branch_template": "gsd/phase-{phase}-{slug}",
    "milestone_branch_template": "gsd/{milestone}-{slug}"
  },
  "planning": {
    "commit_docs": true,
    "search_gitignored": false
  }
}
```

### How `workflow.*` flags are loaded in gsd-tools.cjs

```javascript
// In loadConfig(), these are flattened from workflow section:
research: get('research', { section: 'workflow', field: 'research' }) ?? defaults.research,
plan_checker: get('plan_checker', { section: 'workflow', field: 'plan_check' }) ?? defaults.plan_checker,
verifier: get('verifier', { section: 'workflow', field: 'verifier' }) ?? defaults.verifier,
```

The `loadConfig()` function reads `workflow.review_team` by adding:
```javascript
review_team: get('review_team', { section: 'workflow', field: 'review_team' }) ?? false,
```

But **gsd-tools.cjs does not need to be modified for the extension to work**. The extension can read config.json directly (it's raw JSON) or use the `config_content` already loaded in `init_context`. The `workflow.review_team` value is already present in the JSON — gsd-tools just doesn't extract it as a named field.

### Reading `review_team` in the patch

In `execute-plan.md`, `config_content` is already loaded via `--include config`:

```bash
INIT=$(node ~/.claude/get-shit-done/bin/gsd-tools.cjs init execute-phase "${PHASE}" --include state,config)
CONFIG_CONTENT=$(echo "$INIT" | jq -r '.config_content // empty')
REVIEW_TEAM_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.review_team // false')
```

No gsd-tools modifications needed. The config is plain JSON and `jq` handles nested field access.

### Adding `review_team` to `config-ensure-section` defaults

The `config-ensure-section` command in gsd-tools.cjs writes defaults if config.json is missing:

```javascript
// Line ~622 in gsd-tools.cjs (hardcoded defaults):
workflow: {
  research: true,
  plan_check: true,
  verifier: true,
  // review_team NOT present — defaults to missing/undefined
}
```

Since `workflow.review_team` is not in the hardcoded defaults, it will be absent from new projects until the user enables it or the extension's init step adds it. This is the correct behavior — the extension should default to `false` (opt-in).

The extension's `install.sh` can add `workflow.review_team: false` to any existing `config.json` using jq:

```bash
jq '.workflow.review_team = false' .planning/config.json > tmp.json && mv tmp.json .planning/config.json
```

---

## 5. How `init` Commands Surface Config Values

### Pattern (HIGH confidence — read from gsd-tools.cjs `cmdInitExecutePhase`)

The `init execute-phase` command returns a flat JSON object. Currently it surfaces:

```json
{
  "executor_model": "...",
  "verifier_model": "...",
  "commit_docs": true,
  "parallelization": true,
  "branching_strategy": "none",
  "verifier_enabled": true,
  "phase_found": true,
  "phase_dir": "...",
  ...
}
```

Note: `verifier_enabled` is explicitly extracted from `config.verifier` and surfaced as a named field. But `workflow.review_team` is NOT extracted — it's only available via `config_content` (the raw JSON string).

### Two ways to access `workflow.review_team` without modifying gsd-tools:

**Way 1: Via config_content (no gsd-tools changes)**
```bash
INIT=$(node ~/.claude/get-shit-done/bin/gsd-tools.cjs init execute-phase "${PHASE}" --include state,config)
CONFIG_CONTENT=$(echo "$INIT" | jq -r '.config_content // "{}"')
REVIEW_TEAM_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.review_team // false')
```

**Way 2: Direct config.json read (no gsd-tools changes)**
```bash
REVIEW_TEAM_ENABLED=$(jq -r '.workflow.review_team // false' .planning/config.json 2>/dev/null || echo "false")
```

**Way 3: Modify gsd-tools to add `review_team_enabled` to init output (requires gsd-tools patch)**

This would add the field cleanly to the init JSON, like `verifier_enabled`. But it means the extension also patches gsd-tools.cjs — a larger maintenance burden. **Not recommended.** Use Way 1 or Way 2.

### Verdict: No gsd-tools modification needed

The extension can read `workflow.review_team` from `config_content` or directly from `.planning/config.json`. Both work. Way 2 (direct jq read) is simpler and more explicit.

---

## 6. How `settings.md` Handles New Toggles

### Current settings structure (HIGH confidence — read from settings.md)

The settings workflow presents 6 questions via `AskUserQuestion`:
1. Model profile
2. Plan Researcher (workflow.research)
3. Plan Checker (workflow.plan_check)
4. Execution Verifier (workflow.verifier)
5. Auto-advance (workflow.auto_advance)
6. Git branching strategy

Then writes the full `workflow` section to config.json.

### How to add a new toggle

The extension's `settings.md` patch adds a 7th question AFTER the existing 6. The new question:

```javascript
{
  question: "Spawn Review Team? (multi-agent review after each plan)",
  header: "Review Team",
  multiSelect: false,
  options: [
    { label: "No (Default)", description: "Skip review pipeline — standard execution" },
    { label: "Yes", description: "Sanitize output, spawn isolated reviewers, synthesize findings" }
  ]
}
```

And in the `update_config` step, add `review_team` to the workflow object:
```json
"workflow": {
  "research": true/false,
  "plan_check": true/false,
  "verifier": true/false,
  "auto_advance": true/false,
  "review_team": true/false
}
```

### Critical: settings.md currently overwrites the full workflow object

The `update_config` step in settings.md writes the complete `workflow` section. If a user runs `/gsd:settings` BEFORE the extension patches settings.md, the `review_team` key will be silently dropped because the unpatched settings.md doesn't know about it.

**Mitigation:** The extension should patch `settings.md` to preserve unknown `workflow.*` keys:
```json
"workflow": {
  ...existing_workflow,
  "research": ...,
  "review_team": ...
}
```

Alternatively, `/gsd:settings` output should merge (not replace) the workflow section.

### The `save_as_defaults` step

The settings workflow also writes to `~/.gsd/defaults.json` which includes the `workflow` section. The same preservation issue applies. The patch needs to handle both write locations.

---

## 7. Existing GSD Extensions and Community Patches

### Research findings (MEDIUM confidence — WebSearch not performed; based on package structure analysis)

The GSD codebase shows no built-in extension registry or plugin system. Key observations:

1. **No `extensions/` directory** in the zip — GSD does not ship an extension framework
2. **No plugin hooks** in any workflow file — no `@load-extension` or similar directives
3. **The patch system IS the extension mechanism** — it's the only supported way to modify GSD behavior
4. **The manifest + reapply-patches system** was clearly designed with user modifications in mind — it's not an afterthought

The CHANGELOG.md (57,937 bytes, extensive) likely contains evidence of community-driven features being incorporated upstream, but no extension packages were found in the zip.

**Finding:** GSD Review Team would be among the first (possibly the first) community extension built as a standalone package using the patch system. There are no established patterns to learn from — this project IS establishing the pattern.

---

## 8. Architecture Synthesis

### Integration Point (confirmed)

The correct integration is:

```
execute-plan.md step sequence:
  ...
  update_codebase_map    ← last metadata step
  [review_team_gate]     ← INSERT HERE (conditional on workflow.review_team)
  offer_next             ← unchanged
```

This fires at the right time: SUMMARY.md exists, STATE.md updated, all commits done. Review Team receives a complete, committed artifact.

### File modification surface

| File | Modification Type | Patch Risk |
|------|-------------------|------------|
| `execute-plan.md` | Add one `<step>` block | Low — anchor on `<step name="offer_next">` is stable |
| `settings.md` | Add one question to `AskUserQuestion`, add field to write | Medium — question list order matters |
| `config.json` (per-project) | Add `workflow.review_team: false` | Zero — additive only |

### What does NOT need patching

- `execute-phase.md` — unchanged, passes execution to `execute-plan.md` per plan
- `gsd-tools.cjs` — not needed, `config_content` via `--include config` is sufficient
- Any planning, roadmap, or research workflows — completely untouched
- Agent files — extension ships its own agents, no core agents modified

### The `@` file reference pattern

GSD workflows use `@~/.claude/get-shit-done/...` syntax to load files at runtime. The extension can use the same pattern:

```markdown
@~/.claude/get-shit-done-review-team/workflows/review-team.md
```

This is how `execute-phase.md` already loads `execute-plan.md` into subagents. The extension's `review_team_gate` step can reference the review pipeline the same way.

---

## 9. Key Decisions for Implementation

### Decision 1: Patch delivery mechanism

**Recommended:** Ship `install.sh` that uses pattern-based sed insertion anchored on `<step name="offer_next">`. More robust than line numbers.

```bash
# Find the line containing the offer_next step and insert before it
sed -i "s|<step name=\"offer_next\">|$(cat review_team_gate.xml)\n\n<step name=\"offer_next\">|" \
  "$GSD_WORKFLOWS/execute-plan.md"
```

Or use Python/Node for multi-line insertion without sed quoting nightmares.

### Decision 2: Review Team gate reads config directly

```bash
REVIEW_TEAM_ENABLED=$(jq -r '.workflow.review_team // false' .planning/config.json 2>/dev/null || echo "false")
if [ "$REVIEW_TEAM_ENABLED" != "true" ]; then
  # skip — review team not enabled
  exit 0
fi
```

No gsd-tools changes needed. Simpler, no additional maintenance dependency.

### Decision 3: TEAM.md gate

If `workflow.review_team: true` but `.planning/TEAM.md` doesn't exist:
- Warn the user clearly
- Continue without review (do not block execution)
- Suggest `/gsd:new-reviewer` to create their first role

### Decision 4: Update compatibility

Document explicitly in README:
> "After running `/gsd:update`, run `/gsd:reapply-patches` to restore the Review Team integration."

Consider adding a post-update check script to `install.sh` that sets up a git hook or similar reminder.

---

## 10. Complete config.json Reference for the Extension

Minimal config.json after extension install:

```json
{
  "mode": "interactive",
  "depth": "standard",
  "model_profile": "balanced",
  "commit_docs": true,
  "parallelization": true,
  "workflow": {
    "research": true,
    "plan_check": true,
    "verifier": true,
    "auto_advance": false,
    "review_team": false
  },
  "git": {
    "branching_strategy": "none"
  }
}
```

The extension adds `"review_team": false` to the `workflow` section. It is `false` by default — existing projects are unaffected until the user explicitly sets it to `true` (via `/gsd:settings` after the settings.md patch, or by editing config.json directly).

---

## Confidence Summary

| Area | Confidence | Source |
|------|------------|--------|
| Patch mechanism (install.js) | HIGH | Read from install.js source directly |
| Patch format (verbatim copy, not diff) | HIGH | Read from install.js + reapply-patches.md |
| Update behavior (overwrites, then prompts reapply) | HIGH | Read from update.md + install.js |
| execute-plan.md step sequence | HIGH | Read full file from zip |
| settings.md question/write pattern | HIGH | Read full file from zip |
| config.json schema and workflow section | HIGH | Read from gsd-tools.cjs loadConfig() + settings.md |
| init execute-phase output fields | HIGH | Read from cmdInitExecutePhase() in gsd-tools.cjs |
| config_content --include pattern | HIGH | Read from execute-plan.md init_context step |
| Existing community extensions | LOW | No search performed; zip shows no extension framework |

---

## Open Questions

1. **Does `gsd-tools config-ensure-section` need updating?** Currently it initializes config.json without `workflow.review_team`. The extension's `install.sh` should add this field to any existing config.json. But if a user creates a NEW project without running `install.sh` for that project, `review_team` will be absent and default to `false` via the `// false` jq fallback. This is correct behavior but may be surprising — document it.

2. **Does the reapply-patches AI merge handle XML reliably?** The reapply process uses an AI model to identify user additions and merge them into the new version. For a well-delimited XML `<step>` block, this should work well. For complex multi-section changes, there's more conflict risk. Keep the patch minimal — one `<step>` block only.

3. **REVIEW-REPORT.md per-phase vs global?** Not answered by this research (it's a product decision). The `.planning/phases/XX-name/` location is consistent with how VERIFICATION.md, SUMMARY.md, and UAT.md are stored — per-phase seems right.

4. **`/gsd:new-reviewer` implementation:** The `AskUserQuestion` pattern in settings.md shows the correct approach for multi-step guided conversation. The new-reviewer workflow will follow this pattern for building TEAM.md roles.
