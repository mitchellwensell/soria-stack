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
  `warehouse_manage(group_id=..., publish=True)`
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

## Routing Details

- Clean CSV: `schema_manage` -> `schema_mappings` -> publish. No LLM extraction.
- Dirty CSV / Excel: inspect with `file_query(detailed=True, rows=...)`, use
  `extractor_manage` + SimpleExtractor, dry-run with `extraction_run(test=True)`.
- PDF tables: parse to markdown with `parse_pdf` / `parse_pdfs_bulk`, then
  `agent_extract`; use `detection_run`/child groups only when narrowing pages or
  table sets is necessary.
- Existing legacy PDF group: continue `extraction_run` only for compatibility
  after checking prior files/history. Do not start new PDF work on legacy
  extraction.
- JSON/TXT/ZIP/manual uploads need explicit routing; do not force them into a
  tabular bronze pipeline without a real table grain.

## Value Mapping

- Header drift is `schema_mappings`; cell-value drift is `value_manage`.
- Index values after extraction/schema mapping with
  `value_manage(schema_mapping_id=..., index=True)`.
- Use `auto_map=True` only for obvious formatting variants; use `/soria-map` for
  business meaning, company names, plan types, aggregate rows, historical names,
  or ambiguous canonicals.
- Bronze keeps raw values; mappings are published alongside bronze and applied
  downstream. Never edit extracted CSVs or warehouse rows to normalize values.
