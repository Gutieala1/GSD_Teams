# Phase 7: Agent Dispatcher - Research

**Researched:** 2026-02-26
**Domain:** GSD workflow routing layer — TEAM.md parsing, trigger-based dispatch, existing pipeline passthrough
**Confidence:** HIGH — all findings verified directly from GSD source files and prior planning artifacts on disk

---

## Summary

Phase 7 delivers `agent-dispatcher.md`, the single routing layer that sits between GSD core
workflow trigger points and the downstream execution paths (review pipeline, autonomous agents,
advisory collection). The dispatcher reads TEAM.md, applies the normalizeRole algorithm from
the Phase 6 parser spec, filters roles by the current trigger context, and routes appropriately.
For the post-plan advisory path specifically, it delegates to the unchanged `review-team.md`
pipeline, preserving identical REVIEW-REPORT.md output. When no roles match the trigger, it
exits immediately with zero Task() spawns.

The architectural foundation is fully built. ARCHITECTURE.md contains the authoritative parser
specification (normalizeRole algorithm, version detection rule, defaults table). templates/TEAM.md
demonstrates the v2 schema with scope.allowed_paths and scope.allowed_tools. The live
`.planning/TEAM.md` remains at v1 (version: 1, three starter roles) — the normalizeRole shim
handles this transparently. The dispatcher must be written as a GSD workflow (XML step blocks,
purpose/inputs/step structure), installed via `@`-reference from the modified `review_team_gate`
step in execute-plan.md, and deployed via the existing install.sh + file-copy mechanism.

The only novel design decision in this phase is the bypass flag mechanism for DISP-03. The
flag lives in the PLAN.md YAML frontmatter as `skip_review: true`. The dispatcher checks for
this context signal and exits immediately if detected. The mechanism requires the review_team_gate
step to extract and pass the flag from the current PLAN.md into the dispatcher call. No changes
to gsd-tools.cjs are needed — the flag can be read from the PLAN.md file directly.

**Primary recommendation:** Build agent-dispatcher.md as a GSD workflow file with four steps
(check config + bypass, read/parse TEAM.md, filter by trigger, route by mode), wire it into the
existing review_team_gate via a patch to execute-plan.md, and add the patch to install.sh.
Phase 7 scope is strictly post-plan wiring — pre-plan and post-phase hooks belong to Phase 9.

---

## Standard Stack

### Core (no new dependencies)

| Component | Version/Tool | Purpose | Why Standard |
|-----------|-------------|---------|--------------|
| GSD workflow `.md` with XML step blocks | GSD conventions | agent-dispatcher.md file structure | Every GSD workflow uses `<step name="...">` pattern |
| Python3 patch script | Python 3 (existing) | Idempotent text patch to execute-plan.md review_team_gate body | Proven pattern from patch-execute-plan.py |
| Claude Read tool | — | YAML parsing of TEAM.md (version field, roles list, role YAML blocks) | Only reliable YAML parser in GSD workflow context; jq cannot parse YAML |
| `@`-reference syntax | GSD | Loading agent-dispatcher.md from review_team_gate step | Same pattern as current review-team.md call |
| `jq` + `CONFIG_CONTENT` | existing | Read agent_studio and review_team flags from config.json | Already in scope in execute-plan.md; no re-read needed |

### No New Dependencies

Zero new npm packages, zero new Python libraries, zero new tools. This phase introduces one
new workflow file and one patch update. All patterns already proven in the v1.0 codebase.

---

## Architecture Patterns

### Verified Current review_team_gate Step (HIGH confidence — read from execute-plan.md)

The current step body in `~/.claude/get-shit-done/workflows/execute-plan.md`:

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

**What changes in Phase 7:** The step body changes from calling `review-team.md` directly to
calling `agent-dispatcher.md` with `trigger: post-plan`. The step name and location are
unchanged. The idempotency check string `name="review_team_gate"` remains valid.

**What stays the same:** Step name, location (between `update_codebase_map` and `offer_next`),
CONFIG_CONTENT reading pattern, TEAM.md existence check, no-op on disabled, no-op on missing
TEAM.md.

### Dispatcher File Structure (GSD Workflow Convention)

agent-dispatcher.md must follow the GSD workflow file structure:

```
<purpose>
[description of what the workflow does]
</purpose>

<inputs>
[document all inputs passed by calling workflow]
</inputs>

<step name="check_bypass_and_config" priority="first">
[...]
</step>

<step name="read_and_parse_team_md">
[...]
</step>

<step name="filter_by_trigger">
[...]
</step>

<step name="route_by_mode">
[...]
</step>
```

File location (installed path): `~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md`
File location (source path): `D:/GSDteams/workflows/agent-dispatcher.md`

### Dispatcher Data Flow (from ARCHITECTURE.md — HIGH confidence)

```
Inputs from review_team_gate:
  trigger_type: "post-plan"
  summary_path: ".planning/phases/XX-name/XX-NN-SUMMARY.md"
  phase_id: "07-agent-dispatcher"
  plan_num: "01"
  bypass_flag: false  (or true for agent creation plans)

Step 1: check_bypass_and_config
  - If bypass_flag == true: log skip, return immediately (DISP-03)
  - Read AGENT_STUDIO_ENABLED from CONFIG_CONTENT (already in scope via calling workflow)
  - If review_team_enabled AND agent_studio disabled: call review-team.md directly (v1 passthrough)
  - If agent_studio enabled: proceed to full dispatcher logic

Step 2: read_and_parse_team_md
  - Read .planning/TEAM.md
  - Extract version from frontmatter (default: 1)
  - For each role: apply normalizeRole(role, version)
  - Result: list of normalized roles with all 8 fields populated

Step 3: filter_by_trigger
  - Keep only roles where role.trigger == trigger_type
  - If zero matches: log "Agent Dispatcher: no agents for trigger {trigger_type} — no-op"
    Return immediately. Zero Task() spawns. (DISP-02)
  - If matches found: group by mode

Step 4: route_by_mode
  - advisory roles (any trigger): call review-team.md pipeline
  - autonomous roles: spawn Task() per role with agent definition context
  - Return status
```

### normalizeRole Algorithm (from ARCHITECTURE.md parser spec — HIGH confidence)

The dispatcher applies this to every role before any routing. Implements the Phase 6 parser spec
exactly:

```
function normalizeRole(role, version):
  if version < 2:
    role.mode             = role.mode             ?? "advisory"
    role.trigger          = role.trigger          ?? "post-plan"
    role.tools            = role.tools            ?? []
    role.output_type      = role.output_type      ?? "findings"
    role.commit           = role.commit           ?? false
    role.commit_message   = role.commit_message   ?? null
    role.scope            = role.scope            ?? {}
    role.scope.allowed_paths  = role.scope.allowed_paths  ?? []
    role.scope.allowed_tools  = role.scope.allowed_tools  ?? []
  return role
```

**Critical:** version comparison is numeric (`version < 2`), not string (`version == "2"`).
The live `.planning/TEAM.md` has `version: 1` — this triggers the shim for all three starter
roles, giving each `mode: advisory, trigger: post-plan, output_type: findings`. This is
exactly the v1 behavior path.

### Bypass Flag Mechanism (DISP-03)

**Problem:** Agent creation plans (Phase 11 and beyond) run through execute-plan.md. When
`review_team: true` and TEAM.md exists, the dispatcher fires. But code-oriented reviewers
running on markdown agent definition files produce circular/meaningless findings.

**Solution:** A `skip_review: true` field in the PLAN.md YAML frontmatter. The review_team_gate
step reads this from the current PLAN.md path (already known from `identify_plan` step context)
before calling the dispatcher. If detected, the dispatcher receives a bypass signal and exits
immediately without calling any pipeline.

**Where the flag lives:** PLAN.md YAML frontmatter:
```yaml
---
phase: 07-agent-dispatcher
plan: "01"
type: execute
skip_review: true
---
```

**How the dispatcher detects it:** The review_team_gate step extracts the flag and passes it
as an input to agent-dispatcher.md:

```bash
# In the updated review_team_gate step:
PLAN_FILE=$(ls .planning/phases/${PHASE_DIR}/${PADDED_PHASE}-${PLAN_NUM}-PLAN.md 2>/dev/null || echo "")
if [ -n "$PLAN_FILE" ]; then
  SKIP_REVIEW=$(grep -m1 "^skip_review:" "$PLAN_FILE" | awk '{print $2}')
else
  SKIP_REVIEW="false"
fi
```

Then pass `bypass_flag: ${SKIP_REVIEW}` to the dispatcher call.

**Alternative approach (simpler):** The dispatcher itself reads the current PLAN.md path
from the inputs it receives (plan_num + phase_id) and checks for the flag. This keeps the
bypass logic inside the dispatcher rather than in the patched step — architecturally cleaner.
Either approach works; the dispatcher-reads-its-own approach is preferred.

**Scope of Phase 7:** Only needs to define the mechanism and implement detection. The actual
flag will be set in Phase 11 PLAN.md files when agent creation plans are written. Phase 7
must verify detection works (test: a PLAN.md with skip_review: true causes dispatcher to
no-op silently).

### SC1: "Identical REVIEW-REPORT.md Output"

Success criterion 1 requires that advisory post-plan agents reach the review pipeline and
produce REVIEW-REPORT.md output identical to what the pre-dispatcher v1 produced.

**What must be preserved (verified from review-team.md):**
- ARTIFACT.md written to `.planning/phases/{phase_id}/{padded_phase}-{plan_num}-ARTIFACT.md`
- All reviewers spawned in a single Task() turn (parallelism)
- REVIEW-REPORT.md written with the exact plan section format:
  `## Plan ${PLAN_NUM} — {ISO timestamp}` header
  `| ID | Reviewer | Severity | Description | Evidence | Routing |` table
- All four routing paths still reachable: block_and_escalate, send_for_rework, send_to_debugger, log_and_continue
- Critical severity check BEFORE synthesizer.overall_routing (hardcoded minimum)

**What the dispatcher passes to review-team.md (same as current review_team_gate):**
- SUMMARY_PATH
- PHASE_ID
- PLAN_NUM

The dispatcher is an adapter/router, not a replacement. review-team.md is called unchanged
with the same inputs it currently receives.

### agent_studio Config Toggle Scope

**Finding (from ARCHITECTURE.md and Phase 6 decisions):**

`workflow.agent_studio` is an independent boolean flag. It does NOT gate the post-plan
advisory path to review-team.md. The existing `workflow.review_team` flag controls that path.

**Dispatcher config logic:**

```
REVIEW_TEAM_ENABLED = config.workflow.review_team (from CONFIG_CONTENT)
AGENT_STUDIO_ENABLED = config.workflow.agent_studio (from CONFIG_CONTENT)

If both disabled: no-op (current behavior for review_team: false)
If review_team enabled only: call review-team.md directly (v1 passthrough — no TEAM.md parsing)
If agent_studio enabled: full dispatcher logic (read TEAM.md, filter, route)
If both enabled: full dispatcher logic (agent_studio takes precedence — dispatcher routes advisory to review-team.md anyway)
```

The simplest correct implementation: dispatcher is only called when agent_studio is true.
When review_team is true but agent_studio is false, the review_team_gate still calls
review-team.md directly (v1 behavior unchanged). This avoids making the dispatcher a
required intermediary for all v1 users.

**Implication:** The updated review_team_gate step body becomes:

```
1. Read REVIEW_TEAM_ENABLED and AGENT_STUDIO_ENABLED from CONFIG_CONTENT
2. If neither: silent no-op
3. If REVIEW_TEAM_ENABLED and NOT AGENT_STUDIO_ENABLED:
   - Check TEAM.md exists (existing v1 logic)
   - If exists: call @review-team.md (v1 passthrough, unchanged behavior)
4. If AGENT_STUDIO_ENABLED:
   - Check TEAM.md exists
   - If exists: call @agent-dispatcher.md with trigger=post-plan
   - Dispatcher handles routing including advisory → review-team.md
```

### Patch Mechanism: Execute-Plan.md Update

Phase 7 needs to update the review_team_gate step body in execute-plan.md. This is NOT the
same as the Phase 1 patch (which inserted the step). Phase 7 changes the step body content.

**Options:**

1. **New patch script `patch-execute-plan-dispatcher.py`**: Replaces the current step body
   with the new dispatcher-calling body. Uses content-based idempotency check (unique string
   in the new body). Follows the same 4-touch-point or str.replace() pattern.

2. **Update existing patch-execute-plan.py**: Not recommended — the Phase 1 script inserts
   a step from scratch. Phase 7 needs to update an already-inserted step.

3. **Two-step patch**: Phase 1 script skips (already applied). New script replaces the body.
   The new script's idempotency check is a unique string from the new body (e.g.,
   `"agent-dispatcher.md"`). The anchor is the entire current review_team_gate step content.

**Recommended approach:** New Python3 patch script `patch-execute-plan-dispatcher.py` with:
- Idempotency check: `"agent-dispatcher.md" in content` (present after patch applied)
- Anchor: the full current review_team_gate step content (verified from execute-plan.md)
- Replacement: the new step body calling agent-dispatcher.md with trigger context + bypass check
- install.sh extension: add invocation in Section 6 after existing patch scripts

### Project File Layout After Phase 7

```
D:/GSDteams/
├── workflows/
│   └── agent-dispatcher.md              NEW: dispatcher workflow
├── scripts/
│   ├── patch-execute-plan.py            UNCHANGED (Phase 1 — inserts step)
│   ├── patch-execute-plan-dispatcher.py NEW: updates review_team_gate body
│   ├── patch-settings.py                UNCHANGED
│   └── patch-settings-agent-studio.py  UNCHANGED
└── install.sh                           UPDATED: invoke new patch script

~/.claude/get-shit-done-review-team/
└── workflows/
    ├── review-team.md                   UNCHANGED
    └── agent-dispatcher.md              NEW (copied by install.sh)
```

### Recommended Project Structure for agent-dispatcher.md Steps

```xml
<step name="check_bypass_and_config" priority="first">
  <!-- Read bypass flag from PLAN.md frontmatter -->
  <!-- Check AGENT_STUDIO_ENABLED from CONFIG_CONTENT -->
  <!-- If bypass or disabled: exit immediately -->
</step>

<step name="read_and_parse_team_md">
  <!-- Read .planning/TEAM.md -->
  <!-- Extract version, roles list -->
  <!-- Apply normalizeRole to every role -->
</step>

<step name="filter_by_trigger">
  <!-- Keep roles where role.trigger == trigger_type input -->
  <!-- If zero matches: log no-op, return -->
</step>

<step name="route_by_mode">
  <!-- Group filtered roles by mode -->
  <!-- advisory roles → call @review-team.md -->
  <!-- autonomous roles → spawn Task() per role -->
  <!-- Return status to calling workflow -->
</step>
```

### Anti-Patterns to Avoid

- **Calling review-team.md with a filtered role list:** review-team.md reads TEAM.md itself
  in its `validate_team` step. It does not accept a pre-filtered role list as input. The
  dispatcher cannot pass a subset of roles to the review pipeline — all TEAM.md roles that
  have `mode: advisory` and `trigger: post-plan` will be seen by review-team.md. This is
  acceptable because the dispatcher filtering ensures we only call review-team.md when at
  least one advisory post-plan role exists.

- **Replacing review-team.md instead of routing through it:** The dispatcher must be an
  adapter that calls review-team.md. Do not copy review-team.md logic into the dispatcher.
  The review pipeline (sanitize → review → synthesize) is not dispatcher logic.

- **Parsing TEAM.md in the review_team_gate step:** TEAM.md parsing belongs in the dispatcher.
  The review_team_gate step only needs to pass the PLAN.md path (for bypass flag extraction)
  and the standard SUMMARY_PATH/PHASE_ID/PLAN_NUM inputs.

- **Using agent_studio to gate the v1 review path:** review_team_gate's v1 behavior (calling
  review-team.md directly) must remain unchanged when agent_studio is false. The dispatcher
  is only in the path when agent_studio is enabled.

- **Autonomous agent execution in Phase 7:** The autonomous execution path is architecturally
  correct to include in the dispatcher, but no autonomous agents exist yet (Phase 11).
  The dispatcher should include the routing branch but can log "no autonomous agents active"
  or no-op that branch until Phase 11.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing of TEAM.md | Custom regex/sed parser | Claude Read tool + in-context text parsing | jq cannot parse YAML; the dispatcher workflow runs as a Claude task and can parse YAML natively in-context |
| Config reading | Re-read config.json in dispatcher | Use CONFIG_CONTENT already passed from review_team_gate | CONFIG_CONTENT is already in scope in execute-plan.md; passing it avoids a disk read |
| PLAN.md bypass flag extraction | Complex bash YAML parser | grep -m1 "^skip_review:" then awk | Simple line extraction from PLAN.md frontmatter — no full YAML parse needed |
| Patching execute-plan.md at install time | Manual edit instructions | Python3 patch script (same pattern as patch-execute-plan.py) | Idempotency, drift detection, CI-safe; proven pattern from Phase 1 |
| v1/v2 conditional branches throughout dispatcher | `if version == 1 then X else Y` scattered in multiple places | normalizeRole applied once at top, all downstream code sees normalized fields | Single point of version handling; cleaner routing logic; Phase 6 spec mandates this |

**Key insight:** Every technical challenge in this phase has a solved pattern in the existing
codebase. The dispatcher is pattern-following, not pattern-inventing.

---

## Common Pitfalls

### Pitfall 1: Dispatcher Scope Creep (pre-plan and post-phase routes)

**What goes wrong:** Adding pre_plan_agent_gate and post_phase_agent_gate wiring to Phase 7
because the dispatcher supports those trigger types.

**Why it happens:** The dispatcher's data flow naturally handles all four triggers. Once you
build the filter-by-trigger step, it works for pre-plan and post-phase too. The temptation
is to wire all hooks at once.

**How to avoid:** Phase 7 scope is strictly post-plan. The review_team_gate is the only
calling point being wired in this phase. Pre-plan and post-phase hooks are Phase 9. The
dispatcher can be built to accept all trigger types but only the post-plan calling point
is patched in Phase 7.

**Warning signs:** Phase 7 plans include patches to plan-phase.md or execute-phase.md.

### Pitfall 2: Breaking v1 review_team Behavior for Users Without agent_studio

**What goes wrong:** The updated review_team_gate step always calls agent-dispatcher.md
instead of review-team.md directly. Users who have `review_team: true` but `agent_studio:
false` now route through the dispatcher, even though they're using v1.0 behavior.

**Why it happens:** The dispatcher routes advisory post-plan agents to review-team.md anyway,
so it "works." But it adds unnecessary overhead and introduces a new dependency for v1 users.

**How to avoid:** Keep the v1 path intact. The updated review_team_gate reads both flags:
if review_team true AND agent_studio false → call review-team.md directly (unchanged v1
path). Only when agent_studio is true does the dispatcher enter the picture.

**Warning signs:** After Phase 7, users with agent_studio: false see different behavior or
timing from the review pipeline.

### Pitfall 3: Passing a Filtered Role List to review-team.md

**What goes wrong:** Dispatcher filters TEAM.md to advisory post-plan roles, then tries to
pass only those roles to review-team.md to avoid the pipeline reading all roles.

**Why it happens:** Logical — dispatcher already filtered, don't re-filter in review-team.md.

**How to avoid:** review-team.md does not accept a role list parameter. It reads TEAM.md
itself in its validate_team step. The dispatcher should call review-team.md with the same
inputs it currently receives (SUMMARY_PATH, PHASE_ID, PLAN_NUM) and let review-team.md
do its own TEAM.md validation. For Phase 7, this is correct: all TEAM.md roles are
advisory post-plan (v1 TEAM.md), so no filtering mismatch.

**Warning signs:** The dispatcher call to review-team.md includes a `roles:` or `role_list:`
parameter not in the current inputs contract.

### Pitfall 4: Bypass Flag Placed in Wrong Location

**What goes wrong:** The bypass flag is added to config.json, TEAM.md, or as a hardcoded
plan name check (e.g., "if phase is 11") rather than in PLAN.md frontmatter.

**Why it happens:** Looking for a "system-level" toggle instead of a "per-plan" signal.

**How to avoid:** The bypass is per-plan, not per-project. It belongs in PLAN.md frontmatter
as `skip_review: true`. Plans that should NOT skip review simply omit the field (falsy default).
The review_team_gate extracts it from the current plan's PLAN.md path.

**Warning signs:** bypass flag requires modifying TEAM.md or config.json for agent creation
plans.

### Pitfall 5: Autonomous Agent Execution Path Not Placeholder-Safe

**What goes wrong:** The dispatcher's autonomous route branch is left unimplemented with
no-op or crashes when it encounters an autonomous role in TEAM.md (e.g., Doc Writer from
templates/TEAM.md). After install, users with a v2 TEAM.md template see errors.

**Why it happens:** Phase 7 focuses on post-plan advisory path. Autonomous path is "not needed
yet" and left blank.

**How to avoid:** Include a well-defined no-op or stub for the autonomous path in Phase 7:
log `"Agent Dispatcher: autonomous agent {name} — autonomous execution not yet implemented
(Phase 9)"` and continue. This is safe and informative rather than silent or crashing.

**Warning signs:** The dispatcher crashes or produces confusing output when a v2 TEAM.md
with Doc Writer is used after Phase 7 install.

### Pitfall 6: Patch Anchor Drift for review_team_gate Body Update

**What goes wrong:** The patch script for updating the review_team_gate body uses an anchor
that doesn't exactly match the current content (whitespace, encoding differences) and WARN-skips
on first run.

**Why it happens:** The anchor must match the multi-line step body content exactly, including
whitespace. Copy-paste errors introduce invisible differences.

**How to avoid:** Read the current execute-plan.md content directly from disk before writing
the anchor string in the patch script. Use the idempotency check string (presence of
`"agent-dispatcher.md"` in content) as the first check, then a unique anchor string from the
CURRENT step body. Test the script by running it against a copy of execute-plan.md.

**Warning signs:** Patch script prints `[WARN] anchor not found` on first run.

---

## Code Examples

Verified patterns from existing source files:

### Pattern 1: review_team_gate Step (current — from execute-plan.md)

```xml
<!-- Source: ~/.claude/get-shit-done/workflows/execute-plan.md -->
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
- If TEAM.md is missing: log skip and continue to `offer_next`.
- If TEAM.md exists: load and execute the review pipeline:
  ```
  @~/.claude/get-shit-done-review-team/workflows/review-team.md
  ```
  Pass: current SUMMARY.md path, phase identifier, plan identifier.
</step>
```

### Pattern 2: Updated review_team_gate Step (Phase 7 target)

```xml
<!-- Phase 7 target state for review_team_gate step -->
<step name="review_team_gate">
Check whether Review Team or Agent Dispatcher should run:

```bash
REVIEW_TEAM_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.review_team // false')
AGENT_STUDIO_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.agent_studio // false')
```

If neither `REVIEW_TEAM_ENABLED` nor `AGENT_STUDIO_ENABLED` is `"true"`: skip entirely.

Check bypass flag from current PLAN.md:
```bash
PLAN_FILE=$(ls .planning/phases/${PHASE_DIR}/*-PLAN.md 2>/dev/null | head -1)
SKIP_REVIEW=$(grep -m1 "^skip_review:" "$PLAN_FILE" 2>/dev/null | awk '{print $2}' || echo "false")
```
If `SKIP_REVIEW` is `"true"`: log `Agent Dispatcher: skipped (agent creation plan — bypass active)` and continue.

Check that `.planning/TEAM.md` exists:
```bash
[ -f .planning/TEAM.md ] && echo "EXISTS" || echo "MISSING"
```
If TEAM.md is missing: log skip and continue to `offer_next`. Do NOT block execution.

If TEAM.md exists:
- If `AGENT_STUDIO_ENABLED` is `"true"`:
  ```
  @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
  ```
  Pass: trigger=post-plan, SUMMARY_PATH, PHASE_ID, PLAN_NUM.
- Else if `REVIEW_TEAM_ENABLED` is `"true"`:
  ```
  @~/.claude/get-shit-done-review-team/workflows/review-team.md
  ```
  Pass: current SUMMARY.md path, phase identifier, plan identifier.
</step>
```

### Pattern 3: normalizeRole in Dispatcher Step (from ARCHITECTURE.md parser spec)

```
<!-- Source: D:/GSDteams/.planning/research/ARCHITECTURE.md -->
<!-- Applied in agent-dispatcher.md read_and_parse_team_md step -->

Read .planning/TEAM.md. Extract version from frontmatter (default: 1 if absent).

For each role in the roles list:
  Find the ## Role: {slug} section in TEAM.md body.
  Extract the YAML config block (lines between triple-backtick yaml and triple-backtick).
  Parse fields: name, focus, mode, trigger, tools, output_type, commit, commit_message, scope.

Apply normalizeRole(role, version):
  if version < 2:
    role.mode             = role.mode             ?? "advisory"
    role.trigger          = role.trigger          ?? "post-plan"
    role.tools            = role.tools            ?? []
    role.output_type      = role.output_type      ?? "findings"
    role.commit           = role.commit           ?? false
    role.commit_message   = role.commit_message   ?? null
    role.scope            = role.scope            ?? {}
    role.scope.allowed_paths  = role.scope.allowed_paths  ?? []
    role.scope.allowed_tools  = role.scope.allowed_tools  ?? []

Result: normalized_roles list — every role has all 8 fields.
```

### Pattern 4: No-Match Exit (DISP-02)

```
<!-- In filter_by_trigger step of agent-dispatcher.md -->

matched_roles = [r for r in normalized_roles where r.trigger == trigger_type]

If matched_roles is empty:
  Log: "Agent Dispatcher: no agents configured for trigger '{trigger_type}' — continuing"
  Return immediately. Do NOT call review-team.md. Do NOT spawn any Task().
```

### Pattern 5: Advisory Post-Plan Routing to review-team.md

```
<!-- In route_by_mode step of agent-dispatcher.md -->

advisory_roles = [r for r in matched_roles where r.mode == "advisory"]
autonomous_roles = [r for r in matched_roles where r.mode == "autonomous"]

If advisory_roles is non-empty:
  @~/.claude/get-shit-done-review-team/workflows/review-team.md
  Pass: SUMMARY_PATH, PHASE_ID, PLAN_NUM
  (review-team.md reads TEAM.md itself and validates roles — dispatcher does not pre-filter)

If autonomous_roles is non-empty:
  For each role in autonomous_roles:
    Log: "Agent Dispatcher: autonomous agent {role.name} — autonomous execution not yet
         implemented (Phase 9). Skipping."
  (stub — no crash, no Task() spawns)
```

### Pattern 6: Python3 Patch Script — Body Replacement Pattern

```python
# Source: established by patch-execute-plan.py in D:/GSDteams/scripts/
# Phase 7 new script: patch-execute-plan-dispatcher.py

# Idempotency check — unique string in the NEW step body
if 'agent-dispatcher.md' in content:
    print(f"  [SKIP] {target} already patched (dispatcher already wired)")
    sys.exit(0)

# Anchor: unique string from the CURRENT step body (to be replaced)
# Use the end of the current body as anchor
anchor = '@~/.claude/get-shit-done-review-team/workflows/review-team.md\n  ```\n  Pass: current SUMMARY.md path, phase identifier, plan identifier.\n</step>'

if anchor not in content:
    print(f"  [WARN] Anchor not found in {target} — step body may have changed")
    sys.exit(1)

new_step_body = '''[new step body calling agent-dispatcher.md]</step>'''

patched = content.replace(anchor, new_step_body, 1)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| review_team_gate calls review-team.md directly | review_team_gate calls agent-dispatcher.md with trigger context | Phase 7 (this phase) | Single routing layer for all agent types |
| All agents are advisory post-plan reviewers | Agents have mode (advisory/autonomous) and trigger (pre-plan/post-plan/post-phase/on-demand) | Phase 6 schema, Phase 7 routing | Dispatcher routes by both dimensions |
| v1 TEAM.md implicit behavior (no version field) | v1 TEAM.md gets explicit defaults via normalizeRole shim | Phase 6 spec, Phase 7 implementation | Consistent normalized representation for all downstream code |
| No bypass for agent creation plans | skip_review: true in PLAN.md frontmatter, detected by dispatcher | Phase 7 (this phase) | Review pipeline never fires on agent definition artifacts |

---

## Open Questions

1. **How to determine the current PLAN.md path inside review_team_gate**
   - What we know: execute-plan.md `identify_plan` step finds the plan path and stores it. The `review_team_gate` step runs later and needs to reference the PLAN.md path to extract the bypass flag.
   - What's unclear: Is the plan path stored in a variable named `PLAN_PATH` or similar that persists to the review_team_gate step? The execute-plan.md code shows `cat .planning/phases/XX-name/{phase}-{plan}-PLAN.md` in `load_prompt` step but does not show a variable name for the plan path.
   - Recommendation: The planner should read execute-plan.md carefully to identify what variable name holds the current plan path in scope at the review_team_gate step. If no variable exists, the patch can extract the plan path from the SUMMARY.md path (which IS passed to the gate) by replacing `-SUMMARY.md` with `-PLAN.md`. This is reliable because the naming convention is `{phase}-{plan}-SUMMARY.md` / `{phase}-{plan}-PLAN.md`.

2. **Whether the dispatcher return format needs to be structured**
   - What we know: review-team.md returns a structured `## REVIEW PIPELINE: PIPELINE COMPLETE` block. The calling workflow (execute-plan.md) receives this output when review-team.md is loaded via @-reference.
   - What's unclear: Does the updated review_team_gate need to parse the dispatcher's return, or simply pass through to offer_next? For the post-plan advisory path, the dispatcher calls review-team.md and the existing routing (block_and_escalate, send_for_rework, etc.) handles flow control.
   - Recommendation: The dispatcher does not need a structured return format in Phase 7. The advisory path's flow control lives inside review-team.md (which halts execution on block_and_escalate). The dispatcher returns normally after review-team.md completes. The planner should not add a dispatcher-specific return parsing step.

3. **Exact anchor string for patch-execute-plan-dispatcher.py**
   - What we know: The current review_team_gate step body ends with the @-reference call and "Pass: current SUMMARY.md path, phase identifier, plan identifier." followed by `</step>`.
   - What's unclear: Exact whitespace/indentation in the anchor — needs to be extracted character-for-character from the current execute-plan.md.
   - Recommendation: The plan should instruct the executor to read execute-plan.md first and use the EXACT text of the final lines of the review_team_gate step as the anchor. Do not guess at whitespace.

---

## Sources

### Primary (HIGH confidence)

- `~/.claude/get-shit-done/workflows/execute-plan.md` — Complete step sequence including review_team_gate step (full body verified), CONFIG_CONTENT pattern, SUMMARY_PATH/PHASE_ID/PLAN_NUM inputs contract
- `~/.claude/get-shit-done-review-team/workflows/review-team.md` — Complete pipeline (validate_team → sanitize → spawn_reviewers → synthesize → return_status), input contract, REVIEW-REPORT.md format, routing enum
- `D:/GSDteams/.planning/research/ARCHITECTURE.md` — normalizeRole algorithm, Parser Specification section (Phase 6 deliverable), dispatcher data flow, trigger data flow, all architectural patterns, patch anchor points
- `D:/GSDteams/templates/TEAM.md` — v2 schema reference: version: 2, four roles, scope.allowed_paths/allowed_tools in Doc Writer, three v1 role blocks unchanged
- `D:/GSDteams/.planning/TEAM.md` — live v1 TEAM.md: version: 1, three starter roles, no v2 fields — confirms normalizeRole shim will apply to all three roles
- `D:/GSDteams/scripts/patch-execute-plan.py` — complete Python3 idempotent patch script structure: read/idempotency check/anchor check/str.replace/write pattern
- `D:/GSDteams/.planning/REQUIREMENTS.md` — DISP-01, DISP-02, DISP-03 verbatim; CREA-04 confirms bypass applies to agent creation plans
- `D:/GSDteams/.planning/research/PITFALLS.md` — bypass mechanism context, agent creation circular review problem
- `D:/GSDteams/install.sh` — Section 6 (patch invocation), file copy mechanism, how new workflow files reach installed path

### Secondary (MEDIUM confidence)

- `D:/GSDteams/.planning/phases/06-team-md-v2-schema-config-foundation/06-01-SUMMARY.md` — confirmed decisions: normalizeRole on version < 2 (numeric), scope fields default to [], agents: list omitted from frontmatter
- `D:/GSDteams/.planning/phases/06-team-md-v2-schema-config-foundation/06-02-SUMMARY.md` — confirmed: workflow.agent_studio is independent boolean, does not affect workflow.review_team

---

## Metadata

**Confidence breakdown:**
- Current review_team_gate step (what changes): HIGH — read directly from execute-plan.md
- review-team.md input contract (what must be preserved): HIGH — read directly from review-team.md
- normalizeRole algorithm and v2 parsing: HIGH — from ARCHITECTURE.md parser spec (Phase 6 deliverable)
- Bypass flag mechanism: MEDIUM — DISP-03 in REQUIREMENTS.md describes "flag in plan context"; specific field name and extraction pattern is a planner decision
- agent_studio vs review_team config gate logic: HIGH — from ARCHITECTURE.md and Phase 6 decisions
- Patch script anchor for step body replacement: MEDIUM — approach is proven; exact anchor needs careful extraction from disk
- Autonomous agent stub (Phase 7 placeholder): HIGH — required to avoid crash when v2 TEAM.md has autonomous roles

**Research date:** 2026-02-26
**Valid until:** 60 days or until GSD version changes (whichever comes first) — based on internal project files only
