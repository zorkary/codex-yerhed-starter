#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <repo_path>" >&2
  exit 2
fi

TARGET_REPO="$(CDPATH= cd -- "$1" && pwd)"
SCANNER="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/memory_leak_scan.sh"
BRAIN_ROOT="${YERHED_BRAIN_ROOT:-$HOME/Personal/Yerhed/brain}"

if [ ! -d "$TARGET_REPO/.git" ]; then
  echo "target is not a git repo: $TARGET_REPO" >&2
  exit 1
fi

HOOK_DIR="$TARGET_REPO/.git/hooks"
HOOK="$HOOK_DIR/pre-push"
BACKUP="$HOOK.yerhed-backup"
mkdir -p "$HOOK_DIR"

if [ -f "$HOOK" ] && ! grep -q "Yerhed external memory leak guard" "$HOOK" 2>/dev/null; then
  i=0
  candidate="$BACKUP"
  while [ -e "$candidate" ]; do
    i=$((i + 1))
    candidate="$BACKUP.$i"
  done
  mv "$HOOK" "$candidate"
  BACKUP="$candidate"
elif [ ! -f "$BACKUP" ]; then
  BACKUP=""
fi

cat > "$HOOK" <<HOOK
#!/bin/sh
set -eu
# Yerhed external memory leak guard
EXISTING_HOOK="$BACKUP"
if [ -n "\$EXISTING_HOOK" ] && [ -x "\$EXISTING_HOOK" ]; then
  "\$EXISTING_HOOK" "\$@"
fi
YERHED_BRAIN_ROOT="${BRAIN_ROOT}" "${SCANNER}" --repo "${TARGET_REPO}" --mode tracked --profile external
YERHED_BRAIN_ROOT="${BRAIN_ROOT}" "${SCANNER}" --repo "${TARGET_REPO}" --mode staged --profile external
HOOK
chmod +x "$HOOK"
echo "Installed Yerhed external memory leak guard: $HOOK"
if [ -n "$BACKUP" ]; then
  echo "Preserved existing pre-push hook: $BACKUP"
fi
