---
name: soria-preview
description: 'Soria Stack Hermes skill for preview. Render a dive as markdown tables in Hermes without opening a browser. Use when the user wants to inspect a dive''s current output shape, filters, or likely rendered values by reading the manifest and querying the warehouse. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/preview/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Preview

Hermes adapter for upstream Soria-stack skill `preview`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-preview`
- Upstream source: `plugins/soria-stack/skills/preview/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Preview

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-preview` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- read the manifest, derive the SQL shape from `{table, columns, where,
  filters, groupBy}`
- query `soria_duckdb_staging.main_marts.{model}` via
  `warehouse_query` — this surfaces your local `dbt run` output,
  which the prod-pointed frontend won't show until CI merges
- format the output the way the dive presents it (pivot tables, not raw rows)
- route to `verify` or `dashboard-review` if the preview reveals a real issue

## Notes

- Read-only. No writes. No dbt runs. Report drift; don't fix it.
