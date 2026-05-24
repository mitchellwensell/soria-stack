---
name: soria-diagnose
description: 'Soria Stack Hermes skill for diagnose. Diagnose and fix broken Soria workflows in Hermes. Use for silent failures, missing data, dive load failures, schema mismatches, infrastructure issues, or pipeline behavior that looks wrong and needs triage before guessing. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/diagnose/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Diagnose

Hermes adapter for upstream Soria-stack skill `diagnose`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-diagnose`
- Upstream source: `plugins/soria-stack/skills/diagnose/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Diagnose

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-diagnose` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- triage first, observe before hypothesizing
- schema discovery via `database_query` /
  `warehouse_query` on `information_schema.columns` before any
  other query
- trace failing data through layers: Postgres state → bronze → staging →
  intermediate → marts
- use `pipeline_activity / pipeline_history` as the audit trail
- use mempalace when available for prior failures or known patterns
- either fix inline (flip `deleted_at`, re-run dbt, fix SQL) or hand off to
  `ticket` with a structured disposition

## Common infra recipes

- **Vite died** (`curl https://dev.soriaanalytics.com/` → 000):
  `cd frontend && nohup npx vite --port 5189 > /tmp/soria-vite.log 2>&1 & disown`.
  `make dev-https` is foreground-only; it dies with its shell. If recurrent,
  ticket the Makefile to daemonize like `run-dev` does.
- **"Data looks wrong" on the dev URL:** check the `EnvironmentBadge` mode
  (staging amber vs prod green) before chasing it as a pipeline bug. Routes
  via the `X-SQLMESH-ENV` header (legacy name).
