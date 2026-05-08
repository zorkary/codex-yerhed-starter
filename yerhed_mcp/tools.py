from __future__ import annotations

import datetime as _dt
import hashlib
import difflib
import json
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".sh",
    ".py",
}

SKIP_DIRS = {".git", ".venv", "__pycache__", ".cache", ".tmp"}

GRAPH_SCAFFOLD_FILENAMES = {"README.md", "_template.md", "schema.md", "index.md"}
GRAPH_CATEGORY_HUB_TARGETS = {
    "archive",
    "archives",
    "companion",
    "companions",
    "concept",
    "concepts",
    "idea",
    "ideas",
    "organization",
    "organizations",
    "people",
    "person",
    "place",
    "places",
    "project",
    "projects",
    "source",
    "sources",
}
YERHED_LINK_TARGET = "projects/yerhed"
YERHED_GRAPH_LINK_ALLOWLIST = {
    "concepts/active-anchors.md",
    "concepts/memory-compression-policy.md",
    "projects/open-loops.md",
    "projects/yerhed.md",
}
YERHED_SEMANTIC_CONTEXT_TERMS = {
    "active anchor",
    "active anchors",
    "automation",
    "brain",
    "bootstrap",
    "codex",
    "dream cycle",
    "egress",
    "graph",
    "graph-gardening",
    "local-first",
    "mcp",
    "memory",
    "morning brief",
    "obsidian",
    "open loop",
    "open loops",
    "policy",
    "resolver",
    "salience",
    "starter",
    "tool",
    "tools",
    "vault",
    "weekly review",
    "wikilink",
    "wikilinks",
}
GENERIC_AUTO_LINK_PHRASES = {
    "ai",
    "llm",
    "gpt",
    "chatgpt",
    "claude",
    "opus",
    "codex",
    "agent",
    "agents",
    "memory",
    "project",
    "repo",
    "source",
    "idea",
    "concept",
    "person",
    "people",
    "place",
    "organization",
    "user",
    "operator",
}

BRAIN_SCOPES = {
    "all": ".",
    "people": "people",
    "projects": "projects",
    "concepts": "concepts",
    "ideas": "ideas",
    "places": "places",
    "organizations": "organizations",
    "companions": "companions",
    "pets": "companions",
    "sources": "sources",
    "inbox": "inbox",
    "archive": "archive",
}

BRAIN_TOP_LEVEL = {
    "RESOLVER.md",
    "schema.md",
    "log.md",
    "archive",
    "concepts",
    "ideas",
    "places",
    "organizations",
    "companions",
    "inbox",
    "people",
    "projects",
    "sources",
}

YERHED_TOP_LEVEL = {
    ".gitignore",
    "pyproject.toml",
    "ACCESS_POLICY.md",
    "AGENTS.md",
    "HEARTBEAT.md",
    "MEMORY.example.md",
    "README.md",
    "SOUL.example.md",
    "TOOLS.md",
    "USER.example.md",
    "automations",
    "config",
    "evals",
    "mcp",
    "scripts",
    "skills",
    "tests",
    "templates",
    "yerhed_mcp",
}

SENSITIVE_HINTS = {
    "diagnosis",
    "medical",
    "health",
    "therapy",
    "legal",
    "lawyer",
    "lawsuit",
    "financial",
    "bank",
    "debt",
    "tax",
    "relationship",
    "partner",
    "family",
    "romantic",
    "contact third",
    "third party",
}


SENSITIVITY_LEVELS = {
    "public": 0,
    "private": 1,
    "archival": 1,
    "sensitive": 2,
    "do_not_share": 3,
}

SENSITIVITY_ALIASES = {
    "do_not_share": "do_not_share",
    "do-not-share": "do_not_share",
    "donotshare": "do_not_share",
    "do not share": "do_not_share",
    "no_share": "do_not_share",
    "noshare": "do_not_share",
}


def _normalize_sensitivity(value: Any, default: str = "private") -> str:
    raw = str(value or default or "").strip().lower().strip('"\'')
    if not raw:
        return ""
    alias_key = raw.replace("_", "-")
    normalized = SENSITIVITY_ALIASES.get(raw) or SENSITIVITY_ALIASES.get(alias_key)
    if not normalized:
        normalized = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
        normalized = SENSITIVITY_ALIASES.get(normalized, normalized)
    return normalized if normalized in SENSITIVITY_LEVELS else ""


def _sensitivity_error() -> str:
    labels = ", ".join(sorted(SENSITIVITY_LEVELS | {"do-not-share"}))
    return f"sensitivity must be one of {labels}"


EVIDENCE_STATUSES = {
    "verified_current_turn",
    "memory_derived_stale",
    "assistant_inferred",
    "external_redacted",
}
DEFAULT_EVIDENCE_TTL_SECONDS = 30 * 60
_EVIDENCE_REGISTRY: dict[str, dict[str, Any]] = {}

SENSITIVE_SOURCE_DIRS = {"people", "inbox", "archive", "sources"}

EXTERNAL_DESTINATION_HINTS = {
    "slack",
    "email",
    "gmail",
    "github",
    "issue",
    "pull request",
    "pr comment",
    "comment",
    "public",
    "publish",
    "post",
    "tweet",
    "x.com",
    "calendar",
    "invite",
    "third party",
    "external",
    "linkedin",
    "discord",
}

INTERNAL_DESTINATION_HINTS = {
    "codex",
    "internal",
    "local",
    "private note",
    "owner",
    "operator",
    "self",
    "yerhed",
    "brain",
}

OWNER_OVERRIDE_HINTS = {
    "include this private",
    "include the private",
    "ok to include",
    "okay to include",
    "safe to include",
    "share this private",
    "send this private",
    "explicitly include",
    "you can include",
}

SECRET_PATTERNS = [
    re.compile(r"BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY", re.I),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]+"),
    re.compile(r"(?:ANTHROPIC|OPENAI|GITHUB|SLACK)_API_KEY", re.I),
]


def yerhed_repo() -> Path:
    return Path(os.environ.get("YERHED_REPO", str(Path(__file__).resolve().parents[1]))).expanduser().resolve()


def brain_root() -> Path:
    return Path(os.environ.get("YERHED_BRAIN_ROOT", str(Path.home() / "Personal" / "Yerhed" / "brain"))).expanduser().resolve()


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def _root_lexical_aliases(root_resolved: Path) -> list[Path]:
    aliases = [root_resolved]
    root_text = str(root_resolved)
    for resolved_prefix, alias_prefix in (("/private/var", "/var"), ("/private/tmp", "/tmp")):
        if root_text == resolved_prefix or root_text.startswith(resolved_prefix + "/"):
            aliases.append(Path(alias_prefix + root_text[len(resolved_prefix):]))
    return aliases


def _safe_existing_file_under_root(path: Path | str, root: Path | str) -> Path | None:
    """Resolve an existing regular file without following in-root symlinks."""
    try:
        root_resolved = Path(root).expanduser().resolve()
        raw = Path(path).expanduser()
        candidate = raw if raw.is_absolute() else root_resolved / raw
        lexical = _lexical_absolute(candidate)
    except OSError:
        return None

    rel = None
    current_base = None
    for base in _root_lexical_aliases(root_resolved):
        try:
            rel = lexical.relative_to(base)
            current_base = base
            break
        except ValueError:
            continue
    if rel is None or current_base is None:
        return None

    current = current_base
    for part in rel.parts:
        current = current / part
        try:
            if current.is_symlink():
                return None
        except OSError:
            return None

    try:
        resolved = lexical.resolve(strict=True)
    except (FileNotFoundError, OSError):
        return None
    if not _is_under(resolved, root_resolved):
        return None
    if not resolved.is_file() or resolved.is_symlink():
        return None
    return resolved


def _safe_existing_file(path: Path | str) -> Path | None:
    for root in (yerhed_repo(), brain_root()):
        resolved = _safe_existing_file_under_root(path, root)
        if resolved is not None:
            return resolved
    return None


def _read_text(path: Path, max_chars: int | None = None) -> str:
    safe_path = _safe_existing_file(path)
    if safe_path is None:
        return ""
    try:
        text = safe_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars].rstrip() + "\n... [truncated]"
    return text


def _read_text_with_line_span(path: Path, max_chars: int | None = None) -> tuple[str, int, int]:
    text = _read_text(path)
    if not text:
        return "", 0, 0
    if max_chars is not None and len(text) > max_chars:
        prefix = text[:max_chars].rstrip()
        loaded_line_end = len(prefix.splitlines())
        return prefix + "\n... [truncated]", 1, max(1, loaded_line_end)
    return text, 1, len(text.splitlines())

def _file_excerpt(path: Path, max_chars: int = 1800, tail: bool = False) -> dict[str, Any]:
    safe_path = _safe_existing_file(path)
    if safe_path is None:
        return {"path": str(path), "exists": False, "excerpt": ""}
    text = _read_text(safe_path)
    if tail:
        lines = text.splitlines()
        excerpt = "\n".join(lines[-60:])
    else:
        excerpt = text[:max_chars]
        if len(text) > max_chars:
            excerpt = excerpt.rstrip() + "\n... [truncated]"
    line_count = len(text.splitlines())
    if tail:
        start_line = max(1, line_count - len(excerpt.splitlines()) + 1)
        end_line = line_count
    else:
        start_line = 1 if line_count else 0
        end_line = min(line_count, len(excerpt.splitlines())) if line_count else 0
    evidence_span = _make_evidence_span(safe_path, start_line, end_line, "bootstrap baseline excerpt") if start_line and end_line else None
    return {
        "path": str(safe_path),
        "exists": True,
        "line_count": line_count,
        "excerpt": excerpt,
        "evidence_span": evidence_span,
    }


def _first_existing(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def _summary_files() -> list[tuple[Path, bool]]:
    repo = yerhed_repo()
    brain = brain_root()
    return [
        (repo / "AGENTS.md", False),
        (_first_existing(repo / "MEMORY.md", repo / "MEMORY.example.md"), False),
        (_first_existing(repo / "USER.md", repo / "USER.example.md"), False),
        (repo / "config" / "paths.md", False),
        (repo / "config" / "update-policy.md", False),
        (brain / "projects" / "open-loops.md", False),
        (brain / "projects" / "yerhed.md", False),
        (brain / "log.md", True),
    ]


def _tool_affordance_map() -> dict[str, str]:
    return {
        "people context": "use search(query, scope='people')",
        "project continuity": "use read_project(project) or search(query, scope='projects')",
        "concepts": "use search(query, scope='concepts')",
        "ideas": "use search(query, scope='ideas')",
        "places": "use search(query, scope='places')",
        "organizations": "use search(query, scope='organizations')",
        "companions / pets": "use search(query, scope='companions')",
        "sources/raw notes": "use search(query, scope='sources')",
        "inbox/unprocessed notes": "use search(query, scope='inbox')",
        "archive": "use search(query, scope='archive')",
        "salience map": "use salience_map() to inspect aliases, triggers, and entity handles",
        "entity resolution": "use resolve_entity(query, entity_type) before linking ambiguous people/projects/concepts/places/organizations",
        "link suggestions": "use suggest_links(draft) before writing Obsidian-style brain notes",
        "Dream Cycle graph review": "use suggest_links_for_review_set() to run exact known-entity link suggestions across the required Dream Cycle review set",
        "entity page proposals": "use propose_entity_page(entity_type, name, context_summary) for reviewable new entity pages",
        "entity page writes": "use create_entity_page(...) for conservative new pages; use upsert_entity_page(...) for explicit-path imports with owner_confirmed=true",
        "generic entity updates": "use append_entity_update(path, heading, body, ...) for any existing brain note",
        "memory import plans": "use import_memory_plan(...) for high-volume classified memory imports and coverage ledgers",
        "link validation": "use validate_wikilinks(...) after imports or graph rewrites",
        "resolver updates": "use update_resolver_entry(...) for one entry or batch_update_resolver_entries(...) for policy-backed batches",
        "entity link writes": "use update_entity_links(...) for policy-backed wikilink updates",
        "open loops/current state": "use what_matters_now()",
        "morning brief": "use morning_brief()",
        "closeout": "use closeout_check(repo_path, work_summary, durable_state_change_summary, changed_files)",
        "external output / sharing": "use prepare_external_output(destination, draft, source_paths, user_intent, evidence_spans) before Slack/email/GitHub/public docs/posts when Yerhed memory contributed; use egress_check for raw classification",
        "evidence citations": "use format_memory_citations(evidence_spans) only for verified_current_turn spans returned by Yerhed tools; use summarize_evidence(evidence_spans) for stale, inferred, or redacted evidence",
        "structured log writes": "use append_log_entry(title, body, policy_basis, source_summary, commit_message)",
        "structured project updates": "use append_project_update(project, heading, body, policy_basis, source_summary, commit_message)",
        "structured open-loop changes": "use update_open_loop(project, action, text, policy_basis, source_summary, commit_message, replacement_text)",
        "exact patch writes": "use write_memory_patch(disposition='updated', policy_basis, source_summary, patch, commit_message) only when a structured helper does not fit",
    }


def bootstrap_context(prompt: str = "", cwd: str = "") -> dict[str, Any]:
    """Return fixed Yerhed baseline context and tool affordances."""
    return {
        "ok": True,
        "system": "Yerhed",
        "repo": str(yerhed_repo()),
        "brain_root": str(brain_root()),
        "cwd": cwd,
        "prompt_hint": prompt[:500],
        "baseline_context": [_file_excerpt(path, tail=tail) for path, tail in _summary_files()],
        "active_anchors": active_anchors(),
        "salience_map": _compact_salience_map(),
        "tool_affordance_map": _tool_affordance_map(),
        "write_policy_reminder": (
            "Loading Yerhed is not permission to write. Write only when config/update-policy.md "
            "says the update is expected/allowed, or when the user explicitly asks to remember, "
            "record, save, preserve, refresh, index, or update. Non-sensitive durable repo/project "
            "state changes should get a closeout disposition and may be updated directly; "
            "external output may require egress_check before sharing memory-derived content."
        ),
        "evidence_policy_reminder": (
            "Codex may render citation UI, but Yerhed owns evidence validity. Never hand-write "
            "citation directives for vibes, polish, or stale memory. Use format_memory_citations "
            "only with verified_current_turn evidence spans returned by Yerhed tools; use "
            "summarize_evidence for stale, inferred, or externally redacted claims."
        ),
        "fallback_instructions": {
            "if_mcp_unavailable": [
                f"Read {yerhed_repo() / 'AGENTS.md'}",
                f"Read local {yerhed_repo() / 'MEMORY.md'} if present, otherwise MEMORY.example.md",
                f"Read local {yerhed_repo() / 'USER.md'} when user/project context matters, otherwise USER.example.md",
                f"Read {yerhed_repo() / 'config' / 'paths.md'}",
                f"Read {yerhed_repo() / 'config' / 'update-policy.md'} before writes",
                f"Search {brain_root()} with rg or scripts/brain_search.sh before guessing",
                "Use RESOLVER.md salience entries and Obsidian-style wikilinks when writing brain memory",
            ]
        },
    }



VALID_ENTITY_TYPES = {
    "person": "people",
    "people": "people",
    "project": "projects",
    "projects": "projects",
    "concept": "concepts",
    "concepts": "concepts",
    "idea": "ideas",
    "ideas": "ideas",
    "place": "places",
    "places": "places",
    "organization": "organizations",
    "organizations": "organizations",
    "org": "organizations",
    "orgs": "organizations",
    "companion": "companions",
    "companions": "companions",
    "pet": "companions",
    "pets": "companions",
    "companion animal": "companions",
    "companion_animal": "companions",
    "source": "sources",
    "sources": "sources",
    "archive": "archive",
}
ENTITY_DIR_TO_TYPE = {
    "people": "person",
    "projects": "project",
    "concepts": "concept",
    "ideas": "idea",
    "places": "place",
    "organizations": "organization",
    "companions": "companion",
    "sources": "source",
    "archive": "archive",
}
VALID_LOAD_POLICIES = {"baseline", "triggered", "archival"}
VALID_SALIENCE = {"high", "medium", "low"}


def _normalize_entity_type(entity_type: str | None) -> str | None:
    if not entity_type or not str(entity_type).strip():
        return None
    key = _slug(str(entity_type)).replace("-", "")
    lookup = {
        "person": "people",
        "people": "people",
        "project": "projects",
        "projects": "projects",
        "concept": "concepts",
        "concepts": "concepts",
        "idea": "ideas",
        "ideas": "ideas",
        "place": "places",
        "places": "places",
        "organization": "organizations",
        "organizations": "organizations",
        "org": "organizations",
        "orgs": "organizations",
        "companion": "companions",
        "companions": "companions",
        "pet": "companions",
        "pets": "companions",
        "companionanimal": "companions",
        "source": "sources",
        "sources": "sources",
        "archive": "archive",
    }
    return lookup.get(key)


def _canonical_entity_type(entity_type: str | None) -> str | None:
    directory = _normalize_entity_type(entity_type)
    if directory is None:
        return None
    return ENTITY_DIR_TO_TYPE.get(directory, directory.rstrip("s"))


def _norm_entity_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _strip_wikilink(text: str) -> str:
    value = (text or "").strip()
    if value.startswith("[[") and value.endswith("]]"):
        value = value[2:-2]
    if "|" in value:
        value = value.split("|", 1)[1]
    return value.strip()


def _parse_scalar_or_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip().strip('"\'') for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            line = line[2:].strip()
        parts.extend(piece.strip().strip('"\'') for piece in line.split(","))
    return [_strip_wikilink(part) for part in parts if part]


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = -1
    for idx in range(1, min(len(lines), 80)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end == -1:
        return {}, text
    data: dict[str, Any] = {}
    current_key = ""
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - ") and current_key:
            data.setdefault(current_key, []).append(raw.strip()[2:].strip().strip('"\''))
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        current_key = key.strip().lower().replace("-", "_")
        value = value.strip()
        if value == "":
            data[current_key] = []
        elif value.startswith("[") and value.endswith("]"):
            data[current_key] = _parse_scalar_or_list(value)
        else:
            data[current_key] = value.strip('"\'')
    body = "\n".join(lines[end + 1 :])
    return data, body


def _extract_h1(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or fallback
    return fallback


def _section_lines(text: str, heading: str, level: int = 2) -> list[tuple[int, str]]:
    marker = "#" * level + " " + heading.lower()
    lines = text.splitlines()
    start = -1
    for idx, line in enumerate(lines):
        if line.strip().lower() == marker:
            start = idx + 1
            break
    if start == -1:
        return []
    end = len(lines)
    for idx in range(start, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## ") and level == 2:
            end = idx
            break
        if stripped.startswith("#" * level + " ") and level > 2:
            end = idx
            break
    return [(idx + 1, lines[idx]) for idx in range(start, end)]


def active_anchors() -> list[dict[str, Any]]:
    repo = yerhed_repo()
    user_path = _first_existing(repo / "USER.md", repo / "USER.example.md")
    anchors: list[dict[str, Any]] = []
    for line_no, line in _section_lines(_read_text(user_path), "Active Anchors"):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        text = stripped[2:].strip()
        if not text or text.lower() in {"none", "none yet", "not set"}:
            continue
        label, _, detail = text.partition(":")
        anchors.append(
            {
                "label": label.strip() if detail else text,
                "summary": detail.strip() if detail else text,
                "text": text,
                "source_path": str(user_path),
                "line": line_no,
            }
        )
    return anchors


def _parse_kv_lines(lines: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    current_key = ""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        if stripped.startswith("  - ") and current_key:
            values.setdefault(current_key, []).append(stripped[4:].strip())
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        current_key = key.strip().lower().replace(" ", "_").replace("-", "_")
        value = value.strip()
        if current_key in {"aliases", "triggers", "tags", "review_only_aliases", "auto_link_aliases"}:
            values[current_key] = _parse_scalar_or_list(value)
        else:
            values[current_key] = _strip_wikilink(value.strip('"\''))
    return values


def _resolver_sections() -> list[tuple[str, list[str], int]]:
    resolver = brain_root() / "RESOLVER.md"
    text = _read_text(resolver)
    lines = _section_lines(text, "Salience Map")
    if not lines:
        return []
    sections: list[tuple[str, list[str], int]] = []
    current_title = ""
    current_lines: list[str] = []
    current_line_no = 0
    for line_no, raw in lines:
        stripped = raw.strip()
        if stripped.startswith("### "):
            if current_title:
                sections.append((current_title, current_lines, current_line_no))
            current_title = stripped[4:].strip()
            current_lines = []
            current_line_no = line_no
        elif current_title:
            current_lines.append(raw)
    if current_title:
        sections.append((current_title, current_lines, current_line_no))
    return sections


def _normalize_salience_entry(title: str, values: dict[str, Any], line_no: int, source: str = "resolver") -> tuple[dict[str, Any] | None, str | None]:
    raw_type = str(values.get("type", "")).strip()
    entity_dir = _normalize_entity_type(raw_type)
    if entity_dir is None:
        return None, f"{title}: unsupported or missing type {raw_type!r}"
    path = str(values.get("path", "")).strip()
    if not path:
        return None, f"{title}: missing path"
    if path.startswith("[[") and path.endswith("]]"):
        path = path[2:-2].split("|", 1)[0]
    if path.endswith(".md"):
        rel_path = path
    else:
        rel_path = f"{path}.md" if "/" in path else f"{entity_dir}/{_slug(path)}.md"
    if rel_path.startswith("/") or ".." in Path(rel_path).parts:
        return None, f"{title}: path escapes brain root"
    salience = str(values.get("salience", "medium") or "medium").strip().lower()
    if salience not in VALID_SALIENCE:
        salience = "medium"
    load_policy = str(values.get("load_policy", values.get("load policy", "triggered")) or "triggered").strip().lower().replace("-", "_")
    if load_policy not in VALID_LOAD_POLICIES:
        load_policy = "triggered"
    sensitivity = _normalize_sensitivity(
        values.get("sensitivity") or values.get("privacy") or values.get("sharing_policy") or values.get("egress"),
        default="",
    )
    entry = {
        "title": title,
        "type": ENTITY_DIR_TO_TYPE.get(entity_dir, entity_dir.rstrip("s")),
        "directory": entity_dir,
        "path": rel_path,
        "aliases": _parse_scalar_or_list(values.get("aliases")),
        "review_only_aliases": _parse_scalar_or_list(values.get("review_only_aliases")),
        "auto_link_aliases": _parse_scalar_or_list(values.get("auto_link_aliases")),
        "triggers": _parse_scalar_or_list(values.get("triggers")),
        "salience": salience,
        "load_policy": load_policy,
        "sensitivity": sensitivity,
        "sharing_policy": str(values.get("sharing_policy", "") or "").strip(),
        "egress": str(values.get("egress", "") or "").strip(),
        "baseline_handle": str(values.get("baseline_handle", values.get("baseline handle", "")) or "").strip(),
        "tags": _parse_scalar_or_list(values.get("tags")),
        "source": source,
        "source_path": str(brain_root() / "RESOLVER.md"),
        "line": line_no,
    }
    return entry, None


def _resolver_entries() -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    for title, body_lines, line_no in _resolver_sections():
        entry, warning = _normalize_salience_entry(title, _parse_kv_lines(body_lines), line_no)
        if warning:
            warnings.append(warning)
            continue
        if entry:
            entries.append(entry)
    return entries, warnings



def _is_graph_scaffold_path(rel: str) -> bool:
    name = Path(rel).name
    return name in GRAPH_SCAFFOLD_FILENAMES


def _record_is_graph_scaffold(record: dict[str, Any]) -> bool:
    return _is_graph_scaffold_path(str(record.get("path", "")))


def _frontmatter_entity_record(path: Path) -> dict[str, Any] | None:
    try:
        rel = path.relative_to(brain_root()).as_posix()
    except ValueError:
        return None
    parts = Path(rel).parts
    if not parts or parts[0] not in ENTITY_DIR_TO_TYPE:
        return None
    text = _read_text(path, max_chars=12000)
    fm, body = _parse_frontmatter(text)
    title = str(fm.get("title") or fm.get("name") or _extract_h1(body or text, path.stem.replace("-", " ").title()))
    salience = str(fm.get("salience") or "medium").lower()
    if salience not in VALID_SALIENCE:
        salience = "medium"
    load_policy = str(fm.get("load_policy") or "triggered").lower().replace("-", "_")
    if load_policy not in VALID_LOAD_POLICIES:
        load_policy = "triggered"
    sensitivity = _normalize_sensitivity(
        fm.get("sensitivity") or fm.get("privacy") or fm.get("sharing_policy") or fm.get("egress"),
        default="private",
    )
    return {
        "title": title,
        "type": ENTITY_DIR_TO_TYPE[parts[0]],
        "directory": parts[0],
        "path": rel,
        "aliases": _parse_scalar_or_list(fm.get("aliases")),
        "review_only_aliases": _parse_scalar_or_list(fm.get("review_only_aliases")),
        "auto_link_aliases": _parse_scalar_or_list(fm.get("auto_link_aliases")),
        "triggers": _parse_scalar_or_list(fm.get("triggers")),
        "salience": salience,
        "load_policy": load_policy,
        "sensitivity": sensitivity,
        "sharing_policy": str(fm.get("sharing_policy") or "").strip(),
        "egress": str(fm.get("egress") or "").strip(),
        "baseline_handle": str(fm.get("baseline_handle") or "").strip(),
        "tags": _parse_scalar_or_list(fm.get("tags")),
        "source": "page",
        "source_path": str(path),
        "line": 1,
    }


def _entity_page_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for directory in ENTITY_DIR_TO_TYPE:
        root = brain_root() / directory
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md")):
            rel = _brain_rel_from_existing_path(path)
            if rel and _is_graph_scaffold_path(rel):
                continue
            record = _frontmatter_entity_record(path)
            if record:
                records.append(record)
    return records


def _dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    for record in records:
        path = str(record.get("path", ""))
        if not path:
            continue
        existing = by_path.get(path)
        if existing is None or existing.get("source") != "resolver":
            by_path[path] = record
        elif record.get("source") == "resolver":
            by_path[path] = record
    return list(by_path.values())


def _all_entity_records(entity_type: str | None = None) -> list[dict[str, Any]]:
    directory = _normalize_entity_type(entity_type)
    records = _dedupe_records(_resolver_entries()[0] + _entity_page_records())
    if directory:
        records = [record for record in records if record.get("directory") == directory]
    return records



def _linkable_entity_records(entity_type: str | None = None) -> list[dict[str, Any]]:
    return [record for record in _all_entity_records(entity_type) if not _record_is_graph_scaffold(record)]


def _auto_link_phrase_allowed(name: str) -> bool:
    clean = _strip_wikilink(name).strip()
    if not clean:
        return False
    return _norm_entity_key(clean) not in GENERIC_AUTO_LINK_PHRASES


def _policy_alias_keys(record: dict[str, Any], field: str) -> set[str]:
    return {_norm_entity_key(str(item)) for item in _parse_scalar_or_list(record.get(field)) if _norm_entity_key(str(item))}


def _link_candidate_names(record: dict[str, Any], include_triggers: bool = False) -> list[dict[str, Any]]:
    auto_aliases = _policy_alias_keys(record, "auto_link_aliases")
    review_only_aliases = _policy_alias_keys(record, "review_only_aliases")
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(text: str, match_kind: str, link_policy: str, reason: str) -> None:
        clean = _strip_wikilink(text).strip()
        key = _norm_entity_key(clean)
        if not clean or not key:
            return
        dedupe_key = (key, match_kind)
        if dedupe_key in seen:
            return
        seen.add(dedupe_key)
        candidates.append({"text": clean, "match_kind": match_kind, "link_policy": link_policy, "reason": reason})

    add(str(record.get("title", "")), "canonical_title", "auto", "canonical title match")
    add(Path(str(record.get("path", ""))).stem.replace("-", " "), "canonical_title", "auto", "canonical path-stem match")
    for alias in record.get("aliases", []) or []:
        clean = _strip_wikilink(str(alias)).strip()
        key = _norm_entity_key(clean)
        if not clean or not key:
            continue
        if key in review_only_aliases:
            add(clean, "review_only_alias", "review_only", "alias is review_only")
        elif key in auto_aliases:
            add(clean, "alias", "auto", "alias is explicitly auto_link")
        elif not _auto_link_phrase_allowed(clean):
            add(clean, "review_only_alias", "review_only", "alias is generic review_only")
        else:
            add(clean, "review_only_alias", "review_only", "alias lacks explicit auto_link policy")
    if include_triggers:
        for trigger in record.get("triggers", []) or []:
            add(str(trigger), "trigger", "review_only", "trigger matches are review_only")
    return candidates


def _candidate_names(record: dict[str, Any], include_triggers: bool = True) -> list[str]:
    names = [str(record.get("title", "")), Path(str(record.get("path", ""))).stem.replace("-", " ")]
    names.extend(str(item) for item in record.get("aliases", []) or [])
    if include_triggers:
        names.extend(str(item) for item in record.get("triggers", []) or [])
    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        clean = _strip_wikilink(name).strip()
        key = _norm_entity_key(clean)
        if clean and key and key not in seen:
            seen.add(key)
            unique.append(clean)
    return unique


def _entity_link_target(record: dict[str, Any]) -> str:
    path = str(record.get("path", "")).strip()
    if path.endswith(".md"):
        return path[:-3]
    return path or str(record.get("title", ""))


def _display_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": record.get("title", ""),
        "type": record.get("type", ""),
        "path": record.get("path", ""),
        "aliases": record.get("aliases", []),
        "review_only_aliases": record.get("review_only_aliases", []),
        "auto_link_aliases": record.get("auto_link_aliases", []),
        "triggers": record.get("triggers", []),
        "salience": record.get("salience", "medium"),
        "load_policy": record.get("load_policy", "triggered"),
        "sensitivity": record.get("sensitivity", ""),
        "sharing_policy": record.get("sharing_policy", ""),
        "egress": record.get("egress", ""),
        "baseline_handle": record.get("baseline_handle", ""),
        "source": record.get("source", ""),
        "link_target": _entity_link_target(record),
    }


def salience_map(include_page_records: bool = False) -> dict[str, Any]:
    entries, warnings = _resolver_entries()
    if include_page_records:
        entries = _dedupe_records(entries + _entity_page_records())
    return {
        "ok": True,
        "resolver_path": str(brain_root() / "RESOLVER.md"),
        "entries": [_display_record(entry) for entry in entries],
        "warnings": warnings,
    }


def _compact_salience_map(max_entries: int = 60) -> list[dict[str, Any]]:
    result = salience_map(include_page_records=False)
    compact: list[dict[str, Any]] = []
    for entry in result.get("entries", [])[:max_entries]:
        compact.append(
            {
                "title": entry.get("title", ""),
                "type": entry.get("type", ""),
                "path": entry.get("path", ""),
                "aliases": entry.get("aliases", [])[:6],
                "review_only_aliases": entry.get("review_only_aliases", [])[:6],
                "auto_link_aliases": entry.get("auto_link_aliases", [])[:6],
                "triggers": entry.get("triggers", [])[:8],
                "salience": entry.get("salience", "medium"),
                "load_policy": entry.get("load_policy", "triggered"),
                "sensitivity": entry.get("sensitivity", ""),
                "sharing_policy": entry.get("sharing_policy", ""),
                "egress": entry.get("egress", ""),
                "baseline_handle": entry.get("baseline_handle", ""),
            }
        )
    return compact


def resolve_entity(query: str, entity_type: str = "") -> dict[str, Any]:
    if not query or not query.strip():
        return {"ok": False, "error": "query is required", "matches": []}
    directory = _normalize_entity_type(entity_type)
    if entity_type and directory is None:
        return {"ok": False, "error": f"unsupported entity_type {entity_type!r}", "matches": []}
    q = query.strip()
    q_key = _norm_entity_key(q)
    exact: list[dict[str, Any]] = []
    possible: list[dict[str, Any]] = []
    for record in _all_entity_records(entity_type):
        candidate_keys = [_norm_entity_key(name) for name in _candidate_names(record)]
        title_key = _norm_entity_key(str(record.get("title", "")))
        stem_key = _norm_entity_key(Path(str(record.get("path", ""))).stem)
        if q_key in candidate_keys or q_key == title_key or q_key == stem_key:
            exact.append(record)
            continue
        searchable = " ".join(_candidate_names(record) + [str(record.get("baseline_handle", ""))])
        searchable_key = _norm_entity_key(searchable)
        if q_key and (q_key in searchable_key or any(key and key in q_key for key in candidate_keys)):
            possible.append(record)
    exact = _dedupe_records(exact)
    possible = [record for record in _dedupe_records(possible) if record not in exact]
    ambiguous = len(exact) != 1
    recommended = exact[0] if len(exact) == 1 else (possible[0] if len(possible) == 1 and not exact else None)
    return {
        "ok": True,
        "query": query,
        "entity_type": directory or "all",
        "exact_matches": [_display_record(record) for record in exact],
        "possible_matches": [_display_record(record) for record in possible[:10]],
        "ambiguous": ambiguous,
        "recommended_path": str(recommended.get("path", "")) if recommended else "",
        "ask_before_linking": ambiguous,
        "reason": "one exact match" if len(exact) == 1 else ("multiple exact matches" if len(exact) > 1 else "no exact match"),
    }


def _existing_wikilink_targets(text: str) -> list[str]:
    targets: list[str] = []
    for match in re.finditer(r"\[\[([^\]]+)\]\]", text or ""):
        target = match.group(1).split("|", 1)[0].strip()
        if target:
            targets.append(target)
    return targets


def _should_ignore_wikilink_scan_file(rel: str, ignore_schema_examples: bool = True) -> bool:
    if not ignore_schema_examples:
        return False
    clean = rel.strip().lstrip("/")
    name = Path(clean).name
    return name in {"README.md", "_template.md", "schema.md"} or clean.startswith("sources/legacy") or "/example" in clean or clean.startswith("templates/")


def _should_ignore_wikilink_target(target_name: str, ignore_schema_examples: bool = True) -> bool:
    if not ignore_schema_examples:
        return False
    lowered = target_name.lower()
    return lowered.startswith("example") or "/example" in lowered


def _normalized_wikilink_target(target_text: str) -> str:
    target = (target_text or "").split("|", 1)[0].split("#", 1)[0].strip()
    lowered = target.lower().removesuffix(".md").strip("/")
    if lowered.startswith("./"):
        lowered = lowered[2:]
    return lowered


def _page_has_moc_or_index_tag(path: Path) -> bool:
    fm, _body = _parse_frontmatter(_read_text(path))
    tags = _normalize_sequence(fm.get("tags"))
    return any(str(tag).strip().lower() in {"moc", "index"} for tag in tags)


def _yerhed_link_context_allows(text: str, source_path: str = "") -> bool:
    rel = source_path.strip().lstrip("/")
    if rel in YERHED_GRAPH_LINK_ALLOWLIST:
        return True
    lowered = (text or "").lower()
    return any(term in lowered for term in YERHED_SEMANTIC_CONTEXT_TERMS)


def _graph_hygiene_warning_for_link(source_rel: str, source_path: Path, raw_target: str, line_no: int, resolved: Path | None = None) -> dict[str, Any] | None:
    normalized_target = _normalized_wikilink_target(raw_target)
    resolved_rel = ""
    if resolved is not None:
        try:
            resolved_rel = resolved.relative_to(brain_root()).as_posix()
        except ValueError:
            resolved_rel = ""
    normalized_resolved = resolved_rel.lower().removesuffix(".md")

    if normalized_target in GRAPH_CATEGORY_HUB_TARGETS and not _page_has_moc_or_index_tag(source_path):
        return {
            "source": source_rel,
            "line": line_no,
            "target": raw_target,
            "kind": "category_hub_link",
            "reason": "folders, frontmatter, and tags classify entities; ordinary wikilinks should not create category hubs",
        }

    if normalized_target == YERHED_LINK_TARGET or normalized_resolved == YERHED_LINK_TARGET:
        if source_rel not in YERHED_GRAPH_LINK_ALLOWLIST:
            return {
                "source": source_rel,
                "line": line_no,
                "target": raw_target,
                "kind": "yerhed_storage_hub_link",
                "reason": "link to Yerhed only when the page is semantically about Yerhed, not merely stored in the brain",
            }
    return None


def _protected_text_ranges(text: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in re.finditer(r"\[\[[^\]]+\]\]|`[^`]*`", text or "")]


def _range_overlaps(start: int, end: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start < existing_end and end > existing_start for existing_start, existing_end in ranges)


def _line_column_for_offset(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset)
    column = offset + 1 if line_start == -1 else offset - line_start
    return line, column


def _plain_mention_occurrences(text: str, phrase: str, occupied: list[tuple[int, int]] | None = None) -> list[dict[str, Any]]:
    if not phrase or len(phrase) < 3:
        return []
    blocked = _protected_text_ranges(text) + list(occupied or [])
    pattern = re.compile(rf"(?<![\w/])({re.escape(phrase)})(?![\w/])")
    matches: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        start, end = match.span(1)
        if _range_overlaps(start, end, blocked):
            continue
        line, column = _line_column_for_offset(text, start)
        matches.append({"text": match.group(1), "line": line, "column": column, "offset": start, "end_offset": end})
    return matches


def _replace_plain_entity_mentions(text: str, replacements: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    applied: list[dict[str, Any]] = []
    occupied: list[tuple[int, int]] = []
    replacements_to_apply: list[dict[str, Any]] = []
    for replacement in replacements:
        phrase = str(replacement.get("phrase", ""))
        link_target = str(replacement.get("link_target", ""))
        if not phrase or len(phrase) < 3 or not link_target:
            continue
        occurrences = _plain_mention_occurrences(text, phrase, occupied)
        if not occurrences:
            continue
        occurrence = occurrences[0]
        start = int(occurrence["offset"])
        end = int(occurrence["end_offset"])
        occupied.append((start, end))
        linked = f"[[{link_target}|{occurrence['text']}]]"
        row = {
            **occurrence,
            "link_target": link_target,
            "match_kind": replacement.get("match_kind", "canonical_title"),
            "link_policy": replacement.get("link_policy", "auto"),
            "reason": replacement.get("reason", "canonical title match"),
        }
        replacements_to_apply.append({**row, "replacement": linked})
        applied.append(row)

    if not replacements_to_apply:
        return text, []
    replacements_to_apply.sort(key=lambda item: int(item["offset"]))
    chunks: list[str] = []
    cursor = 0
    for item in replacements_to_apply:
        start = int(item["offset"])
        end = int(item["end_offset"])
        chunks.append(text[cursor:start])
        chunks.append(str(item["replacement"]))
        cursor = end
    chunks.append(text[cursor:])
    return "".join(chunks), applied


def suggest_links(draft: str, allowed_entity_types: Any = None, source_path: str = "", ignore_schema_examples: bool = True) -> dict[str, Any]:
    if draft is None:
        return {"ok": False, "error": "draft is required"}
    allowed_dirs = {_normalize_entity_type(item) for item in _normalize_sequence(allowed_entity_types)} if allowed_entity_types else set()
    allowed_dirs.discard(None)
    name_to_candidates: dict[str, list[dict[str, Any]]] = {}
    for record in _linkable_entity_records():
        if allowed_dirs and record.get("directory") not in allowed_dirs:
            continue
        for match in _link_candidate_names(record, include_triggers=False):
            name = str(match.get("text", ""))
            if len(name) < 3:
                continue
            key = _norm_entity_key(name)
            if not key:
                continue
            name_to_candidates.setdefault(key, []).append({**match, "record": record, "link_target": _entity_link_target(record)})

    replacements: list[dict[str, Any]] = []
    matched_entities: list[dict[str, Any]] = []
    review_only: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    seen_matched_paths: set[str] = set()
    for key, candidates in name_to_candidates.items():
        deduped_by_path: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            path = str(candidate.get("record", {}).get("path", ""))
            deduped_by_path.setdefault(path, candidate)
        deduped = list(deduped_by_path.values())
        sample_name = str(deduped[0].get("text", "")) if deduped else ""
        occurrences = _plain_mention_occurrences(draft, sample_name) if sample_name else []
        if not occurrences:
            continue
        if len(deduped) == 1:
            candidate = deduped[0]
            record = candidate["record"]
            link_target = str(candidate.get("link_target", ""))
            if link_target.lower().removesuffix(".md") == YERHED_LINK_TARGET and not _yerhed_link_context_allows(draft, source_path):
                continue
            if candidate.get("link_policy") == "auto":
                replacements.append({
                    "phrase": sample_name,
                    "link_target": link_target,
                    "match_kind": candidate.get("match_kind", "canonical_title"),
                    "link_policy": "auto",
                    "reason": candidate.get("reason", "canonical title match"),
                })
                path = str(record.get("path", ""))
                if path not in seen_matched_paths:
                    seen_matched_paths.add(path)
                    matched_entities.append(_display_record(record))
            else:
                occurrence = occurrences[0]
                review_only.append({
                    **occurrence,
                    "link_target": link_target,
                    "match_kind": candidate.get("match_kind", "review_only_alias"),
                    "link_policy": candidate.get("link_policy", "review_only"),
                    "requires_operator_approval": True,
                    "reason": candidate.get("reason", "alias is review_only"),
                    "target_entity": _display_record(record),
                })
        else:
            occurrence = occurrences[0]
            ambiguous.append({
                **occurrence,
                "match_kind": "ambiguous",
                "link_policy": "review_only",
                "requires_operator_approval": True,
                "reason": "multiple entity records match text",
                "matches": [_display_record(candidate["record"]) for candidate in deduped[:5]],
            })
    replacements.sort(key=lambda item: len(str(item.get("phrase", ""))), reverse=True)
    suggested, applied = _replace_plain_entity_mentions(draft, replacements)
    unresolved: list[dict[str, Any]] = []
    scan_unresolved = not _should_ignore_wikilink_scan_file(source_path, ignore_schema_examples) if source_path else True
    if scan_unresolved:
        for match in re.finditer(r"\[\[([^\]]+)\]\]", suggested or ""):
            raw_target = match.group(1).split("|", 1)[0].strip()
            target_name = raw_target.split("#", 1)[0].strip()
            if _should_ignore_wikilink_target(target_name, ignore_schema_examples):
                continue
            resolved, reason = _resolve_wikilink_target(raw_target)
            if resolved is None:
                line, column = _line_column_for_offset(suggested, match.start(1))
                unresolved.append({"target": raw_target, "line": line, "column": column, "offset": match.start(1), "end_offset": match.end(1), "reason": reason})
    warnings = []
    if ambiguous:
        warnings.append("ambiguous entity mentions were left unlinked")
    if review_only:
        warnings.append("review-only alias candidates were left unlinked")
    if unresolved:
        warnings.append("existing wikilinks include unresolved targets")
    return {
        "ok": True,
        "suggested_draft": suggested,
        "matched_entities": matched_entities,
        "applied_links": applied,
        "review_only_candidates": review_only,
        "ambiguous_candidates": ambiguous,
        "unresolved_candidates": unresolved,
        "warnings": warnings,
        "wrote_files": False,
    }


def _git_output(cwd: Path, args: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(["git", *args], cwd=str(cwd), text=True, capture_output=True)
    except OSError as exc:
        return False, str(exc)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "git command failed").strip()
    return True, proc.stdout


def _brain_rel_from_existing_path(path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(brain_root().resolve()).as_posix()
    except ValueError:
        return None
    if rel.startswith(".") or ".." in Path(rel).parts:
        return None
    return rel


def _add_review_path(review: dict[str, set[str]], rel: str, reason: str) -> None:
    clean = rel.strip().lstrip("/")
    if not clean or ".." in Path(clean).parts:
        return
    if clean.startswith(".git/") or clean.startswith(".obsidian/"):
        return
    if not clean.endswith(".md"):
        return
    path = brain_root() / clean
    if not path.exists() or not path.is_file():
        return
    review.setdefault(clean, set()).add(reason)


def _changed_brain_markdown_paths(since_days: int) -> tuple[list[str], dict[str, Any], list[str]]:
    root = brain_root()
    warnings: list[str] = []
    ok, inside = _git_output(root, ["rev-parse", "--is-inside-work-tree"])
    if not ok or inside.strip() != "true":
        return [], {"kind": "not_git_worktree", "since_days": since_days}, ["brain root is not a git worktree; changed-file review set is empty"]

    marker_ok, marker = _git_output(
        root,
        ["log", "--regexp-ignore-case", "--grep=Dream Cycle", "--format=%cI", "--max-count=1"],
    )
    marker = marker.strip().splitlines()[0] if marker_ok and marker.strip() else ""
    if marker:
        since_spec = marker
        basis = {"kind": "previous_dream_cycle_marker", "since": since_spec}
    else:
        since_dt = _dt.datetime.now(_dt.UTC) - _dt.timedelta(days=max(1, since_days))
        since_spec = since_dt.isoformat()
        basis = {"kind": "fallback_last_days", "since_days": since_days, "since": since_spec}

    paths: set[str] = set()
    log_ok, log_out = _git_output(root, ["log", f"--since={since_spec}", "--name-only", "--pretty=format:", "--", "*.md"])
    if log_ok:
        paths.update(line.strip() for line in log_out.splitlines() if line.strip().endswith(".md"))
    else:
        warnings.append(f"git changed-file scan failed: {log_out}")

    status_ok, status_out = _git_output(root, ["status", "--porcelain", "--", "*.md"])
    if status_ok:
        for raw in status_out.splitlines():
            rel = raw[3:].strip()
            if " -> " in rel:
                rel = rel.split(" -> ", 1)[1].strip()
            if rel.endswith(".md"):
                paths.add(rel)
    else:
        warnings.append(f"git status changed-file scan failed: {status_out}")
    return sorted(paths), basis, warnings


def _collect_dream_cycle_review_set(
    since_days: int,
    include_changed_files: bool = True,
    include_active_projects: bool = True,
    include_inbox: bool = True,
    include_open_loops: bool = True,
    include_resolver: bool = True,
    include_salience_pages: bool = True,
    max_files: int = 120,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    review: dict[str, set[str]] = {}
    warnings: list[str] = []
    basis: dict[str, Any] = {"kind": "not_requested"}

    if include_changed_files:
        changed, basis, changed_warnings = _changed_brain_markdown_paths(since_days)
        warnings.extend(changed_warnings)
        for rel in changed:
            _add_review_path(review, rel, "changed since previous Dream Cycle marker or fallback window")

    if include_active_projects:
        for record in _all_entity_records("project"):
            if record.get("load_policy") == "archival" or record.get("salience") == "low":
                continue
            _add_review_path(review, str(record.get("path", "")), "active project page")

    if include_inbox:
        inbox = brain_root() / "inbox"
        if inbox.exists():
            for path in sorted(inbox.rglob("*.md")):
                rel = _brain_rel_from_existing_path(path)
                if rel:
                    _add_review_path(review, rel, "inbox note")

    if include_open_loops:
        _add_review_path(review, "projects/open-loops.md", "central open loops")

    if include_resolver:
        _add_review_path(review, "RESOLVER.md", "resolver salience map")

    if include_salience_pages:
        for record in _all_entity_records():
            if record.get("load_policy") == "baseline" or record.get("salience") == "high":
                _add_review_path(review, str(record.get("path", "")), "high-salience or baseline page")

    ordered = [
        {"path": rel, "reasons": sorted(reasons)}
        for rel, reasons in sorted(review.items(), key=lambda item: item[0])
    ]
    omitted = 0
    if max_files > 0 and len(ordered) > max_files:
        omitted = len(ordered) - max_files
        ordered = ordered[:max_files]
        warnings.append(f"review set capped at {max_files} files; {omitted} files omitted")
    basis["review_set_count"] = len(ordered)
    basis["omitted_count"] = omitted
    return ordered, basis, warnings


def _record_index_by_link_target() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in _linkable_entity_records():
        targets = {
            _entity_link_target(record),
            str(record.get("path", "")),
            str(record.get("path", "")).removesuffix(".md"),
            str(record.get("title", "")),
        }
        for target in targets:
            key = target.strip().lower()
            if key and key not in index:
                index[key] = record
    return index


def _link_candidate_requires_approval(source_sensitivity: str, target_record: dict[str, Any] | None) -> tuple[bool, str]:
    if source_sensitivity in {"sensitive", "do_not_share"}:
        return True, f"source note is {source_sensitivity}"
    if not target_record:
        return True, "target entity record not found"
    sensitivity = _normalize_sensitivity(target_record.get("sensitivity"), default="private") or "private"
    sharing = str(target_record.get("sharing_policy", "")).strip().lower().replace("-", "_")
    egress = str(target_record.get("egress", "")).strip().lower().replace("-", "_")
    if sensitivity in {"sensitive", "do_not_share"}:
        return True, f"target entity is {sensitivity}"
    if sharing == "do_not_share" or egress in {"do_not_share", "block"}:
        return True, "target entity has do-not-share sharing/egress metadata"
    return False, "unambiguous non-sensitive known entity"


def _entity_name_collisions() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    title_map: dict[str, list[dict[str, Any]]] = {}
    alias_map: dict[str, list[dict[str, Any]]] = {}
    for record in _linkable_entity_records():
        display = _display_record(record)
        for name in [str(record.get("title", "")), Path(str(record.get("path", ""))).stem.replace("-", " ")]:
            key = _norm_entity_key(name)
            if key:
                title_map.setdefault(key, []).append(display)
        for alias in record.get("aliases", []) or []:
            key = _norm_entity_key(str(alias))
            if key:
                alias_map.setdefault(key, []).append(display)

    def collisions(mapping: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for key, records in sorted(mapping.items()):
            deduped = {str(record.get("path", "")): record for record in records}
            if len(deduped) > 1:
                rows.append({"key": key, "matches": list(deduped.values())})
        return rows

    return collisions(title_map), collisions(alias_map)


def _missing_resolver_entries() -> list[dict[str, Any]]:
    resolver_paths = {str(entry.get("path", "")) for entry in _resolver_entries()[0]}
    missing: list[dict[str, Any]] = []
    for record in _entity_page_records():
        rel = str(record.get("path", ""))
        if rel in resolver_paths:
            continue
        if record.get("load_policy") == "archival" and record.get("salience") == "low":
            continue
        missing.append(_display_record(record))
    return missing


def _report_list(title: str, rows: list[Any], formatter: Any | None = None) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        lines.extend(["- None", ""])
        return lines
    for row in rows[:40]:
        lines.append(formatter(row) if formatter else f"- {row}")
    if len(rows) > 40:
        lines.append(f"- ... {len(rows) - 40} more")
    lines.append("")
    return lines



def _candidate_location(row: dict[str, Any]) -> str:
    line = row.get("line")
    column = row.get("column")
    if line and column:
        return f":{line}:{column}"
    if line:
        return f":{line}"
    return ""


def suggest_links_for_review_set(
    since_days: int = 7,
    max_files: int = 120,
    allowed_entity_types: Any = None,
    include_drafts: bool = False,
    include_changed_files: bool = True,
    include_active_projects: bool = True,
    include_inbox: bool = True,
    include_open_loops: bool = True,
    include_resolver: bool = True,
    include_salience_pages: bool = True,
) -> dict[str, Any]:
    """Run exact known-entity link suggestions over the Dream Cycle review set."""
    review_set, basis, warnings = _collect_dream_cycle_review_set(
        since_days=since_days,
        include_changed_files=include_changed_files,
        include_active_projects=include_active_projects,
        include_inbox=include_inbox,
        include_open_loops=include_open_loops,
        include_resolver=include_resolver,
        include_salience_pages=include_salience_pages,
        max_files=max_files,
    )
    target_index = _record_index_by_link_target()
    per_file: list[dict[str, Any]] = []
    new_candidates: list[dict[str, Any]] = []
    approval_candidates: list[dict[str, Any]] = []
    unresolved_candidates: list[dict[str, Any]] = []
    skipped_updates: list[dict[str, Any]] = []

    seen_new_candidates: set[tuple[Any, ...]] = set()
    seen_approval_candidates: set[tuple[Any, ...]] = set()
    seen_unresolved_candidates: set[tuple[Any, ...]] = set()
    seen_skipped_updates: set[tuple[Any, ...]] = set()

    def add_skipped(row: dict[str, Any]) -> None:
        key = (row.get("source"), row.get("link_target"), row.get("text"), row.get("line"), row.get("column"), row.get("reason"))
        if key in seen_skipped_updates:
            return
        seen_skipped_updates.add(key)
        skipped_updates.append(row)

    for item in review_set:
        rel = item["path"]
        path = brain_root() / rel
        source_sensitivity = _source_sensitivity(str(path)).get("sensitivity", "private")
        if rel == "RESOLVER.md":
            warning = "resolver metadata is audited by validate_wikilinks and resolver/frontmatter checks; alias/trigger text is not treated as link-application candidates"
            add_skipped({"source": rel, "reason": warning})
            per_file.append(
                {
                    "path": rel,
                    "reasons": item.get("reasons", []),
                    "source_sensitivity": source_sensitivity,
                    "new_wikilink_candidates": [],
                    "ambiguous_or_sensitive_candidates": [],
                    "unresolved_candidates": [],
                    "safe_to_apply": False,
                    "warnings": [warning],
                }
            )
            continue
        suggestion = suggest_links(_read_text(path), allowed_entity_types=allowed_entity_types, source_path=rel, ignore_schema_examples=True)
        file_candidates: list[dict[str, Any]] = []
        file_approval_candidates: list[dict[str, Any]] = []
        for applied in suggestion.get("applied_links", []) or []:
            link_target = str(applied.get("link_target", ""))
            source_target = rel.removesuffix(".md")
            if link_target.lower().removesuffix(".md") == source_target.lower():
                add_skipped({
                    "source": rel,
                    "text": applied.get("text", ""),
                    "link_target": link_target,
                    "line": applied.get("line", 0),
                    "column": applied.get("column", 0),
                    "reason": "self-link candidate skipped",
                })
                continue
            record = target_index.get(link_target.lower())
            requires_approval, reason = _link_candidate_requires_approval(source_sensitivity, record)
            candidate = {
                "source": rel,
                "text": applied.get("text", ""),
                "link_target": link_target,
                "line": applied.get("line", 0),
                "column": applied.get("column", 0),
                "offset": applied.get("offset", 0),
                "end_offset": applied.get("end_offset", 0),
                "target_entity": _display_record(record) if record else {},
                "source_sensitivity": source_sensitivity,
                "match_kind": applied.get("match_kind", "canonical_title"),
                "link_policy": applied.get("link_policy", "auto"),
                "requires_operator_approval": requires_approval,
                "reason": reason,
            }
            candidate_key = (candidate["source"], candidate["link_target"], candidate["offset"], candidate["end_offset"])
            if candidate_key in seen_new_candidates:
                continue
            seen_new_candidates.add(candidate_key)
            file_candidates.append(candidate)
            new_candidates.append(candidate)
            add_skipped({**candidate, "reason": "read-only Dream Cycle review; apply/propose separately under update policy"})
            if requires_approval:
                approval_key = (candidate["source"], candidate["link_target"], candidate["offset"], candidate["end_offset"], candidate["reason"])
                if approval_key not in seen_approval_candidates:
                    seen_approval_candidates.add(approval_key)
                    file_approval_candidates.append(candidate)
                    approval_candidates.append(candidate)
        for review_candidate in suggestion.get("review_only_candidates", []) or []:
            link_target = str(review_candidate.get("link_target", ""))
            source_target = rel.removesuffix(".md")
            if link_target.lower().removesuffix(".md") == source_target.lower():
                add_skipped({
                    "source": rel,
                    "text": review_candidate.get("text", ""),
                    "link_target": link_target,
                    "line": review_candidate.get("line", 0),
                    "column": review_candidate.get("column", 0),
                    "reason": "self-link candidate skipped",
                })
                continue
            record = target_index.get(link_target.lower())
            candidate = {
                "source": rel,
                "text": review_candidate.get("text", ""),
                "link_target": link_target,
                "line": review_candidate.get("line", 0),
                "column": review_candidate.get("column", 0),
                "offset": review_candidate.get("offset", 0),
                "end_offset": review_candidate.get("end_offset", 0),
                "target_entity": _display_record(record) if record else review_candidate.get("target_entity", {}),
                "source_sensitivity": source_sensitivity,
                "match_kind": review_candidate.get("match_kind", "review_only_alias"),
                "link_policy": review_candidate.get("link_policy", "review_only"),
                "requires_operator_approval": True,
                "reason": review_candidate.get("reason", "alias is review_only"),
            }
            candidate_key = (candidate["source"], candidate["link_target"], candidate["offset"], candidate["end_offset"])
            if candidate_key not in seen_new_candidates:
                seen_new_candidates.add(candidate_key)
                file_candidates.append(candidate)
                new_candidates.append(candidate)
            approval_key = (candidate["source"], candidate["link_target"], candidate["offset"], candidate["end_offset"], candidate["reason"])
            if approval_key not in seen_approval_candidates:
                seen_approval_candidates.add(approval_key)
                file_approval_candidates.append(candidate)
                approval_candidates.append(candidate)
            add_skipped({**candidate, "reason": "review-only alias requires operator approval"})
        for ambiguous in suggestion.get("ambiguous_candidates", []) or []:
            row = {"source": rel, "kind": "ambiguous", **ambiguous}
            approval_key = (row.get("source"), row.get("text"), row.get("line"), row.get("column"), row.get("kind"))
            if approval_key not in seen_approval_candidates:
                seen_approval_candidates.add(approval_key)
                file_approval_candidates.append(row)
                approval_candidates.append(row)
            add_skipped({"source": rel, "text": ambiguous.get("text", ""), "line": ambiguous.get("line", 0), "column": ambiguous.get("column", 0), "reason": "ambiguous entity mention requires operator approval"})
        for unresolved in suggestion.get("unresolved_candidates", []) or []:
            target = unresolved.get("target", "") if isinstance(unresolved, dict) else unresolved
            row = {"source": rel, "target": target, "reason": "existing wikilink does not resolve"}
            if isinstance(unresolved, dict):
                row.update({key: unresolved.get(key) for key in ["line", "column", "offset", "end_offset"] if key in unresolved})
            unresolved_key = (row.get("source"), row.get("target"), row.get("line"), row.get("column"))
            if unresolved_key in seen_unresolved_candidates:
                continue
            seen_unresolved_candidates.add(unresolved_key)
            unresolved_candidates.append(row)
        file_report = {
            "path": rel,
            "reasons": item.get("reasons", []),
            "source_sensitivity": source_sensitivity,
            "new_wikilink_candidates": file_candidates,
            "ambiguous_or_sensitive_candidates": file_approval_candidates,
            "unresolved_candidates": suggestion.get("unresolved_candidates", []),
            "safe_to_apply": bool(file_candidates) and not file_approval_candidates and not suggestion.get("unresolved_candidates"),
            "warnings": suggestion.get("warnings", []),
        }
        if include_drafts:
            file_report["suggested_draft"] = suggestion.get("suggested_draft", "")
        per_file.append(file_report)

    validation = validate_wikilinks(ignore_schema_examples=True)
    graph_hygiene_warnings = list(validation.get("graph_hygiene_warnings", []))
    duplicate_pages, stale_aliases = _entity_name_collisions()
    missing_resolver = _missing_resolver_entries()
    missing_entities = list(validation.get("unresolved", [])) + unresolved_candidates
    stale_salience = list(validation.get("resolver_frontmatter_drift", []))
    active_anchor_candidates = [
        {"label": anchor.get("label", ""), "source_path": anchor.get("source_path", ""), "line": anchor.get("line", 0), "reason": "review for stale, bulky, or promotion/demotion status"}
        for anchor in active_anchors()
    ]

    lines = [
        "# Dream Cycle Graph-Gardening Review",
        "",
        f"- review set files: {len(review_set)}",
        f"- changed-file basis: {basis.get('kind', '')}",
        "",
    ]
    lines.extend(_report_list("Broken Links", validation.get("unresolved", []), lambda row: f"- {row.get('source')}:{row.get('line')} -> {row.get('target')} ({row.get('reason')})"))
    lines.extend(_report_list("Duplicate/Near-Duplicate Entity Pages", duplicate_pages, lambda row: f"- {row.get('key')}: " + ", ".join(match.get("path", "") for match in row.get("matches", []))))
    lines.extend(_report_list("Missing Entity Pages", missing_entities, lambda row: f"- {row.get('source', '')} -> {row.get('target', '')} ({row.get('reason', '')})"))
    lines.extend(_report_list("Missing Resolver Entries", missing_resolver, lambda row: f"- {row.get('title')} ({row.get('path')})"))
    lines.extend(_report_list("Stale Aliases", stale_aliases, lambda row: f"- {row.get('key')}: " + ", ".join(match.get("path", "") for match in row.get("matches", []))))
    lines.extend(_report_list("Stale Salience / Active Anchor Promotion-Demotion Candidates", stale_salience + active_anchor_candidates, lambda row: f"- {row.get('path', row.get('label', 'anchor'))}: review salience/anchor status"))
    lines.extend(_report_list("Graph Hygiene Warnings", graph_hygiene_warnings, lambda row: f"- {row.get('source')}:{row.get('line')} -> {row.get('target')} [{row.get('kind')}] ({row.get('reason')})"))
    lines.extend(_report_list("New Wikilink Candidates", new_candidates, lambda row: f"- {row.get('source')}{_candidate_location(row)}: {row.get('text')} -> [[{row.get('link_target')}]] [{row.get('match_kind', 'canonical_title')}] ({row.get('reason')})"))
    lines.extend(_report_list("Ambiguous/Sensitive Link Candidates Requiring Operator Approval", approval_candidates, lambda row: f"- {row.get('source')}{_candidate_location(row)}: {row.get('text', row.get('target', 'candidate'))} [{row.get('match_kind', row.get('kind', 'review'))}] ({row.get('reason', 'review')})"))
    lines.extend(_report_list("Applied Safe Link/Entity Updates", [], None))
    lines.extend(_report_list("Skipped Link/Entity Updates With Reason", skipped_updates, lambda row: f"- {row.get('source')}{_candidate_location(row)}: {row.get('link_target', row.get('text', 'candidate'))} ({row.get('reason')})"))

    return {
        "ok": True,
        "root": str(brain_root()),
        "review_set": review_set,
        "changed_file_basis": basis,
        "per_file": per_file,
        "new_wikilink_candidates": new_candidates,
        "ambiguous_sensitive_link_candidates": approval_candidates,
        "unresolved_candidates": unresolved_candidates,
        "broken_links": validation.get("unresolved", []),
        "duplicate_near_duplicate_entity_pages": duplicate_pages,
        "missing_entity_pages": missing_entities,
        "missing_resolver_entries": missing_resolver,
        "stale_aliases": stale_aliases,
        "stale_salience_active_anchor_candidates": stale_salience + active_anchor_candidates,
        "graph_hygiene_warnings": graph_hygiene_warnings,
        "applied_safe_link_entity_updates": [],
        "skipped_link_entity_updates": skipped_updates,
        "wikilink_validation_counts": validation.get("counts", {}),
        "warnings": warnings,
        "wrote_files": False,
        "graph_gardening_report": "\n".join(lines),
    }


def _format_yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    escaped = [item.replace('"', '\\"') for item in items]
    return "[" + ", ".join(f'"{item}"' for item in escaped) + "]"


def _entity_page_rel_path(entity_type: str, name: str) -> str | None:
    directory = _normalize_entity_type(entity_type)
    if directory is None:
        return None
    return f"{directory}/{_slug(name)}.md"


def _resolver_entry_text(
    title: str,
    entity_type: str,
    path: str,
    aliases: list[str],
    triggers: list[str],
    salience: str,
    load_policy: str,
    baseline_handle: str,
    sensitivity: str = "",
    sharing_policy: str = "",
    egress: str = "",
) -> str:
    entity = _canonical_entity_type(entity_type) or entity_type
    lines = [
        f"### {title.strip()}",
        "",
        f"- type: {entity}",
        f"- path: {path}",
        f"- aliases: {_format_yaml_list(aliases)}",
        f"- triggers: {_format_yaml_list(triggers)}",
        f"- salience: {salience}",
        f"- load_policy: {load_policy}",
    ]
    normalized_sensitivity = _normalize_sensitivity(sensitivity, default="")
    if normalized_sensitivity:
        lines.append(f"- sensitivity: {normalized_sensitivity}")
    if sharing_policy:
        lines.append(f"- sharing_policy: {sharing_policy.strip()}")
    if egress:
        lines.append(f"- egress: {egress.strip()}")
    lines.append(f"- baseline_handle: {baseline_handle.strip()}")
    return "\n".join(lines).rstrip() + "\n"


def propose_entity_page(
    entity_type: str,
    name: str,
    context_summary: str,
    aliases: Any = None,
    triggers: Any = None,
    salience: str = "medium",
    sensitivity: str = "private",
    load_policy: str = "triggered",
) -> dict[str, Any]:
    directory = _normalize_entity_type(entity_type)
    if directory is None:
        return {"ok": False, "error": f"unsupported entity_type {entity_type!r}"}
    if not name or not name.strip():
        return {"ok": False, "error": "name is required"}
    salience = (salience or "medium").strip().lower()
    if salience not in VALID_SALIENCE:
        return {"ok": False, "error": f"salience must be one of {', '.join(sorted(VALID_SALIENCE))}"}
    load_policy = (load_policy or "triggered").strip().lower().replace("-", "_")
    if load_policy not in VALID_LOAD_POLICIES:
        return {"ok": False, "error": f"load_policy must be one of {', '.join(sorted(VALID_LOAD_POLICIES))}"}
    sensitivity = _normalize_sensitivity(sensitivity, default="private")
    if not sensitivity:
        return {"ok": False, "error": _sensitivity_error()}
    alias_list = _parse_scalar_or_list(aliases)
    trigger_list = _parse_scalar_or_list(triggers)
    rel_path = _entity_page_rel_path(entity_type, name)
    assert rel_path is not None
    tag_type = ENTITY_DIR_TO_TYPE.get(directory, directory.rstrip("s"))
    baseline_handle = (context_summary or "").strip().splitlines()[0][:240]
    frontmatter = (
        "---\n"
        f"type: {tag_type}\n"
        f"aliases: {_format_yaml_list(alias_list)}\n"
        f"triggers: {_format_yaml_list(trigger_list)}\n"
        f"tags: {_format_yaml_list(['yerhed', f'entity/{tag_type}'])}\n"
        f"salience: {salience}\n"
        f"load_policy: {load_policy}\n"
        f"sensitivity: {sensitivity}\n"
        f"baseline_handle: \"{baseline_handle.replace(chr(34), chr(92) + chr(34))}\"\n"
        "---\n"
    )
    body = (
        f"{frontmatter}\n"
        f"# {name.strip()}\n\n"
        "## Summary\n\n"
        f"{(context_summary or 'TODO: summarize why this entity matters.').strip()}\n\n"
        "## Current State\n\n"
        "- TODO: add current known state.\n\n"
        "## Open Questions\n\n"
        "- TODO: add unresolved questions.\n\n"
        "## Links\n\n"
        "- [[RESOLVER]]\n"
    )
    return {
        "ok": True,
        "entity_type": tag_type,
        "path": rel_path,
        "frontmatter": frontmatter.strip(),
        "body": body,
        "resolver_entry": _resolver_entry_text(name, entity_type, rel_path, alias_list, trigger_list, salience, load_policy, baseline_handle, sensitivity=sensitivity),
        "wrote_files": False,
    }


def _resolver_alias_collision(aliases: list[str], target_path: str = "") -> list[dict[str, Any]]:
    wanted = {_norm_entity_key(alias) for alias in aliases if alias}
    collisions: list[dict[str, Any]] = []
    for entry in salience_map(include_page_records=True).get("entries", []):
        if target_path and entry.get("path") == target_path:
            continue
        keys = {_norm_entity_key(name) for name in _candidate_names(entry, include_triggers=False)}
        overlap = wanted & keys
        if overlap:
            collisions.append({"entry": entry, "aliases": sorted(overlap)})
    return collisions



def _normalize_brain_write_path(path_text: str, require_md: bool = True) -> tuple[str, Path] | tuple[None, None]:
    raw = (path_text or "").strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0]
    if not raw:
        return None, None
    candidate = Path(raw).expanduser()
    root = brain_root()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        if not _is_under(resolved, root):
            return None, None
        try:
            rel = resolved.relative_to(root).as_posix()
        except ValueError:
            return None, None
    else:
        if ".." in candidate.parts:
            return None, None
        rel = candidate.as_posix()
        resolved = (root / rel).resolve()
        if not _is_under(resolved, root):
            return None, None
    if require_md and not rel.endswith(".md"):
        rel = f"{rel}.md"
        resolved = (root / rel).resolve()
    parts = Path(rel).parts
    if not parts:
        return None, None
    top = parts[0]
    if top not in BRAIN_TOP_LEVEL and rel not in BRAIN_TOP_LEVEL:
        return None, None
    return rel, resolved


def _sections_markdown(sections: Any) -> str:
    if not sections:
        return ""
    chunks: list[str] = []
    if isinstance(sections, dict):
        iterable = [{"heading": key, "body": value} for key, value in sections.items()]
    elif isinstance(sections, list):
        iterable = sections
    else:
        return str(sections).strip()
    for item in iterable:
        if isinstance(item, dict):
            heading = str(item.get("heading") or item.get("title") or "Note").strip()
            body = str(item.get("body") or item.get("text") or "").strip()
        else:
            heading = "Note"
            body = str(item).strip()
        if heading and body:
            chunks.append(f"## {heading}\n\n{body}")
    return "\n\n".join(chunks).strip()


def _entity_frontmatter(
    entity_type: str,
    aliases: list[str],
    triggers: list[str],
    salience: str,
    load_policy: str,
    sensitivity: str,
    baseline_handle: str,
    sharing_policy: str = "",
    egress: str = "",
) -> str:
    directory = _normalize_entity_type(entity_type)
    tag_type = ENTITY_DIR_TO_TYPE.get(directory or "", _canonical_entity_type(entity_type) or entity_type)
    lines = [
        "---",
        f"type: {tag_type}",
        f"aliases: {_format_yaml_list(aliases)}",
        f"triggers: {_format_yaml_list(triggers)}",
        f"tags: {_format_yaml_list(['yerhed', f'entity/{tag_type}'])}",
        f"salience: {salience}",
        f"load_policy: {load_policy}",
        f"sensitivity: {sensitivity}",
    ]
    if sharing_policy:
        lines.append(f"sharing_policy: {sharing_policy}")
    if egress:
        lines.append(f"egress: {egress}")
    safe_handle = baseline_handle.replace('"', '\\"')
    lines.append(f"baseline_handle: \"{safe_handle}\"")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _replace_or_prepend_frontmatter(text: str, frontmatter: str) -> str:
    if text.startswith("---"):
        lines = text.splitlines()
        for idx in range(1, min(len(lines), 120)):
            if lines[idx].strip() == "---":
                return frontmatter.rstrip() + "\n\n" + "\n".join(lines[idx + 1 :]).lstrip() + "\n"
    return frontmatter.rstrip() + "\n\n" + text.lstrip()


def _dedupe_preserve(items: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in _parse_scalar_or_list(items):
        value = str(item).strip()
        key = value.lower()
        if value and key not in seen:
            result.append(value)
            seen.add(key)
    return result


def _merge_unique(*values: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _parse_scalar_or_list(value):
            item = str(item).strip()
            key = item.lower()
            if item and key not in seen:
                merged.append(item)
                seen.add(key)
    return merged


def _strip_leading_h1(text: str) -> tuple[str, str | None]:
    lines = text.strip().splitlines()
    if not lines:
        return "", None
    if lines[0].strip().startswith("# "):
        title = lines[0].strip()[2:].strip()
        return "\n".join(lines[1:]).lstrip(), title
    return text.strip(), None


def _replace_body_h1(body: str, title: str) -> str:
    lines = body.splitlines()
    for idx, line in enumerate(lines):
        if line.strip().startswith("# "):
            lines[idx] = f"# {title.strip()}"
            return "\n".join(lines).rstrip() + "\n"
    prefix = f"# {title.strip()}\n\n"
    return prefix + body.lstrip().rstrip() + "\n"


def upsert_entity_page(
    path: str,
    entity_type: str,
    name: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    aliases: Any = None,
    triggers: Any = None,
    salience: str = "medium",
    load_policy: str = "triggered",
    sensitivity: str = "private",
    baseline_handle: str = "",
    sections: Any = None,
    body: str = "",
    owner_confirmed: bool = False,
    sharing_policy: str = "",
    egress: str = "",
) -> dict[str, Any]:
    """Create or update an explicit-path entity page for high-volume imports."""
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    directory = _normalize_entity_type(entity_type)
    if directory is None:
        return {"ok": False, "error": f"unsupported entity_type {entity_type!r}"}
    if not name or not name.strip():
        return {"ok": False, "error": "name is required"}
    rel, target = _normalize_brain_write_path(path)
    if rel is None or target is None:
        return {"ok": False, "error": "path must stay inside the brain root and use a supported brain top-level path"}
    if Path(rel).parts[0] != directory:
        return {"ok": False, "error": f"path folder must match entity_type {entity_type!r}", "path": rel, "expected_folder": directory}
    salience = (salience or "medium").strip().lower()
    load_policy = (load_policy or "triggered").strip().lower().replace("-", "_")
    sensitivity = _normalize_sensitivity(sensitivity, default="private")
    if salience not in VALID_SALIENCE:
        return {"ok": False, "error": f"salience must be one of {', '.join(sorted(VALID_SALIENCE))}"}
    if load_policy not in VALID_LOAD_POLICIES:
        return {"ok": False, "error": f"load_policy must be one of {', '.join(sorted(VALID_LOAD_POLICIES))}"}
    if not sensitivity:
        return {"ok": False, "error": _sensitivity_error()}

    resolved = resolve_entity(name, entity_type)
    target_rel = rel
    matches = [*resolved.get("exact_matches", []), *resolved.get("possible_matches", [])]
    conflicts = [match for match in matches if match.get("path") != target_rel]
    warnings: list[str] = []
    informational_matches: list[dict[str, Any]] = []
    if conflicts:
        if not owner_confirmed:
            return {
                "ok": False,
                "error": "possible entity match exists; pass owner_confirmed=true with an explicit path to upsert anyway",
                "resolution": resolved,
                "path": target_rel,
            }
        informational_matches = conflicts[:5]

    root = brain_root()
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [target_rel]) or _ensure_paths_clean(root, [target_rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [target_rel]}

    alias_list = _parse_scalar_or_list(aliases)
    trigger_list = _parse_scalar_or_list(triggers)
    section_text = _sections_markdown(sections)
    body_text = body.strip() if body and body.strip() else ""
    stripped_h1 = None
    if body_text:
        body_text, stripped_h1 = _strip_leading_h1(body_text)
        if stripped_h1:
            warnings.append("stripped duplicate leading H1 from body; upsert_entity_page owns the page title")
    handle_source = baseline_handle or body_text or section_text or name
    handle = handle_source.strip().splitlines()[0][:240]
    frontmatter = _entity_frontmatter(entity_type, alias_list, trigger_list, salience, load_policy, sensitivity, handle, sharing_policy, egress)
    existed = target.exists()
    if existed:
        existing = _read_text(target)
        new_body = body_text if body_text else _parse_frontmatter(existing)[1].strip()
        if section_text:
            new_body = (new_body.rstrip() + "\n\n" + section_text).strip()
        content = _replace_or_prepend_frontmatter(new_body + "\n", frontmatter)
    else:
        new_body = body_text if body_text else section_text
        if not new_body:
            new_body = "## Summary\n\nTODO: summarize why this entity matters."
        content = f"{frontmatter}\n# {name.strip()}\n\n{new_body.strip()}\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    result = _commit_structured_change(root, [target_rel], commit_message, source_summary)
    result["created"] = not existed
    result["warnings"] = warnings
    result["informational_matches"] = informational_matches
    result["resolution"] = resolved
    return result


def append_entity_update(
    path: str,
    heading: str,
    body: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
) -> dict[str, Any]:
    """Append a section to any existing brain note and commit locally."""
    if not heading or not heading.strip():
        return {"ok": False, "error": "heading is required"}
    if not body or not body.strip():
        return {"ok": False, "error": "body is required"}
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    rel, target = _normalize_brain_write_path(path)
    if rel is None or target is None:
        return {"ok": False, "error": "path must be a note under the brain root"}
    if not target.exists() or not target.is_file():
        return {"ok": False, "error": "target note does not exist", "path": str(target)}
    root = brain_root()
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [rel]}
    _append_section(target, heading, body)
    return _commit_structured_change(root, [rel], commit_message, source_summary)


def _brain_rel_from_path(path_text: str) -> tuple[str | None, Path | None]:
    rel, target = _normalize_brain_write_path(path_text)
    if rel is not None and target is not None:
        return rel, target
    resolved = _resolve_read_path(path_text)
    if resolved is not None and _is_under(resolved, brain_root()):
        return resolved.relative_to(brain_root()).as_posix(), resolved
    return None, None


def set_canonical_entity_name(
    path: str,
    name: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    aliases: Any = None,
    triggers: Any = None,
    baseline_handle: str = "",
    update_backlinks: bool = False,
) -> dict[str, Any]:
    """Rename an entity's displayed/canonical name without moving the file."""
    if not name or not name.strip():
        return {"ok": False, "error": "name is required"}
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    rel, target = _brain_rel_from_path(path)
    if rel is None or target is None:
        return {"ok": False, "error": "path must be an existing entity note under the brain root"}
    if not target.exists() or not target.is_file():
        return {"ok": False, "error": "target entity note does not exist", "path": str(target)}
    parts = Path(rel).parts
    if not parts or parts[0] not in ENTITY_DIR_TO_TYPE:
        return {"ok": False, "error": "target path is not an entity page", "path": rel}

    root = brain_root()
    resolver_rel = "RESOLVER.md"
    changed = [rel, resolver_rel]
    page_text = _read_text(target)
    fm, body = _parse_frontmatter(page_text)
    old_title = _extract_h1(body or page_text, target.stem.replace("-", " ").title())
    resolver_entry = next((entry for entry in _resolver_entries()[0] if entry.get("path") == rel), {})
    existing_aliases = _merge_unique(fm.get("aliases"), resolver_entry.get("aliases"), aliases)
    if old_title and old_title.lower() != name.strip().lower():
        existing_aliases = _merge_unique(existing_aliases, [old_title])
    existing_aliases = [alias for alias in existing_aliases if alias.lower() != name.strip().lower()]
    trigger_list = _merge_unique(fm.get("triggers"), resolver_entry.get("triggers"), triggers)
    salience = str(fm.get("salience") or resolver_entry.get("salience") or "medium").strip().lower()
    if salience not in VALID_SALIENCE:
        salience = "medium"
    load_policy = str(fm.get("load_policy") or resolver_entry.get("load_policy") or "triggered").strip().lower().replace("-", "_")
    if load_policy not in VALID_LOAD_POLICIES:
        load_policy = "triggered"
    sensitivity = _normalize_sensitivity(fm.get("sensitivity") or resolver_entry.get("sensitivity"), default="private") or "private"
    sharing_policy = str(fm.get("sharing_policy") or resolver_entry.get("sharing_policy") or "").strip()
    egress = str(fm.get("egress") or resolver_entry.get("egress") or "").strip()
    handle = baseline_handle.strip() or str(fm.get("baseline_handle") or resolver_entry.get("baseline_handle") or "").strip()
    if not handle:
        handle = f"{name.strip()} is a Yerhed {ENTITY_DIR_TO_TYPE[parts[0]]} entity."
    frontmatter = _entity_frontmatter(ENTITY_DIR_TO_TYPE[parts[0]], existing_aliases, trigger_list, salience, load_policy, sensitivity, handle, sharing_policy, egress)
    new_body = _replace_body_h1(body, name.strip())

    backlinks_changed: list[str] = []
    backlink_updates: list[tuple[Path, str]] = []
    if update_backlinks and old_title and old_title.lower() != name.strip().lower():
        target_no_ext = rel[:-3] if rel.endswith(".md") else rel
        old_patterns = [
            (f"[[{target_no_ext}|{old_title}]]", f"[[{target_no_ext}|{name.strip()}]]"),
            (f"[[{rel}|{old_title}]]", f"[[{target_no_ext}|{name.strip()}]]"),
            (f"[[{old_title}]]", f"[[{target_no_ext}|{name.strip()}]]"),
        ]
        for note in _iter_text_files(root) or []:
            if note.suffix.lower() != ".md" or note.resolve() == target.resolve():
                continue
            note_rel = note.relative_to(root).as_posix()
            note_text = _read_text(note)
            updated = note_text
            for old, new in old_patterns:
                updated = updated.replace(old, new)
            if updated != note_text:
                backlinks_changed.append(note_rel)
                backlink_updates.append((note, updated))
    changed.extend(backlinks_changed)
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, changed) or _ensure_paths_clean(root, changed)
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": changed}

    target.write_text(_replace_or_prepend_frontmatter(new_body, frontmatter), encoding="utf-8")
    block = _resolver_entry_text(
        name.strip(),
        ENTITY_DIR_TO_TYPE[parts[0]],
        rel,
        existing_aliases,
        trigger_list,
        salience,
        load_policy,
        handle,
        sensitivity=sensitivity,
        sharing_policy=sharing_policy,
        egress=egress,
    )
    resolver = root / resolver_rel
    resolver.write_text(_rewrite_resolver_entry(_read_text(resolver), name.strip(), rel, block), encoding="utf-8")
    for note, updated in backlink_updates:
        note.write_text(updated, encoding="utf-8")
    result = _commit_structured_change(root, changed, commit_message, source_summary)
    result["old_title"] = old_title
    result["new_title"] = name.strip()
    result["backlinks_changed"] = backlinks_changed
    return result


def replace_text(
    path: str,
    replacements: Any,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    expected_count: int = 1,
) -> dict[str, Any]:
    """Structured helper for simple text substitutions without hand-written patch hunks."""
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    brain_rel, brain_target = _brain_rel_from_path(path)
    if brain_target is not None and brain_target.exists() and brain_target.is_file():
        resolved = brain_target
        root = brain_root()
    else:
        resolved = _resolve_read_path(path)
        if resolved is None or not resolved.exists() or not resolved.is_file():
            return {"ok": False, "error": "path must be an existing file under Yerhed repo or brain root", "path": path}
        if _is_under(resolved, brain_root()):
            root = brain_root()
        elif _is_under(resolved, yerhed_repo()):
            root = yerhed_repo()
        else:
            return {"ok": False, "error": "path is outside allowed Yerhed roots", "path": path}
    rel = resolved.relative_to(root).as_posix()
    repl_items = _coerce_items(replacements)
    if not repl_items and isinstance(replacements, dict) and "old" in replacements:
        repl_items = [replacements]
    if not repl_items:
        return {"ok": False, "error": "replacements must be a dict/list with old and new text"}
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [rel]}
    text = _read_text(resolved)
    results: list[dict[str, Any]] = []
    for item in repl_items:
        old = str(item.get("old") or item.get("from") or "")
        new = str(item.get("new") or item.get("to") or "")
        item_expected = int(item.get("expected_count", expected_count))
        if not old:
            return {"ok": False, "error": "replacement old text is required"}
        count = text.count(old)
        if count != item_expected:
            return {"ok": False, "error": "replacement count mismatch", "old": old, "expected_count": item_expected, "actual_count": count}
        text = text.replace(old, new, item_expected)
        results.append({"old": old, "new": new, "count": count})
    resolved.write_text(text, encoding="utf-8")
    commit = _commit_structured_change(root, [rel], commit_message, source_summary)
    commit["replacements"] = results
    return commit


def _frontmatter_drift_for_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    rel = str(entry.get("path") or "")
    if not rel:
        return None
    page = brain_root() / rel
    if not page.exists() or not page.is_file():
        return None
    record = _frontmatter_entity_record(page)
    if not record:
        return {"path": rel, "field": "frontmatter", "resolver": "present", "page": "missing or unparsable"}
    differences: dict[str, dict[str, Any]] = {}
    for field in ["title", "salience", "load_policy", "sensitivity", "sharing_policy", "egress"]:
        resolver_value = entry.get(field) or ""
        page_value = record.get(field) or ""
        if str(resolver_value) != str(page_value):
            differences[field] = {"resolver": resolver_value, "page": page_value}
    for field in ["aliases", "triggers"]:
        resolver_values = set(str(item).lower() for item in entry.get(field, []) or [])
        page_values = set(str(item).lower() for item in record.get(field, []) or [])
        if resolver_values != page_values:
            differences[field] = {"resolver": entry.get(field, []), "page": record.get(field, [])}
    if not differences:
        return None
    return {"path": rel, "title": entry.get("title", ""), "differences": differences}


def sync_resolver_to_frontmatter(
    path: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
) -> dict[str, Any]:
    """Sync one entity page frontmatter and H1 from its RESOLVER.md entry."""
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    rel, target = _brain_rel_from_path(path)
    if rel is None or target is None or not target.exists():
        return {"ok": False, "error": "path must be an existing entity note under the brain root"}
    entry = next((item for item in _resolver_entries()[0] if item.get("path") == rel), None)
    if not entry:
        return {"ok": False, "error": "no resolver entry found for path", "path": rel}
    parts = Path(rel).parts
    if not parts or parts[0] not in ENTITY_DIR_TO_TYPE:
        return {"ok": False, "error": "target path is not an entity page", "path": rel}
    root = brain_root()
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [rel]}
    fm, body = _parse_frontmatter(_read_text(target))
    frontmatter = _entity_frontmatter(
        str(entry.get("type") or ENTITY_DIR_TO_TYPE[parts[0]]),
        _parse_scalar_or_list(entry.get("aliases")),
        _parse_scalar_or_list(entry.get("triggers")),
        str(entry.get("salience") or "medium"),
        str(entry.get("load_policy") or "triggered"),
        _normalize_sensitivity(entry.get("sensitivity"), default=_normalize_sensitivity(fm.get("sensitivity"), default="private")) or "private",
        str(entry.get("baseline_handle") or fm.get("baseline_handle") or ""),
        str(entry.get("sharing_policy") or fm.get("sharing_policy") or ""),
        str(entry.get("egress") or fm.get("egress") or ""),
    )
    new_body = _replace_body_h1(body, str(entry.get("title") or target.stem.replace("-", " ").title()))
    target.write_text(_replace_or_prepend_frontmatter(new_body, frontmatter), encoding="utf-8")
    return _commit_structured_change(root, [rel], commit_message, source_summary)


def create_entity_page(
    entity_type: str,
    name: str,
    context_summary: str,
    sensitivity: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    aliases: Any = None,
    triggers: Any = None,
    salience: str = "medium",
    load_policy: str = "triggered",
) -> dict[str, Any]:
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    sensitivity = _normalize_sensitivity(sensitivity, default="")
    if not sensitivity:
        return {"ok": False, "error": "sensitivity is required and must be a supported label"}
    resolved = resolve_entity(name, entity_type)
    if resolved.get("exact_matches") or resolved.get("possible_matches"):
        return {"ok": False, "error": "matching or possible entity already exists; refusing to create duplicate", "resolution": resolved}
    proposal = propose_entity_page(entity_type, name, context_summary, aliases, triggers, salience, sensitivity, load_policy)
    if not proposal.get("ok"):
        return proposal
    root = brain_root()
    rel = proposal["path"]
    target = root / rel
    if target.exists():
        return {"ok": False, "error": "target entity page already exists", "path": str(target)}
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [rel]}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(proposal["body"], encoding="utf-8")
    return _commit_structured_change(root, [rel], commit_message, source_summary)


def _ensure_salience_section(text: str) -> str:
    if any(line.strip().lower() == "## salience map" for line in text.splitlines()):
        return text
    base = text.rstrip()
    prefix = base + "\n\n" if base else "# Yerhed Brain Resolver\n\n"
    return prefix + "## Salience Map\n\n"


def _rewrite_resolver_entry(text: str, title: str, path: str, block: str) -> str:
    text = _ensure_salience_section(text)
    lines = text.splitlines()
    salience_start = -1
    for idx, line in enumerate(lines):
        if line.strip().lower() == "## salience map":
            salience_start = idx
            break
    if salience_start == -1:
        return text.rstrip() + "\n\n## Salience Map\n\n" + block.rstrip() + "\n"
    entry_start = -1
    entry_end = -1
    for idx in range(salience_start + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("### "):
            section_title = stripped[4:].strip()
            section_end = len(lines)
            for probe in range(idx + 1, len(lines)):
                probe_stripped = lines[probe].strip()
                if probe_stripped.startswith("### ") or probe_stripped.startswith("## "):
                    section_end = probe
                    break
            body = "\n".join(lines[idx:section_end])
            if section_title.lower() == title.strip().lower() or f"path: {path}" in body:
                entry_start = idx
                entry_end = section_end
                break
    block_lines = block.rstrip().splitlines()
    if entry_start != -1:
        new_lines = lines[:entry_start] + block_lines + lines[entry_end:]
    else:
        insert_at = len(lines)
        for idx in range(salience_start + 1, len(lines)):
            if lines[idx].strip().startswith("## "):
                insert_at = idx
                break
        prefix = lines[:insert_at]
        while prefix and not prefix[-1].strip():
            prefix.pop()
        new_lines = prefix + [""] + block_lines + [""] + lines[insert_at:]
    return "\n".join(new_lines).rstrip() + "\n"


def update_resolver_entry(
    entity_type: str,
    name: str,
    path: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    aliases: Any = None,
    triggers: Any = None,
    salience: str = "medium",
    load_policy: str = "triggered",
    baseline_handle: str = "",
    sensitivity: str = "",
    sharing_policy: str = "",
    egress: str = "",
) -> dict[str, Any]:
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    directory = _normalize_entity_type(entity_type)
    if directory is None:
        return {"ok": False, "error": f"unsupported entity_type {entity_type!r}"}
    rel_path = path.strip()
    if rel_path.startswith("[[") and rel_path.endswith("]]"):
        rel_path = rel_path[2:-2].split("|", 1)[0]
    if rel_path.startswith("/") or ".." in Path(rel_path).parts:
        return {"ok": False, "error": "path must be relative to the brain root"}
    if not rel_path.endswith(".md"):
        rel_path += ".md"
    target = brain_root() / rel_path
    if not target.exists() or not target.is_file():
        return {"ok": False, "error": "target entity page does not exist", "path": str(target)}
    if not _is_under(target, brain_root()):
        return {"ok": False, "error": "target entity page is outside brain root"}
    salience = (salience or "medium").strip().lower()
    load_policy = (load_policy or "triggered").strip().lower().replace("-", "_")
    if salience not in VALID_SALIENCE:
        return {"ok": False, "error": f"salience must be one of {', '.join(sorted(VALID_SALIENCE))}"}
    if load_policy not in VALID_LOAD_POLICIES:
        return {"ok": False, "error": f"load_policy must be one of {', '.join(sorted(VALID_LOAD_POLICIES))}"}
    alias_list = _parse_scalar_or_list(aliases)
    sensitivity = _normalize_sensitivity(sensitivity, default="")
    collisions = _resolver_alias_collision([name, *alias_list], target_path=rel_path)
    if collisions:
        return {"ok": False, "error": "alias collision with existing resolver entry", "collisions": collisions}
    resolver = brain_root() / "RESOLVER.md"
    rel = "RESOLVER.md"
    error = _ensure_git_worktree(brain_root()) or _ensure_write_paths_safe(brain_root(), [rel]) or _ensure_paths_clean(brain_root(), [rel])
    if error:
        return {"ok": False, "error": error, "root": str(brain_root()), "changed_files": [rel]}
    block = _resolver_entry_text(
        name,
        entity_type,
        rel_path,
        alias_list,
        _parse_scalar_or_list(triggers),
        salience,
        load_policy,
        baseline_handle,
        sensitivity=sensitivity,
        sharing_policy=sharing_policy,
        egress=egress,
    )
    resolver.write_text(_rewrite_resolver_entry(_read_text(resolver), name, rel_path, block), encoding="utf-8")
    return _commit_structured_change(brain_root(), [rel], commit_message, source_summary)


def update_entity_links(
    path: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    allowed_entity_types: Any = None,
) -> dict[str, Any]:
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    resolved = _resolve_read_path(path)
    if resolved is None or not _is_under(resolved, brain_root()):
        return {"ok": False, "error": "path must be an existing note under the brain root", "path": path}
    if not resolved.exists() or not resolved.is_file():
        return {"ok": False, "error": "target note does not exist", "path": str(resolved)}
    rel = str(resolved.relative_to(brain_root()))
    error = _ensure_git_worktree(brain_root()) or _ensure_write_paths_safe(brain_root(), [rel]) or _ensure_paths_clean(brain_root(), [rel])
    if error:
        return {"ok": False, "error": error, "root": str(brain_root()), "changed_files": [rel]}
    suggestion = suggest_links(_read_text(resolved), allowed_entity_types=allowed_entity_types)
    if suggestion.get("ambiguous_candidates") or suggestion.get("unresolved_candidates"):
        return {"ok": False, "error": "ambiguous or unresolved entity links; review before writing", "suggestion": suggestion}
    suggested = suggestion.get("suggested_draft", "")
    if suggested == _read_text(resolved):
        return {"ok": True, "changed": False, "path": str(resolved), "message": "no link changes suggested", "suggestion": suggestion}
    resolved.write_text(suggested, encoding="utf-8")
    result = _commit_structured_change(brain_root(), [rel], commit_message, source_summary)
    result["suggestion"] = suggestion
    return result


def _scope_root(scope: str | None) -> Path:
    normalized = (scope or "all").strip().lower()
    if normalized not in BRAIN_SCOPES:
        raise ValueError(f"unsupported scope {scope!r}; expected one of {', '.join(sorted(BRAIN_SCOPES))}")
    return (brain_root() / BRAIN_SCOPES[normalized]).resolve()


def _approved_root_for(path: Path) -> Path | None:
    for root in (yerhed_repo(), brain_root()):
        if _is_under(path, root):
            return root.resolve()
    return None


def _iter_text_files(root: Path):
    allowed_root = _approved_root_for(root)
    if allowed_root is None:
        return
    safe_root_file = _safe_existing_file_under_root(root, allowed_root)
    if safe_root_file is not None:
        if safe_root_file.suffix.lower() in TEXT_SUFFIXES or safe_root_file.name in {"log"}:
            yield safe_root_file
        return
    if not root.exists() or root.is_symlink():
        return
    for current_root, dirs, files in os.walk(root):
        base = Path(current_root)
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not (base / d).is_symlink()
        ]
        for name in files:
            path = base / name
            if path.suffix.lower() not in TEXT_SUFFIXES and name not in {"log"}:
                continue
            safe_path = _safe_existing_file_under_root(path, allowed_root)
            if safe_path is not None:
                yield safe_path


def _line_matches(query_terms: list[str], line: str) -> bool:
    lowered = line.lower()
    return all(term in lowered for term in query_terms)


def search(query: str, scope: str = "all", limit: int = 10) -> dict[str, Any]:
    """Search the Yerhed brain root and return path/line/snippet matches."""
    if not query or not query.strip():
        return {"ok": False, "error": "query is required", "results": [], "evidence_spans": []}
    try:
        root = _scope_root(scope)
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "results": [], "evidence_spans": []}
    if not _is_under(root, brain_root()):
        return {"ok": False, "error": "scope resolved outside brain root", "results": [], "evidence_spans": []}

    terms = [term for term in re.split(r"\s+", query.strip().lower()) if term]
    matches: list[dict[str, Any]] = []
    evidence_spans: list[dict[str, Any]] = []
    max_results = max(1, min(int(limit or 10), 100))
    for path in _iter_text_files(root) or []:
        text = _read_text(path)
        if not text:
            continue
        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            if _line_matches(terms, line):
                start = max(1, idx - 1)
                end = min(len(lines), idx + 1)
                snippet = "\n".join(lines[start - 1 : end])
                span = _make_evidence_span(path, start, end, f"search match for {query!r}")
                evidence_spans.append(span)
                matches.append(
                    {
                        "path": str(path),
                        "line": idx,
                        "snippet": snippet,
                        "evidence_span": span,
                    }
                )
                if len(matches) >= max_results:
                    return {"ok": True, "query": query, "scope": scope, "root": str(root), "results": matches, "evidence_spans": evidence_spans}
    return {"ok": True, "query": query, "scope": scope, "root": str(root), "results": matches, "evidence_spans": evidence_spans}

def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _resolve_read_path(path_text: str) -> Path | None:
    raw = Path(path_text).expanduser()
    candidates = [raw] if raw.is_absolute() else [yerhed_repo() / raw, brain_root() / raw]
    for candidate in candidates:
        safe_path = _safe_existing_file(candidate)
        if safe_path is not None:
            return safe_path
    return None


def read_file(path: str, max_chars: int = 20000) -> dict[str, Any]:
    """Read a file under the Yerhed repo or brain root only."""
    resolved = _resolve_read_path(path)
    if resolved is None:
        return {"ok": False, "error": "path is outside allowed Yerhed roots", "path": path, "evidence_spans": []}
    if not resolved.exists() or not resolved.is_file():
        return {"ok": False, "error": "file not found", "path": str(resolved), "evidence_spans": []}
    content, line_start, line_end = _read_text_with_line_span(resolved, max_chars=max_chars)
    evidence_spans = []
    evidence_span = None
    if line_start and line_end:
        evidence_span = _make_evidence_span(resolved, line_start, line_end, "read_file loaded content")
        evidence_spans.append(evidence_span)
    return {"ok": True, "path": str(resolved), "content": content, "evidence_span": evidence_span, "evidence_spans": evidence_spans}

def _slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "project"


def read_project(project: str) -> dict[str, Any]:
    """Read a matching brain project page."""
    projects_root = brain_root() / "projects"
    wanted = _slug(project)
    candidates = []
    exact = _safe_existing_file_under_root(projects_root / f"{wanted}.md", brain_root())
    if exact is not None:
        candidates = [exact]
    else:
        for path in sorted(projects_root.glob("*.md")):
            safe_path = _safe_existing_file_under_root(path, brain_root())
            if safe_path is None:
                continue
            stem = _slug(safe_path.stem)
            if wanted in stem or stem in wanted:
                candidates.append(safe_path)
        if not candidates:
            query_result = search(project, scope="projects", limit=5)
            seen = set()
            for result in query_result.get("results", []):
                p = _safe_existing_file_under_root(Path(result["path"]), brain_root())
                if p is not None and p not in seen:
                    candidates.append(p)
                    seen.add(p)
    if not candidates:
        return {"ok": False, "error": "no matching project page", "project": project, "evidence_spans": []}
    if len(candidates) > 1:
        matches = []
        evidence_spans: list[dict[str, Any]] = []
        for path in candidates[:5]:
            excerpt, line_start, line_end = _read_text_with_line_span(path, max_chars=1200)
            span = _make_evidence_span(path, line_start, line_end, f"project match excerpt for {project!r}") if line_start and line_end else None
            if span:
                evidence_spans.append(span)
            matches.append({"path": str(path), "excerpt": excerpt, "evidence_span": span})
        return {
            "ok": True,
            "project": project,
            "matches": matches,
            "evidence_spans": evidence_spans,
        }
    path = candidates[0]
    content, line_start, line_end = _read_text_with_line_span(path, max_chars=30000)
    span = _make_evidence_span(path, line_start, line_end, f"read_project loaded {project!r}") if line_start and line_end else None
    return {"ok": True, "project": project, "path": str(path), "content": content, "evidence_span": span, "evidence_spans": [span] if span else []}

def _bullet_lines(text: str, max_items: int = 12) -> list[str]:
    items = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:])
        if len(items) >= max_items:
            break
    return items


def _recent_log_headings(max_items: int = 8) -> list[str]:
    text = _read_text(brain_root() / "log.md")
    headings = [line.strip("# ") for line in text.splitlines() if line.startswith("## ")]
    return headings[-max_items:]


def what_matters_now() -> dict[str, Any]:
    """Return a compact grounded current-state summary from Yerhed files."""
    repo = yerhed_repo()
    memory_path = _first_existing(repo / "MEMORY.md", repo / "MEMORY.example.md")
    user_path = _first_existing(repo / "USER.md", repo / "USER.example.md")
    open_loops_path = brain_root() / "projects" / "open-loops.md"
    yerhed_project_path = brain_root() / "projects" / "yerhed.md"
    log_path = brain_root() / "log.md"
    memory, memory_start, memory_end = _read_text_with_line_span(memory_path, max_chars=4000)
    user, user_start, user_end = _read_text_with_line_span(user_path, max_chars=3000)
    open_loops, loops_start, loops_end = _read_text_with_line_span(open_loops_path, max_chars=5000)
    yerhed_project, project_start, project_end = _read_text_with_line_span(yerhed_project_path, max_chars=5000)
    log_headings = _recent_log_headings()
    bullets = _bullet_lines(open_loops, max_items=10)
    summary = [
        "Yerhed remains the private file-first memory layer; Codex remains the execution engine.",
        "Current open loops are drawn from brain/projects/open-loops.md, not guessed.",
    ]
    if bullets:
        summary.append("Top open-loop signals: " + "; ".join(bullets[:4]))
    if log_headings:
        summary.append("Recent log signals: " + "; ".join(log_headings[-4:]))
    evidence_spans: list[dict[str, Any]] = []
    for path, start, end, note in [
        (memory_path, memory_start, memory_end, "what_matters_now read operational memory"),
        (user_path, user_start, user_end, "what_matters_now read user context"),
        (open_loops_path, loops_start, loops_end, "what_matters_now read open loops"),
        (yerhed_project_path, project_start, project_end, "what_matters_now read Yerhed project page"),
    ]:
        if start and end:
            evidence_spans.append(_make_evidence_span(path, start, end, note))
    if log_path.exists():
        line_count = len(_read_text(log_path).splitlines())
        if line_count:
            start = max(1, line_count - 59)
            evidence_spans.append(_make_evidence_span(log_path, start, line_count, "what_matters_now read recent log headings"))
    return {
        "ok": True,
        "summary": "\n".join(summary),
        "open_loops": bullets,
        "recent_log_headings": log_headings,
        "evidence_spans": evidence_spans,
        "evidence_summary": summarize_evidence(evidence_spans),
        "evidence": [
            {"path": str(memory_path), "excerpt": memory[:1200]},
            {"path": str(user_path), "excerpt": user[:800]},
            {"path": str(open_loops_path), "excerpt": open_loops[:1200]},
            {"path": str(yerhed_project_path), "excerpt": yerhed_project[:1200]},
            {"path": str(log_path), "recent_headings": log_headings},
        ],
    }

def morning_brief() -> dict[str, Any]:
    """Run the review-only Yerhed morning brief protocol."""
    current = what_matters_now()
    open_loops = current.get("open_loops", [])
    recent = current.get("recent_log_headings", [])
    suggested_tasks = []
    for item in open_loops:
        lower = item.lower()
        if "validate" in lower or "create" in lower or "setup" in lower or "mcp" in lower:
            suggested_tasks.append(item)
    evidence_spans = current.get("evidence_spans", [])
    return {
        "ok": True,
        "needs_action": open_loops[:5],
        "changed": recent[-5:],
        "ignore": [
            "Do not create cron, launchd, daemons, shell watchers, pushes, or third-party side effects from this brief.",
            "Treat memory as context, not permission to act.",
        ],
        "suggested_codex_tasks": suggested_tasks[:5],
        "proposed_yerhed_diffs": [],
        "evidence_spans": evidence_spans,
        "evidence_summary": summarize_evidence(evidence_spans),
        "evidence": current.get("evidence", []),
    }

def _normalize_changed_files(changed_files: Any) -> list[str]:
    if changed_files is None:
        return []
    if isinstance(changed_files, str):
        return [line.strip() for line in changed_files.splitlines() if line.strip()]
    if isinstance(changed_files, (list, tuple)):
        return [str(item) for item in changed_files]
    return [str(changed_files)]


def _has_durable_change(summary: str, changed_files: list[str]) -> bool:
    summary_lower = summary.strip().lower()
    if not summary_lower or summary_lower in {"none", "no", "n/a", "na", "no durable change"}:
        return False
    return True


def _looks_sensitive(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in SENSITIVE_HINTS)


def _project_update_material(repo_path: str, work_summary: str, durable_summary: str, changed_files: list[str]) -> tuple[Path, str, str]:
    slug = _slug(Path(repo_path or "project").name)
    target = brain_root() / "projects" / f"{slug}.md"
    old = _read_text(target)
    if not old:
        old = f"# {Path(repo_path or slug).name}\n\n## Summary\n\nProject page created by Yerhed closeout.\n"
    date = _dt.date.today().isoformat()
    files = "\n".join(f"  - `{item}`" for item in changed_files) or "  - none supplied"
    block = (
        f"\n## Update: {date}\n\n"
        f"- Repo: `{repo_path}`\n"
        f"- Work: {work_summary.strip() or 'not supplied'}\n"
        f"- Durable state: {durable_summary.strip() or 'not supplied'}\n"
        f"- Changed files:\n{files}\n"
    )
    new = old.rstrip() + "\n" + block + "\n"
    rel = target.relative_to(brain_root())
    patch = "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
    )
    return target, block.strip() + "\n", patch


def _default_closeout_commit_message(repo_path: str) -> str:
    name = Path(repo_path or "project").name or "project"
    return f"Record {name} closeout"


def closeout_check(
    repo_path: str,
    work_summary: str,
    durable_state_change_summary: str,
    changed_files: Any = None,
    dry_run: bool = False,
    commit_message: str = "",
) -> dict[str, Any]:
    """Close out durable project work, writing non-sensitive memory by default."""
    changed = _normalize_changed_files(changed_files)
    durable = durable_state_change_summary or ""
    if not _has_durable_change(durable, changed):
        return {
            "ok": True,
            "disposition": "skipped",
            "reason": "no durable project state change was supplied",
            "target_files": [],
            "proposed_patch": "",
        }
    target, note, patch = _project_update_material(repo_path, work_summary, durable, changed)
    if _looks_sensitive("\n".join([work_summary, durable])):
        return {
            "ok": True,
            "disposition": "proposed",
            "reason": "sensitive or ambiguous memory should be reviewed before writing",
            "target_files": [str(target)],
            "proposed_note": note,
            "proposed_patch": patch,
            "must_show_proposal": True,
        }
    already_updated = any(_is_under(Path(item).expanduser().resolve(), yerhed_repo()) or _is_under(Path(item).expanduser().resolve(), brain_root()) for item in changed if item.startswith("/"))
    if already_updated:
        return {
            "ok": True,
            "disposition": "updated",
            "reason": "changed files already include Yerhed or brain-root files",
            "target_files": [str(target)],
            "proposed_patch": "",
        }
    if dry_run:
        return {
            "ok": True,
            "disposition": "proposed",
            "reason": "dry_run requested; this is the exact closeout note that would be written",
            "target_files": [str(target)],
            "proposed_note": note,
            "proposed_patch": patch,
            "must_show_proposal": True,
            "write_expected": True,
        }
    root = brain_root()
    rel = target.relative_to(root).as_posix()
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {
            "ok": True,
            "disposition": "proposed",
            "reason": f"memory write blocked: {error}",
            "target_files": [str(target)],
            "proposed_note": note,
            "proposed_patch": patch,
            "must_show_proposal": True,
            "write_expected": True,
            "error": error,
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    old = _read_text(target)
    if not old:
        old = f"# {Path(repo_path or rel).name}\n\n## Summary\n\nProject page created by Yerhed closeout.\n"
    target.write_text(old.rstrip() + "\n\n" + note, encoding="utf-8")
    commit = _commit_structured_change(root, [rel], commit_message or _default_closeout_commit_message(repo_path), f"Closeout for {repo_path or rel}: {durable.strip()}")
    if not commit.get("ok"):
        commit.update(
            {
                "disposition": "proposed",
                "reason": "memory write attempted but validation or commit failed; show the proposed note",
                "target_files": [str(target)],
                "proposed_note": note,
                "proposed_patch": patch,
                "must_show_proposal": True,
                "write_expected": True,
            }
        )
        return commit
    commit.update(
        {
            "disposition": "updated",
            "reason": "durable non-sensitive project state changed; Yerhed project memory was updated and locally committed",
            "target_files": [str(target)],
            "written_note": note,
            "proposed_patch": "",
            "write_expected": True,
        }
    )
    return commit




def _coerce_items(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return _coerce_items(parsed)
    if isinstance(value, dict):
        if isinstance(value.get("items"), list):
            return [item for item in value["items"] if isinstance(item, dict)]
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _resolve_wikilink_target(target_text: str) -> tuple[Path | None, str]:
    target = (target_text or "").split("|", 1)[0].split("#", 1)[0].strip()
    if not target:
        return None, "empty target"
    if target.startswith("/") or ".." in Path(target).parts:
        return None, "target escapes brain root"
    root = brain_root()
    candidates: list[Path] = []
    if target.endswith(".md"):
        candidates.append(root / target)
    elif "/" in target:
        candidates.append(root / f"{target}.md")
        candidates.append(root / target)
    else:
        candidates.append(root / f"{target}.md")
        slug = _slug(target)
        for path in _iter_text_files(root) or []:
            if path.suffix.lower() == ".md" and (_slug(path.stem) == slug or path.stem == target):
                candidates.append(path)
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if _is_under(resolved, root) and resolved.exists() and resolved.is_file():
            return resolved, ""
    return None, "unresolved"


def _planned_wikilink_resolves(target_text: str, planned_paths: set[str]) -> bool:
    target = (target_text or "").split("|", 1)[0].split("#", 1)[0].strip()
    if not target or target.startswith("/") or ".." in Path(target).parts:
        return False
    candidates = {target}
    if target.endswith(".md"):
        candidates.add(target[:-3])
    else:
        candidates.add(f"{target}.md")
    return bool(candidates & planned_paths)


def _memory_item_wants_resolver_update(item: dict[str, Any]) -> bool:
    value = item.get("resolver_intent", item.get("resolver"))
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"add", "update", "upsert", "true", "yes"}


def _memory_import_sort_key(row: tuple[dict[str, Any], str, Path, str]) -> tuple[int, str]:
    item, rel, _target, status = row
    folder = Path(rel).parts[0] if Path(rel).parts else ""
    action = str(item.get("action") or "upsert").strip().lower()
    if folder == "concepts" and action in {"create_spine", "spine", "upsert", "write", "written"}:
        phase = 0
    elif status == "written" and folder in ENTITY_DIR_TO_TYPE:
        phase = 1
    elif status == "merged" and folder in ENTITY_DIR_TO_TYPE:
        phase = 2
    elif folder in {"sources", "archive"}:
        phase = 3
    else:
        phase = 4
    return phase, rel


def validate_wikilinks(ignore_schema_examples: bool = True) -> dict[str, Any]:
    """Validate Obsidian-style wikilinks and resolver/page consistency."""
    root = brain_root()
    unresolved: list[dict[str, Any]] = []
    self_links: list[dict[str, Any]] = []
    graph_hygiene_warnings: list[dict[str, Any]] = []
    scanned_files = 0
    link_count = 0
    skipped_files = 0
    for path in _iter_text_files(root) or []:
        if path.suffix.lower() != ".md":
            continue
        rel = path.relative_to(root).as_posix()
        if _should_ignore_wikilink_scan_file(rel, ignore_schema_examples):
            skipped_files += 1
            continue
        text = _read_text(path)
        scanned_files += 1
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in re.finditer(r"\[\[([^\]]+)\]\]", line):
                raw_target = match.group(1)
                target_name = raw_target.split("|", 1)[0].split("#", 1)[0].strip()
                if _should_ignore_wikilink_target(target_name, ignore_schema_examples):
                    continue
                link_count += 1
                pre_resolve_hygiene_warning = None
                if _normalized_wikilink_target(raw_target) in GRAPH_CATEGORY_HUB_TARGETS:
                    pre_resolve_hygiene_warning = _graph_hygiene_warning_for_link(rel, path, raw_target, line_no, None)
                    if pre_resolve_hygiene_warning:
                        graph_hygiene_warnings.append(pre_resolve_hygiene_warning)
                resolved, reason = _resolve_wikilink_target(raw_target)
                if resolved is None:
                    unresolved.append({"source": rel, "line": line_no, "target": raw_target, "reason": reason})
                    continue
                hygiene_warning = None if pre_resolve_hygiene_warning else _graph_hygiene_warning_for_link(rel, path, raw_target, line_no, resolved)
                if hygiene_warning:
                    graph_hygiene_warnings.append(hygiene_warning)
                if resolved == path.resolve():
                    self_links.append({"source": rel, "line": line_no, "target": raw_target})

    resolver_mismatches: list[dict[str, Any]] = []
    resolver_frontmatter_drift: list[dict[str, Any]] = []
    for entry in salience_map(include_page_records=False).get("entries", []):
        entry_path = str(entry.get("path", ""))
        resolved, reason = _resolve_wikilink_target(entry_path)
        if resolved is None:
            resolver_mismatches.append({"entry": entry.get("title", ""), "path": entry_path, "reason": reason})
            continue
        expected_dir = _normalize_entity_type(str(entry.get("type", "")))
        try:
            rel_parts = resolved.relative_to(root).parts
        except ValueError:
            rel_parts = ()
        if expected_dir and rel_parts and rel_parts[0] != expected_dir:
            resolver_mismatches.append(
                {"entry": entry.get("title", ""), "path": entry_path, "reason": f"resolver type maps to {expected_dir} but page is under {rel_parts[0]}"}
            )
        drift = _frontmatter_drift_for_entry(entry)
        if drift:
            resolver_frontmatter_drift.append(drift)

    has_errors = bool(unresolved or self_links or resolver_mismatches)
    report_lines = [
        "# Wikilink Validation",
        "",
        f"- scanned files: {scanned_files}",
        f"- skipped files: {skipped_files}",
        f"- links checked: {link_count}",
        f"- unresolved links: {len(unresolved)}",
        f"- self-links: {len(self_links)}",
        f"- resolver/page mismatches: {len(resolver_mismatches)}",
        f"- resolver/frontmatter drift: {len(resolver_frontmatter_drift)}",
        f"- graph hygiene warnings: {len(graph_hygiene_warnings)}",
    ]
    if graph_hygiene_warnings:
        report_lines.extend(["", "## Graph Hygiene Warnings", ""])
        for row in graph_hygiene_warnings[:40]:
            report_lines.append(f"- {row.get('source')}:{row.get('line')} -> {row.get('target')} ({row.get('reason')})")
        if len(graph_hygiene_warnings) > 40:
            report_lines.append(f"- ... {len(graph_hygiene_warnings) - 40} more")
    return {
        "ok": True,
        "has_errors": has_errors,
        "root": str(root),
        "counts": {
            "scanned_files": scanned_files,
            "skipped_files": skipped_files,
            "links_checked": link_count,
            "unresolved": len(unresolved),
            "self_links": len(self_links),
            "resolver_page_mismatches": len(resolver_mismatches),
            "resolver_frontmatter_drift": len(resolver_frontmatter_drift),
            "graph_hygiene_warnings": len(graph_hygiene_warnings),
        },
        "unresolved": unresolved,
        "self_links": self_links,
        "resolver_page_mismatches": resolver_mismatches,
        "resolver_frontmatter_drift": resolver_frontmatter_drift,
        "graph_hygiene_warnings": graph_hygiene_warnings,
        "obsidian_report": "\n".join(report_lines),
    }


def batch_update_resolver_entries(
    entries: Any,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
    include_low_salience: bool = False,
) -> dict[str, Any]:
    """Add/update multiple RESOLVER.md entries in one local commit."""
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    items = _coerce_items(entries)
    if not items:
        return {"ok": False, "error": "entries must be a non-empty list"}
    root = brain_root()
    rel = "RESOLVER.md"
    resolver = root / rel
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [rel]}
    text = _read_text(resolver)
    results: list[dict[str, Any]] = []
    proposed_text = text
    for item in items:
        name = str(item.get("name") or item.get("title") or "").strip()
        entity_type = str(item.get("entity_type") or item.get("type") or "").strip()
        rel_path = str(item.get("path") or "").strip()
        salience = str(item.get("salience") or "medium").strip().lower()
        load_policy = str(item.get("load_policy") or "triggered").strip().lower().replace("-", "_")
        if not name or not entity_type or not rel_path:
            results.append({"name": name, "path": rel_path, "status": "skipped", "reason": "missing name/entity_type/path"})
            continue
        if salience == "low" and not include_low_salience:
            results.append({"name": name, "path": rel_path, "status": "skipped", "reason": "low salience skipped by default"})
            continue
        directory = _normalize_entity_type(entity_type)
        if directory is None:
            results.append({"name": name, "path": rel_path, "status": "skipped", "reason": "unsupported entity_type"})
            continue
        normalized_path, target = _normalize_brain_write_path(rel_path)
        if normalized_path is None or target is None or not target.exists():
            results.append({"name": name, "path": rel_path, "status": "skipped", "reason": "target page missing or outside brain root"})
            continue
        if load_policy not in VALID_LOAD_POLICIES:
            load_policy = "triggered"
        if salience not in VALID_SALIENCE:
            salience = "medium"
        alias_list = _parse_scalar_or_list(item.get("aliases"))
        collisions = _resolver_alias_collision([name, *alias_list], target_path=normalized_path)
        if collisions:
            results.append({"name": name, "path": normalized_path, "status": "skipped", "reason": "alias collision", "collisions": collisions})
            continue
        block = _resolver_entry_text(
            name,
            entity_type,
            normalized_path,
            alias_list,
            _parse_scalar_or_list(item.get("triggers")),
            salience,
            load_policy,
            str(item.get("baseline_handle") or "").strip(),
            sensitivity=_normalize_sensitivity(item.get("sensitivity"), default=""),
            sharing_policy=str(item.get("sharing_policy") or "").strip(),
            egress=str(item.get("egress") or "").strip(),
        )
        proposed_text = _rewrite_resolver_entry(proposed_text, name, normalized_path, block)
        results.append({"name": name, "path": normalized_path, "status": "updated"})
    if proposed_text == text:
        return {"ok": True, "changed": False, "results": results, "pushed": False}
    resolver.write_text(proposed_text, encoding="utf-8")
    commit = _commit_structured_change(root, [rel], commit_message, source_summary)
    commit["results"] = results
    return commit


def _memory_item_id(item: dict[str, Any]) -> str:
    return str(item.get("id") or item.get("memory_id") or item.get("stable_id") or "").strip()


def _ledger_existing_ids(ledger: Path) -> set[str]:
    text = _read_text(ledger)
    return set(re.findall(r"\bM\d{3,}\b", text))


def _memory_item_destination(item: dict[str, Any]) -> str:
    return str(item.get("destination") or item.get("path") or item.get("dest") or "").strip()


def _memory_item_markdown(item: dict[str, Any]) -> str:
    memory_id = _memory_item_id(item)
    text = str(item.get("distilled_text") or item.get("text") or item.get("summary") or "").strip()
    links = _parse_scalar_or_list(item.get("links"))
    lines = [f"## Import {memory_id}", "", text or "TODO: add distilled memory text."]
    if links:
        lines.extend(["", "### Links", ""])
        for link in links:
            target = link if link.startswith("[[") else f"[[{link}]]"
            lines.append(f"- {target}")
    return "\n".join(lines).strip() + "\n"


def _create_import_note(item: dict[str, Any], rel: str) -> str:
    title = str(item.get("name") or item.get("title") or Path(rel).stem.replace("-", " ").title()).strip()
    top = Path(rel).parts[0]
    entity_type = ENTITY_DIR_TO_TYPE.get(top, top.rstrip("s"))
    sensitivity = _normalize_sensitivity(item.get("sensitivity"), default="private") or "private"
    load_policy = str(item.get("load_policy") or "triggered").strip().lower().replace("-", "_")
    if load_policy not in VALID_LOAD_POLICIES:
        load_policy = "triggered"
    baseline = str(item.get("baseline_handle") or item.get("distilled_text") or title).strip().splitlines()[0][:240]
    frontmatter = _entity_frontmatter(
        entity_type,
        _parse_scalar_or_list(item.get("aliases")),
        _parse_scalar_or_list(item.get("triggers")),
        str(item.get("salience") or "medium").strip().lower() if str(item.get("salience") or "medium").strip().lower() in VALID_SALIENCE else "medium",
        load_policy,
        sensitivity,
        baseline,
        sharing_policy=str(item.get("sharing_policy") or "").strip(),
        egress=str(item.get("egress") or "").strip(),
    )
    return f"{frontmatter}\n# {title}\n\n{_memory_item_markdown(item)}"


def _append_ledger(ledger: Path, rows: list[dict[str, str]], source_summary: str) -> None:
    if not ledger.exists():
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text("# Memory Import Coverage Ledger\n", encoding="utf-8")
    timestamp = _dt.datetime.now().isoformat(timespec="seconds")
    lines = ["", f"## Import Run {timestamp}", "", f"Source: {source_summary.strip()}", "", "| ID | Status | Destination | Action | Notes |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| {row.get('id', '')} | {row.get('status', '')} | `{row.get('destination', '')}` | {row.get('action', '')} | {row.get('notes', '')} |")
    existing = _read_text(ledger).rstrip()
    ledger.write_text(existing + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


def import_memory_plan(
    items: Any,
    policy_basis: str = "",
    source_summary: str = "",
    commit_message: str = "Import memory plan",
    dry_run: bool = True,
    commit_strategy: str = "single",
    ledger_path: str = "sources/import-ledgers/memory-import.md",
) -> dict[str, Any]:
    """Import a classified memory plan with full ID coverage reporting."""
    plan_items = _coerce_items(items)
    if not plan_items:
        return {"ok": False, "error": "items must be a non-empty list"}
    if commit_strategy not in {"single", "per_file"}:
        return {"ok": False, "error": "commit_strategy must be single or per_file"}
    if not dry_run:
        error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
        if error:
            return {"ok": False, "error": error}
    root = brain_root()
    ledger_rel, ledger = _normalize_brain_write_path(ledger_path)
    if ledger_rel is None or ledger is None or not (ledger_rel.startswith("sources/") or ledger_rel.startswith("archive/")):
        return {"ok": False, "error": "ledger_path must stay under sources/ or archive/"}
    existing_ids = _ledger_existing_ids(ledger)
    planned_paths: set[str] = set()
    for planned_item in plan_items:
        planned_dest = _memory_item_destination(planned_item)
        planned_rel, _planned_target = _normalize_brain_write_path(planned_dest) if planned_dest else (None, None)
        if planned_rel:
            planned_paths.add(planned_rel)
            planned_paths.add(planned_rel[:-3] if planned_rel.endswith(".md") else planned_rel)
    seen_ids: set[str] = set()
    coverage: list[dict[str, str]] = []
    write_plan: list[tuple[dict[str, Any], str, Path, str]] = []
    for item in plan_items:
        memory_id = _memory_item_id(item)
        action = str(item.get("action") or "upsert").strip().lower()
        destination = _memory_item_destination(item)
        notes = ""
        status = "review"
        if not memory_id:
            notes = "missing stable ID"
            status = "review"
        elif memory_id in seen_ids or memory_id in existing_ids:
            notes = "duplicate ID"
            status = "duplicate"
        elif action in {"skip", "skipped"}:
            status = "skipped"
            notes = "action requested skip"
        elif action in {"review", "needs_review"}:
            status = "review"
            notes = "action requested review"
        elif not destination:
            status = "review"
            notes = "missing destination"
        else:
            rel, target = _normalize_brain_write_path(destination)
            if rel is None or target is None:
                status = "review"
                notes = "destination outside brain root or unsupported"
            else:
                unresolved_links = []
                for link in _parse_scalar_or_list(item.get("links")):
                    resolved, reason = _resolve_wikilink_target(link)
                    if resolved is None and not _planned_wikilink_resolves(link, planned_paths):
                        unresolved_links.append(f"{link}: {reason}")
                if unresolved_links:
                    status = "review"
                    notes = "unresolved links: " + "; ".join(unresolved_links[:3])
                else:
                    status = "merged" if target.exists() else "written"
                    write_plan.append((item, rel, target, status))
        if memory_id:
            seen_ids.add(memory_id)
        coverage.append({"id": memory_id, "status": status, "destination": destination, "action": action, "notes": notes})

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "coverage": coverage,
            "ledger_path": str(ledger),
            "would_write_count": sum(1 for row in coverage if row["status"] in {"written", "merged"}),
            "would_update_resolver_count": sum(1 for item, _rel, _target, status in write_plan if status in {"written", "merged"} and _memory_item_wants_resolver_update(item)),
            "apply_order": [rel for _item, rel, _target, _status in sorted(write_plan, key=_memory_import_sort_key)],
            "pushed": False,
        }

    write_plan = sorted(write_plan, key=_memory_import_sort_key)
    resolver_update_items = [item for item, _rel, _target, status in write_plan if status in {"written", "merged"} and _memory_item_wants_resolver_update(item)]
    paths = sorted({rel for _, rel, _, _ in write_plan} | {ledger_rel} | ({"RESOLVER.md"} if resolver_update_items else set()))
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, paths) or _ensure_paths_clean(root, paths)
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": paths, "coverage": coverage}

    if commit_strategy == "single":
        for item, rel, target, status in write_plan:
            target.parent.mkdir(parents=True, exist_ok=True)
            if status == "written":
                target.write_text(_create_import_note(item, rel), encoding="utf-8")
            else:
                target.write_text(_read_text(target).rstrip() + "\n\n" + _memory_item_markdown(item), encoding="utf-8")
        if resolver_update_items:
            resolver = root / "RESOLVER.md"
            proposed = _read_text(resolver)
            for item in resolver_update_items:
                rel = _memory_item_destination(item)
                normalized_rel, _target = _normalize_brain_write_path(rel)
                if not normalized_rel:
                    continue
                salience = str(item.get("salience") or "medium").strip().lower()
                if salience == "low":
                    continue
                if salience not in VALID_SALIENCE:
                    salience = "medium"
                load_policy = str(item.get("load_policy") or "triggered").strip().lower().replace("-", "_")
                if load_policy not in VALID_LOAD_POLICIES:
                    load_policy = "triggered"
                entity_type = str(item.get("entity_type") or item.get("category") or Path(normalized_rel).parts[0]).strip()
                name = str(item.get("name") or item.get("title") or Path(normalized_rel).stem.replace("-", " ").title()).strip()
                block = _resolver_entry_text(
                    name,
                    entity_type,
                    normalized_rel,
                    _parse_scalar_or_list(item.get("aliases")),
                    _parse_scalar_or_list(item.get("triggers")),
                    salience,
                    load_policy,
                    str(item.get("baseline_handle") or item.get("distilled_text") or "").strip().splitlines()[0][:240],
                    sensitivity=_normalize_sensitivity(item.get("sensitivity"), default=""),
                    sharing_policy=str(item.get("sharing_policy") or "").strip(),
                    egress=str(item.get("egress") or "").strip(),
                )
                proposed = _rewrite_resolver_entry(proposed, name, normalized_rel, block)
            resolver.write_text(proposed, encoding="utf-8")
        _append_ledger(ledger, coverage, source_summary)
        commit = _commit_structured_change(root, paths, commit_message, source_summary)
        commit["coverage"] = coverage
        commit["ledger_path"] = str(ledger)
        return commit

    commits: list[str] = []
    for item, rel, target, status in write_plan:
        item_id = _memory_item_id(item)
        target.parent.mkdir(parents=True, exist_ok=True)
        if status == "written":
            target.write_text(_create_import_note(item, rel), encoding="utf-8")
        else:
            target.write_text(_read_text(target).rstrip() + "\n\n" + _memory_item_markdown(item), encoding="utf-8")
        _append_ledger(ledger, [row for row in coverage if row.get("id") == item_id], source_summary)
        commit = _commit_structured_change(root, sorted({rel, ledger_rel}), f"{commit_message.strip()} {item_id}".strip(), source_summary)
        if not commit.get("ok"):
            commit["coverage"] = coverage
            return commit
        commits.append(commit.get("commit", ""))
    return {"ok": True, "root": str(root), "changed_files": paths, "commits": commits, "coverage": coverage, "ledger_path": str(ledger), "pushed": False}

def _normalize_sequence(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts: list[str] = []
        for line in value.splitlines():
            parts.extend(piece.strip() for piece in line.split(","))
        return [part for part in parts if part]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _extract_sensitivity_label(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:40]:
        stripped = line.strip()
        if stripped == "---":
            return None
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if key.strip().lower().replace("-", "_") in {"sensitivity", "privacy", "sharing_policy", "egress"}:
            normalized = _normalize_sensitivity(value, default="")
            return normalized or None
    return None


def _source_sensitivity(path_text: str) -> dict[str, Any]:
    resolved = _resolve_read_path(path_text)
    if resolved is None:
        return {
            "path": path_text,
            "resolved_path": "",
            "exists": False,
            "sensitivity": "private",
            "label": "",
            "reason": "source path is outside Yerhed roots or could not be resolved",
        }

    text = _read_text(resolved, max_chars=4000)
    label = _extract_sensitivity_label(text)
    reason = "explicit sensitivity label" if label else "default sensitivity"
    default = "private"
    if _is_under(resolved, brain_root()):
        rel = resolved.relative_to(brain_root())
        top = rel.parts[0] if rel.parts else ""
        default = "sensitive" if top in SENSITIVE_SOURCE_DIRS else "private"
        if label is None:
            reason = f"brain-root {top or 'file'} default"
    elif _is_under(resolved, yerhed_repo()):
        reason = "Yerhed repo file default" if label is None else reason

    sensitivity = label or default
    return {
        "path": path_text,
        "resolved_path": str(resolved),
        "exists": resolved.exists(),
        "sensitivity": sensitivity,
        "label": label or "",
        "reason": reason,
    }


def _redact_local_paths(text: str) -> str:
    redacted = text or ""
    roots = [str(brain_root()), str(yerhed_repo()), str(Path.home())]
    for root in sorted({item for item in roots if item}, key=len, reverse=True):
        redacted = redacted.replace(root, "[redacted local/private path]")
    macos_user_prefix = "/" + "Users/"
    redacted = re.sub(re.escape(macos_user_prefix) + r"[^\s),;\]]+", "[redacted local/private path]", redacted)
    return redacted


def _has_path_owner_override(user_intent: str) -> bool:
    lowered = (user_intent or "").lower()
    hints = {
        "include local path",
        "include local paths",
        "include private path",
        "include private paths",
        "share local path",
        "share local paths",
        "share private path",
        "share private paths",
        "show the path externally",
        "send the path externally",
    }
    return any(hint in lowered for hint in hints)


def _utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.UTC)


def _utc_iso() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


def _source_kind_for_path(path: Path) -> str:
    safe_path = _safe_existing_file(path)
    if safe_path is None:
        return "unknown"
    if _is_under(safe_path, brain_root()):
        return "brain"
    if _is_under(safe_path, yerhed_repo()):
        return "yerhed_repo"
    return "unknown"


def _span_text_for_hash(path: Path, line_start: int, line_end: int) -> str:
    text = _read_text(path)
    if not text:
        return ""
    lines = text.splitlines()
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        return ""
    return "\n".join(lines[line_start - 1 : line_end])


def _hash_span_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _effective_evidence_ttl(max_age_seconds: int | None = DEFAULT_EVIDENCE_TTL_SECONDS) -> int:
    try:
        requested = int(max_age_seconds or DEFAULT_EVIDENCE_TTL_SECONDS)
    except (TypeError, ValueError):
        requested = DEFAULT_EVIDENCE_TTL_SECONDS
    return max(0, min(requested, DEFAULT_EVIDENCE_TTL_SECONDS))


def _prune_evidence_registry(max_age_seconds: int = DEFAULT_EVIDENCE_TTL_SECONDS) -> None:
    now = time.time()
    cutoff = DEFAULT_EVIDENCE_TTL_SECONDS
    stale = [eid for eid, span in _EVIDENCE_REGISTRY.items() if now - float(span.get("_registered_at_epoch", 0)) > cutoff]
    for eid in stale:
        _EVIDENCE_REGISTRY.pop(eid, None)


def _make_evidence_span(
    path: Path | str,
    line_start: int,
    line_end: int,
    note: str,
    evidence_status: str = "verified_current_turn",
    source_kind: str = "",
) -> dict[str, Any]:
    status = evidence_status if evidence_status in EVIDENCE_STATUSES else "assistant_inferred"
    resolved = Path(path).expanduser().resolve() if str(path or "") else Path("")
    sensitivity = _source_sensitivity(str(resolved)).get("sensitivity", "private") if str(path or "") else "private"
    span_text = _span_text_for_hash(resolved, int(line_start or 0), int(line_end or 0)) if str(path or "") else ""
    content_hash = _hash_span_text(span_text) if span_text else ""
    evidence_id = uuid.uuid4().hex
    span = {
        "evidence_id": evidence_id,
        "path": str(resolved) if str(path or "") else "",
        "line_start": int(line_start or 0),
        "line_end": int(line_end or 0),
        "note": note,
        "sensitivity": sensitivity,
        "source_kind": source_kind or (_source_kind_for_path(resolved) if str(path or "") else "assistant"),
        "loaded_at": _utc_iso(),
        "evidence_status": status,
        "content_hash": content_hash,
    }
    if status == "verified_current_turn" and content_hash:
        registry_row = dict(span)
        registry_row["_registered_at_epoch"] = time.time()
        _EVIDENCE_REGISTRY[evidence_id] = registry_row
        _prune_evidence_registry()
    return span


def _normalize_evidence_spans(evidence_spans: Any) -> list[dict[str, Any]]:
    if evidence_spans is None:
        return []
    if isinstance(evidence_spans, dict):
        if "evidence_spans" in evidence_spans:
            return _normalize_evidence_spans(evidence_spans.get("evidence_spans"))
        return [dict(evidence_spans)]
    if isinstance(evidence_spans, str):
        try:
            parsed = json.loads(evidence_spans)
        except json.JSONDecodeError:
            return []
        return _normalize_evidence_spans(parsed)
    if isinstance(evidence_spans, (list, tuple, set)):
        rows: list[dict[str, Any]] = []
        for item in evidence_spans:
            if isinstance(item, dict):
                rows.append(dict(item))
        return rows
    return []


def _validated_evidence_for_egress(evidence_spans: Any) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    paths: list[str] = []
    normalized_spans: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for span in _normalize_evidence_spans(evidence_spans):
        status = str(span.get("evidence_status", ""))
        if status == "assistant_inferred":
            normalized_spans.append(dict(span))
            continue
        if status == "verified_current_turn":
            ok, reason, normalized = _validate_citable_span(span, DEFAULT_EVIDENCE_TTL_SECONDS)
            if ok:
                path = str(normalized.get("path", ""))
                if path:
                    paths.append(path)
                normalized_spans.append(normalized)
                continue
            redacted = dict(span)
            redacted.update({
                "evidence_status": "memory_derived_stale",
                "sensitivity": "private",
                "note": f"unverified evidence span: {reason}",
            })
            normalized_spans.append(redacted)
            invalid.append({
                "path": span.get("path", ""),
                "evidence_status": status,
                "reason": reason,
            })
            continue
        if str(span.get("path", "")).strip():
            invalid.append({
                "path": span.get("path", ""),
                "evidence_status": status or "missing",
                "reason": "evidence is not verified_current_turn",
            })
        normalized_spans.append(dict(span))
    return paths, normalized_spans, invalid


def _evidence_source_paths(evidence_spans: Any) -> list[str]:
    paths, _, _ = _validated_evidence_for_egress(evidence_spans)
    return paths


def _validate_citable_span(span: dict[str, Any], max_age_seconds: int) -> tuple[bool, str, dict[str, Any]]:
    if span.get("evidence_status") != "verified_current_turn":
        return False, f"status is {span.get('evidence_status') or 'missing'}", span
    evidence_id = str(span.get("evidence_id", ""))
    registered = _EVIDENCE_REGISTRY.get(evidence_id)
    if not registered:
        return False, "evidence id is not in the current MCP registry", span
    if time.time() - float(registered.get("_registered_at_epoch", 0)) > _effective_evidence_ttl(max_age_seconds):
        return False, "evidence span is stale for citation UI", registered
    path = _safe_existing_file(str(span.get("path", "")))
    if path is None:
        return False, "path is malformed, unsafe, or outside allowed Yerhed roots", span
    if str(path) != str(registered.get("path", "")):
        return False, "path does not match registered evidence", span
    if not path.exists() or not path.is_file():
        return False, "file no longer exists", span
    try:
        line_start = int(span.get("line_start", 0))
        line_end = int(span.get("line_end", 0))
    except (TypeError, ValueError):
        return False, "line range is malformed", span
    if line_start < 1 or line_end < line_start:
        return False, "line range is malformed", span
    current_text = _span_text_for_hash(path, line_start, line_end)
    if not current_text:
        return False, "line range does not exist in the current file", span
    current_hash = _hash_span_text(current_text)
    if current_hash != registered.get("content_hash") or current_hash != span.get("content_hash"):
        return False, "content hash no longer matches current file", span
    normalized = dict(registered)
    normalized.update({"path": str(path), "line_start": line_start, "line_end": line_end})
    return True, "verified current-turn span", normalized


def _citation_note(note: str) -> str:
    clean = re.sub(r"[\r\n]+", " ", note or "Yerhed memory").strip()
    clean = clean.replace("[", "(").replace("]", ")")
    return clean[:180] or "Yerhed memory"


def format_memory_citations(evidence_spans: Any, max_age_seconds: int = DEFAULT_EVIDENCE_TTL_SECONDS) -> dict[str, Any]:
    """Return Codex-compatible citation UI only for server-verified current evidence spans."""
    spans = _normalize_evidence_spans(evidence_spans)
    entries: list[str] = []
    omitted: list[dict[str, Any]] = []
    for span in spans:
        ok, reason, normalized = _validate_citable_span(span, max_age_seconds)
        if not ok:
            omitted.append({
                "path": span.get("path", ""),
                "line_start": span.get("line_start", 0),
                "line_end": span.get("line_end", 0),
                "evidence_status": span.get("evidence_status", ""),
                "reason": reason,
            })
            continue
        entries.append(
            f"{normalized['path']}:{normalized['line_start']}-{normalized['line_end']}|note=[{_citation_note(str(normalized.get('note', '')))}]"
        )
    citation_ui = ""
    if entries:
        citation_ui = "<oai-mem-citation>\n<citation_entries>\n" + "\n".join(entries) + "\n</citation_entries>\n<rollout_ids>\n</rollout_ids>\n</oai-mem-citation>"
    summary = summarize_evidence(spans).get("summary", "")
    return {
        "ok": True,
        "citation_ui": citation_ui,
        "citations": entries,
        "omitted": omitted,
        "summary": summary,
        "never_fabricates": True,
    }


def summarize_evidence(evidence_spans: Any) -> dict[str, Any]:
    """Summarize whether evidence is current, stale, inferred, or redacted."""
    spans = _normalize_evidence_spans(evidence_spans)
    counts = {status: 0 for status in sorted(EVIDENCE_STATUSES)}
    unknown = 0
    sensitivities: dict[str, int] = {}
    for span in spans:
        status = str(span.get("evidence_status", ""))
        if status in counts:
            counts[status] += 1
        else:
            unknown += 1
        sensitivity = str(span.get("sensitivity", "") or "unknown")
        sensitivities[sensitivity] = sensitivities.get(sensitivity, 0) + 1
    phrases: list[str] = []
    if counts["verified_current_turn"]:
        phrases.append("from current Yerhed memory")
    if counts["memory_derived_stale"]:
        phrases.append("from memory, not freshly verified")
    if counts["assistant_inferred"]:
        phrases.append("assistant inference without a direct source span")
    if counts["external_redacted"]:
        phrases.append("source redacted for external safety")
    if unknown:
        phrases.append("unrecognized evidence status")
    if not phrases:
        phrases.append("no Yerhed evidence spans supplied")
    return {
        "ok": True,
        "summary": "; ".join(phrases),
        "counts": counts,
        "unknown_status_count": unknown,
        "sensitivity_summary": sensitivities,
    }


def _max_sensitivity(items: list[dict[str, Any]]) -> str:
    if not items:
        return "none"
    return max((item.get("sensitivity", "private") for item in items), key=lambda item: SENSITIVITY_LEVELS.get(item, 1))


def _destination_kind(destination: str) -> str:
    lowered = (destination or "").strip().lower()
    if not lowered:
        return "unknown"
    if any(hint in lowered for hint in EXTERNAL_DESTINATION_HINTS):
        return "external"
    if any(hint in lowered for hint in INTERNAL_DESTINATION_HINTS):
        return "internal"
    return "external"


def _has_secret_like_text(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in SECRET_PATTERNS)


def _has_owner_override(user_intent: str) -> bool:
    lowered = (user_intent or "").lower()
    return any(hint in lowered for hint in OWNER_OVERRIDE_HINTS)


def _redact_draft(draft: str) -> str:
    redacted_lines: list[str] = []
    for line in (draft or "").splitlines():
        lowered = line.lower()
        if _has_secret_like_text(line):
            redacted_lines.append("[redacted secret-like material]")
            continue
        if "sensitivity:" in lowered or "do-not-share" in lowered or "do_not_share" in lowered:
            redacted_lines.append("[redacted private memory marker]")
            continue
        if str(brain_root()).lower() in lowered or str(Path.home()).lower() in lowered:
            redacted_lines.append("[redacted local/private path]")
            continue
        if any(hint in lowered for hint in SENSITIVE_HINTS):
            redacted_lines.append("[redacted private detail]")
            continue
        redacted_lines.append(line)
    suggested = "\n".join(redacted_lines).strip()
    if suggested == (draft or "").strip():
        suggested = "I have private context that may be relevant, but I should not include the underlying details without explicit approval.\n\n" + suggested
    return suggested


def egress_check(
    destination: str,
    draft: str,
    source_paths: Any = None,
    user_intent: str = "",
) -> dict[str, Any]:
    """Classify whether memory-derived content is safe to include in an external output."""
    destination_kind = _destination_kind(destination)
    sources = [_source_sensitivity(path) for path in _normalize_sequence(source_paths)]
    max_sensitivity = _max_sensitivity(sources)
    source_sensitivity_summary = {
        "max": max_sensitivity,
        "sources": sources,
    }
    reasons: list[str] = []
    triggers: list[str] = []
    owner_override = _has_owner_override(user_intent)

    if _has_secret_like_text(draft):
        return {
            "ok": True,
            "disposition": "block",
            "destination_kind": destination_kind,
            "reasons": ["draft contains secret-like material"],
            "triggers": ["secret-like-content"],
            "source_sensitivity_summary": source_sensitivity_summary,
            "suggested_draft": _redact_draft(draft),
            "requires_user_approval": True,
            "owner_override_available": False,
        }

    if max_sensitivity == "do_not_share":
        return {
            "ok": True,
            "disposition": "block",
            "destination_kind": destination_kind,
            "reasons": ["one or more source files are labeled do-not-share"],
            "triggers": ["do-not-share-source"],
            "source_sensitivity_summary": source_sensitivity_summary,
            "suggested_draft": _redact_draft(draft),
            "requires_user_approval": True,
            "owner_override_available": False,
        }

    if destination_kind == "internal":
        return {
            "ok": True,
            "disposition": "allow",
            "destination_kind": destination_kind,
            "reasons": ["destination is internal Codex/Yerhed context"],
            "triggers": [],
            "source_sensitivity_summary": source_sensitivity_summary,
            "suggested_draft": draft,
            "requires_user_approval": False,
            "owner_override_available": False,
        }

    if destination_kind == "unknown":
        return {
            "ok": True,
            "disposition": "ask",
            "destination_kind": destination_kind,
            "reasons": ["destination is missing or ambiguous"],
            "triggers": ["unknown-destination"],
            "source_sensitivity_summary": source_sensitivity_summary,
            "suggested_draft": _redact_draft(draft) if _looks_sensitive(draft) else draft,
            "requires_user_approval": True,
            "owner_override_available": False,
        }

    if not sources:
        if _looks_sensitive(draft):
            return {
                "ok": True,
                "disposition": "ask",
                "destination_kind": destination_kind,
                "reasons": ["external draft appears sensitive but no source paths were supplied"],
                "triggers": ["sensitive-draft-no-sources"],
                "source_sensitivity_summary": source_sensitivity_summary,
                "suggested_draft": _redact_draft(draft),
                "requires_user_approval": True,
                "owner_override_available": True,
            }
        return {
            "ok": True,
            "disposition": "allow",
            "destination_kind": destination_kind,
            "reasons": ["no Yerhed source paths supplied"],
            "triggers": [],
            "source_sensitivity_summary": source_sensitivity_summary,
            "suggested_draft": draft,
            "requires_user_approval": False,
            "owner_override_available": False,
        }

    if any(not item.get("exists") for item in sources):
        reasons.append("one or more source paths are unresolved or outside allowed roots")
        triggers.append("unknown-source")

    if max_sensitivity == "public" and not reasons:
        return {
            "ok": True,
            "disposition": "allow",
            "destination_kind": destination_kind,
            "reasons": ["all supplied Yerhed sources are public"],
            "triggers": [],
            "source_sensitivity_summary": source_sensitivity_summary,
            "suggested_draft": draft,
            "requires_user_approval": False,
            "owner_override_available": False,
        }

    if max_sensitivity == "sensitive" or _looks_sensitive(draft):
        reasons.append("external draft uses sensitive or sensitive-looking Yerhed context")
        triggers.append("sensitive-memory-egress")
        return {
            "ok": True,
            "disposition": "redact",
            "destination_kind": destination_kind,
            "reasons": reasons,
            "triggers": triggers,
            "source_sensitivity_summary": source_sensitivity_summary,
            "suggested_draft": _redact_draft(draft),
            "requires_user_approval": True,
            "owner_override_available": True,
        }

    if max_sensitivity == "private" or reasons:
        if owner_override and not reasons:
            return {
                "ok": True,
                "disposition": "allow",
                "destination_kind": destination_kind,
                "reasons": ["owner intent explicitly allows this private detail"],
                "triggers": ["owner-override"],
                "source_sensitivity_summary": source_sensitivity_summary,
                "suggested_draft": draft,
                "requires_user_approval": False,
                "owner_override_available": True,
            }
        reasons.append("external draft uses private Yerhed memory")
        triggers.append("private-memory-egress")
        return {
            "ok": True,
            "disposition": "ask",
            "destination_kind": destination_kind,
            "reasons": reasons,
            "triggers": triggers,
            "source_sensitivity_summary": source_sensitivity_summary,
            "suggested_draft": draft,
            "requires_user_approval": True,
            "owner_override_available": True,
        }

    return {
        "ok": True,
        "disposition": "allow",
        "destination_kind": destination_kind,
        "reasons": ["no egress risk detected"],
        "triggers": [],
        "source_sensitivity_summary": source_sensitivity_summary,
        "suggested_draft": draft,
        "requires_user_approval": False,
        "owner_override_available": False,
    }


def prepare_external_output(
    destination: str,
    draft: str,
    source_paths: Any = None,
    user_intent: str = "",
    evidence_spans: Any = None,
) -> dict[str, Any]:
    """Prepare a memory-derived draft for an external connector without sending it."""
    normalized_source_paths = _normalize_sequence(source_paths)
    evidence_paths, normalized_evidence_spans, invalid_evidence = _validated_evidence_for_egress(evidence_spans)
    combined_source_paths = normalized_source_paths + [path for path in evidence_paths if path not in normalized_source_paths]
    if invalid_evidence:
        combined_source_paths.append("__yerhed_unvalidated_evidence__")
    check = egress_check(
        destination=destination,
        draft=draft,
        source_paths=combined_source_paths,
        user_intent=user_intent,
    )
    disposition = check.get("disposition")
    suggested = check.get("suggested_draft", draft)
    evidence_summary = summarize_evidence(normalized_evidence_spans)
    destination_kind = check.get("destination_kind") or _destination_kind(destination)
    redact_paths = destination_kind != "internal" and not _has_path_owner_override(user_intent)

    if disposition == "allow":
        connector_action = "proceed_with_connector_review"
        draft_for_connector = draft
        may_use_connector = True
        approval_question = ""
    elif disposition == "ask":
        connector_action = "ask_owner_before_connector_use"
        draft_for_connector = ""
        may_use_connector = False
        if "unknown-destination" in check.get("triggers", []):
            approval_question = "The destination is missing or ambiguous. Tell me the target surface before using Yerhed-derived content externally."
        else:
            approval_question = "This draft uses private Yerhed memory. Do you want me to include those private details in the external output?"
    elif disposition == "redact":
        connector_action = "use_sanitized_draft_after_owner_review"
        draft_for_connector = suggested
        may_use_connector = False
        approval_question = "I made a safer draft by removing private details. Do you want me to use this sanitized version externally?"
    else:
        connector_action = "do_not_use_connector"
        draft_for_connector = ""
        may_use_connector = False
        approval_question = ""

    if redact_paths and draft_for_connector:
        draft_for_connector = _redact_local_paths(draft_for_connector)

    return {
        "ok": True,
        "destination": destination,
        "connector_action": connector_action,
        "may_use_connector": may_use_connector,
        "draft_for_connector": draft_for_connector,
        "approval_question": approval_question,
        "egress_check": check,
        "evidence_summary": evidence_summary,
        "evidence_paths_used_for_egress": evidence_paths,
        "invalid_evidence_spans": invalid_evidence,
        "local_paths_redacted_by_default": redact_paths,
        "never_sends_or_posts": True,
    }

def _extract_patch_paths(patch: str) -> list[str]:
    paths: set[str] = set()
    for line in patch.splitlines():
        candidate = None
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                candidate = parts[3]
        elif line.startswith("+++ ") or line.startswith("--- "):
            candidate = line[4:].split("\t", 1)[0].split(" ", 1)[0]
        if not candidate or candidate == "/dev/null":
            continue
        if candidate.startswith("a/") or candidate.startswith("b/"):
            candidate = candidate[2:]
        if candidate.startswith("/") or ".." in Path(candidate).parts:
            raise ValueError(f"patch path is outside allowed roots: {candidate}")
        paths.add(candidate)
    return sorted(paths)


def _infer_patch_root(paths: list[str]) -> Path:
    if not paths:
        raise ValueError("patch contains no file paths")
    brain_ok = all(path.split("/", 1)[0] in BRAIN_TOP_LEVEL for path in paths)
    repo_ok = all(path.split("/", 1)[0] in YERHED_TOP_LEVEL for path in paths)
    if brain_ok and not repo_ok:
        return brain_root()
    if repo_ok and not brain_ok:
        return yerhed_repo()
    if brain_ok and repo_ok:
        raise ValueError("patch root is ambiguous; split brain and repo changes into separate patches")
    raise ValueError(f"patch contains unsupported top-level paths: {paths}")


def _run(cmd: list[str], cwd: Path, input_text: str | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), input=input_text, text=True, capture_output=True, env=env)


def _git_commit_hash(root: Path) -> str:
    proc = _run(["git", "rev-parse", "--short", "HEAD"], root)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _cheap_validation(root: Path, paths: list[str]) -> tuple[bool, list[str]]:
    messages = []
    diff_check = _run(["git", "diff", "--check", "--", *paths], root)
    if diff_check.returncode != 0:
        return False, [diff_check.stdout, diff_check.stderr]
    messages.append("git diff --check passed")
    script = yerhed_repo() / "scripts" / "check_structure.sh"
    if script.exists() and os.access(script, os.X_OK):
        env = os.environ.copy()
        env["YERHED_REPO"] = str(yerhed_repo())
        env["BRAIN_ROOT"] = str(brain_root())
        env["YERHED_BRAIN_ROOT"] = str(brain_root())
        proc = _run([str(script)], yerhed_repo(), env=env)
        if proc.returncode != 0:
            return False, [proc.stdout, proc.stderr]
        messages.append("scripts/check_structure.sh passed")
    return True, messages


def _validate_policy_inputs(policy_basis: str, source_summary: str, commit_message: str) -> str | None:
    basis_lower = (policy_basis or "").lower()
    if not policy_basis or not any(term in basis_lower for term in ("update-policy", "explicit", "expected", "non-sensitive", "project", "durable")):
        return "policy_basis is missing or does not cite an allowed update-policy basis"
    if not source_summary or not source_summary.strip():
        return "source_summary is required"
    if not commit_message or not commit_message.strip():
        return "commit_message is required"
    return None


def _ensure_git_worktree(root: Path) -> str | None:
    git_check = _run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if git_check.returncode != 0:
        return f"{root} is not a git worktree"
    return None


def _ensure_paths_clean(root: Path, paths: list[str]) -> str | None:
    status = _run(["git", "status", "--porcelain", "--", *paths], root)
    if status.returncode != 0:
        return status.stderr or "git status failed"
    if status.stdout.strip():
        return "target file already has uncommitted changes; refusing to bundle unrelated memory edits"
    return None


def _ensure_write_paths_safe(root: Path, paths: list[str]) -> str | None:
    root = root.resolve()
    for rel_text in paths:
        rel = Path(rel_text)
        if rel.is_absolute() or ".." in rel.parts:
            return f"target path is outside allowed root: {rel_text}"
        current = root
        for part in rel.parts:
            current = current / part
            if current.is_symlink():
                return f"target path uses a symlink; refusing to write through {current}"
        target = root / rel
        parent = target.parent
        if parent.exists() and not _is_under(parent.resolve(), root):
            return f"target parent resolves outside allowed root: {rel_text}"
        if target.exists():
            if target.is_symlink():
                return f"target path uses a symlink; refusing to write through {target}"
            if not _is_under(target.resolve(), root):
                return f"target path resolves outside allowed root: {rel_text}"
    return None


def _patch_contains_symlink_mode(patch: str) -> bool:
    for line in patch.splitlines():
        if re.match(r"^(?:new file mode|old mode|deleted file mode|mode) 120000\b", line):
            return True
        if re.match(r"^index [0-9a-f]+\.\.[0-9a-f]+ 120000\b", line):
            return True
    return False


def _commit_structured_change(root: Path, paths: list[str], commit_message: str, source_summary: str) -> dict[str, Any]:
    valid, validation_messages = _cheap_validation(root, paths)
    if not valid:
        return {
            "ok": False,
            "error": "validation failed after structured write; changes left uncommitted for review",
            "validation": validation_messages,
            "root": str(root),
            "changed_files": paths,
        }
    add = _run(["git", "add", "--", *paths], root)
    if add.returncode != 0:
        return {"ok": False, "error": "git add failed", "stdout": add.stdout, "stderr": add.stderr, "root": str(root)}
    commit = _run(["git", "commit", "-m", commit_message.strip()], root)
    if commit.returncode != 0:
        return {"ok": False, "error": "git commit failed", "stdout": commit.stdout, "stderr": commit.stderr, "root": str(root)}
    return {
        "ok": True,
        "root": str(root),
        "changed_files": paths,
        "commit": _git_commit_hash(root),
        "validation": validation_messages,
        "pushed": False,
        "source_summary": source_summary,
    }


def _append_section(path: Path, title: str, body: str) -> None:
    clean_title = re.sub(r"[\r\n]+", " ", title).strip()
    clean_body = body.strip()
    old = _read_text(path)
    prefix = old.rstrip() + "\n\n" if old.strip() else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{prefix}## {clean_title}\n\n{clean_body}\n", encoding="utf-8")


def append_log_entry(
    title: str,
    body: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
) -> dict[str, Any]:
    """Append a section to brain/log.md and commit it locally without hand-written patch hunks."""
    if not title or not title.strip():
        return {"ok": False, "error": "title is required"}
    if not body or not body.strip():
        return {"ok": False, "error": "body is required"}
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    root = brain_root()
    rel = "log.md"
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [rel]}
    _append_section(root / rel, title, body)
    return _commit_structured_change(root, [rel], commit_message, source_summary)


def _project_path(project: str) -> Path:
    return brain_root() / "projects" / f"{_slug(project)}.md"


def append_project_update(
    project: str,
    heading: str,
    body: str,
    policy_basis: str,
    source_summary: str,
    commit_message: str,
) -> dict[str, Any]:
    """Append a project-page section and commit it locally without hand-written patch hunks."""
    if not project or not project.strip():
        return {"ok": False, "error": "project is required"}
    if not heading or not heading.strip():
        return {"ok": False, "error": "heading is required"}
    if not body or not body.strip():
        return {"ok": False, "error": "body is required"}
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    root = brain_root()
    path = _project_path(project)
    rel = str(path.relative_to(root))
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [rel]}
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {project.strip()}\n\n", encoding="utf-8")
    _append_section(path, heading, body)
    return _commit_structured_change(root, [rel], commit_message, source_summary)


def _find_h2_section(lines: list[str], heading: str) -> tuple[int, int]:
    wanted = f"## {heading}".lower()
    start = -1
    for idx, line in enumerate(lines):
        if line.strip().lower() == wanted:
            start = idx
            break
    if start == -1:
        return -1, -1
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return start, end


def _find_open_loop_section(lines: list[str], central_page: bool = False, section: str = "") -> tuple[int, int]:
    if section:
        return _find_h2_section(lines, section)
    if central_page:
        start, end = _find_h2_section(lines, "Yerhed V1")
        if start != -1:
            return start, end
    return _find_h2_section(lines, "Open Loops")


def _merge_central_open_loop_sections(lines: list[str]) -> list[str]:
    yerhed_start, _ = _find_h2_section(lines, "Yerhed V1")
    open_start, open_end = _find_h2_section(lines, "Open Loops")
    if yerhed_start == -1 or open_start == -1:
        return lines

    open_body = [line for line in lines[open_start + 1 : open_end] if line.strip()]
    lines_without_open = lines[:open_start] + lines[open_end:]
    if not open_body:
        return lines_without_open

    yerhed_start, yerhed_end = _find_h2_section(lines_without_open, "Yerhed V1")
    existing = {line.strip() for line in lines_without_open[yerhed_start + 1 : yerhed_end]}
    to_move = [line for line in open_body if line.strip() not in existing]
    if not to_move:
        return lines_without_open

    insert_at = yerhed_end
    while insert_at > yerhed_start + 1 and not lines_without_open[insert_at - 1].strip():
        insert_at -= 1
    return lines_without_open[:insert_at] + to_move + lines_without_open[insert_at:]


def _rewrite_open_loop(
    text: str,
    action: str,
    item: str,
    replacement_text: str = "",
    central_page: bool = False,
    section: str = "",
) -> tuple[str, str | None]:
    normalized_action = action.strip().lower()
    if normalized_action not in {"add", "remove", "replace"}:
        return text, "action must be one of add, remove, or replace"
    item = item.strip()
    replacement_text = replacement_text.strip()
    if not item:
        return text, "text is required"
    if normalized_action == "replace" and not replacement_text:
        return text, "replacement_text is required for replace"

    lines = text.splitlines()
    if central_page:
        lines = _merge_central_open_loop_sections(lines)
    section_name = section.strip() or ("Yerhed V1" if central_page else "Open Loops")
    start, end = _find_open_loop_section(lines, central_page=central_page, section=section_name)
    if start == -1:
        if normalized_action != "add":
            return text, f"target has no {section_name} section"
        base = "\n".join(lines).rstrip()
        prefix = base + "\n\n" if base else ""
        return f"{prefix}## {section_name}\n\n- {item}\n", None

    target = f"- {item}"
    replacement = f"- {replacement_text}"
    body_start = start + 1
    match_idx = -1
    for idx in range(body_start, end):
        if lines[idx].strip() == target:
            match_idx = idx
            break

    if normalized_action == "add":
        if match_idx != -1:
            return text, "open loop already exists"
        insert_at = end
        while insert_at > body_start and not lines[insert_at - 1].strip():
            insert_at -= 1
        lines.insert(insert_at, target)
        return "\n".join(lines).rstrip() + "\n", None
    if match_idx == -1:
        return text, "open loop text not found"
    if normalized_action == "remove":
        del lines[match_idx]
    else:
        lines[match_idx] = replacement
    return "\n".join(lines).rstrip() + "\n", None


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
    """Add, remove, or replace an Open Loops bullet and commit it locally."""
    if not project or not project.strip():
        return {"ok": False, "error": "project is required; use 'open-loops' for the central open-loop page"}
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    root = brain_root()
    central_keys = {"open-loops", "global", "yerhed-v1", "yerhed-v1-open-loops"}
    central_page = _slug(project) in central_keys or bool(section.strip())
    target = root / "projects" / "open-loops.md" if central_page else _project_path(project)
    rel = str(target.relative_to(root))
    error = _ensure_git_worktree(root) or _ensure_write_paths_safe(root, [rel]) or _ensure_paths_clean(root, [rel])
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": [rel]}
    if not target.exists():
        if action.strip().lower() != "add":
            return {"ok": False, "error": "target project file does not exist", "path": str(target)}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {project.strip()}\n\n", encoding="utf-8")
    new_text, rewrite_error = _rewrite_open_loop(_read_text(target), action, text, replacement_text, central_page=central_page, section=section.strip())
    if rewrite_error:
        return {"ok": False, "error": rewrite_error, "path": str(target)}
    target.write_text(new_text, encoding="utf-8")
    return _commit_structured_change(root, [rel], commit_message, source_summary)


def write_memory_patch(
    disposition: str,
    policy_basis: str,
    source_summary: str,
    patch: str,
    commit_message: str,
) -> dict[str, Any]:
    """Apply an exact policy-backed Yerhed/brain patch and commit it locally."""
    if disposition != "updated":
        return {"ok": False, "error": "disposition must be exactly 'updated'"}
    error = _validate_policy_inputs(policy_basis, source_summary, commit_message)
    if error:
        return {"ok": False, "error": error}
    if not patch or not patch.strip():
        return {"ok": False, "error": "patch is required"}
    if _patch_contains_symlink_mode(patch):
        return {"ok": False, "error": "patch creates or modifies a symlink; refusing to apply mode 120000 entries"}
    try:
        paths = _extract_patch_paths(patch)
        root = _infer_patch_root(paths)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    git_check = _run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if git_check.returncode != 0:
        return {"ok": False, "error": f"{root} is not a git worktree"}
    error = _ensure_write_paths_safe(root, paths) or _ensure_paths_clean(root, paths)
    if error:
        return {"ok": False, "error": error, "root": str(root), "changed_files": paths}
    check = _run(["git", "apply", "--check", "-"], root, input_text=patch)
    if check.returncode != 0:
        return {
            "ok": False,
            "error": "git apply --check failed; for simple substitutions prefer replace_text(...)",
            "stdout": check.stdout,
            "stderr": check.stderr,
            "diagnostics": {"paths": paths, "hint": "Use replace_text for exact old/new edits or regenerate the patch with full context."},
        }
    apply = _run(["git", "apply", "-"], root, input_text=patch)
    if apply.returncode != 0:
        return {"ok": False, "error": "git apply failed", "stdout": apply.stdout, "stderr": apply.stderr}
    post_apply_error = _ensure_write_paths_safe(root, paths)
    if post_apply_error:
        return {
            "ok": False,
            "error": post_apply_error,
            "root": str(root),
            "changed_files": paths,
        }
    valid, validation_messages = _cheap_validation(root, paths)
    if not valid:
        return {
            "ok": False,
            "error": "validation failed after patch apply; changes left uncommitted for review",
            "validation": validation_messages,
            "root": str(root),
            "changed_files": paths,
        }
    add = _run(["git", "add", "--", *paths], root)
    if add.returncode != 0:
        return {"ok": False, "error": "git add failed", "stdout": add.stdout, "stderr": add.stderr, "root": str(root)}
    commit = _run(["git", "commit", "-m", commit_message.strip()], root)
    if commit.returncode != 0:
        return {"ok": False, "error": "git commit failed", "stdout": commit.stdout, "stderr": commit.stderr, "root": str(root)}
    return {
        "ok": True,
        "root": str(root),
        "changed_files": paths,
        "commit": _git_commit_hash(root),
        "validation": validation_messages,
        "pushed": False,
        "source_summary": source_summary,
    }
