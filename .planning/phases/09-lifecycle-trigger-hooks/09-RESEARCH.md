# Phase 9: Lifecycle Trigger Hooks — Research

**Researched:** 2026-02-26
**Domain:** GSD core workflow patching — Python patch scripts, plan-phase.md, execute-phase.md
**Confidence:** HIGH

---

## Summary

Phase 9 patches two GSD core workflows (plan-phase.md and execute-phase.md) to call
agent-dispatcher.md at two new trigger points: `pre_plan_agent_gate` (before planner spawn in
plan-phase.md) and `post_phase_agent_gate` (after all waves complete in execute-phase.md). The
on-demand invoke path (LIFE-04) via /gsd:team is fully implemented by Phase 8. The post-plan
dispatcher wiring (LIFE-01) is NOT implemented in the currently installed execute-plan.md — the
patch script exists (Phase 7-02) but must have been run against the installed file at install
time. That gap is handled by ensuring install.sh is idempotent and run fresh.

The Phase 9 scope is narrower than the requirements list suggests. LIFE-01 was built in Phase 7
as a patch script and install.sh wiring — it activates when install.sh is run. LIFE-04 was built
in Phase 8 as team-studio.md invoke_on_demand. The genuine new work in Phase 9 is two new Python
patch scripts (one for plan-phase.md, one for execute-phase.md) and two corresponding install.sh
additions in Section 6. The fail-open contract for LIFE-02 is the critical safety invariant: any
error in the pre-plan gate must be caught silently and execution must always reach the planner.

The patch pattern established in Phases 1, 6, and 7 is mature and well-understood. All three
existing patch scripts use the same structure: read file, idempotency check via unique string
presence, anchor string lookup with explicit error on not-found, str.replace(anchor, new_content,
1), write file, print result. Phase 9 patch scripts must follow this exact pattern.

**Primary recommendation:** Build two Python patch scripts following the existing patch-execute-plan-dispatcher.py pattern. Anchor on the unique opening tag of the step that comes immediately after the intended insertion point, inserting the new step before that anchor. Add both scripts to install.sh Section 6 in the correct order. Write the new step bodies to call agent-dispatcher.md with trigger_type="pre-plan" and trigger_type="post-phase" respectively. Wrap the pre-plan gate body in a try/catch-equivalent (bash `|| true` or markdown equivalent) to guarantee fail-open.

---

## What Is Already Done (Scope Reduction)

This is the most critical finding for planning. Phase 9 requirements include four items, two of
which were already implemented in prior phases:

| Requirement | Status | Evidence |
|-------------|--------|----------|
| LIFE-01: review_team_gate calls dispatcher | **BUILT IN PHASE 7** — patch script + install.sh wiring complete | `scripts/patch-execute-plan-dispatcher.py` exists and contains the correct dispatcher-routing step body; install.sh line 175 invokes it. The installed `execute-plan.md` at `~/.claude/get-shit-done/workflows/execute-plan.md` still shows v1 step body, confirming install.sh must be re-run after Phase 9 to apply all patches. |
| LIFE-02: pre_plan_agent_gate in plan-phase.md | **NOT YET BUILT** — new work required | No pre_plan, no agent_gate, no AGENT_STUDIO grep match found in plan-phase.md |
| LIFE-03: post_phase_agent_gate in execute-phase.md | **NOT YET BUILT** — new work required | No pre_plan, no post_phase, no agent_gate grep match found in execute-phase.md |
| LIFE-04: on-demand via /gsd:team | **BUILT IN PHASE 8** — team-studio.md invoke_on_demand step complete | `D:/GSDteams/workflows/team-studio.md` contains `<step name="invoke_on_demand">` with Task() spawn, result display, and AGENT-REPORT.md logging. 08-02-PLAN success criteria explicitly lists "ROST-02, LIFE-04". |

**Conclusion:** Phase 9 genuine new deliverables are:
1. `scripts/patch-plan-phase.py` — inserts pre_plan_agent_gate into plan-phase.md
2. `scripts/patch-execute-phase.py` — inserts post_phase_agent_gate into execute-phase.md
3. `install.sh` updates — Section 6 invocations for both new scripts, and a new Section 2.5 or file variable for plan-phase.md and execute-phase.md paths

---

## Standard Stack

### Core (No External Dependencies)

This is a pure file-patching domain. No npm packages or external libraries.

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Python 3 | any 3.x | Patch script execution | All existing patches use Python3; already a dependency in install.sh |
| bash | POSIX | install.sh orchestration | Already the install.sh shell |
| GSD workflow markdown | n/a | Target files to patch | plan-phase.md, execute-phase.md are the patch targets |
| agent-dispatcher.md | Phase 7 | Called by new trigger points | Already built and installed |

### Patch Script Pattern (Verified from Source)

The exact pattern used in all three existing patch scripts, which Phase 9 MUST follow:

```python
#!/usr/bin/env python3
"""
{script-name}.py — {brief description}

Usage: python3 scripts/{script-name}.py <path-to-target-file>

Idempotency check: '{unique-string-only-in-new-content}' in content
"""
import sys, os

def main():
    if len(sys.argv) < 2:
        print("Usage: ...", file=sys.stderr); sys.exit(1)
    target = sys.argv[1]
    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr); sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Idempotency check — unique string only in NEW content
    if '{unique_string}' in content:
        print(f"  [SKIP] {target} already patched ({description})")
        sys.exit(0)

    # Anchor — must match character-for-character
    anchor = '{exact text from target file}'
    if anchor not in content:
        print(f"ERROR: Anchor not found in {target}", file=sys.stderr)
        print(f"       Expected: {anchor[:60]}...", file=sys.stderr)
        sys.exit(1)

    new_content = '''...'''
    patched = content.replace(anchor, new_content + anchor, 1)  # or replace(anchor, new_content, 1)

    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)
    print(f"  [OK] Patched: {target}")
    print(f"       Inserted: {description}")

if __name__ == '__main__':
    main()
```

**Insert-before pattern:** `content.replace(anchor, new_step + anchor, 1)` — inserts new step before the anchor string. Used by patch-execute-plan.py (inserts review_team_gate before offer_next step opening tag).

**Replace pattern:** `content.replace(anchor, new_step, 1)` — replaces anchor entirely with new step. Used by patch-execute-plan-dispatcher.py (replaces the full step body).

Phase 9 new patches use the **insert-before** pattern — they add new steps before existing steps.

---

## Architecture Patterns

### Patch Script File Layout

```
D:/GSDteams/
└── scripts/
    ├── patch-execute-plan.py               # Phase 1: inserts review_team_gate step
    ├── patch-settings.py                   # Phase 1: adds review_team toggle to settings
    ├── patch-settings-agent-studio.py      # Phase 6: adds agent_studio toggle
    ├── patch-execute-plan-dispatcher.py    # Phase 7: replaces review_team_gate body
    ├── patch-plan-phase.py                 # Phase 9 NEW: inserts pre_plan_agent_gate
    └── patch-execute-phase.py             # Phase 9 NEW: inserts post_phase_agent_gate
```

### install.sh Section 6 Order (Current + Phase 9 Additions)

The order matters: patch-execute-plan.py must run before patch-execute-plan-dispatcher.py
(step must exist before body can be replaced). Phase 9 scripts are independent additions.

```bash
# Section 6: Apply patches (current lines 172-175)
python3 "$EXT_DIR/scripts/patch-execute-plan.py" "$EXECUTE_PLAN"
python3 "$EXT_DIR/scripts/patch-settings.py" "$SETTINGS"
python3 "$EXT_DIR/scripts/patch-settings-agent-studio.py" "$SETTINGS"
python3 "$EXT_DIR/scripts/patch-execute-plan-dispatcher.py" "$EXECUTE_PLAN"
# Phase 9 additions (new):
python3 "$EXT_DIR/scripts/patch-plan-phase.py" "$PLAN_PHASE"
python3 "$EXT_DIR/scripts/patch-execute-phase.py" "$EXECUTE_PHASE"
```

Two new file variables needed in Section 6 preamble (alongside `$EXECUTE_PLAN` and `$SETTINGS`):
```bash
PLAN_PHASE="$GSD_DIR/get-shit-done/workflows/plan-phase.md"
EXECUTE_PHASE="$GSD_DIR/get-shit-done/workflows/execute-phase.md"
```

And the existence checks need to cover the new targets.

### LIFE-02: pre_plan_agent_gate Insertion Point

**Where:** In plan-phase.md, inserted after Step 11/12 (checker + revision loop) and BEFORE Step 13 ("Present Final Status"). The requirement says "fires after the plan-checker step and before plan creation" — but plans are already created by the time the checker runs. The correct interpretation is: fires after the checker/revision cycle completes, before execution proceeds (i.e., before the offer_next or auto-advance steps).

**Anchor string for insertion:** The opening of the "## 13. Present Final Status" section:

```
## 13. Present Final Status
```

**New step body inserts before this anchor.** Pre-plan gate fires advisory pre-plan agents, collects output, injects as `<agent_notes>`. Note: ADVY-01 (full injection into planner prompt) is Phase 10 — Phase 9 only needs the gate to fire and collect; injection is Phase 10's work. For Phase 9, the gate fires and logs/displays, but the notes injection into the planner Task() is deferred.

**Fail-open contract:** Any error in the pre-plan gate (agent timeout, agent failure, TEAM.md missing, dispatcher error) MUST NOT prevent plan creation. The step body must use error-handling language that makes this explicit — if the dispatcher call fails, log the error and continue.

**Agent dispatcher inputs for pre-plan:**
- `trigger_type`: "pre-plan"
- `summary_path`: not applicable (no SUMMARY exists yet) — pass `phase_dir` and `phase_num` instead, or a synthesized placeholder
- `phase_id`: `phase_dir` slug (e.g., "09-lifecycle-trigger-hooks")
- `plan_num`: null or "00" (pre-plan, no plan yet)

Looking at agent-dispatcher.md inputs, `summary_path` is used to derive `plan_path` for bypass flag check. For pre-plan, there is no SUMMARY yet. The dispatcher will attempt to derive plan_path from summary_path and fail gracefully if the file doesn't exist (it uses `grep ... || echo "false"` which is safe). Pass `phase_dir/{phase_num}-00-PLAN.md` as a placeholder or pass an explicit `plan_path` parameter.

**What the pre-plan gate does in plan-phase.md step:**
1. Check if agent_studio is enabled in config
2. If not enabled: skip silently (no output, no log)
3. If enabled: call dispatcher with trigger="pre-plan", collect output
4. Fail-open: if anything fails, log and proceed to Step 13
5. ADVY-01 (inject notes into planner prompt) is Phase 10 — not implemented here

### LIFE-03: post_phase_agent_gate Insertion Point

**Where:** In execute-phase.md, inserted AFTER `aggregate_results` step and BEFORE `close_parent_artifacts` step. Specifically, after the closing `</step>` of `aggregate_results` and before the opening `<step name="close_parent_artifacts">`.

**Anchor string for insertion:**

```
<step name="close_parent_artifacts">
```

**New step body inserts before this anchor.**

**Agent dispatcher inputs for post-phase:**
- `trigger_type`: "post-phase"
- `summary_path`: not a single plan's SUMMARY — pass phase_dir for the agent to find all SUMMARYs
- `phase_id`: `phase_dir` slug (e.g., "09-lifecycle-trigger-hooks")
- `plan_num`: "all" or null (post-phase, covers all plans)

**Output:** Advisory agents write to `.planning/phases/{phase_id}/AGENT-REPORT.md` using the append-with-header format defined in Phase 8: `## Post-Phase: {agent-slug} — {ISO timestamp}`. Autonomous agents commit artifacts directly.

**Agent-dispatcher.md current state:** The dispatcher's `route_by_mode` step currently stubs autonomous agents with "autonomous execution not yet implemented (Phase 9). Skipping." — Phase 9 must ALSO update agent-dispatcher.md's `route_by_mode` step for the post-phase trigger to implement the autonomous execution path. Alternatively, Phase 9 may leave autonomous stub behavior as-is if the Phase 9 scope is limited to the wiring only and autonomous execution follows in a later phase.

**IMPORTANT SCOPE CLARIFICATION:** Looking at agent-dispatcher.md's purpose comment: "Calling point: review_team_gate step in execute-plan.md (Phase 7: post-plan trigger only)". The dispatcher itself is designed to accept pre-plan and post-phase trigger_type values — the filter_by_trigger step handles them. Phase 9's job is to add the calling points, not change the dispatcher logic.

### Pattern: Idempotency Check Strings (Phase 9 Scripts)

For `patch-plan-phase.py`:
- Idempotency check string: `'pre_plan_agent_gate'` in content
- This string is unique to the new step — not present in current plan-phase.md

For `patch-execute-phase.py`:
- Idempotency check string: `'post_phase_agent_gate'` in content
- This string is unique to the new step — not present in current execute-phase.md

---

## Exact Anchor Strings

These must be copied character-for-character into the patch scripts. Verified by reading the
actual files.

### patch-plan-phase.py anchor

The insertion point is before "## 13. Present Final Status". The exact anchor:

```
## 13. Present Final Status
```

This string appears exactly once in plan-phase.md (verified: it's a numbered markdown heading
in the `<process>` section). Inserting before it places the pre_plan_agent_gate after the
checker/revision loop (steps 10-12) and before final status + offer_next.

### patch-execute-phase.py anchor

The insertion point is before `<step name="close_parent_artifacts">`. The exact anchor:

```
<step name="close_parent_artifacts">
```

This string appears exactly once in execute-phase.md. The step ordering is:
`aggregate_results` → [NEW: post_phase_agent_gate] → `close_parent_artifacts` → `verify_phase_goal` → `update_roadmap` → `offer_next`.

This placement is correct: all waves complete (aggregate_results just ran), before the gap-closure cleanup step runs. The post-phase gate fires once per phase execution, not once per wave.

---

## New Step Bodies

### pre_plan_agent_gate step for plan-phase.md

The step must be expressed in the markdown numbered-section format of plan-phase.md (not XML
`<step>` tags — plan-phase.md uses `## N. Step Name` format throughout):

```markdown
## 13. Pre-Plan Agent Gate

Check whether pre-plan agents should fire before presenting final status.

**This gate is ALWAYS fail-open.** Any failure here — dispatcher error, agent timeout,
TEAM.md unreadable, config missing — MUST NOT prevent plan creation. Catch all errors and
proceed to step 14 (present final status) regardless.

```bash
AGENT_STUDIO_ENABLED=$(node C:/Users/gutie/.claude/get-shit-done/bin/gsd-tools.cjs config get workflow.agent_studio 2>/dev/null || echo "false")
```

If `AGENT_STUDIO_ENABLED` is not `"true"`: skip this step entirely — no output, no log.
Proceed directly to step 14.

If `AGENT_STUDIO_ENABLED` is `"true"`:

1. Call the dispatcher:
   ```
   @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
   ```
   Pass: trigger=pre-plan, phase_id={phase_dir}, plan_num=null.

2. If the dispatcher call fails or errors: log
   `Pre-plan gate: dispatcher error — proceeding with plan creation (fail-open)`
   and continue to step 14. Do NOT stop or report failure.

3. Dispatcher output (agent notes, if any) is collected for Phase 10 injection.
   For Phase 9: display notes inline if any agents fired. Injection into planner
   prompt is Phase 10 (ADVY-01).
```

**NOTE:** The existing step numbering in plan-phase.md must shift up by 1 after insertion
(old 13 → 14, old 14 → 15). The patch script handles this by inserting the new step block
before the old "## 13." text — the old step text is preserved as-is after insertion. The
orchestrator running plan-phase.md reads it as a narrative, not by step number, so renumbering
old steps is not strictly required. However, for readability, the patch can either:
- Just insert the new section before "## 13." leaving the old numbers unchanged, or
- Insert as "## 13. Pre-Plan Agent Gate" and rename the old 13 to 13.5 or leave as-is

The safest approach: insert as "## 13. Pre-Plan Agent Gate\n\n" and leave existing "## 13." untouched — the file will have duplicate "## 13." headings, which is non-ideal but won't break execution. Alternatively, insert AFTER the revision loop content with a new heading that doesn't conflict — e.g., insert as a new section named differently, between the revision loop and "## 13." heading. The planner needs clear guidance on this choice.

**ALTERNATIVE ANCHOR APPROACH:** Instead of anchoring on "## 13. Present Final Status", anchor on the text just before it — the end of the iteration >= 3 block. This avoids the numbering conflict entirely:

Exact anchor text (from plan-phase.md lines ~322-327):
```
**If iteration_count >= 3:**

Display: `Max iterations reached. {N} issues remain:` + issue list

Offer: 1) Force proceed, 2) Provide guidance and retry, 3) Abandon

## 13. Present Final Status
```

Using this full block as anchor and inserting pre_plan_agent_gate section (with heading "## 13. Pre-Plan Agent Gate") BEFORE "## 13. Present Final Status" and renaming the old 13 to 14 in the replacement. This is the cleanest approach but requires more precise anchor text.

### post_phase_agent_gate step for execute-phase.md

The step uses the XML `<step>` tag format of execute-phase.md:

```xml
<step name="post_phase_agent_gate">
Check whether post-phase agents should fire after all waves complete.

```bash
AGENT_STUDIO_ENABLED=$(echo "$INIT" | jq -r '.config.workflow.agent_studio // false' 2>/dev/null || echo "false")
```

If `AGENT_STUDIO_ENABLED` is not `"true"`: skip this step entirely — no output, no log.

If `AGENT_STUDIO_ENABLED` is `"true"`:

Check that `.planning/TEAM.md` exists:
```bash
[ -f .planning/TEAM.md ] && echo "EXISTS" || echo "MISSING"
```
If TEAM.md is missing: log `Post-phase gate: no TEAM.md found — skipping` and continue to close_parent_artifacts. Do NOT block execution.

If TEAM.md exists: call the dispatcher:
```
@~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
```
Pass: trigger=post-phase, phase_id={phase_dir}, plan_num=all.

Advisory agent output is written to `.planning/phases/{phase_dir}/AGENT-REPORT.md` by the
dispatcher. Autonomous agents commit artifacts directly per their role definition.

If dispatcher errors: log `Post-phase gate: dispatcher error — skipping (non-blocking)` and
continue to close_parent_artifacts. Do NOT block phase completion.
</step>

```

**Config access in execute-phase.md:** The INIT JSON is loaded at the `initialize` step and contains config data. However, the format differs from execute-plan.md which has `CONFIG_CONTENT` as a shell variable containing the JSON string. In execute-phase.md, config is inside the INIT JSON parsed from `gsd-tools.cjs init execute-phase`. The safest approach is to re-read config.json directly in the gate step:
```bash
AGENT_STUDIO_ENABLED=$(node C:/Users/gutie/.claude/get-shit-done/bin/gsd-tools.cjs config get workflow.agent_studio 2>/dev/null || echo "false")
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config reading in gate steps | Custom jq parsing | `gsd-tools.cjs config get workflow.agent_studio` | Consistent with plan-phase.md pattern; handles missing keys safely |
| Anchor detection | Line-number-based insertion | Exact string match via `anchor not in content` | Line numbers change; exact string is resilient to whitespace changes |
| Error handling in pre-plan gate | Complex try/catch logic | Simple `|| true` or `|| echo "false"` bash fallback + markdown "if fails: log and continue" | The fail-open contract is a prose instruction to the executing LLM, not code; keep it simple |
| Dispatcher contract | New dispatcher call format | Existing `@~/.claude/.../agent-dispatcher.md` with trigger, phase_id, plan_num | Dispatcher already handles all trigger_type values; no new contract needed |

---

## Common Pitfalls

### Pitfall 1: Installing Without Running install.sh
**What goes wrong:** Phase 9 delivers patch scripts, but the GSD core files at `~/.claude/get-shit-done/` are not updated until `bash install.sh` is run in the project directory.
**Why it happens:** Phase 7 already demonstrated this — patch-execute-plan-dispatcher.py exists but the installed execute-plan.md still shows the v1 step body (verified by grep).
**How to avoid:** The verification task for Phase 9 must run `bash install.sh` and then grep the installed files for the new step bodies.
**Warning signs:** Scripts exist in `D:/GSDteams/scripts/` but grepping the installed files shows no new gate steps.

### Pitfall 2: Pre-Plan Gate Step Number Conflict
**What goes wrong:** Inserting "## 13. Pre-Plan Agent Gate" creates two sections numbered 13 in plan-phase.md.
**Why it happens:** plan-phase.md uses numbered sections (## 1., ## 2., etc.) not XML step tags.
**How to avoid:** The patch script should replace the anchor "## 13. Present Final Status" with "## 14. Present Final Status" in the replacement, while inserting "## 13. Pre-Plan Agent Gate" before it. This requires the anchor to include the heading itself and the replacement to include the new heading with renumbered old heading.
**Warning signs:** Two "## 13." sections appear in plan-phase.md after patching.

### Pitfall 3: Anchor String Whitespace Mismatch
**What goes wrong:** Patch script prints "ERROR: Anchor string not found" when run against the installed file.
**Why it happens:** Copy-pasting anchor from documentation rather than reading the actual file. Trailing whitespace, different line endings, or different indentation breaks exact match.
**How to avoid:** The patch script author MUST read the actual installed file and copy the anchor text directly. All existing patch scripts include this warning ("Read file first before writing anchor").
**Warning signs:** Script exits with code 1 on first run.

### Pitfall 4: Post-Phase Gate AGENT-REPORT.md Config Access
**What goes wrong:** `AGENT_STUDIO_ENABLED` reads as "false" even though config.json has it set to true.
**Why it happens:** execute-phase.md doesn't load CONFIG_CONTENT the same way execute-plan.md does. The INIT JSON from `gsd-tools.cjs init execute-phase` does NOT include `config_content` by default (no `--include config` flag).
**How to avoid:** Use `gsd-tools.cjs config get workflow.agent_studio` as the config reader in the post-phase gate step — it reads directly from disk rather than depending on a preloaded variable.
**Warning signs:** Gate fires with "agent_studio disabled" even after config.json has been updated.

### Pitfall 5: ADVY-01 Scope Creep into Phase 9
**What goes wrong:** Phase 9 attempts to inject pre-plan agent notes into the planner Task() prompt — this is ADVY-01, which belongs to Phase 10.
**Why it happens:** LIFE-02 requirement text says "injects as `<agent_notes>` block into planner Task() prompt" — but the Phase 9 goal text only says "fires before plan creation, always fail-open". The injection is Phase 10.
**How to avoid:** Phase 9 pre-plan gate fires the dispatcher and collects/displays output. It does NOT modify the planner Task() call. Phase 10 does the injection.
**Warning signs:** Plan includes tasks modifying the planner spawn in step 8 of plan-phase.md.

### Pitfall 6: Duplicate Patches on Re-run
**What goes wrong:** Running install.sh twice inserts the same gate step twice into plan-phase.md or execute-phase.md.
**Why it happens:** Forgetting idempotency check, or using a non-unique idempotency string.
**How to avoid:** Idempotency strings `'pre_plan_agent_gate'` and `'post_phase_agent_gate'` are unique to the new content and completely absent from the original files (verified). The patch scripts check for these strings before applying.
**Warning signs:** Grep for idempotency string returns multiple occurrences in target file.

---

## Code Examples

### Verified: Dispatcher @-reference call format (from execute-plan.md after Phase 7 patch)

```markdown
If TEAM.md exists:
- If `AGENT_STUDIO_ENABLED` is `"true"`:
  ```
  @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
  ```
  Pass: trigger=post-plan, current SUMMARY.md path, phase identifier, plan identifier.
```
Source: D:/GSDteams/scripts/patch-execute-plan-dispatcher.py (new_step_body variable, lines 80-114)

### Verified: Fail-open handling in GSD workflow prose

The fail-open pattern in GSD markdown workflows uses conditional prose:
```markdown
If the dispatcher call fails or errors: log `{message}` and continue to {next step}. Do NOT stop or report failure.
```
Source: Pattern derived from review_team_gate step in execute-plan.md — "If TEAM.md is missing: log ... and continue to offer_next. Do NOT block execution."

### Verified: Idempotency check pattern

```python
# Idempotency check — unique string only present after the dispatcher patch
if 'agent-dispatcher.md' in content:
    print(f"  [SKIP] {target} already patched (dispatcher already wired)")
    sys.exit(0)
```
Source: D:/GSDteams/scripts/patch-execute-plan-dispatcher.py lines 44-46

### Verified: install.sh file variable + existence check pattern

```bash
EXECUTE_PLAN="$GSD_DIR/get-shit-done/workflows/execute-plan.md"
SETTINGS="$GSD_DIR/get-shit-done/workflows/settings.md"

if [ ! -f "$EXECUTE_PLAN" ]; then
  echo "  ERROR: $EXECUTE_PLAN not found"
  exit 1
fi
```
Source: D:/GSDteams/install.sh lines 159-165

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| review_team_gate calls review-team.md directly (v1) | review_team_gate calls agent-dispatcher.md when agent_studio enabled (v2) | Phase 7 (built); Phase 9 verification confirms it applies after install.sh | LIFE-01 satisfied once install.sh is re-run |
| No pre-plan agent gate in plan-phase.md | pre_plan_agent_gate step inserted by Phase 9 patch | Phase 9 (new work) | LIFE-02 satisfied |
| No post-phase agent gate in execute-phase.md | post_phase_agent_gate step inserted by Phase 9 patch | Phase 9 (new work) | LIFE-03 satisfied |
| On-demand invoke not available | /gsd:team invoke_on_demand step live | Phase 8 complete | LIFE-04 satisfied |
| Autonomous agents stubbed in dispatcher | Autonomous execution still stubbed | Phase 9 does NOT change this | Autonomous agents log "not yet implemented" for post-phase trigger too |

**Deprecated/outdated:**
- LIFE-02 requirement text mentions `<agent_notes>` injection: this is ADVY-01 (Phase 10). Phase 9 only builds the gate trigger — injection is deferred.

---

## Open Questions

1. **How should pre-plan gate pass inputs to dispatcher when no SUMMARY exists?**
   - What we know: dispatcher expects `summary_path`, `phase_id`, `plan_num`; for pre-plan there is no SUMMARY
   - What's unclear: dispatcher derives `plan_path` from `summary_path` for bypass check — what to pass when there's no SUMMARY yet
   - Recommendation: Pass `phase_id` and `plan_num="pre-plan"` and omit `summary_path` (or pass null). The dispatcher's bypass check uses `grep -m1 "^skip_review:" 2>/dev/null || echo "false"` — if file doesn't exist, grep returns empty and `|| echo "false"` returns false, which is safe. This is already handled gracefully.

2. **Should Phase 9 update agent-dispatcher.md's route_by_mode step for autonomous post-phase execution?**
   - What we know: current route_by_mode stubs autonomous agents with "Phase 9. Skipping." — the purpose comment explicitly says Phase 9 implements autonomous execution path
   - What's unclear: the Phase 9 goal text says "Autonomous agents commit artifacts directly" for LIFE-03, but requirements focus on wiring, not implementing autonomous agent execution logic
   - Recommendation: Phase 9 SHOULD update route_by_mode to remove the "Phase 9" stub message and implement the basic autonomous execution path (spawn Task() with role definition + artifact). The purpose comment on agent-dispatcher.md names Phase 9 as the owner of this work.

3. **Step numbering in plan-phase.md after pre_plan_agent_gate insertion**
   - What we know: plan-phase.md has numbered sections ## 1. through ## 14.; inserting a new ## 13. creates a conflict
   - What's unclear: whether duplicate heading numbers affect LLM execution of the workflow
   - Recommendation: The patch script should replace the anchor "## 13. Present Final Status" with the new section + renumbered old section. Specifically: anchor = `\n## 13. Present Final Status\n`, replacement = `\n## 13. Pre-Plan Agent Gate\n\n[new step body]\n\n## 14. Present Final Status\n`, with all subsequent numbers (+1). This is the cleanest approach but requires the anchor to include the old step 13 AND the script to renumber 14 → 15 as well. Simpler: just rename the anchor target rather than trying to renumber everything — this is an internal documentation file, not code.

4. **What happens to the autonomous execution path in LIFE-03 — does Phase 9 fully implement it?**
   - What we know: LIFE-03 says "Autonomous agents commit artifacts directly" and the dispatcher currently stubs them
   - What's unclear: the full autonomous execution specification (what prompt, what commit message, what scope enforcement)
   - Recommendation: Phase 9 should implement basic autonomous execution: spawn Task() for autonomous agents, agent commits via its commit field. Full scope enforcement (allowed_paths, allowed_tools) is a future hardening concern. The Phase 9 planner should make an explicit decision here.

---

## Sources

### Primary (HIGH confidence)

All findings are based on direct file reads of the actual source code.

- `C:/Users/gutie/.claude/get-shit-done/workflows/execute-plan.md` — Confirmed: review_team_gate step still shows v1 body (no dispatcher wiring in installed file); step names and order verified
- `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md` — Confirmed: no pre_plan_agent_gate; numbered section structure verified; "## 13. Present Final Status" anchor confirmed
- `C:/Users/gutie/.claude/get-shit-done/workflows/execute-phase.md` — Confirmed: no post_phase_agent_gate; `<step name="close_parent_artifacts">` anchor confirmed; step order verified
- `D:/GSDteams/scripts/patch-execute-plan-dispatcher.py` — Patch pattern verified; idempotency check pattern confirmed; insert-before vs replace-full patterns documented
- `D:/GSDteams/scripts/patch-execute-plan.py` — Insert-before pattern (anchor + new_step + anchor) confirmed
- `D:/GSDteams/install.sh` — Section 6 ordering confirmed; file variable pattern confirmed; Section 9 completion message confirmed
- `D:/GSDteams/workflows/agent-dispatcher.md` — Input contract verified; trigger_type values confirmed; autonomous stub confirmed
- `D:/GSDteams/workflows/team-studio.md` — LIFE-04 invoke_on_demand fully implemented; AGENT-REPORT.md logging format confirmed
- `D:/GSDteams/.planning/phases/07-agent-dispatcher/07-02-SUMMARY.md` — LIFE-01 built in Phase 7 confirmed; patch script existence and install.sh update confirmed
- `D:/GSDteams/.planning/phases/08-team-roster-gsd-team/08-02-SUMMARY.md` — LIFE-04 built in Phase 8 confirmed
- `D:/GSDteams/.planning/REQUIREMENTS.md` — LIFE-01 through LIFE-04 requirements text confirmed verbatim

---

## Metadata

**Confidence breakdown:**
- Scope (what's already done vs new work): HIGH — verified by direct file reads and grep checks
- Anchor strings for patch scripts: HIGH — verified by reading actual target files
- Patch script pattern: HIGH — verified from three existing scripts using same pattern
- New step body content: MEDIUM — derived from dispatcher contract and existing step bodies; exact wording needs planner discretion
- Numbering conflict in plan-phase.md: MEDIUM — the impact is real but the resolution is a planner choice
- Autonomous execution in LIFE-03: MEDIUM — Phase 9 obligation confirmed by agent-dispatcher.md purpose comment, but implementation details are open questions

**Research date:** 2026-02-26
**Valid until:** 2026-03-28 (stable domain; only changes if GSD core workflows are updated)
