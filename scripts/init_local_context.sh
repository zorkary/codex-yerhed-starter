#!/bin/sh
set -eu

REPO="$(git rev-parse --show-toplevel 2>/dev/null || { CDPATH= cd -- "$(dirname -- "$0")/.." && pwd; })"

for base in USER SOUL MEMORY; do
  target="$REPO/$base.md"
  example="$REPO/$base.example.md"
  if [ -f "$target" ]; then
    echo "exists: $target"
    continue
  fi
  if [ ! -f "$example" ]; then
    echo "missing example: $example" >&2
    exit 1
  fi
  cp "$example" "$target"
  echo "created local-only: $target"
done

echo "Local Yerhed context files are ignored by git."
