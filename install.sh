#!/usr/bin/env bash
set -e

# ==============================================================================
# GSD Review Team — install.sh
# Orchestrates the complete extension installation:
#   - GSD location detection
#   - Extension file copies
#   - Python patch invocations (execute-plan.md, settings.md)
#   - config.json update
#   - TEAM.md copy with existence guard
# Run from the root of your GSD project: bash install.sh
# ==============================================================================

echo ""
echo "GSD Review Team — Installer"
echo "============================"
echo ""

# ------------------------------------------------------------------------------
# Section 1: Dependency checks
# ------------------------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required but not found."
  echo "       Install Python 3 and re-run."
  exit 1
fi

# jq is optional — Python3 fallback is used if jq is absent
HAS_JQ=0
if command -v jq >/dev/null 2>&1; then
  HAS_JQ=1
  echo "  [OK] python3 found: $(python3 --version)"
  echo "  [OK] jq found: $(jq --version)"
else
  echo "  [OK] python3 found: $(python3 --version)"
  echo "  [INFO] jq not found — will use python3 for config.json update"
fi

# ------------------------------------------------------------------------------
# Section 2: GSD location detection
# ------------------------------------------------------------------------------
GSD_DIR=""

if [ -d "$HOME/.claude/get-shit-done" ]; then
  GSD_DIR="$HOME/.claude"
  echo "  [OK] GSD found (global): $GSD_DIR/get-shit-done"
elif [ -d "./.claude/get-shit-done" ]; then
  GSD_DIR="$(pwd)/.claude"
  echo "  [OK] GSD found (local): $GSD_DIR/get-shit-done"
else
  echo ""
  echo "ERROR: GSD not found. Install GSD first."
  echo "       Expected locations:"
  echo "         - $HOME/.claude/get-shit-done  (global)"
  echo "         - ./.claude/get-shit-done       (local)"
  exit 1
fi

# ------------------------------------------------------------------------------
# Section 3: Project root detection
# ------------------------------------------------------------------------------
if [ ! -d ".planning" ]; then
  echo ""
  echo "ERROR: No .planning/ directory found."
  echo "       Run install.sh from your GSD project root."
  echo "       (The directory containing .planning/ should be your working directory.)"
  exit 1
fi

echo "  [OK] .planning/ directory found"

# ------------------------------------------------------------------------------
# Section 4: Extension directory setup
# ------------------------------------------------------------------------------
EXT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(pwd)"
EXT_INSTALL_DIR="$GSD_DIR/get-shit-done-review-team"

echo ""
echo "Setting up extension directories..."
mkdir -p "$EXT_INSTALL_DIR/agents"
mkdir -p "$EXT_INSTALL_DIR/workflows"
mkdir -p "$EXT_INSTALL_DIR/templates"
echo "  [OK] $EXT_INSTALL_DIR/agents"
echo "  [OK] $EXT_INSTALL_DIR/workflows"
echo "  [OK] $EXT_INSTALL_DIR/templates"

# ------------------------------------------------------------------------------
# Section 5: Copy extension files
# ------------------------------------------------------------------------------
echo ""
echo "Copying extension files..."

# Copy agents/*.md if any exist
if ls "$EXT_DIR/agents/"*.md >/dev/null 2>&1; then
  cp "$EXT_DIR/agents/"*.md "$EXT_INSTALL_DIR/agents/"
  echo "  [OK] agents/*.md copied"
else
  echo "  [SKIP] No agents/*.md files yet (Phase 2)"
fi

# Copy workflows/*.md if any exist
if ls "$EXT_DIR/workflows/"*.md >/dev/null 2>&1; then
  cp "$EXT_DIR/workflows/"*.md "$EXT_INSTALL_DIR/workflows/"
  echo "  [OK] workflows/*.md copied"
else
  echo "  [SKIP] No workflows/*.md files yet (Phase 2)"
fi

# Copy templates/*.md
if ls "$EXT_DIR/templates/"*.md >/dev/null 2>&1; then
  cp "$EXT_DIR/templates/"*.md "$EXT_INSTALL_DIR/templates/"
  echo "  [OK] templates/*.md copied"
else
  echo "  [SKIP] No templates/*.md files found"
fi

# ------------------------------------------------------------------------------
# Section 6: Apply patches
# ------------------------------------------------------------------------------
echo ""
echo "Applying patches..."

EXECUTE_PLAN="$GSD_DIR/get-shit-done/workflows/execute-plan.md"
SETTINGS="$GSD_DIR/get-shit-done/workflows/settings.md"

if [ ! -f "$EXECUTE_PLAN" ]; then
  echo "  ERROR: $EXECUTE_PLAN not found"
  exit 1
fi

if [ ! -f "$SETTINGS" ]; then
  echo "  ERROR: $SETTINGS not found"
  exit 1
fi

python3 "$EXT_DIR/scripts/patch-execute-plan.py" "$EXECUTE_PLAN"
python3 "$EXT_DIR/scripts/patch-settings.py" "$SETTINGS"

# ------------------------------------------------------------------------------
# Section 7: config.json update
# ------------------------------------------------------------------------------
echo ""
echo "Updating config.json..."

CONFIG="$PROJECT_DIR/.planning/config.json"
if [ -f "$CONFIG" ]; then
  if [ "$HAS_JQ" -eq 1 ]; then
    tmp=$(mktemp)
    jq 'if .workflow.review_team == null then .workflow.review_team = false else . end' "$CONFIG" > "$tmp" && mv "$tmp" "$CONFIG"
  else
    # Python3 fallback when jq is not available
    python3 - "$CONFIG" <<'PYEOF'
import sys, json

path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

workflow = data.setdefault('workflow', {})
if 'review_team' not in workflow:
    workflow['review_team'] = False

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
PYEOF
  fi
  echo "  [OK] config.json: workflow.review_team ensured"
else
  echo "  [SKIP] No .planning/config.json found (run /gsd:new-project first)"
fi

# ------------------------------------------------------------------------------
# Section 8: TEAM.md copy with existence guard
# ------------------------------------------------------------------------------
echo ""
echo "Checking .planning/TEAM.md..."

if [ -f "$PROJECT_DIR/.planning/TEAM.md" ]; then
  echo "  [SKIP] .planning/TEAM.md already exists — not overwriting"
else
  cp "$EXT_DIR/templates/TEAM.md" "$PROJECT_DIR/.planning/TEAM.md"
  echo "  [OK] .planning/TEAM.md created from starter template"
fi

# ------------------------------------------------------------------------------
# Section 9: Completion message
# ------------------------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " GSD Review Team — Installed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  GSD location:    $GSD_DIR"
echo "  Extension files: $EXT_INSTALL_DIR"
echo ""
echo "  Patches applied:"
echo "    - execute-plan.md (review_team_gate step)"
echo "    - settings.md (Review Team toggle)"
echo ""
echo "  IMPORTANT: After running /gsd:update, you must run"
echo "  /gsd:reapply-patches to restore the patches above."
echo ""
echo "  Next steps:"
echo "    1. Run /gsd:settings to enable Review Team"
echo "    2. Edit .planning/TEAM.md to customize your reviewer roles"
echo "       (or run /gsd:new-reviewer for a guided conversation)"
echo "    3. Run /gsd:execute-phase <phase> to see the pipeline in action"
echo ""
