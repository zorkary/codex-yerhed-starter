#!/bin/sh
set -eu
exec python3 - "$@" <<'PYCODE'
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

TEXT_LIMIT = 1024 * 1024
SKIP_DIRS = {".git", ".venv", "__pycache__", ".cache", ".tmp", "node_modules", "dist", "build"}
REAL_CONTEXT_NAMES = {"USER.md", "SOUL.md", "MEMORY.md"}
PRIVATE_FILE_RE = re.compile(r"(^|/)(\.obsidian/|\.codex/|\.venv/|__pycache__/|\.env($|\.)|automation\.toml$|id_rsa$|id_ed25519$|.*\.(pem|key|p12|mobileprovision)$)")
SECRET_RE = re.compile(
    r"BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY"
    r"|github_pat_[A-Za-z0-9_]+"
    r"|ghp_[A-Za-z0-9_]{20,}"
    r"|sk-[A-Za-z0-9_-]{20,}"
    r"|xox[baprs]-[A-Za-z0-9-]+"
    r"|(?:ANTHROPIC|OPENAI|GITHUB|SLACK)_API_KEY",
    re.I,
)
AUTOMATION_RE = re.compile(
    r"\btarget" r"_thread_id\b|\btarget" r"_thread\b|\bkind\s*=\s*['\"]?heartbeat",
    re.I,
)
BRAIN_TOP_FILES = {"RESOLVER.md", "schema.md", "log.md"}
BRAIN_DIRS = {"people", "projects", "concepts", "ideas", "places", "organizations", "companions", "sources", "inbox", "archive"}
INTERNAL_ALLOWED_PATH_PREFIXES = (
    "README.md",
    "AGENTS.md",
    "ACCESS_POLICY.md",
    "HEARTBEAT.md",
    "TOOLS.md",
    "pyproject.toml",
    "config/",
    "docs/",
    "scripts/",
    "tests/",
    "yerhed_mcp/",
    "automations/",
    "evals/",
    "mcp/",
)


def run(cmd: list[str], cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=check)


def is_git_repo(repo: Path) -> bool:
    return run(["git", "rev-parse", "--is-inside-work-tree"], repo).returncode == 0


def git_lines(repo: Path, args: list[str]) -> list[str]:
    proc = run(["git", *args], repo)
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line]


def candidate_paths(repo: Path, mode: str) -> list[str]:
    if mode == "staged":
        return git_lines(repo, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if mode == "tracked":
        return git_lines(repo, ["ls-files"])
    found: list[str] = []
    for current_root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        base = Path(current_root)
        for name in files:
            path = base / name
            try:
                found.append(path.relative_to(repo).as_posix())
            except ValueError:
                continue
    return sorted(found)


def staged_content(repo: Path, rel: str) -> bytes | None:
    proc = subprocess.run(["git", "show", f":{rel}"], cwd=str(repo), capture_output=True)
    if proc.returncode == 0:
        return proc.stdout[:TEXT_LIMIT]
    return None


def file_content(repo: Path, rel: str) -> bytes | None:
    path = repo / rel
    try:
        return path.read_bytes()[:TEXT_LIMIT]
    except OSError:
        return None


def content_for(repo: Path, rel: str, mode: str) -> str:
    raw = staged_content(repo, rel) if mode == "staged" and is_git_repo(repo) else None
    if raw is None:
        raw = file_content(repo, rel)
    if raw is None:
        return ""
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def is_internal_allowed_path(rel: str) -> bool:
    return any(rel == prefix.rstrip("/") or rel.startswith(prefix) for prefix in INTERNAL_ALLOWED_PATH_PREFIXES)


def add_issue(issues: list[str], rel: str, reason: str) -> None:
    issues.append(f"{rel}: {reason}")


def scan_path(rel: str, issues: list[str]) -> None:
    normalized = rel.replace("\\", "/")
    name = Path(normalized).name
    if name in REAL_CONTEXT_NAMES:
        add_issue(issues, rel, "real local context file must not be committed; use *.example.md")
    if PRIVATE_FILE_RE.search(normalized):
        add_issue(issues, rel, "runtime, credential, live automation, or private-key-like path")
    path_parts = Path(normalized).parts
    parts = set(path_parts)
    if path_parts and path_parts[0] in BRAIN_DIRS and not normalized.startswith("templates/brain/"):
        add_issue(issues, rel, "top-level path looks like copied Yerhed brain content")
    if "Personal" in parts and "Yerhed" in parts and "brain" in parts:
        add_issue(issues, rel, "path appears to copy the Yerhed brain root")


def brain_root_in_text(text: str, brain_root: str) -> bool:
    candidates = {
        str(Path(brain_root).expanduser()),
        str(Path(os.path.expandvars(brain_root)).expanduser()),
        "Personal/Yerhed/brain",
    }
    return any(candidate and candidate in text for candidate in candidates)


def scan_content(rel: str, text: str, profile: str, brain_root: str, issues: list[str]) -> None:
    if not text:
        return
    if SECRET_RE.search(text):
        add_issue(issues, rel, "possible secret or private key content")
    if AUTOMATION_RE.search(text) and (rel.endswith("automation.toml") or ".codex" in rel):
        add_issue(issues, rel, "live Codex automation record content")
    if brain_root_in_text(text, brain_root):
        if not (profile == "self" and is_internal_allowed_path(rel)):
            add_issue(issues, rel, "absolute or recognizable Yerhed brain-root path")


def scan_brain_fingerprint(paths: list[str], issues: list[str]) -> None:
    top = {p.split("/", 1)[0] for p in paths}
    root_files = {p for p in paths if "/" not in p and p in BRAIN_TOP_FILES}
    brain_dirs = top & BRAIN_DIRS
    if len(root_files) >= 2 and len(brain_dirs) >= 2:
        add_issue(issues, ".", "candidate set looks like a copied Yerhed brain root")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a repo for accidentally copied Yerhed private memory.")
    parser.add_argument("--repo", default=".", help="repo/path to scan")
    parser.add_argument("--mode", choices=("staged", "tracked", "all"), default="staged")
    parser.add_argument("--brain-root", default=os.environ.get("YERHED_BRAIN_ROOT", "$HOME/Personal/Yerhed/brain"))
    parser.add_argument("--profile", choices=("external", "self"), default="external", help="self allows documented Yerhed path references inside Yerhed repos")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists():
        print(f"memory leak scan failed: repo does not exist: {repo}", file=sys.stderr)
        return 2
    if args.mode in {"staged", "tracked"} and not is_git_repo(repo):
        print(f"memory leak scan failed: {repo} is not a git repo", file=sys.stderr)
        return 2

    issues: list[str] = []
    paths = candidate_paths(repo, args.mode)
    scan_brain_fingerprint(paths, issues)
    for rel in paths:
        scan_path(rel, issues)
        scan_content(rel, content_for(repo, rel, args.mode), args.profile, args.brain_root, issues)

    if issues:
        print("Yerhed memory leak scan failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print(f"Yerhed memory leak scan OK ({args.mode}, {len(paths)} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PYCODE
