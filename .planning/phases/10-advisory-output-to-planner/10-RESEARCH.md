# Phase 10: Advisory Output to Planner — Research

**Researched:** 2026-02-26
**Domain:** GSD workflow modification — plan-phase.md planner prompt injection, agent-dispatcher.md output_type routing, advisory agent note collection
**Confidence:** HIGH

---

## Summary

Phase 10 is a targeted workflow modification with two deliverables. The first is an update to
`plan-phase.md`'s step 13 (`pre_plan_agent_gate`) to collect notes from pre-plan advisory agents
and inject them into the planner's Task() prompt as an `<agent_notes>` block before the planner
is spawned at step 8. The second is an update to `agent-dispatcher.md`'s `route_by_mode` step to
distinguish between advisory roles with `output_type: notes` (return structured markdown directly
to the calling gate) versus `output_type: findings` (route through the existing synthesizer
pipeline). Both pieces are required for ADVY-01 and ADVY-02 respectively.

The Phase 9 patch already wired `pre_plan_agent_gate` as step 13 and explicitly deferred the
planner injection to Phase 10. The step currently fires the dispatcher, collects output, and
"displays inline" — but the injection into the step 8 Task() prompt is the missing piece. Phase
10 must solve the sequencing problem: the gate fires at step 13 (after planning + checking), but
the planner runs at step 8. This means Phase 10 must restructure plan-phase.md so that the
pre-plan agent gate fires BEFORE the planner spawns (at step 8), not after the checker loop. The
Phase 9 gate position (step 13) was explicitly a "Phase 9 wiring only" compromise; Phase 10 is
the phase where the gate moves earlier or the planner receives the collected notes.

Reading the Phase 9 plan carefully: the gate fires "before plan creation" (LIFE-02), but in
plan-phase.md it was inserted at step 13 which is AFTER the planner and checker have already run.
The Phase 9 research acknowledged this: "fires after the checker/revision cycle completes, before
execution proceeds." The LIFE-02 requirement says "fires after the plan-checker step and before
plan creation" but that is a misstatement in the plan-phase ordering — the planner runs before the
checker. The correct interpretation for Phase 10 is: the gate should fire BEFORE step 8 (planner
spawn), not after. Phase 10 must move the gate earlier OR pass collected notes forward as a
variable to the planner prompt at step 8.

**Primary recommendation:** Phase 10 should (1) move the pre_plan_agent_gate step to execute
BEFORE step 8 (planner spawn) — specifically between step 7 (load context files) and step 8
(spawn planner), and (2) update step 8's planner prompt to include an `<agent_notes>` block when
notes were collected. The gate collects notes, stores them in a variable (`AGENT_NOTES`), and step
8 interpolates them into the planner prompt. The agent-dispatcher.md update routes `output_type:
notes` roles to a direct-return path rather than the synthesizer pipeline.

---

## What Phase 9 Built (Scope Baseline)

Understanding Phase 9's deliverables is critical before planning Phase 10.

| Artifact | What It Does | Phase 10 Impact |
|----------|-------------|-----------------|
| `scripts/patch-plan-phase.py` | Inserts pre_plan_agent_gate as step 13 in plan-phase.md | Phase 10 must either update this patch script or write a new one that moves the gate to step 7.5 |
| `plan-phase.md` (installed) | Step 13: calls dispatcher with trigger=pre-plan, displays output, explicitly defers ADVY-01 injection | Phase 10 must modify step 13 body (or move it) and update step 8 planner prompt |
| `scripts/patch-execute-phase.py` | Inserts post_phase_agent_gate into execute-phase.md | Phase 10 does NOT touch this |
| `install.sh` | Invokes both Phase 9 patch scripts | Phase 10 install.sh changes are only needed if a new patch script is added |

**Step 13 in plan-phase.md currently says:**
> "Dispatcher output (agent notes, if any) is collected and displayed inline.
> Injection into the planner Task() prompt is Phase 10 (ADVY-01) — not implemented here."

Phase 10 must fulfill this deferred injection.

---

## The Sequencing Problem

This is the central architectural challenge for Phase 10.

**Current flow in plan-phase.md:**
1. Steps 1-7: Initialize, research, load context files
2. **Step 8: Spawn planner** — plans are created here
3. Steps 9-12: Checker + revision loop
4. **Step 13: Pre-Plan Agent Gate** — dispatcher fires here (WRONG POSITION for injection)
5. Step 14: Present final status

**Problem:** Step 13 fires AFTER the planner has already completed. Notes collected at step 13
cannot be injected into the step 8 Task() call — that Task() has already returned.

**Required flow for Phase 10:**
1. Steps 1-7: Initialize, research, load context files
2. **NEW Step 7.5 (or renamed Step 8): Pre-Plan Agent Gate** — dispatcher fires, notes collected
3. **Step 8 (renumbered): Spawn planner** — planner prompt includes `<agent_notes>` block
4. Steps 9-12: Checker + revision loop
5. ~~Step 13: Pre-Plan Agent Gate~~ — this step's gate logic MOVES EARLIER
6. Step 13 (renumbered): Present final status (was step 14)
7. Step 14 (renumbered): Auto-Advance Check (was step 15)

**Resolution options:**

| Option | Description | Tradeoff |
|--------|-------------|----------|
| **Option A: Move gate earlier (RECOMMENDED)** | Remove gate from step 13, add it between steps 7 and 8. Update patch-plan-phase.py to target new anchor. | Clean; gate fires before planner as intended; requires updating existing step 13 body and adding new gate before step 8. Two patch script updates. |
| **Option B: Two-pass gate** | Keep step 13 gate as-is, add a SECOND gate call before step 8 that collects notes and stores them. | Dispatcher fires twice; wasteful; confusing. Rejected. |
| **Option C: Store and defer** | Modify step 13 to store notes in a file, modify step 8 to read that file before spawning planner. | Step 13 still runs AFTER planner; notes stored but never injected into first planner call. Broken semantics. Rejected. |

**Option A is the only architecturally correct approach.** The gate moves before the planner.

---

## Architecture Patterns

### Recommended: Move Gate Earlier + Update Planner Prompt

**What changes in plan-phase.md:**

1. Step 13 body changes: remove the dispatcher call. Step 13 becomes just "Present Final Status"
   (renumbered from step 14). Step 14 becomes "Auto-Advance Check" (renumbered from step 15).

2. Between step 7 (context loading) and step 8 (planner spawn), insert the pre-plan agent gate:

```markdown
## 8. Pre-Plan Agent Gate
<!-- step: pre_plan_agent_gate -->

Check whether pre-plan agents should fire before creating plans.

**This gate is ALWAYS fail-open.** Any failure — dispatcher error, agent timeout, TEAM.md
unreadable, config missing — MUST NOT prevent plan creation. Set AGENT_NOTES="" and proceed
to step 9 (spawn planner) regardless.

```bash
AGENT_NOTES=""
AGENT_STUDIO_ENABLED=$(node C:/Users/gutie/.claude/get-shit-done/bin/gsd-tools.cjs config get workflow.agent_studio 2>/dev/null || echo "false")
```

If `AGENT_STUDIO_ENABLED` is not `"true"`: set AGENT_NOTES="" and proceed to step 9.

If `AGENT_STUDIO_ENABLED` is `"true"`:

1. Check that `.planning/TEAM.md` exists. If missing: log
   `Pre-plan gate: no TEAM.md found — skipping` and set AGENT_NOTES="" and proceed to step 9.

2. If TEAM.md exists: call the dispatcher:
   ```
   @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
   ```
   Pass: trigger=pre-plan, phase_id={phase_dir}, plan_num=pre-plan.

3. If dispatcher call fails or errors: log
   `Pre-plan gate: dispatcher error — proceeding with plan creation (fail-open)`
   Set AGENT_NOTES="" and proceed to step 9.

4. If dispatcher returns advisory notes from `output_type: notes` agents:
   Set AGENT_NOTES to the formatted `<agent_notes>` block (see format below).

5. Log: `Pre-plan gate: {N} advisory agent(s) fired. Notes collected: {yes|no}`

## 9. Spawn gsd-planner Agent
```

3. Step 9's planner prompt includes the `<agent_notes>` block when `AGENT_NOTES` is non-empty:

```markdown
{context_content}

**Research:** {research_content}

{AGENT_NOTES}
```

### agent_notes Block Format

```xml
<agent_notes>
Advisory agents ran before this plan was created. These notes are INPUT — incorporate them
where relevant, or explicitly disregard with a brief note. Always produce a plan.

{for each notes agent that fired:}
## {agent.name} Notes

{agent.structured_markdown_output}

{end for}
</agent_notes>
```

The block is only included when AGENT_NOTES is non-empty. When no pre-plan advisory agents
with `output_type: notes` fired, the planner prompt does not include any `<agent_notes>` block.

### Dispatcher Changes for output_type: notes

The dispatcher's current `route_by_mode` step routes all advisory roles to `review-team.md`.
Phase 10 must split the advisory routing by `output_type`:

```
advisory_notes_roles   = [r for r in advisory_roles if r.output_type == "notes"]
advisory_findings_roles = [r for r in advisory_roles if r.output_type != "notes"]
```

**advisory_findings_roles** (output_type: findings or default): Continue to review-team.md as
before. No change to the existing pipeline.

**advisory_notes_roles** (output_type: notes): Spawn each agent with a Task() that instructs
them to return structured markdown. Collect return values. Format as `<agent_notes>` block.
Return the collected notes to the calling gate.

The dispatcher returns the collected notes to the pre_plan_agent_gate step. The gate stores them
in AGENT_NOTES for injection into the planner prompt.

---

## Standard Stack

### Core (No External Dependencies)

This is a pure workflow modification. No npm packages or external libraries.

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Python 3 | any 3.x | Patch script for plan-phase.md update | All existing patches use Python 3 |
| bash | POSIX | install.sh orchestration | Already the install.sh shell |
| GSD workflow markdown | n/a | plan-phase.md and agent-dispatcher.md are the modification targets | These are the wiring points |
| agent-dispatcher.md | Phase 7 | Routes pre-plan agents, now split by output_type | Already built |

### No New Files Required

Phase 10 modifies existing files only:

| File | Change Type | What Changes |
|------|------------|--------------|
| `D:/GSDteams/scripts/patch-plan-phase.py` | Update or replace | New anchor, new gate position (before step 8 not after step 12), new step numbering |
| `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md` | Patch target | Gate moves earlier, planner prompt gains `<agent_notes>` block |
| `D:/GSDteams/workflows/agent-dispatcher.md` | Direct modification | route_by_mode step splits advisory_roles by output_type |

No new agent files. No new workflow files. No install.sh changes unless the patch script
filename changes (it doesn't — patch-plan-phase.py is reused with updated content).

---

## Exact Current State of plan-phase.md (Phase 9 outcome)

These are the exact headings in the installed file after Phase 9:

```
## 8. Spawn gsd-planner Agent   (line ~156)
...planner prompt...Task() call (lines 167-215)...

## 9. Handle Planner Return     (line ~217)
## 10. Spawn gsd-plan-checker Agent (line ~223)
## 11. Handle Checker Return    (line ~272)
## 12. Revision Loop (Max 3 Iterations)  (line ~278)
...
## 13. Pre-Plan Agent Gate      (line 328)  <- gate currently HERE (wrong position)
<!-- step: pre_plan_agent_gate -->
...dispatcher call...displays inline...ADVY-01 deferred...

## 14. Present Final Status     (line ~362)
## 15. Auto-Advance Check       (line ~366)
```

**After Phase 10, the target layout:**

```
## 8. Pre-Plan Agent Gate       <- gate moved HERE (before planner)
<!-- step: pre_plan_agent_gate -->
...dispatcher call...collects AGENT_NOTES...

## 9. Spawn gsd-planner Agent   <- was step 8, planner prompt includes {AGENT_NOTES}
...planner prompt with <agent_notes> block...

## 10. Handle Planner Return    <- was step 9
## 11. Spawn gsd-plan-checker Agent  <- was step 10
## 12. Handle Checker Return    <- was step 11
## 13. Revision Loop (Max 3 Iterations)  <- was step 12
## 14. Present Final Status     <- was step 14 (unchanged number)
## 15. Auto-Advance Check       <- was step 15 (unchanged number)
```

Note: Steps 14 and 15 retain their numbers because step 13 (old gate) is removed and replaced
by the new step 8 (gate moves earlier). Net effect: steps 8-13 each shift up by 1, steps 14-15
stay the same.

---

## Patch Script Strategy

The existing `patch-plan-phase.py` must be replaced with a new version. The Phase 9 patch is
already applied to the installed `plan-phase.md` — Phase 10 must work on the ALREADY-PATCHED
file.

### Patch Strategy for Already-Patched File

The installed plan-phase.md already has:
- `<!-- step: pre_plan_agent_gate -->` at line 329 (idempotency marker)
- The dispatcher call in step 13 body (to be replaced with "Present Final Status")
- Steps 8-15 as numbered above

Phase 10 patch script (`patch-plan-phase-phase10.py` or updated `patch-plan-phase.py`) needs to:

1. **Idempotency check:** Look for `AGENT_NOTES` variable or `agent_notes` XML tag in content.
   If present: already patched for Phase 10, exit 0 with SKIP.

2. **Remove old step 13 gate body:** Replace the old step 13 gate content with just
   "Present Final Status" content (what was step 14).

3. **Insert new gate before step 8:** Insert the new pre_plan_agent_gate step before
   `## 8. Spawn gsd-planner Agent`.

4. **Update step 8 planner prompt:** Add the `{AGENT_NOTES}` interpolation to the planner
   prompt template inside the Task() call.

5. **Renumber steps 8-13** to account for the new step 8 insertion.

**Anchor strings needed:**

```python
# Anchor 1: Insert new gate BEFORE old step 8
anchor_before_planner = '\n## 8. Spawn gsd-planner Agent\n'

# Anchor 2: Remove old step 13 gate body (replace with Present Final Status)
anchor_old_gate = '\n## 13. Pre-Plan Agent Gate\n<!-- step: pre_plan_agent_gate -->\n'

# Anchor 3: Add AGENT_NOTES to planner prompt — target the closing of planning_context
# The planner prompt ends with:
anchor_planner_prompt_end = '\n**Research:** {research_content}\n**Gap Closure'
```

**WARNING:** Read the installed plan-phase.md BEFORE writing the Phase 10 patch script.
The exact text must be verified character-for-character. The Phase 9 research had
`## 14. Auto-Advance Check` as the second rename — Phase 10 must account for the fact
that this is now `## 15. Auto-Advance Check`.

### Alternative Approach: Two Separate Patch Scripts

To reduce complexity, Phase 10 could deliver:

1. `patch-plan-phase-10a.py` — Moves gate: removes old step 13 gate body, inserts new gate
   before step 8, renumbers steps.
2. `patch-plan-phase-10b.py` — Adds `{AGENT_NOTES}` interpolation to the planner prompt.

Each script is simpler and independently idempotent. The tradeoff is two scripts in install.sh.
This is the RECOMMENDED approach for Phase 10 to keep each script focused.

---

## Dispatcher Changes (ADVY-02)

The dispatcher's `route_by_mode` step currently routes ALL advisory roles to review-team.md.
Phase 10 must split this by `output_type`.

### Current route_by_mode (advisory path):

```
If advisory_roles is non-empty:
  Call review-team.md with SUMMARY_PATH, PHASE_ID, PLAN_NUM
```

### Required route_by_mode after Phase 10:

```
Split advisory_roles by output_type:
  advisory_notes_roles    = [r for r in advisory_roles if r.output_type == "notes"]
  advisory_findings_roles = [r for r in advisory_roles if r.output_type not in ["notes"]]

If advisory_findings_roles is non-empty AND trigger_type == "post-plan":
  Call review-team.md (unchanged behavior)

If advisory_notes_roles is non-empty AND trigger_type == "pre-plan":
  For each role in advisory_notes_roles:
    Spawn Task() to fire the advisory agent
    Collect structured markdown return
  Format collected notes as <agent_notes> block
  Return the <agent_notes> block to the calling gate step
```

**Key constraint:** The review-team.md path is only correct for post-plan trigger. A pre-plan
advisory agent with `output_type: findings` should NOT go through review-team.md because there
is no SUMMARY.md to sanitize. For pre-plan + findings, the safest behavior is: log a warning
("pre-plan advisory agent with output_type: findings is not supported — use output_type: notes
for pre-plan agents") and skip.

**Dispatcher input for pre-plan advisory notes agents:**

Each notes agent is spawned as a Task() with:
- The phase description / context as input
- Their role definition from TEAM.md
- Instructions to return structured markdown

The agent has no artifact to review (no SUMMARY, no ARTIFACT.md) — it operates on the phase
context (phase goal, requirements, roadmap state). The dispatcher must pass this context.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Collecting agent notes | Custom aggregation loop | Task() calls on each advisory notes agent, collect returns | Task() is the established agent spawn pattern; no new infrastructure needed |
| Passing notes to planner | File-based note storage (write to disk, read at step 8) | AGENT_NOTES variable interpolated directly | The planner prompt is built as a string in plan-phase.md; variable interpolation is the correct pattern, matching how `context_content`, `research_content` etc. are passed |
| Routing advisory vs findings roles | New dispatcher | Modify existing route_by_mode step | The dispatcher already has the output_type field from normalizeRole; just split the logic |
| Agent notes format | Free-form output | Structured markdown with section headers per agent | The planner must be able to skim notes efficiently; structured format is parseable |

---

## Common Pitfalls

### Pitfall 1: Gate Fires After Planner
**What goes wrong:** Step 13 (current position) gate fires after the planner has already returned.
Notes are collected but cannot be injected into the planner's Task() — that call has completed.
**Why it happens:** Phase 9 inserted the gate at step 13 as a placeholder, explicitly deferring
ADVY-01 injection to Phase 10. The gate position was always wrong for actual injection.
**How to avoid:** Phase 10 MUST move the gate before step 8 (planner spawn). The plan must
explicitly require this re-positioning — it is not optional.
**Warning signs:** Plan proposes "storing notes in a file" or "reading notes before spawning
planner" without moving the gate to before step 8.

### Pitfall 2: Anchor String Mismatch on Already-Patched File
**What goes wrong:** Patch script uses anchors from the ORIGINAL plan-phase.md (before Phase 9),
but Phase 10 targets the ALREADY-PATCHED file (which has different step numbers and the
pre_plan_agent_gate step).
**Why it happens:** Assuming the same anchors from Phase 9 research are still valid.
**How to avoid:** Read the INSTALLED plan-phase.md (`C:/Users/gutie/.claude/get-shit-done/
workflows/plan-phase.md`) immediately before writing any Phase 10 patch script. Use anchors
from the Phase 9-patched file, not the original.
**Warning signs:** Patch script exits with "ERROR: Anchor string not found".

### Pitfall 3: Planner Receives Empty agent_notes Block
**What goes wrong:** `<agent_notes>` block appears in planner prompt even when no advisory
notes agents fired (empty block with no content).
**Why it happens:** AGENT_NOTES variable is set to the `<agent_notes>` skeleton but no agents
populated it.
**How to avoid:** Only include the `<agent_notes>` block in the planner prompt when AGENT_NOTES
is non-empty (i.e., when at least one notes agent returned content). Use conditional inclusion.
**Warning signs:** Planner output says "No agent notes provided" or planner gets confused by
an empty notes block.

### Pitfall 4: review-team.md Called for Pre-Plan Findings Agents
**What goes wrong:** An advisory pre-plan agent with `output_type: findings` triggers the
review-team.md pipeline, which expects a SUMMARY.md and ARTIFACT.md — neither of which exist
at pre-plan time. The sanitizer fails. The pipeline halts (fail-open still applies, but it's
messy).
**Why it happens:** Phase 10 dispatcher change routes all advisory roles to review-team.md
without distinguishing trigger_type.
**How to avoid:** The dispatcher update must gate the review-team.md call on trigger_type ==
"post-plan". For pre-plan trigger, advisory findings agents should log a warning and be skipped.
**Warning signs:** Sanitizer agent fails during /gsd:plan-phase with "SUMMARY.md not found".

### Pitfall 5: ADVY-02 Without ADVY-01
**What goes wrong:** Dispatcher is updated to return structured markdown for notes agents, but
the pre_plan_agent_gate step in plan-phase.md is not updated to inject the returned notes into
the planner prompt.
**Why it happens:** Building ADVY-02 (dispatcher routing) without the corresponding ADVY-01
(planner injection) gate update.
**How to avoid:** ADVY-01 and ADVY-02 are a coupled pair. Both must be implemented in Phase 10.
The plan should have tasks for both changes, verified together in a success criterion that
confirms end-to-end: agent fires → notes collected → notes appear in planner prompt.
**Warning signs:** Dispatcher correctly returns notes but planner prompt doesn't include them.

### Pitfall 6: Step Renumber Collision
**What goes wrong:** After moving the gate before step 8 and inserting a new step 8, there
are duplicate step numbers (two "## 8." headings or gaps in numbering).
**Why it happens:** The patch script inserts new step 8 but doesn't renumber old steps 8-13
to 9-14.
**How to avoid:** The patch script must perform sequential renaming: old 13 → 14 (handled in
Phase 9's second str.replace), and new insertions must use the correct numbers. Verify with
`grep "## [0-9]*\." plan-phase.md` after patching.
**Warning signs:** Two sections with the same step number appear in plan-phase.md.

---

## Code Examples

### Pattern: Variable Interpolation in Planner Prompt (verified from plan-phase.md)

The existing planner prompt in plan-phase.md uses direct variable interpolation in a markdown
code block. The AGENT_NOTES variable follows the same pattern:

```markdown
**Research:** {research_content}
**Gap Closure (if --gaps):** {verification_content} {uat_content}

{AGENT_NOTES}
```

Source: `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md` lines 186-188 (verified)

### Pattern: Conditional Block Inclusion in Plan-Phase Workflow

The existing pattern for conditional content in plan-phase.md:

```markdown
If `context_content` is not null, display: `Using phase context from: ${PHASE_DIR}/*-CONTEXT.md`
```

The same pattern applies to AGENT_NOTES inclusion:

```markdown
If `AGENT_NOTES` is non-empty: include it in the planner prompt.
If `AGENT_NOTES` is empty: omit the block entirely.
```

### Pattern: Agent Notes Return Format (advisory notes agent output)

Advisory notes agents (`output_type: notes`) return structured markdown:

```markdown
## Advisory Notes: {phase goal area}

**Key observation:** {finding}

**Recommendation:** {specific suggestion for the planner}

**Confidence:** HIGH | MEDIUM | LOW

---
```

The dispatcher wraps all collected notes in `<agent_notes>` tags:

```xml
<agent_notes>
Advisory agents ran before this plan was created. These notes are INPUT — incorporate them
where relevant, or explicitly disregard with a brief note. Always produce a plan.

## {agent.name}

{agent.structured_markdown_output}

</agent_notes>
```

### Pattern: Dispatcher output_type Split (pseudo-code for route_by_mode update)

```
# Split advisory roles by output_type
advisory_notes_roles    = [r for r in advisory_roles if r.output_type == "notes"]
advisory_findings_roles = [r for r in advisory_roles if r.output_type != "notes"]

# Handle findings roles (post-plan only)
if advisory_findings_roles is non-empty:
  if trigger_type == "post-plan":
    Call review-team.md (unchanged)
  else:
    Log: "Advisory findings agents ignored for trigger '{trigger_type}' — use output_type: notes for pre-plan agents"

# Handle notes roles (pre-plan)
if advisory_notes_roles is non-empty:
  collected_notes = []
  For each role in advisory_notes_roles:
    Spawn Task() with role definition + phase context
    Collect structured markdown return
    Append to collected_notes
  Build and return <agent_notes> block from collected_notes
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No pre-plan advisory gate | Step 13 gate wired (but injection deferred) | Phase 9 | Gate fires but notes not injected into planner |
| Advisory notes: no routing path | output_type: notes → direct return (Phase 10) | Phase 10 | New notes path enables planner injection |
| All advisory roles → review-team.md | Advisory roles split by output_type | Phase 10 | findings → review pipeline; notes → direct return |
| Planner has no advisory context | Planner receives `<agent_notes>` block | Phase 10 | Planner can incorporate or explicitly disregard |

**Deprecated/outdated after Phase 10:**
- Step 13 body with "ADVY-01 not implemented here" comment — removed in Phase 10
- Dispatcher stub "autonomous not yet implemented (Phase 9)" note — was Phase 9 scope; if still
  present, Phase 10 does NOT need to fix it (out of scope)

---

## Delivery Plan (Suggested)

Phase 10 is cleanly deliverable in 2 plans:

### Plan 10-01: Move Gate + Update Planner Prompt

**Deliverables:**
- Updated `patch-plan-phase.py` (replaces Phase 9 version) that works on the already-patched
  plan-phase.md to move the gate before step 8 and inject AGENT_NOTES into planner prompt
- Applied patch to installed plan-phase.md

**Verification:** Gate is now step 8; planner is step 9; planner prompt template includes
`{AGENT_NOTES}` block; step 13 body no longer contains the dispatcher call; step numbers are
consistent with no duplicates.

### Plan 10-02: Dispatcher output_type Routing

**Deliverables:**
- Updated `agent-dispatcher.md` (route_by_mode step) that splits advisory roles by output_type,
  returns collected notes for pre-plan trigger, routes findings roles to review-team.md for
  post-plan trigger only

**Verification:** A pre-plan advisory agent with `output_type: notes` fires and its structured
markdown appears in the planner's Task() prompt as `<agent_notes>`. A pre-plan advisory agent
with `output_type: findings` logs a warning and is skipped (does not call review-team.md).

---

## Open Questions

1. **How does the dispatcher return collected notes to plan-phase.md's gate step?**
   - What we know: Task() returns a string. The dispatcher workflow returns text. The gate
     step reads the dispatcher's return value.
   - What's unclear: The dispatch call is `@~/.../agent-dispatcher.md` — how does this
     workflow communicate a return value (the `<agent_notes>` block) back to the calling step?
     Looking at review-team.md, it returns structured markdown to the calling step (the
     review_team_gate reads its return). The same pattern applies here.
   - Recommendation: The dispatcher returns the `<agent_notes>` block as part of its output
     text. The pre_plan_agent_gate step reads the dispatcher return and extracts/stores
     the `<agent_notes>` block in AGENT_NOTES. This is the same pattern used everywhere else
     in GSD for subagent communication — return value is parsed from the text response.

2. **What context does a pre-plan advisory notes agent receive?**
   - What we know: There is no SUMMARY.md or ARTIFACT.md at pre-plan time. The agent has
     access to phase description, requirements, roadmap, CONTEXT.md.
   - What's unclear: Does the dispatcher pass this context, or does the notes agent read
     these files itself?
   - Recommendation: The dispatcher passes the phase context (phase_id, phase description,
     requirements section) in the Task() prompt. The notes agent reads phase-specific files
     via its own tool calls. This is consistent with how gsd-reviewer.md receives its inputs.

3. **Should patch-plan-phase.py be updated in-place or replaced with a new script?**
   - What we know: Phase 9's patch-plan-phase.py applied its patch to plan-phase.md already.
     The Phase 10 script must work on the already-patched file.
   - What's unclear: Whether a single updated script handles both Phase 9 and Phase 10
     idempotency, or whether a new Phase 10 script is added separately.
   - Recommendation: Write a new `patch-plan-phase-p10.py` that has its own idempotency
     check (looks for `AGENT_NOTES` or `agent_notes`), targets the Phase-9-patched file,
     and applies the Phase 10 changes only. This keeps Phase 9 and Phase 10 changes
     independently reversible. install.sh adds the new script after the existing one.

---

## Sources

### Primary (HIGH confidence)

All findings based on direct file reads of actual source files.

- `C:/Users/gutie/.claude/get-shit-done/workflows/plan-phase.md` — Current state verified:
  step 13 gate position, step 8 planner prompt template, step numbering (8-15), planner
  Task() call structure, variable interpolation pattern
- `D:/GSDteams/workflows/agent-dispatcher.md` — Current route_by_mode step verified: all
  advisory roles go to review-team.md; output_type split does not exist yet; autonomous stub
  language confirmed
- `D:/GSDteams/scripts/patch-plan-phase.py` — Phase 9 patch script verified: idempotency
  string, anchor pattern, step renaming logic
- `D:/GSDteams/.planning/phases/09-lifecycle-trigger-hooks/09-RESEARCH.md` — Phase 9 research
  confirms Phase 10 scope: "Injection into the planner Task() prompt is ADVY-01 (Phase 10)"
- `D:/GSDteams/.planning/phases/09-lifecycle-trigger-hooks/09-01-SUMMARY.md` — Phase 9 Plan 01
  decisions: idempotency string embedded as HTML comment, step renumbering pattern
- `D:/GSDteams/.planning/REQUIREMENTS.md` — ADVY-01 and ADVY-02 requirements verified verbatim
- `D:/GSDteams/.planning/ROADMAP.md` — Phase 10 goal and success criteria verified

### Tertiary (LOW confidence — not verified against external sources)

- Advisory agent notes format: derived from the requirement that notes are "structured markdown"
  (ADVY-02) and from the `<agent_notes>` block name (ADVY-01). The exact format is not specified
  in requirements and is a planner discretion item.

---

## Metadata

**Confidence breakdown:**
- Sequencing problem (gate must move earlier): HIGH — directly verified by reading plan-phase.md
  step ordering
- Dispatcher output_type split: HIGH — requirements ADVY-01/ADVY-02 are unambiguous; current
  dispatcher code confirmed to lack this split
- Patch script strategy: MEDIUM — the two-script approach (Phase 9 + Phase 10 separate) is
  recommended but the planner may choose to consolidate
- agent_notes format: LOW — not specified in requirements; planner has discretion on exact format
- Dispatcher return value communication: MEDIUM — inferred from existing GSD subagent patterns;
  not explicitly documented

**Research date:** 2026-02-26
**Valid until:** 2026-03-28 (stable domain; only changes if plan-phase.md or agent-dispatcher.md
are modified outside Phase 10)
