# GSD Review Team

A GSD extension that runs a parallel review pipeline after each plan execution. Reviewer roles are defined in `.planning/TEAM.md`. After execution, findings are routed to `REVIEW-REPORT.md` or halt the pipeline for critical issues.

## Requirements

- [GSD](https://github.com/anthropics/get-shit-done) installed (tested with GSD 1.19.x)
- Python 3 (for install patches)
- A GSD project with `.planning/` directory

## Installation

From your GSD project root:

```bash
bash /path/to/gsd-review-team/install.sh
```

The installer:
1. Detects your GSD installation (`~/.claude/get-shit-done` or `./.claude/get-shit-done`)
2. Checks GSD version compatibility (warns if outside tested range 1.19.x)
3. Copies extension files to `~/.claude/get-shit-done-review-team/`
4. Copies `/gsd:new-reviewer` command to `~/.claude/commands/gsd/`
5. Patches `execute-plan.md` to add the `review_team_gate` step
6. Patches `settings.md` to add the Review Team toggle
7. Creates `.planning/TEAM.md` from the starter template (if it does not already exist)

## Post-`/gsd:update` Procedure

`/gsd:update` replaces GSD core files, which removes the patches this extension applies to `execute-plan.md` and `settings.md`. It also wipes `~/.claude/commands/gsd/`, removing `/gsd:new-reviewer`.

**After every `/gsd:update`, re-run the installer:**

```bash
bash /path/to/gsd-review-team/install.sh
```

This restores:
- The `review_team_gate` step in `execute-plan.md`
- The Review Team toggle in `settings.md`
- The `/gsd:new-reviewer` command

Note: The extension's own files in `~/.claude/get-shit-done-review-team/` are NOT wiped by `/gsd:update` — only the GSD core directories are affected. Your `.planning/TEAM.md` is also preserved (it lives in your project, not in GSD directories).

## Enabling the Review Team

After installation, enable the review pipeline in Claude:

```
/gsd:settings
```

Toggle "Review Team" to enabled. This writes `workflow.review_team: true` to `.planning/config.json`.

Once enabled, every `/gsd:execute-phase` plan run will trigger the review pipeline after the plan's executor completes.

## TEAM.md Format

`.planning/TEAM.md` defines your reviewer roles. The file uses YAML frontmatter and Markdown role sections.

### Role Format

Each role requires:

````markdown
## Role: Display Name

```yaml
name: slug-with-dashes
focus: One sentence domain description
```

**What this role reviews:**
- Review criterion 1
- Review criterion 2
- Review criterion 3

**Severity thresholds:**
- `critical`: Example that warrants stopping a deploy
- `major`: Example requiring fix before next plan
- `minor`: Example worth tracking but shippable

**Routing hints:**
- Critical findings: `block_and_escalate`
- Major findings: `send_for_rework`
- Minor findings: `log_and_continue`
````

### Validation Rules

The pipeline validates TEAM.md before running. A role is valid if it has ALL THREE:
1. A `## Role:` section header
2. A YAML fenced block with a `name:` field
3. At least one item under `**What this role reviews:**`

If TEAM.md has zero valid roles, the pipeline halts before sanitization.

### Adding Roles

**Guided conversation:**
```
/gsd:new-reviewer
```

**Manual:** Copy a role section from the starter template and customize it.

### Starter Roles

The installer ships three ready-to-use roles:

| Role | Slug | Focus |
|------|------|-------|
| Security Auditor | `security-auditor` | Security vulnerabilities and unsafe patterns |
| Performance Analyst | `performance-analyst` | Performance implications of new code |
| Rules Lawyer | `rules-lawyer` | Consistency with requirements and conventions |

## First-Run Walkthrough

1. **Enable Review Team** — run `/gsd:settings`, toggle "Review Team" on
2. **Verify TEAM.md** — open `.planning/TEAM.md`, confirm at least one role exists
3. **Run a plan** — `/gsd:execute-phase <your-phase>`
4. **Watch the pipeline** — after the plan executes, the review pipeline fires automatically:
   - Sanitizer produces `{phase-dir}/{phase}-{plan}-ARTIFACT.md`
   - Each reviewer role runs in parallel
   - Synthesizer routes findings
5. **Check findings** — open `{phase-dir}/REVIEW-REPORT.md` to see logged findings

### Routing Outcomes

| Severity | Default Routing | What Happens |
|----------|----------------|--------------|
| `critical` | `block_and_escalate` | Pipeline halts, user must decide |
| `major` | `send_for_rework` | Execution paused, rework requested |
| `minor` | `log_and_continue` | Finding logged to REVIEW-REPORT.md, execution continues |

## Troubleshooting

**"Review Team: skipped (no TEAM.md)"** — `.planning/TEAM.md` does not exist. Run `bash install.sh` or create the file manually.

**"Review Team: skipped (disabled)"** — Toggle is off. Run `/gsd:settings` and enable Review Team.

**"REVIEW PIPELINE HALTED — zero valid roles"** — TEAM.md exists but no role passes validation. Check that each role has `## Role:`, a YAML block with `name:`, and a `**What this role reviews:**` list.

**`/gsd:new-reviewer` not found after `/gsd:update`** — Re-run `bash install.sh` to restore the command.
