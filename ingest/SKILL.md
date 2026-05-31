---
name: ingest
version: 6.0.0
description: |
  Build and run Soria ingestion pipelines through MCP: scrape, group, define
  schema, detect pages, extract with the new agent extraction path, validate,
  map headers/values, and publish bronze. Use when asked to "ingest this",
  "build the pipeline", "extract this data", "run the scraper", "load this
  into the warehouse", refresh an existing source, or diagnose what step is
  next in ingestion. Proactively invoke this skill for data-pipeline work;
  do not scrape, extract, map, or publish ad hoc. New PDF/table work should
  prefer agent extraction (`agent_extract`) over the older `extraction_run`
  Gemini workflow. SimpleExtractor is still used for structured Excel/CSV
  reshaping. Value-mapping decisions hand off to /map when they are substantial.
  (soria-stack)
benefits-from: [plan, scraper, status, verify]
allowed-tools:
  - Read
  - Bash
  - Write
  - AskUserQuestion
---

## Preamble

```bash
mkdir -p ~/.soria-stack/artifacts
echo "SKILL: ingest"
echo "---"
echo "Recent ingest/plan artifacts:"
ls -t ~/.soria-stack/artifacts/ingest-*.md ~/.soria-stack/artifacts/plan-*.md 2>/dev/null | head -5 || true
```

Also run `mcp__soria__pipeline_activity(limit=10)` before writes. Ingestion
writes shared Postgres and `soria_duckdb_staging`; recent activity tells you
who else touched scrapers, groups, files, schemas, prompts, values, or publish
records.

Read `ETHOS.md`, especially: inspect before creating, test on three files
before all files, extract wide and transform in SQL, never edit extracted CSVs,
and show evidence before saying data is correct.

If a `/plan` artifact exists, read it. If not, warn that no plan was found and
state the assumptions you will use.

## Scope

This skill owns E, T, and L in ETVLR:

- Extract: source discovery and file download.
- Transform: groups, schema, detection, extraction, validation, schema mapping.
- Load: publish to bronze in staging.

Use `/map` for non-trivial value normalization, `/dive` for dbt/React
representation, `/verify` for deeper proof, and `/promote` for prod.

Use `/scraper` when the hard part is writing or repairing scraper code. Return
to `/ingest` after files are landing.

## Current System Truths

- Pipeline operations go through `mcp__soria__*`. There is no `soria` CLI.
- Scrapers are `SimpleScraper` classes. In the app repo, `scrapers/{name}.py`
  is the durable code artifact; the runtime loads active code from Postgres.
  Use `scraper_run(test=True, code=..., url=...)` to dry-run before saving or
  landing code.
- Groups are the processing anchor. Schema columns, extractors, prompts,
  schema mappings, value mappings, files, and warehouse tables all hang off a
  `group_id`.
- New PDF/table extraction should use `agent_extract` after `parse_pdf` /
  `parse_pdfs_bulk` has produced markdown child files. The older
  `extraction_run` PDF path still exists during migration; do not choose it for
  new work unless `agent_extract` is unavailable or a legacy group already
  depends on it.
- `extraction_run` remains the route for SimpleExtractor-based Excel/CSV
  transformations and for legacy pipelines.
- SimpleExtractor is for deterministic Excel/CSV reshaping, header cleanup,
  sheet/row selection, and light pivots. It should not contain business
  normalization that belongs in schema mapping, value mapping, or dbt.
- Schema mapping maps headers to canonical columns. Value mapping maps cell
  contents to canonical values. Do not confuse them.
- Publish is the only path into bronze. Never hand-insert warehouse rows.

## Pipeline Choice

Choose the simplest valid path after inspecting files:

| Source shape | Path |
|---|---|
| Clean CSV with stable headers | group -> `schema_manage` -> `schema_mappings` -> publish |
| CSV/Excel needing row/header reshaping | group -> `extractor_manage` SimpleExtractor -> `extraction_run(test=True)` -> full `extraction_run` -> mappings -> publish |
| PDF with data tables | parent group for source PDFs -> child group if detection needs a narrower table set -> schema -> `detection_run` if needed -> `parse_pdf` / `parse_pdfs_bulk` on PDFs to create markdown pages -> `agent_extract` -> spot-check / map -> publish |
| Mixed sources or format eras | split by group or child group only when the schema/grain truly differs |

Default to extracting wide. Unpivot wide metric columns in dbt staging unless
the source is already long.

## Gate 0: Inventory And Samples

Never create groups, schema, scraper code, or extractors before looking.

1. Find existing state:
   - `mcp__soria__database_query` for candidate scrapers/groups/files.
   - `mcp__soria__file_query` for existing files and file details.
   - `mcp__soria__warehouse_manage(status=True, group_id=...)` for published groups.
2. Inspect representative source files:
   - oldest, newest, and one mid-history file.
   - include every suspected format era.
   - for CSV/Excel, use `file_query(..., detailed=True, rows=":10,-10:")`.
   - for PDFs, inspect pages/tables and determine whether detection needs child groups.
3. State:
   - file count, date range, file types.
   - likely logical groups and grain.
   - extraction path choice and why.

Stop if the group/schema design is ambiguous. Schema design is a conversation.

## Gate 1: Scrape

Goal: source files land with correct filenames, dates, URLs, hashes, and groups
can match them.

If the scraper already exists and files are current, do not rewrite it. Run a
refresh only when the source has new data.

If a scraper is needed:

1. Use `/scraper` to write or repair the `SimpleScraper`.
2. Dry-run with:
   - `mcp__soria__scraper_run(scraper_name="...", test=True, code=code, url=url)`
3. Save or land only after the dry-run returns correct files:
   - MCP session: `mcp__soria__scraper_manage(scraper_name="...", save={"code": code, "url": url})`
   - app repo session: edit `scrapers/{name}.py`, then follow repo tests and PR flow.
4. Run for real:
   - `mcp__soria__scraper_run(scraper_name="...", auto_pipeline=True)`
5. Verify with `file_query` and show:
   - count by file type.
   - date range.
   - sample filenames.
   - any skipped duplicates by `content_hash`.

Use manual upload only when the human asks or the source truly has no
scrapable URL. Manual upload is not a workaround for a fixable scraper.

Stop at the gate and present the inventory.

## Gate 2: Groups And Schema

Goal: each group represents one logical dataset with one canonical schema.

Groups:

- Top-level groups belong to a scraper; child groups narrow a parent.
- File assignment is regex over filename. Parent patterns should be broad;
  child patterns should be narrow.
- PDF detection into child groups keeps original PDFs in the parent and writes
  detected/parsed child files to the child group.
- Do not create separate groups just because column names drift. Use schema
  variants/mappings for that.

Create/read/update with:

```text
mcp__soria__group_manage(scraper_id="...", create=[{"name": "...", "pattern": "..."}])
mcp__soria__group_manage(group_id="...", create=[{"name": "...", "pattern": "..."}])
mcp__soria__group_manage(group_id="...", read=True)
```

Schema:

- Canonical columns are defined per group before extraction or publish.
- Use atomic columns. Exclude derivable totals/ratios unless the source value
  itself is analytically important.
- Include provenance/business dimensions needed downstream.
- Avoid premature reshaping. Wide source metrics can stay wide through bronze.

Manage schema with:

```text
mcp__soria__schema_manage(
  scraper_id="...",
  group_id="...",
  update_columns=[
    {"name": "state", "column_source": "header", "is_required": true},
    {"name": "enrollment", "column_source": "header"},
  ],
)
```

For CSV groups, run `schema_mappings(read=True)` after headers are known and
map raw source headers to canonical columns. For extraction groups, schema is
the target the agent/extractor must produce.

Stop and get approval on grain, group split, and schema.

## Gate 3: Detection, Parsing, And Agent Extraction

Goal: prove extraction on representative samples before scaling.

For new PDF/table work:

1. Ensure schema columns exist.
2. Run detection when source PDFs need page selection or child groups:
   - `mcp__soria__detection_run(group_id=child_group_id, file_ids=[...])`
3. Ensure markdown pages exist for table pages:
   - `mcp__soria__parse_pdf(file_id="...")` for one PDF.
   - `mcp__soria__parse_pdfs_bulk(file_ids=[...])` for many PDFs.
   - `mcp__soria__file_query(group_id="...")` to confirm markdown child files
     were created.
4. Run the new extraction path:
   - `mcp__soria__agent_extract(group_id=group_id, file_ids=[sample_pdf_ids], instructions="...")`
   - `file_ids` are the IDs of the PDFs whose markdown children are in this
     same group. If detection created child PDFs, use those detected child PDF
     IDs, not the original parent-group PDF IDs.
5. Poll with `mcp__soria__agent_status(workflow_id="...")` and inspect output
   CSVs through `file_query`.

Agent extraction behavior to rely on:

- It extracts from markdown pages with tables, not raw PDFs.
- It uses the group's canonical schema columns exactly.
- It stamps `_source_page` on rows for provenance.
- It saves prompt instructions for history.
- It skips fully extracted files unless specific page re-extraction is requested.
- It indexes values at the end so `/map` can work from observed values.
- It runs page-level markdown-to-CSV validation inline and stores validation
  metadata on the extracted CSV/markdown file metadata. This is distinct from
  the older `validation_run` workflow.

Do not use the older `extraction_run` PDF path for new work unless the new agent
path is missing or blocked. If you must use the old path, state why in the
artifact.

For SimpleExtractor Excel/CSV work:

1. Read existing extractor/schema:
   - `mcp__soria__extractor_manage(group_id="...", read=True)`
2. Inspect raw file structure with `file_query(..., detailed=True, rows=":10,-10:")`.
3. Write a `SimpleExtractor` using `extract(self, reader)`, not legacy
   `transform(self, df)`, unless updating old code.
4. Dry-run:
   - `mcp__soria__extraction_run(group_id="...", file_ids=[...], extractor_name="...", test=True)`
5. Save:
   - `mcp__soria__extractor_manage(group_id="...", save_name="...", save_code=code, save_is_default=True)`
6. Run:
   - `mcp__soria__extraction_run(group_id="...", file_ids=[...])`

SimpleExtractor guidelines:

- Use `reader.read(n_rows=...)` to find headers.
- Use `reader.iter(start_row=..., columns=...)` for chunks.
- Yield Polars DataFrames.
- Do not rename columns to canonical names solely to dodge schema mapping.
- Keep pivots mechanical. Business normalization belongs later.

Sample proof:

- Pick oldest, newest, and mid-history files.
- For each, compare at least 10 source values to extracted rows.
- Include source page/sheet/row and extracted row identifiers.
- If any mismatch appears, fix prompt/extractor/schema and repeat Gate 3.

Stop when the sample proof passes.

## Gate 4: Full Extraction, Validation, And Mapping Readiness

Goal: extract all files and surface every gap before publish.

Run the approved path over the full group:

- PDF agent path: `mcp__soria__agent_extract(group_id="...")`
- SimpleExtractor path: `mcp__soria__extraction_run(group_id="...")`
- CSV no-extraction path: go directly to schema mapping.

Then:

1. Inspect `file_query(group_id="...")` for source/extracted counts.
2. Validate according to path:
   - Agent path: do source spot checks plus inspect each page's
     `extraction_metadata` / `validation_metadata` via `file_query`; do not
     reflexively call legacy `validation_run`.
   - Legacy `extraction_run` PDF path: extraction already enqueues
     `validation_run`; use `mcp__soria__validation_run(group_id="...", force=True)`
     only for force re-validation.
   - SimpleExtractor / CSV path: use `validation_run` only when that group's
     source/CSV parent relationship is supported; otherwise use direct
     source-vs-output spot checks.
3. Check:
   - every expected source has a CSV or documented skip.
   - no unexpected 0-row files.
   - row counts by source are plausible.
   - headers are consistent enough for schema mapping.
   - `_source_page` exists for agent/PDF extractions.
4. Run `schema_mappings(read=True)` and close unmapped business headers. Treat
   `_source_page` as provenance from extraction; do not force it into the
   business schema unless the group intentionally stores page numbers in bronze.
5. If value normalization is meaningful, hand off to `/map` after indexing:
   - `mcp__soria__value_manage(schema_mapping_id="...", index=True)`
   - use `/map` for actual canonical decisions unless the mapping is trivial.

Stop and show summary stats before publishing.

## Gate 5: Publish Bronze

Goal: create or refresh the group's bronze table atomically.

Before publish:

- every raw header is schema-mapped.
- extraction/validation failures are resolved or explicitly excluded.
- value mapping state is either handled or documented as a follow-up.

Publish:

```text
mcp__soria__warehouse_manage(group_id="...", publish=True)
```

Use `force=True` only when intentionally rebuilding because schema, extraction,
or mapping changed:

```text
mcp__soria__warehouse_manage(group_id="...", publish=True, force=True)
```

Verify:

- `warehouse_manage(status=True, group_id="...")`
- `warehouse_query("SELECT COUNT(*) ...")`
- compare warehouse row count to extracted row count.
- run a sample query for latest and oldest periods.
- check NULLs on primary dimensions and obvious denominator fields.

Stop with the publish evidence and next steps.

## Refresh Mode

For an existing pipeline:

1. Inventory current scraper/group/table status.
2. Run `scraper_run(scraper_name="...", auto_pipeline=True)` only if new source
   files are expected.
3. Identify new file IDs via `file_query` or Postgres state.
4. Run extraction only for new files unless a schema/prompt/extractor changed.
5. Re-run schema mappings for new headers.
6. Index/map new values if needed.
7. Publish incrementally, or `force=True` if schema/mapping changed globally.
8. Verify new rows against source.

Flag anomalies: new columns, changed grain, large row-count deltas, source
format changes, or new values that break existing canonical mappings.

## Failure Rules

- If a scraper/extractor fails twice after targeted fixes, invoke `/diagnose`.
- If three extraction approaches fail, stop and escalate with evidence.
- Never retry a timed-out workflow blindly. Check status/logs/pipeline activity;
  duplicated runs can re-download or re-enqueue expensive work.
- Never patch outputs by SQL or CSV edits. Fix scraper, schema, prompt, or
  extractor and re-run.

## Artifact

Write an artifact at completion or handoff:

```bash
cat > ~/.soria-stack/artifacts/ingest-$(date +%Y%m%d-%H%M%S).md << 'ARTIFACT'
# Ingest Report: [Dataset]

## State
- Scraper: [name/id]
- Groups: [group ids and patterns]
- Path: [CSV mapping | SimpleExtractor | agent_extract | legacy extraction_run]
- Files: [count/type/date range]

## Schema
- Grain: [one row = ...]
- Canonical columns: [count + key columns]
- Exclusions: [derivable totals/ratios/etc.]

## Extraction Evidence
- Samples: [oldest/newest/mid]
- Spot check: [X/Y values matched]
- Failures/skips: [none or details]

## Mapping And Publish
- Schema mappings: [complete/incomplete]
- Value mapping: [not needed | handed to /map | completed]
- Bronze table: [schema.table]
- Rows: [extracted vs warehouse]

## Next Steps
- [ ] /map
- [ ] /verify
- [ ] /dive
- [ ] /promote

## Outcome
Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
Lesson: [specific reusable lesson]
ARTIFACT
```

## Anti-Patterns

- Starting with schema creation before inspecting source files.
- Using `extraction_run` old PDF extraction for a new agent-extraction group.
- Treating value mapping as header mapping.
- Splitting groups for cosmetic header drift.
- Running all files before the three-file sample proof.
- Stripping `_source_page`.
- Saving scraper/extractor code before a `test=True` dry-run.
- Using raw SQL writes on pipeline-owned tables when a domain MCP tool exists.
- Publishing after schema changes without an intentional `force=True`.
- Promoting from ingestion. Use `/promote`.
