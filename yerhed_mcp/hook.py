#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from yerhed_mcp.disabled import DISABLED_HOOK_CONTEXT, is_yerhed_disabled

HOOK_EVENT = "UserPromptSubmit"

REMINDER = (
    "Yerhed is available as the private memory layer. "
    "If this chat has not already loaded Yerhed and the request may involve memory, "
    "project continuity, people, preferences, history, ideas, sources, open loops, "
    "repo continuity, or external-output safety, call yerhed.bootstrap_context once. "
    "After bootstrap, retain its tool map and use specific Yerhed tools as needed. "
    "Do not call bootstrap repeatedly unless context was compacted, the working repo changed, "
    "or the user asks to refresh memory. Do not write memory merely because Yerhed loaded. "
    "Before sharing memory-derived text externally, use prepare_external_output. "
    "For full policy or MCP fallback, read the AGENTS.md file in the Yerhed checkout."
)


def hook_output(text: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "additionalContext": text,
        }
    }


def main() -> int:
    try:
        raw = sys.stdin.read()
        if raw.strip():
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                parsed = {}
        context = DISABLED_HOOK_CONTEXT if is_yerhed_disabled() else REMINDER
        print(json.dumps(hook_output(context), separators=(",", ":")))
        return 0
    except Exception as exc:  # pragma: no cover - hooks must never block prompts
        fallback = (
            "Yerhed hook encountered a non-blocking error: "
            f"{type(exc).__name__}. If memory/project continuity matters, call yerhed.bootstrap_context."
        )
        print(json.dumps(hook_output(fallback), separators=(",", ":")))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
