from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from yerhed_mcp import hook

REPO = Path(__file__).resolve().parents[1]


class YerhedHookTests(unittest.TestCase):
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def run_script(self, name: str, codex_home: Path) -> None:
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        env["YERHED_REPO"] = str(self.repo_root())
        subprocess.run([str(self.repo_root() / "scripts" / name)], check=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_hook_output_is_compact_and_conditional(self) -> None:
        output = hook.hook_output(hook.REMINDER)
        text = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("yerhed.bootstrap_context once", text)
        self.assertIn("Do not call bootstrap repeatedly", text)
        self.assertIn("Do not write memory merely because Yerhed loaded", text)
        self.assertNotIn("Always call", text)
        self.assertNotIn("brain root", text.lower())


    def test_hook_disabled_notice_is_model_facing_and_conditional(self) -> None:
        env = os.environ.copy()
        env["YERHED_DISABLED"] = "1"
        proc = subprocess.run(
            [sys.executable, str(REPO / "yerhed_mcp" / "hook.py")],
            input=json.dumps({"hookEventName": "UserPromptSubmit"}),
            text=True,
            capture_output=True,
            env=env,
            check=True,
        )
        payload = json.loads(proc.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Yerhed is disabled by YERHED_DISABLED=1", context)
        self.assertIn("Do not call yerhed.bootstrap_context", context)
        self.assertIn("Yerhed MCP tools will refuse", context)
        self.assertIn("unset YERHED_DISABLED", context)
        self.assertIn("codex mcp remove yerhed", context)
        self.assertIn("Do not repeatedly announce disabled state", context)
        self.assertNotIn("If this chat has not already loaded Yerhed", context)

    def test_disable_script_prints_steps_and_can_remove_global_boot_card(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            codex_home = Path(td) / "codex"
            codex_home.mkdir()
            agents = codex_home / "AGENTS.md"
            agents.write_text(
                "before\n"
                "<!-- BEGIN YERHED GLOBAL BOOTSTRAP -->\n"
                "Yerhed boot card\n"
                "<!-- END YERHED GLOBAL BOOTSTRAP -->\n"
                "after\n"
            )
            env = os.environ.copy()
            env["CODEX_HOME"] = str(codex_home)
            env["YERHED_REPO"] = str(REPO)

            proc = subprocess.run(
                [str(REPO / "scripts" / "disable_yerhed.sh")],
                text=True,
                capture_output=True,
                env=env,
                check=True,
            )
            self.assertIn("export YERHED_DISABLED=1", proc.stdout)
            self.assertIn("unset YERHED_DISABLED", proc.stdout)
            self.assertIn("codex mcp remove yerhed", proc.stdout)

            subprocess.run(
                [str(REPO / "scripts" / "disable_yerhed.sh"), "--remove-global-boot-card"],
                text=True,
                capture_output=True,
                env=env,
                check=True,
            )
            updated = agents.read_text()
            self.assertIn("before", updated)
            self.assertIn("after", updated)
            self.assertNotIn("Yerhed boot card", updated)

    def test_hook_cli_handles_malformed_input(self) -> None:
        proc = subprocess.run(
            ["python3", str(self.repo_root() / "yerhed_mcp" / "hook.py")],
            input="not json",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        result = json.loads(proc.stdout)
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("non-blocking error", result["hookSpecificOutput"]["additionalContext"])

    def test_installers_are_idempotent_and_preserve_other_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / "codex"
            codex_home.mkdir()
            config = codex_home / "config.toml"
            config.write_text(
                "# BEGIN QUIET_CLOCK HOOK\n"
                "[[hooks.UserPromptSubmit]]\n"
                "matcher = \"\"\n"
                "# END QUIET_CLOCK HOOK\n",
                encoding="utf-8",
            )
            self.run_script("install_hook.sh", codex_home)
            self.run_script("install_hook.sh", codex_home)
            text = config.read_text(encoding="utf-8")
            self.assertEqual(text.count("BEGIN YERHED HOOK"), 1)
            self.assertIn("BEGIN QUIET_CLOCK HOOK", text)
            self.run_script("uninstall_hook.sh", codex_home)
            text = config.read_text(encoding="utf-8")
            self.assertNotIn("BEGIN YERHED HOOK", text)
            self.assertIn("BEGIN QUIET_CLOCK HOOK", text)

    def test_global_bootstrap_installer_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / "codex"
            codex_home.mkdir()
            agents = codex_home / "AGENTS.md"
            agents.write_text("# Existing\n\nKeep this.\n", encoding="utf-8")
            self.run_script("install_global_bootstrap.sh", codex_home)
            self.run_script("install_global_bootstrap.sh", codex_home)
            text = agents.read_text(encoding="utf-8")
            self.assertIn("# Existing", text)
            self.assertEqual(text.count("BEGIN YERHED GLOBAL BOOTSTRAP"), 1)
            self.assertIn("Yerhed Global Boot Card", text)


if __name__ == "__main__":
    unittest.main()
