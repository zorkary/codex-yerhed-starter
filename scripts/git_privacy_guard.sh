#!/bin/sh
set -eu

MODE="${1:-pre-commit}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO="${YERHED_REPO:-$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)}"

fail() {
  echo "Yerhed starter privacy guard failed: $*" >&2
  exit 1
}

"$REPO/scripts/privacy_scan.sh"
if [ -x "$REPO/scripts/memory_leak_scan.sh" ]; then
  if [ "$MODE" = "pre-push" ]; then
    "$REPO/scripts/memory_leak_scan.sh" --repo "$REPO" --mode tracked --profile self
  else
    "$REPO/scripts/memory_leak_scan.sh" --repo "$REPO" --mode staged --profile self
  fi
fi

if git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  staged_paths="$(git -C "$REPO" diff --cached --name-only --diff-filter=ACMR || true)"
  if [ -n "$staged_paths" ]; then
    bad_paths="$(printf '%s\n' "$staged_paths" | grep -E '(^|/)(\.obsidian/|\.codex/|\.venv/|__pycache__/|\.env($|\.)|automation\.toml$|id_rsa$|id_ed25519$|.*\.(pem|key|p12|mobileprovision)$)|^(USER|SOUL|MEMORY)\.md$' || true)"
    if [ -n "$bad_paths" ]; then
      printf '%s\n' "$bad_paths" >&2
      fail "staged private/runtime files are not allowed in the sanitized starter"
    fi
  fi
fi

tracked_private_context="$(git -C "$REPO" ls-files USER.md SOUL.md MEMORY.md 2>/dev/null || true)"
if [ -n "$tracked_private_context" ]; then
  printf '%s\n' "$tracked_private_context" >&2
  fail "real local context files must not be tracked; use *.example.md templates"
fi

if command -v gitleaks >/dev/null 2>&1; then
  if [ "$MODE" = "pre-push" ]; then
    gitleaks detect --source "$REPO" --redact --no-banner
  else
    gitleaks protect --staged --source "$REPO" --redact --no-banner
  fi
else
  echo "gitleaks not found; skipped optional secret scan" >&2
fi

echo "Yerhed starter privacy guard OK"
