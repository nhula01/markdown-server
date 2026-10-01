#!/bin/zsh
set -eu
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
# This Mac uses Application Support because ~/.config is owned by root.
if [[ -z "${GH_CONFIG_DIR:-}" && -d "$HOME/Library/Application Support/gh" ]]; then
  export GH_CONFIG_DIR="$HOME/Library/Application Support/gh"
fi
REPO="${0:A:h:h}"
cd "$REPO"
# Prevent overlapping scheduled/manual runs.
LOCK="$REPO/.remarkable-sync.lock"
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK"' EXIT
# Export PDFs from the official reMarkable desktop app into pdfs/Obsidian.
# Publish those files unchanged; do not run third-party PDF conversion.
# Import only questions and trail links from the editable Obsidian source.
LEADS_SOURCE="${LEADS_SOURCE:-$HOME/Documents/MyBrain/Follow a thread.md}"
if [[ -f "$LEADS_SOURCE" ]]; then
  python3 scripts/update-leads.py "$LEADS_SOURCE"
fi
# Commit only the authorized exports and curated leads; preserve other staged work.
git add -- pdfs site/leads.md
if ! git diff --cached --quiet -- pdfs site/leads.md; then
  git commit --only -m "Update reMarkable notes $(date +%F)" -- pdfs site/leads.md
fi
# Retry a previously failed push even when this sync made no changes.
git push origin HEAD
