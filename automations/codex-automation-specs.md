# Codex Automation Prompt Templates

These are reusable prompts for Codex heartbeats. They are not live scheduled
records. Keep real automation records, target thread IDs, and local Codex state
out of this repo.

Prefer Yerhed MCP with file fallback. Do not create cron jobs, launchd jobs,
daemons, shell watchers, sends, publishes, pushes, remotes, or third-party
effects from these templates.

## Defaults

- Morning Brief: weekdays at 8:30 AM local time.
- Dream Cycle: Sundays at 2:00 PM local time; output must include the graph-gardening audit fields from `automations/dream-cycle.md`.
- Weekly Review: Fridays at 4:30 PM local time.
- Project Refresh: manual, after meaningful repo/product/doc changes.

Use dedicated Codex heartbeat threads for recurring loops. Some Codex clients may
limit active heartbeat count per thread, and dedicated threads keep review output
cleaner.

## Morning Brief

```text
Use Yerhed. Create or update one Codex heartbeat automation for the Yerhed
Morning Brief in this dedicated thread.

Prefer Yerhed MCP if available:
- call yerhed.bootstrap_context first and retain its tool affordance map
- use yerhed.morning_brief when available
- use yerhed.closeout_check when durable Yerhed state may need updating
- use structured memory helpers when allowed by config/update-policy.md

If MCP is unavailable, fall back to automations/morning-brief.md and direct file
reads from the Yerhed repo and brain root.

Schedule suggestion: weekdays at 8:30 AM in my local timezone.
Keep it attached to this thread.
Keep it review-only for external side effects.

Do not create cron jobs, launchd jobs, daemons, shell watchers, email sends,
calendar writes, pushes, remotes, or third-party side effects.

After setup, report the automation name, kind, status, schedule, target thread,
and automation record path if Codex exposes one.
```

## Dream Cycle

```text
Use Yerhed. Create or update one Codex heartbeat automation for the Yerhed Dream
Cycle in this dedicated thread.

Prefer Yerhed MCP if available:
- call yerhed.bootstrap_context first and retain its tool affordance map
- use yerhed.search, yerhed.read_file, yerhed.salience_map, yerhed.resolve_entity, and yerhed.validate_wikilinks as needed throughout the thread
- run yerhed.suggest_links_for_review_set or an equivalent concrete per-file suggest_links sweep over the required review set; pass source-path context to suggest_links when supported so schema/example wikilink ignore behavior matches validation
- review inbox notes, ideas, stale open loops, concepts, sources, and project pages for possible connections
- report graph-gardening fields: broken links; duplicate/near-duplicate entity pages; missing entity pages; missing resolver entries; stale aliases; stale salience / Active Anchor promotion-demotion candidates; graph hygiene warnings for fake hub links such as storage-only `[[Yerhed]]` links or ordinary-page category hubs like `[[Projects]]`; new wikilink candidates with match_kind/link_policy when useful; ambiguous/sensitive/review-only link candidates requiring operator approval; applied safe link/entity updates only when requires_operator_approval=false, link_policy=auto, Codex/LLM semantic review passes, and update policy allows it; skipped link/entity updates with reason
- use yerhed.closeout_check
- use structured memory helpers when allowed by config/update-policy.md

If MCP is unavailable, fall back to automations/dream-cycle.md and direct file
reads from the Yerhed repo and brain root.

Schedule suggestion: Sundays at 2:00 PM in my local timezone.
Attach it to this dedicated thread.
Keep it review-only for external side effects.

Do not create cron jobs, launchd jobs, daemons, shell watchers, email sends,
calendar writes, pushes, remotes, or third-party side effects.

After setup, report the automation name, kind, status, schedule, target thread,
and automation record path if Codex exposes one.
```

## Weekly Review

```text
Use Yerhed. Create or update one Codex heartbeat automation for the Yerhed Weekly
Review in this dedicated thread.

Prefer Yerhed MCP if available:
- call yerhed.bootstrap_context first and retain its tool affordance map
- use yerhed.what_matters_now
- use yerhed.search and yerhed.read_file as needed throughout the thread
- review current projects, decisions, open loops, and next actions
- use yerhed.closeout_check
- use structured memory helpers when allowed by config/update-policy.md

If MCP is unavailable, fall back to automations/weekly-review.md and direct file
reads from the Yerhed repo and brain root.

Schedule suggestion: Fridays at 4:30 PM in my local timezone.
Attach it to this dedicated thread.
Keep it review-only for external side effects.

Do not create cron jobs, launchd jobs, daemons, shell watchers, email sends,
calendar writes, pushes, remotes, or third-party side effects.

After setup, report the automation name, kind, status, schedule, target thread,
and automation record path if Codex exposes one.
```

## Project Refresh

```text
Use Yerhed. Run the project refresh protocol for this repo or project.

Prefer Yerhed MCP if available:
- call yerhed.bootstrap_context first and retain its tool affordance map
- read the matching project page with yerhed.read_project or scoped search
- inspect repo docs/status enough to ground the refresh
- use yerhed.closeout_check
- use structured memory helpers when allowed by config/update-policy.md

If MCP is unavailable, fall back to automations/project-refresh.md and direct
file reads.

Return a reviewable summary of status, decisions, open loops, and next action.
Do not push, create remotes, schedule jobs, send messages, publish, or affect
third parties unless explicitly requested.
```
