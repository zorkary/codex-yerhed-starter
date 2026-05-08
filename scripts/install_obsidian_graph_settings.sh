#!/bin/sh
set -eu

QUIET_FILTER='-(file:README OR file:_template OR file:schema OR file:log OR file:open-loops OR path:sources OR path:archive)'
BRAIN_ROOT="${YERHED_BRAIN_ROOT:-${BRAIN_ROOT:-$HOME/Personal/Yerhed/brain}}"
FORCE=0
DRY_RUN=0
PRINT_FILTER=0

usage() {
  cat <<USAGE
Usage: $0 [--brain-root PATH] [--force] [--dry-run] [--print-filter]

Installs local-only Obsidian Global Graph settings for a Yerhed brain root.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --brain-root)
      [ "$#" -ge 2 ] || { echo "missing value for --brain-root" >&2; exit 2; }
      BRAIN_ROOT="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --print-filter)
      PRINT_FILTER=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ "$PRINT_FILTER" -eq 1 ]; then
  printf '%s\n' "$QUIET_FILTER"
  [ "$DRY_RUN" -eq 1 ] || exit 0
fi

if [ "$FORCE" -ne 1 ]; then
  for required in RESOLVER.md schema.md projects people concepts; do
    if [ ! -e "$BRAIN_ROOT/$required" ]; then
      echo "refusing: $BRAIN_ROOT does not look like a Yerhed brain root; missing $required" >&2
      echo "use --force only for a deliberate test or fresh local setup" >&2
      exit 1
    fi
  done
fi

GRAPH_DIR="$BRAIN_ROOT/.obsidian"
GRAPH_FILE="$GRAPH_DIR/graph.json"

if [ "$DRY_RUN" -eq 1 ]; then
  printf 'Would update: %s\n' "$GRAPH_FILE"
  printf 'Search filter: %s\n' "$QUIET_FILTER"
  exit 0
fi

mkdir -p "$GRAPH_DIR"
export GRAPH_FILE QUIET_FILTER
python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["GRAPH_FILE"])
quiet_filter = os.environ["QUIET_FILTER"]

if path.exists():
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid existing graph.json: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("invalid existing graph.json: expected object")
else:
    data = {}

data["search"] = quiet_filter
data["showAttachments"] = False
data["showTags"] = False
data["showOrphans"] = False

path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
json.loads(path.read_text(encoding="utf-8"))
print(f"Installed Obsidian graph settings: {path}")
print(f"Search filter: {quiet_filter}")
PY
