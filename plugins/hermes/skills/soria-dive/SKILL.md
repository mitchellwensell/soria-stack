---
name: soria-dive
description: 'Soria Stack Hermes skill for dive. Build or revise a dive end-to-end in Hermes — dbt marts SQL, manifest, TSX component, DivesPage registration, verification rows, and methodology content. Use for new dives, major dive refactors, or deep review of an existing dive. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/dive/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Dive

Hermes adapter for upstream Soria-stack skill `dive`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-dive`
- Upstream source: `plugins/soria-stack/skills/dive/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Dive

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-dive` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- dbt marts SQL under `frontend/src/dives/dbt/models/marts/...`
  (layers: staging → intermediate → marts; no upstream SQLMesh)
- manifests at `frontend/src/dives/manifests/{id}.manifest.tsx` — **`.tsx`**
  because the `methodology` field is JSX. Manifest owns `title`, `overview`,
  `methodology`, `table`, `modelId`, `verificationModel`, `columns`,
  `metrics`, `filters`, `defaultTopN`. Manifest `table` values should use
  the prod-looking catalog name (`soria_duckdb_main.main_marts...`); the
  frontend rewrites that catalog to staging when the environment badge is on
  staging.
- React components at `frontend/src/dives/{id}.tsx`. Compose
  `DiveShell` + `useDiveData(manifest, filters)` + `useDiveParam` (URL
  state) + `useDiveVerifications(manifest.verificationModel)` +
  `pivotRows` + `DiveGrid` / `DiveKPIRow` / `DiveSection`.
- DivesPage registration, rows in the shared `verifications.csv` seed
- grain-first design, not just visual assembly
- data survey via `warehouse_query` before writing SQL

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

## Notes

- Methodology lives in the manifest as JSX. `DiveShell` surfaces it; don't
  put it in the component.
- `useDiveData` hides the dual-mode load (Postgres proxy → WASM). Don't
  branch on mode in the component.
- Local `dbt run` writes to `soria_duckdb_staging`. Prod target is absent
  from committed `profiles.yml`; CI injects it on PR merge.
- Do **not** "fix" a dive manifest by changing `soria_duckdb_main` to
  `soria_duckdb_staging`. `use-dive-query.ts` intentionally rewrites
  `soria_duckdb_main` to the selected data environment. A local/staging dive
  should therefore have a manifest table like
  `soria_duckdb_main.main_marts.some_dive`, while the actual query hits
  `soria_duckdb_staging.main_marts.some_dive` when the EnvironmentBadge is
  set to staging.
- If a dive works in staging but `soria_duckdb_main.main_marts.<model>` is
  missing, that is expected before promotion. Treat prod absence as a
  promotion/build state, not evidence that the staging dive is wired wrong.
- **Iteration loop:** local `dbt run` → open `dev.soriaanalytics.com` →
  click the `EnvironmentBadge` (amber/green pill) to **staging** to see
  your changes; toggle back to **prod** for the customer view. Default is
  prod. The badge sends `X-SQLMESH-ENV` (legacy name; not SQLMesh-related).
- Browser QA is required after meaningful UI changes. At minimum check each
  view/control family for latest-period columns visible, horizontal scrollbar
  present when needed, row click updating chart/state, no blank or repeated
  rows, no redundant controls, and console/network free of hidden data
  failures.
- Use `preview` for in-chat output or `dashboard-review` for live UI proof
  after implementation.
- Use mempalace when available for domain definitions or prior design context.
