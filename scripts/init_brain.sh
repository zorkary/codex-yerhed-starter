#!/bin/sh
set -eu

REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
BRAIN_ROOT="${YERHED_BRAIN_ROOT:-$HOME/Personal/Yerhed/brain}"
TEMPLATE_ROOT="$REPO/templates/brain"

[ -d "$TEMPLATE_ROOT" ] || { echo "missing template root: $TEMPLATE_ROOT" >&2; exit 1; }
mkdir -p "$BRAIN_ROOT"
for dir in archive concepts ideas inbox people projects places organizations companions sources; do
  mkdir -p "$BRAIN_ROOT/$dir"
done

# Copy starter templates without overwriting local private notes.
find "$TEMPLATE_ROOT" -type f | while IFS= read -r src; do
  rel=${src#"$TEMPLATE_ROOT"/}
  dest="$BRAIN_ROOT/$rel"
  mkdir -p "$(dirname "$dest")"
  if [ ! -f "$dest" ]; then
    cp "$src" "$dest"
  fi
done

if command -v git >/dev/null 2>&1 && [ ! -d "$BRAIN_ROOT/.git" ]; then
  git -C "$BRAIN_ROOT" init >/dev/null
  git -C "$BRAIN_ROOT" add .
  git -C "$BRAIN_ROOT" commit -m "Initialize Yerhed brain" >/dev/null 2>&1 || true
fi

echo "Brain root initialized: $BRAIN_ROOT"
