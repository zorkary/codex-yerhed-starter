# ACCESS_POLICY.md

Yerhed v1 is owner-only by default.

## Allowed

- read local Yerhed files
- search the configured brain root
- draft review-only notes
- commit local memory changes when update policy allows it

## Requires Explicit Approval

- sending, posting, publishing, scheduling, or spending
- contacting third parties
- creating remotes or pushing commits
- enabling recurring automations
- installing daemons, launch agents, cron jobs, or shell watchers

## Forbidden

- exposing private memory to third parties
- storing secrets in Markdown
- bypassing Codex approvals or sandboxing

## Memory Egress

Treat memory as private by default. Before sending, posting, publishing, commenting, or otherwise sharing external output that used Yerhed memory, run or apply `egress_check`.

If the result is `ask`, ask for explicit approval. If it is `redact`, provide the safer draft. If it is `block`, do not proceed. Secrets and `do-not-share` content cannot be overridden.
