# Yerhed Egress Policy

Yerhed memory is private by default. This policy governs memory-derived content leaving Codex/Yerhed for an external destination.

## Core Rule

Before sending, posting, publishing, commenting, scheduling, or otherwise sharing output outside the operator's local Codex/Yerhed context, check whether Yerhed memory contributed to the draft.

If Yerhed memory contributed, run or mentally apply `egress_check` before the external action.

## External Destinations

External destinations include Slack, email/Gmail, GitHub issues/comments/PRs, public docs, posts, calendar invites, third-party messages, and any shared repository or document.

Internal Codex chat responses and private Yerhed notes do not require a blocking prompt by default.

## Sensitivity Labels

Optional Markdown frontmatter:

```yaml
---
sensitivity: public | private | archival | sensitive | do_not_share
---
```

If no label exists, treat memory as `private`.

People, inbox, archive, and raw source notes are treated as at least `sensitive` unless explicitly labeled lower.

Do not run a mandatory whole-brain labeling pass in v1. Add labels only where they matter.

## Decisions

- `allow`: internal output, no Yerhed memory, or only public sources.
- `ask`: external output uses private memory without explicit owner approval.
- `redact`: useful draft includes unnecessary private or sensitive specifics; return a safer draft.
- `block`: do_not_share content, credentials, secrets, or raw sensitive personal notes are present.

Owner approval can allow private-memory egress, but it cannot override secrets or do_not_share labels. The legacy `do-not-share` spelling is accepted as an alias.


## Evidence And Local Paths

When Yerhed evidence spans are available, preserve them internally for review and provenance. Do not copy private local paths into Slack, email, GitHub comments, public docs, posts, calendar invites, or third-party messages by default.

`prepare_external_output` should redact private local paths from connector-bound drafts unless the owner explicitly approves sharing paths. Secrets and `do_not_share` content remain blocked even with owner approval.

Citation UI is for internal Codex/Yerhed answers backed by current-turn verified spans. External outputs should use prose evidence summaries or redacted references unless sharing exact paths is explicitly approved.

## Non-Goal

This is an accident-prevention guardrail, not a formal DLP system or security sandbox.
