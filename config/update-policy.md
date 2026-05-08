# Yerhed Update Policy

Load Yerhed often; write memory only under clear triggers.

## Write When

- the user explicitly asks to remember, record, save, preserve, index, refresh, or update memory
- completed repo/project work changes non-sensitive durable docs, status, architecture, decisions, open loops, or next actions

## Closeout Behavior

For local repo/project work, non-sensitive durable closeouts are expected memory
writes. `closeout_check` should write and locally commit the narrow project-page
update by default when policy allows it.

Use `dry_run=true` only for a check-only pass. If a closeout is sensitive,
ambiguous, blocked by a dirty target, blocked by sandbox/approval limits, or
otherwise cannot be safely written, the result is `proposed` and must include
the exact proposed note and patch. Agents must show or summarize that proposal
instead of reporting only "proposed, not written."

## Ask Or Propose First

- sensitive or ambiguous facts
- inferred personal facts
- relationship, health, legal, or financial facts
- broad behavior changes
- pushes, remotes, schedules, sends, publishes, or third-party effects

## Never Write

- secrets
- ungrounded guesses as facts
- private memory into this operational repo
- files outside the configured repo or brain root

## Memory Linking And Durability Judgment

For brain-root writes, Codex should perform link and durability judgment at write time, not only during Dream Cycle.

- Link existing durable entities when they resolve unambiguously.
- Create or update entity pages only for explicit durable requests or clearly durable project/open-loop/decision context.
- Leave one-off mentions unlinked unless a page already exists and the link improves retrieval.
- Ask or propose first for ambiguous identity, sensitive personal facts, relationship-heavy notes, health/legal/financial context, or baseline anchor promotion.
- Use `inbox/` or a Dream Cycle proposal when something may become durable but is not yet clear.
- Add or update `RESOLVER.md` when future chats should recognize aliases, triggers, or salience for an entity.

Yerhed tools do not decide semantic durability. Codex should use them to inspect known entities and apply explicit changes, but the judgment to create, link, promote, or ask remains with Codex and the operator.

## High-Volume Memory Imports

When importing a classified memory batch with stable IDs:

- run `import_memory_plan` in dry-run mode first
- preserve every source ID in the coverage ledger, even when skipped or marked review
- write only to explicit destinations under the brain root
- use `do_not_share` for stronger-than-sensitive local material; `do-not-share` is accepted as a legacy alias
- use `owner_confirmed=true` only when the operator confirmed the explicit destination path despite fuzzy entity matches; fuzzy matches become informational when path identity is explicit
- use `set_canonical_entity_name` for canonical display renames and `replace_text` for exact substitutions instead of hand-written patch hunks
- use `sync_resolver_to_frontmatter` or review `validate_wikilinks` drift output when resolver/page metadata diverges
- run `validate_wikilinks` after writes
- never push the brain root
