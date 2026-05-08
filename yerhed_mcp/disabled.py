from __future__ import annotations

import os
from collections.abc import Mapping

DISABLED_VALUES = {"1", "true", "yes", "on"}
DISABLED_ERROR = "Yerhed is disabled by YERHED_DISABLED=1"
DISABLED_HOOK_CONTEXT = (
    "Yerhed is disabled by YERHED_DISABLED=1. "
    "Do not call yerhed.bootstrap_context, Yerhed MCP tools, or Yerhed closeout memory writes. "
    "Yerhed MCP tools will refuse while disabled. "
    "If the user asks why Yerhed is unavailable, asks how to disable/remove/re-enable it, "
    "or the task depends on Yerhed memory, explain that the runtime kill switch is active. "
    "To re-enable for this shell/session, unset YERHED_DISABLED or set it to 0, then restart Codex if needed. "
    "To fully remove reminders, run scripts/uninstall_hook.sh, remove the Yerhed global boot card from "
    "$CODEX_HOME/AGENTS.md, and run codex mcp remove yerhed. "
    "Do not repeatedly announce disabled state in unrelated chats."
)


def is_yerhed_disabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    value = str(env.get("YERHED_DISABLED", "")).strip().lower()
    return value in DISABLED_VALUES


def disabled_response() -> dict[str, object]:
    return {"ok": False, "disabled": True, "error": DISABLED_ERROR, "pushed": False}
