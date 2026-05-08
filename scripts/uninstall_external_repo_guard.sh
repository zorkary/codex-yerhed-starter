#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <repo_path>" >&2
  exit 2
fi

TARGET_REPO="$(CDPATH= cd -- "$1" && pwd)"
HOOK="$TARGET_REPO/.git/hooks/pre-push"
MARKER="Yerhed external memory leak guard"
if [ ! -f "$HOOK" ]; then
  echo "No Yerhed external memory leak guard installed at $HOOK"
  exit 0
fi
if ! grep -q "$MARKER" "$HOOK" 2>/dev/null; then
  echo "refusing to remove non-Yerhed pre-push hook: $HOOK" >&2
  exit 1
fi
backup="$(sed -n 's/^EXISTING_HOOK="\(.*\)"$/\1/p' "$HOOK" | head -n 1)"
rm -f "$HOOK"
if [ -n "$backup" ] && [ -f "$backup" ]; then
  mv "$backup" "$HOOK"
  chmod +x "$HOOK"
  echo "Restored previous pre-push hook from $backup"
else
  echo "Removed Yerhed external memory leak guard"
fi
