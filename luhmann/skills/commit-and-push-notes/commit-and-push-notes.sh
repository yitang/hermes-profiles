#!/usr/bin/env bash
# commit-and-push-notes.sh — commit and push all note repos
#
# Walks ~/matrix/*/meta-*/notes/ directories, commits any changes
# found within each notes/ folder, pushes, and reports a summary.
#
# Usage:
#   ./commit-and-push-notes.sh                    # commit with auto date message
#   ./commit-and-push-notes.sh "my commit msg"    # custom commit message

set -euo pipefail

# $HOME is overridden in Hermes profiles — use the real user home
REAL_HOME="/home/tangyi"
MATRIX_ROOT="$REAL_HOME/matrix"
TOTAL_FILES=0
TOTAL_REPOS=0
CHANGED_REPOS=0

# Use custom commit message if provided, else auto date
COMMIT_MSG="${1:-notes: auto-commit $(date +%Y-%m-%d)}"

# Walk all meta-* dirs one level deep
for dir in "$MATRIX_ROOT"/*/meta-*; do
  # Guard: only process if it's actually a directory
  [ -d "$dir" ] || continue

  REPO_NAME="$(basename "$dir")"
  NOTES_DIR="$dir/notes"
  [ -d "$NOTES_DIR" ] || continue  # skip if no notes/ folder

  cd "$dir"

  # Check for any tracked or untracked changes inside notes/
  CHANGES="$(git status --porcelain -- notes/ 2>/dev/null || true)"
  if [ -z "$CHANGES" ]; then
    echo "  ✓ $REPO_NAME — clean, nothing to commit"
    TOTAL_REPOS=$((TOTAL_REPOS + 1))
    continue
  fi

  FILES_CHANGED="$(echo "$CHANGES" | wc -l)"
  TOTAL_FILES=$((TOTAL_FILES + FILES_CHANGED))
  CHANGED_REPOS=$((CHANGED_REPOS + 1))

  echo "  → $REPO_NAME — $FILES_CHANGED file(s) changed"

  git add notes/
  git commit -m "$COMMIT_MSG"

  # Push (handles detached HEAD, new branches, etc.)
  CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
  if [ "$CURRENT_BRANCH" != "" ] && [ "$CURRENT_BRANCH" != "HEAD" ]; then
    git push origin "$CURRENT_BRANCH" 2>/dev/null || echo "     ⚠ push failed (remote may not be configured)"
  else
    echo "     ⚡ detached HEAD — skipping push"
  fi

  TOTAL_REPOS=$((TOTAL_REPOS + 1))
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Summary: $CHANGED_REPOS / $TOTAL_REPOS repos had changes"
echo "  Total files/notes changed: $TOTAL_FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
