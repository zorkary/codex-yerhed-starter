#!/bin/sh
set -eu

REPO_DIR="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
BEGIN_MARKER="<!-- BEGIN YERHED GLOBAL BOOTSTRAP -->"
END_MARKER="<!-- END YERHED GLOBAL BOOTSTRAP -->"

show_steps() {
  cat <<EOF
Yerhed local disable steps

Immediate runtime kill switch:
  export YERHED_DISABLED=1

Re-enable for the current shell/session:
  unset YERHED_DISABLED
  # or
  export YERHED_DISABLED=0

If Codex does not pick up the environment change, restart Codex.

Full local removal steps:
  scripts/uninstall_hook.sh
  remove the Yerhed global boot card from \$CODEX_HOME/AGENTS.md
  codex mcp remove yerhed
  scripts/uninstall_git_hooks.sh
  scripts/uninstall_brain_git_guard.sh --brain-root <brain-root>
  scripts/uninstall_external_repo_guard.sh <repo-path>
  optionally rename or move the brain root if you want tools to stop finding it by path

Optional local mutations supported by this script:
  scripts/disable_yerhed.sh --uninstall-hook
  scripts/disable_yerhed.sh --remove-global-boot-card

This script never deletes memory, pushes, calls network services, or mutates third-party state.
EOF
}

remove_global_boot_card() {
  agents_file="$CODEX_HOME_DIR/AGENTS.md"
  if [ ! -f "$agents_file" ]; then
    echo "No AGENTS.md found at $agents_file"
    return 0
  fi
  tmp_file="$agents_file.tmp.$$"
  python3 - "$agents_file" "$tmp_file" "$BEGIN_MARKER" "$END_MARKER" <<'PY_REMOVE_BOOT_CARD'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
begin = sys.argv[3]
end = sys.argv[4]
text = source.read_text()
start = text.find(begin)
if start == -1:
    target.write_text(text)
    print("Yerhed global boot card was not present")
    raise SystemExit(0)
finish = text.find(end, start)
if finish == -1:
    raise SystemExit("Found begin marker without end marker; refusing to edit")
finish += len(end)
new_text = text[:start].rstrip() + "\n" + text[finish:].lstrip()
target.write_text(new_text)
print("Removed Yerhed global boot card")
PY_REMOVE_BOOT_CARD
  mv "$tmp_file" "$agents_file"
}

if [ "$#" -eq 0 ]; then
  show_steps
  exit 0
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    --uninstall-hook)
      "$REPO_DIR/scripts/uninstall_hook.sh"
      ;;
    --remove-global-boot-card)
      remove_global_boot_card
      ;;
    --help|-h)
      show_steps
      ;;
    *)
      echo "Unknown option: $1" >&2
      show_steps >&2
      exit 2
      ;;
  esac
  shift
done
