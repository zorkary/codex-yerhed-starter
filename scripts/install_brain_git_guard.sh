#!/bin/sh
set -eu

BRAIN_ROOT="${YERHED_BRAIN_ROOT:-$HOME/Personal/Yerhed/brain}"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --brain-root)
      BRAIN_ROOT="$2"
      shift 2
      ;;
    *)
      echo "usage: $0 [--brain-root PATH]" >&2
      exit 2
      ;;
  esac
done

if [ ! -d "$BRAIN_ROOT/.git" ]; then
  echo "brain root is not a git repo: $BRAIN_ROOT" >&2
  exit 1
fi

HOOK="$BRAIN_ROOT/.git/hooks/pre-push"
MARKER="Yerhed brain root local-only guard"
backup=""
mkdir -p "$(dirname "$HOOK")"

if [ -f "$HOOK" ] && grep -q "$MARKER" "$HOOK" 2>/dev/null; then
  echo "Brain-root push guard already installed: $HOOK"
elif [ -f "$HOOK" ]; then
  backup_base="$HOOK.yerhed-backup"
  candidate="$backup_base"
  i=0
  while [ -e "$candidate" ]; do
    i=$((i + 1))
    candidate="$backup_base.$i"
  done
  mv "$HOOK" "$candidate"
  backup="$candidate"
else
  backup=""
fi

if [ ! -f "$HOOK" ] || ! grep -q "$MARKER" "$HOOK" 2>/dev/null; then
  cat > "$HOOK" <<HOOK
#!/bin/sh
# $MARKER
EXISTING_HOOK="$backup"
echo "Yerhed brain root is local-only; refusing git push." >&2
echo "Remove any brain-root remote and use encrypted backup/export tooling instead." >&2
exit 1
HOOK
  chmod +x "$HOOK"
  echo "Installed brain-root push guard: $HOOK"
  if [ -n "$backup" ]; then
    echo "Preserved existing pre-push hook: $backup"
  fi
fi

if [ -n "$(git -C "$BRAIN_ROOT" remote 2>/dev/null || true)" ]; then
  git -C "$BRAIN_ROOT" remote -v >&2 || true
  echo "brain root has a git remote; push guard is installed, but remove the remote before treating this as safe" >&2
  exit 1
fi
