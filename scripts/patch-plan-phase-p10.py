#!/usr/bin/env python3
"""
patch-plan-phase-p10.py — Move pre_plan_agent_gate from step 13 (after planner) to
                           step 8 (before planner), and inject AGENT_NOTES into the
                           planner Task() prompt.

Phase 10 — ADVY-01: Advisory output to planner.

Usage: python3 scripts/patch-plan-phase-p10.py <path-to-plan-phase.md>

Prerequisites:
  - GSD plan-phase.md must already have Phase 9 patch applied
    (pre_plan_agent_gate step must exist at step 13).
    Typically: ~/.claude/get-shit-done/workflows/plan-phase.md

Idempotency check: 'AGENT_NOTES' in content
  If already present, exits 0 with skip message — safe to run multiple times.

What this patch does:
  1. Removes old step 13 (Pre-Plan Agent Gate with ADVY-01 deferred note),
     renaming old step 14 "Present Final Status" to step 13.
  2. Inserts a new step 8 (Pre-Plan Agent Gate) before the planner spawn,
     renumbering old step 8 "Spawn gsd-planner Agent" to step 9 and all
     subsequent steps (9->10, 10->11, 11->12, 12->13).
  3. Injects {AGENT_NOTES} interpolation into the planner Task() prompt block
     (after {research_content} / {uat_content} line, before </planning_context>).
  4. Updates internal step cross-references for correctness.

The gate is ALWAYS fail-open — any dispatcher error, agent timeout, or missing
config MUST NOT prevent plan creation. AGENT_NOTES defaults to "" and is harmless
whitespace when empty.
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch-plan-phase-p10.py <path-to-plan-phase.md>",
              file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(1)

    with open(target, 'r', encoding='utf-8') as f:
        content = f.read()

    # Idempotency check — unique string only present after Phase 10 patch
    if 'AGENT_NOTES' in content:
        print(f"  [SKIP] {target} already patched (AGENT_NOTES already present)")
        sys.exit(0)

    # -------------------------------------------------------------------------
    # Anchor A — Remove old step 13 gate body and rename step 14 → step 13
    # -------------------------------------------------------------------------
    # The old step 13 heading was inserted by the Phase 9 patch. It starts with
    # the heading line and the idempotency HTML comment, and runs until step 14.
    # We replace the entire old step 13 block (heading + body) such that old
    # step 14 "Present Final Status" becomes the new step 13.

    anchor_old_gate_heading = '\n## 13. Pre-Plan Agent Gate\n<!-- step: pre_plan_agent_gate -->\n'
    anchor_step14 = '\n## 14. Present Final Status\n'

    if anchor_old_gate_heading not in content:
        print(
            'ERROR: Anchor not found — old step 13 gate heading '
            '(## 13. Pre-Plan Agent Gate / <!-- step: pre_plan_agent_gate -->)',
            file=sys.stderr
        )
        sys.exit(1)

    if anchor_step14 not in content:
        print(
            'ERROR: Anchor not found — ## 14. Present Final Status',
            file=sys.stderr
        )
        sys.exit(1)

    # Find the start of the old step 13 block and the start of step 14
    gate_start = content.index(anchor_old_gate_heading)
    step14_start = content.index(anchor_step14)

    if step14_start <= gate_start:
        print(
            'ERROR: Step 14 appears before step 13 — unexpected file structure',
            file=sys.stderr
        )
        sys.exit(1)

    # Replace everything from the old step 13 heading up to (not including) step 14,
    # and rename step 14 → step 13 at the same time.
    # Before gate: content[:gate_start]
    # After step14 heading: content[step14_start + len(anchor_step14):]
    # We replace anchor_step14 with \n## 13. Present Final Status\n
    content = (
        content[:gate_start]
        + '\n## 13. Present Final Status\n'
        + content[step14_start + len(anchor_step14):]
    )

    # Also rename ## 15. Auto-Advance Check → ## 14. Auto-Advance Check
    # (old step 15 becomes new step 14 after removing old step 13)
    if '\n## 15. Auto-Advance Check\n' in content:
        content = content.replace(
            '\n## 15. Auto-Advance Check\n',
            '\n## 14. Auto-Advance Check\n',
            1
        )

    # -------------------------------------------------------------------------
    # Anchor B — Insert new step 8 gate before planner and renumber steps 8-13
    # -------------------------------------------------------------------------
    anchor_before_planner = '\n## 8. Spawn gsd-planner Agent\n'

    if anchor_before_planner not in content:
        print(
            'ERROR: Anchor not found — ## 8. Spawn gsd-planner Agent',
            file=sys.stderr
        )
        sys.exit(1)

    new_gate_block = '''
## 8. Pre-Plan Agent Gate
<!-- step: pre_plan_agent_gate -->

Check whether pre-plan advisory agents should fire before creating plans.

**This gate is ALWAYS fail-open.** Any failure — dispatcher error, agent timeout, TEAM.md
unreadable, config missing — MUST NOT prevent plan creation. Set AGENT_NOTES="" and
proceed to step 9 (spawn planner) regardless.

```bash
AGENT_NOTES=""
AGENT_STUDIO_ENABLED=$(node C:/Users/gutie/.claude/get-shit-done/bin/gsd-tools.cjs config get workflow.agent_studio 2>/dev/null || echo "false")
```

If `AGENT_STUDIO_ENABLED` is not `"true"`: set `AGENT_NOTES=""` and proceed to step 9.

If `AGENT_STUDIO_ENABLED` is `"true"`:

1. Check that `.planning/TEAM.md` exists. If missing: log
   `Pre-plan gate: no TEAM.md found — skipping` and set `AGENT_NOTES=""` and proceed to step 9.

2. If TEAM.md exists: call the dispatcher:
   ```
   @~/.claude/get-shit-done-review-team/workflows/agent-dispatcher.md
   ```
   Pass: trigger=pre-plan, phase_id={phase_dir}, plan_num=pre-plan.

3. If dispatcher call fails or errors: log
   `Pre-plan gate: dispatcher error — proceeding with plan creation (fail-open)`
   Set `AGENT_NOTES=""` and proceed to step 9.

4. If dispatcher returns advisory notes from `output_type: notes` agents:
   Set `AGENT_NOTES` to the formatted `<agent_notes>` block returned by the dispatcher.
   The dispatcher returns the block as part of its output text — extract by looking for
   `<agent_notes>` opening tag in the dispatcher return value.

5. If `AGENT_NOTES` is non-empty: include it in the planner prompt at step 9 (see {AGENT_NOTES}
   interpolation position in the planner Task() prompt block).
   If `AGENT_NOTES` is empty: the template interpolation at step 9 produces harmless whitespace
   — this is acceptable and does not confuse the planner. No conditional omission is needed.

6. Log: `Pre-plan gate: {N} advisory agent(s) fired. Notes collected: {yes|no}`

'''

    # Insert new gate block before old step 8, then rename old step 8 → step 9
    content = content.replace(
        anchor_before_planner,
        new_gate_block + '## 9. Spawn gsd-planner Agent\n',
        1
    )

    # Renumber subsequent steps: old 9→10, 10→11, 11→12, 12→13
    # These are now: Handle Planner Return, Spawn Checker, Handle Checker, Revision Loop
    # Perform in reverse order to avoid cascade conflicts
    step_renames = [
        ('\n## 12. Revision Loop', '\n## 13. Revision Loop'),
        ('\n## 11. Handle Checker Return', '\n## 12. Handle Checker Return'),
        ('\n## 10. Spawn gsd-plan-checker Agent', '\n## 11. Spawn gsd-plan-checker Agent'),
        ('\n## 9. Handle Planner Return', '\n## 10. Handle Planner Return'),
    ]
    for old, new in step_renames:
        if old in content:
            content = content.replace(old, new, 1)
        else:
            print(
                f'ERROR: Anchor not found — step heading: {old.strip()}',
                file=sys.stderr
            )
            sys.exit(1)

    # -------------------------------------------------------------------------
    # Anchor C — Inject {AGENT_NOTES} into planner prompt template
    # -------------------------------------------------------------------------
    anchor_planner_research = (
        '**Research:** {research_content}\n'
        '**Gap Closure (if --gaps):** {verification_content} {uat_content}\n'
        '</planning_context>'
    )

    if anchor_planner_research not in content:
        print(
            'ERROR: Anchor not found — planner research/planning_context block '
            '(**Research:** {research_content} line)',
            file=sys.stderr
        )
        sys.exit(1)

    content = content.replace(
        anchor_planner_research,
        '**Research:** {research_content}\n'
        '**Gap Closure (if --gaps):** {verification_content} {uat_content}\n'
        '\n{AGENT_NOTES}\n'
        '</planning_context>',
        1
    )

    # -------------------------------------------------------------------------
    # Update internal step cross-references for correctness after renumbering
    # -------------------------------------------------------------------------
    # Handle Planner Return (now step 10) references: "skip to step 13" -> "skip to step 14"
    # (Present Final Status moved from 14->13 then back to 14 after planner step shifts)
    # Final numbering: Present Final Status = 14, Revision Loop = 13
    content = content.replace(
        'skip to step 13. Otherwise: step 10.',
        'skip to step 14. Otherwise: step 11.',
        1
    )
    # "spawn continuation (step 12)" — Revision Loop is now step 13
    content = content.replace(
        'get response, spawn continuation (step 12)',
        'get response, spawn continuation (step 13)',
        1
    )
    # Handle Checker Return (now step 12) references: "proceed to step 13" -> "proceed to step 14"
    content = content.replace(
        '- **`## VERIFICATION PASSED`:** Display confirmation, proceed to step 13.',
        '- **`## VERIFICATION PASSED`:** Display confirmation, proceed to step 14.',
        1
    )
    # "proceed to step 12" — Revision Loop is now step 13
    content = content.replace(
        '- **`## ISSUES FOUND`:** Display issues, check iteration count, proceed to step 12.',
        '- **`## ISSUES FOUND`:** Display issues, check iteration count, proceed to step 13.',
        1
    )
    # Revision Loop (now step 13) references: "spawn checker again (step 10)" -> "(step 11)"
    content = content.replace(
        'spawn checker again (step 10), increment iteration_count.',
        'spawn checker again (step 11), increment iteration_count.',
        1
    )

    # -------------------------------------------------------------------------
    # Write patched content
    # -------------------------------------------------------------------------
    with open(target, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'  [OK] Patched: {target}')
    print(f'       Removed: ## 13. Pre-Plan Agent Gate (old post-planner position + ADVY-01 deferred note)')
    print(f'       Inserted: ## 8. Pre-Plan Agent Gate (before planner, fail-open, collects AGENT_NOTES)')
    print(f'       Renamed:  ## 8. Spawn gsd-planner Agent -> ## 9. Spawn gsd-planner Agent')
    print(f'       Renumbered: old steps 9-12 -> new steps 10-13')
    print(f'       Added: {{AGENT_NOTES}} interpolation in planner Task() prompt block')
    print(f'       Updated: internal step cross-references')


if __name__ == '__main__':
    main()
