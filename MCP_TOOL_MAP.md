# MCP Tool Map

Every `mcp__soria__*` tool the skills call, grouped by domain. This is the
only place the tool surface is documented — individual skills reference
tools by name and this file is the authority on what each one does.

All writes are soft-delete reversible unless noted. The full flag is always
required to restore a soft-deleted row (`mcp__soria__database_mutate` sets
`deleted_at = NULL`, respecting `SOFT_DELETE_CASCADES`).

## Scrapers & files

| Tool | Read/Write | Purpose |
|---|---|---|
| `scraper_manage` | RW | CRUD scraper code + metadata. |
| `scraper_run` | W | Download files. `test=True` first to dry-run. |
| `scraper_upload_urls` | W | Generate presigned GCS URLs for manual uploads. |
| `scraper_confirm_uploads` | W | Confirm uploads and trigger the pipeline. |
| `file_query` | R | List/inspect files, refresh CSV headers. |
| `files_reprocess` | W | Re-run post-download processing (e.g., Excel sheet split). |

## Groups, schemas, detection

| Tool | Read/Write | Purpose |
|---|---|---|
| `group_manage` | RW | CRUD groups. Soft-delete cascades to extractors/schemas/prompts. |
| `schema_manage` | RW | CRUD schema columns for a group (PDF extraction). |
| `schema_mappings` | RW | Map CSV headers to canonical columns. |
| `detection_run` | W | Gemini detects which pages match the schema (PDF). |
| `parse_pdf` / `parse_pdfs_bulk` | W | Parse PDFs into markdown child files and chunks. Required before new `agent_extract` PDF/table extraction. |

## Extraction & validation

| Tool | Read/Write | Purpose |
|---|---|---|
| `extractor_manage` | RW | CRUD Python extractors for Excel/CSV. |
| `agent_extract` | W | New markdown-page extraction path for PDF/table data. Returns a workflow ID; poll with `agent_status`. |
| `agent_status` / `agent_review` | R/W | Check or respond to long-running agent workflows such as `agent_extract` and `agent_map`. |
| `extraction_run` | W | Run SimpleExtractor for Excel/CSV, or legacy Gemini PDF extraction during migration. `test=True` dry-runs SimpleExtractor. |
| `validation_run` | W | Legacy validation workflow for extracted CSVs against source PDFs. Agent extraction validates page CSVs inline; do not double-run by default. |
| `prompt_manage` | RW | CRUD detection/extraction LLM prompts per group. |

## Value mapping

| Tool | Read/Write | Purpose |
|---|---|---|
| `value_manage` | RW | Index raw values + map to canonical. Map/unmap/rename/soft-delete. |
| `derived_column_manage` | RW | CRUD derived columns (computed from other columns). |

## Warehouse

| Tool | Read/Write | Purpose |
|---|---|---|
| `warehouse_manage` | W | Publish a group's CSVs → `soria_duckdb_staging` bronze. Unpublish = soft-delete. |
| `warehouse_query` | R | `SELECT` against `soria_duckdb_staging` (SELECT only, 1000 rows max). |
| `warehouse_diff` | R | Compare staging vs prod bronze at `_file_id` grain. |
| `warehouse_promote` | W | Build the PR manifest comment (`<!-- soria-promotion-manifest -->`) that CI reads on merge. |

## Postgres state

| Tool | Read/Write | Purpose |
|---|---|---|
| `database_query` | R | `SELECT` against Postgres (pipeline state). |
| `database_mutate` | W | `INSERT/UPDATE/DELETE` raw SQL. **Never** use on pipeline tables — use the domain tool instead. Use for soft-delete restores (`SET deleted_at = NULL`). |

## SQL models & dashboards

| Tool | Read/Write | Purpose |
|---|---|---|
| `sql_model_list` / `get` / `save` / `delete` | RW | Manage stored SQL model code (legacy dashboards — **not** dives). |
| `list_dashboard_pages` / `get_dashboard_page` / `get_dashboard_data` | R | Read legacy Perses dashboards. |
| `dashboard_manage` | W | Update Perses dashboard panels/variables/layout. |

## Pipeline activity & search

| Tool | Read/Write | Purpose |
|---|---|---|
| `pipeline_activity` / `pipeline_history` / `pipeline_cascade` | R | Audit trail — who changed what when. Read `PipelineEvent` rows. |
| `search` / `chunk_search` | R | Full-text + vector search over files/chunks. |
| `github_prs` | R | List/inspect PRs for promotion context. |
| `tag_manage` | RW | CRUD tags on entities. |

## News

| Tool | Read/Write | Purpose |
|---|---|---|
| `news_pipeline` | W | Run fetch → extract → cluster → summarize. |
| `news_branches` | RW | CRUD news config branches. |
| `news_articles` / `news_events` | R | List/search. |

## Dead verbs (old `soria` CLI)

These no longer exist. Use the MCP equivalent or a local command.

| Old CLI | Replacement |
|---|---|
| `soria scraper run/test` | `mcp__soria__scraper_run` (`test=True` for dry-run) |
| `soria detect / extract / validate` | `mcp__soria__detection_run` / `parse_pdf` or `parse_pdfs_bulk` / `agent_extract` for new PDF extraction, `extraction_run` for SimpleExtractor or legacy PDF, `validation_run` for legacy/force validation |
| `soria warehouse query/publish/status` | `mcp__soria__warehouse_query` / `warehouse_manage(action="publish")` |
| `soria schema read/update/mappings` | `mcp__soria__schema_manage` / `schema_mappings` |
| `soria value index/map` | `mcp__soria__value_manage` |
| `soria db query/schema` | `mcp__soria__database_query` |
| `soria model list/get` | `mcp__soria__sql_model_list` / `sql_model_get` (legacy only) |
| `soria file show/list/open` | `mcp__soria__file_query` |
| `soria group list/show/create` | `mcp__soria__group_manage` |
| `soria env branch/checkout/status/diff/teardown/restore` | **Removed.** No isolated envs. `git checkout` + `make dev-https` is the local flow. |
| `soria revert` | **Removed.** Undo by flipping `deleted_at` via `mcp__soria__database_mutate` (for state) or `git revert` the PR (for promoted warehouse changes). |
| `soria auth login` | **Removed.** Auth is via Clerk in the browser when you visit `https://dev.soriaanalytics.com`. |
