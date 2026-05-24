---
name: soria-verify
description: 'Soria Stack Hermes skill for verify. Prove Soria data is correct in Hermes with evidence, not assertions. Use for warehouse checks, dive verification, extraction validation, verification-seed analysis, and any request to prove, validate, or spot-check data. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/verify/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Verify

Hermes adapter for upstream Soria-stack skill `verify`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-verify`
- Upstream source: `plugins/soria-stack/skills/verify/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Verify

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-verify` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- compare rendered / queried values against rows in the shared
  `verifications.csv` seed (filtered by `model` column)
- run `warehouse_query` for each layer when tracing data through
  bronze → staging → intermediate → marts
- escalate from Tier 1 spot checks to Tier 2 sum checks to Tier 3 external
  benchmarks whenever the data supports it
- refresh the seed via local `dbt seed --select verifications`; query
  `soria_duckdb_staging.main.verifications` to confirm
- never claim success without showing concrete evidence
- route to `dashboard-review` if the user needs live UI proof
