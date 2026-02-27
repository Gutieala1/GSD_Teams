#!/usr/bin/env python3
"""
patch-settings-agent-studio.py -- Add Agent Studio toggle to GSD settings.md

Usage: python3 scripts/patch-settings-agent-studio.py <path-to-settings.md>

Makes four targeted replacements:
  1. Adds 8th question to AskUserQuestion array (Agent Studio toggle)
  2. Adds agent_studio to update_config workflow object
  3. Adds agent_studio to save_as_defaults workflow object
  4. Updates success_criteria count 7 -> 8

Idempotent: each replacement is skipped if already applied.
Anchors target the state of settings.md already patched with Review Team (patch-settings.py).
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-settings-agent-studio.py <path-to-settings.md>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    patches_applied = 0
    patches_skipped = 0

    # --- Touch point 1: AskUserQuestion 8th entry (Agent Studio) ---
    # Anchor: tail of the Review Team question block's closing in the already-patched settings.md
    tp1_check = '"Agent Studio"'
    tp1_anchor_full = '      { label: "No (Default)", description: "Skip review pipeline -- standard execution" },\n      { label: "Yes", description: "After each plan: sanitize output, spawn reviewers, synthesize findings" }\n    ]\n  }\n])'
    tp1_new_full = '      { label: "No (Default)", description: "Skip review pipeline -- standard execution" },\n      { label: "Yes", description: "After each plan: sanitize output, spawn reviewers, synthesize findings" }\n    ]\n  }\n  ,\n  {\n    question: "Enable Agent Studio? (agents fire on plan/phase lifecycle events)",\n    header: "Agent Studio",\n    multiSelect: false,\n    options: [\n      { label: "No (Default)", description: "Disable all agent lifecycle hooks" },\n      { label: "Yes", description: "Enable agents to run at pre-plan, post-plan, and post-phase triggers" }\n    ]\n  }\n])'

    if tp1_check in content:
        print("  [SKIP] Touch point 1 (AskUserQuestion 8th entry): already patched")
        patches_skipped += 1
    elif tp1_anchor_full not in content:
        print("  [WARN] Touch point 1: anchor not found -- settings.md structure may have changed", file=sys.stderr)
        patches_skipped += 1
    else:
        content = content.replace(tp1_anchor_full, tp1_new_full, 1)
        print("  [OK]   Touch point 1: added Agent Studio question to AskUserQuestion array")
        patches_applied += 1

    # --- Touch point 2: update_config workflow object ---
    # Anchor: current last key in the update_config workflow block (review_team), already spread-safe
    tp2_check = '"agent_studio": true/false'
    tp2_old = '    "review_team": true/false\n  },'
    tp2_new = '    "review_team": true/false,\n    "agent_studio": true/false\n  },'

    if tp2_check in content:
        print("  [SKIP] Touch point 2 (update_config workflow object): already patched")
        patches_skipped += 1
    elif tp2_old not in content:
        print("  [WARN] Touch point 2: anchor not found -- settings.md structure may have changed", file=sys.stderr)
        patches_skipped += 1
    else:
        content = content.replace(tp2_old, tp2_new, 1)
        print("  [OK]   Touch point 2: update_config workflow object now includes agent_studio")
        patches_applied += 1

    # --- Touch point 3: save_as_defaults workflow object ---
    # Anchor: current last key in the save_as_defaults workflow block (review_team)
    tp3_check = '"agent_studio": <current>'
    tp3_old = '    "review_team": <current>\n  }'
    tp3_new = '    "review_team": <current>,\n    "agent_studio": <current>\n  }'

    if tp3_check in content:
        print("  [SKIP] Touch point 3 (save_as_defaults workflow object): already patched")
        patches_skipped += 1
    elif tp3_old not in content:
        print("  [WARN] Touch point 3: anchor not found -- settings.md structure may have changed", file=sys.stderr)
        patches_skipped += 1
    else:
        content = content.replace(tp3_old, tp3_new, 1)
        print("  [OK]   Touch point 3: save_as_defaults workflow object now includes agent_studio")
        patches_applied += 1

    # --- Touch point 4: success_criteria count ---
    tp4_check = '8 settings'
    tp4_old = '- [ ] User presented with 7 settings (profile + 5 workflow toggles + git branching)'
    tp4_new = '- [ ] User presented with 8 settings (profile + 6 workflow toggles + git branching)'

    if tp4_check in content:
        print("  [SKIP] Touch point 4 (success_criteria count): already patched")
        patches_skipped += 1
    elif tp4_old not in content:
        print("  [WARN] Touch point 4: anchor not found -- settings.md structure may have changed", file=sys.stderr)
        patches_skipped += 1
    else:
        content = content.replace(tp4_old, tp4_new, 1)
        print("  [OK]   Touch point 4: success_criteria updated (7 -> 8 settings)")
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
