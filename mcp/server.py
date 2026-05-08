#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - fallback for alternate installs
    from fastmcp import FastMCP  # type: ignore

from yerhed_mcp.disabled import disabled_response, is_yerhed_disabled
from yerhed_mcp.tools import (
    append_log_entry as _append_log_entry,
    append_project_update as _append_project_update,
    append_entity_update as _append_entity_update,
    batch_update_resolver_entries as _batch_update_resolver_entries,
    bootstrap_context as _bootstrap_context,
    closeout_check as _closeout_check,
    create_entity_page as _create_entity_page,
    egress_check as _egress_check,
    format_memory_citations as _format_memory_citations,
    import_memory_plan as _import_memory_plan,
    replace_text as _replace_text,
    morning_brief as _morning_brief,
    propose_entity_page as _propose_entity_page,
    prepare_external_output as _prepare_external_output,
    read_file as _read_file,
    read_project as _read_project,
    resolve_entity as _resolve_entity,
    salience_map as _salience_map,
    search as _search,
    suggest_links as _suggest_links,
    suggest_links_for_review_set as _suggest_links_for_review_set,
    summarize_evidence as _summarize_evidence,
    upsert_entity_page as _upsert_entity_page,
    set_canonical_entity_name as _set_canonical_entity_name,
    sync_resolver_to_frontmatter as _sync_resolver_to_frontmatter,
    update_entity_links as _update_entity_links,
    update_open_loop as _update_open_loop,
    update_resolver_entry as _update_resolver_entry,
    validate_wikilinks as _validate_wikilinks,
    what_matters_now as _what_matters_now,
    write_memory_patch as _write_memory_patch,
)

mcp = FastMCP("yerhed")


def _call_tool(fn, *args, **kwargs) -> dict[str, Any]:
    if is_yerhed_disabled():
        return disabled_response()
    return fn(*args, **kwargs)


@mcp.tool(name="bootstrap_context", description="Return Yerhed baseline context, tool affordances, write policy, and file fallback instructions.")
def bootstrap_context(prompt: str = "", cwd: str = "") -> dict[str, Any]:
    return _call_tool(_bootstrap_context, prompt=prompt, cwd=cwd)


@mcp.tool(name="search", description="Search the private Yerhed brain root by query and optional scope.")
def search(query: str, scope: str = "all", limit: int = 10) -> dict[str, Any]:
    return _call_tool(_search, query=query, scope=scope, limit=limit)


@mcp.tool(name="salience_map", description="Return parsed Yerhed RESOLVER.md salience entries and warnings.")
def salience_map(include_page_records: bool = False) -> dict[str, Any]:
    return _call_tool(_salience_map, include_page_records=include_page_records)


@mcp.tool(name="resolve_entity", description="Resolve a person, project, concept, place, organization, source, or idea before linking.")
def resolve_entity(query: str, entity_type: str = "") -> dict[str, Any]:
    return _call_tool(_resolve_entity, query=query, entity_type=entity_type)


@mcp.tool(name="suggest_links", description="Suggest Obsidian wikilinks for unambiguous known Yerhed entities; does not write.")
def suggest_links(draft: str, allowed_entity_types: list[str] | str | None = None) -> dict[str, Any]:
    return _call_tool(_suggest_links, draft=draft, allowed_entity_types=allowed_entity_types)


@mcp.tool(name="suggest_links_for_review_set", description="Run exact known-entity link suggestions across the Dream Cycle review set; does not write.")
def suggest_links_for_review_set(
    since_days: int = 7,
    max_files: int = 120,
    allowed_entity_types: list[str] | str | None = None,
    include_drafts: bool = False,
    include_changed_files: bool = True,
    include_active_projects: bool = True,
    include_inbox: bool = True,
    include_open_loops: bool = True,
    include_resolver: bool = True,
    include_salience_pages: bool = True,
) -> dict[str, Any]:
    return _call_tool(_suggest_links_for_review_set,
        since_days=since_days,
        max_files=max_files,
        allowed_entity_types=allowed_entity_types,
        include_drafts=include_drafts,
        include_changed_files=include_changed_files,
        include_active_projects=include_active_projects,
        include_inbox=include_inbox,
        include_open_loops=include_open_loops,
        include_resolver=include_resolver,
        include_salience_pages=include_salience_pages,
    )


@mcp.tool(name="propose_entity_page", description="Return a proposed entity page and resolver entry; does not write.")
def propose_entity_page(
    entity_type: str,
    name: str,
    context_summary: str,
    aliases: list[str] | str | None = None,
    triggers: list[str] | str | None = None,
    salience: str = "medium",
    sensitivity: str = "private",
    load_policy: str = "triggered",
) -> dict[str, Any]:
    return _call_tool(_propose_entity_page,
        entity_type=entity_type,
        name=name,
        context_summary=context_summary,
        aliases=aliases,
        triggers=triggers,
        salience=salience,
        sensitivity=sensitivity,
        load_policy=load_policy,
    )




@mcp.tool(name="format_memory_citations", description="Emit Codex-compatible citation UI only for verified current-turn Yerhed evidence spans.")
def format_memory_citations(evidence_spans: list[dict[str, Any]] | dict[str, Any] | str | None = None, max_age_seconds: int = 1800) -> dict[str, Any]:
    return _call_tool(_format_memory_citations, evidence_spans=evidence_spans, max_age_seconds=max_age_seconds)


@mcp.tool(name="summarize_evidence", description="Summarize whether Yerhed evidence is current, stale, inferred, or redacted without rendering citation UI.")
def summarize_evidence(evidence_spans: list[dict[str, Any]] | dict[str, Any] | str | None = None) -> dict[str, Any]:
    return _call_tool(_summarize_evidence, evidence_spans=evidence_spans)


@mcp.tool(name="read_file", description="Read a file under the Yerhed repo or brain root only.")
def read_file(path: str, max_chars: int = 20000) -> dict[str, Any]:
    return _call_tool(_read_file, path=path, max_chars=max_chars)


@mcp.tool(name="read_project", description="Read a matching project page from the Yerhed brain root.")
def read_project(project: str) -> dict[str, Any]:
    return _call_tool(_read_project, project=project)


@mcp.tool(name="what_matters_now", description="Return a compact grounded Yerhed current-state summary.")
def what_matters_now() -> dict[str, Any]:
    return _call_tool(_what_matters_now, )


@mcp.tool(name="morning_brief", description="Run the review-only Yerhed morning brief protocol.")
def morning_brief() -> dict[str, Any]:
    return _call_tool(_morning_brief, )


@mcp.tool(name="closeout_check", description="Close out durable repo/project changes; writes non-sensitive memory by default and proposes exact notes when blocked.")
def closeout_check(
    repo_path: str,
    work_summary: str,
    durable_state_change_summary: str,
    changed_files: list[str] | str | None = None,
    dry_run: bool = False,
    commit_message: str = "",
) -> dict[str, Any]:
    return _call_tool(_closeout_check,
        repo_path=repo_path,
        work_summary=work_summary,
        durable_state_change_summary=durable_state_change_summary,
        changed_files=changed_files,
        dry_run=dry_run,
        commit_message=commit_message,
    )


@mcp.tool(name="append_log_entry", description="Append a section to brain/log.md, commit locally, and never push.")
def append_log_entry(
    title: str,
    body: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
) -> dict[str, Any]:
    return _call_tool(_append_log_entry,
        title=title,
        body=body,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
    )


@mcp.tool(name="append_project_update", description="Append a section to a brain project page, commit locally, and never push.")
def append_project_update(
    project: str,
    heading: str,
    body: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
) -> dict[str, Any]:
    return _call_tool(_append_project_update,
        project=project,
        heading=heading,
        body=body,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
    )


@mcp.tool(name="update_open_loop", description="Add, remove, or replace an Open Loops bullet, commit locally, and never push.")
def update_open_loop(
    project: str,
    action: str,
    text: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    replacement_text: str = "",
    section: str = "",
) -> dict[str, Any]:
    return _call_tool(_update_open_loop,
        project=project,
        action=action,
        text=text,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        replacement_text=replacement_text,
        section=section,
    )


@mcp.tool(name="egress_check", description="Classify whether memory-derived content is safe to include in an external output.")
def egress_check(
    destination: str,
    draft: str,
    source_paths: list[str] | str | None = None,
    user_intent: str = "",
) -> dict[str, Any]:
    return _call_tool(_egress_check,
        destination=destination,
        draft=draft,
        source_paths=source_paths,
        user_intent=user_intent,
    )


@mcp.tool(name="prepare_external_output", description="Preflight a Yerhed-memory-derived draft before using an external connector; never sends or posts.")
def prepare_external_output(
    destination: str,
    draft: str,
    source_paths: list[str] | str | None = None,
    user_intent: str = "",
    evidence_spans: list[dict[str, Any]] | dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    return _call_tool(_prepare_external_output,
        destination=destination,
        draft=draft,
        source_paths=source_paths,
        user_intent=user_intent,
        evidence_spans=evidence_spans,
    )


@mcp.tool(name="create_entity_page", description="Create a policy-backed Yerhed entity page, commit locally, and never push.")
def create_entity_page(
    entity_type: str,
    name: str,
    context_summary: str,
    sensitivity: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    aliases: list[str] | str | None = None,
    triggers: list[str] | str | None = None,
    salience: str = "medium",
    load_policy: str = "triggered",
) -> dict[str, Any]:
    return _call_tool(_create_entity_page,
        entity_type=entity_type,
        name=name,
        context_summary=context_summary,
        sensitivity=sensitivity,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        aliases=aliases,
        triggers=triggers,
        salience=salience,
        load_policy=load_policy,
    )


@mcp.tool(name="set_canonical_entity_name", description="Rename an entity display name across H1, frontmatter, resolver entry, and optional wikilink backlinks.")
def set_canonical_entity_name(
    path: str,
    name: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    aliases: list[str] | str | None = None,
    triggers: list[str] | str | None = None,
    baseline_handle: str = "",
    update_backlinks: bool = False,
) -> dict[str, Any]:
    return _call_tool(_set_canonical_entity_name,
        path=path,
        name=name,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        aliases=aliases,
        triggers=triggers,
        baseline_handle=baseline_handle,
        update_backlinks=update_backlinks,
    )


@mcp.tool(name="replace_text", description="Apply exact old/new text substitutions under Yerhed repo or brain root, commit locally, and never push.")
def replace_text(
    path: str,
    replacements: list[dict[str, Any]] | dict[str, Any] | str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    expected_count: int = 1,
) -> dict[str, Any]:
    return _call_tool(_replace_text,
        path=path,
        replacements=replacements,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        expected_count=expected_count,
    )


@mcp.tool(name="upsert_entity_page", description="Create or update an explicit-path Yerhed entity page for high-volume imports, commit locally, and never push.")
def upsert_entity_page(
    path: str,
    entity_type: str,
    name: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    aliases: list[str] | str | None = None,
    triggers: list[str] | str | None = None,
    salience: str = "medium",
    load_policy: str = "triggered",
    sensitivity: str = "private",
    baseline_handle: str = "",
    sections: dict[str, str] | list[dict[str, str]] | str | None = None,
    body: str = "",
    owner_confirmed: bool = False,
    sharing_policy: str = "",
    egress: str = "",
) -> dict[str, Any]:
    return _call_tool(_upsert_entity_page,
        path=path,
        entity_type=entity_type,
        name=name,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        aliases=aliases,
        triggers=triggers,
        salience=salience,
        load_policy=load_policy,
        sensitivity=sensitivity,
        baseline_handle=baseline_handle,
        sections=sections,
        body=body,
        owner_confirmed=owner_confirmed,
        sharing_policy=sharing_policy,
        egress=egress,
    )


@mcp.tool(name="append_entity_update", description="Append a section to any existing Yerhed brain note, commit locally, and never push.")
def append_entity_update(
    path: str,
    heading: str,
    body: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
) -> dict[str, Any]:
    return _call_tool(_append_entity_update,
        path=path,
        heading=heading,
        body=body,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
    )


@mcp.tool(name="import_memory_plan", description="Import a classified memory plan with stable ID coverage, dry-run by default, local commits only.")
def import_memory_plan(
    items: list[dict[str, Any]] | dict[str, Any] | str,
    policy_basis: str = "",
    source_summary: str = "",
    commit_message: str = "Import memory plan",
    dry_run: bool = True,
    commit_strategy: str = "single",
    ledger_path: str = "sources/import-ledgers/memory-import.md",
) -> dict[str, Any]:
    return _call_tool(_import_memory_plan,
        items=items,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        dry_run=dry_run,
        commit_strategy=commit_strategy,
        ledger_path=ledger_path,
    )


@mcp.tool(name="validate_wikilinks", description="Validate Obsidian wikilinks and resolver/page consistency in the Yerhed brain root.")
def validate_wikilinks(ignore_schema_examples: bool = True) -> dict[str, Any]:
    return _call_tool(_validate_wikilinks, ignore_schema_examples=ignore_schema_examples)


@mcp.tool(name="update_resolver_entry", description="Add or update one policy-backed RESOLVER.md salience entry, commit locally, and never push.")
def update_resolver_entry(
    entity_type: str,
    name: str,
    path: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    aliases: list[str] | str | None = None,
    triggers: list[str] | str | None = None,
    salience: str = "medium",
    load_policy: str = "triggered",
    baseline_handle: str = "",
    sensitivity: str = "",
    sharing_policy: str = "",
    egress: str = "",
) -> dict[str, Any]:
    return _call_tool(_update_resolver_entry,
        entity_type=entity_type,
        name=name,
        path=path,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        aliases=aliases,
        triggers=triggers,
        salience=salience,
        load_policy=load_policy,
        baseline_handle=baseline_handle,
        sensitivity=sensitivity,
        sharing_policy=sharing_policy,
        egress=egress,
    )


@mcp.tool(name="batch_update_resolver_entries", description="Add or update multiple RESOLVER.md salience entries in one local commit; low salience is skipped unless explicitly included.")
def batch_update_resolver_entries(
    entries: list[dict[str, Any]] | dict[str, Any] | str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    include_low_salience: bool = False,
) -> dict[str, Any]:
    return _call_tool(_batch_update_resolver_entries,
        entries=entries,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        include_low_salience=include_low_salience,
    )


@mcp.tool(name="sync_resolver_to_frontmatter", description="Sync one entity page frontmatter and H1 from its RESOLVER.md entry, commit locally, and never push.")
def sync_resolver_to_frontmatter(
    path: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
) -> dict[str, Any]:
    return _call_tool(_sync_resolver_to_frontmatter,
        path=path,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
    )


@mcp.tool(name="update_entity_links", description="Apply unambiguous Obsidian wikilinks to one brain note, commit locally, and never push.")
def update_entity_links(
    path: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    allowed_entity_types: list[str] | str | None = None,
) -> dict[str, Any]:
    return _call_tool(_update_entity_links,
        path=path,
        policy_basis=policy_basis,
        source_summary=source_summary,
        commit_message=commit_message,
        allowed_entity_types=allowed_entity_types,
    )


@mcp.tool(name="write_memory_patch", description="Apply an exact policy-backed Yerhed or brain patch, commit locally, and never push.")
def write_memory_patch(
    disposition: str,
    policy_basis: str,
    source_summary: str,
    patch: str,
    commit_message: str,
) -> dict[str, Any]:
    return _call_tool(_write_memory_patch,
        disposition=disposition,
        policy_basis=policy_basis,
        source_summary=source_summary,
        patch=patch,
        commit_message=commit_message,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
