#!/usr/bin/env python3
"""
patch-execute-plan-dispatcher.py — Replace review_team_gate step body in GSD execute-plan.md
                                    to wire in the agent-dispatcher.md routing layer.

Phase 7 — Agent Dispatcher integration.

Usage: python3 scripts/patch-execute-plan-dispatcher.py <path-to-execute-plan.md>

Prerequisites:
  - patch-execute-plan.py (Phase 1) must have already been run first.
    That script inserts the review_team_gate step. This script replaces
    the step body with the dispatcher-aware version.

Idempotency check: 'agent-dispatcher.md' in content
  If already present, exits 0 with skip message — safe to run multiple times.

What this patch does:
  Replaces the review_team_gate step body so that:
    - If agent_studio is enabled → routes to agent-dispatcher.md
    - If only review_team is enabled → falls back to review-team.md (v1 path preserved)
    - Adds SKIP_REVIEW bypass flag for agent-creation plans
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-execute-plan-dispatcher.py <path-to-execute-plan.md>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Idempotency check — unique string only present after the dispatcher patch
    if 'agent-dispatcher.md' in content:
        print(f"  [SKIP] {target} already patched (dispatcher already wired)")
        sys.exit(0)

    # Anchor — the full current review_team_gate step body (inserted by patch-execute-plan.py)
    # Must match character-for-character including all whitespace and newlines.
    anchor = '''<step name="review_team_gate">
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
- If TEAM.md is missing: log `Review Team: skipped (no .planning/TEAM.md found — run /gsd:new-agent to create your first role)` and continue to `offer_next`. Do NOT block execution.
- If TEAM.md exists: load and execute the review pipeline:
  ```
  @~/.claude/get-shit-done-review-team/workflows/review-team.md
  ```
  Pass: current SUMMARY.md path, phase identifier, plan identifier.
</step>'''

    if anchor not in content:
        print(f"ERROR: Anchor string not found in {target}", file=sys.stderr)
        print(f"       Expected: review_team_gate step body (pre-dispatcher version)", file=sys.stderr)
        print(f"       This may mean:", file=sys.stderr)
        print(f"         1. patch-execute-plan.py has not been run yet (run it first)", file=sys.stderr)
        print(f"         2. The GSD version has changed the step structure", file=sys.stderr)
        sys.exit(1)

    new_step_body = '''<step name="review_team_gate">
Check whether Review Team pipeline or Agent Dispatcher should run:

```bash
REVIEW_TEAM_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.review_team // false')
AGENT_STUDIO_ENABLED=$(echo "$CONFIG_CONTENT" | jq -r '.workflow.agent_studio // false')
```

If neither `REVIEW_TEAM_ENABLED` nor `AGENT_STUDIO_ENABLED` is `"true"`: skip this step entirely — no output, no log.

Check bypass flag from current PLAN.md:
```bash
PLAN_FILE=$(ls .planning/phases/${PHASE_DIR}/*-PLAN.md 2>/dev/null | head -1)
SKIP_REVIEW=$(grep -m1 "^skip_review:" "$PLAN_FILE" 2>/dev/null | awk '{print $2}' || echo "false")
```
If `SKIP_REVIEW` is `"true"`: log `Agent Dispatcher: skipped (agent creation plan — bypass active)` and continue to `offer_next`.

Check that `.planning/TEAM.md` exists:
```bash
[ -f .planning/TEAM.md ] && echo "EXISTS" || echo "MISSING"
```
If TEAM.md is missing: log `Review Team: skipped (no .planning/TEAM.md found — run /gsd:new-agent to create your first role)` and continue to `offer_next`. Do NOT block execution.

If TEAM.md exists:
- If `AGENT_STUDIO_ENABLED` is `"true"`:
  ```
  @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
  ```
  Pass: trigger=post-plan, current SUMMARY.md path, phase identifier, plan identifier.
- Else if `REVIEW_TEAM_ENABLED` is `"true"`:
  ```
  @~/.claude/get-shit-done-review-team/workflows/review-team.md
  ```
  Pass: current SUMMARY.md path, phase identifier, plan identifier.
</step>'''

    patched = content.replace(anchor, new_step_body, 1)

    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)

    print(f"  [OK] Patched: {target}")
    print(f"       Updated: review_team_gate step body (dispatcher wired)")


if __name__ == '__main__':
    main()
