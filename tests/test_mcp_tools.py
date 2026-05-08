from __future__ import annotations

import difflib
import importlib.util
import inspect
import os
import subprocess
import sys
import types
import tempfile
import unittest
from pathlib import Path

from yerhed_mcp import tools


class YerhedToolTests(unittest.TestCase):
    def setUp(self) -> None:
        tools._EVIDENCE_REGISTRY.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo"
        self.brain = self.base / "brain"
        self.repo.mkdir()
        self.brain.mkdir()
        for path in [
            self.repo / "AGENTS.md",
            self.repo / "MEMORY.md",
            self.repo / "config" / "paths.md",
            self.repo / "config" / "update-policy.md",
            self.repo / "scripts" / "check_structure.sh",
        ]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.name}\nYerhed test content.\n", encoding="utf-8")
        (self.repo / "USER.md").write_text(
            "# USER.md\n\n"
            "## Active Anchors\n\n"
            "- Grounded work: prefer actual repo/tool state over guesses.\n",
            encoding="utf-8",
        )
        (self.repo / "scripts" / "check_structure.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (self.repo / "scripts" / "check_structure.sh").chmod(0o755)
        for dirname in ["people", "projects", "concepts", "ideas", "places", "organizations", "companions", "sources", "inbox", "archive"]:
            (self.brain / dirname).mkdir(parents=True, exist_ok=True)
        (self.brain / "projects" / "open-loops.md").write_text(
            "# Open Loops\n\n"
            "## From Legacy Seed\n\n"
            "- Legacy loop.\n\n"
            "## Yerhed V1\n\n"
            "- Finish Yerhed MCP.\n\n"
            "## Open Loops\n\n"
            "- Migrate prior memory and system-prompt material into Yerhed.\n",
            encoding="utf-8",
        )
        (self.brain / "projects" / "yerhed.md").write_text("# Yerhed\n\nMCP project page.\n", encoding="utf-8")
        (self.brain / "projects" / "README.md").write_text("# README\n\nREADME pages are scaffolding, not entities.\n", encoding="utf-8")
        (self.brain / "concepts" / "_template.md").write_text("# Template\n\nTemplate pages are scaffolding, not entities.\n", encoding="utf-8")
        (self.brain / "sources" / "index.md").write_text("# Source Index\n\nIndex pages are scaffolding, not entities.\n", encoding="utf-8")
        (self.brain / "projects" / "example-project.md").write_text("# Example Project\n\nCompact docs-first project. See Example Concept. ChatGPT should be review-only evidence.\n", encoding="utf-8")
        (self.brain / "RESOLVER.md").write_text(
            "# Brain Resolver\n\n"
            "## Salience Map\n\n"
            "### Example Concept\n\n"
            "- type: concept\n"
            "- path: concepts/example-concept.md\n"
            "- aliases: Example Framework\n"
            "- auto_link_aliases: Example Framework\n"
            "- triggers: durable linking, graph maintenance\n"
            "- salience: high\n"
            "- load_policy: triggered\n"
            "- baseline_handle: A test concept used to validate resolver salience.\n\n"
            "### Example Place\n\n"
            "- type: place\n"
            "- path: places/example-place.md\n"
            "- aliases: Test Place\n"
            "- triggers: location context\n"
            "- salience: medium\n"
            "- load_policy: triggered\n"
            "- baseline_handle: A test place used to validate place scope.\n\n"
            "### LLM Workflow\n\n"
            "- type: concept\n"
            "- path: concepts/llm-workflow.md\n"
            "- aliases: ChatGPT\n"
            "- review_only_aliases: ChatGPT\n"
            "- triggers: broad model workflow\n"
            "- salience: medium\n"
            "- load_policy: triggered\n"
            "- baseline_handle: A broad workflow concept with a generic alias.\n\n"
            "### Example Project\n\n"
            "- type: project\n"
            "- path: projects/example-project.md\n"
            "- aliases: Starter Project\n"
            "- triggers: project continuity\n"
            "- salience: medium\n"
            "- load_policy: triggered\n"
            "- baseline_handle: A test project used to validate review-set graph gardening.\n",
            encoding="utf-8",
        )
        (self.brain / "concepts" / "llm-workflow.md").write_text(
            "---\n"
            "type: concept\n"
            "aliases: [\"ChatGPT\"]\n"
            "review_only_aliases: [\"ChatGPT\"]\n"
            "triggers: [\"broad model workflow\"]\n"
            "salience: medium\n"
            "load_policy: triggered\n"
            "sensitivity: private\n"
            "---\n"
            "# LLM Workflow\n\nA broad workflow concept.\n",
            encoding="utf-8",
        )
        (self.brain / "concepts" / "example-concept.md").write_text(
            "---\n"
            "type: concept\n"
            "aliases: [\"Example Framework\"]\n"
            "auto_link_aliases: [\"Example Framework\"]\n"
            "triggers: [\"durable linking\"]\n"
            "salience: high\n"
            "load_policy: triggered\n"
            "sensitivity: private\n"
            "---\n"
            "# Example Concept\n\nA durable test concept. See [[RESOLVER]].\n",
            encoding="utf-8",
        )
        (self.brain / "places" / "example-place.md").write_text("# Example Place\n\nA durable test place.\n", encoding="utf-8")
        (self.brain / "organizations" / "example-org.md").write_text("# Example Org\n\nA durable test organization.\n", encoding="utf-8")
        (self.brain / "people" / "operator.md").write_text("# Operator\n\nPrefers direct, grounded work.\n", encoding="utf-8")
        (self.brain / "people" / "example-user.md").write_text(
            "---\n"
            "type: person\n"
            "aliases: [\"Example\", \"Example User\"]\n"
            "triggers: [\"operator\"]\n"
            "salience: high\n"
            "load_policy: baseline\n"
            "sensitivity: private\n"
            "---\n"
            "# Example User\n\nOperator page.\n",
            encoding="utf-8",
        )
        (self.brain / "projects" / "public.md").write_text("---\nsensitivity: public\n---\n# Public\n\nShareable project facts.\n", encoding="utf-8")
        (self.brain / "projects" / "do-not-share.md").write_text("---\nsensitivity: do-not-share\n---\n# Private\n\nNever share this.\n", encoding="utf-8")
        (self.brain / "log.md").write_text("# Log\n\n## Recent Item\n\nYerhed MCP started.\n", encoding="utf-8")
        self.old_repo = os.environ.get("YERHED_REPO")
        self.old_brain = os.environ.get("YERHED_BRAIN_ROOT")
        self.old_disabled = os.environ.get("YERHED_DISABLED")
        os.environ["YERHED_REPO"] = str(self.repo)
        os.environ["YERHED_BRAIN_ROOT"] = str(self.brain)

    def init_brain_git(self) -> None:
        subprocess.run(["git", "init"], cwd=self.brain, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "yerhed@example.invalid"], cwd=self.brain, check=True)
        subprocess.run(["git", "config", "user.name", "Yerhed Test"], cwd=self.brain, check=True)
        subprocess.run(["git", "add", "."], cwd=self.brain, check=True)
        subprocess.run(["git", "commit", "-m", "seed"], cwd=self.brain, check=True, stdout=subprocess.DEVNULL)

    def tearDown(self) -> None:
        if self.old_repo is None:
            os.environ.pop("YERHED_REPO", None)
        else:
            os.environ["YERHED_REPO"] = self.old_repo
        if self.old_brain is None:
            os.environ.pop("YERHED_BRAIN_ROOT", None)
        else:
            os.environ["YERHED_BRAIN_ROOT"] = self.old_brain
        if self.old_disabled is None:
            os.environ.pop("YERHED_DISABLED", None)
        else:
            os.environ["YERHED_DISABLED"] = self.old_disabled
        self.tmp.cleanup()


    def load_mcp_server(self):
        server_path = Path(__file__).resolve().parents[1] / "mcp" / "server.py"
        spec = importlib.util.spec_from_file_location("yerhed_mcp_server_under_test", server_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        class FakeFastMCP:
            def __init__(self, *_args, **_kwargs):
                pass

            def tool(self, *_args, **_kwargs):
                def decorator(fn):
                    return fn

                return decorator

            def run(self) -> None:
                pass

        module_names = ["mcp", "mcp.server", "mcp.server.fastmcp"]
        sentinel = object()
        old_modules = {name: sys.modules.get(name, sentinel) for name in module_names}
        mcp_pkg = types.ModuleType("mcp")
        mcp_pkg.__path__ = []
        server_pkg = types.ModuleType("mcp.server")
        server_pkg.__path__ = []
        fastmcp_pkg = types.ModuleType("mcp.server.fastmcp")
        fastmcp_pkg.FastMCP = FakeFastMCP
        sys.modules["mcp"] = mcp_pkg
        sys.modules["mcp.server"] = server_pkg
        sys.modules["mcp.server.fastmcp"] = fastmcp_pkg
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            for name, old in old_modules.items():
                if old is sentinel:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = old

    def test_all_mcp_server_tools_refuse_when_disabled(self) -> None:
        os.environ["YERHED_DISABLED"] = "1"
        server = self.load_mcp_server()
        tool_names = [
            "bootstrap_context",
            "search",
            "salience_map",
            "resolve_entity",
            "suggest_links",
            "suggest_links_for_review_set",
            "propose_entity_page",
            "format_memory_citations",
            "summarize_evidence",
            "read_file",
            "read_project",
            "what_matters_now",
            "morning_brief",
            "closeout_check",
            "append_log_entry",
            "append_project_update",
            "update_open_loop",
            "egress_check",
            "prepare_external_output",
            "create_entity_page",
            "set_canonical_entity_name",
            "replace_text",
            "upsert_entity_page",
            "append_entity_update",
            "import_memory_plan",
            "validate_wikilinks",
            "update_resolver_entry",
            "batch_update_resolver_entries",
            "sync_resolver_to_frontmatter",
            "update_entity_links",
            "write_memory_patch",
        ]
        values = {
            "action": "add",
            "aliases": [],
            "baseline_handle": "Example",
            "body": "Body",
            "changed_files": [],
            "commit_message": "Test commit",
            "context_summary": "Example context",
            "destination": "Slack",
            "draft": "Example draft",
            "disposition": "updated",
            "entity_type": "project",
            "entries": [],
            "heading": "Update",
            "items": [],
            "load_policy": "triggered",
            "name": "Example Project",
            "new_text": "new",
            "new_name": "New Project",
            "old_text": "old",
            "patch": "",
            "path": str(self.brain / "projects" / "example-project.md"),
            "policy_basis": "explicit update-policy test",
            "project": "Example Project",
            "query": "Example",
            "repo_path": str(self.repo),
            "replacements": [("old", "new")],
            "salience": "medium",
            "sections": {},
            "sensitivity": "private",
            "source_summary": "test",
            "text": "Item",
            "title": "Title",
            "triggers": [],
            "work_summary": "work",
            "durable_state_change_summary": "durable",
        }
        for name in tool_names:
            fn = getattr(server, name)
            sig = inspect.signature(fn)
            kwargs = {}
            for param_name, param in sig.parameters.items():
                if param.default is inspect._empty:
                    self.assertIn(param_name, values, f"missing dummy value for {name}.{param_name}")
                    kwargs[param_name] = values[param_name]
            result = fn(**kwargs)
            self.assertEqual(False, result.get("ok"), name)
            self.assertEqual(True, result.get("disabled"), name)
            self.assertIn("YERHED_DISABLED=1", result.get("error", ""), name)

    def test_bootstrap_returns_baseline_and_affordances(self) -> None:
        result = tools.bootstrap_context(prompt="hello", cwd=str(self.repo))
        self.assertTrue(result["ok"])
        self.assertEqual(result["system"], "Yerhed")
        self.assertIn("people context", result["tool_affordance_map"])
        self.assertIn("places", result["tool_affordance_map"])
        self.assertIn("active_anchors", result)
        self.assertEqual(result["active_anchors"][0]["label"], "Grounded work")
        self.assertIn("salience_map", result)
        self.assertEqual(result["salience_map"][0]["title"], "Example Concept")
        paths = [item["path"] for item in result["baseline_context"]]
        self.assertIn(str((self.repo / "AGENTS.md").resolve()), paths)
        self.assertIn(str((self.brain / "projects" / "open-loops.md").resolve()), paths)

    def test_search_scopes(self) -> None:
        result = tools.search("grounded work", scope="people", limit=5)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["results"]), 1)
        self.assertIn("operator.md", result["results"][0]["path"])
        place = tools.search("durable test place", scope="places", limit=5)
        self.assertTrue(place["ok"])
        self.assertEqual(len(place["results"]), 1)
        org = tools.search("durable test organization", scope="organizations", limit=5)
        self.assertTrue(org["ok"])
        self.assertEqual(len(org["results"]), 1)
        bad = tools.search("grounded", scope="nope", limit=5)
        self.assertFalse(bad["ok"])

    def test_read_file_allows_roots_and_refuses_outside(self) -> None:
        allowed = tools.read_file(str(self.repo / "MEMORY.md"))
        self.assertTrue(allowed["ok"])
        outside = tools.read_file("/etc/passwd")
        self.assertFalse(outside["ok"])

    def test_read_helpers_refuse_in_root_symlink_files(self) -> None:
        outside = self.base / "outside-secret.md"
        outside.write_text("outside-only secret marker\n", encoding="utf-8")
        linked_person = self.brain / "people" / "linked-secret.md"
        linked_person.symlink_to(outside)
        linked_project = self.brain / "projects" / "linked-secret.md"
        linked_project.symlink_to(outside)

        read_result = tools.read_file(str(linked_person))
        self.assertFalse(read_result["ok"], read_result)

        search_result = tools.search("outside-only secret marker", scope="people", limit=5)
        self.assertTrue(search_result["ok"], search_result)
        self.assertFalse(search_result["results"], search_result)

        project_result = tools.read_project("linked-secret")
        self.assertFalse(project_result["ok"], project_result)

        excerpt = tools._file_excerpt(linked_project)
        self.assertFalse(excerpt["exists"], excerpt)

    def test_read_project(self) -> None:
        result = tools.read_project("example-project")
        self.assertTrue(result["ok"])
        self.assertIn("Compact docs-first", result["content"])

    def test_what_matters_now_and_morning_brief_are_grounded(self) -> None:
        now = tools.what_matters_now()
        self.assertTrue(now["ok"])
        self.assertIn("Finish Yerhed MCP", now["summary"])
        brief = tools.morning_brief()
        self.assertTrue(brief["ok"])
        self.assertIn("needs_action", brief)

    def test_closeout_check_dispositions(self) -> None:
        skipped = tools.closeout_check(str(self.repo), "worked", "none", [])
        self.assertEqual(skipped["disposition"], "skipped")
        blocked = tools.closeout_check(str(self.base / "example-project"), "updated docs", "durable architecture changed", ["README.md"])
        self.assertEqual(blocked["disposition"], "proposed")
        self.assertIn("proposed_note", blocked)
        self.assertTrue(blocked["must_show_proposal"])
        self.init_brain_git()
        updated = tools.closeout_check(str(self.base / "example-project"), "updated docs", "durable architecture changed", ["README.md"])
        self.assertEqual(updated["disposition"], "updated", updated)
        self.assertFalse(updated["pushed"])
        self.assertIn("Update:", (self.brain / "projects" / "example-project.md").read_text(encoding="utf-8"))
        dry = tools.closeout_check(str(self.base / "example-project"), "updated docs", "durable architecture changed again", ["README.md"], dry_run=True)
        self.assertEqual(dry["disposition"], "proposed")
        self.assertIn("projects/example-project.md", dry["proposed_patch"])
        self.assertIn("proposed_note", dry)
        self.assertTrue(dry["must_show_proposal"])
        sensitive = tools.closeout_check(str(self.base / "x"), "relationship note", "relationship fact changed", [])
        self.assertEqual(sensitive["disposition"], "proposed")
        self.assertIn("sensitive", sensitive["reason"])
        self.assertIn("proposed_note", sensitive)
        self.assertTrue(sensitive["must_show_proposal"])

    def test_egress_check_decisions(self) -> None:
        internal = tools.egress_check(
            destination="internal Codex chat",
            draft="Summarize the operator context for this private chat.",
            source_paths=[str(self.brain / "people" / "operator.md")],
        )
        self.assertEqual(internal["disposition"], "allow")

        private_external = tools.egress_check(
            destination="Slack",
            draft="The Example Project project changed direction.",
            source_paths=[str(self.brain / "projects" / "example-project.md")],
        )
        self.assertEqual(private_external["disposition"], "ask")

        override = tools.egress_check(
            destination="Slack",
            draft="The Example Project project changed direction.",
            source_paths=[str(self.brain / "projects" / "example-project.md")],
            user_intent="ok to include this private project detail",
        )
        self.assertEqual(override["disposition"], "allow")

        public = tools.egress_check(
            destination="GitHub README",
            draft="Shareable project facts.",
            source_paths=[str(self.brain / "projects" / "public.md")],
        )
        self.assertEqual(public["disposition"], "allow")

        sensitive = tools.egress_check(
            destination="email",
            draft="The operator prefers direct, grounded work and has relationship context.",
            source_paths=[str(self.brain / "people" / "operator.md")],
        )
        self.assertEqual(sensitive["disposition"], "redact")
        self.assertIn("suggested_draft", sensitive)

        blocked = tools.egress_check(
            destination="Slack",
            draft="Never share this.",
            source_paths=[str(self.brain / "projects" / "do-not-share.md")],
            user_intent="ok to include this private detail",
        )
        self.assertEqual(blocked["disposition"], "block")

        token = "sk-" + "abcdefghijklmnopqrstuvwxyz123456"
        secret = tools.egress_check(
            destination="Slack",
            draft=f"Token {token} should not go out.",
        )
        self.assertEqual(secret["disposition"], "block")

        missing_destination = tools.egress_check(
            destination="",
            draft="Generic project update.",
        )
        self.assertEqual(missing_destination["destination_kind"], "unknown")
        self.assertEqual(missing_destination["disposition"], "ask")
        self.assertIn("unknown-destination", missing_destination["triggers"])


    def test_prepare_external_output_wrapper(self) -> None:
        allowed = tools.prepare_external_output(
            destination="GitHub issue comment",
            draft="Shareable project facts.",
            source_paths=[str(self.brain / "projects" / "public.md")],
        )
        self.assertTrue(allowed["may_use_connector"], allowed)
        self.assertEqual(allowed["connector_action"], "proceed_with_connector_review")
        self.assertEqual(allowed["draft_for_connector"], "Shareable project facts.")

        private = tools.prepare_external_output(
            destination="Slack",
            draft="Project direction changed.",
            source_paths=[str(self.brain / "projects" / ("example-project.md" if (self.brain / "projects" / "example-project.md").exists() else "example.md"))],
        )
        self.assertFalse(private["may_use_connector"], private)
        self.assertEqual(private["connector_action"], "ask_owner_before_connector_use")
        self.assertIn("private Yerhed memory", private["approval_question"])

        sensitive = tools.prepare_external_output(
            destination="email",
            draft="The operator has relationship context.",
            source_paths=[str(self.brain / "people" / "operator.md")],
        )
        self.assertFalse(sensitive["may_use_connector"], sensitive)
        self.assertEqual(sensitive["connector_action"], "use_sanitized_draft_after_owner_review")
        self.assertIn("[redacted private detail]", sensitive["draft_for_connector"])


    def test_evidence_spans_and_citation_formatting(self) -> None:
        search_result = tools.search("grounded work", scope="people", limit=5)
        self.assertTrue(search_result["ok"], search_result)
        self.assertTrue(search_result["evidence_spans"], search_result)
        search_span = search_result["evidence_spans"][0]
        self.assertEqual(search_span["evidence_status"], "verified_current_turn")
        self.assertEqual(search_span["source_kind"], "brain")

        formatted = tools.format_memory_citations([search_span])
        self.assertTrue(formatted["citation_ui"], formatted)
        self.assertIn("<oai-mem-citation>", formatted["citation_ui"])
        self.assertIn("operator.md", formatted["citation_ui"])
        self.assertFalse(formatted["omitted"], formatted)

        file_result = tools.read_file(str(self.repo / "MEMORY.md"))
        self.assertTrue(file_result["evidence_spans"], file_result)
        file_formatted = tools.format_memory_citations(file_result["evidence_spans"])
        self.assertTrue(file_formatted["citation_ui"], file_formatted)

        project_result = tools.read_project("yerhed")
        self.assertTrue(project_result["evidence_spans"], project_result)
        project_formatted = tools.format_memory_citations(project_result["evidence_spans"])
        self.assertTrue(project_formatted["citation_ui"], project_formatted)

        fake = dict(search_span)
        fake["path"] = str(self.base / "fake.md")
        fake_formatted = tools.format_memory_citations([fake])
        self.assertFalse(fake_formatted["citation_ui"], fake_formatted)
        self.assertTrue(fake_formatted["omitted"], fake_formatted)

        stale = dict(search_span)
        stale["evidence_status"] = "memory_derived_stale"
        stale_formatted = tools.format_memory_citations([stale])
        self.assertFalse(stale_formatted["citation_ui"], stale_formatted)
        stale_summary = tools.summarize_evidence([stale])
        self.assertIn("not freshly verified", stale_summary["summary"])

        inferred = {
            "path": "",
            "line_start": 0,
            "line_end": 0,
            "note": "assistant conclusion",
            "sensitivity": "private",
            "source_kind": "assistant",
            "loaded_at": "",
            "evidence_status": "assistant_inferred",
            "evidence_id": "",
            "content_hash": "",
        }
        inferred_formatted = tools.format_memory_citations([inferred])
        self.assertFalse(inferred_formatted["citation_ui"], inferred_formatted)
        self.assertIn("assistant inference", tools.summarize_evidence([inferred])["summary"])

        redacted = dict(search_span)
        redacted["evidence_status"] = "external_redacted"
        redacted_formatted = tools.format_memory_citations([redacted])
        self.assertFalse(redacted_formatted["citation_ui"], redacted_formatted)
        self.assertIn("redacted", tools.summarize_evidence([redacted])["summary"])

        malformed = dict(search_span)
        malformed["line_start"] = 99
        malformed["line_end"] = 1
        malformed_formatted = tools.format_memory_citations([malformed])
        self.assertFalse(malformed_formatted["citation_ui"], malformed_formatted)
        self.assertIn("line range", malformed_formatted["omitted"][0]["reason"])

        expired = tools.search("grounded work", scope="people", limit=1)["evidence_spans"][0]
        tools._EVIDENCE_REGISTRY[expired["evidence_id"]]["_registered_at_epoch"] -= 3600
        expired_formatted = tools.format_memory_citations([expired], max_age_seconds=1)
        self.assertFalse(expired_formatted["citation_ui"], expired_formatted)
        self.assertIn("stale", expired_formatted["omitted"][0]["reason"])
        extended_ttl_formatted = tools.format_memory_citations([expired], max_age_seconds=999999)
        self.assertFalse(extended_ttl_formatted["citation_ui"], extended_ttl_formatted)
        self.assertIn("stale", extended_ttl_formatted["omitted"][0]["reason"])

        fresh = tools.read_file(str(self.brain / "people" / "operator.md"))["evidence_span"]
        (self.brain / "people" / "operator.md").write_text("# Operator Changed\n\nPrefers direct, grounded work.\n", encoding="utf-8")
        changed = tools.format_memory_citations([fresh])
        self.assertFalse(changed["citation_ui"], changed)
        self.assertIn("content hash", changed["omitted"][0]["reason"])

        public = tools.read_file(str(self.brain / "projects" / "public.md"))
        public_span = public["evidence_span"]
        draft = f"See {public_span['path']} for the public note."
        prepared = tools.prepare_external_output(destination="GitHub issue", draft=draft, evidence_spans=[public_span])
        self.assertTrue(prepared["may_use_connector"], prepared)
        self.assertNotIn(str(self.brain), prepared["draft_for_connector"])
        self.assertIn("[redacted local/private path]", prepared["draft_for_connector"])

        forged = dict(public_span)
        forged["evidence_id"] = "not-registered"
        forged["content_hash"] = "not-real"
        forged["sensitivity"] = "public"
        forged_prepared = tools.prepare_external_output(
            destination="GitHub issue",
            draft="Shareable project facts.",
            evidence_spans=[forged],
        )
        self.assertFalse(forged_prepared["may_use_connector"], forged_prepared)
        self.assertEqual(forged_prepared["connector_action"], "ask_owner_before_connector_use")
        self.assertTrue(forged_prepared["invalid_evidence_spans"], forged_prepared)
        self.assertFalse(forged_prepared["evidence_paths_used_for_egress"], forged_prepared)


    def test_salience_entity_resolution_and_link_suggestions(self) -> None:
        salience = tools.salience_map()
        self.assertTrue(salience["ok"])
        self.assertEqual(salience["entries"][0]["title"], "Example Concept")
        self.assertFalse(salience["warnings"])

        exact = tools.resolve_entity("Example Framework", entity_type="concept")
        self.assertTrue(exact["ok"])
        self.assertFalse(exact["ambiguous"])
        self.assertEqual(exact["recommended_path"], "concepts/example-concept.md")

        suggested = tools.suggest_links("Use Example Concept near Example Place and Example Framework.")
        self.assertTrue(suggested["ok"])
        self.assertIn("[[concepts/example-concept|Example Concept]]", suggested["suggested_draft"])
        self.assertIn("[[places/example-place|Example Place]]", suggested["suggested_draft"])
        self.assertIn("[[concepts/example-concept|Example Framework]]", suggested["suggested_draft"])
        self.assertTrue(all("line" in item and "offset" in item and "match_kind" in item for item in suggested["applied_links"]))
        self.assertTrue(any(item["match_kind"] == "alias" for item in suggested["applied_links"]))

        broad = tools.suggest_links("ChatGPT stays unlinked while Example Concept links.")
        self.assertTrue(broad["ok"], broad)
        self.assertIn("ChatGPT stays unlinked", broad["suggested_draft"])
        self.assertNotIn("[[concepts/llm-workflow|ChatGPT]]", broad["suggested_draft"])
        self.assertIn("[[concepts/example-concept|Example Concept]]", broad["suggested_draft"])
        self.assertTrue(any(item["text"] == "ChatGPT" and item["match_kind"] == "review_only_alias" and item["requires_operator_approval"] for item in broad["review_only_candidates"]))

        schema_example = tools.suggest_links("Schema example: [[path/to/page|display text]].", source_path="schema.md")
        self.assertTrue(schema_example["ok"], schema_example)
        self.assertFalse(schema_example["unresolved_candidates"], schema_example)
        ordinary_unresolved = tools.suggest_links("Ordinary note: [[path/to/page|display text]].", source_path="projects/ordinary-project.md")
        self.assertTrue(ordinary_unresolved["unresolved_candidates"], ordinary_unresolved)

        review = tools.suggest_links_for_review_set(include_changed_files=False)
        self.assertTrue(review["ok"], review)
        review_paths = {item["path"] for item in review["review_set"]}
        self.assertIn("projects/example-project.md", review_paths)
        self.assertIn("projects/open-loops.md", review_paths)
        self.assertIn("RESOLVER.md", review_paths)
        self.assertTrue(
            any(candidate["link_target"] == "concepts/example-concept" for candidate in review["new_wikilink_candidates"]),
            review,
        )
        self.assertFalse(any(candidate["source"] == "RESOLVER.md" for candidate in review["new_wikilink_candidates"]))
        self.assertFalse(any(candidate["source"].removesuffix(".md") == candidate["link_target"] for candidate in review["new_wikilink_candidates"]))
        self.assertTrue(all(candidate.get("line") and candidate.get("offset") is not None and candidate.get("match_kind") for candidate in review["new_wikilink_candidates"]))
        self.assertTrue(any(candidate.get("text") == "ChatGPT" and candidate.get("match_kind") == "review_only_alias" and candidate.get("requires_operator_approval") for candidate in review["new_wikilink_candidates"]))
        self.assertFalse(any(row.get("target") == "RESOLVER" for row in review["missing_entity_pages"]))
        candidate_keys = {
            (candidate.get("source"), candidate.get("link_target"), candidate.get("offset"), candidate.get("end_offset"))
            for candidate in review["new_wikilink_candidates"]
        }
        self.assertEqual(len(candidate_keys), len(review["new_wikilink_candidates"]))
        self.assertFalse(any(Path(row.get("path", "")).name in {"README.md", "_template.md", "index.md", "schema.md"} for row in review["missing_resolver_entries"]))
        self.assertFalse(any(row.get("key") == "readme" for row in review["duplicate_near_duplicate_entity_pages"]))
        for section in [
            "## Broken Links",
            "## Duplicate/Near-Duplicate Entity Pages",
            "## Missing Entity Pages",
            "## Missing Resolver Entries",
            "## Stale Aliases",
            "## Stale Salience / Active Anchor Promotion-Demotion Candidates",
            "## Graph Hygiene Warnings",
            "## New Wikilink Candidates",
            "## Ambiguous/Sensitive Link Candidates Requiring Operator Approval",
            "## Applied Safe Link/Entity Updates",
            "## Skipped Link/Entity Updates With Reason",
        ]:
            self.assertIn(section, review["graph_gardening_report"])

        empty_review = tools.suggest_links_for_review_set(include_changed_files=False, allowed_entity_types="companions")
        self.assertTrue(empty_review["ok"], empty_review)
        self.assertIn("## New Wikilink Candidates", empty_review["graph_gardening_report"])

    def test_graph_hygiene_warnings_for_storage_and_category_hubs(self) -> None:
        (self.brain / "projects" / "ordinary-project.md").write_text(
            "# Ordinary Project\n\n"
            "Stored in [[projects/yerhed|Yerhed]] and filed under [[Projects]].\n",
            encoding="utf-8",
        )
        (self.brain / "projects" / "project-map.md").write_text(
            "---\n"
            "tags: [\"moc\"]\n"
            "---\n"
            "# Project Map\n\n"
            "Navigation page for [[Projects]].\n",
            encoding="utf-8",
        )
        (self.brain / "projects" / "open-loops.md").write_text(
            (self.brain / "projects" / "open-loops.md").read_text(encoding="utf-8")
            + "\nAllowed semantic link to [[projects/yerhed|Yerhed]].\n",
            encoding="utf-8",
        )

        validation = tools.validate_wikilinks()
        warnings = validation["graph_hygiene_warnings"]
        self.assertTrue(
            any(row["source"] == "projects/ordinary-project.md" and row["kind"] == "yerhed_storage_hub_link" for row in warnings),
            warnings,
        )
        self.assertTrue(
            any(row["source"] == "projects/ordinary-project.md" and row["kind"] == "category_hub_link" for row in warnings),
            warnings,
        )
        self.assertFalse(
            any(row["source"] == "projects/project-map.md" and row["kind"] == "category_hub_link" for row in warnings),
            warnings,
        )
        self.assertFalse(
            any(row["source"] == "projects/open-loops.md" and row["kind"] == "yerhed_storage_hub_link" for row in warnings),
            warnings,
        )
        self.assertIn("graph hygiene warnings", validation["obsidian_report"])

    def test_yerhed_link_suggestions_require_semantic_context(self) -> None:
        (self.brain / "RESOLVER.md").write_text(
            (self.brain / "RESOLVER.md").read_text(encoding="utf-8")
            + "\n### Yerhed\n\n"
            "- type: project\n"
            "- path: projects/yerhed.md\n"
            "- aliases: Yerhed\n"
            "- triggers: private memory, graph infrastructure\n"
            "- salience: high\n"
            "- load_policy: baseline\n"
            "- baseline_handle: Yerhed is the private memory layer.\n",
            encoding="utf-8",
        )
        (self.brain / "projects" / "yerhed.md").write_text(
            "---\n"
            "type: project\n"
            "aliases: [\"Yerhed\"]\n"
            "triggers: [\"private memory\", \"graph infrastructure\"]\n"
            "salience: high\n"
            "load_policy: baseline\n"
            "sensitivity: private\n"
            "---\n"
            "# Yerhed\n\nMCP project page.\n",
            encoding="utf-8",
        )

        storage_context = tools.suggest_links("Ordinary note is named inside Yerhed.", source_path="projects/example-project.md")
        self.assertTrue(storage_context["ok"], storage_context)
        self.assertNotIn("[[projects/yerhed|Yerhed]]", storage_context["suggested_draft"])

        semantic_context = tools.suggest_links("Yerhed MCP manages the memory graph.", source_path="projects/example-graph-tool.md")
        self.assertTrue(semantic_context["ok"], semantic_context)
        self.assertIn("[[projects/yerhed|Yerhed]]", semantic_context["suggested_draft"])

        pet = tools.propose_entity_page(
            entity_type="pet",
            name="Example Cat",
            context_summary="A generic companion animal used in a unit test.",
            sensitivity="private",
        )
        self.assertTrue(pet["ok"], pet)
        self.assertEqual(pet["path"], "companions/example-cat.md")

        proposed = tools.propose_entity_page(
            entity_type="organization",
            name="New Org",
            context_summary="A generic organization used in a unit test.",
            aliases="NO",
            triggers="organization context",
            salience="low",
            sensitivity="private",
        )
        self.assertTrue(proposed["ok"], proposed)
        self.assertEqual(proposed["path"], "organizations/new-org.md")
        self.assertIn("type: organization", proposed["frontmatter"])
        self.assertIn("### New Org", proposed["resolver_entry"])

    def test_import_entity_helpers_handle_sensitive_high_volume_paths(self) -> None:
        self.init_brain_git()
        blocked = tools.upsert_entity_page(
            path="people/example-users-parent.md",
            entity_type="person",
            name="Example User's Parent",
            aliases=["Parent"],
            triggers=["family context"],
            salience="medium",
            load_policy="triggered",
            sensitivity="do_not_share",
            baseline_handle="Family context for import tests.",
            sections={"Summary": "A private family note for import testing."},
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture M001",
            commit_message="Upsert family import note",
        )
        self.assertFalse(blocked["ok"], blocked)
        self.assertIn("owner_confirmed", blocked["error"])

        created = tools.upsert_entity_page(
            path="people/example-users-parent.md",
            entity_type="person",
            name="Example User's Parent",
            aliases=["Parent"],
            triggers=["family context"],
            salience="medium",
            load_policy="triggered",
            sensitivity="do_not_share",
            baseline_handle="Family context for import tests.",
            sections={"Summary": "A private family note for import testing."},
            owner_confirmed=True,
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture M001",
            commit_message="Upsert family import note",
        )
        self.assertTrue(created["ok"], created)
        self.assertFalse(created["pushed"])
        self.assertFalse(created["warnings"], created)
        self.assertTrue(created["informational_matches"], created)
        contents = (self.brain / "people" / "example-users-parent.md").read_text(encoding="utf-8")
        self.assertIn("sensitivity: do_not_share", contents)
        self.assertIn("A private family note", contents)

        h1_stripped = tools.upsert_entity_page(
            path="concepts/h1-test.md",
            entity_type="concept",
            name="H1 Test",
            body="# H1 Test\n\n## Summary\n\nThe body should not duplicate the H1.",
            sensitivity="private",
            owner_confirmed=True,
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test H1 fixture",
            commit_message="Upsert H1 stripped note",
        )
        self.assertTrue(h1_stripped["ok"], h1_stripped)
        h1_contents = (self.brain / "concepts" / "h1-test.md").read_text(encoding="utf-8")
        self.assertEqual(h1_contents.count("# H1 Test"), 1)
        self.assertIn("stripped duplicate leading H1", " ".join(h1_stripped["warnings"]))

        append = tools.append_entity_update(
            path="people/example-user.md",
            heading="Import M002",
            body="Append helper can update people pages, not just project pages.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture M002",
            commit_message="Append person import note",
        )
        self.assertTrue(append["ok"], append)
        self.assertIn("Append helper", (self.brain / "people" / "example-user.md").read_text(encoding="utf-8"))

        concept_append = tools.append_entity_update(
            path="concepts/example-concept.md",
            heading="Import M003",
            body="Append helper can update concept pages.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture M003",
            commit_message="Append concept import note",
        )
        self.assertTrue(concept_append["ok"], concept_append)


    def test_canonical_rename_text_replace_open_loop_and_resolver_sync(self) -> None:
        self.init_brain_git()
        renamed = tools.set_canonical_entity_name(
            path="concepts/example-concept.md",
            name="Better Concept",
            aliases=["Example Concept"],
            triggers=["renamed concept"],
            baseline_handle="Better Concept is the renamed canonical display.",
            update_backlinks=True,
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test canonical rename",
            commit_message="Rename example concept",
        )
        self.assertTrue(renamed["ok"], renamed)
        concept = (self.brain / "concepts" / "example-concept.md").read_text(encoding="utf-8")
        resolver = (self.brain / "RESOLVER.md").read_text(encoding="utf-8")
        self.assertIn("# Better Concept", concept)
        self.assertIn("### Better Concept", resolver)
        self.assertIn("Example Concept", concept)

        replaced = tools.replace_text(
            path="concepts/example-concept.md",
            replacements={"old": "A durable test concept.", "new": "A durable renamed test concept."},
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test text replacement",
            commit_message="Replace concept text",
        )
        self.assertTrue(replaced["ok"], replaced)
        self.assertIn("renamed test concept", (self.brain / "concepts" / "example-concept.md").read_text(encoding="utf-8"))

        targeted = tools.update_open_loop(
            project="Yerhed V1",
            action="add",
            text="Target central open-loop section by name.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test open loop section",
            commit_message="Add named section open loop",
        )
        self.assertTrue(targeted["ok"], targeted)
        open_loops = (self.brain / "projects" / "open-loops.md").read_text(encoding="utf-8")
        self.assertIn("## Yerhed V1", open_loops)
        self.assertIn("Target central open-loop section by name.", open_loops)
        self.assertFalse((self.brain / "projects" / "yerhed-v1.md").exists())

        drift_before = tools.validate_wikilinks()
        self.assertIn("resolver_frontmatter_drift", drift_before)
        resolver_update = tools.batch_update_resolver_entries(
            [{
                "entity_type": "concept",
                "name": "Synced Concept",
                "path": "concepts/example-concept.md",
                "aliases": ["Better Concept"],
                "triggers": ["sync drift"],
                "salience": "medium",
                "load_policy": "triggered",
                "sensitivity": "private",
                "baseline_handle": "Synced resolver state.",
            }],
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test resolver drift",
            commit_message="Create resolver drift",
        )
        self.assertTrue(resolver_update["ok"], resolver_update)
        synced = tools.sync_resolver_to_frontmatter(
            path="concepts/example-concept.md",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test resolver sync",
            commit_message="Sync resolver frontmatter",
        )
        self.assertTrue(synced["ok"], synced)
        synced_text = (self.brain / "concepts" / "example-concept.md").read_text(encoding="utf-8")
        self.assertIn("# Synced Concept", synced_text)
        self.assertIn("salience: medium", synced_text)

    def test_memory_plan_import_coverage_and_wikilink_validation(self) -> None:
        self.init_brain_git()
        plan = [
            {
                "id": "M001",
                "category": "people",
                "destination": "people/example-user.md",
                "sensitivity": "private",
                "load_policy": "baseline",
                "action": "merge",
                "distilled_text": "Operator prefers grounded memory imports.",
                "links": ["concepts/example-concept"],
            },
            {
                "id": "M002",
                "category": "concepts",
                "destination": "concepts/example-concept.md",
                "sensitivity": "sensitive",
                "load_policy": "triggered",
                "action": "merge",
                "distilled_text": "Example Concept carries import validation context.",
                "links": ["people/example-user"],
            },
            {
                "id": "M003",
                "category": "archive",
                "destination": "archive/import-review.md",
                "sensitivity": "archival",
                "load_policy": "archival",
                "action": "upsert",
                "distilled_text": "Archival import item for coverage validation.",
                "links": ["RESOLVER"],
            },
        ]
        dry = tools.import_memory_plan(plan, dry_run=True)
        self.assertTrue(dry["ok"], dry)
        self.assertTrue(dry["dry_run"])
        self.assertEqual([row["id"] for row in dry["coverage"]], ["M001", "M002", "M003"])

        imported = tools.import_memory_plan(
            plan,
            dry_run=False,
            commit_strategy="single",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture M001-M003",
            commit_message="Import mini memory plan",
        )
        self.assertTrue(imported["ok"], imported)
        self.assertFalse(imported["pushed"])
        statuses = {row["id"]: row["status"] for row in imported["coverage"]}
        self.assertEqual(statuses, {"M001": "merged", "M002": "merged", "M003": "written"})
        ledger = self.brain / "sources" / "import-ledgers" / "memory-import.md"
        self.assertTrue(ledger.exists())
        self.assertIn("M001", ledger.read_text(encoding="utf-8"))

        validation = tools.validate_wikilinks()
        self.assertTrue(validation["ok"], validation)
        self.assertFalse(validation["unresolved"], validation)
        self.assertFalse(validation["self_links"], validation)
        self.assertFalse(validation["resolver_page_mismatches"], validation)

        dep_plan = [
            {
                "id": "M004",
                "category": "people",
                "entity_type": "person",
                "destination": "people/planned-person.md",
                "name": "Planned Person",
                "sensitivity": "private",
                "load_policy": "triggered",
                "action": "upsert",
                "resolver_intent": "upsert",
                "distilled_text": "Planned Person links to a concept created in the same import.",
                "links": ["concepts/planned-concept"],
            },
            {
                "id": "M005",
                "category": "concepts",
                "entity_type": "concept",
                "destination": "concepts/planned-concept.md",
                "name": "Planned Concept",
                "sensitivity": "private",
                "load_policy": "triggered",
                "action": "create_spine",
                "resolver_intent": "upsert",
                "distilled_text": "Concept spine created before dependent entity links.",
            },
        ]
        dry_dep = tools.import_memory_plan(dep_plan, dry_run=True)
        self.assertTrue(dry_dep["ok"], dry_dep)
        self.assertEqual(dry_dep["apply_order"][0], "concepts/planned-concept.md")
        self.assertEqual(dry_dep["would_update_resolver_count"], 2)
        imported_dep = tools.import_memory_plan(
            dep_plan,
            dry_run=False,
            commit_strategy="single",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test dependency import",
            commit_message="Import dependency ordered plan",
            ledger_path="sources/import-ledgers/dependency-import.md",
        )
        self.assertTrue(imported_dep["ok"], imported_dep)
        resolver_text = (self.brain / "RESOLVER.md").read_text(encoding="utf-8")
        self.assertIn("### Planned Concept", resolver_text)
        self.assertIn("### Planned Person", resolver_text)

    def test_batch_resolver_update_skips_low_and_preserves_sensitivity(self) -> None:
        self.init_brain_git()
        entries = [
            {
                "entity_type": "person",
                "name": "Example User",
                "path": "people/example-user.md",
                "aliases": ["Example"],
                "triggers": ["operator"],
                "salience": "high",
                "load_policy": "baseline",
                "sensitivity": "private",
                "baseline_handle": "Operator page.",
            },
            {
                "entity_type": "place",
                "name": "Skipped Place",
                "path": "places/example-place.md",
                "salience": "low",
                "load_policy": "triggered",
            },
        ]
        result = tools.batch_update_resolver_entries(
            entries,
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test resolver batch",
            commit_message="Batch resolver update",
        )
        self.assertTrue(result["ok"], result)
        statuses = {row["name"]: row["status"] for row in result["results"]}
        self.assertEqual(statuses["Example User"], "updated")
        self.assertEqual(statuses["Skipped Place"], "skipped")
        salience = tools.salience_map(include_page_records=True)
        self.assertTrue(salience["ok"], salience)
        self.assertFalse(salience["warnings"], salience)
        example_user = [entry for entry in salience["entries"] if entry["path"] == "people/example-user.md"][0]
        self.assertEqual(example_user["sensitivity"], "private")

    def test_entity_write_tools_are_policy_gated_and_commit_locally(self) -> None:
        self.init_brain_git()
        missing = tools.create_entity_page(
            entity_type="place",
            name="New Place",
            context_summary="A generic place used in a unit test.",
            sensitivity="",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Create test place",
        )
        self.assertFalse(missing["ok"])

        created = tools.create_entity_page(
            entity_type="place",
            name="New Place",
            context_summary="A generic place used in a unit test.",
            sensitivity="private",
            aliases="NP",
            triggers="new location",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Create test place",
        )
        self.assertTrue(created["ok"], created)
        self.assertFalse(created["pushed"])
        self.assertTrue((self.brain / "places" / "new-place.md").exists())

        resolver = tools.update_resolver_entry(
            entity_type="place",
            name="New Place",
            path="places/new-place.md",
            aliases="NP",
            triggers="new location",
            salience="medium",
            load_policy="triggered",
            baseline_handle="A generic place used in a unit test.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Add test place resolver entry",
        )
        self.assertTrue(resolver["ok"], resolver)
        self.assertFalse(resolver["pushed"])

        links = tools.update_entity_links(
            path=str(self.brain / "projects" / ("example-project.md" if (self.brain / "projects" / "example-project.md").exists() else "example.md")),
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Link test project note",
        )
        self.assertTrue(links["ok"], links)
        self.assertFalse(links["pushed"])
        target = self.brain / "projects" / ("example-project.md" if (self.brain / "projects" / "example-project.md").exists() else "example.md")
        self.assertIn("[[concepts/example-concept|Example Concept]]", target.read_text(encoding="utf-8"))

    def test_write_memory_patch_refuses_missing_policy_and_outside_paths(self) -> None:
        missing = tools.write_memory_patch("updated", "", "source", "", "commit")
        self.assertFalse(missing["ok"])
        outside_patch = """--- a/../oops.md\n+++ b/../oops.md\n@@ -0,0 +1 @@\n+bad\n"""
        outside = tools.write_memory_patch("updated", "explicit update-policy request", "source", outside_patch, "commit")
        self.assertFalse(outside["ok"])

    def test_write_memory_patch_refuses_symlink_creation(self) -> None:
        self.init_brain_git()
        patch = (
            "diff --git a/projects/link-out.md b/projects/link-out.md\n"
            "new file mode 120000\n"
            "index 0000000..1111111\n"
            "--- /dev/null\n"
            "+++ b/projects/link-out.md\n"
            "@@ -0,0 +1 @@\n"
            "+../../outside.md\n"
        )
        result = tools.write_memory_patch(
            disposition="updated",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            patch=patch,
            commit_message="Try symlink creation",
        )
        self.assertFalse(result["ok"], result)
        self.assertIn("symlink", result["error"])
        self.assertFalse((self.brain / "projects" / "link-out.md").exists())

    def test_write_memory_patch_refuses_dirty_target_paths(self) -> None:
        self.init_brain_git()
        path = self.brain / "projects" / "example-project.md"
        if not path.exists():
            path = self.brain / "projects" / "example.md"
        dirty = path.read_text(encoding="utf-8") + "\nUncommitted private note.\n"
        path.write_text(dirty, encoding="utf-8")
        patch = "".join(
            difflib.unified_diff(
                dirty.splitlines(keepends=True),
                (dirty + "\n## Update\n\n- This should not be bundled.\n").splitlines(keepends=True),
                fromfile=f"a/projects/{path.name}",
                tofile=f"b/projects/{path.name}",
            )
        )
        result = tools.write_memory_patch(
            disposition="updated",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            patch=patch,
            commit_message="Try dirty memory update",
        )
        self.assertFalse(result["ok"], result)
        self.assertIn("uncommitted", result["error"])
        self.assertNotIn("This should not be bundled", path.read_text(encoding="utf-8"))

    def test_write_helpers_refuse_symlink_targets(self) -> None:
        self.init_brain_git()
        outside = self.base / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        linked = self.brain / "projects" / "linked.md"
        linked.symlink_to(outside)

        structured = tools.append_project_update(
            project="linked",
            heading="Should Not Write",
            body="This must not follow a symlink.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Try symlink structured write",
        )
        self.assertFalse(structured["ok"], structured)
        self.assertIn("symlink", structured["error"])

        patch = "".join(
            difflib.unified_diff(
                outside.read_text(encoding="utf-8").splitlines(keepends=True),
                "outside\npatched\n".splitlines(keepends=True),
                fromfile="a/projects/linked.md",
                tofile="b/projects/linked.md",
            )
        )
        exact = tools.write_memory_patch(
            disposition="updated",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            patch=patch,
            commit_message="Try symlink exact write",
        )
        self.assertFalse(exact["ok"], exact)
        self.assertIn("symlink", exact["error"])
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside\n")

    def test_write_memory_patch_applies_and_commits_fixture_patch(self) -> None:
        self.init_brain_git()
        path = self.brain / "projects" / "example-project.md"
        old = path.read_text(encoding="utf-8")
        new = old + "\n## Update\n\n- MCP write fixture.\n"
        patch = "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile="a/projects/example-project.md",
                tofile="b/projects/example-project.md",
            )
        )
        result = tools.write_memory_patch(
            disposition="updated",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            patch=patch,
            commit_message="Record fixture memory update",
        )
        self.assertTrue(result["ok"], result)
        self.assertRegex(result["commit"], r"^[0-9a-f]+$")
        self.assertIn("MCP write fixture", path.read_text(encoding="utf-8"))

    def test_structured_log_and_project_writes_commit_without_patch_hunks(self) -> None:
        self.init_brain_git()
        log_result = tools.append_log_entry(
            title="Structured Write",
            body="Yerhed can append logs without hand-written patch hunks.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Append structured log entry",
        )
        self.assertTrue(log_result["ok"], log_result)
        self.assertIn("Structured Write", (self.brain / "log.md").read_text(encoding="utf-8"))

        project_result = tools.append_project_update(
            project="example-project",
            heading="Structured Project Update",
            body="Project update helper wrote this section directly.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Append structured project update",
        )
        self.assertTrue(project_result["ok"], project_result)
        self.assertIn("Structured Project Update", (self.brain / "projects" / "example-project.md").read_text(encoding="utf-8"))

    def test_update_open_loop_central_page_targets_yerhed_v1_and_merges_duplicate_section(self) -> None:
        self.init_brain_git()
        add = tools.update_open_loop(
            project="open-loops",
            action="add",
            text="Exercise structured open-loop helper.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Add structured open loop",
        )
        self.assertTrue(add["ok"], add)
        contents = (self.brain / "projects" / "open-loops.md").read_text(encoding="utf-8")
        self.assertIn("## Yerhed V1", contents)
        self.assertIn("- Exercise structured open-loop helper.", contents)
        self.assertIn("- Migrate prior memory and system-prompt material into Yerhed.", contents)
        self.assertNotIn("\n## Open Loops\n", contents)

        replace = tools.update_open_loop(
            project="open-loops",
            action="replace",
            text="Exercise structured open-loop helper.",
            replacement_text="Structured open-loop helper exercised.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Replace structured open loop",
        )
        self.assertTrue(replace["ok"], replace)
        remove = tools.update_open_loop(
            project="open-loops",
            action="remove",
            text="Structured open-loop helper exercised.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Remove structured open loop",
        )
        self.assertTrue(remove["ok"], remove)
        contents = (self.brain / "projects" / "open-loops.md").read_text(encoding="utf-8")
        self.assertNotIn("Structured open-loop helper exercised.", contents)

    def test_update_open_loop_project_page_uses_open_loops_section(self) -> None:
        self.init_brain_git()
        add = tools.update_open_loop(
            project="example-project",
            action="add",
            text="Exercise project-specific open-loop helper.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Add project open loop",
        )
        self.assertTrue(add["ok"], add)
        replace = tools.update_open_loop(
            project="example-project",
            action="replace",
            text="Exercise project-specific open-loop helper.",
            replacement_text="Project-specific open-loop helper exercised.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Replace project open loop",
        )
        self.assertTrue(replace["ok"], replace)
        remove = tools.update_open_loop(
            project="example-project",
            action="remove",
            text="Project-specific open-loop helper exercised.",
            policy_basis="explicit update-policy backed test update",
            source_summary="unit test fixture",
            commit_message="Remove project open loop",
        )
        self.assertTrue(remove["ok"], remove)
        contents = (self.brain / "projects" / "example-project.md").read_text(encoding="utf-8")
        self.assertIn("## Open Loops", contents)
        self.assertNotIn("Project-specific open-loop helper exercised.", contents)


if __name__ == "__main__":
    unittest.main()
