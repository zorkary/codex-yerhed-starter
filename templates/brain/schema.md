# Brain Schema

Suggested directories: people, projects, concepts, ideas, sources, inbox, archive, and log.md.

## Obsidian-Compatible Entity Notes

Yerhed brain roots are Obsidian-compatible Markdown vaults, but Obsidian is optional.

Entity pages should use simple frontmatter:

```md
---
type: concept
aliases: ["Example Alias"]
auto_link_aliases: []
review_only_aliases: ["Broad Alias"]
triggers: ["when this topic appears"]
tags: ["yerhed", "entity/concept"]
salience: medium
load_policy: triggered
sensitivity: private
# stronger local options: sensitive, do_not_share; archival is for retired/source material
baseline_handle: "One sentence handle for bootstrap/resolver use."
---
```

Use `[[path/to/page|display text]]` for durable links when the entity is known and unambiguous. Do not over-link ordinary language. Canonical titles may be safe link candidates; aliases default to review-only evidence unless repeated in `auto_link_aliases`. Broad aliases belong in `review_only_aliases`; triggers are review-only if surfaced.

Recommended entity folders: `people/`, `projects/`, `concepts/`, `ideas/`, `places/`, `organizations/`, `sources/`, `inbox/`, and `archive/`.

`RESOLVER.md` is the salience map and map-of-content. It should contain aliases, triggers, salience, load policy, and baseline handles for entities Codex should recognize naturally.

## Import Coverage

For classified memory imports with stable IDs, keep a coverage ledger under `sources/` or `archive/`. Each source ID should resolve to one of: written, merged, duplicate, review, or skipped. Run wikilink validation after imports and keep resolver entries limited to entities that should be easy for Codex to recognize later.

## Companion Entities

Use `companions/` for durable companion animal context. `pet`, `pets`, and `companion animal` normalize to the `companion` entity type. Do not force companion animals into `people/` unless there is a deliberate reason.

## Resolver Frontmatter Sync

`RESOLVER.md` is the salience map. Entity page frontmatter should generally agree with resolver salience, load policy, canonical title, aliases, triggers, sensitivity, sharing policy, and egress labels. `validate_wikilinks` reports resolver/frontmatter drift; `sync_resolver_to_frontmatter` can apply one resolver entry back to a page.
