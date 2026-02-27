# Phase 12: New-Project Integration — Research

**Researched:** 2026-02-26
**Domain:** GSD workflow patching — new-project.md hook insertion, PROJECT.md agent proposal logic, /gsd:new-agent delegation
**Confidence:** HIGH — all findings verified directly from source files in the repository

---

## Summary

Phase 12 adds exactly one question to the `/gsd:new-project` flow. After the roadmap is committed (end of Step 8), the user is asked whether they want to set up an agent team. Three options are offered: "Set up now", "Set up later (/gsd:team)", and "Skip". Choosing "Set up later" or "Skip" produces an outcome identical to a v1.0 new-project run — zero timing impact, zero file changes. Choosing "Set up now" reads PROJECT.md and any existing research output, proposes 2–3 tailored agents, shows each proposal inline, and delegates each creation to `/gsd:new-agent`.

Phase 11 delivered `/gsd:new-agent` as a complete 9-step guided conversation workflow. Phase 12 is a consumer of that workflow — it never reimplements agent creation inline. The delegation model (INIT-03) is the architectural lock: agent configuration is never inlined into the new-project flow. This keeps the new-project timing unchanged for users who skip agent setup, and avoids duplicating agent creation logic.

The implementation has two deliverables: (1) a Python patch script (`scripts/patch-new-project.py`) that inserts the new step into `new-project.md` at the correct anchor, and (2) an `install.sh` update to invoke the patch script during installation. The hook point is between the roadmap commit bash block and "## 9. Done" — specifically using `\n## 9. Done\n` as the anchor string for pattern-based insertion.

**Primary recommendation:** Insert a new "## 8.5. Agent Team Setup" step between Step 8 and Step 9 in new-project.md, using the same idempotent Python patch script pattern established in earlier phases. Delegate to `/gsd:new-agent` for each proposed agent. No new config flags, no new agent creation logic.

---

## Standard Stack

This phase is pure workflow authoring and Python patch scripting. No npm packages, no external libraries.

### Core

| Component | Location | Purpose | Why Standard |
|-----------|----------|---------|--------------|
| `scripts/patch-new-project.py` | New file | Pattern-based insertion of agent_team_hook step into new-project.md | Same pattern as patch-plan-phase.py, patch-execute-phase.py |
| `new-project.md` (installed) | `~/.claude/get-shit-done/workflows/new-project.md` | Target file — receives the new step | GSD core workflow, already patched by earlier phases |
| `install.sh` | `D:/GSDteams/install.sh` | Invoke the new patch script during installation | Section 6 is the established patch invocation area |
| `/gsd:new-agent` | Delegatee | Handles each agent creation via guided conversation | Phase 11 deliverable — live, tested, wired |
| `PROJECT.md` | `.planning/PROJECT.md` | Source of goals/stack for agent proposals | Written during Step 4 of new-project.md |

### Supporting

| Component | Location | Purpose | When to Use |
|-----------|---------|---------|-------------|
| `.planning/research/FEATURES.md` | Optional | Domain-specific features for smarter proposals | Read if research was run (Step 6 of new-project.md) |
| `.planning/research/STACK.md` | Optional | Tech stack for stack-aware proposals | Read if research was run |
| `gsd-tools.cjs` | `~/.claude/get-shit-done/bin/gsd-tools.cjs` | Commit updated config.json if agent_studio enabled | agent_studio flag set to true after "Set up now" flow |

### No New External Dependencies

```bash
# No npm install required — zero new dependencies
# No new Python libraries — standard library only (sys, os)
```

---

## Architecture Patterns

### Recommended File Structure (Phase 12 deliverables)

```
D:/GSDteams/
├── scripts/
│   └── patch-new-project.py      # NEW: inserts agent_team_hook step
└── install.sh                    # MODIFIED: +1 patch invocation in Section 6
```

The new-project.md file at `~/.claude/get-shit-done/workflows/new-project.md` is modified by the patch script at install time — not stored in this repo.

### Pattern 1: Python Patch Script (patch-new-project.py)

**What:** Idempotent Python script that inserts a new step into new-project.md using `str.replace(anchor, new_content, 1)`.

**Anchor string:** `\n## 9. Done\n` (character-for-character, including surrounding newlines)

**Idempotency check:** `'agent_team_hook' in content` — unique string only present after this patch applied

**When to use:** This is the only insertion pattern used by all extension patches.

**Example (modeled on patch-plan-phase.py):**
```python
# Source: D:/GSDteams/scripts/patch-plan-phase.py
#!/usr/bin/env python3
"""
patch-new-project.py — Insert agent_team_hook step into GSD new-project.md
                        to wire in agent team setup after project initialization.

Phase 12 — INIT-01: agent_team_hook lifecycle step.

Usage: python3 scripts/patch-new-project.py <path-to-new-project.md>

Idempotency check: 'agent_team_hook' in content
  If already present, exits 0 with skip message — safe to run multiple times.
"""
import sys, os

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-new-project.py <path-to-new-project.md>", file=sys.stderr)
        sys.exit(1)
    target = sys.argv[1]
    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)
    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'agent_team_hook' in content:
        print(f"  [SKIP] {target} already patched (agent_team_hook already present)")
        sys.exit(0)
    anchor = '\n## 9. Done\n'
    if anchor not in content:
        print(f"ERROR: Anchor '\\n## 9. Done\\n' not found in {target}", file=sys.stderr)
        sys.exit(1)
    new_section = '''
## 8.5. Agent Team Setup
<!-- step: agent_team_hook -->

After the roadmap is committed, offer to set up an agent team.

[... step body here ...]

'''
    patched = content.replace(anchor, new_section + '## 9. Done\n', 1)
    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)
    print(f"  [OK] Patched: {target}")

if __name__ == '__main__':
    main()
```

**Source:** `D:/GSDteams/scripts/patch-plan-phase.py` (HIGH confidence — direct analog)

### Pattern 2: Agent Team Hook Step Body

**What:** The step content inserted into new-project.md. Exactly one AskUserQuestion with three options. No additional config questions inside the new-project flow.

**Requirements (INIT-01, INIT-02, INIT-03) drive this structure:**

```markdown
## 8.5. Agent Team Setup
<!-- step: agent_team_hook -->

**If auto mode:** Skip this step entirely — no agent team questions in auto mode.

Ask the user one question:

AskUserQuestion([{
  header: "Agent Team",
  question: "Set up an agent team for this project?",
  multiSelect: false,
  options: [
    { label: "Set up now",          description: "I'll propose 2-3 agents based on your project goals" },
    { label: "Set up later",        description: "/gsd:team — add agents any time" },
    { label: "Skip",                description: "No agent team for this project" }
  ]
}])

**If "Set up later" or "Skip":** Continue to Step 9. No files written. Timing unchanged.

**If "Set up now":**

Read .planning/PROJECT.md and extract:
- Core value (what must work)
- Domain/purpose
- Tech stack (from Key Decisions or requirements categories)

Also read .planning/research/STACK.md if it exists.

Based on the project domain and stack, propose 2-3 tailored agents.
Display proposals inline (NOT via AskUserQuestion):

---
## Proposed Agent Team

Based on your project goals, here are agents that would be useful:

**Agent 1: [Name]**
- Purpose: [one sentence]
- Mode: [advisory/autonomous]
- Trigger: [pre-plan/post-plan/post-phase]

**Agent 2: [Name]**
- Purpose: [one sentence]
- Mode: [advisory/autonomous]
- Trigger: [pre-plan/post-plan/post-phase]

**Agent 3: [Name]** (optional)
- Purpose: [one sentence]
- Mode: [advisory/autonomous]
- Trigger: [pre-plan/post-plan/post-phase]
---

For each proposed agent, ask individually:

AskUserQuestion([{
  header: "Agent [N]",
  question: "Set up [Agent Name]?",
  multiSelect: false,
  options: [
    { label: "Create this agent",    description: "Walk through /gsd:new-agent" },
    { label: "Modify first",         description: "I'll describe what to change" },
    { label: "Skip this one",        description: "Don't create this agent" }
  ]
}])

If "Create this agent":
  Run /gsd:new-agent with the proposed agent context prefilled where possible.

If "Modify first":
  Accept their modification notes, adjust the proposal, re-display, then:
  Run /gsd:new-agent with the modified proposal.

If "Skip this one":
  Continue to next proposed agent.

After all agents processed (or if user skips all):
  Announce: "Agent team setup complete."
  Continue to Step 9.
```

**Source:** Requirements INIT-01, INIT-02, INIT-03; `D:/GSDteams/.planning/research/ARCHITECTURE.md` Patch 4 section (HIGH confidence)

### Pattern 3: Hook Point — After Roadmap Commit, Before Done Banner

**What:** The correct insertion point in new-project.md.

**Why Step 8 end, not Step 5 end:**

ARCHITECTURE.md describes inserting at "Step 5.6" (after config.json commit, before "Note: Run /gsd:settings anytime"). However, the requirements state: "After `/gsd:new-project` completes and PROJECT.md is committed." Success criterion 3 requires that "Set up later" or "Skip" produces an outcome "identical to a v1.0 new-project run — new-project timing is effectively unchanged."

The Step 5 hook would add a question in the middle of workflow preferences, before research and roadmap. At Step 9, the project is fully initialized (all commits done) and the user can make an informed decision. This also means the research output (FEATURES.md, STACK.md) is available for smarter proposals.

**Confirmed anchor:** The line `\n## 9. Done\n` in new-project.md (verified at line 899 of the installed file).

```
... Step 8: Roadmap commit bash block ...

## 8.5. Agent Team Setup   ← INSERT HERE
<!-- step: agent_team_hook -->
[step body]

## 9. Done
[completion banner]
```

**Source:** `C:/Users/gutie/.claude/get-shit-done/workflows/new-project.md` lines 893-899 (HIGH confidence — direct file read)

### Pattern 4: install.sh Extension

**What:** Add new-project.md patch to Section 6 of install.sh.

**Current Section 6 ordering (verified from install.sh):**
```bash
python3 "$EXT_DIR/scripts/patch-execute-plan.py" "$EXECUTE_PLAN"
python3 "$EXT_DIR/scripts/patch-settings.py" "$SETTINGS"
python3 "$EXT_DIR/scripts/patch-settings-agent-studio.py" "$SETTINGS"
python3 "$EXT_DIR/scripts/patch-execute-plan-dispatcher.py" "$EXECUTE_PLAN"
python3 "$EXT_DIR/scripts/patch-plan-phase.py" "$PLAN_PHASE"
python3 "$EXT_DIR/scripts/patch-plan-phase-p10.py" "$PLAN_PHASE"
python3 "$EXT_DIR/scripts/patch-execute-phase.py" "$EXECUTE_PHASE"
```

**Phase 12 addition (appended to Section 6):**
```bash
NEW_PROJECT="$GSD_DIR/get-shit-done/workflows/new-project.md"
if [ ! -f "$NEW_PROJECT" ]; then
  echo "  ERROR: $NEW_PROJECT not found"
  exit 1
fi
python3 "$EXT_DIR/scripts/patch-new-project.py" "$NEW_PROJECT"
```

**Also update Section 9 completion message** to include new-project.md in the "Patches applied" list.

**Source:** `D:/GSDteams/install.sh` Section 6, lines 156-191 (HIGH confidence — direct file read)

### Pattern 5: Delegation to /gsd:new-agent (INIT-03)

**What:** When user selects "Create this agent" for a proposed agent, the flow invokes `/gsd:new-agent`. No special-case path, no inline agent creation.

**INIT-03 is explicit:** "Agent creation during new-project setup delegates to the same `/gsd:new-agent` workflow — no special-case path."

**How delegation works in Claude Code workflows:**

In the new-project.md context, `/gsd:new-agent` is invoked by narrating the instruction to run it — the same pattern used when team-studio.md routes to `/gsd:new-agent`. The workflow instruction reads:

```
Run /gsd:new-agent to create this agent.
```

If the proposal includes prefilled context (name, purpose, mode, trigger), surface it before delegating so the user can reference it during the /gsd:new-agent conversation:

```
Based on the proposal, this agent would be:
- Name: [proposed name]
- Purpose: [purpose sentence]
- Mode: [advisory/autonomous]
- Trigger: [trigger]

Running /gsd:new-agent — the guided conversation will walk through the full setup.
```

Then invoke /gsd:new-agent. The user goes through the full workflow; the proposal acts as context, not as pre-answer.

**Source:** `D:/GSDteams/workflows/team-studio.md` add_agent step (HIGH confidence — confirmed pattern in Phase 11 VERIFICATION.md)

### Agent Proposal Logic (for "Set up now" path)

**What:** How to derive 2-3 meaningful agent proposals from PROJECT.md.

**Sources to read:**
1. `.planning/PROJECT.md` — Core value, goals, stack decisions
2. `.planning/research/STACK.md` — Tech stack (if research ran)
3. `.planning/research/FEATURES.md` — Feature categories (if research ran)

**Domain-to-agent mapping heuristics (HIGH confidence — derived from completed phases):**

| Domain Signal | Agent Proposal |
|---------------|---------------|
| Any project | "Requirements Coverage Checker" — pre-plan advisory, checks plans cover active requirements |
| Code-producing project | "Security Auditor" — post-plan advisory, checks for security issues (already in TEAM.md starters) |
| Documentation-heavy | "Doc Sync Agent" — post-phase autonomous, updates docs after each phase |
| API/backend project | "API Contract Checker" — post-plan advisory, checks endpoint contracts |
| Frontend/UI project | "Accessibility Auditor" — post-plan advisory |
| Any project | "Changelog Agent" — post-phase autonomous, writes CHANGELOG.md entries |

**Three-proposal structure (INIT-02):**
- Proposal 1: A post-plan advisory agent (most universally useful)
- Proposal 2: Domain-specific agent (derived from project goals/stack)
- Proposal 3 (optional): A post-phase autonomous agent if project is documentation-heavy

**Do not over-engineer proposals.** The goal is to show enough value to get the user started — they can always run `/gsd:team` to add more.

### Anti-Patterns to Avoid

- **Asking more than one question:** INIT-01 is explicit — exactly one question about agent team setup. The proposals and per-agent confirmations that follow are part of the "Set up now" branch, not additional new-project questions.
- **Inlining agent creation logic:** INIT-03 prohibits this. Never write agent config, role blocks, or TEAM.md content directly in the new-project.md step. Always delegate to /gsd:new-agent.
- **Using Step 5 as hook point:** ARCHITECTURE.md describes Step 5.6 but the requirements and success criteria require the hook to be at the END of the workflow (after roadmap is committed). At Step 5, research hasn't run yet — proposals would be less informed.
- **Firing in auto mode:** Auto mode skips interactive questions. The agent team hook must be skipped in auto mode (`--auto` flag check).
- **Patching to wrong file:** The patch target is the installed path `~/.claude/get-shit-done/workflows/new-project.md`, NOT the source repo path. install.sh uses `$GSD_DIR/get-shit-done/workflows/new-project.md`.
- **Duplicating /gsd:new-agent logic:** The `write_agent` step of new-agent.md handles all TEAM.md mutations. Phase 12 must never write to TEAM.md directly.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent creation | Inline TEAM.md write in new-project step | Delegate to `/gsd:new-agent` | INIT-03 requirement; avoids duplication and drift |
| Pattern insertion | Line-number based file edit | Python str.replace with idempotency check | Phase 1-11 establish this as the only safe GSD patch pattern |
| Agent proposals | Complex PROJECT.md parser | Simple keyword extraction from core value + decisions | Proposals are a UX starting point, not a spec |
| Config update | Direct json write in workflow | `jq '.workflow.agent_studio = true'` bash snippet | Consistent with how all other config flags are set |
| Commit of config change | Manual `git add` | `gsd-tools.cjs commit` | Established pattern throughout the codebase |

**Key insight:** Phase 12 is the thinnest possible integration. The value is in the delegation, not in the new-project step itself. Keep the step body short and the proposal logic simple — users who want more can run `/gsd:team`.

---

## Common Pitfalls

### Pitfall 1: Hook at Wrong Insertion Point

**What goes wrong:** Patch script uses `## 5.5. Resolve Model Profile\n` or `**Note:** Run /gsd:settings anytime` as anchor, inserting the step in the middle of the workflow instead of at the end.

**Why it happens:** ARCHITECTURE.md's Patch 4 section says "Insert AFTER Step 5 (after config.json is written and committed)" — this is an earlier architectural draft that conflicts with the success criteria.

**How to avoid:** Use `\n## 9. Done\n` as the anchor (verified at line 899 of installed new-project.md). This inserts the step after the roadmap commit and before the completion banner — exactly when "the project is complete."

**Warning signs:** If the hook fires before research runs, it cannot access FEATURES.md or STACK.md for informed proposals.

### Pitfall 2: Violating the Single-Question Rule

**What goes wrong:** The "Set up now" branch asks config questions inline (model selection, output type, trigger settings) instead of delegating to /gsd:new-agent.

**Why it happens:** Wanting to make agent setup "seamless" by capturing everything in the new-project flow.

**How to avoid:** INIT-01 is a hard constraint: "This is the only addition to the new-project flow." Proposals display inline (no question). Per-agent approval asks one question (Create/Modify/Skip). All detailed questions go to /gsd:new-agent.

**Warning signs:** Any AskUserQuestion with headers like "Agent Mode", "Trigger", "Scope" appearing in the new-project.md hook step is wrong.

### Pitfall 3: Anchor Not Found After GSD Updates

**What goes wrong:** If GSD ships an update that renumbers steps in new-project.md, `## 9. Done` might become `## 10. Done` or change format, and the patch script exits with ERROR.

**Why it happens:** GSD workflows are updated independently of this extension.

**How to avoid:** The patch script must handle anchor-not-found gracefully — exit with an explanatory error that names the expected anchor string. This is consistent with all other patch scripts. The install.sh documentation should mention "Re-run `bash install.sh` after `/gsd:update`."

**Warning signs:** `patch-new-project.py` printing `ERROR: Anchor string not found` after a GSD update.

### Pitfall 4: Missing auto Mode Guard

**What goes wrong:** The agent team hook fires during `gsd:new-project --auto` runs, asking interactive questions that block automation.

**Why it happens:** Forgetting that new-project.md has an auto mode where interactive steps are skipped.

**How to avoid:** Add explicit auto mode guard at the start of the hook step:
```
**If auto mode:** Skip this step entirely.
```

Auto mode is detected via `$ARGUMENTS` containing `--auto` — established at Step 2 of new-project.md.

**Warning signs:** `/gsd:new-project --auto @doc.md` hanging on an AskUserQuestion prompt.

### Pitfall 5: Proposal Quality — Too Generic or Too Specific

**What goes wrong:** Proposals say "an advisory agent" with no specifics (too generic), or propose an agent for a technology that isn't in the stack (too specific/wrong).

**Why it happens:** Trying to generate proposals without reading PROJECT.md carefully.

**How to avoid:** Always read PROJECT.md before generating proposals. Extract the domain and stack from "Core Value" and "Key Decisions" sections. Use the domain-to-agent mapping heuristics documented in Architecture Patterns above.

**Warning signs:** All three proposals are identical for different projects.

### Pitfall 6: install.sh Missing NEW_PROJECT File Check

**What goes wrong:** install.sh invokes `patch-new-project.py` without checking that `new-project.md` exists first, causing a confusing error on GSD versions that restructure the workflows directory.

**Why it happens:** Copying the patch invocation without copying the existence check pattern.

**How to avoid:** Add a `[ ! -f "$NEW_PROJECT" ]` guard with `exit 1` before the python3 invocation — exactly the pattern used for EXECUTE_PLAN, SETTINGS, PLAN_PHASE, and EXECUTE_PHASE.

---

## Code Examples

Verified patterns from source files:

### Patch Script: Idempotency + Anchor Pattern

```python
# Source: D:/GSDteams/scripts/patch-plan-phase.py (direct analog)
#!/usr/bin/env python3
"""
patch-new-project.py — Insert agent_team_hook step into GSD new-project.md
Phase 12 — INIT-01.
Idempotency check: 'agent_team_hook' in content
"""
import sys, os

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-new-project.py <path-to-new-project.md>", file=sys.stderr)
        sys.exit(1)
    target = sys.argv[1]
    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)
    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()
    # Idempotency check
    if 'agent_team_hook' in content:
        print(f"  [SKIP] {target} already patched (agent_team_hook already present)")
        sys.exit(0)
    anchor = '\n## 9. Done\n'
    if anchor not in content:
        print(f"ERROR: Anchor string not found in {target}", file=sys.stderr)
        print(f"       Expected: '\\n## 9. Done\\n'", file=sys.stderr)
        sys.exit(1)
    new_section = """
## 8.5. Agent Team Setup
<!-- step: agent_team_hook -->
[step body]
"""
    patched = content.replace(anchor, new_section + '\n## 9. Done\n', 1)
    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)
    print(f"  [OK] Patched: {target}")
    print(f"       Inserted: ## 8.5. Agent Team Setup (agent_team_hook)")

if __name__ == '__main__':
    main()
```

### install.sh Section 6 Extension

```bash
# Source: D:/GSDteams/install.sh Section 6 (lines 156-191)
# Add after the existing 7 patch invocations:

NEW_PROJECT="$GSD_DIR/get-shit-done/workflows/new-project.md"

if [ ! -f "$NEW_PROJECT" ]; then
  echo "  ERROR: $NEW_PROJECT not found"
  exit 1
fi

python3 "$EXT_DIR/scripts/patch-new-project.py" "$NEW_PROJECT"
```

### AskUserQuestion — Single Hook Question (INIT-01)

```
# Source: Requirements INIT-01 (exact options specified)
AskUserQuestion([{
  header: "Agent Team",
  question: "Set up an agent team for this project?",
  multiSelect: false,
  options: [
    { label: "Set up now",     description: "I'll propose 2-3 agents based on your project goals" },
    { label: "Set up later",   description: "/gsd:team — add agents any time" },
    { label: "Skip",           description: "No agent team for this project" }
  ]
}])
```

### Per-Agent Approval Pattern (INIT-02)

```
# Source: Requirements INIT-02 — "user approves, modifies, or skips each individually"
For each proposed agent [1..N]:
  Display proposal inline as markdown block (NOT via AskUserQuestion).

  AskUserQuestion([{
    header: "Agent [N]",
    question: "Create [Agent Name]?",
    multiSelect: false,
    options: [
      { label: "Create this agent", description: "Walk through /gsd:new-agent" },
      { label: "Modify first",      description: "I'll describe what to change" },
      { label: "Skip",              description: "Don't create this agent" }
    ]
  }])
```

### Read PROJECT.md for Proposals

```
# Source: D:/GSDteams/.planning/research/ARCHITECTURE.md Patch 4 section
Read .planning/PROJECT.md — extract:
  - Core value (the ONE thing that must work)
  - Key Decisions table (technology choices)
  - Requirements categories (indicate domain)

Read .planning/research/STACK.md if it exists (richer stack information).
Read .planning/research/FEATURES.md if it exists (feature categories).
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| New-project ends at Step 9 Done with no agent question | New-project ends with Step 8.5 agent team question then Step 9 | Phase 12 | Minimal: "Later/Skip" = identical to old behavior |
| ARCHITECTURE.md proposed Step 5.6 hook (before research) | Correct hook at Step 8.5 (after roadmap, research available) | Phase 12 research | Proposals can reference STACK.md and FEATURES.md |
| Agent creation required /gsd:new-agent after project init | Agent creation offered inline via /gsd:new-agent delegation | Phase 12 | No separate step needed; smooth onboarding |

**Deprecated/outdated:**

- ARCHITECTURE.md "Step 5.6" hook position: The ARCHITECTURE.md draft proposed inserting at Step 5.6 (after config.json commit). The correct position is Step 8.5 (after roadmap commit). The Step 5.6 position is pre-research; at Step 8.5, all research artifacts exist and can inform proposals.

---

## Open Questions

1. **Should agent_studio be enabled in config.json when "Set up now" is selected?**
   - What we know: The ARCHITECTURE.md step body includes `jq '.workflow.agent_studio = true'` after "Set up now"
   - What's unclear: If the user creates agents but sets agent_studio to false later via /gsd:settings, the agents exist but don't fire — confusing
   - Recommendation: Yes, enable agent_studio when "Set up now" is selected. This is the natural expectation: the user chose to set up agents, so they want them active. Document in the completion message that they can adjust via `/gsd:settings`.

2. **How should "Modify first" work in the per-agent approval loop?**
   - What we know: INIT-02 says "User approves, modifies, or skips each individually"
   - What's unclear: How much modification is in-scope? Name change? Mode change? Full redesign?
   - Recommendation: Accept free-text modification notes, adjust the proposal inline, re-display the modified proposal, then offer Create/Skip. Do not re-ask all fields — just apply the stated change and show the updated proposal. If the user wants a fundamentally different agent, /gsd:new-agent from scratch is the right path.

3. **What if no PROJECT.md goals are parseable (very terse PROJECT.md)?**
   - What we know: PROJECT.md always has a Core Value and Requirements section
   - What's unclear: Very minimal PROJECT.md files may not have enough domain signal for good proposals
   - Recommendation: Fall back to 2 generic proposals: "Requirements Coverage Checker" (pre-plan advisory) and "Doc Sync Agent" (post-phase autonomous). These are universally useful regardless of domain.

4. **Should the patch script be named `patch-new-project.py` or follow a more specific name like `patch-new-project-p12.py`?**
   - What we know: Phase 10 used `patch-plan-phase-p10.py` as a second patch to the same file. Phase 12 has only one patch to new-project.md.
   - Recommendation: Use `patch-new-project.py` (no phase suffix) since this is the only patch to new-project.md. If a future phase patches it again, add a suffix then.

---

## Sources

### Primary (HIGH confidence)

All sources read directly from the repository. No WebSearch used — all domain knowledge is internal to the codebase.

- `C:/Users/gutie/.claude/get-shit-done/workflows/new-project.md` — full step sequence (Steps 1-9), exact anchor text `\n## 9. Done\n` confirmed at line 899, Step 5 commit block and "Note:" text confirmed at lines 365-368, auto mode detection via $ARGUMENTS confirmed at Step 2
- `D:/GSDteams/workflows/new-agent.md` — 9-step guided conversation; confirmed Phase 11 deliverable is live and correct; no inputs required (reads TEAM.md directly)
- `D:/GSDteams/commands/gsd/new-agent.md` — slash command entry point; execution_context confirmed at installed path
- `D:/GSDteams/scripts/patch-plan-phase.py` — patch script pattern; idempotency check; anchor string format; str.replace(anchor, new_content, 1) pattern; ERROR vs SKIP exit codes
- `D:/GSDteams/install.sh` — Section 6 ordering (7 current patches); Section 3 project root detection; file existence guards; Section 9 completion message; Section 2 GSD_DIR variable
- `D:/GSDteams/.planning/research/ARCHITECTURE.md` — Patch 4 section: agent_team_hook step body, config.json agent_studio flag; also confirmed "after config.json commit" vs. requirements text "after completes"
- `D:/GSDteams/.planning/phases/11-agent-creation-new-agent/11-RESEARCH.md` — Phase 11 pattern reference; delegation model; install.sh Section 5 auto-pickup of commands/gsd/*.md
- `D:/GSDteams/.planning/phases/11-agent-creation-new-agent/11-VERIFICATION.md` — Phase 11 confirmed complete; /gsd:new-agent command wired and live; team-studio add_agent routes to /gsd:new-agent
- `D:/GSDteams/.planning/REQUIREMENTS.md` — INIT-01 through INIT-03 exact text; Phase 12 traceability confirmed
- `D:/GSDteams/.planning/ROADMAP.md` — Phase 12 success criteria (3 criteria verbatim); depends on Phase 8 and Phase 11; Phase 11 marked complete
- `D:/GSDteams/.planning/STATE.md` — Phase 11 complete; current position confirmed; no pending todos for Phase 12

### Secondary (MEDIUM confidence)

- `D:/GSDteams/.planning/research/ARCHITECTURE.md` full file — agent_team_hook step body proposed at Step 5.6 (architectural draft; corrected to Step 8.5 based on requirements analysis)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; same patch script pattern; patch target and anchor verified directly
- Architecture: HIGH — hook insertion point derived from requirements text + direct file read; delegation pattern verified from Phase 11; all patterns from prior phases
- Pitfalls: HIGH — all pitfalls derived from reading actual source code and requirements constraints, not speculation

**Research date:** 2026-02-26
**Valid until:** Stable — changes only if new-project.md step numbering changes in a GSD update (patch anchor would need adjustment)

---

## Plan Count Recommendation

Based on the deliverables:

| Plan | Scope | Tasks |
|------|-------|-------|
| 12-01 | `scripts/patch-new-project.py` + `install.sh` update | 2 tasks: patch script + install.sh Section 6 + Section 9 additions |

**Rationale:** One plan covers both deliverables because they are tightly coupled (the patch script is meaningless without install.sh invoking it, and install.sh change is trivial). This is the lightest phase in the entire roadmap — it is primarily a wiring step. The new-project.md step body is written inside the patch script as a string. The delegation to /gsd:new-agent is a workflow instruction, not a new file.

The phase goal is complete when:
1. `bash install.sh` patches `~/.claude/get-shit-done/workflows/new-project.md` with the agent_team_hook step
2. Running `/gsd:new-project` and choosing "Set up later" produces the Done banner with no TEAM.md created
3. Running `/gsd:new-project` and choosing "Set up now" shows 2-3 proposals and routes to `/gsd:new-agent` per agent
