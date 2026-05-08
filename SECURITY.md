# Security Policy

Yerhed is a local experiment and starter kit, not a managed security
product. See [THREAT_MODEL.md](THREAT_MODEL.md) for trust boundaries, failure modes, mitigations, and residual risk.

## Supported Versions

Only the current `main` branch is considered supported. There are no supported
older releases in this starter repo unless release tags are added later.

## Reporting A Vulnerability

Please do not post sensitive vulnerability details in public issues, discussions,
pull requests, screenshots, or social posts.

During private beta, report issues privately through the same channel that gave
you access to the repository. For public releases, use GitHub private
vulnerability reporting if it is enabled. If no private channel is available,
open a minimal public issue asking for a private contact path, without including
exploit details, secrets, private memory, or reproduction data that could expose
someone's files.

Reports are handled on a best-effort basis. There is no bug bounty, no service
level agreement, no staffed security team, and no guarantee of a fix timeline.

## Scope

Useful reports include bugs where Yerhed may:

- read files outside configured roots
- write or commit files outside configured roots
- leak private paths, memory, or evidence spans into external drafts
- miss obvious copied-memory or secret patterns in the included guard scripts
- create unexpected network, scheduler, push, or third-party side effects

Out of scope:

- vulnerabilities caused by intentionally disabling or removing guardrails
- leaks caused by publishing real private memory despite the README warnings
- modified forks or local configurations that materially change the safety model
- issues in Codex, Git, GitHub, Obsidian, MCP clients, or other third-party tools

## No Security Guarantee

The privacy scans, memory leak guards, and egress helpers are best-effort
accident-prevention tools. They may contain bugs, false negatives, false
positives, or unsafe assumptions. They are not a security boundary, DLP system,
compliance product, or guarantee that private memory cannot leak.

The software is provided as-is under the MIT License, without warranty or
liability. Users are responsible for reviewing scripts, configuration, commits,
generated drafts, and external outputs before using or sharing them.

## Disable / Kill Switch

Set `YERHED_DISABLED=1` to make the hook emit disabled guidance and make MCP tools refuse before reads or writes. Re-enable with `unset YERHED_DISABLED` or `YERHED_DISABLED=0`, then restart Codex if needed. For full removal, uninstall the hook, remove the global boot card, run `codex mcp remove yerhed`, remove installed git hooks, and optionally move or rename the brain root.
