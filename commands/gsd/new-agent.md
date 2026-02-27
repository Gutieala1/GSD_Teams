---
name: gsd:new-agent
description: Create a new agent role through a guided conversation
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
Create a new agent role in `.planning/TEAM.md` through a guided conversation.

Walks through: purpose → mode → trigger → output type → advisory details (advisory only)
→ scope (autonomous only) → confirmation gate → write.

**Creates or updates:**
- `.planning/TEAM.md` (always — role block appended, frontmatter roles: list updated)
- `agents/gsd-agent-{slug}.md` (autonomous agents only — agent prompt template)
</objective>

<execution_context>
@~/.claude/get-shit-done-review-team/workflows/new-agent.md
</execution_context>

<process>
Follow the new-agent workflow end-to-end.
Preserve all gates including the decision gate before writing.
Do not write to .planning/TEAM.md or agents/ until the user confirms in the decision_gate step.
If the user selects "Cancel" at the decision gate, exit immediately with no file writes.
</process>
