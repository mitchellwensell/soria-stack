---
name: soria-plan
description: 'Soria Stack Hermes skill for plan. ETVLR planning for Hermes. Use when the user wants a plan before building, when a data task needs phase breakdowns, verification criteria, or sequencing across ingest, mapping, dive work, verification, and promotion. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/plan/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Plan

Hermes adapter for upstream Soria-stack skill `plan`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-plan`
- Upstream source: `plugins/soria-stack/skills/plan/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Plan

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-plan` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- break work into Extract, Transform, Value Map, Load, and Represent phases
- R phase targets a dive (dbt marts + manifest + TSX + DivesPage entry +
  verify seed rows + methodology content) — not a legacy dashboard
- define verification before implementation
- ask clarifying questions directly when the plan depends on a real choice
- use mempalace when available for prior context and domain grounding
- t-shirt sizing (S/M/L/XL), never time estimates
