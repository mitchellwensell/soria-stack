---
name: soria-test
description: 'Soria Stack Hermes skill for test. Use when testing Soria engineering changes, deciding which proof layer is credible, running E2E checks, or verifying MCP, DBOS, FastAPI, Turbopuffer, warehouse, scraper, extractor, or frontend behavior. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/test/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Test

Hermes adapter for upstream Soria-stack skill `test`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-test`
- Upstream source: `plugins/soria-stack/skills/test/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Test

Hermes adaptation of `Soria-Inc/soria-stack` `/soria-test`.

Read `../../references/hermes-adapter.md`, then read the target repo's
`AGENTS.md` and `CLAUDE.md` when present.

Testing means choosing evidence, not blindly running pytest. Classify the
change and pick the needed proof layer:

1. Unit proof
2. Local integration proof
3. Boundary proof
4. Runtime proof
5. Pipeline E2E proof
6. Preview/staging/prod proof when configured

Use repo scripts such as `scripts/create-test-db.sh` and
`scripts/run-tests.sh`. For TP/search/chunk runtime proof, use the app repo
helper `scripts/seed-dev-tp.py` before claiming the dev namespace has real
chunks.
