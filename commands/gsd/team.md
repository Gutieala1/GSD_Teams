---
name: gsd:team
description: View and manage the agent team roster
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
View and manage all configured agents in `.planning/TEAM.md`.

Displays a formatted roster table with name, mode, triggers, output_type, and enabled status.
Disabled agents appear in the table but are visually distinguished.

From the roster: add an agent (→ `/gsd:new-reviewer`), remove an agent with confirmation,
enable or disable an agent, invoke an agent on-demand against a specified artifact, or view
agent history from AGENT-REPORT.md.

**Reads and writes:** `.planning/TEAM.md`
**Logs on-demand results to:** `.planning/phases/{current_phase}/AGENT-REPORT.md`
</objective>

<execution_context>
@~/.claude/get-shit-done-review-team/workflows/team-studio.md
</execution_context>

<process>
Follow the team-studio workflow end-to-end.
Do not write to .planning/TEAM.md until the user confirms any destructive action (remove)
or any state-change action (enable/disable).
Loop back to the action menu after each operation — exit only when user selects "Done".
</process>
