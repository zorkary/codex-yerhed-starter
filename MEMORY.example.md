# MEMORY.md

Operational memory for Yerhed. Durable world/project knowledge belongs in the brain root.

## Current Decisions

- Codex is the execution engine.
- Yerhed is the private memory and operating layer.
- Source of truth is Markdown files.
- MCP is a local stdio tool layer, not a cloud service.

## Installation State

- Repo path:
- Brain root:
- MCP registration:
- Active automations:

## Egress Guard

- Use `egress_check` before external output when Yerhed memory contributed.
- Normal non-sensitive memory writes should remain low-friction under `config/update-policy.md`.

## Salience / Vault Conventions

- Yerhed supports Obsidian-compatible brain roots: YAML frontmatter, wikilinks, `RESOLVER.md` salience entries, and optional Obsidian editing without Obsidian runtime dependency.
- Live memory writes should resolve/link known entities immediately; Dream Cycle audits emergent graph structure later.
