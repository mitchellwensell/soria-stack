---
name: soria-tools
description: 'Soria Stack Hermes skill for tools. Verify the Soria MCP and local dev stack are ready in Hermes. Use at the start of a Soria session or whenever the workflow is blocked by missing MCP config, missing local tools (uv, node, dbt, make, git, gh), or a broken dev-https cert. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/tools/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Tools

Hermes adapter for upstream Soria-stack skill `tools`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-tools`
- Upstream source: `plugins/soria-stack/skills/tools/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Tools

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-tools` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- probe `database_query "SELECT 1"` to confirm MCP reachability
- verify local tools: `uv`, `node`, `dbt`, `make`, `git`, `gh`
- confirm `dbt debug` passes against `soria_duckdb_staging`
- confirm the `dev-https` cert exists (`frontend/dev.soriaanalytics.com.pem`)
- route the user into `status`, `plan`, `ingest`, or `dive` once the shell is ready

## Notes

- There is no `soria` CLI anymore. If you reach for one, stop and fix the
  MCP config instead.
