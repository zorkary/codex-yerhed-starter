# Obsidian Graph View

Yerhed brain roots are Obsidian-compatible Markdown vaults. Obsidian is optional:
it is a viewer and editor for local Markdown, not Yerhed's source of truth.

Open your brain root as an Obsidian vault. By default, starter installs usually
use:

```text
~/Personal/Yerhed/brain
```

If you use a different location, set `YERHED_BRAIN_ROOT` or pass `--brain-root`
to the setup scripts.

## Why The Raw Graph Looks Noisy

Obsidian's Global Graph shows every Markdown file by default. Yerhed brain roots
contain active entity pages plus useful scaffolding:

- `README.md` files explain folders.
- `schema.md` documents conventions.
- `log.md` records continuity.
- `sources/` preserves raw/source material.
- `archive/` keeps retired material available for audits.

Those files are useful, but they are not the active memory graph.

## Recommended Graph Setup

Run the local installer once:

```sh
scripts/install_obsidian_graph_settings.sh
```

Or choose a brain root explicitly:

```sh
scripts/install_obsidian_graph_settings.sh --brain-root "$HOME/Personal/Yerhed/brain"
```

The installer writes only:

```text
<brain-root>/.obsidian/graph.json
```

The `.obsidian/` folder must stay ignored/local-only. The script does not edit
memory notes, does not push, does not use Obsidian Sync, and preserves unrelated
graph settings where possible.

After running the script, reopen or reload the vault if Obsidian does not pick up
the settings immediately.

## Default Quiet Graph Filter

The installer sets Graph view -> Filters -> Search files to:

```text
-(file:README OR file:_template OR file:schema OR file:log OR file:open-loops OR path:sources OR path:archive)
```

This hides scaffolding, source indexes, archive notes, and open-loop dashboards from the default Global Graph without hiding them from Yerhed itself. It also hides orphan dots by default so the first view emphasizes connected memory.

## Optional Entity-Only Filter

For a stricter view, paste this into Graph view -> Filters -> Search files:

```text
path:people OR path:projects OR path:concepts OR path:ideas OR path:places OR path:organizations
```

Use this when you want to inspect only the entity graph.

## Recommended Workflow

- Use Global Graph after installing the quiet filter for a connected salient memory map.
- Use Local Graph from `RESOLVER.md` to inspect the salience hub.
- Use Local Graph from entity pages such as `projects/example-project.md` or
  `concepts/example-concept.md` to inspect neighborhood context.
- Isolated dots are hidden by default; turn on orphans temporarily when auditing unlinked notes.
- Keep source files in `sources/`; they remain available for review, retrieval,
  and audits even when hidden from Global Graph.

## Semantic Links, Not Category Hubs

Yerhed uses folders, YAML frontmatter, and tags for classification. Obsidian
wikilinks should mean that two entities are meaningfully related.

Do not add `[[Projects]]`, `[[People]]`, `[[Concepts]]`, or similar category hubs
to ordinary entity notes. They create tidy-looking but low-signal starbursts in
the graph. Navigation maps are fine when useful, but tag them `moc` or `index`
and keep them filtered out of graph views.

Likewise, do not link notes to `[[projects/yerhed|Yerhed]]` merely because the
note is stored in the Yerhed brain. Keep Yerhed links for pages that are actually
about Yerhed as a system: memory policy, MCP/tools, automations, graph
infrastructure, Active Anchors, Open Loops, starter work, or closely related
product/system context.
