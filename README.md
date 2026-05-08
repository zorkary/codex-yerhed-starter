# Yerhed

Doc-first local memory for Codex.

Yerhed is a small, inspectable local experiment for giving Codex durable context
without turning memory into a black box. It keeps the source of truth in plain
Markdown, exposes local stdio MCP tools for search/read/write workflows, and uses
explicit policies for memory updates, external sharing, and evidence.

It is designed for people who want agent memory to feel more like a private
working notebook than a hidden product feature: readable files, local commits,
reviewable automation prompts, and no daemon or cloud service required.

## What It Does

- **Local Markdown memory vault**: durable memory lives outside this repo in a
  private brain root, defaulting to `~/Personal/Yerhed/brain`.
- **Obsidian-compatible graph**: people, projects, concepts, ideas, places,
  organizations, sources, inbox notes, archive notes, wikilinks, YAML
  frontmatter, and a `RESOLVER.md` salience map.
- **Codex stdio MCP tools**: bootstrap context, search, safe file reads,
  project reads, current-state summaries, closeout checks, egress checks,
  evidence summaries, and policy-backed memory writes.
- **Hook-assisted bootstrap**: an optional `UserPromptSubmit` hook and global
  boot card remind Codex that Yerhed exists without preloading private memory.
- **Policy-backed writes**: explicit user intent or a clear update-policy basis
  is required; sensitive or ambiguous changes are proposed first.
- **External sharing guardrails**: `prepare_external_output` and `egress_check`
  classify or redact memory-derived drafts before they leave Codex/Yerhed.
- **Evidence-aware citations**: read/search tools return structured evidence
  spans so Codex can distinguish fresh reads, stale memory, assistant inference,
  and externally redacted sources.
- **Review-only automation templates**: morning brief, weekly dream cycle,
  weekly review, and project refresh protocols are included as prompts/docs, not
  hidden schedulers.
- **Privacy and leak guards**: privacy scans, git hooks, `gitleaks` support,
  brain-root push blocking, external repo guards, and copied-memory scanners.
- **No background runtime**: no daemon, cron job, launchd job, watcher, cloud
  sync, automatic push, or hosted service.

## What It Is Not

Yerhed is not a replacement for Codex, a vector database, a transcript miner, a
cloud memory service, a DLP system, a compliance product, or an autonomous
assistant that contacts people. It does not bypass Codex approvals, sandboxing,
connector safety, or your own review gates.

Memory is context, not permission to act.

## Safety Snapshot

This is alpha local software. Use it at your own risk.

- The repo contains code, docs, tests, and generic templates. Real memory should
  live outside the repo in your private brain root.
- Keep real `USER.md`, `SOUL.md`, `MEMORY.md`, brain notes, live automation
  records, `.codex` runtime files, `.env` files, secrets, and transcript dumps
  out of git.
- Yerhed has **No Send / No Network** behavior in its hook and MCP tools.
  Egress helpers classify drafts; they do not send, post, publish, invite, push,
  or call third-party services.
- Guardrails are best-effort accident-prevention tools, not DLP, not a security
  boundary, and not a guarantee that private memory cannot leak.
- Do not use it with credentials, regulated data, client data, workplace secrets,
  or anything you cannot afford to expose.
- Yerhed is provided under the MIT License with **No Warranty** and no liability.

Read [SECURITY.md](SECURITY.md) and [THREAT_MODEL.md](THREAT_MODEL.md) before
using this with real notes. For emergency disable and full removal, see
[docs/disable.md](docs/disable.md).

## Quickstart

Requirements: Python 3.11+, Git, Codex with MCP support, and optionally
`gitleaks` for local secret scanning.

```sh
git clone https://github.com/zorkary/codex-yerhed-starter.git yerhed
cd yerhed
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

Initialize a local brain root and local-only context files:

```sh
scripts/init_brain.sh
scripts/init_local_context.sh
```

Register the stdio MCP server with Codex:

```sh
codex mcp add yerhed -- "$PWD/.venv/bin/python" "$PWD/mcp/server.py"
```

Optionally install the tiny prompt hook and global boot card:

```sh
scripts/install_hook.sh
scripts/install_global_bootstrap.sh
```

Run smoke checks:

```sh
scripts/check_structure.sh
scripts/smoke_mcp_tools.sh
scripts/smoke_what_matters_now.sh
python -m unittest discover -s tests -v
scripts/privacy_scan.sh
```

Start a fresh Codex chat and ask it to use Yerhed. The expected first Yerhed tool
call is:

```text
yerhed.bootstrap_context
```

## Portable Paths

Override defaults when needed:

```sh
export YERHED_REPO="$PWD"
export YERHED_BRAIN_ROOT="$HOME/Personal/Yerhed/brain"
export CODEX_HOME="$HOME/.codex"
```

Fresh installs work with an empty brain. For an unknown repo, the intended flow
is: bootstrap Yerhed, search for existing project memory, inspect the repo if no
memory exists, and create or propose a project page only when the repo should
survive the current chat.

## How The Pieces Fit

```text
Codex chat
  -> optional hook/global boot card reminds Codex Yerhed exists
  -> yerhed.bootstrap_context loads compact operating context
  -> MCP tools search/read/write plain Markdown under allowed roots
  -> update/egress/evidence policies decide what can be written or shared

Yerhed repo
  -> instructions, policies, MCP server, scripts, tests, templates

Brain root
  -> private Markdown memory: people, projects, concepts, ideas, sources, logs
```

The repo is the operating layer. The brain root is private memory. The boundary
is intentionally sharp.

## Common Workflows

The MCP surface is designed around a compact bootstrap followed by narrow reads
and policy-backed writes when the conversation actually needs them.

- Use `search`, `read_project`, and `read_file` for grounded memory retrieval.
- Use `what_matters_now`, `morning_brief`, and automation prompts for local,
  review-only current-state summaries.
- Use `closeout_check` and structured write helpers for durable local memory
  updates. Write helpers commit locally and never push.
- Use `prepare_external_output` or `egress_check` before sharing memory-derived
  text through Slack, email, GitHub, public docs, posts, calendar invites, or
  other third-party surfaces.
- Use evidence helpers to label current reads, stale memory, assistant inference,
  and redacted evidence without faking citation authority.
- Use graph helpers to validate wikilinks, resolver entries, and salience.

See [TOOLS.md](TOOLS.md) for the full MCP surface and
[config/update-policy.md](config/update-policy.md) for write behavior. After MCP
tool changes, Codex may need a fresh session or app restart before new tools
appear.

## Memory Writes

Yerhed separates "this is useful context" from "this should become durable
memory."

- **Write** when the user explicitly asks to remember/save/update, or when a
  non-sensitive repo/project closeout changes durable state.
- **Propose first** for sensitive, ambiguous, inferred, relationship, health,
  legal, financial, or broad behavior changes.
- **Refuse** silent background writes, writes outside allowed roots, pushes,
  remotes, cloud sync, schedulers, or third-party side effects.

Git push remains outside the memory tool layer.

## External Sharing And Evidence

External surfaces include Slack, email, GitHub issues/comments/PRs, public docs,
posts, calendar invites, and third-party messages. Yerhed's egress guard returns
`allow`, `ask`, `redact`, or `block`; it never sends or posts.

Codex can render citation-looking UI, but rendering is not proof. Yerhed's MCP
reads/searches return `evidence_spans`; citation UI should be generated only for
current, server-validated `verified_current_turn` spans. Stale memory,
assistant inference, and redacted evidence should be labeled in prose instead.

## Obsidian Compatibility

The brain root can be opened as an Obsidian vault for visual browsing. Obsidian
is optional; Yerhed does not depend on Obsidian Sync or plugins.

```sh
scripts/install_obsidian_graph_settings.sh
```

The script writes ignored local config at `<brain-root>/.obsidian/graph.json`.
See [docs/obsidian.md](docs/obsidian.md) for graph filters and conventions.

## Automation Templates

`automations/` contains review-only protocols for Morning Brief, Weekly Dream
Cycle, Weekly Review, and Project Refresh. They are prompts and docs, not live
automation records. They do not create cron, launchd, daemons, shell watchers,
emails, calendar events, pushes, or external side effects.

## Privacy Checks

Install repo hooks in any checkout you plan to commit from. Existing hooks are
preserved and restored by the uninstaller when possible:

```sh
scripts/install_git_hooks.sh
scripts/uninstall_git_hooks.sh
```

Run release checks manually before sharing:

```sh
git status --short
scripts/privacy_scan.sh
scripts/git_privacy_guard.sh pre-commit
scripts/git_privacy_guard.sh pre-push
scripts/memory_leak_scan.sh --repo . --mode all --profile self
gitleaks detect --source . --redact --no-banner
git ls-files
```

For other repos that may contain copied Yerhed memory:

```sh
scripts/memory_leak_scan.sh --repo /path/to/repo --mode staged
scripts/install_external_repo_guard.sh /path/to/repo
scripts/uninstall_external_repo_guard.sh /path/to/repo
```

For a git-backed brain root, install a pre-push blocker:

```sh
scripts/install_brain_git_guard.sh --brain-root "$YERHED_BRAIN_ROOT"
scripts/uninstall_brain_git_guard.sh --brain-root "$YERHED_BRAIN_ROOT"
```

## Customization

Templates become local ignored files:

- `USER.example.md` -> `USER.md`: profile, preferences, active anchors.
- `SOUL.example.md` -> `SOUL.md`: voice, tone, boundaries.
- `MEMORY.example.md` -> `MEMORY.md`: operating decisions and conventions.

Common customization points:

- `ACCESS_POLICY.md`: local safety policy.
- `HEARTBEAT.md`: review rhythms and quiet hours.
- `config/paths.md`: repo and brain-root conventions.
- `config/update-policy.md`: when Codex writes, proposes, or skips memory.
- `config/egress-policy.md`: what can leave Yerhed/Codex.

The useful version is sparse, grounded, and maintained through real use rather
than filled with invented facts up front.

## Related Work

Yerhed is doc-first and Obsidian-compatible. It takes inspiration from
[GBrain](https://github.com/garrytan/gbrain)-style local knowledge graph
patterns, but does not depend on GBrain.

If you want a more retrieval-engine-oriented memory system, also look at
[MemPalace](https://github.com/MemPalace/mempalace). Yerhed has a different
bias: curated Markdown, explicit policy, Codex MCP tools, and reviewable local
writes rather than making verbatim transcript retrieval the center of the
system.

## Status

Yerhed is an alpha local experiment and starter repo, not a managed service.
Review scripts before installing hooks, keep real memory out of git, run privacy
checks before sharing anything, and use it at your own risk.

MIT licensed.
