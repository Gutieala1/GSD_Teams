---
name: gsd:new-reviewer
description: Add a reviewer role to TEAM.md through a guided conversation
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
Add a new reviewer role to `.planning/TEAM.md` through a guided conversation.

Walks through: domain → role name → review criteria → severity thresholds → routing → confirmation → write.

**Creates or updates:** `.planning/TEAM.md`
</objective>

<execution_context>
@~/.claude/get-shit-done-review-team/workflows/new-reviewer.md
</execution_context>

<process>
Follow the new-reviewer workflow end-to-end.
Preserve all gates including the decision gate before writing.
Do not write to .planning/TEAM.md until the user confirms in the decision_gate step.
</process>
