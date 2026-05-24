# Hermes Adapter

This directory is the Hermes-facing surface for `Soria-Inc/soria-stack`.
The Soria-stack repo remains the source of truth; do not edit generated
Hermes skill files by hand.

## Runtime Differences

- Hermes skill names are namespaced as `soria-*` to avoid collisions with
  bundled skills such as `plan`, `test`, `status`, and `browse`.
- The Soria MCP is configured in Hermes as the `sumo` MCP server.
- Soria MCP tools appear without the legacy `mcp__soria__` prefix. For example,
  use `database_query`, `warehouse_query`, `file_query`, `scraper_manage`,
  `extraction_run`, `value_manage`, `warehouse_promote`, and related tools.
- If an upstream skill says to invoke `/status`, use `/soria-status` in Hermes.
- If an upstream skill says to invoke `/browse`, use `/soria-browse` in Hermes.
- Use the same evidence standard as the canonical Soria-stack workflow: show rows, counts, file paths,
  screenshots, logs, or exact command output before claiming completion.

## Maintenance

Run this from the repo root after changing Codex skill wrappers:

```bash
python3 scripts/sync-hermes-skills.py
```

The VPS installer and auto-update script run it automatically.
