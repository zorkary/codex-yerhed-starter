# Disable And Remove Yerhed

Use this when you want Yerhed to stop participating immediately, or when you want
to remove the local integration pieces from a Codex setup.

## Runtime Kill Switch

Set:

```sh
export YERHED_DISABLED=1
```

While this is set:

- the hook emits disabled guidance instead of bootstrap reminders
- MCP tools refuse before reading or writing anything
- static `AGENTS.md` files remain plain text, but disabled mode overrides their
  Yerhed bootstrap and closeout guidance

Re-enable for the shell/session with:

```sh
unset YERHED_DISABLED
# or
export YERHED_DISABLED=0
```

Restart Codex if the running app session does not pick up the environment
change.

## Helper Script

For a local summary of disable/re-enable/remove steps:

```sh
scripts/disable_yerhed.sh
```

The helper must not delete memory, push, call network services, or mutate
third-party state.

## Full Local Removal

Remove installed integration points you no longer want:

```sh
scripts/uninstall_hook.sh
codex mcp remove yerhed
scripts/uninstall_git_hooks.sh
scripts/uninstall_brain_git_guard.sh --brain-root "$YERHED_BRAIN_ROOT"
scripts/uninstall_external_repo_guard.sh /path/to/repo
```

Also remove the Yerhed global boot card from `$CODEX_HOME/AGENTS.md` if you
installed it with `scripts/install_global_bootstrap.sh`.

If you want tools to stop finding memory by path, move or rename the brain root
manually. Do not delete your brain root unless you are intentionally destroying
your local memory.
