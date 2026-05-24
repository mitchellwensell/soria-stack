---
name: soria-ticket
description: 'Soria Stack Hermes skill for ticket. Capture a structured issue from a Soria workflow in Hermes. Use when the user wants a ticket filed, when a bug or feature needs to be recorded with enough context to act on, or when another Soria skill reaches a ticket disposition. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/ticket/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Ticket

Hermes adapter for upstream Soria-stack skill `ticket`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-ticket`
- Upstream source: `plugins/soria-stack/skills/ticket/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Ticket

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-ticket` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- gather repro steps (exact MCP tool call + params), recent pipeline
  activity, workaround, and root-cause hints
- deduplicate against existing issues when the Linear connector exists
- keep ticket filing as a side-quest, then return to the main workflow

## Notes

- If Linear is available in the Hermes session, use it.
- If Linear is unavailable, file a GitHub issue when appropriate or produce a
  ready-to-paste issue draft with the same structure.
