#!/bin/sh
set -eu
REPO="${YERHED_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)}"
YERHED_PYTHON="${YERHED_PYTHON:-$REPO/.venv/bin/python}"
if [ ! -x "$YERHED_PYTHON" ]; then
  YERHED_PYTHON="${PYTHON:-python3}"
fi
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
BRAIN="$TMPDIR/brain"
mkdir -p "$BRAIN/archive" "$BRAIN/concepts" "$BRAIN/ideas" "$BRAIN/inbox" "$BRAIN/people" "$BRAIN/projects" "$BRAIN/companions" "$BRAIN/sources"
printf '# Open Loops\n\n## Current\n\n- Customize Yerhed starter.\n' > "$BRAIN/projects/open-loops.md"
printf '# Yerhed\n\nStarter project page.\n' > "$BRAIN/projects/yerhed.md"
printf '# Brain Log\n\n## Smoke\n\nTool smoke.\n' > "$BRAIN/log.md"
printf '# Example\n\nPrefers grounded work.\n' > "$BRAIN/people/example.md"
YERHED_REPO="$REPO" YERHED_BRAIN_ROOT="$BRAIN" PYTHONPATH="$REPO" "$YERHED_PYTHON" - <<'PY'
from yerhed_mcp.tools import append_entity_update, batch_update_resolver_entries, bootstrap_context, egress_check, format_memory_citations, import_memory_plan, morning_brief, prepare_external_output, read_project, replace_text, search, set_canonical_entity_name, suggest_links_for_review_set, summarize_evidence, sync_resolver_to_frontmatter, upsert_entity_page, validate_wikilinks, what_matters_now
bootstrap = bootstrap_context(prompt="smoke", cwd=".")
assert bootstrap["ok"]
assert "people context" in bootstrap["tool_affordance_map"]
assert "external output / sharing" in bootstrap["tool_affordance_map"]
assert "evidence citations" in bootstrap["tool_affordance_map"]
result = search("grounded", scope="people")
assert result["results"]
assert result["evidence_spans"]
assert callable(format_memory_citations)
assert callable(summarize_evidence)
assert read_project("yerhed")["ok"]
assert what_matters_now()["ok"]
assert morning_brief()["ok"]
egress = egress_check(destination="Slack", draft="Generic update.")
assert egress["ok"]
assert egress["disposition"] == "allow"
connector = prepare_external_output(destination="Slack", draft="Generic update.")
assert connector["ok"]
assert connector["may_use_connector"]
assert callable(set_canonical_entity_name)
assert callable(replace_text)
assert callable(upsert_entity_page)
assert callable(append_entity_update)
assert callable(import_memory_plan)
assert callable(suggest_links_for_review_set)
assert callable(validate_wikilinks)
assert callable(sync_resolver_to_frontmatter)
assert callable(batch_update_resolver_entries)

import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def _assert_server_lists_review_tool() -> None:
    env = os.environ.copy()
    repo = Path(env.get("YERHED_REPO") or ".")
    if str(repo) == ".":
        repo = Path.cwd()
    env["YERHED_REPO"] = str(repo)
    env["PYTHONPATH"] = str(repo) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    params = StdioServerParameters(command=sys.executable, args=[str(repo / "mcp" / "server.py")], env=env, cwd=str(repo))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            assert "suggest_links_for_review_set" in names, sorted(names)
            assert "format_memory_citations" in names, sorted(names)
            assert "summarize_evidence" in names, sorted(names)

asyncio.run(_assert_server_lists_review_tool())
print("Yerhed MCP tool smoke OK")
PY
