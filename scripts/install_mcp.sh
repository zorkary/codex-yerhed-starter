#!/bin/sh
set -eu

REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
PYTHON_BIN="${YERHED_PYTHON:-$REPO/.venv/bin/python}"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN="${YERHED_PYTHON:-python3}"
SERVER="$REPO/mcp/server.py"
[ -f "$SERVER" ] || { echo "missing MCP server: $SERVER" >&2; exit 1; }
command -v codex >/dev/null 2>&1 || { echo "codex command not found; cannot register MCP" >&2; exit 1; }
if codex mcp list 2>/dev/null | awk '{print $1}' | grep -qx 'yerhed'; then
  codex mcp remove yerhed >/dev/null
fi
codex mcp add yerhed -- "$PYTHON_BIN" "$SERVER"
codex mcp list | sed -n '1,120p'
