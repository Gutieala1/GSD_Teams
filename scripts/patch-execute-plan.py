#!/usr/bin/env python3
"""
patch-execute-plan.py — Insert review_team_gate step into GSD execute-plan.md

Usage: python3 scripts/patch-execute-plan.py <path-to-execute-plan.md>

Idempotent: exits 0 with skip message if already patched.
"""

import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-execute-plan.py <path-to-execute-plan.md>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Idempotency check
    if 'name="review_team_gate"' in content:
        print(f"  [SKIP] {target} already patched (review_team_gate step found)")
        sys.exit(0)

    anchor = '<step name="offer_next">'

    if anchor not in content:
        print(f"ERROR: Anchor string not found in {target}", file=sys.stderr)
        print(f"       Expected: {anchor}", file=sys.stderr)
        print(f"       This may mean the GSD version has changed the step structure.", file=sys.stderr)
        sys.exit(1)

    new_step = '''<step name="review_team_gate">
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
</step>

'''

    patched = content.replace(anchor, new_step + anchor, 1)

    with open(target, 'w', encoding='utf-8') as f:
        f.write(patched)

    print(f"  [OK] Patched: {target}")
    print(f"       Inserted: review_team_gate step before offer_next")

if __name__ == '__main__':
    main()
