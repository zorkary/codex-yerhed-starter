#!/bin/sh
set -eu

REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
export CODEX_HOME="$TMPDIR/codex-home"
export YERHED_SMOKE_TMP="$TMPDIR"
export YERHED_REPO="$REPO"
export YERHED_BRAIN_ROOT="$TMPDIR/brain"
mkdir -p "$CODEX_HOME"

"$REPO/scripts/init_brain.sh"
"$REPO/scripts/init_local_context.sh"
"$REPO/scripts/install_hook.sh"
"$REPO/scripts/install_global_bootstrap.sh"

if command -v codex >/dev/null 2>&1; then
  "$REPO/scripts/install_mcp.sh" >/dev/null
  codex mcp list | grep -q '^yerhed[[:space:]]'
else
  echo "codex not found; skipped mcp registration smoke" >&2
fi

grep -q 'BEGIN YERHED HOOK' "$CODEX_HOME/config.toml"
grep -q 'BEGIN YERHED GLOBAL BOOTSTRAP' "$CODEX_HOME/AGENTS.md"

mkdir -p "$TMPDIR/unknown-repo"
printf '# Unknown Repo\n\nFresh install smoke repo.\n' > "$TMPDIR/unknown-repo/README.md"
git -C "$TMPDIR/unknown-repo" init >/dev/null 2>&1 || true

PYTHONPATH="$REPO" python3 - <<'PY'
from pathlib import Path
from yerhed_mcp.tools import bootstrap_context, closeout_check, search
import os

repo = Path(os.environ["YERHED_REPO"])
brain = Path(os.environ["YERHED_BRAIN_ROOT"])
unknown = Path(os.environ["YERHED_SMOKE_TMP"]) / "unknown-repo"
result = bootstrap_context(prompt="fresh install smoke", cwd=str(repo))
assert result["ok"], result
assert "tool_affordance_map" in result, result
assert search("definitely-empty-search-token", scope="projects", limit=3)["ok"]
if unknown:
    closeout = closeout_check(
        str(unknown),
        "Inspected fresh unknown repo during Yerhed first-run smoke.",
        "Unknown repo should be onboarded if it matters beyond this turn.",
        ["README.md"],
        dry_run=True,
    )
    assert closeout["disposition"] in {"proposed", "updated"}, closeout
assert (brain / "RESOLVER.md").exists()
print("fresh install smoke OK")
PY

echo "Yerhed fresh install smoke OK"
