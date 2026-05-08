# TOOLS.md

## MCP Server

```sh
.venv/bin/python mcp/server.py
```

Register with Codex:

```sh
codex mcp add yerhed -- "$PWD/.venv/bin/python" "$PWD/mcp/server.py"
```

## Tools

- `bootstrap_context`
- `search`
- `read_file`
- `read_project`
- `what_matters_now`
- `morning_brief`
- `closeout_check`: closeout gate for durable project changes. Non-sensitive
  project updates write and locally commit by default; use `dry_run=true` for a
  check-only pass. Any `proposed` result includes `proposed_note` and
  `proposed_patch`, and the caller must show the proposal instead of reporting
  only "proposed, not written".
- `append_log_entry`
- `append_project_update`
- `update_open_loop`
- `prepare_external_output`
- `format_memory_citations`: emit Codex-compatible citation UI only for verified current-turn evidence spans
- `summarize_evidence`: label current, stale, inferred, or redacted evidence without citation UI
- `write_memory_patch`

## MCP Tool Refresh

Codex sessions may cache the MCP server process and tool registry when the chat starts. After adding, removing, or renaming MCP tools, start a fresh Codex session or restart the app before expecting the new tool name to appear in `tool_search` or the live `yerhed` namespace. `scripts/smoke_mcp_tools.sh` verifies the stdio server itself lists the expected tools.

## Environment

- `YERHED_REPO` overrides repo root
- `YERHED_BRAIN_ROOT` overrides brain root

## Egress Check

Use `prepare_external_output` before external connector use when Yerhed memory contributed to a draft. It wraps `egress_check`, returns whether the connector may be used, and provides a safe draft or approval question when needed. It never sends, posts, publishes, or writes externally.

Use `egress_check` directly when you only need raw classification. Inputs: destination, draft, optional source paths, optional user intent. Output: `allow`, `ask`, `redact`, or `block`, plus reasons and a suggested safe draft when useful.


## Evidence-Aware Citations

Yerhed read/search tools return structured `evidence_spans` with path, line range, sensitivity, source kind, loaded time, evidence status, evidence id, and content hash.

Use `format_memory_citations(evidence_spans)` only for current-turn verified spans returned by Yerhed. It omits fake paths, stale spans, inferred claims, malformed ranges, outside-root paths, and content-hash mismatches. Use `summarize_evidence(evidence_spans)` when citation UI is not appropriate.

Codex renders citation UI; Yerhed validates whether the evidence is real. Do not hand-write citation directives.


## Salience And Entity Tools

Additional salience/entity tools:

- `salience_map`: parse `RESOLVER.md` aliases, triggers, salience, load policy, and baseline handles.
- `resolve_entity`: resolve a name/query before linking a durable entity.
- `suggest_links`: propose Obsidian wikilinks for unambiguous known entities; never writes.
- `suggest_links_for_review_set`: run exact known-entity wikilink suggestions across the required Dream Cycle review set and return an auditable graph-gardening report; never writes.
- `propose_entity_page`: propose frontmatter, page body, and resolver entry for a new entity; never writes.
- `create_entity_page`: conservative policy-backed entity page create; refuses possible duplicates.
- `set_canonical_entity_name`: rename display/canonical entity names across H1, frontmatter, resolver entry, baseline handle, and optional wikilink backlinks.
- `upsert_entity_page`: explicit-path create/update for high-volume imports; `owner_confirmed=true` can override fuzzy duplicate warnings while path safety still hard-fails.
- `append_entity_update`: append a section to any existing brain note, not only project pages.
- `import_memory_plan`: dry-run or write a classified import plan with stable ID coverage and a local coverage ledger under `sources/` or `archive/`.
- `validate_wikilinks`: report unresolved links, self-links, resolver/page mismatches, and resolver/frontmatter drift in an Obsidian-friendly shape.
- `sync_resolver_to_frontmatter`: apply one resolver entry back onto page frontmatter/H1, local commit, never push.
- `update_resolver_entry`: policy-backed resolver entry write; refuses missing target pages and alias collisions.
- `batch_update_resolver_entries`: policy-backed resolver batch update; skips low-salience entries unless explicitly included.
- `update_entity_links`: policy-backed wikilink update for one existing brain note; refuses ambiguous or unresolved links.

Supported search scopes now include `places`, `organizations`, and `companions`/`pets` in addition to the original brain folders.

## Deterministic Tool Boundary

Alias link policy: candidate rows include `match_kind` (`canonical_title`, `alias`, `review_only_alias`, or future `trigger`) and `requires_operator_approval`. Canonical titles can be safe candidates; aliases are review-only unless listed in `auto_link_aliases`; broad aliases belong in `review_only_aliases`.

Semantic judgment belongs to Codex/LLM, not deterministic Yerhed tools:

- Codex decides whether a mention is meaningful, durable, sensitive, or worth asking about.
- Yerhed tools only parse known resolver/page metadata, return exact candidates, check collisions, enforce safety gates, and apply explicit policy-backed writes.
- `suggest_links` is an auditable exact-known-entity helper, not a semantic classifier.
- Do not let regex-style matching create meaning, create people pages, or promote anchors by itself.

## Hook-Assisted Bootstrap

Install the optional tiny Codex hook with:

```sh
scripts/install_hook.sh
```

The hook only reminds Codex that Yerhed exists and when to call `yerhed.bootstrap_context`; it does not read memory, call MCP tools, write files, or search the brain root.

Install the compact global boot card with:

```sh
scripts/install_global_bootstrap.sh
```

The full policy remains in `AGENTS.md`; repo-local `AGENTS.md` files should stay project-specific.
