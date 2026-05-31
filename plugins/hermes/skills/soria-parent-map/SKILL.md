---
name: soria-parent-map
description: 'Soria Stack Hermes skill for parent-map. Centralized parent-company mapping in Hermes. Use when company names or codes must be resolved to ultimate parents, ownership changes need to be tracked over time, or the shared parent-mapping table needs to be maintained. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/parent-map/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Parent Map

Hermes adapter for upstream Soria-stack skill `parent-map`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-parent-map`
- Upstream source: `plugins/soria-stack/skills/parent-map/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Parent Map

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-parent-map` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- centralized parent-company resolution; code-based joins, not name-based
- ownership timelines, tickers, and affiliations from parallel.ai
- MCP-driven upload/publish flow:
  `scraper_upload_urls / scraper_confirm_uploads`,
  `schema_mappings`,
  `warehouse_manage(group_id=..., publish=True)`
- wire into dbt intermediate/marts, not into a "gold" layer
- explicit review of ambiguous parent relationships before mutating shared data
