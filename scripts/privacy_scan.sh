#!/bin/sh
set -eu
REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
# Generic share-safety scan. Public GitHub links are allowed; use a local denylist for private repo URLs or project names.
USER_PATH='/Us''ers/[[:alnum:]_.-]+'
THREAD_FIELD='target''_thread'
LIVE_ID='019[0-9a-f]{20,}'
BASE_PATTERN="$USER_PATH|$THREAD_FIELD|$LIVE_ID"
LOCAL_DENYLIST="${YERHED_PRIVACY_DENYLIST:-$REPO/.privacy-denylist.local}"
LOCAL_PATTERN=""
if [ -f "$LOCAL_DENYLIST" ]; then
  LOCAL_PATTERN="$(grep -Ev '^[[:space:]]*(#|$)' "$LOCAL_DENYLIST" | paste -sd'|' - || true)"
fi
if [ -n "$LOCAL_PATTERN" ]; then
  PATTERN="($BASE_PATTERN|$LOCAL_PATTERN)"
else
  PATTERN="($BASE_PATTERN)"
fi
TMP="${TMPDIR:-/tmp}/yerhed-privacy-scan-$$"
: > "$TMP"
if git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1 && [ -n "$(git -C "$REPO" ls-files)" ]; then
  git -C "$REPO" ls-files | while IFS= read -r f; do
    [ "$f" = "scripts/privacy_scan.sh" ] && continue
    [ -f "$REPO/$f" ] && grep -Ein "$PATTERN" "$REPO/$f" || true
  done > "$TMP"
else
  find "$REPO" -type f \( -path '*/.git/*' -o -path '*/.venv/*' -o -path '*/__pycache__/*' \) -prune -o -type f -print | xargs grep -Ein "$PATTERN" > "$TMP" || true
fi
if [ -s "$TMP" ]; then cat "$TMP"; rm -f "$TMP"; echo "privacy scan failed" >&2; exit 1; fi
rm -f "$TMP"
if git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  tracked_private_context="$(git -C "$REPO" ls-files USER.md SOUL.md MEMORY.md 2>/dev/null || true)"
  if [ -n "$tracked_private_context" ]; then
    printf '%s
' "$tracked_private_context"
    echo "privacy scan failed: real local context files must not be tracked; use *.example.md templates" >&2
    exit 1
  fi
fi

echo "Privacy scan baseline checks OK (not exhaustive; review diffs and use a local denylist before publishing)"
