#!/bin/sh
set -eu

CONFIG="${CODEX_HOME:-$HOME/.codex}/config.toml"
BEGIN="# BEGIN YERHED HOOK"
END="# END YERHED HOOK"
[ -f "$CONFIG" ] || { echo "No Codex config found: $CONFIG"; exit 0; }
python3 - "$CONFIG" "$BEGIN" "$END" <<'PY'
from __future__ import annotations
import sys
from pathlib import Path

config = Path(sys.argv[1])
begin = sys.argv[2]
end = sys.argv[3]
text = config.read_text(encoding="utf-8")
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
config.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
PY

echo "Removed Yerhed hook from $CONFIG"
