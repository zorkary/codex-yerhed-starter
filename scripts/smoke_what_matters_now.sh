#!/bin/sh
set -eu
REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
BRAIN="$TMPDIR/brain"
mkdir -p "$BRAIN/archive" "$BRAIN/concepts" "$BRAIN/ideas" "$BRAIN/inbox" "$BRAIN/people" "$BRAIN/projects" "$BRAIN/sources"
printf '# Open Loops\n\n## Current\n\n- Review the starter install path.\n' > "$BRAIN/projects/open-loops.md"
printf '# Yerhed\n\nStarter project page.\n' > "$BRAIN/projects/yerhed.md"
printf '# Brain Log\n\n## Install Smoke\n\nValidated starter state.\n' > "$BRAIN/log.md"
YERHED_REPO="$REPO" YERHED_BRAIN_ROOT="$BRAIN" PYTHONPATH="$REPO" python3 - <<'PY'
from yerhed_mcp.tools import what_matters_now
result = what_matters_now()
assert result["ok"]
assert "Review the starter install path" in result["summary"]
print(result["summary"])
PY
