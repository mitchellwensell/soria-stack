---
name: dive
version: 2.0.0
description: |
  Build a dive end-to-end — dbt marts SQL + manifest + TSX component +
  DivesPage registration + rows in the shared verifications seed +
  methodology content wired into the dive component. Forces grain-first
  thinking, end-user framing, and the "what question does this answer?"
  conversation before any SQL. Includes data quality survey, SQL review
  checklist, and verify-check authoring. Uses `mcp__soria__warehouse_query`
  for data inspection; authors dbt SQL locally in `frontend/src/dives/dbt/`.
  Use when asked to "build a dive", "make a dashboard", "write the SQL",
  "create a pivot", "show me the data", "profile this table", "review the
  dive SQL", or "add verify checks".
  Proactively invoke this skill (do NOT write dbt models ad-hoc) when the
  user wants to build or modify a dive. Three Questions must be answered first.
  Use after /ingest or /map, before /verify. (soria-stack)
benefits-from: [ingest, map, parent-map]
allowed-tools:
  - Read
  - Bash
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - WebSearch
  - AskUserQuestion
---

## Preamble (run first)

```bash
mkdir -p ~/.soria-stack/artifacts
echo "SKILL: dive"
echo "---"
echo "Git state (soria-2):"
git status --short 2>&1 | head -15 || echo "  (not in soria-2 checkout)"
echo "---"
echo "Checking for prior artifacts..."
ls -t ~/.soria-stack/artifacts/ingest-*.md ~/.soria-stack/artifacts/map-*.md 2>/dev/null | head -3
echo "---"
echo "Dive filesystem layout:"
ls frontend/src/dives/ 2>/dev/null | head -20
ls frontend/src/dives/dbt/models/marts/ 2>/dev/null
ls frontend/src/dives/dbt/seeds/ 2>/dev/null
```

Read `ETHOS.md`. Key principles for /dive: #4, #5, #12, #13, #14, #16, #28, #29, #30, #31.

**Check for prior work:** Read any ingest or map artifacts — they have table
names, schemas, value mapping status, and open questions. If no artifacts
exist, check what tables are available:

```
mcp__soria__warehouse_query(sql="
  SELECT table_schema, table_name
  FROM information_schema.tables
  WHERE table_schema IN ('bronze', 'main_staging', 'main_intermediate', 'main_marts')
  ORDER BY 1, 2
")
```

If /plan exists, check if it specified R-phase verification criteria.

## Skill routing (always active)

When the user's intent shifts mid-conversation, invoke the matching skill —
do NOT continue ad-hoc:

- User wants to check pipeline status → invoke `/status`
- User wants to fix extraction issues → invoke `/ingest`
- User wants to fix value mappings → invoke `/map`
- User says "verify this", "spot check", "is this correct" → invoke `/verify`
- User wants to see the dive rendered in chat → invoke `/preview`
- User wants to test the dive in a browser → invoke `/dashboard-review`
- User says "push to prod" → invoke `/promote`

**After /dive completes, suggest `/verify`** (Model Verify + Semantic Verify)
and `/preview` to inspect the output.

---

# /dive — "What question does this answer?"

You are a dive designer. Your job is to build the full stack for a dive:
dbt marts model → verify rows in the shared seed → manifest → TSX component
→ methodology content in the component → `DivesPage.tsx` registration.

You NEVER write SQL before answering three questions.

---

## Reusable Dive Design Principles

- Treat a dive as a consistent analytical instrument, not a collection of
  unrelated charts.
- Prefer a stable page pattern: KPI row, selected-row chart, then a pivot
  table.
- Tables should usually put time on the column axis and the primary dimension
  on rows.
- Prefer shared dive primitives over custom one-off wiring. For standard
  time-across-columns tables, use `DiveGrid` pivot mode unless there is a
  clear reason not to. Custom tables must preserve the same baseline behavior:
  pinned row labels, latest-period visibility, horizontal scroll, row click,
  formatting, empty-row suppression, and total/other styling.
- Time-axis tables must be visually usable on first render. When periods run
  left-to-right, the latest/rightmost period should be visible by default, and
  the table must expose an obvious horizontal scrollbar when older periods are
  off-screen.
- Use URL state for every meaningful control and selected row.
- When a table row represents an entity, clicking it should update the
  selected entity and redraw the chart.
- Default the selected entity to the first meaningful ranked row, not a
  hardcoded company unless product context requires it.
- For company or entity comparisons, prefer Top N cohorts on a stable size
  metric, plus `Other` and `Industry Total` where applicable.
- Keep ranking basis separate from displayed metric. Avoid ranking by noisy
  ratios like margin or mix percentage unless that is explicitly the analysis.
- Compute `Other`, totals, and ratios from summed numerators and denominators;
  do not average percentages.
- Suppress empty or meaningless rows. Avoid tables with many blanks, single
  low-value rows, or rows that do not add analytical value.
- Hide controls with only one meaningful option. Do not add redundant toggles
  or dropdowns when row click already controls selection.
- Keep core analytical choices visible when practical. Use segmented/pill
  controls for primary views, metrics, and modes; reserve searchable dropdowns
  for large entity or filter lists.
- Avoid adding analytical modes that require explanation unless the user
  explicitly asked for them or the UI names them clearly.
- Use tree or pivot rows for subdimensions such as product mix, payer mix,
  rating bucket mix, or revenue category mix while preserving time as columns.
- For tree/grouped pivot rows, verify the rendered hierarchy directly:
  parent labels, child labels, expand/collapse behavior, row-click target, and
  total/other handling. Parent/child identity should be deliberate, not an
  accidental side effect of the row key used for selection.
- KPIs should be view-specific and should explain the selected row or the
  market context, not reuse generic headline numbers.
- Charts should focus on the selected row, use the simplest legible visual
  form, and match existing dive styling.
- Build grain-first: model the analytical grain in dbt before composing React
  views.
- Prefer separate narrow marts or normalized semantic marts over pushing
  complex cohort/math logic into React.
- Verification rows should cover key totals, formula denominators, and known
  anchor values before the dive is considered ready.

---

## Layering And Grain Discipline

Use the dbt layer boundaries deliberately:

- **Source / Bronze**: raw published files only. No dashboard reads this
  directly.
- **Staging**: one model per raw concept. Clean, type, dedupe, normalize
  headers, unpivot, and drop messy source artifacts. No business joins beyond
  source cleanup.
- **Intermediate**: business logic and joins. This is where calculated fields,
  mappings, thresholds, exposures, parent joins, and methodology logic belong.
- **Marts**: customer-ready tables at explicit dashboard grains.
- **Dive**: presentation and interaction only. Minimal heavy logic.

Prefer fewer marts when the grain is the same. Do not create one mart per chart
if several views can be powered by the same customer-ready grain.

Never combine across incompatible grains. If joining detail rows would multiply
the primary entity rows, keep that detail in a separate intermediate or mart.

Rule of thumb:

- Combine aggressively within the same grain.
- Split when the grain changes.
- Keep numerator and denominator fields available when ratios or rollups
  matter.
- Keep dashboard code out of staging/intermediate joins and raw source patching.

Example:

A Star Ratings dive can use one primary mart:

- `star_ratings_contract_year`
- Grain: `contract_number + rating_year`
- Includes parent, enrollment, Overall, Part C, Part D, calculated score,
  exposure, and methodology fields

That mart can power parent history, Top N, Other, industry benchmark,
selected-company charts, and star mix by grouping contract-year rows.

Measure-level cutpoint logic is a different grain:

- `contract_number + rating_year + measure_code`

So it should stay separate:

- `int_star_ratings__measure_detail`
- `star_ratings_measure_heatmap`

Do not join measure rows into the contract-year mart, because that multiplies
contract rows and breaks enrollment-weighted metrics.

The goal is not "one table" or "many tables." The goal is one clean
customer-ready mart per analytical grain, with the dive doing only controls,
selection, chart formatting, and light grouping.

---

## Dive Architecture (what you're building)

Every dive has **five pieces of your own code plus rows in a shared seed
file**, all in the `soria-2` git checkout:

```
frontend/src/dives/dbt/models/marts/{domain}/{model}.sql    -- dbt marts SQL
frontend/src/dives/manifests/{dive-id}.manifest.ts          -- data contract
frontend/src/dives/{dive-id}.tsx                            -- React component
frontend/src/pages/DivesPage.tsx                            -- registration entry
frontend/src/dives/dbt/seeds/verifications.csv              -- ADD ROWS HERE for
                                                             --    your dive's checks
                                                             --    (shared seed across
                                                             --    all dives)
```

The dive is **not done** until:
- The marts model is in git and `dbt run` materializes it successfully
- The manifest references the marts model and all filter values exist in the data
- The component imports `useDiveData(manifest, filters)` and uses
  `useDiveVerifications({model_name})` to surface verify checks
- The component is registered in `DivesPage.tsx`
- At least ~15–20 rows have been added to `seeds/verifications.csv` with
  `model = '{your_marts_model}'` (one check row per metric × parent × period
  combination you care about)
- `dbt seed` has refreshed the verifications table
- Methodology content is visible through the dive's DivePageHeader or
  MethodologyModal integration (see "Methodology content" below)

## Git discipline

Every file you touch in this skill is git-tracked. Commit in logical chunks:

| Milestone | Commit |
|---|---|
| After `dbt run` succeeds for the new marts model | `dive({id}): add {domain} marts model` |
| After the manifest + TSX component exist and build | `dive({id}): add manifest + component` |
| After DivesPage registration | `dive({id}): register in DivesPage` |
| After verifications.csv rows added + `dbt seed` | `dive({id}): add verify checks` |
| After methodology content wired up | `dive({id}): add methodology content` |

Run `git status --short` before each commit to see what you changed. Don't
include unrelated edits in dive commits — keep the scope tight so PR
review stays readable.

## Iterative dev loop

The default flow is `make dev-https`: vite at `https://dev.soriaanalytics.com`
proxies `/api` to the prod DBOS backend + Clerk. The backend serves **both**
a staging and a prod MotherDuck — the frontend picks which one to query
via the **staging/prod badge** (amber "staging" / green "prod") in the app
chrome. Default is prod.

### The iteration loop

1. Edit dbt SQL locally in `frontend/src/dives/dbt/models/...`.
2. `../../../../.venv/bin/dbt run --select {model}` — lands in
   `soria_duckdb_staging.main_marts.{model}`.
3. Open `https://dev.soriaanalytics.com/dives?dive={dive-id}` (or already
   open — hot reload picks up component changes).
4. **Click the badge to toggle to staging** — the same page re-queries
   against your fresh `dbt run` output. Iterate.
5. When satisfied, toggle back to prod for a "what does the customer
   actually see today?" sanity check.
6. Commit → PR → CI materializes to `soria_duckdb_main` on merge. Prod
   badge mode then reflects your work.

The toggle is implemented via the `X-SQLMESH-ENV` header (legacy name;
doesn't mean SQLMesh is involved) on every request from `dashboardClient`.
Customer view locks to prod — the badge is disabled there.

Dive manifests should still declare prod-looking table names such as
`soria_duckdb_main.main_marts.{model}`. The frontend rewrites that catalog to
the selected data environment at query time, so the exact same manifest hits
`soria_duckdb_staging.main_marts.{model}` when the badge is set to staging.
Do not "fix" a local/staging dive by hardcoding `soria_duckdb_staging` in the
manifest. If the staging badge renders the dive but `soria_duckdb_main` lacks
the table, that is an expected pre-promotion state.

For fast in-chat inspection without opening a browser, `/preview` queries
`soria_duckdb_staging` directly via `mcp__soria__warehouse_query`.

---

## Domain Grounding (before the Three Questions)

Before designing the model, ground it in how the real world talks about this data.

### Earnings transcript and meeting search

Search prior sessions and transcripts for how the data domain is discussed:

```
mcp__openclaw__mempalace_search: query="utilization trends adjusted discharges", wing="earnings"
mcp__openclaw__mempalace_search: query="MLR medical loss ratio", wing="granola"
```

This tells you the exact metrics analysts ask about, how they frame YoY
comparisons, and what baseline periods they reference.

### External research (WebSearch / WebFetch)

Use `WebSearch` and `WebFetch` for broader domain grounding:
- "Standard KPIs for [this analytical domain]?"
- "How do equity analysts evaluate [this metric]?"
- "What's the published benchmark for [this rate]?"

Skip both steps if the domain is well-understood from prior sessions.

---

## Before ANY SQL: The Three Questions

### The Simplicity Check (before anything else)

If the user asks for multiple dives, multiple marts models, or a complex
structure — push back:
- "Can this be 1 dive with filter controls slicing it instead of 5 separate dives?"
- "Can this be 1 marts model with filter dimensions instead of 6 models?"
- "Do we need an intermediate model here, or can staging feed marts directly?"

Take a position. The simpler approach that produces correct data wins.

### Question 1: What specific question does this answer?
Not "show hospital data." Specific:
- "Which parent company has the lowest enrollment-weighted premium in each state?"
- "What's the Medical Care Ratio trend for UNH vs HUM over 10 years?"
- "How many Medicare Advantage beneficiaries are in 4+ star plans by insurer?"

If you can't state the question in one sentence, you're not ready to write SQL.

### Question 2: Who is looking at this?
- **Equity research analyst** → sortable pivot tables, company comparisons,
  YoY trends, enrollment-weighted metrics
- **Internal team** → pipeline health, data freshness, coverage gaps
- **Customer dashboard** → clean presentation, intuitive filters, audit trail
- **Adam exploring data** → flexibility, slice by any dimension

The audience determines: metric selection, grain, aggregation level, and
which filters to expose in the manifest.

### Question 3: What's the ideal visualization?
- Pivot table with companies as rows, months as columns?
- Time series chart with company lines?
- Bar chart comparing segments?
- Map with state-level shading?
- KPI cards + comparison table?

Sketch the visualization in text before writing SQL. The visualization
determines the grain and the shared primitives you'll reuse:

- `DiveGrid` — AG-Grid-based table with hierarchical rows
- `DiveKPIRow` — top-of-page KPI cards
- `DiveControlBar` — filter controls bound to manifest filters
- `DivePageHeader` — title, subtitle, last-updated
- `DiveUSMap` — state-level map
- `StickyDiveHeader` — sticky header for long-scroll dives
- `MethodologyModal` — per-element information button
- `VerifyModal` — semantic check results + provenance

### ⛔ GATE: THREE QUESTIONS ANSWERED
Present your answers to the three questions. Wait for confirmation before
designing the model.

---

## The Grain Design Step

This is the hardest part. Get this wrong and everything downstream is broken.

### Step 1: Define the grain
State it explicitly:
```
One row = one [parent_organization] per [reporting_month] per [segment]
```

### Step 2: List all dimensions in the grain
```
Dimensions in grain: parent_organization, reporting_month, segment, distribution
```

### Step 3: Check the filter compatibility
For each metric you plan to include:

| Metric | Type | Safe to aggregate across which dimensions? |
|--------|------|-------------------------------------------|
| enrollment | Additive | All dimensions — SUM always works |
| plan_count | Additive | All dimensions — COUNT DISTINCT works |
| market_share_pct | Ratio | ONLY within (segment, distribution, month) |
| yoy_delta_pct | Ratio | ONLY within (org, segment, distribution) |

### Step 4: Identify the conflict
If the dive filter will aggregate across a dimension that breaks ratio metrics:
- **Option A:** Drop the dimension from the grain. Ratios are correct but
  you lose the filter.
- **Option B:** Only include additive metrics at the fine grain. Ratios
  get computed at display time via the DiveGrid's rollup system.
- **Option C:** Two grain levels in one model (union).

**Never serve pre-computed ratios at a grain finer than the display.** This
is the 171% market share bug.

### Step 5: Present the grain design

### ⛔ GATE: GRAIN APPROVED
Present the grain design. This is where most pushback happens. Wait for approval.

---

## Data Quality Survey (before writing SQL)

Before writing SQL, get your eyes on the data. Run these 4 checks against the
warehouse table you'll be modeling (using `mcp__soria__warehouse_query`):

**Check 1: Schema & Row Counts**
```
mcp__soria__warehouse_query(sql="DESCRIBE {table}")
mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM {table}")
mcp__soria__warehouse_query(sql="SELECT DATE_TRUNC('year', date_col), COUNT(*) FROM {table} GROUP BY 1 ORDER BY 1")
mcp__soria__warehouse_query(sql="SELECT * FROM {table} LIMIT 5")
```
Report: column inventory, time range, shape.

**Check 2: Value Distributions**
For categoricals: `SELECT col, COUNT(*) FROM {table} GROUP BY col ORDER BY 2 DESC LIMIT 20`.
For numerics: `SELECT MIN, MAX, AVG, STDDEV, COUNT(DISTINCT col) FROM {table}`.
Report: unexpected entries, impossible values, cardinality.

**Check 3: Length & Format Outliers**
`SELECT LENGTH(col), COUNT(*) FROM {table} GROUP BY 1 ORDER BY 1 DESC LIMIT 10`.
Report: mixed formats, encoding issues.

**Check 4: NULL Analysis**
`SELECT COUNT(*) FILTER (WHERE col IS NULL) * 100.0 / COUNT(*) FROM {table}`.
Report: concentration patterns, recommended handling.

Skip this step if you already know the data well from prior sessions.

---

## The dbt Model Stack

Dive SQL lives in one dbt project (`soria_dives`) that reads bronze tables
published by the ingestion pipeline. There is no upstream SQL transformation
layer — bronze is raw, and staging/intermediate/marts are the dbt layers.

```
(ingest pipeline publishes → soria_duckdb_staging.bronze.*)
                ↓
frontend/src/dives/dbt/    (project: soria_dives)
  dbt_project.yml          → schemas: staging / intermediate / marts
  profiles.yml             → target: staging (reads MOTHERDUCK_STAGING_DATABASE)
  models/
    staging/               → views (CAST + clean + unpivot)
    intermediate/          → views (joins across staging)
    marts/
      {domain}/            → tables (the dive's main query target)
  seeds/
    verifications.csv      → shared seed: every dive's checks, filtered by model
    benchmarks.csv         → shared seed: external benchmarks referenced by checks
```

**Schema resolution** (dbt's rule): the final materialized schema is
`{target_default_schema}_{config_schema}`. For duckdb profiles the default
schema is `main`, so `+schema: marts` produces `main_marts`. Fully qualified:

- Local `dbt run` → `soria_duckdb_staging.main_marts.{model}`
- CI `dbt run --target prod` (on PR merge) → `soria_duckdb_main.main_marts.{model}`

There is no `prod` target in the committed `profiles.yml` — CI injects it
at deploy time so you can't accidentally `dbt run --target prod` locally.

The manifest points at `soria_duckdb_main.main_marts.{model}`. That is the
stable manifest convention, not proof the current browser query is using prod:
`use-dive-query.ts` rewrites `soria_duckdb_main` to the selected environment.
Use the staging badge for browser iteration against
`soria_duckdb_staging.main_marts.{model}`; use `/preview` when you want the
same staging inspection rendered in chat via `mcp__soria__warehouse_query`.

### Bronze sources
- Published by `mcp__soria__warehouse_manage(group_id="...", publish=True)`
- Schema: `soria_duckdb_staging.bronze.{table}`
- Declared in `dbt_project.yml` sources block
- Don't hand-insert bronze — use the ingest pipeline

### staging/ (dive project)
- `CAST` and rename as needed
- Unpivot wide metric columns to long format (Principle #3)
- `ref('bronze_source')` via sources block
- One staging model per bronze table
- No joins in staging (Principle #4)

### intermediate/ (dive project)
- Joins across staging
- Business logic specific to this dive
- `ref('stg_...')` to pull from staging
- No direct bronze references

### marts/{domain}/ (dive project)
- Dashboard-ready output
- One marts model per dive
- Materialized as TABLE
- Ratios computed HERE, after aggregation: `SUM(num) / NULLIF(SUM(denom), 0)`
- Column descriptions via dbt `description:` in `_{domain}__models.yml`
- Pre-compute only what the dive manifest's filters can't derive

### seeds/verifications.csv (dive project, shared across all dives)
- One CSV seed at `frontend/src/dives/dbt/seeds/verifications.csv`
- Each row is one verify check scoped to a specific dbt marts model via the
  `model` column
- Columns: `id, model, description, parent_company, lob, quarter, metric,
  min_value, max_value, source, source_url`
- Refreshed via `dbt seed --select verifications`
- Queried per-dive via `useDiveVerifications({marts_model_name})`

---

## CTE Naming Convention

| Prefix | Purpose | Example |
|--------|---------|---------|
| `src_` | Source reference | `src_enrollment AS (SELECT * FROM {{ ref('stg_ma_enrollment') }})` |
| `flt_` | Filter | `flt_active AS (SELECT * FROM src WHERE status = 'active')` |
| `jnd_` | Join | `jnd_enriched AS (SELECT ... FROM flt JOIN {{ ref('stg_companies') }} ...)` |
| `wnd_` | Window function | `wnd_yoy AS (SELECT *, LAG(value, 12) OVER (...))` |
| `clc_` | Calculation | `clc_metrics AS (SELECT *, (value - prior) / prior AS yoy_pct)` |
| `ded_` | Dedup | `ded_latest AS (SELECT * FROM src QUALIFY ROW_NUMBER() OVER (...) = 1)` |
| `agg_` | Aggregation | `agg_summary AS (SELECT org, month, SUM(enrollment) ...)` |
| `pvt_` | Pivot/Unpivot | `pvt_long AS (UNPIVOT src ON ...)` |

---

## Pivot Dive SQL Pattern

Canonical CTE structure for any pivot dive with time-series columns and
ratio metrics:

```sql
{{ config(materialized='table') }}

WITH
  src AS (SELECT * FROM {{ ref('stg_source_table') }}),

  -- Step 1: Aggregate to the row dimension grain
  agg AS (
    SELECT segment, distribution, parent_organization,
      reporting_date,
      STRFTIME(reporting_date, '%Y-%m') AS reporting_month,
      SUM(enrollment) AS enrollment
    FROM src
    GROUP BY ALL
  ),

  -- Step 2: Join prior year AT THE SAME GRAIN
  prior AS (
    SELECT c.*, p.enrollment AS prior_year_enrollment
    FROM agg c
    LEFT JOIN agg p
      ON c.parent_organization = p.parent_organization
      AND c.segment = p.segment
      AND c.distribution = p.distribution
      AND c.reporting_date = p.reporting_date + INTERVAL 12 MONTH
  ),

  -- Step 3: Compute ratio metrics at this grain
  metrics AS (
    SELECT *,
      ROUND(enrollment * 100.0 / NULLIF(
        SUM(enrollment) OVER (PARTITION BY segment, distribution, reporting_month), 0
      ), 2) AS market_share_pct,
      enrollment - prior_year_enrollment AS yoy_delta,
      ROUND((enrollment - prior_year_enrollment) * 100.0
        / NULLIF(prior_year_enrollment, 0), 2) AS yoy_delta_pct
    FROM prior
  )

SELECT * FROM metrics
```

Key rules this template encodes:
1. **Grain matches the row dimension** — no finer keys than what the
   manifest exposes as row dimensions
2. **Ratio metrics partition by ALL filter columns** — `PARTITION BY segment,
   distribution, reporting_month`, not just `reporting_month`
3. **YoY joined at the model grain** — matching on segment + distribution +
   org + date, not just org + date
4. **Filter columns in output** — the manifest picks them up via `where`/`filters`
5. **Raw components alongside ratios** — enrollment ships with market_share_pct
   so the DiveGrid rollup can recompute

---

## The Manifest

After the marts SQL is written, create the dive manifest at
`frontend/src/dives/manifests/{dive-id}.manifest.tsx` (note: **`.tsx`**,
not `.ts` — the `methodology` field is JSX). This is the single source of
truth for the dive: title, table, columns, filters, metric picker options,
and the methodology prose the frontend surfaces.

```tsx
// frontend/src/dives/manifests/{dive-id}.manifest.tsx
import { defineDiveManifest } from "@/dives/lib/dive-manifest";

export default defineDiveManifest({
  id: "{dive-id}",
  title: "{Human-readable dive title}",
  overview: "{One-sentence description shown under the title}",
  methodology: (
    <p className="text-muted-foreground" style={{ lineHeight: 1.7 }}>
      Source: {dataset name + cadence}.
      {Grain statement — "One row = one X per Y per Z".}
      {Key formulas — MLR, market share, YoY derivation.}
      {Known gotchas — M&A, methodology changes, era splits.}
    </p>
  ),
  table: "soria_duckdb_main.main_marts.{model}",
  modelId: "model.soria_dives.{model}",        // dbt node id for lineage
  verificationModel: "{model}",                // seed row filter
  columns: [
    // projection: identity cols + every metric the user can pivot on
    "parent_company",
    "quarter_label",
    "total_enrollees",
    "market_share_pct",
    "yoy_delta_pct",
    // ...
  ],
  defaultTopN: 20,
  metrics: [
    { key: "total_enrollees",   label: "Total Enrollees", fmt: "number" },
    { key: "market_share_pct",  label: "Market Share %",  fmt: "pct2"   },
    { key: "yoy_delta_pct",     label: "YoY Growth %",    fmt: "pct2"   },
    // ...
  ],
  filters: {
    planType: {
      column: "plan_type",
      values: ["Full Service", "Specialized", "Dental"],
      default: "Full Service",
      prefetch: true,   // warm the session cache for the other values after first paint
    },
  },
});
```

**Rules:**
- Explicit `columns` — drops payload size vs `SELECT *`.
- Methodology lives **in the manifest** as JSX. `DiveShell` surfaces it;
  don't wire it by hand in the component.
- `verificationModel` is the string the `verifications.csv` seed filters by
  (same as the dbt marts model name).
- Every filter value must exist in the data. Verify against staging (where
  your local `dbt run` just landed):
  ```
  mcp__soria__warehouse_query(sql="
    SELECT DISTINCT plan_type FROM soria_duckdb_staging.main_marts.{model}
  ")
  ```
- `prefetch: true` on filter options the user typically cycles through.
- The manifest is the source of truth — never hardcode WHERE clauses or
  column projections in the component.

---

## The TSX Component

The component is thin: it binds filter state, calls `useDiveData`, shapes
the rows (usually via `pivotRows`), and composes a handful of primitives
from `frontend/src/dives/components/`. A minimal dive looks like this:

```tsx
// frontend/src/dives/{dive-id}.tsx
import { useMemo } from "react";
import { useDiveData } from "@/dives/lib/use-dive-data";
import { useDiveParam } from "@/dives/lib/use-dive-param";
import { useDiveVerifications } from "@/dives/lib/use-dive-verifications";
import { filterOptions, metricOptions, findMetric } from "@/dives/lib/dive-manifest";
import { pivotRows } from "./lib/pivot";
import { DiveShell } from "./components/DiveShell";
import { DiveKPIRow } from "./components/DiveKPIRow";
import { DiveSection } from "./components/DiveSection";
import { DiveGrid } from "./components/DiveGrid";
import manifest from "./manifests/{dive-id}.manifest";

const METRICS = metricOptions(manifest);
const { planType: PLAN_TYPES } = filterOptions(manifest);

export default function MyDive() {
  // URL-bound filter state — shareable links, browser back/forward work.
  const [metric,   setMetric]   = useDiveParam("metric",   "total_enrollees");
  const [planType, setPlanType] = useDiveParam("planType", "Full Service");

  // Filter values flow into useDiveData; changing them re-queries.
  const filterValues = useMemo(() => ({ planType }), [planType]);
  const { data, isLoading } = useDiveData(manifest, filterValues);

  // Verify rows for this dive — per-cell tooltips when actuals fall outside bounds.
  const { data: verifyData } = useDiveVerifications(
    manifest.verificationModel,
    { enabled: !!data },
  );

  // Client-side pivot to "row per parent × column per quarter".
  const rows     = useMemo(() => (Array.isArray(data) ? data : []), [data]);
  const quarters = useMemo(() => [...new Set(rows.map(r => r.quarter_label))].sort(), [rows]);
  const { pivoted } = useMemo(
    () => pivotRows(rows, {
      rowField:   "parent_company",
      colField:   "quarter_label",
      valueField: metric,
      columns:    quarters,
    }),
    [rows, metric, quarters],
  );

  const metricDef = findMetric(manifest, metric)!;

  return (
    <DiveShell
      manifest={manifest}
      controlGroups={[
        { label: "Plan Type", options: PLAN_TYPES, value: planType, onChange: setPlanType },
        { label: "Metric",    options: METRICS,    value: metric,   onChange: setMetric   },
      ]}
    >
      <DiveKPIRow loading={isLoading} kpis={[/* ... */]} />

      <DiveSection title={`${planType} · ${metricDef.label}`} loading={isLoading}>
        <DiveGrid
          rowData={pivoted}
          rowField="parent_company"
          valueColumns={quarters}
          columnHeaderFormat="quarter"
          valueFormat={metricDef.fmt}
          verifyChecks={verifyData}   // cells outside bounds get a tooltip
        />
      </DiveSection>
    </DiveShell>
  );
}
```

### How the composition actually works

- **`DiveShell`** owns the page layout, the sticky filter bar built from
  `controlGroups`, and the Methodology / Verify buttons that open the
  manifest's methodology JSX and the verify modal. You pass the `manifest`
  in; it reads `title` / `overview` / `methodology` itself.
- **`useDiveData(manifest, filterValues)`** builds the SQL from the
  manifest (columns + active filter values) and returns `{data, isLoading,
  isError}`. It handles the dual-mode load automatically: first paint
  arrives via the Postgres wire proxy (~500ms); the WASM DuckDB client
  takes over transparently (~20s to warm). The component shouldn't branch
  on "mode" — just render what's in `data`.
- **`useDiveParam(key, default)`** is `useState` backed by the URL
  querystring. Every filter that belongs in the manifest should use this;
  links become shareable and browser back/forward work correctly.
- **`useDiveVerifications(manifest.verificationModel)`** returns the rows
  of the shared `verifications.csv` seed filtered to this dive's marts
  model. Pass them to `DiveGrid` as `verifyChecks`; the grid walks each
  cell and shows `VerifyTooltip` when the rendered value falls outside
  `[min_value, max_value]`.
- **`pivotRows(rows, {rowField, colField, valueField, columns, rowOrder?})`**
  reshapes long-format rows into wide pivot. The marts model stays at the
  correct grain; pivoting happens at render time.

Other primitives available in `frontend/src/dives/components/`:
`DivePageHeader`, `StickyDiveHeader`, `DiveUSMap`, `DiveBarChart`,
`DiveLineChart`, `DiveStackedBarChart`, `DiveDashboardGrid` (for
multi-section dives), `DiveBackLink`, `DiveFullscreen`. Scan the directory
before inventing a new one — reuse beats bespoke.

### Anti-patterns in the component

- **Branching on "the WASM isn't ready yet."** `useDiveData` hides the
  transition. Don't try to show different UIs for server vs WASM modes.
- **Hardcoding filter values in the component.** Filters live in the
  manifest; `DiveShell` builds the control bar from them.
- **Rolling your own grid.** `DiveGrid` has verify tooltips, heatmap
  toggle, hierarchical rows, and `rowOrder` support. Extend it rather than
  fork.
- **Putting methodology text inside the component.** Methodology is a JSX
  field on the manifest. That's what `DiveShell` surfaces — bypassing it
  means customers don't see your explanation.

---

## Verify checks — rows in the shared verifications seed

Every dive's verify checks live in **one shared dbt seed file**:
`frontend/src/dives/dbt/seeds/verifications.csv`. The file has these columns:

```
id, model, description, parent_company, lob, quarter, metric,
min_value, max_value, source, source_url
```

- **`model`** — the dbt marts model name (e.g. `naic_national_kpis_by_company`).
  Matches the manifest's `verificationModel`. This is how dives filter to
  their own checks.
- **`description`** — human-readable prose explaining what the check validates
  (e.g. "UNH Total membership ~23M")
- **`parent_company`, `lob`, `quarter`, `metric`** — the row/column/cell this
  check applies to. NULL values mean "any".
- **`min_value`, `max_value`** — the accepted bound. If the real value is
  outside, the check fails.
- **`source`, `source_url`** — provenance. Every non-self-check needs a real
  external citation (SEC filing, KFF report, CMS data, Kaufman Hall report).

Add ~15–20 rows per dive: top companies × key metrics × key periods, plus
a few bounded_range sanity checks for the overall market. Commit the CSV,
then run:

```bash
cd frontend/src/dives/dbt
../../../../.venv/bin/dbt seed --select verifications
```

The dive component picks up your new rows automatically via
`useDiveVerifications(manifest.verificationModel)`.

## Methodology content

Methodology lives **in the manifest** as a JSX element on the
`methodology` field (see the Manifest section above). `DiveShell` renders
it behind the Methodology button — no separate file, no prop passing, no
bespoke pattern per dive.

Every dive's methodology must cover:

- **Sources** — dataset name, URL, update cadence
- **Grain** — "one row = one X per Y per Z"
- **Metric definitions** — each metric's formula in plain language
- **Gotchas** — M&A events, source methodology changes, bounds

Keep it prose, not a spec sheet. Customers read it once to decide whether
to trust the numbers; make that decision easy.

---

## DivesPage Registration

Add the dive to `frontend/src/pages/DivesPage.tsx`:

```tsx
const DIVES: DiveEntry[] = [
  // ... existing dives ...
  {
    id: "ma-enrollment",
    title: "MA Enrollment",
    description: "Monthly Medicare Advantage enrollment by parent organization — filter by segment, distribution, network.",
    component: lazy(() => import("@/dives/ma-enrollment")),
  },
];
```

---

## Build + Test

Run dbt locally (writes to `soria_duckdb_staging`):

```bash
cd frontend/src/dives/dbt
../../../../.venv/bin/dbt run --select {model}
../../../../.venv/bin/dbt test --select {model}
../../../../.venv/bin/dbt seed --select verifications   # refresh verify checks
```

Or from the repo root: `make dbt-docs` rebuilds the manifest so the
frontend's lineage view picks up changes.

Verify the marts table landed in staging:

```
mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM soria_duckdb_staging.main_marts.{model}")
```

Verify your verify check rows landed in the shared table:

```
mcp__soria__warehouse_query(sql="
  SELECT COUNT(*) FROM soria_duckdb_staging.main.verifications
  WHERE model = '{your_marts_model}'
")
```

### Running the dive in a browser

Default flow is `make dev-https` — vite at `https://dev.soriaanalytics.com`
proxied to DBOS. The data environment is selected by the staging/prod badge.
Set the badge to **staging** to validate local dbt output in the browser;
set it to **prod** only for the customer-view sanity check. `/preview` is the
chat-native staging alternative.

The `vite-dbt-sync.ts` Vite plugin copies `dbt/target/manifest.json` +
`run_results.json` into `frontend/public/dbt-docs/` on change — this is
what powers the `DbtLineageFlow` component and the `last_dbt_run`
timestamps in `VerifyTooltip`. If you run `dbt run` while `make dev-https`
is active, the sync is automatic.

---

## SQL Review Checklist (pre-commit)

Before committing a dive's SQL:

1. **CTE hygiene** — Every CTE earns its place, has the right prefix (`src_`,
   `flt_`, `clc_`, `agg_`, `wnd_`, `ded_`, `jnd_`, `pvt_`), no over-splitting
   or under-splitting.
2. **Conventions** — Column descriptions in the dbt `_models.yml`, no joins
   in staging, ratios after aggregation, `QUALIFY ROW_NUMBER()` for dedup.
3. **No dead code** — No unreferenced CTEs, unselected columns, no-op WHEREs.
4. **Grain matches row dimension** — no finer keys than what the manifest
   exposes as row dimensions
5. **Ratio metrics computed at model grain** — not at a finer grain
6. **YoY joined at model grain** — not on sub-entity keys
7. **Filter columns present** — every manifest filter column is in the SELECT
8. **Raw components alongside ratios** — enrollment ships with market_share_pct

---

## Verify checks (every dive)

Every dive ships with verify check rows added to
`frontend/src/dives/dbt/seeds/verifications.csv`. Build them as part of
the /dive workflow, not as an afterthought.

### Steps

1. **Spot checks against external sources** — for top companies, top
   metrics, recent periods, add a row citing an SEC filing, earnings call,
   or industry report. These are the high-signal checks customers see in
   the VerifyModal.
2. **Bounded range checks** — use `WebSearch` / `WebFetch` to find
   published bounds for headline metrics (total market size, top-N
   concentration). Add rows with `parent_company=NULL` (overall market).
3. **Historical sanity checks** — add a few rows for older periods so
   long-range queries have verify coverage too.

### Adding rows

Edit `frontend/src/dives/dbt/seeds/verifications.csv` and append new rows:

```csv
id,model,description,parent_company,lob,quarter,metric,min_value,max_value,source,source_url
NNN,your_marts_model,UNH Total membership ~23M,UNITEDHEALTH,Total,2025-06,membership,18000000,28000000,UNH 10-K 2024,https://www.sec.gov/...
```

Pick a new unique `id` (the column is bigint — max(id) + 1). Use NULL
(empty cell) for dimensions that don't apply. Every row with a non-null
`source` needs a real `source_url`.

### Refresh the seed

```bash
cd frontend/src/dives/dbt
../../../../.venv/bin/dbt seed --select verifications
```

Then query the materialized seed to confirm your rows landed:

```
mcp__soria__warehouse_query(sql="
  SELECT COUNT(*), MIN(id), MAX(id)
  FROM soria_duckdb_staging.main.verifications
  WHERE model = 'your_marts_model'
")
```

### Investigating failures

When a cell in the dive is outside a verify bound, the `VerifyTooltip`
component surfaces the check + source. During /verify Mode 3, query the
verifications table and compare actual values against `min_value`/`max_value`.
Classify failures by the same taxonomy as old semantic checks:

| Classification | Action |
|---|---|
| Pipeline bug (data wrong) | Fix (invoke `/ingest` or edit marts SQL) |
| M&A structural change | Document + update the check's description |
| Source data limitation | Document + update bounds with rationale |
| Known industry event | Document + add source URL |
| Threshold too tight | Widen bounds with justification |

### ⛔ GATE: VERIFY CHECKS ADDED + PASSING
At least ~15 rows in `verifications.csv` for this model. Every failing
check investigated and classified before DONE. Zero unexplained failures.

---

## Artifact Output

At the end of a dive session, write a dive spec:

```bash
cat > ~/.soria-stack/artifacts/dive-$(date +%Y%m%d-%H%M%S).md << 'ARTIFACT'
# Dive Spec: [Dive Name]

## Three Questions
[Question, audience, visualization]

## Grain Design
[Grain statement, dimension list, filter compatibility check]

## Files Created / Modified
- dbt: frontend/src/dives/dbt/models/marts/{domain}/{model}.sql
- seed: frontend/src/dives/dbt/seeds/verifications.csv (added N rows)
- manifest: frontend/src/dives/manifests/{dive-id}.manifest.ts
- component: frontend/src/dives/{dive-id}.tsx
- registration: frontend/src/pages/DivesPage.tsx (entry added)
- methodology: (location follows existing dive convention — document here)

## dbt Results
- Model row count: [N]
- `dbt test` passed: [X/Y]
- Verify checks for this model: [N rows in verifications table]

## Open Questions
[Anything that needs human decision]

## Outcome
Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
Lesson: [What was interesting or unexpected]
ARTIFACT
```

This artifact is consumed by `/verify` when proving the dive correct and by
`/promote` when preparing the PR.

---

## Anti-Patterns

1. **Writing SQL before answering the three questions.** Wrong grain, wrong
   metrics, wasted time.

2. **Pre-computing ratios at fine grain.** Market share per plan type × org
   × month → pivot sums to 171%.

3. **Six marts models for one dataset.** One model + manifest filters.

4. **Skipping column descriptions in dbt `_models.yml`.** Every column needs
   a business label. DivesGrid reads them for headers and the MethodologyModal
   references them.

5. **Joins across sources in staging.** Staging is one-bronze-in, one-staging-out.
   Joins happen in intermediate or marts.

6. **Averaging ratios.** `AVG(margin_pct)` gives equal weight to 10-bed and
   1000-bed hospitals.

7. **Shipping a dive with empty or missing methodology + verify surfacing.**
   The dive component must route users to (a) methodology content (sources,
   formulas, grain) and (b) verify check results via `VerifyModal` /
   `VerifyTooltip`, backed by rows in the verifications seed (Principle #29).
   A dive where clicking "How is this built?" opens an empty panel is shipping
   opaque data.

8. **Hardcoding WHERE clauses in the component.** The manifest is the config.
   Always add filters to the manifest — never bypass it (Principle #31).

9. **Forgetting the DivesPage registration.** The component can be lazy-
   imported without registration, but it won't show up in the UI. Always
   add the entry.

10. **Skipping `dbt test` before declaring done.** Running `dbt run` is not
    the same as running `dbt test`. Both must pass.

11. **Skipping the semantic model.** Every dive ships with semantic checks.
    If you don't have time for semantic checks, you don't have time to
    ship the dive.

12. **Wiring the manifest table to a non-existent marts model.** If `dbt run`
    hasn't landed the marts table, the manifest will fail at runtime. Build
    the SQL and verify the table exists before writing the manifest.
