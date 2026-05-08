#!/bin/sh
set -eu

BRAIN_ROOT="${YERHED_BRAIN_ROOT:-$HOME/Personal/Yerhed/brain}"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --brain-root)
      BRAIN_ROOT="$2"
      shift 2
      ;;
    *)
      echo "usage: $0 [--brain-root PATH]" >&2
      exit 2
      ;;
  esac
done

HOOK="$BRAIN_ROOT/.git/hooks/pre-push"
MARKER="Yerhed brain root local-only guard"
if [ ! -f "$HOOK" ]; then
  echo "No brain-root push guard installed at $HOOK"
  exit 0
fi
if ! grep -q "$MARKER" "$HOOK" 2>/dev/null; then
  echo "refusing to remove non-Yerhed brain pre-push hook: $HOOK" >&2
  exit 1
fi
backup="$(sed -n 's/^EXISTING_HOOK="\(.*\)"$/\1/p' "$HOOK" | head -n 1)"
rm -f "$HOOK"
if [ -n "$backup" ] && [ -f "$backup" ]; then
  mv "$backup" "$HOOK"
  chmod +x "$HOOK"
  echo "Restored previous brain pre-push hook from $backup"
else
  echo "Removed brain-root push guard"
fi
