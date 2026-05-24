---
name: soria-promote
description: 'Soria Stack Hermes skill for promote. Safe path to production in Hermes. Use when the user wants to land Soria work through git + CI, after `warehouse_diff`, `warehouse_promote` posts the PR manifest, verification passes, and dashboard QA is clean for customer-facing dive changes. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/promote/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Promote

Hermes adapter for upstream Soria-stack skill `promote`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-promote`
- Upstream source: `plugins/soria-stack/skills/promote/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Promote

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-promote` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- pre-flight: clean git tree, recent `/soria-verify` artifact, recent
  `/soria-dashboard-review` artifact, `dbt test` passes, methodology + verify
  coverage present
- `warehouse_diff` to surface bronze file-level changes vs prod
- `git push`, `gh pr create`, then `warehouse_promote(pr=N)` to
  post the `<!-- soria-promotion-manifest -->` comment that CI reads
- CI executes on merge: `.github/workflows/dbt-deploy.yml` materializes
  marts into `soria_duckdb_main`; `.github/workflows/promote.yml` copies
  bronze `_file_id` rows from staging to prod
- final browser QA via `dashboard-review` against
  `https://soriaanalytics.com` after merge

## Notes

- Rollback is `git revert` the PR (for marts/bronze) or `database_mutate`
  flipping `deleted_at` (for Postgres state). No force-push.
- Follow the repo's `AGENTS.md` landing rules if you are actually committing.
- Use `ticket` instead of burying open concerns in the promotion flow.
