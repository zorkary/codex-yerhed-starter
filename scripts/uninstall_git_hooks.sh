#!/bin/sh
set -eu

REPO="$(git rev-parse --show-toplevel 2>/dev/null || { CDPATH= cd -- "$(dirname -- "$0")/.." && pwd; })"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      REPO="$(CDPATH= cd -- "$2" && pwd)"
      shift 2
      ;;
    *)
      echo "usage: $0 [--repo PATH]" >&2
      exit 2
      ;;
  esac
done

HOOK_DIR="$REPO/.git/hooks"
MARKER="Yerhed starter privacy hook"

restore_hook() {
  hook="$HOOK_DIR/$1"
  if [ ! -f "$hook" ]; then
    echo "No $1 hook installed at $hook"
    return 0
  fi
  if ! grep -q "$MARKER" "$hook" 2>/dev/null; then
    echo "refusing to remove non-Yerhed $1 hook: $hook" >&2
    return 1
  fi
  backup="$(sed -n 's/^EXISTING_HOOK="\(.*\)"$/\1/p' "$hook" | head -n 1)"
  rm -f "$hook"
  if [ -n "$backup" ] && [ -f "$backup" ]; then
    mv "$backup" "$hook"
    chmod +x "$hook"
    echo "Restored previous $1 hook from $backup"
  else
    echo "Removed Yerhed starter $1 hook"
  fi
}

restore_hook pre-commit
restore_hook pre-push
