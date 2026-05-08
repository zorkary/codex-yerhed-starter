from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCANNER = REPO_ROOT / "scripts" / "memory_leak_scan.sh"
INSTALL_BRAIN = REPO_ROOT / "scripts" / "install_brain_git_guard.sh"
UNINSTALL_BRAIN = REPO_ROOT / "scripts" / "uninstall_brain_git_guard.sh"
INSTALL_EXTERNAL = REPO_ROOT / "scripts" / "install_external_repo_guard.sh"
UNINSTALL_EXTERNAL = REPO_ROOT / "scripts" / "uninstall_external_repo_guard.sh"
INSTALL_GIT_HOOKS = REPO_ROOT / "scripts" / "install_git_hooks.sh"
UNINSTALL_GIT_HOOKS = REPO_ROOT / "scripts" / "uninstall_git_hooks.sh"
GIT_PRIVACY_GUARD = REPO_ROOT / "scripts" / "git_privacy_guard.sh"
PRIVACY_SCAN = REPO_ROOT / "scripts" / "privacy_scan.sh"


def run(cmd: list[str | Path], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run([str(part) for part in cmd], cwd=str(cwd) if cwd else None, text=True, capture_output=True, env=merged_env)


class MemoryLeakGuardScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.brain = self.base / "brain"
        self.brain.mkdir()
        self.env = {"YERHED_BRAIN_ROOT": str(self.brain)}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def make_repo(self) -> Path:
        repo = self.base / f"repo-{len(list(self.base.glob('repo-*')))}"
        repo.mkdir()
        self.assertEqual(run(["git", "init"], cwd=repo).returncode, 0)
        self.assertEqual(run(["git", "config", "user.email", "yerhed@example.invalid"], cwd=repo).returncode, 0)
        self.assertEqual(run(["git", "config", "user.name", "Yerhed Test"], cwd=repo).returncode, 0)
        return repo

    def write_and_stage(self, repo: Path, rel: str, text: str) -> None:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.assertEqual(run(["git", "add", rel], cwd=repo).returncode, 0)

    def scan(self, repo: Path, mode: str = "staged") -> subprocess.CompletedProcess[str]:
        return run([SCANNER, "--repo", repo, "--mode", mode], env=self.env)

    def test_examples_and_ordinary_docs_pass(self) -> None:
        repo = self.make_repo()
        self.write_and_stage(repo, "README.md", "# Ordinary project\nNo private memory here.\n")
        self.write_and_stage(repo, "USER.example.md", "# USER.example.md\nTemplate only.\n")
        result = self.scan(repo)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_context_file_fails(self) -> None:
        repo = self.make_repo()
        self.write_and_stage(repo, "notes/USER.md", "# USER.md\nreal context\n")
        result = self.scan(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("real local context", result.stderr)

    def test_brain_root_path_fails(self) -> None:
        repo = self.make_repo()
        self.write_and_stage(repo, "docs/note.md", f"Copied from {self.brain}\n")
        result = self.scan(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("brain-root path", result.stderr)

    def test_runtime_and_secret_content_fail(self) -> None:
        repo = self.make_repo()
        self.write_and_stage(repo, ".codex/automations/example/automation.toml", "kind = 'heartbeat'\n" + "target" + "_thread_id = '019" + "abcdefabcdefabcdef'\n")
        self.write_and_stage(repo, "key.txt", "-----BEGIN OPENSSH PRIVATE" + " KEY-----\nabc\n")
        result = self.scan(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("private-key", result.stderr)

    def test_brain_fingerprint_fails(self) -> None:
        repo = self.make_repo()
        for rel in ["RESOLVER.md", "schema.md", "people/a.md", "sources/raw.md"]:
            self.write_and_stage(repo, rel, "brain-ish\n")
        result = self.scan(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("copied Yerhed brain root", result.stderr)

    def test_new_brain_dirs_and_obsidian_config_fail(self) -> None:
        repo = self.make_repo()
        self.write_and_stage(repo, "places/home.md", "private place note\n")
        self.write_and_stage(repo, "organizations/example.md", "private org note\n")
        self.write_and_stage(repo, ".obsidian/workspace.json", "{}\n")
        result = self.scan(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("top-level path looks like copied Yerhed brain content", result.stderr)
        self.assertIn("runtime, credential", result.stderr)

    def test_brain_push_guard_blocks_pushes_and_remote_install(self) -> None:
        brain = self.base / "guarded-brain"
        brain.mkdir()
        self.assertEqual(run(["git", "init"], cwd=brain).returncode, 0)
        install = run([INSTALL_BRAIN, "--brain-root", brain], env=self.env)
        self.assertEqual(install.returncode, 0, install.stderr)
        hook = brain / ".git" / "hooks" / "pre-push"
        blocked = run([hook], cwd=brain)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("local-only", blocked.stderr)
        uninstall = run([UNINSTALL_BRAIN, "--brain-root", brain], env=self.env)
        self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
        self.assertFalse(hook.exists())

        with_remote = self.base / "remote-brain"
        with_remote.mkdir()
        self.assertEqual(run(["git", "init"], cwd=with_remote).returncode, 0)
        self.assertEqual(run(["git", "remote", "add", "origin", "https://example.invalid/brain.git"], cwd=with_remote).returncode, 0)
        refused = run([INSTALL_BRAIN, "--brain-root", with_remote], env=self.env)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("push guard is installed", refused.stderr)
        remote_hook = with_remote / ".git" / "hooks" / "pre-push"
        self.assertTrue(remote_hook.exists())
        blocked_remote = run([remote_hook], cwd=with_remote)
        self.assertNotEqual(blocked_remote.returncode, 0)
        self.assertIn("local-only", blocked_remote.stderr)


    def test_privacy_scan_success_message_is_not_overconfident(self) -> None:
        repo = self.make_repo()
        self.write_and_stage(repo, "README.md", "# Ordinary project\n")
        result = run([PRIVACY_SCAN], env={"YERHED_REPO": str(repo)})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("baseline checks OK", result.stdout)
        self.assertIn("not exhaustive", result.stdout)

    def test_privacy_scan_uses_ignored_local_denylist(self) -> None:
        repo = self.make_repo()
        self.write_and_stage(repo, "README.md", "private-test-codename\n")
        (repo / ".privacy-denylist.local").write_text("private-test-codename\n", encoding="utf-8")
        result = run([PRIVACY_SCAN], env={"YERHED_REPO": str(repo)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("private-test-codename", result.stdout)
        self.assertEqual(run(["git", "status", "--short"], cwd=repo).stdout.count(".privacy-denylist.local"), 1)


    def test_self_profile_allows_internal_docs_with_brain_path(self) -> None:
        repo = self.make_repo()
        self.write_and_stage(repo, "docs/obsidian.md", "Use ~/Personal/Yerhed/brain as the default brain root.\n")
        result = run([SCANNER, "--repo", repo, "--mode", "staged", "--profile", "self"], env=self.env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        external = run([SCANNER, "--repo", repo, "--mode", "staged"], env=self.env)
        self.assertNotEqual(external.returncode, 0)
        self.assertIn("brain-root path", external.stderr)

    def test_git_privacy_guard_uses_script_repo_when_called_from_other_cwd(self) -> None:
        other_repo = self.make_repo()
        result = run([GIT_PRIVACY_GUARD, "pre-push"], cwd=other_repo, env=self.env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    def test_install_git_hooks_preserves_existing_hooks(self) -> None:
        repo = self.make_repo()
        scripts = repo / "scripts"
        scripts.mkdir()
        guard_log = repo / "guard-ran.txt"
        guard = scripts / "git_privacy_guard.sh"
        guard.write_text(
            f"#!/bin/sh\necho guard:$1 >> {guard_log}\n",
            encoding="utf-8",
        )
        guard.chmod(0o755)
        hook_dir = repo / ".git" / "hooks"
        pre_commit_marker = repo / "existing-pre-commit.txt"
        pre_push_marker = repo / "existing-pre-push.txt"
        (hook_dir / "pre-commit").write_text(f"#!/bin/sh\necho existing > {pre_commit_marker}\n", encoding="utf-8")
        (hook_dir / "pre-push").write_text(f"#!/bin/sh\necho existing > {pre_push_marker}\n", encoding="utf-8")
        (hook_dir / "pre-commit").chmod(0o755)
        (hook_dir / "pre-push").chmod(0o755)

        install = run([INSTALL_GIT_HOOKS], cwd=repo, env=self.env)
        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertIn("Preserved existing pre-commit hook", install.stdout)
        self.assertIn("Preserved existing pre-push hook", install.stdout)
        self.assertTrue((hook_dir / "pre-commit.yerhed-backup").exists())
        self.assertTrue((hook_dir / "pre-push.yerhed-backup").exists())

        self.assertEqual(run([hook_dir / "pre-commit"], cwd=repo, env=self.env).returncode, 0)
        self.assertEqual(run([hook_dir / "pre-push"], cwd=repo, env=self.env).returncode, 0)
        self.assertTrue(pre_commit_marker.exists())
        self.assertTrue(pre_push_marker.exists())
        guard_text = guard_log.read_text(encoding="utf-8")
        self.assertIn("guard:pre-commit", guard_text)
        self.assertIn("guard:pre-push", guard_text)

        uninstall = run([UNINSTALL_GIT_HOOKS, "--repo", repo], cwd=repo, env=self.env)
        self.assertEqual(uninstall.returncode, 0, uninstall.stderr)
        self.assertIn("Restored previous pre-commit hook", uninstall.stdout)
        self.assertIn("Restored previous pre-push hook", uninstall.stdout)
        self.assertNotIn("Yerhed starter privacy hook", (hook_dir / "pre-commit").read_text(encoding="utf-8"))
        self.assertNotIn("Yerhed starter privacy hook", (hook_dir / "pre-push").read_text(encoding="utf-8"))

    def test_external_repo_guard_preserves_existing_hook_and_blocks_memory(self) -> None:
        repo = self.make_repo()
        hook_dir = repo / ".git" / "hooks"
        existing_hook = hook_dir / "pre-push"
        marker = repo / "existing-hook-ran.txt"
        existing_hook.write_text(f"#!/bin/sh\necho ran > {marker}\n", encoding="utf-8")
        existing_hook.chmod(0o755)

        install = run([INSTALL_EXTERNAL, repo], env=self.env)
        self.assertEqual(install.returncode, 0, install.stderr)
        clean = run([hook_dir / "pre-push"], cwd=repo, env=self.env)
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertTrue(marker.exists())

        self.write_and_stage(repo, "MEMORY.md", "# private memory\n")
        blocked = run([hook_dir / "pre-push"], cwd=repo, env=self.env)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("real local context", blocked.stderr)

        uninstall_external = run([UNINSTALL_EXTERNAL, repo], env=self.env)
        self.assertEqual(uninstall_external.returncode, 0, uninstall_external.stderr)
        self.assertIn("Restored previous pre-push hook", uninstall_external.stdout)
        self.assertNotIn("Yerhed external memory leak guard", existing_hook.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
