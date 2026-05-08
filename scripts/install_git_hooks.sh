#!/bin/sh
set -eu

REPO="$(git rev-parse --show-toplevel 2>/dev/null || { CDPATH= cd -- "$(dirname -- "$0")/.." && pwd; })"
HOOK_DIR="$REPO/.git/hooks"
GUARD="$REPO/scripts/git_privacy_guard.sh"
MARKER="Yerhed starter privacy hook"

if [ ! -d "$REPO/.git" ]; then
  echo "install_git_hooks.sh must run inside a git checkout" >&2
  exit 1
fi

if [ ! -x "$GUARD" ]; then
  echo "missing executable guard script: $GUARD" >&2
  exit 1
fi

mkdir -p "$HOOK_DIR"

install_hook() {
  hook_name="$1"
  guard_mode="$2"
  hook="$HOOK_DIR/$hook_name"
  backup=""

  if [ -f "$hook" ] && grep -q "$MARKER" "$hook" 2>/dev/null; then
    echo "Yerhed starter $hook_name hook already installed: $hook"
    return 0
  fi

  if [ -f "$hook" ]; then
    backup_base="$hook.yerhed-backup"
    candidate="$backup_base"
    i=0
    while [ -e "$candidate" ]; do
      i=$((i + 1))
      candidate="$backup_base.$i"
    done
    mv "$hook" "$candidate"
    backup="$candidate"
  fi

  cat > "$hook" <<HOOK
#!/bin/sh
set -eu
# $MARKER
EXISTING_HOOK="$backup"
if [ -n "\$EXISTING_HOOK" ] && [ -x "\$EXISTING_HOOK" ]; then
  "\$EXISTING_HOOK" "\$@"
fi
exec "\$(git rev-parse --show-toplevel)/scripts/git_privacy_guard.sh" $guard_mode
HOOK
  chmod +x "$hook"
  echo "Installed Yerhed starter $hook_name privacy hook: $hook"
  if [ -n "$backup" ]; then
    echo "Preserved existing $hook_name hook: $backup"
  fi
}

install_hook pre-commit pre-commit
install_hook pre-push pre-push
chmod +x "$GUARD"
