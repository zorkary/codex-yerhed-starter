# Dream Cycle Protocol

Manual protocol and Codex Automation prompt source for background-style reflection without hidden background work.

Dream Cycle is the review-only layer for emergent discovery and graph gardening. Live memory writes should still handle obvious links, entity updates, and resolver updates at write time; Dream Cycle catches what accumulated, drifted, duplicated, or was missed.

## Inputs

- recent brain-root changes
- `inbox/`
- active `projects/`
- `projects/open-loops.md`
- `RESOLVER.md`
- high-salience or baseline salience-map pages
- `SOUL.md`, `USER.md`, and `MEMORY.md` when contradictions or Active Anchors may be involved
- current Codex task summaries when explicitly provided

## Required Startup

1. Use Yerhed.
2. Prefer Yerhed MCP when available.
3. Call `yerhed.bootstrap_context` first and retain its tool affordance map, `active_anchors`, and `salience_map`.
4. Use `yerhed.search`, `yerhed.read_file`, `yerhed.read_project`, `yerhed.salience_map`, `yerhed.resolve_entity`, `yerhed.suggest_links`, `yerhed.suggest_links_for_review_set`, `yerhed.propose_entity_page`, and `yerhed.validate_wikilinks` as needed.
5. If MCP is unavailable, read this file plus `AGENTS.md`, `MEMORY.md`, `HEARTBEAT.md`, `config/paths.md`, and `config/update-policy.md`, then perform the same review manually against the brain root.

## Required Graph-Gardening Audit

Every Dream Cycle run must include an explicit graph-gardening section. It may say `None` for a field, but it must not omit the field.

Minimum required fields:

- broken links
- duplicate/near-duplicate entity pages
- missing entity pages
- missing resolver entries
- stale aliases
- stale salience / Active Anchor promotion-demotion candidates
- graph hygiene warnings
- new wikilink candidates
- ambiguous/sensitive link candidates requiring operator approval
- applied safe link/entity updates
- skipped link/entity updates with reason

The `new wikilink candidates` field is mandatory even when no candidates exist. A Dream Cycle run that only calls `suggest_links` on its own summary has not completed the graph-gardening audit.

## Concrete Review Set

Minimum review set:

Run `yerhed.suggest_links_for_review_set` or an equivalent per-file sweep over this set:

- files changed in the brain root since the previous Dream Cycle marker, or since the last 7 days if no prior marker exists
- active project pages
- inbox notes
- `projects/open-loops.md`
- `RESOLVER.md`
- high-salience or baseline salience-map pages where relevant

If `suggest_links_for_review_set` is unavailable in an already-open Codex session, first consider that the MCP tool registry may be stale; start a fresh Codex session or restart the app after tool additions. If it is still unavailable, build the review set manually and run `yerhed.suggest_links` on each concrete file. When the tool supports it, pass source-path context to `suggest_links` so schema/example wikilink ignore semantics match `validate_wikilinks(ignore_schema_examples=true)`. Report the file list or a compact count by category so the sweep is auditable.

## Link And Entity Update Policy

- Treat candidate metadata as a safety gate. Only consider safe application when `requires_operator_approval=false`, `link_policy=auto`, Codex/LLM semantic review agrees the occurrence means that entity, and `config/update-policy.md` allows it.
- Treat `match_kind=review_only_alias`, `link_policy=review_only`, broad aliases, sensitive sources/targets, ambiguous mentions, and semantically risky mentions as proposal/review-only even when the string match is exact.
- Treat graph hygiene warnings as non-blocking cleanup signals: folders/frontmatter/tags classify notes, while wikilinks should represent semantic relationships. Do not add `[[Yerhed]]` storage links or category-hub links such as `[[Projects]]` to ordinary entity pages.
- Report `match_kind` and `link_policy` in graph-gardening output when useful.
- Propose exact diffs for ambiguous, sensitive, relationship-heavy, identity-heavy, or semantically risky links.
- Do not create sensitive or ambiguous entities silently.
- Do not create people, companion/pet, relationship, health, legal, financial, or family pages from casual mentions without owner confirmation or an explicit policy basis.
- Keep semantic durability and salience judgment in Codex/LLM. Yerhed MCP helpers are deterministic/auditable plumbing for known-entity lookup, collision checks, policy gates, local commits, and validation.
- Use `validate_wikilinks(ignore_schema_examples=true)` after any graph rewrite.
- Use `sync_resolver_to_frontmatter`, `batch_update_resolver_entries`, `set_canonical_entity_name`, `append_entity_update`, or `update_entity_links` only when their policy gates are satisfied.

## General Review Steps

1. Scan recent notes and active project files.
2. Run the graph-gardening audit over the concrete review set.
3. Identify duplicate, stale, contradictory, under-linked, or weakly sourced knowledge.
4. Look for repeated unlinked people, places, organizations, projects, concepts, ideas, companions/pets, or sources.
5. Propose missing entity pages, aliases, resolver entries, wikilinks, and duplicate-page cleanup.
6. Check Active Anchor promotion/demotion candidates and contradictions across `SOUL.md`, `USER.md`, `MEMORY.md`, `RESOLVER.md`, and salient pages.
7. Preserve raw source notes before distilling them unless the update policy explicitly prefers a distilled-only coverage ledger.
8. Emit a review summary with applied updates, proposed diffs, skipped updates, and next tasks.

## Output Format

Use these sections:

```md
# Weekly Dream Cycle - YYYY-MM-DD

## Graph Gardening
- broken links: ...
- duplicate/near-duplicate entity pages: ...
- missing entity pages: ...
- missing resolver entries: ...
- stale aliases: ...
- stale salience / Active Anchor promotion-demotion candidates: ...
- new wikilink candidates: ...
- ambiguous/sensitive link candidates requiring operator approval: ...
- applied safe link/entity updates: ...
- skipped link/entity updates with reason: ...

## Memory Distillations
...

## Contradictions And Drift
...

## Stale Notes
...

## Open Questions
...

## Suggested Next Codex Tasks
...

## Yerhed Memory Updates
- Applied: ...
- Proposed: ...
- Skipped: ...
```

## Forbidden In V1

- hidden writes
- hidden scheduling
- third-party outreach
- privileged side effects
- cron, launchd, daemons, shell watchers, or background services
- pushes or remote writes
- email sends, calendar writes, posts, or other external side effects
