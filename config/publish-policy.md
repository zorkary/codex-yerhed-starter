# Yerhed Publish Policy

This starter repo may contain templates, scripts, tests, and example data. Real brain memory must live outside this repo. Run `scripts/privacy_scan.sh` before sharing or publishing.


## Local Git Privacy Hooks

Run `scripts/install_git_hooks.sh` in each checkout you plan to publish from. The
installed `pre-commit` and `pre-push` hooks call `scripts/git_privacy_guard.sh`,
which runs the starter privacy scan, blocks common runtime/credential/live
automation files, and uses `gitleaks` when it is installed.

Hooks are local to each clone. They reduce accidental leaks, but they are not a
substitute for reviewing `git diff --cached` and confirming remote visibility
before sharing.


## Cross-Repo Leak Guard

Use `scripts/memory_leak_scan.sh --repo <path> --mode staged` before pushing, exporting, building a share pack, or attaching files from any repo that may contain Yerhed-derived memory. Install `scripts/install_external_repo_guard.sh <repo_path>` only for selected high-risk repos. Install `scripts/install_brain_git_guard.sh` on the brain root so brain pushes are blocked at git-hook level. Do not install global git hooks in v1.
