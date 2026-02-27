#!/usr/bin/env python3
"""
patch-plan-phase.py — Insert pre_plan_agent_gate step into GSD plan-phase.md
                       to wire in the agent dispatcher before plan creation.

Phase 9 — LIFE-02: pre_plan_agent_gate lifecycle trigger hook.

Usage: python3 scripts/patch-plan-phase.py <path-to-plan-phase.md>

Prerequisites:
  - GSD plan-phase.md must exist at the target path.
    Typically: ~/.claude/get-shit-done/workflows/plan-phase.md

Idempotency check: 'pre_plan_agent_gate' in content
  If already present, exits 0 with skip message — safe to run multiple times.

What this patch does:
  Inserts a new "## 13. Pre-Plan Agent Gate" step before "## 13. Present Final Status",
  renaming the old step 13 to "## 14. Present Final Status" and the old step 14 to
  "## 15. Auto-Advance Check". The pre-plan gate is ALWAYS fail-open — any dispatcher
  error, agent timeout, or missing config MUST NOT prevent plan creation.
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-plan-phase.py <path-to-plan-phase.md>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Idempotency check — unique string only present after the pre-plan gate patch
    if 'pre_plan_agent_gate' in content:
        print(f"  [SKIP] {target} already patched (pre_plan_agent_gate already present)")
        sys.exit(0)

    # Anchor — the old step 13 heading, renamed to 14 in the replacement.
    # Must match character-for-character including surrounding newlines.
    anchor = '\n## 13. Present Final Status\n'

    if anchor not in content:
        print(f"ERROR: Anchor string not found in {target}", file=sys.stderr)
        print(f"       Expected: '\\n## 13. Present Final Status\\n'", file=sys.stderr)
        print(f"       This may mean:", file=sys.stderr)
        print(f"         1. The GSD version has changed the step structure", file=sys.stderr)
        print(f"         2. plan-phase.md step numbering has already been modified", file=sys.stderr)
        sys.exit(1)

    new_section = '''
## 13. Pre-Plan Agent Gate
<!-- step: pre_plan_agent_gate -->

Check whether pre-plan agents should fire before presenting final status.

**This gate is ALWAYS fail-open.** Any failure here — dispatcher error, agent timeout,
TEAM.md unreadable, config missing — MUST NOT prevent plan creation. Catch all errors
and proceed to step 14 (present final status) regardless.

```bash
AGENT_STUDIO_ENABLED=$(node C:/Users/gutie/.claude/get-shit-done/bin/gsd-tools.cjs config get workflow.agent_studio 2>/dev/null || echo "false")
```

If `AGENT_STUDIO_ENABLED` is not `"true"`: skip this step entirely — no output, no log.
Proceed directly to step 14.

If `AGENT_STUDIO_ENABLED` is `"true"`:

1. Check that `.planning/TEAM.md` exists. If missing: log
   `Pre-plan gate: no TEAM.md found — skipping` and proceed to step 14.

2. If TEAM.md exists: call the dispatcher:
   ```
   @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
   ```
   Pass: trigger=pre-plan, phase_id={phase_dir}, plan_num=pre-plan.

3. If the dispatcher call fails or errors: log
   `Pre-plan gate: dispatcher error — proceeding with plan creation (fail-open)`
   and continue to step 14. Do NOT stop or report failure.

4. Dispatcher output (agent notes, if any) is collected and displayed inline.
   Injection into the planner Task() prompt is Phase 10 (ADVY-01) — not implemented here.

'''

    # Replace: insert new section 13 before old section 13, renaming old 13 → 14
    replacement = new_section + '## 14. Present Final Status\n'
    patched = content.replace(anchor, replacement, 1)

    # Also rename old "## 14. Auto-Advance Check" → "## 15. Auto-Advance Check"
    # Only perform this rename if "## 14. Auto-Advance Check" exists in the (already patched) content
    if '## 14. Auto-Advance Check' in patched:
        patched = patched.replace('## 14. Auto-Advance Check', '## 15. Auto-Advance Check', 1)

    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)

    print(f"  [OK] Patched: {target}")
    print(f"       Inserted: ## 13. Pre-Plan Agent Gate (fail-open dispatcher trigger)")
    print(f"       Renamed:  ## 13. Present Final Status -> ## 14. Present Final Status")
    if '## 15. Auto-Advance Check' in patched:
        print(f"       Renamed:  ## 14. Auto-Advance Check -> ## 15. Auto-Advance Check")


if __name__ == '__main__':
    main()
