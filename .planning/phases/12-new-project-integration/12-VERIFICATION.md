---
phase: 12-new-project-integration
verified: 2026-02-27T06:00:00Z
status: passed
score: 3/3 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Run /gsd:new-project end-to-end and select 'Set up later'"
    expected: "Proceeds directly to Step 9 Done banner with no TEAM.md or agent files created"
    why_human: "Requires an interactive Claude session to execute the workflow"
  - test: "Run /gsd:new-project end-to-end and select 'Set up now'"
    expected: "Reads PROJECT.md, displays 2-3 agent proposals as an inline markdown block, then for each agent asks one AskUserQuestion (Create/Modify/Skip), and selecting 'Create this agent' delegates to /gsd:new-agent"
    why_human: "Requires an interactive Claude session; proposal content is dynamic and depends on PROJECT.md contents"
---

# Phase 12: New-Project Integration Verification Report

**Phase Goal:** After /gsd:new-project completes and PROJECT.md is committed, one question is asked: "Do you want to set up an agent team?" The options are "Set up now", "Set up later (/gsd:team)", and "Skip". Choosing "Set up now" reads PROJECT.md goals and stack, proposes 2-3 tailored agents, and delegates each creation to /gsd:new-agent. Choosing "Set up later" or "Skip" produces an outcome identical to v1.0. Agent configuration is never inlined into the new-project flow.

**Verified:** 2026-02-27T06:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | After /gsd:new-project completes, exactly one question is asked about agent team setup — no additional questions about agent configuration appear in the new-project flow | VERIFIED | `scripts/patch-new-project.py` contains exactly one initial AskUserQuestion block (the 3-option hook at line 55). Proposals are explicitly displayed inline ("do NOT use AskUserQuestion for proposals" at line 79). Per-agent approval questions are in the conditional "Set up now" branch only — they do not appear in the base flow. "Modify first" path uses free-text inline ask, not AskUserQuestion. |
| 2 | Choosing "Set up now" produces 2-3 agent proposals derived from PROJECT.md goals and stack — each proposal is shown individually and the user approves, modifies, or skips each one before anything is written | VERIFIED | Patch script step body (lines 68–144) instructs: read `.planning/PROJECT.md`, optionally read `STACK.md` and `FEATURES.md`, display all proposals as inline markdown block, then loop per-agent showing proposal again + AskUserQuestion (Create/Modify/Skip) before delegating to `Run /gsd:new-agent`. No file writes occur in the step body — all writes are delegated to /gsd:new-agent. |
| 3 | Choosing "Set up later" or "Skip" produces an outcome identical to a v1.0 new-project run — no TEAM.md changes, no agent files created, new-project timing is effectively unchanged | VERIFIED | Line 66 of patch script: `**If "Set up later" or "Skip":** Continue to Step 9. No files written. Timing unchanged.` No TEAM.md write, no agent config, no config.json mutation in the hook step. The entire step body was confirmed in the live-patched file (lines 899–997 of temp test). |

**Score:** 3/3 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/patch-new-project.py` | Idempotent Python patch script inserting ## 8.5 Agent Team Setup into new-project.md | VERIFIED | File exists (159 lines). Python syntax valid (`python3 -c "import ast; ast.parse(...)"` → OK). Contains: `agent_team_hook` (8 occurrences), `\n## 9. Done\n` anchor (3 occurrences), `AskUserQuestion` (4 occurrences: 2 blocks + 2 comment/negative references), auto mode guard, `/gsd:new-agent` delegation (3 occurrences). No placeholder text, no TODO/FIXME/stub comments. |
| `install.sh` | Section 6 invocation of patch-new-project.py with file existence guard; Section 9 completion message listing new-project.md | VERIFIED | `NEW_PROJECT` variable declared at line 193, file existence guard at lines 195–198, `python3 "$EXT_DIR/scripts/patch-new-project.py" "$NEW_PROJECT"` at line 200. Section 9 completion message at line 267: `- new-project.md (agent_team_hook step — agent team setup offer)`. All 7 prior Section 6 patch invocations (lines 185–191) are unchanged. Bash syntax valid. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `install.sh` | `scripts/patch-new-project.py` | `python3 "$EXT_DIR/scripts/patch-new-project.py" "$NEW_PROJECT"` in Section 6 | WIRED | Line 200 of install.sh; preceded by file existence guard at lines 195–198. Ordering confirmed: comes after `patch-execute-phase.py` (line 191). |
| `scripts/patch-new-project.py` | `new-project.md` (installed) | `str.replace` on anchor `\n## 9. Done\n` | WIRED | Dry-run confirmed: first run on `/tmp/new-project-test.md` printed `[OK] Patched` (exit 0); second run printed `[SKIP] already patched` (exit 0). Inserted step confirmed at line 899, `## 9. Done` at line 998. |
| `patch-new-project.py` step body | `/gsd:new-agent` | `Run /gsd:new-agent to create this agent.` (lines 132, 137) | WIRED | Both "Create this agent" and "Modify first" branches contain `Run /gsd:new-agent` delegation. No inline agent creation logic present in the step body. |

---

## Requirements Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| INIT-01: Exactly one AskUserQuestion with three options (Set up now / Set up later / Skip) added to new-project flow | SATISFIED | Single AskUserQuestion at line 55 with 3 options exactly matching INIT-01 spec. Proposals displayed inline (not via AskUserQuestion). |
| INIT-02: "Set up now" path reads PROJECT.md, proposes 2-3 agents inline, per-agent approval before delegation | SATISFIED | Step body reads PROJECT.md + optional STACK.md/FEATURES.md; displays all proposals as inline markdown block; loops per-agent with AskUserQuestion (Create/Modify/Skip) before calling /gsd:new-agent. |
| INIT-03: Agent configuration never inlined into new-project flow — all creation delegated to /gsd:new-agent | SATISFIED | Step body contains zero TEAM.md writes, zero agent config blocks, zero role definitions. Only delegation instructions: `Run /gsd:new-agent to create this agent.` and `Then run /gsd:new-agent with the modified context.` |

---

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None | — | — | No TODO/FIXME/placeholder/stub patterns found in either deliverable. |

Scan performed:
- `grep -n "TODO|FIXME|XXX|HACK|PLACEHOLDER"` on `scripts/patch-new-project.py` → 0 matches
- `grep -n "step body here|FULL STEP BODY|placeholder"` on `scripts/patch-new-project.py` → 0 matches (the plan's placeholder text was replaced with the real step body in the delivered file)
- `grep -n "return null|return \{\}"` not applicable (Python, not JS)
- No `console.log` patterns applicable

---

## Dry-Run Test Results

**Test performed:** Copied `~/.claude/get-shit-done/workflows/new-project.md` to `/tmp/new-project-test.md` and ran the patch script twice.

| Run | Command | Output | Exit |
|-----|---------|--------|------|
| First | `python3 scripts/patch-new-project.py /tmp/new-project-test.md` | `[OK] Patched: ...` + `Inserted: ## 8.5. Agent Team Setup (agent_team_hook)` | 0 |
| Second | `python3 scripts/patch-new-project.py /tmp/new-project-test.md` | `[SKIP] ... already patched (agent_team_hook already present)` | 0 |

**Insertion confirmed:** `## 8.5. Agent Team Setup` at line 899, `## 9. Done` at line 998 — exactly one `agent_team_hook` occurrence in patched file. Step body inserted between them is verbatim from the script's triple-quoted `new_section` string.

---

## Human Verification Required

### 1. Set up later / Skip path produces v1.0-identical outcome

**Test:** Run `/gsd:new-project`, complete through Step 8 (roadmap committed). When Step 8.5 asks "Set up an agent team for this project?", choose "Set up later" (or "Skip").
**Expected:** Immediately proceeds to Step 9 Done banner. No new files created. No TEAM.md modified. No agent files created. Elapsed time is effectively unchanged from a v1.0 run.
**Why human:** Requires an interactive Claude session to trigger the workflow.

### 2. Set up now path shows proposals before any AskUserQuestion

**Test:** Run `/gsd:new-project` through to Step 8.5. Choose "Set up now". Observe what Claude displays.
**Expected:** Claude reads PROJECT.md, then displays a "Proposed Agent Team" markdown block with 2-3 named agents (derived from the project's domain and stack), before any per-agent AskUserQuestion appears. The proposals show Name, Purpose, Mode, and Trigger for each agent.
**Why human:** Proposal content is dynamic and LLM-generated based on PROJECT.md contents. Requires interactive session to verify inline display precedes questions.

### 3. Per-agent delegation runs full /gsd:new-agent conversation

**Test:** In the "Set up now" path, when the per-agent AskUserQuestion appears for Agent 1, choose "Create this agent".
**Expected:** Claude displays the proposal context block (Name, Purpose, Mode, Trigger), then starts the full /gsd:new-agent guided conversation (9 steps). The new-project flow does not ask any additional configuration questions directly.
**Why human:** Requires interactive session; tests that delegation runs the complete /gsd:new-agent workflow rather than a shortened inline path.

---

## Gaps Summary

No gaps found. All three must-haves are verified by direct codebase inspection and dry-run testing.

The two deliverables (`scripts/patch-new-project.py` and `install.sh` Section 6 + Section 9 additions) are:
- Substantive (full step body implemented, no placeholders)
- Wired (install.sh invokes the patch script with existence guard; patch script inserts step at correct anchor with idempotency)
- Verified end-to-end via dry-run on the live installed new-project.md

Three items require human verification but are blocked only by the need for an interactive Claude session, not by code gaps.

---

_Verified: 2026-02-27T06:00:00Z_
_Verifier: Claude (gsd-verifier)_
