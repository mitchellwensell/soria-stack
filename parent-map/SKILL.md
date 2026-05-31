---
name: parent-map
version: 3.0.0
description: |
  Build and maintain the centralized parent company mapping table. Resolves
  company names and codes to their ultimate parent using parallel.ai enrichment,
  with ownership timelines, tickers, and network affiliations.
  One table, all data sources. Code-based joins, not name-based.
  Drives the Soria platform through `mcp__soria__*` tools and the
  `parallel.ai` API.
  Use when asked to "parent map", "who owns", "map these companies",
  "consolidate companies", "resolve parent", or when a new data source
  needs parent company rollup for dives.
  Use after /ingest (companies exist in warehouse), before /dive
  (dbt intermediate/marts need parent join). Parallel to /map (value mapping).
  (soria-stack)
benefits-from: [ingest, map, status]
allowed-tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - WebSearch
  - AskUserQuestion
---

## Preamble (run first)

```bash
mkdir -p ~/.soria-stack/artifacts
echo "SKILL: parent-map"
echo "---"
echo "Checking for prior artifacts..."
ls -t ~/.soria-stack/artifacts/ingest-*.md ~/.soria-stack/artifacts/parent-map-*.md 2>/dev/null | head -5
```

Read `ETHOS.md`. Key principles: #9 (historical names stay historical),
#10 (validate with eyes).

## Skill routing (always active)

- Need to scrape/extract source data first → invoke `/ingest`
- Need to normalize values (not parent companies) → invoke `/map`
- Parent mapping done, ready to build a dive → invoke `/dive`
- Parent mapping done, ready to verify → invoke `/verify`

---

# /parent-map — "Who owns this company?"

You are building the single source of truth for parent company assignments
across all data sources. Every dive that shows company-level data joins
to this table. Get it wrong and market share, concentration metrics, and
company trend lines are all broken.

**Where this state lives:**
- The `ref_company_parent_mapping` rows live in the `parent_mapping` scraper's
  bronze table — published via `mcp__soria__warehouse_manage(group_id="...", publish=True)`
  and promoted to prod through a PR (see `/promote`)
- dbt model changes that wire the join live as SQL files in
  `frontend/src/dives/dbt/models/intermediate/` or `models/staging/`

Commit the dbt SQL edits in git before `/promote`. The parent mapping rows
themselves travel with the PR via the `warehouse_promote` manifest.

---

## The Table

`ref_company_parent_mapping` is the centralized reference table. One table,
all data sources, code-based joins.

### Schema

```
input_name          -- Company name as it appears in source data
code                -- Numeric/string join key (group code, cocode, contract ID, CCN)
code_type           -- What the code is: naic_group, naic_cocode, ma_contract, cms_ccn, etc.
current_parent_name -- Raw parent from parallel.ai
canonical_parent    -- Cleaned display name for dives (value-mapped)
ticker              -- Stock ticker if public, NULL if private
affiliation         -- Network: BCBS, Delta Dental, Kaiser Permanente, or NULL
sources             -- Citation URLs from parallel.ai
ownership_timeline  -- JSON array of ownership changes with dates
source              -- Where mapping came from: parallel.ai, manual, naic_demographics
created_at          -- When mapping was created
```

### Key design decisions

- **`code + code_type` is the join key, NOT company name.** Names are fuzzy
  (punctuation, abbreviation, capitalization). Codes are exact.
- **`canonical_parent`** is the value-mapped clean name. One name per economic
  entity across all datasets and all time periods.
- **Independent companies** have `canonical_parent` = their own cleaned name.
- **Multiple `input_name` rows** can point to same `canonical_parent` (name
  variants, rebrands, subsidiaries).
- **Multiple `code_type` rows** for same company — NAIC group + MA contract +
  CCN all resolve to the same parent.

### Join pattern (any data source)

```sql
-- NAIC: two-stage join (group first, cocode fallback)
LEFT JOIN staging.stg_parent_mapping m_group
  ON d.group_code = m_group.code AND m_group.code_type = 'naic_group'
LEFT JOIN staging.stg_parent_mapping m_cocode
  ON d.cocode = m_cocode.code AND m_cocode.code_type = 'naic_cocode'
-- Result: COALESCE(m_group.canonical_parent, m_cocode.canonical_parent, d.company_name)

-- MA Enrollment: direct join on contract
LEFT JOIN staging.stg_parent_mapping m
  ON d.contract_number = m.code AND m.code_type = 'ma_contract'

-- SNF/HHA Cost Reports: join on CCN
LEFT JOIN staging.stg_parent_mapping m
  ON d.provider_ccn = m.code AND m.code_type = 'cms_ccn'

-- Generic: any dataset with a code
LEFT JOIN staging.stg_parent_mapping m
  ON d.{code_column} = m.code AND m.code_type = '{type}'
```

---

## Gate 1: Identify What Needs Mapping

Before running parallel.ai, figure out what's unmapped.

### The universal pattern

```
mcp__soria__warehouse_query(sql="
WITH src_entities AS (
  SELECT DISTINCT
    {code_column} AS code,
    '{code_type}' AS code_type,
    {name_column} AS entity_name
  FROM {source_table}
  WHERE {code_column} IS NOT NULL
)
SELECT
  COUNT(*) AS total,
  COUNT(CASE WHEN m.code IS NOT NULL THEN 1 END) AS matched,
  COUNT(CASE WHEN m.code IS NULL THEN 1 END) AS unmapped
FROM src_entities e
LEFT JOIN staging.stg_parent_mapping m
  ON e.code = m.code AND e.code_type = m.code_type
")
```

### Source-specific patterns

**NAIC** — two tiers of codes:
```sql
-- Grouped companies: one per group_code (preferred)
SELECT DISTINCT group_code AS code, 'naic_group' AS code_type, group_name
FROM staging.stg_naic_demographics
WHERE group_code IS NOT NULL AND group_code != '0'

-- Ungrouped: one per cocode (fallback)
SELECT DISTINCT cocode AS code, 'naic_cocode' AS code_type, full_company_name
FROM staging.stg_naic_demographics
WHERE group_code IS NULL OR group_code = '0'
```

**MA Enrollment** — one per contract:
```sql
SELECT DISTINCT contract_number AS code, 'ma_contract' AS code_type, parent_organization
FROM staging.stg_ma_monthly_enrollment_by_plan
```

**CMS Cost Reports** — one per CCN:
```sql
SELECT DISTINCT provider_ccn AS code, 'cms_ccn' AS code_type, facility_name
FROM staging.stg_snf_cost_reports
```

### ⛔ GATE: Match rate assessed

Report: total entities, already mapped, need mapping. If >90% already mapped,
this is an incremental update. If <50%, this is a full build.

---

## Gate 2: Run Parallel.ai Enrichment

Send unmapped entities to parallel.ai for parent company resolution.

### Output schema (what we ask for)

```json
{
  "current_parent_name": {
    "type": "string",
    "description": "Current ultimate parent company name as of 2025"
  },
  "ticker": {
    "type": ["string", "null"],
    "description": "Stock ticker if publicly traded, null if private"
  },
  "ownership_timeline": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "parent_name": {"type": "string"},
        "from_date": {"type": ["string", "null"], "description": "YYYY-MM-DD or YYYY"},
        "to_date": {"type": ["string", "null"], "description": "YYYY-MM-DD or YYYY, null if current"},
        "event": {"type": "string", "description": "founding, rename, acquisition, merger, spinoff, current, independent"}
      }
    }
  }
}
```

### Input format

Include context to help parallel.ai. Don't just send the name — add what you know:

```
Good:  "Anthem Inc - U.S. health insurance holding company, NAIC group 671. Rebranded to Elevance Health in 2022."
Good:  "H5216 - CMS Medicare Advantage contract operated by Humana Insurance Company in Kentucky."
Bad:   "Anthem Inc"
Bad:   "H5216"
```

Context fields that help: business type, state, regulatory ID, known affiliations.

### Batch execution

```python
# Create task group
group = client.beta.taskGroup.create({})

# Add runs in chunks of 100
for chunk in chunks(inputs, 100):
    client.beta.taskGroup.addRuns(group.taskgroup_id, {
        "default_task_spec": {"output_schema": schema},
        "inputs": [{"input": c, "processor": "base"} for c in chunk]
    })

# Poll for completion
while True:
    status = client.beta.taskGroup.retrieve(group.taskgroup_id)
    if not status.is_active:
        break
    sleep(30)

# Stream results
results = client.beta.taskGroup.getRuns(group.taskgroup_id,
    include_input=True, include_output=True)
```

### Expected results

- ~85-90% fully correct (major companies, public entities)
- ~10% partially correct (wrong parent level, verbose names)
- ~5% failures (blank/None for obscure private entities)

### ⛔ GATE: Results received

Report: total sent, success rate, sample of top 5 results for quick sanity check.

---

## Gate 3: Reconciliation

This is the manual work. Do it in Python, not SQL.

### Step 1: Collapse failures to self-named

Any result where `current_parent_name` is blank, None, "Unknown", "Not identified",
or verbose ("No ultimate parent company could be identified...") → set
`canonical_parent` to a cleaned version of the input company name. These are
independent/standalone entities.

### Step 2: Canonicalize parent names

Build a cleanup map for name variants:
```python
canonical = {
    'UnitedHealth Group Incorporated': 'UnitedHealth Group',
    'UnitedHealth Group, Inc.': 'UnitedHealth Group',
    'The Cigna Group (Cigna Corporation)': 'The Cigna Group',
    'Elevance Health, Inc.': 'Elevance Health',
    ...
}
```

Systematic cleanup rules:
- Strip suffixes: Inc., LLC, Corp., Corporation, Grp, L.P.
- Title-case ALL CAPS entries (except known acronyms: BCBS, CVS, HCSC)
- Remove parenthetical clarifications
- Remove d/b/a clauses

### Step 3: Check for near-duplicates

```python
for each canonical_parent:
    if ALL_CAPS and len > 4: flag
    if len > 40: flag (verbose parallel output not cleaned)
    if contains '(': flag (parenthetical)
    if starts with 'No ' or 'Not ': flag (failed lookup)
    if contains 'd/b/a': flag
```

### Step 4: Tag affiliations

BCBS, Delta Dental, and Kaiser Permanente are network affiliations — tag them:
```python
bcbs_keywords = ['blue cross', 'blue shield', 'bcbs', 'anthem', 'elevance',
                  'carefirst', 'premera', 'cambia', 'wellmark', 'highmark',
                  'capital blue', 'guidewell', 'florida blue']
delta_keywords = ['delta dental']
kaiser_keywords = ['kaiser']
```
Cross-reference against the official BCBS Association member list to verify.

### Step 5: Add historical name variants

Rebrands need rows for old names pointing to current canonical:
```
AETNA GRP → CVS Health
Anthem Inc Grp → Elevance Health
WELLCARE GRP → Centene
Spectrum Hlth GRP → Corewell Health
```

### Step 6: Add code-based join keys

Every row needs `code + code_type`. Extract from the original query that
identified what needed mapping. Verify 100% of rows have codes.

### ⛔ GATE: Reconciliation reviewed

Present: total entities, canonical parents created, affiliations tagged,
failures collapsed to self-named. Wait for human review of the canonical
parent list before uploading.

---

## Gate 4: Upload and Verify

1. Save as CSV with full schema.
2. Upload via the standard scraper flow:
   ```
   mcp__soria__scraper_upload_urls(scraper="parent_mapping", count=1)
   # upload the CSV to the returned presigned URL
   mcp__soria__scraper_confirm_uploads(scraper="parent_mapping")
   ```
3. Schema mappings (CSV):
   ```
   mcp__soria__schema_mappings(group_id="{id}", read=True)
   mcp__soria__schema_mappings(group_id="{id}", update={...})
   ```
4. Publish to warehouse with force:
   ```
   mcp__soria__warehouse_manage(group_id="{id}", publish=True, force=True)
   ```
5. Re-run dbt for any downstream staging/intermediate that reads from
   `stg_parent_mapping` (`dbt run --select +stg_parent_mapping+`).

### Verify 100% join

```
mcp__soria__warehouse_query(sql="
WITH src_entities AS (
  SELECT DISTINCT
    {code_column} AS code,
    '{code_type}' AS code_type
  FROM {source_table}
  WHERE {code_column} IS NOT NULL
)
SELECT
  COUNT(*) AS total,
  COUNT(CASE WHEN m.code IS NOT NULL THEN 1 END) AS matched
FROM src_entities e
LEFT JOIN staging.stg_parent_mapping m
  ON e.code = m.code AND e.code_type = m.code_type
")
```

**Must be 100% before proceeding.** If not, go back to Gate 2 for the
remaining unmapped entities.

### ⛔ GATE: 100% match rate confirmed

---

## Gate 5: Wire Into dbt Intermediate / Marts

Replace name-based parent derivation with code-based join in the dbt
intermediate or marts model that feeds dives.

### Standard pattern

```sql
-- Deduplicate: one parent per code+code_type
ded_parent_mapping AS (
  SELECT code, code_type, canonical_parent, ticker, affiliation
  FROM staging.stg_parent_mapping
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY code, code_type ORDER BY input_name
  ) = 1
),

-- Join to source data
jnd_add_parent AS (
  SELECT s.*,
    m.canonical_parent AS parent_company,
    m.affiliation,
    m.ticker
  FROM {source_cte} s
  LEFT JOIN ded_parent_mapping m
    ON s.{code_column} = m.code AND m.code_type = '{code_type}'
)
```

### NAIC two-stage join (group preferred, cocode fallback)

```sql
jnd_add_parent AS (
  SELECT j.*,
    COALESCE(
      m_group.canonical_parent,
      m_cocode.canonical_parent,
      j.full_company_name
    ) AS parent_company,
    COALESCE(m_group.affiliation, m_cocode.affiliation) AS affiliation,
    COALESCE(m_group.ticker, m_cocode.ticker) AS ticker
  FROM source j
  LEFT JOIN ded_parent_mapping m_group
    ON j.group_code = m_group.code AND m_group.code_type = 'naic_group'
    AND j.group_code IS NOT NULL AND j.group_code != '0'
  LEFT JOIN ded_parent_mapping m_cocode
    ON j.cocode = m_cocode.code AND m_cocode.code_type = 'naic_cocode'
)
```

### Verify after wiring

- Zero blank `parent_company` values
- Rebrands consolidated (Anthem/Elevance shows as one entity across all years)
- Acquisitions consolidated (Aetna/CVS under one name)
- Market share sums to ~100% per period
- Top company table looks right

---

## Maintenance

### When new data arrives
1. Check match rate against mapping table
2. Unmatched codes → run through parallel.ai (Gate 2)
3. Reconcile and add to table (Gate 3)
4. Republish and re-verify (Gate 4)

### When M&A happens
1. Source data will eventually reflect new ownership (NAIC updates group_code,
   CMS reassigns contracts)
2. Add new code → parent mapping row
3. Update `canonical_parent` if acquiring company is the new display name
4. Old codes keep their old mapping — historical data stays correct

### When a company rebrands
1. Code stays the same (NAIC group_code doesn't change for rebrands)
2. Add new name as `input_name` row pointing to updated `canonical_parent`
3. Update `canonical_parent` to current name for dive clarity
   (Anthem → Elevance Health)

---

## Anti-Patterns

1. **Joining on company name.** Names have punctuation variants, abbreviations,
   capitalization differences. Always join on `code + code_type`.

2. **Running parallel.ai without context.** "Anthem Inc" alone gets worse results
   than "Anthem Inc - U.S. health insurance holding company, NAIC group 671."
   Always include business type, state, regulatory ID.

3. **Trusting parallel.ai blindly.** ~10% of results are wrong, especially for
   obscure private companies. Always reconcile (Gate 3).

4. **Separate mapping tables per data source.** One centralized table. NAIC,
   MA Enrollment, CMS Cost Reports, and Form 5500 all join to the same table
   via different `code_type` values.

5. **Skipping the 100% match verification.** If even 1% is unmatched, those
   companies show up with wrong/missing parents on dives. Fix before shipping.

6. **Forgetting historical name variants.** If NAIC used "AETNA GRP" in 2016
   but "CVS HEALTH GRP" in 2019, both names need rows pointing to "CVS Health".
   Missing variants cause companies to split into multiple entities in time series.

---

## Artifact Output

```bash
cat > ~/.soria-stack/artifacts/parent-map-$(date +%Y%m%d-%H%M%S).md << 'ARTIFACT'
# Parent Mapping: [Data Source]

## Scope
[Code type, source table, total entities]

## Coverage
[Already mapped, newly mapped, failures collapsed to self-named]

## Parallel.ai Run
[Task group ID, success rate, cost]

## Reconciliation
[Canonical parents created, affiliations tagged, name variants added]

## Match Rate
[100% achieved? If not, what's unmatched and why]

## dbt Model
[Which intermediate/marts model was wired up, join pattern used]

## Outcome
Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
Lesson: [What was interesting or unexpected]
ARTIFACT
```
