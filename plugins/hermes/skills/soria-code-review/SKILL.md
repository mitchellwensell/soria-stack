---
name: soria-code-review
description: 'Soria Stack Hermes skill for code-review. Use when reviewing Soria code, PRs, commits, or diffs for readiness, especially DBOS, MCP, API, database, scraper, extractor, observability, Turbopuffer, warehouse, frontend, or test-boundary changes. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/code-review/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Code Review

Hermes adapter for upstream Soria-stack skill `code-review`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-code-review`
- Upstream source: `plugins/soria-stack/skills/code-review/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Code Review

Hermes adaptation of `Soria-Inc/soria-stack` `/soria-code-review`.

Read `../../references/hermes-adapter.md`, then read the target repo's
`AGENTS.md` and `CLAUDE.md` when present.

Review Soria diffs against repo-specific implementation patterns:

- DBOS workflows, queues, dedupe, worker imports
- workflow/tool/API/schema boundaries
- MCP and FastAPI wrapper contracts
- database idempotency and races
- observability suppression
- scraper/extractor/pipeline contracts
- Turbopuffer/search safety
- whether `/soria-test` evidence hit the risky boundary

Findings first. Then residual risks. Then verdict: ready, ready after fixes,
or not ready.
