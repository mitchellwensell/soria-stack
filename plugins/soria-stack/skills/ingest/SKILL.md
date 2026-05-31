---
name: ingest
description: Build and run Soria ingestion pipelines in Codex. Use for scraping, grouping, schema work, parse/detection, new agent extraction, SimpleExtractor Excel/CSV extraction, validation/spot checks, schema/value-mapping handoff, refresh runs, and publishing bronze — all through `mcp__soria__*` tools.
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: ingest/SKILL.md
  variant: codex
---

# Ingest

Codex adaptation of the `Soria-Inc/soria-stack` `/ingest` skill.

Read [../../references/codex-adapter.md](../../references/codex-adapter.md)
before acting.

## Focus

- scraper -> groups/schema -> parse/detect -> extract/map -> publish (bronze)
- exact MCP tools:
  `mcp__soria__scraper_manage / scraper_run`,
  `mcp__soria__group_manage`,
  `mcp__soria__schema_manage / schema_mappings`,
  `mcp__soria__parse_pdf / parse_pdfs_bulk`,
  `mcp__soria__detection_run`,
  `mcp__soria__agent_extract / agent_status`,
  `mcp__soria__extraction_run / extractor_manage` for SimpleExtractor groups,
  `mcp__soria__validation_run` only for legacy/force re-validation,
  `mcp__soria__warehouse_manage(group_id=..., publish=True)`
- new PDF/table work should prefer `agent_extract` over the older PDF
  `extraction_run` path; parse PDFs to markdown first
- `test=True` on `scraper_run` and SimpleExtractor `extraction_run` to dry-run
  inline code before saving it to shared state
- human review gates at each major step
- browser inspection only when it materially helps the scrape or extract path

## Notes

- Writes are soft-delete reversible via `deleted_at` + the `PipelineEvent`
  audit trail. Check `mcp__soria__pipeline_activity` before starting so you
  don't race a concurrent run.
- Bronze lands at `soria_duckdb_staging.bronze.{table}`. Prod promotion is
  PR-gated; do not call `warehouse_promote` from here (that's `/promote`).
- Use `/scraper` when source discovery/code is the hard part. Use `/map` for
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
  `mcp__soria__value_manage(schema_mapping_id=..., index=True)`.
- Use `auto_map=True` only for obvious formatting variants; use `/map` for
  business meaning, company names, plan types, aggregate rows, historical names,
  or ambiguous canonicals.
- Bronze keeps raw values; mappings are published alongside bronze and applied
  downstream. Never edit extracted CSVs or warehouse rows to normalize values.
