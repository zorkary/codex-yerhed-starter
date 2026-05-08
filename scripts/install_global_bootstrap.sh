#!/bin/sh
set -eu

REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
AGENTS="${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
SNIPPET="$REPO/config/global-bootstrap.md"
BEGIN="<!-- BEGIN YERHED GLOBAL BOOTSTRAP -->"
END="<!-- END YERHED GLOBAL BOOTSTRAP -->"
[ -f "$SNIPPET" ] || { echo "missing bootstrap snippet: $SNIPPET" >&2; exit 1; }
mkdir -p "$(dirname "$AGENTS")"
touch "$AGENTS"
python3 - "$AGENTS" "$SNIPPET" "$BEGIN" "$END" <<'PY'
from __future__ import annotations
import sys
from pathlib import Path

agents = Path(sys.argv[1])
snippet = Path(sys.argv[2])
begin = sys.argv[3]
end = sys.argv[4]
block = begin + "\n" + snippet.read_text(encoding="utf-8").strip() + "\n" + end
text = agents.read_text(encoding="utf-8") if agents.exists() else ""
lines = text.splitlines()
out = []
skip = False
for line in lines:
    if line.strip() == begin:
        skip = True
        continue
    if skip and line.strip() == end:
        skip = False
        continue
    if not skip:
        out.append(line)
new_text = "\n".join(out).rstrip()
if new_text:
    new_text += "\n\n"
new_text += block + "\n"
agents.write_text(new_text, encoding="utf-8")
PY

echo "Installed Yerhed global bootstrap in $AGENTS"
