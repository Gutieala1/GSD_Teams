#!/usr/bin/env python3
"""
patch-settings.py -- Add Review Team toggle to GSD settings.md

Usage: python3 scripts/patch-settings.py <path-to-settings.md>

Makes four targeted replacements:
  1. Adds 7th question to AskUserQuestion array
  2. Adds review_team + spread to update_config workflow object
  3. Adds review_team + spread to save_as_defaults workflow object
  4. Updates success_criteria count 6 -> 7

Idempotent: each replacement is skipped if already applied.
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-settings.py <path-to-settings.md>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    patches_applied = 0
    patches_skipped = 0

    # --- Touch point 1: AskUserQuestion 7th entry ---
    tp1_check = '"Review Team"'
    tp1_anchor = '      { label: "Per Milestone", description: "Create branch for entire milestone (gsd/{version}-{name})" }'
    tp1_replacement = '      { label: "Per Milestone", description: "Create branch for entire milestone (gsd/{version}-{name})" }\n    ]\n  }\n  ,\n  {\n    question: "Spawn Review Team? (multi-agent review after each plan executes)",\n    header: "Review Team",\n    multiSelect: false,\n    options: [\n      { label: "No (Default)", description: "Skip review pipeline -- standard execution" },\n      { label: "Yes", description: "After each plan: sanitize output, spawn reviewers, synthesize findings" }\n    ]\n  }\n])'

    # The anchor for tp1 needs to cover the closing of the branching question block
    # The exact anchor: from the "Per Milestone" line through the closing of the AskUserQuestion call
    tp1_anchor_full = '      { label: "Per Milestone", description: "Create branch for entire milestone (gsd/{version}-{name})" }\n    ]\n  }\n])'
    tp1_new_full = '      { label: "Per Milestone", description: "Create branch for entire milestone (gsd/{version}-{name})" }\n    ]\n  }\n  ,\n  {\n    question: "Spawn Review Team? (multi-agent review after each plan executes)",\n    header: "Review Team",\n    multiSelect: false,\n    options: [\n      { label: "No (Default)", description: "Skip review pipeline -- standard execution" },\n      { label: "Yes", description: "After each plan: sanitize output, spawn reviewers, synthesize findings" }\n    ]\n  }\n])'

    if tp1_check in content:
        print("  [SKIP] Touch point 1 (AskUserQuestion 7th entry): already patched")
        patches_skipped += 1
    elif tp1_anchor_full not in content:
        print("  [WARN] Touch point 1: anchor not found -- settings.md structure may have changed", file=sys.stderr)
        patches_skipped += 1
    else:
        content = content.replace(tp1_anchor_full, tp1_new_full, 1)
        print("  [OK]   Touch point 1: added Review Team question to AskUserQuestion array")
        patches_applied += 1

    # --- Touch point 2: update_config workflow spread ---
    tp2_check = '...existing_config.workflow'
    tp2_old = '  "workflow": {\n    "research": true/false,\n    "plan_check": true/false,\n    "verifier": true/false,\n    "auto_advance": true/false\n  },'
    tp2_new = '  "workflow": {\n    ...existing_config.workflow,\n    "research": true/false,\n    "plan_check": true/false,\n    "verifier": true/false,\n    "auto_advance": true/false,\n    "review_team": true/false\n  },'

    if tp2_check in content:
        print("  [SKIP] Touch point 2 (update_config workflow spread): already patched")
        patches_skipped += 1
    elif tp2_old not in content:
        print("  [WARN] Touch point 2: anchor not found -- settings.md structure may have changed", file=sys.stderr)
        patches_skipped += 1
    else:
        content = content.replace(tp2_old, tp2_new, 1)
        print("  [OK]   Touch point 2: update_config workflow object now spread-safe with review_team")
        patches_applied += 1

    # --- Touch point 3: save_as_defaults workflow spread ---
    tp3_check = '...existing_workflow'
    tp3_old = '    "research": <current>,\n    "plan_check": <current>,\n    "verifier": <current>,\n    "auto_advance": <current>'
    tp3_new = '    ...existing_workflow,\n    "research": <current>,\n    "plan_check": <current>,\n    "verifier": <current>,\n    "auto_advance": <current>,\n    "review_team": <current>'

    if tp3_check in content:
        print("  [SKIP] Touch point 3 (save_as_defaults workflow spread): already patched")
        patches_skipped += 1
    elif tp3_old not in content:
        print("  [WARN] Touch point 3: anchor not found -- settings.md structure may have changed", file=sys.stderr)
        patches_skipped += 1
    else:
        content = content.replace(tp3_old, tp3_new, 1)
        print("  [OK]   Touch point 3: save_as_defaults workflow object now spread-safe with review_team")
        patches_applied += 1

    # --- Touch point 4: success_criteria count ---
    tp4_check = '7 settings'
    tp4_old = '- [ ] User presented with 6 settings (profile + 4 workflow toggles + git branching)'
    tp4_new = '- [ ] User presented with 7 settings (profile + 5 workflow toggles + git branching)'

    if tp4_check in content:
        print("  [SKIP] Touch point 4 (success_criteria count): already patched")
        patches_skipped += 1
    elif tp4_old not in content:
        print("  [WARN] Touch point 4: anchor not found -- settings.md structure may have changed", file=sys.stderr)
        patches_skipped += 1
    else:
        content = content.replace(tp4_old, tp4_new, 1)
        print("  [OK]   Touch point 4: success_criteria updated (6 -> 7 settings)")
        patches_applied += 1

    # Write result
    if patches_applied > 0:
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n  Patched: {target} ({patches_applied} change(s) applied, {patches_skipped} skipped)")
    else:
        print(f"\n  [SKIP] No changes needed: {target} is already fully patched")


if __name__ == '__main__':
    main()
