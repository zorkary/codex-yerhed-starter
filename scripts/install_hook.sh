#!/bin/sh
set -eu

REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
CONFIG="${CODEX_HOME:-$HOME/.codex}/config.toml"
PYTHON_BIN="${YERHED_PYTHON:-python3}"
HOOK_CMD="$PYTHON_BIN $REPO/yerhed_mcp/hook.py"
BEGIN="# BEGIN YERHED HOOK"
END="# END YERHED HOOK"
BLOCK=$(cat <<BLOCK_EOF
$BEGIN
[[hooks.UserPromptSubmit]]
matcher = ""

[[hooks.UserPromptSubmit.hooks]]
type = "command"
command = "$HOOK_CMD"
timeoutSec = 2
async = false
statusMessage = "Yerhed"
$END
BLOCK_EOF
)

mkdir -p "$(dirname "$CONFIG")"
touch "$CONFIG"
python3 - "$CONFIG" "$BEGIN" "$END" "$BLOCK" <<'PY'
from __future__ import annotations
import sys
from pathlib import Path

config = Path(sys.argv[1])
begin = sys.argv[2]
end = sys.argv[3]
block = sys.argv[4]
text = config.read_text(encoding="utf-8") if config.exists() else ""
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
new_text += block.rstrip() + "\n"
config.write_text(new_text, encoding="utf-8")
PY

echo "Installed Yerhed UserPromptSubmit hook in $CONFIG"
