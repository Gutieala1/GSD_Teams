#!/usr/bin/env python3
"""
patch-new-project.py — Insert agent_team_hook step into GSD new-project.md
                        to wire in agent team setup after project initialization.

Phase 12 — INIT-01, INIT-02, INIT-03: agent_team_hook lifecycle step.

Usage: python3 scripts/patch-new-project.py <path-to-new-project.md>

Idempotency check: 'agent_team_hook' in content
  If already present, exits 0 with skip message — safe to run multiple times.
"""

import sys
import os


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

    # Idempotency check — unique string only present after agent_team_hook patch
    if 'agent_team_hook' in content:
        print(f"  [SKIP] {target} already patched (agent_team_hook already present)")
        sys.exit(0)

    anchor = '\n## 9. Done\n'

    if anchor not in content:
        print(f"ERROR: Anchor string not found in {target}", file=sys.stderr)
        print(f"       Expected: '\\n## 9. Done\\n'", file=sys.stderr)
        print(f"       This may mean:", file=sys.stderr)
        print(f"         1. The GSD version has changed the step numbering", file=sys.stderr)
        print(f"         2. new-project.md has already been manually modified", file=sys.stderr)
        sys.exit(1)

    new_section = '''
## 8.5. Agent Team Setup
<!-- step: agent_team_hook -->

**If auto mode:** Skip this step entirely — no agent team questions in auto mode.

Ask the user one question:

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

**If "Set up later" or "Skip":** Continue to Step 9. No files written. Timing unchanged.

**If "Set up now":**

Read `.planning/PROJECT.md` and extract:
- Core value (what must work)
- Domain/purpose (inferred from requirements and goals)
- Tech stack (from Key Decisions table or requirements categories)

Also read `.planning/research/STACK.md` if it exists.
Also read `.planning/research/FEATURES.md` if it exists.

Based on the project domain and stack, propose 2-3 tailored agents.
Display all proposals inline as a markdown block — do NOT use AskUserQuestion for proposals:

---
**Proposed Agent Team**

Based on your project goals, here are agents that would be useful:

**Agent 1: [Name]**
- Purpose: [one sentence]
- Mode: [advisory/autonomous]
- Trigger: [pre-plan/post-plan/post-phase]

**Agent 2: [Name]**
- Purpose: [one sentence]
- Mode: [advisory/autonomous]
- Trigger: [pre-plan/post-plan/post-phase]

**Agent 3: [Name]** (optional — include only if a clear third agent is appropriate)
- Purpose: [one sentence]
- Mode: [advisory/autonomous]
- Trigger: [pre-plan/post-plan/post-phase]
---

Domain-to-agent heuristics (use these to derive proposals):
- Any project → "Requirements Coverage Checker" (pre-plan advisory: checks plans cover active requirements)
- Code-producing project → "Security Auditor" (post-plan advisory: checks for security issues)
- API/backend project → "API Contract Checker" (post-plan advisory: checks endpoint contracts)
- Frontend/UI project → "Accessibility Auditor" (post-plan advisory)
- Any project → "Changelog Agent" (post-phase autonomous: writes CHANGELOG.md entries)
- If PROJECT.md is very minimal → fall back to 2 generic proposals: "Requirements Coverage Checker" + "Changelog Agent"

For EACH proposed agent (sequentially, not all at once):

Display the proposal block again so the user knows which agent is being discussed.

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

If "Create this agent":
  Display the proposal context so the user can reference it:
  > Based on the proposal, this agent would be:
  > - Name: [proposed name]
  > - Purpose: [purpose sentence]
  > - Mode: [advisory/autonomous]
  > - Trigger: [trigger]
  Run /gsd:new-agent to create this agent.

If "Modify first":
  Ask: "What would you like to change?" (free text, no AskUserQuestion — just ask inline).
  Accept their modification notes, adjust the proposal, re-display the updated proposal.
  Then run /gsd:new-agent with the modified context.

If "Skip":
  Continue to the next proposed agent.

After all proposed agents are processed:
  Announce: "Agent team setup complete. You can manage agents anytime with /gsd:team."
  Continue to Step 9.

'''

    patched = content.replace(anchor, new_section + '\n## 9. Done\n', 1)

    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)

    print(f"  [OK] Patched: {target}")
    print(f"       Inserted: ## 8.5. Agent Team Setup (agent_team_hook)")


if __name__ == '__main__':
    main()
