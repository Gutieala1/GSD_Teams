---
phase: 08-team-roster-gsd-team
plan: "02"
subsystem: team-studio
tags: [team-roster, slash-command, interactive-workflow, agent-management]
dependency_graph:
  requires:
    - 06-team-md-v2-schema-config-foundation  # TEAM.md v2 schema
    - 07-agent-dispatcher                      # normalizeRole algorithm reference
    - 08-01-PLAN                               # TEAM.md runtime context (ROST-01)
  provides:
    - /gsd:team slash command
    - team-studio.md interactive roster workflow
  affects:
    - install.sh Section 5 glob copy (commands/gsd/*.md, workflows/*.md)
    - ~/.claude/get-shit-done-review-team/commands/gsd/team.md (installed)
    - ~/.claude/get-shit-done-review-team/workflows/team-studio.md (installed)
tech_stack:
  added: []
  patterns:
    - AskUserQuestion menu loop (loop-back-to-menu convention)
    - Read-then-Write for TEAM.md state mutations
    - Task() on-demand agent invocation
    - AGENT-REPORT.md append logging pattern
key_files:
  created:
    - D:/GSDteams/commands/gsd/team.md
    - D:/GSDteams/workflows/team-studio.md
  modified: []
decisions:
  - "/gsd:team entry point references installed path (~/.claude/...) not source path — consistent with new-reviewer.md convention"
  - "show_roster re-uses dispatcher normalizeRole logic inline — no shared import; keeps workflow self-contained"
  - "invoke_on_demand filters to active_roles (enabled != false) only — disabled agents cannot be invoked on-demand"
  - "add_agent step: /gsd:new-reviewer for review roles, /gsd:new-agent noted as Phase 11 — no @-reference added (workflow not yet built)"
  - "remove_agent shows role block preview before confirmation gate — user sees exactly what will be deleted"
metrics:
  duration: "~1 minute"
  completed: "2026-02-27"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
---

# Phase 08 Plan 02: Team Studio Command + Workflow Summary

**One-liner:** `/gsd:team` slash command + 7-step team-studio.md workflow implementing full ROST-01/ROST-02 interactive roster management with on-demand agent invocation logged to AGENT-REPORT.md.

## What Was Built

### commands/gsd/team.md
Thin slash command entry point following the new-reviewer.md structure exactly:
- YAML frontmatter: `name: gsd:team`, `allowed-tools: [Read, Write, Bash, AskUserQuestion]`
- `<objective>`: describes roster display and all action capabilities
- `<execution_context>`: `@~/.claude/get-shit-done-review-team/workflows/team-studio.md` (installed path)
- `<process>`: no-write-until-confirmed constraint + loop-back-to-menu instruction

Picked up automatically by `install.sh` Section 5 `cp "$EXT_DIR/commands/gsd/"*.md` glob.

### workflows/team-studio.md
Full 7-step interactive workflow:

1. **show_roster** (priority="first") — checks TEAM.md exists, reads + parses roles, applies
   normalizeRole defaults (mode/trigger/output_type for version < 2, enabled default true),
   renders markdown table with `active` / `**DISABLED**` status, shows trigger-count summary line

2. **present_actions** — AskUserQuestion menu loop with 6 options: Enable/Disable, Remove agent,
   Run agent now, View history, Add agent, Done. Only "Done" exits; all others loop back.

3. **toggle_enabled** — shows per-agent current status, Read-then-Write to flip `enabled` field
   in YAML config block, announces dispatcher behavior change

4. **remove_agent** — agent selection → role block preview → "cannot be undone" confirmation gate
   → deletes slug from frontmatter roles list + role block from body → updates in-memory roster
   and re-renders table

5. **invoke_on_demand** — enabled agents only (`active_roles` filter), artifact selection from
   recent files or manual path, Task() spawn with role_block + artifact content, result displayed
   inline, appended to `AGENT-REPORT.md` with ISO timestamp header

6. **view_history** — finds all AGENT-REPORT.md files via bash find, filters to specific agent
   slug or displays all, graceful "no history" message when none found

7. **add_agent** — informs user of /gsd:new-reviewer (review-team roles) and /gsd:new-agent
   (Phase 11, not yet built); no @-reference to missing workflow

Picked up automatically by `install.sh` Section 5 `cp "$EXT_DIR/workflows/"*.md` glob.

## Deviations from Plan

None — plan executed exactly as written.

## Decisions Made

1. **Installed path in @-reference**: `team.md` uses `@~/.claude/get-shit-done-review-team/workflows/team-studio.md` — same pattern as `new-reviewer.md` referencing its installed workflow. Source path would break after `install.sh` copies files.

2. **normalizeRole inline**: The team-studio.md workflow re-implements the same normalizeRole algorithm from agent-dispatcher.md inline. This keeps the workflow self-contained (no cross-file import needed for a slash command context).

3. **active_roles filter for invoke_on_demand**: `enabled != false` is the correct guard — matches the dispatcher's behavior where absent/null enabled is treated as true.

4. **No @-reference to /gsd:new-agent**: The add_agent step informs users that `/gsd:new-agent` is Phase 11 but does NOT add an @-reference to a workflow that doesn't exist yet. Informational message only.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 2ca1276 | feat(08-02): create /gsd:team slash command entry point |
| Task 2 | 1fc39ff | feat(08-02): create team-studio.md interactive roster workflow |

## Self-Check: PASSED

- FOUND: commands/gsd/team.md
- FOUND: workflows/team-studio.md
- FOUND: .planning/phases/08-team-roster-gsd-team/08-02-SUMMARY.md
- FOUND: commit 2ca1276 (feat(08-02): create /gsd:team slash command entry point)
- FOUND: commit 1fc39ff (feat(08-02): create team-studio.md interactive roster workflow)
