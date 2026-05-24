---
name: soria-dev-env
description: 'Soria Stack Hermes skill for dev-env. Use when entering a Soria app worktree, starting or repairing the local backend/frontend stack, preparing runtime tests, or needing an isolated branch dev environment. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/dev-env/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Dev Env

Hermes adapter for upstream Soria-stack skill `dev-env`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-dev-env`
- Upstream source: `plugins/soria-stack/skills/dev-env/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Dev Env

Hermes adaptation of `Soria-Inc/soria-stack` `/soria-dev-env`.

Read `../../references/hermes-adapter.md`, then read the target repo's
`AGENTS.md` and `CLAUDE.md`.

Use the canonical top-level skill logic:

- start or repair the Soria branch dev stack
- ensure `frontend/.env.local` is present in branch worktrees by copying it
  from `~/workspace/soria-2/frontend/.env.local` when missing
- report frontend/backend URLs and logs
- distinguish branch dev envs from data/dive `/soria-env`
- explain that Postgres and MotherDuck are cloned but Turbopuffer is not
- route chunk/search/delete runtime tests to the app repo helper
  `scripts/seed-dev-tp.py` when real dev TP rows are needed
