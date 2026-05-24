---
name: soria-env
description: 'Soria Stack Hermes skill for env. Preflight the Soria dev stack in Hermes. Use when the user asks what they''re pointed at or whether their local setup is working. There are no isolated envs anymore — MCP writes land on shared state with soft-delete safety. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/env/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Env

Hermes adapter for upstream Soria-stack skill `env`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-env`
- Upstream source: `plugins/soria-stack/skills/env/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Env

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-env` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- probe `database_query "SELECT 1"` to confirm MCP reachability
- check `make dev-https` cert presence (`frontend/dev.soriaanalytics.com.pem`)
- report recent writes via `pipeline_activity`
- surface uncommitted / unpushed work — shared state doesn't forgive WIP

## Notes

- If the MCP probe fails, the user must configure `soria` MCP in their Hermes
  client (HTTP endpoint) and restart.
- There is no `soria env branch/checkout/status/diff/teardown/restore` — the
  CLI is gone. `git checkout` + `make dev-https` is the local flow.
- **Vite liveness:** `curl -sk -o /dev/null -w "%{http_code}\n"
  https://dev.soriaanalytics.com/` — if 000, `make dev-https` runs in the
  foreground and died with its shell. Restart detached:
  `cd frontend && nohup npx vite --port 5189 > /tmp/soria-vite.log 2>&1 & disown`.
- **Staging/prod badge:** default is prod; toggle to staging to see your
  local `dbt run` output. Customer view locks to prod.
