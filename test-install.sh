#!/usr/bin/env bash
# test-install.sh — Safe test installer for GSD Agent Studio v2.0
#
# Creates a snapshot of every file that install.sh will touch,
# runs install.sh, then prints the exact command to restore.
#
# Usage:
#   bash test-install.sh          # backup + install
#   bash test-restore.sh          # undo everything (generated below)

set -euo pipefail

EXT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$EXT_DIR/.test-backup"
GSD_DIR="$HOME/.claude"

# ── files that will be PATCHED (modified in place) ───────────────────────────
PATCHED_FILES=(
  "$GSD_DIR/get-shit-done/workflows/new-project.md"
)

# ── files that will be ADDED (new, not present before) ───────────────────────
ADDED_FILES=(
  "$GSD_DIR/get-shit-done-review-team/workflows/new-agent.md"
  "$GSD_DIR/commands/gsd/new-agent.md"
)

# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║      GSD Agent Studio v2.0 — Test Installer         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# 1. Create backup directory
rm -rf "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

echo "Creating snapshot..."

# 2. Backup files that will be patched
for f in "${PATCHED_FILES[@]}"; do
  if [ -f "$f" ]; then
    fname="$(basename "$f")"
    cp "$f" "$BACKUP_DIR/$fname.bak"
    echo "  [BAK] $fname"
  else
    echo "  [WARN] Not found, skipping backup: $f"
  fi
done

# 3. Record which ADDED files did NOT exist before (so restore knows to delete them)
ADDED_MANIFEST="$BACKUP_DIR/added-files.txt"
touch "$ADDED_MANIFEST"
for f in "${ADDED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "$f" >> "$ADDED_MANIFEST"
    echo "  [NEW] Will track: $f"
  else
    echo "  [SKIP-track] Already exists: $f"
  fi
done

echo ""
echo "Snapshot saved to: $BACKUP_DIR"
echo ""

# 4. Run the real install
echo "Running install.sh..."
echo "────────────────────────────────────────────────────────"
bash "$EXT_DIR/install.sh"
echo "────────────────────────────────────────────────────────"
echo ""

echo "✅ Install complete."
echo ""
echo "Test the features now:"
echo "  /gsd:new-agent     — guided agent creation"
echo "  /gsd:team          — view agent roster"
echo "  /gsd:new-project   — should offer agent team at the end"
echo ""
echo "When you're done testing, run:"
echo ""
echo "  bash $EXT_DIR/test-restore.sh"
echo ""
echo "That will put everything back exactly as it was."
