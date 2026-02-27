---
phase: 01-extension-scaffold-gsd-integration
plan: 04
source: D:/GSDteams/.planning/phases/01-extension-scaffold-gsd-integration/01-04-SUMMARY.md
generated: 2026-02-26T04:07:05Z
---

# Artifact: Phase 01 Plan 04 - install.sh Installer

**Phase:** 01-extension-scaffold-gsd-integration
**Plan:** 04
**Generated:** 2026-02-26T04:07:05Z

## Files Changed

| Path | Action | Purpose |
|------|--------|---------|
| `install.sh` | Created | POSIX bash installer; 9-section script orchestrating GSD extension installation |
| `.planning/TEAM.md` | Created | Copied from templates/TEAM.md with 3 starter roles: Security Auditor, Rules Lawyer, Performance Analyst |
| `.planning/config.json` | Modified | `workflow.review_team: false` ensured present |
| `.planning/ROADMAP.md` | Modified | Phase 1 marked complete (4/4 plans), status updated to "Complete" |

## Behavior Implemented

- `install.sh` detects GSD global install at `$HOME/.claude/` before falling back to `./.claude/`
- GSD location stored in `$GSD_DIR` variable pointing to the `.claude/` parent directory
- Extension files deployed to `$GSD_DIR/get-shit-done-review-team/`
- `patch-execute-plan.py` and `patch-settings.py` invoked by the installer
- `review_team_gate` inserted at line 412 before `offer_next` at line 434 in `execute-plan.md`
- All 4 `settings.md` touch points patched
- `.planning/TEAM.md` copied from `templates/TEAM.md`; existence guard (`[ -f path ]`) prevents overwrite on re-run
- `workflow.review_team: false` ensured present in `.planning/config.json`
- Installer outputs `[OK]`, `[SKIP]`, `[INFO]`, `[WARN]` prefixes per section
- Second run (idempotency): all patches show `[SKIP]`, TEAM.md shows `[SKIP]`, installer exits 0
- `templates/*.md` copy uses glob pattern, not individual file names
- `config.json` update uses `jq` when present (`HAS_JQ=1`), otherwise falls back to an inline Python3 heredoc using the `json` stdlib module
- `HAS_JQ` flag (0/1) set by `command -v jq` at install time
- `set -e` used for fail-fast error handling

## Stack Changes

| Dependency | Version | Purpose |
|------------|---------|---------|
| bash | POSIX | Installer script language |

## API Contracts

None

## Configuration Changes

| Config | Value | Location |
|--------|-------|----------|
| `workflow.review_team` | `false` | `.planning/config.json` |

## Key Decisions

- `jq` is an optional dependency; Python3 json module used as fallback when `jq` is not available
- `$GSD_DIR` points to the `.claude/` parent directory, not the workflow subdirectory
- `EXT_INSTALL_DIR` = `$GSD_DIR/get-shit-done-review-team`
- `templates/*.md` copy uses glob, not individual file names
- `config.json` Python3 fallback uses `json.dump()` to preserve key ordering and add trailing newline
- Existence guard (`[ -f path ]`) on TEAM.md copy prevents overwrite on re-run
- Idempotency achieved at two levels: bash guards (TEAM.md) and Python script idempotency (patches)
- `install.sh` section pattern: comment header + echo status line + action + `[OK]`/`[SKIP]` report

## Test Coverage

- `bash -n install.sh` — syntax check exits 0
- `bash install.sh` — first run exits 0, completion banner printed
- `review_team_gate` present at line 412 in `execute-plan.md`, before `offer_next` at line 434
- All 4 `settings.md` touch points applied with zero WARN messages
- `config.json workflow.review_team` = `false` confirmed present
- `.planning/TEAM.md` file exists with 3 roles
- Second run (idempotency): all patches `[SKIP]`, TEAM.md `[SKIP]`, exits 0

## Error Handling

- `set -e` causes installer to exit immediately on any command failure
- `HAS_JQ` flag: if `jq` absent, Python3 heredoc executes identical JSON manipulation
- `[ -f path ]` guard on TEAM.md copy skips the copy operation if file already exists; outputs `[SKIP]`
- Patch scripts report `[SKIP]` when already applied (idempotency)
