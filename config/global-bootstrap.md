# Yerhed Global Boot Card

Yerhed is the private memory and operating layer for Codex.

- Prefer the `yerhed` MCP server for memory, project continuity, people, preferences, history, ideas, sources, open loops, and external-output safety.
- If `YERHED_DISABLED=1` is set, it overrides this boot card: do not call Yerhed bootstrap, Yerhed MCP tools, or closeout memory writes; use ordinary repo-local context until re-enabled.
- If Yerhed has not already loaded in this chat and the request may need continuity, call `yerhed.bootstrap_context` once and retain its tool map.
- For durable local repo/project changes, run `yerhed.closeout_check` before the final response.
- Before sharing memory-derived text through Slack, email, GitHub, public docs, posts, calendar invites, or other third-party surfaces, use `yerhed.prepare_external_output`.
- If MCP is unavailable, read the `AGENTS.md` file in the Yerhed checkout and follow its file-first fallback.
- Never push the brain root; if the brain root has a remote, stop and report it.
- Repo-local `AGENTS.md` files are project-specific only and should not duplicate the full Yerhed policy.
