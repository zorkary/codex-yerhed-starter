#!/bin/sh
set -eu
QUERY="${1:-}"
if [ -z "$QUERY" ]; then echo "usage: scripts/brain_search.sh <query>" >&2; exit 2; fi
BRAIN_ROOT="${YERHED_BRAIN_ROOT:-$HOME/Personal/Yerhed/brain}"
rg -n --hidden --glob '!.git/**' --glob '!*.pyc' -- "$QUERY" "$BRAIN_ROOT"
