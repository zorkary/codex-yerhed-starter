# Threat Model

Yerhed is a local experiment for doc-first Codex memory. It is not DLP, security, compliance, or enterprise data-loss-prevention tooling. Use it at your own risk, and do not use it with data you cannot afford to expose.

## Assets

- Private Markdown memory in the brain root.
- Local profile files such as `USER.md`, `SOUL.md`, and `MEMORY.md` when a user creates them locally.
- Project notes, people notes, source notes, open loops, and logs.
- Local Codex configuration, hooks, MCP registration, and git hooks.
- Secrets or credentials that users might accidentally put in local notes, prompts, diffs, or drafts.

## Trust Boundaries

- The operational repo contains code, docs, scripts, tests, and templates.
- The brain root is private local data and should live outside the repo.
- The MCP server is a local stdio process. It reads local files only when tools are called.
- The hook emits advisory model-facing context. It does not read memory.
- Git-backed writes are local commits unless the user separately pushes a repo.
- External sending surfaces such as Slack, email, GitHub comments, public docs, posts, and calendar invites are outside Yerhed. Yerhed can classify or prepare drafts, but it does not send, post, publish, invite, or push.

## No Send / No Network By Default

Yerhed has no network send path in its MCP tools or hook. Egress helpers classify drafts and return guidance. They do not transmit data.

This matters because the main leak risk is not Yerhed secretly posting to the internet. The realistic risks are user copy/paste, Codex connectors, another tool, a repo push, a copied file, a misconfigured script, or a bug in best-effort classification.

## What Yerhed Helps With

- Separating operational code from private memory.
- Keeping memory writes local, git-backed, reviewable, and reversible.
- Refusing known unsafe paths and obvious private-file leaks.
- Classifying external drafts before a human or connector sends them.
- Redacting private local paths from external drafts by default.
- Providing evidence-aware citations so current reads are not confused with stale memory or assistant inference.
- Offering a kill switch that makes hooks go quiet and MCP tools refuse before reading or writing.

## What Yerhed Does Not Protect

- It does not provide formal DLP guarantees.
- It does not sandbox Codex, your shell, your editor, your browser, Obsidian, or third-party connectors.
- It does not stop a user from manually copying private memory into a public place.
- It does not stop another repo or tool from reading files it is allowed to read.
- It does not make secrets safe to store in Markdown.
- It does not provide legal, compliance, privacy, or security certification.
- It does not guarantee that every sensitive fact will be classified correctly.

## Failure Modes

- A user commits real memory, secrets, or local runtime files to a shareable repo.
- A copied brain-root note appears in another repo and gets pushed.
- A prompt injection convinces an agent to skip the egress check.
- An egress check misclassifies a draft as safe.
- A user approves or copy-pastes sensitive content into an external surface.
- A symlink, archive, export, screenshot, or attachment contains private memory.
- A stale or inferred statement is presented too confidently.

## Mitigations

- Keep the brain root outside the operational repo.
- Keep real `USER.md`, `SOUL.md`, `MEMORY.md`, live automation records, `.codex`, `.obsidian`, `.deepsec`, and `.env` files untracked.
- Use `scripts/privacy_scan.sh`, `scripts/git_privacy_guard.sh`, `scripts/memory_leak_scan.sh`, and `gitleaks` before sharing or pushing. The hook installers preserve existing hooks where possible, and uninstallers restore backed-up hooks where possible.
- Use `yerhed.prepare_external_output` before external drafts.
- Treat egress helpers as best-effort checks, not proof of safety.
- Review git diffs before pushing.
- Keep all memory writes local and reversible through git.
- Use `YERHED_DISABLED=1` when you want the system to refuse all MCP tools immediately.

## Kill Switch

Set:

```sh
export YERHED_DISABLED=1
```

While this is set, the hook emits disabled context instead of bootstrap reminders, and MCP tools refuse before reading or writing anything.

Re-enable for the shell/session with:

```sh
unset YERHED_DISABLED
# or
export YERHED_DISABLED=0
```

Restart Codex if the running app session does not pick up the environment change.

For full local removal, uninstall the hook, remove the global boot card from `$CODEX_HOME/AGENTS.md`, remove MCP registration with `codex mcp remove yerhed`, and remove any git hooks you installed. If you want tools to be unable to find memory by path, move or rename the brain root manually.

## Residual Risk

Even with all safeguards enabled, bugs and misconfiguration can leak private information. Treat Yerhed as alpha local software. Do not use it with credentials, regulated data, client data, or anything you cannot afford to expose.
