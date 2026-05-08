from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install_obsidian_graph_settings.sh"
QUIET_FILTER = "-(file:README OR file:_template OR file:schema OR file:log OR file:open-loops OR path:sources OR path:archive)"


def run(cmd: list[str | Path], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run([str(part) for part in cmd], text=True, capture_output=True, env=merged_env)


class ObsidianGraphSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "brain"
        self.root.mkdir()
        for item in ["RESOLVER.md", "schema.md"]:
            (self.root / item).write_text(f"# {item}\n", encoding="utf-8")
        for dirname in ["projects", "people", "concepts"]:
            (self.root / dirname).mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def read_graph(self) -> dict[str, object]:
        return json.loads((self.root / ".obsidian" / "graph.json").read_text(encoding="utf-8"))

    def test_installer_creates_graph_json(self) -> None:
        result = run([INSTALLER, "--brain-root", self.root])
        self.assertEqual(result.returncode, 0, result.stderr)
        graph = self.read_graph()
        self.assertEqual(graph["search"], QUIET_FILTER)
        self.assertIs(graph["showAttachments"], False)
        self.assertIs(graph["showTags"], False)
        self.assertIs(graph["showOrphans"], False)

    def test_installer_preserves_unrelated_settings(self) -> None:
        graph_dir = self.root / ".obsidian"
        graph_dir.mkdir()
        (graph_dir / "graph.json").write_text(
            json.dumps({"scale": 0.42, "showTags": True, "colorGroups": [{"query": "path:projects", "color": {"a": 1}}]}),
            encoding="utf-8",
        )
        result = run([INSTALLER, "--brain-root", self.root])
        self.assertEqual(result.returncode, 0, result.stderr)
        graph = self.read_graph()
        self.assertEqual(graph["scale"], 0.42)
        self.assertEqual(graph["colorGroups"], [{"query": "path:projects", "color": {"a": 1}}])
        self.assertEqual(graph["search"], QUIET_FILTER)
        self.assertIs(graph["showTags"], False)

    def test_installer_supports_env_brain_root(self) -> None:
        result = run([INSTALLER], env={"YERHED_BRAIN_ROOT": str(self.root)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_graph()["search"], QUIET_FILTER)

    def test_installer_refuses_non_brain_root_without_force(self) -> None:
        bad_root = Path(self.tmp.name) / "not-brain"
        bad_root.mkdir()
        refused = run([INSTALLER, "--brain-root", bad_root])
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("does not look like a Yerhed brain root", refused.stderr)

        forced = run([INSTALLER, "--brain-root", bad_root, "--force"])
        self.assertEqual(forced.returncode, 0, forced.stderr)
        graph = json.loads((bad_root / ".obsidian" / "graph.json").read_text(encoding="utf-8"))
        self.assertEqual(graph["search"], QUIET_FILTER)


if __name__ == "__main__":
    unittest.main()
