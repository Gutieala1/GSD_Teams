#!/usr/bin/env bash
# test-restore.sh — Undo test-install.sh completely
#
# Restores every file that was backed up and deletes every file
# that was added. Leaves your GSD install exactly as it was before.
#
# Usage:
#   bash test-restore.sh

set -euo pipefail

EXT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$EXT_DIR/.test-backup"
GSD_DIR="$HOME/.claude"

# ── same lists as test-install.sh ────────────────────────────────────────────
PATCHED_FILES=(
  "$GSD_DIR/get-shit-done/workflows/new-project.md"
)

# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║      GSD Agent Studio v2.0 — Restore                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

if [ ! -d "$BACKUP_DIR" ]; then
  echo "ERROR: No backup found at $BACKUP_DIR"
  echo "       Run test-install.sh first, or nothing to restore."
  exit 1
fi

echo "Restoring patched files..."

# 1. Restore patched files from backup
for f in "${PATCHED_FILES[@]}"; do
  fname="$(basename "$f")"
  bak="$BACKUP_DIR/$fname.bak"
  if [ -f "$bak" ]; then
    cp "$bak" "$f"
    echo "  [RESTORED] $fname"
  else
    echo "  [SKIP] No backup for $fname (was not present before install)"
  fi
done

echo ""
echo "Removing added files..."

# 2. Remove files that were added (tracked in manifest)
ADDED_MANIFEST="$BACKUP_DIR/added-files.txt"
if [ -f "$ADDED_MANIFEST" ]; then
  while IFS= read -r f; do
    if [ -f "$f" ]; then
      rm "$f"
      echo "  [REMOVED] $f"
    else
      echo "  [SKIP] Already gone: $f"
    fi
  done < "$ADDED_MANIFEST"
else
  echo "  [SKIP] No added-files manifest found"
fi

echo ""
echo "Cleaning up backup..."
rm -rf "$BACKUP_DIR"
echo "  [OK] $BACKUP_DIR removed"

echo ""
echo "✅ Restore complete. GSD is back to its pre-test state."
echo ""
