---
name: parent-map
description: Centralized parent-company mapping in Codex. Use when company names or codes must be resolved to ultimate parents, ownership changes need to be tracked over time, or the shared parent-mapping table needs to be maintained.
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: parent-map/SKILL.md
  variant: codex
---

# Parent Map

Codex adaptation of the `Soria-Inc/soria-stack` `/parent-map` skill.

Read [../../references/codex-adapter.md](../../references/codex-adapter.md)
before acting.

## Focus

- centralized parent-company resolution; code-based joins, not name-based
- ownership timelines, tickers, and affiliations from parallel.ai
- MCP-driven upload/publish flow:
  `mcp__soria__scraper_upload_urls / scraper_confirm_uploads`,
  `mcp__soria__schema_mappings`,
  `mcp__soria__warehouse_manage(group_id=..., publish=True)`
- wire into dbt intermediate/marts, not into a "gold" layer
- explicit review of ambiguous parent relationships before mutating shared data
