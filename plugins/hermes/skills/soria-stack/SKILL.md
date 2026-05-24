---
name: soria-stack
description: 'Soria Stack Hermes skill for soria-stack. Use when the task follows the Soria workflow from the `Soria-Inc/soria-stack` repo: MCP pipeline work, dive work, branch dev env setup, testing, code review, E2E proof, diagnosis, or promotion. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/soria-stack/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Stack

Hermes adapter for upstream Soria-stack skill `soria-stack`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-stack`
- Upstream source: `plugins/soria-stack/skills/soria-stack/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Soria Stack

Hermes adaptation of the `Soria-Inc/soria-stack` workflow. Pipeline/product work
is MCP-first in Hermes. Branch-local engineering dev environments follow the app
repo's documented `soria env` and Makefile flow when present.

## When to use this skill

- User wants to inventory what data / pipeline state exists for a concept
- User wants a plan before changing ingestion, mappings, or dives
- User is building or fixing a dive, verify flow, or promotion flow
- User is setting up a Soria app dev environment, testing a change, or reviewing a Soria code diff
- User wants the Soria-stack workflow specifically, but inside Hermes

## When not to use it

- If the task is generic repo coding with no Soria workflow implications
- If the task is pure browser QA, jump straight to `browse`

## Session start

Run these before making assumptions:

```bash
git status --short
```

Probe the Soria MCP (once per session):

```
database_query(sql="SELECT 1 AS ok")
```

If the probe fails, the user must configure the Soria MCP in their Hermes
client (HTTP endpoint at `https://<your-dbos>.cloud.dbos.dev/mcp/`) and
restart. There is no fallback — every pipeline skill depends on it.

For dive work, the default local flow is `make dev-https` from the soria-2
repo root (vite at `https://dev.soriaanalytics.com` against prod DBOS).

## Core workflow

1. Inventory before action.
   Use `database_query` (Postgres state),
   `warehouse_query` (staging warehouse),
   `pipeline_activity` (recent writes), and filesystem walks
   under `frontend/src/dives/` to understand what already exists.
2. Plan before building when the scope is not obvious.
   Be explicit about the target output: pipeline change, bronze table,
   dive, verify pass, or promotion.
3. Use MCP tools, not ad-hoc workarounds. The main surfaces are:
   - `scraper_manage / scraper_run / scraper_upload_urls / scraper_confirm_uploads`
   - `group_manage`, `schema_manage`, `schema_mappings`
   - `detection_run`, `extraction_run`, `validation_run`
   - `value_manage`, `derived_column_manage`
   - `warehouse_query`, `warehouse_manage`, `warehouse_diff`, `warehouse_promote`
   - `database_query`, `database_mutate`, `file_query`, `files_reprocess`
   - `news_*`, `prompt_manage`, `pipeline_activity/history/cascade`
4. Verify with evidence.
   Show actual rows, counts, traces, or file state before claiming success.
5. Reversibility, not isolation. Writes hit shared state but soft-delete
   + the `PipelineEvent` audit trail make every write reversible.

## Dive work

For dive implementation, stick to the repo's file-based flow:

- dbt models under `frontend/src/dives/dbt/models/...`
  (staging / intermediate / marts — materialized as `main_staging`,
   `main_intermediate`, `main_marts` in MotherDuck)
- manifests under `frontend/src/dives/manifests/...`
- React components under `frontend/src/dives/...`
- registration in `frontend/src/pages/DivesPage.tsx`
- verify rows in `frontend/src/dives/dbt/seeds/verifications.csv`

Local `dbt run` writes to `soria_duckdb_staging`. Prod materialization
happens in CI on PR merge.

When the user wants UI proof, invoke `browse` instead of defaulting to the
slower Chrome-first browser tools.

## Guardrails

- No force-push. Rollback is `git revert` the PR (for warehouse / React) or
  `database_mutate` flipping `deleted_at` (for Postgres state).
- Promotion is PR + CI, never a command. `warehouse_promote(pr=N)`
  posts the file-level manifest; CI executes on merge.
- Respect this repo's `AGENTS.md` completion rules if you end up committing:
  tests or validation, `git pull --rebase`, `git push`.
- Treat `direnv` and repo-local `.env` loading as the source of truth; do not
  tell the user to `source .env`.

## Routing hints

- Preflight: `/soria-env` (MCP probe + dev-https cert + recent activity)
- Inventory and recon: `/soria-status`
- Planning: `/soria-plan`
- Ingestion path: `/soria-ingest` (scrape → detect/extract/validate → mappings → publish)
- Value mapping: `/soria-map` (or `/soria-parent-map` for company rollup)
- Dive path: `/soria-dive` (dbt + manifest + TSX + verifications + methodology)
- In-chat dive inspection: `/soria-preview`
- Verification: `/soria-verify`
- Diagnosis: `/soria-diagnose`
- Ticketing: `/soria-ticket`
- Browser QA: `/soria-browse` or `/soria-dashboard-review`
- Promotion: `/soria-promote`
- Engineering dev env: `/soria-dev-env`
- Engineering tests and E2E proof: `/soria-test`
- Soria code review: `/soria-code-review`
- Retrospective: `/soria-lessons`

If a live page, screenshot, auth import, or UI repro is involved, switch to
`browse`.
