#!/usr/bin/env python3
"""
patch-execute-phase.py — Insert post_phase_agent_gate step into GSD execute-phase.md
                         before the close_parent_artifacts step.

Phase 9 LIFE-03 — Post-Phase Agent Gate.

Usage: python3 scripts/patch-execute-phase.py <path-to-execute-phase.md>

Idempotency check: 'post_phase_agent_gate' in content
  If already present, exits 0 with skip message — safe to run multiple times.

What this patch does:
  Inserts a new <step name="post_phase_agent_gate"> block immediately before
  <step name="close_parent_artifacts"> so that after all waves complete:
    - If agent_studio is enabled and TEAM.md exists -> calls agent-dispatcher.md
      with trigger=post-phase
    - On any error (dispatcher failure, TEAM.md missing, config absent):
      logs and proceeds to close_parent_artifacts (fail-open, non-blocking)
    - Advisory agent output is written to AGENT-REPORT.md by the dispatcher
    - Autonomous agents commit artifacts directly per their role definition
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-execute-phase.py <path-to-execute-phase.md>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Idempotency check — unique string only present after this patch
    if 'post_phase_agent_gate' in content:
        print(f"  [SKIP] {target} already patched (post_phase_agent_gate already present)")
        sys.exit(0)

    # Anchor — insert the new step immediately BEFORE this string
    anchor = '<step name="close_parent_artifacts">'

    if anchor not in content:
        print(f"ERROR: Anchor string not found in {target}", file=sys.stderr)
        print(f"       Expected: {anchor}", file=sys.stderr)
        print(f"       This may mean:", file=sys.stderr)
        print(f"         1. The GSD version has changed the step structure", file=sys.stderr)
        print(f"         2. The file path is incorrect", file=sys.stderr)
        sys.exit(1)

    new_step = '''<step name="post_phase_agent_gate">
Check whether post-phase agents should fire after all waves complete.

```bash
AGENT_STUDIO_ENABLED=$(node C:/Users/gutie/.claude/get-shit-done/bin/gsd-tools.cjs config get workflow.agent_studio 2>/dev/null || echo "false")
```

If `AGENT_STUDIO_ENABLED` is not `"true"`: skip this step entirely — no output, no log.
Proceed to close_parent_artifacts.

If `AGENT_STUDIO_ENABLED` is `"true"`:

1. Check that `.planning/TEAM.md` exists:
   ```bash
   [ -f .planning/TEAM.md ] && echo "EXISTS" || echo "MISSING"
   ```
   If TEAM.md is missing: log `Post-phase gate: no TEAM.md found — skipping` and continue
   to close_parent_artifacts. Do NOT block execution.

2. If TEAM.md exists: call the dispatcher:
   ```
   @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
   ```
   Pass: trigger=post-phase, phase_id={phase_dir}, plan_num=all.

3. Advisory agent output is written to `.planning/phases/{phase_dir}/AGENT-REPORT.md` by
   the dispatcher (append with header `## Post-Phase: {agent-slug} — {ISO timestamp}`).
   Autonomous agents commit artifacts directly per their role definition.

4. If the dispatcher call fails or errors: log
   `Post-phase gate: dispatcher error — skipping (non-blocking)` and continue to
   close_parent_artifacts. Do NOT block phase completion.
</step>'''

    patched = content.replace(anchor, new_step + '\n\n' + anchor, 1)

    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)

    print(f"  [OK] Patched: {target}")
    print(f"       Inserted: post_phase_agent_gate step before close_parent_artifacts")


if __name__ == '__main__':
    main()
