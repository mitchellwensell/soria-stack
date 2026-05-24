---
name: soria-map
description: 'Soria Stack Hermes skill for map. Value mapping in Hermes. Use when raw values need to be normalized to canonical forms across eras and sources. Drive through `value_manage` (index / map / unmap / rename / delete) with evidence, not string matching. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/map/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Map

Hermes adapter for upstream Soria-stack skill `map`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-map`
- Upstream source: `plugins/soria-stack/skills/map/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Map

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-map` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- `value_manage(action="read"|"index"|"map"|"unmap"|"rename")`
- semantic normalization decisions with concrete evidence (typo vs rebrand
  vs methodology change vs genuinely distinct)
- mempalace support when available for ticker, company, or domain grounding
- re-publish bronze with `force=True` after mapping updates so mapped values
  propagate
- hand off to `verify` after substantial mapping changes
