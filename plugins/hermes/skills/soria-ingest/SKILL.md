---
name: soria-ingest
description: 'Soria Stack Hermes skill for ingest. Build and run Soria ingestion pipelines in Hermes. Use for scraping, grouping, schema work, parse/detection, new agent extraction, SimpleExtractor Excel/CSV extraction, validation/spot checks, schema/value-mapping handoff, refresh runs, and publishing bronze — all through `Soria MCP tools`. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/ingest/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Ingest

Hermes adapter for upstream Soria-stack skill `ingest`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-ingest`
- Upstream source: `plugins/soria-stack/skills/ingest/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Ingest

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-ingest` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- scraper -> groups/schema -> parse/detect -> extract/map -> publish (bronze)
- exact MCP tools:
  `scraper_manage / scraper_run`,
  `group_manage`,
  `schema_manage / schema_mappings`,
  `parse_pdf / parse_pdfs_bulk`,
  `detection_run`,
  `agent_extract / agent_status`,
  `extraction_run / extractor_manage` for SimpleExtractor groups,
  `validation_run` only for legacy/force re-validation,
  `warehouse_manage(action="publish")`
- new PDF/table work should prefer `agent_extract` over the older PDF
  `extraction_run` path; parse PDFs to markdown first
- `test=True` on `scraper_run` and SimpleExtractor `extraction_run` to dry-run
  inline code before saving it to shared state
- human review gates at each major step
- browser inspection only when it materially helps the scrape or extract path

## Notes

- Writes are soft-delete reversible via `deleted_at` + the `PipelineEvent`
  audit trail. Check `pipeline_activity` before starting so you
  don't race a concurrent run.
- Bronze lands at `soria_duckdb_staging.bronze.{table}`. Prod promotion is
  PR-gated; do not call `warehouse_promote` from here (that's `/soria-promote`).
- Use `/soria-scraper` when source discovery/code is the hard part. Use `/soria-map` for
  non-trivial value canonicalization.
