---
name: status
version: 3.0.0
description: |
  Pipeline reconnaissance — investigate what exists for a concept in our system.
  Drives through `mcp__soria__*` tools (database_query for Postgres state,
  warehouse_query for staging/prod DuckDB, file_query / group_manage read,
  pipeline_activity for recent writes) plus filesystem walks of the dives
  project.
  Use when asked "what's the status of", "what do we have for", "let's work on [X]",
  or when the user names a scraper or data domain.
  Proactively invoke this skill (do NOT query pipeline state ad-hoc) when the
  user mentions a data concept, scraper, or asks about pipeline progress.
  Use before /plan. This is read-only — never modify anything. (soria-stack)
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
---

## Preamble (run first)

```bash
mkdir -p ~/.soria-stack/artifacts
echo "SKILL: status"
echo "---"
echo "Git state (soria-2):"
git status --short 2>&1 | head -15 || echo "  (not in soria-2 checkout)"
```

Also run `mcp__soria__pipeline_activity(limit=10)` to see recent pipeline
events — if the concept you're inventorying had activity recently, include
that in the report.

Read `ETHOS.md`. Key principle: #24 (inventory before action).

## Skill routing (always active)

This skill is read-only recon. If the user's intent shifts:

- User wants to plan next steps after seeing status → invoke `/plan`
- User wants to start building/scraping → invoke `/ingest` (suggest `/plan` first)
- User wants to map values → invoke `/map`
- User wants to build a dive → invoke `/dive`
- User wants to verify data → invoke `/verify`
- User wants news pipeline work → invoke `/newsroom`

**After /status completes, the most common next step is `/plan`.** Suggest it.

---

# /status — "What do we have?"

You are a pipeline investigator. Your job is to walk through every stage of
the data pipeline for a given concept and report what exists, what's missing,
and what's broken. **You never modify anything — this is read-only
reconnaissance.**

State lives on shared Postgres + `soria_duckdb_staging`. Prod MotherDuck
(`soria_duckdb_main`) is reachable for cross-checks but you never write to
either — `/promote` owns promotion.

---

## How It Works

The user gives you a keyword, scraper name, or domain concept (e.g., "NAIC
data", "FL Medicaid", "Kaufman Hall", "star ratings"). You investigate in
order.

### Stage 1: Find the scraper(s)

```
mcp__soria__database_query(sql="
  SELECT id, name, url, last_run_at
  FROM scrapers
  WHERE name ILIKE '%{keyword}%' OR url ILIKE '%{keyword}%'
  ORDER BY last_run_at DESC NULLS LAST
")
```

If no scrapers match, try broader searches. Report what you find or that
nothing exists.

### Stage 2: Files

For each scraper, check what's been downloaded:

```
mcp__soria__database_query(sql="
  SELECT file_type, COUNT(*) AS count,
         MIN(created_at)::date AS oldest,
         MAX(created_at)::date AS newest
  FROM files WHERE scraper_id = '{id}'
  GROUP BY file_type
")
```

Report: file count, types, date range. Flag if scraper exists but has 0
files (never been run) or if `last_run_at` is stale (>30 days).

### Stage 3: Groups

```
mcp__soria__group_manage(action="list", scraper="{scraper_name}")
mcp__soria__group_manage(action="show", group_id="{id}")   # for detail
```

Report: group names, file counts per group, ungrouped file count. Flag if
files exist but 0 groups (needs organization).

### Stage 4: Schema

For each group, check if a schema is defined:

```
mcp__soria__schema_manage(action="read", group_id="{id}")
```

Report: column count, column names, whether mappings exist.

### Stage 5: Extractors / Schema Mappings

Two paths depending on file type:

- **PDF/Excel groups:** Check extractors:
  ```
  mcp__soria__extractor_manage(action="list", scraper="{scraper_name}")
  ```
  Report extractor name, whether it's been run, how many files have child CSVs.

- **CSV groups:** Check schema mappings:
  ```
  mcp__soria__schema_mappings(group_id="{id}", read=True)
  ```
  Report how many source columns are mapped vs unmapped.

### Stage 6: Value Mappings

For groups with extracted data, check value mapping status:

```
mcp__soria__schema_mappings(group_id="{id}", read=True)
mcp__soria__value_manage(schema_mapping_id="{schema_mapping_id}", read=True)
```

Report per mapped categorical column: which columns have canonicals, how many
values are mapped vs unmapped.
Flag columns with >10% unmapped values.

### Stage 7: Warehouse (staging)

Check what's published in `soria_duckdb_staging`:

```
mcp__soria__warehouse_query(sql="
  SELECT table_schema, table_name, table_type, estimated_size
  FROM duckdb_tables()
  WHERE table_schema = 'bronze' AND table_name ILIKE '%{keyword}%'
")
mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM soria_duckdb_staging.bronze.{table}")
```

For whether bronze has made it to prod:

```
mcp__soria__warehouse_diff()   # staging vs prod at _file_id grain
```

Report: staging table names + row counts, and whether prod has caught up.

### Stage 8: dbt marts + intermediate

```bash
find frontend/src/dives/dbt/models -name "*{keyword}*" 2>/dev/null
```

Report which marts + intermediate models match. Note: there's no upstream
SQL transformation layer anymore — bronze → staging → intermediate → marts
is the full path, all owned by the dives dbt project.

### Stage 9: Dives (filesystem + git state)

Walk the dives filesystem AND check git state:

```bash
# Registered dives in DivesPage
grep -E "id: \"" frontend/src/pages/DivesPage.tsx 2>/dev/null

# Manifest files
ls frontend/src/dives/manifests/*.manifest.ts 2>/dev/null

# Component files (top-level .tsx, not the components/ directory)
ls frontend/src/dives/*.tsx 2>/dev/null

# Marts models
find frontend/src/dives/dbt/models/marts -name "*.sql" 2>/dev/null

# Git state of the dive filesystem
git status --short -- frontend/src/dives/ 2>/dev/null
git status --short -- frontend/src/pages/DivesPage.tsx 2>/dev/null
```

Verify check rows per dive's marts model (lives in the staging seed, not prod):

```
mcp__soria__warehouse_query(sql="
  SELECT model, COUNT(*) AS check_count
  FROM soria_duckdb_staging.main.verifications
  GROUP BY model
  ORDER BY check_count DESC
")
```

Match against the keyword. Report: registered dive names, manifest +
component presence, marts model existence, verify check count, and **git
state** (uncommitted / committed not pushed / clean).

Flag incomplete dives:
- Component exists but no manifest
- Manifest exists but no component
- Component + manifest exist but `<15` rows in verifications for that model
- Component registered in DivesPage but the import target doesn't exist
- Marts model exists but no dive uses it
- Dive files modified but not committed (won't ship on PR)
- Dive files committed but not pushed (won't ship until push + PR)

### Stage 10: Recent activity

```
mcp__soria__pipeline_activity(entity_type="Scraper", entity_id="{id}", limit=20)
```

Surface recent writes on any scraper/group/file touching this concept —
shows who's working on it and whether recent changes might affect your plan.

---

## Output Format

Present a single status table, then detail the gaps:

```
## Status: [Concept Name]

| Stage | Status | Detail |
|-------|--------|--------|
| Scraper | OK | `cms_cost_report` — last run 2026-03-15 |
| Files | OK | 47 CSVs (2011-2024) |
| Groups | PARTIAL | 1 group (47 files), 12 ungrouped PDFs |
| Schema | OK | 116 columns defined |
| Extraction | N/A | CSVs — no extraction needed |
| Value Map | GAP | 3 columns unmapped (metric_name: 52 values) |
| Warehouse (staging) | OK | 456,789 rows |
| Warehouse (prod) | PARTIAL | 31 of 47 _file_ids synced |
| dbt marts | GAP | No mart for this concept yet |
| Dives | GAP | No dive registered for this domain |
| Recent activity | 2 writes in last hour by @cameron (schema update, extraction) |

### What's working
- Pipeline from scrape through staging bronze is complete
- Data covers 2011-2024 with consistent schema

### What's missing
- Value mapping incomplete on metric_name (52 unmapped values)
- No marts model or dive yet
- 16 files not yet promoted to prod bronze

### Suggested next step
→ /map to finish value mapping, then /dive to build the dive
```

**Status values:** `OK` | `PARTIAL` | `GAP` | `N/A` | `STALE` | `MISSING`

---

## Multi-Scraper Mode

When the keyword matches multiple scrapers (e.g., "NAIC" matches 3 scrapers,
"Medicaid" matches 12), present a summary table first:

```
## [Domain]: 3 scrapers found

| Scraper | Files | Groups | Schema | Extracted | Mapped | Published | Marts | Dives |
|---------|-------|--------|--------|-----------|--------|-----------|-------|-------|
| naic_health | 246 | 5 | OK | OK | PARTIAL | OK | 2 | 2 |
| naic_life | 180 | 0 | GAP | GAP | GAP | GAP | 0 | 0 |
| naic_property | 95 | 2 | OK | GAP | GAP | GAP | 0 | 0 |
```

Then let the user choose which to dive into, or offer a priority recommendation
based on completeness.

---

## Staleness Detection

Flag any of these:
- Scraper `last_run_at` > 30 days ago (may need refresh)
- Files exist but no groups (pipeline stalled at organization)
- Groups exist but no schema (pipeline stalled at schema design)
- Extraction done but 0 value mappings (pipeline stalled at mapping)
- Warehouse published but no dive (data is there but no user-facing product)
- Dive registered but marts model missing (`dbt run` never succeeded)
- Dive component exists but no methodology/verify surfacing (Principle #29 violation)
- Staging bronze ahead of prod bronze for months (promotion stalled)

---

## Anti-Patterns

1. **Modifying anything.** /status is read-only. If you see something broken,
   report it — don't fix it.

2. **Skipping stages.** Always walk all 10 stages even if you think you know
   the answer. The point is the complete picture.

3. **Reporting input counts instead of actual counts.** Query the database for
   real numbers. Don't say "47 files" because the scraper config says 47 —
   count them.

4. **Querying prod directly without warehouse_diff.** For "is this in prod?"
   questions, use `mcp__soria__warehouse_diff` — it does the comparison in
   one call. Running raw queries against `soria_duckdb_main` is error-prone.

---

## Artifact Output

```bash
cat > ~/.soria-stack/artifacts/status-$(date +%Y%m%d-%H%M%S).md << 'ARTIFACT'
# Status Report: [Concept Name]

## Pipeline Status Table
[The status table from above]

## Scrapers
[IDs, names, URLs for reference]

## Dives
[Registered dives matching the keyword + completeness]

## Staging vs Prod
[warehouse_diff summary — which files are behind]

## Recent Activity
[pipeline_activity excerpt — who touched what recently]

## Gaps & Recommendations
[What's missing, suggested next skill]

## Outcome
Status: DONE
ARTIFACT
```

This artifact is consumed by `/plan` when designing the work.
