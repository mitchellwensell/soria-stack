---
name: soria-status
description: 'Soria Stack Hermes skill for status. Pipeline reconnaissance in Hermes. Use when the user asks what exists for a concept, scraper, group, marts model, warehouse table, or dive. Drive through `database_query` / `warehouse_query` / `file_query` / `pipeline_activity` plus filesystem walks. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/status/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Status

Hermes adapter for upstream Soria-stack skill `status`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-status`
- Upstream source: `plugins/soria-stack/skills/status/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Status

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-status` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- Postgres state via `database_query` (scrapers, groups, files,
  schemas, mappings, events)
- warehouse state via `warehouse_query` against
  `soria_duckdb_staging` (bronze + dbt layers)
- `warehouse_diff` for staging vs prod at `_file_id` grain
- dive filesystem and git-state reconnaissance under `frontend/src/dives/`
- report gaps, staleness, and incomplete pipeline stages explicitly
- read-only — never modify anything
