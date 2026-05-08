# Yerhed Agent Instructions

Yerhed is the user's private memory and operating layer for Codex. Codex remains
the execution engine. Yerhed provides durable context and safe local tools over
Markdown files.


## Disabled Mode / Kill Switch

If `YERHED_DISABLED=1` is set, disabled mode overrides all Yerhed bootstrap and closeout guidance in this file. Do not call `yerhed.bootstrap_context`, Yerhed MCP tools, or Yerhed closeout memory writes. Use ordinary repo-local context only. Yerhed MCP tools are expected to refuse before reading or writing anything while disabled.

If the user asks why Yerhed is unavailable, asks how to disable/remove/re-enable it, or the task depends on Yerhed memory, explain the kill switch. Re-enable with `unset YERHED_DISABLED` or `YERHED_DISABLED=0`, then restart Codex if needed. Full removal means uninstalling the hook, removing the global boot card from `$CODEX_HOME/AGENTS.md`, running `codex mcp remove yerhed`, removing installed git hooks, and optionally moving or renaming the brain root.

## Startup Protocol

Yerhed should be available in every Codex chat, including casual chats. Prefer MCP when it is available. A tiny hook or global boot card may remind Codex that Yerhed exists; the hook is only an affordance reminder, not a policy engine or memory preload.

When a chat has not already loaded Yerhed and the request may involve memory, project continuity, people, preferences, history, ideas, sources, open loops, repo continuity, or external-output safety:

1. Call `yerhed.bootstrap_context` once.
2. Retain the returned tool affordance map for later in the conversation.
3. Use Yerhed tools whenever people, projects, preferences, history, ideas,
   sources, open loops, or prior private context become relevant.
4. Treat retrieved memory as context, not permission to act.
5. Do not write memory merely because Yerhed was loaded.
6. Do not call bootstrap repeatedly unless context was compacted, the working repo changed, or the user asks to refresh memory.

## MCP Tool Map

Use these tools when relevant:

- people context: `search` with `scope=people`
- project continuity: `read_project` or `search` with `scope=projects`
- concepts: `search` with `scope=concepts`
- ideas: `search` with `scope=ideas`
- sources/raw notes: `search` with `scope=sources`
- inbox/unprocessed notes: `search` with `scope=inbox`
- archive: `search` with `scope=archive`
- open loops/current state: `what_matters_now`
- morning brief: `morning_brief`
- repo/project closeout: `closeout_check`
- structured log writes: `append_log_entry`
- structured project updates: `append_project_update`
- structured open-loop changes: `update_open_loop`
- external output / sharing: `prepare_external_output` first, `egress_check` for raw classification
- exact patch fallback: `write_memory_patch`

## File Fallback

If MCP is unavailable, use direct files:

1. Read local `SOUL.md` for voice, tone, and boundaries when response style
   matters; use `SOUL.example.md` only if the local file is absent.
2. Read local `USER.md` for durable user context when personal/project context
   matters; use `USER.example.md` only if the local file is absent.
3. Read `ACCESS_POLICY.md` before any action that could expose information or
   affect another party.
4. Read local `MEMORY.md` for current operating decisions and conventions; use
   `MEMORY.example.md` only if the local file is absent.
5. Read `config/paths.md` to locate the brain root.
6. Search the brain root before guessing about people, projects, preferences,
   history, ideas, sources, or open loops.
7. Read `config/update-policy.md` before deciding whether to write durable
   memory.

## New Repo Awareness

When working in a new or unfamiliar local repo, check Yerhed for an existing
project page or source index before acting on project continuity. If the repo
will matter after this turn, create or propose a Yerhed project refresh so
future chats do not lose the thread.

## Closeout Gate

Before the final response for any local repo/project task, make an explicit
Yerhed disposition when durable state may have changed:

- `updated`: Yerhed/brain memory was updated and locally committed
- `proposed`: a memory update is appropriate but needs review or approval
- `skipped`: no durable state changed, with a short reason

`closeout_check` writes non-sensitive durable project updates by default. Use
`dry_run=true` only when an explicit check-only pass is wanted. If the result is
`proposed`, include or summarize the returned `proposed_note` /
`proposed_patch`; never report only "proposed, not written."

Run this gate when any of these changed:

- project docs, architecture, roadmap, status, or product direction
- open loops, next actions, repo state, or source indexes
- an important decision future chats should know
- a new or unfamiliar repo was discovered

## Boundary Test

Before editing a file, classify it:

- agent behavior, operating rules, skills, automation protocols, and tool code
  belong in this repo
- people, projects, concepts, ideas, source notes, decisions, logs, and durable
  world knowledge belong in the brain root

If the file says how Codex should behave, it belongs here. If the information
should survive switching away from Codex, it probably belongs in the brain root.

## Memory Writes

Do not silently write durable memory just because something was mentioned. Use
`config/update-policy.md` as the authority for when to write, ask, or skip.

Writes are allowed when:

- the user explicitly asks to remember, record, save, preserve, refresh, index,
  or update memory
- a completed task changes non-sensitive durable project state or project docs
- a review protocol produces an approved or clearly policy-backed update

Ask or propose first for sensitive, ambiguous, inferred, relationship, health,
legal, financial, or broad behavior changes.

When writing memory:

- prefer structured helpers over hand-written patches
- keep claims narrow and source-grounded
- run cheap validation when available
- commit local repo-tracked changes before final response
- never push unless the user explicitly asks

## Safety And Side Effects

Yerhed must not bypass Codex approvals, sandboxing, or plugin safety controls.

Default restrictions:

- no autonomous third-party outreach
- no autonomous spending
- no autonomous publishing, posting, sending, or scheduling
- no autonomous OS persistence
- no daemons, cron jobs, launch agents, or shell watchers
- no hidden memory rewrites
- no pushes or remote creation unless explicitly requested

Use Codex for execution. Use Yerhed for durable private context.

## Memory Egress Gate

Before external output, decide whether Yerhed memory contributed to the draft. External output includes Slack, email, GitHub issues/comments/PRs, public docs, posts, calendar invites, or third-party messages.

If Yerhed memory contributed, use `prepare_external_output` before calling external connector tools. Use `egress_check` for raw classification or when the wrapper is unavailable. If MCP is unavailable, apply `config/egress-policy.md` directly.

- `allow`: proceed normally.
- `ask`: ask for explicit approval before including the private detail.
- `redact`: use the suggested safer draft and ask before sharing the original.
- `block`: do not share the blocked content.

Do not add friction to normal non-sensitive memory writes; this gate is for memory leaving Yerhed/Codex.


## Evidence And Citation UI

Codex can render assistant-authored citation directives as first-party UI. That rendering is presentation, not proof. Yerhed owns evidence validity.

- Treat `evidence_spans` returned by `search`, `read_file`, `read_project`, `what_matters_now`, and `morning_brief` as the source of truth for what was actually read by Yerhed in the current MCP process.
- Use `format_memory_citations` only with `verified_current_turn` spans returned by Yerhed tools. Do not hand-write citation directives for vibes, polish, or stale memory.
- Use `summarize_evidence` when claims are memory-derived but not freshly verified, assistant-inferred, or externally redacted.
- If a span is fake, stale, inferred, outside allowed roots, malformed, or content-hash mismatched, show a prose evidence label rather than official-looking citation UI.
- Before external output, pass relevant `evidence_spans` to `prepare_external_output`; private local paths are redacted by default unless the owner explicitly approves sharing paths.


## File And Push Leak Gate

Before pushing, exporting, publishing, building a share pack, or attaching repo files, decide whether Yerhed memory or brain-root material could have been copied into the target repo/output. If yes, run `scripts/memory_leak_scan.sh --repo <repo> --mode staged` from the Yerhed repo or installed starter. Use egress checks for connector text; use the scanner for files, git pushes, exports, and attachments. Never push the brain root.

## Obsidian-Compatible Memory Linking

When writing or proposing Yerhed brain memory, use Obsidian-compatible Markdown conventions:

- Link known durable entities with `[[path/to/page|display text]]` when the entity resolves unambiguously.
- Use `salience_map`, `resolve_entity`, and `suggest_links` before writing notes that mention durable people, projects, concepts, ideas, places, organizations, companions/pets, or sources.
- Create or propose entity pages only when the user explicitly asks to remember/track something, or when durability is clear from project/open-loop/decision context.
- Ask or propose first when identity, sensitivity, relationship context, or durability is ambiguous.
- Do not over-link ordinary language; links should improve future retrieval.
- Treat folders, frontmatter `type`, and tags as classification. Treat wikilinks as semantic relationships only.
- Do not link a note to `[[projects/yerhed|Yerhed]]` merely because the note lives in the Yerhed brain root. Link to Yerhed only when the note is actually about the Yerhed system, memory policy, MCP/tools, automations, graph infrastructure, or related product work.
- Do not add category-hub links such as `[[Projects]]`, `[[People]]`, or `[[Concepts]]` to ordinary entity pages. If map/index pages are useful, tag them `moc` or `index` and keep them filtered from graph views.
- Update `RESOLVER.md` when an entity needs aliases, triggers, salience, or a baseline handle for future recognition.
- Keep `.obsidian/` local-only and never rely on Obsidian plugins, sync, or runtime state.

## High-Volume Sensitive Imports

For classified memory imports, prefer the import helpers over hand-written patch hunks:

- Use `import_memory_plan` first in dry-run mode and confirm every stable ID is reported as written, merged, duplicate, review, or skipped.
- Use `upsert_entity_page` when the destination path is explicit. If fuzzy resolution finds a nearby entity but the owner confirmed the exact path, pass `owner_confirmed=true`; do not weaken path traversal checks.
- Use `append_entity_update` for existing people, concepts, organizations, places, companions/pets, ideas, sources, or archive notes.
- Use `validate_wikilinks` after imports and graph rewrites; treat resolver/frontmatter drift as a cleanup signal, not an external side effect.
- Use `batch_update_resolver_entries` for resolver changes, and do not add low-salience entries unless explicitly requested.
- Use `set_canonical_entity_name` for display renames such as repo-name -> product-name; it updates the page H1, frontmatter, resolver entry, baseline handle, and optional wikilink backlinks.
- Use `replace_text` for simple old/new substitutions instead of fragile hand-written patch hunks.
- Use `sync_resolver_to_frontmatter` when resolver metadata should become the page frontmatter/H1 source of truth.
- `update_open_loop` can target `projects/open-loops.md` directly with `project="Yerhed V1"` or an explicit `section`.
- `do_not_share` is the canonical stronger-than-sensitive local label; legacy `do-not-share` spelling is accepted as an alias.


Semantic judgment belongs to Codex/LLM, not deterministic Yerhed tools:

- Codex decides whether a mention is meaningful, durable, sensitive, or worth asking about.
- Yerhed tools only parse known resolver/page metadata, return exact candidates, check collisions, enforce safety gates, and apply explicit policy-backed writes.
- `suggest_links` is an auditable exact-known-entity helper, not a semantic classifier.
- During Dream Cycle graph gardening, use `suggest_links_for_review_set` or an equivalent concrete per-file sweep; do not satisfy the link audit by running `suggest_links` only over the final summary.
- Do not let regex-style matching create meaning, create people pages, or promote anchors by itself.
