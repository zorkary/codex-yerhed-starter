#!/bin/sh
set -eu
REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
BRAIN_ROOT="${YERHED_BRAIN_ROOT:-$HOME/Personal/Yerhed/brain}"
missing=0
check_file() { if [ ! -f "$1" ]; then echo "missing file: $1"; missing=1; fi; }
check_dir() { if [ ! -d "$1" ]; then echo "missing dir: $1"; missing=1; fi; }
for file in README.md AGENTS.md SECURITY.md THREAT_MODEL.md SOUL.example.md USER.example.md MEMORY.example.md ACCESS_POLICY.md HEARTBEAT.md TOOLS.md pyproject.toml config/egress-policy.md config/global-bootstrap.md mcp/server.py yerhed_mcp/disabled.py yerhed_mcp/tools.py yerhed_mcp/hook.py scripts/smoke_mcp_tools.sh scripts/smoke_fresh_install.sh scripts/init_brain.sh scripts/init_local_context.sh scripts/install_mcp.sh scripts/install_hook.sh scripts/uninstall_hook.sh scripts/disable_yerhed.sh scripts/uninstall_git_hooks.sh scripts/uninstall_brain_git_guard.sh scripts/uninstall_external_repo_guard.sh scripts/install_global_bootstrap.sh scripts/install_obsidian_graph_settings.sh scripts/memory_leak_scan.sh scripts/install_brain_git_guard.sh scripts/install_external_repo_guard.sh docs/disable.md docs/obsidian.md tests/test_obsidian_graph_settings.py tests/test_hook_bootstrap_scripts.py tests/test_safety_docs.py templates/obsidian/graph.json.example; do check_file "$REPO/$file"; done
for base in SOUL USER MEMORY; do
  if [ ! -f "$REPO/$base.md" ] && [ ! -f "$REPO/$base.example.md" ]; then
    echo "missing local $base.md or tracked $base.example.md"
    missing=1
  fi
done
for dir in automations config evals scripts tests templates yerhed_mcp; do check_dir "$REPO/$dir"; done
if [ -d "$BRAIN_ROOT" ]; then
  for dir in archive concepts ideas inbox people projects places organizations companions sources; do check_dir "$BRAIN_ROOT/$dir"; done
  check_file "$BRAIN_ROOT/log.md"
  check_file "$BRAIN_ROOT/projects/open-loops.md"
else
  echo "brain root not initialized yet: $BRAIN_ROOT"
fi
if [ "$missing" -ne 0 ]; then exit 1; fi
echo "Yerhed starter structure OK"
echo "Repo: $REPO"
echo "Brain root: $BRAIN_ROOT"
