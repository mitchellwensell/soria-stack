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
  `mcp__soria__warehouse_manage(action="publish")`
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
