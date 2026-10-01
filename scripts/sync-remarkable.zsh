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
SYNC="$(command -v reMarkableSync || command -v RemarkableSync)"
"$SYNC" --output-dir "$REPO/pdfs"
# Commit only exports; preserve any unrelated staged work.
git add -- pdfs
if ! git diff --cached --quiet -- pdfs; then
  git commit --only -m "Update reMarkable notes $(date +%F)" -- pdfs
fi
# Retry a previously failed push even when this sync made no changes.
git push origin HEAD
