---
name: soria-stack
version: 6.0.0
description: |
  Data pipeline skills for Soria Analytics. Cognitive modes for upstream
  pipeline work (scrape → parse/extract → value-map → publish) and for building
  dives (dbt marts + manifest + React component + DivesPage registration +
  rows in the shared verifications seed + methodology wired into the component).
  All skills drive the Soria platform through the `mcp__soria__*` MCP tool
  namespace. SQL and React dives are authored locally in `frontend/src/dives/`
  and shipped via `git push` + PR — there is no `soria` CLI.
  Soria skills: /tools (verify MCP + local stack), /env (preflight; no
  isolated envs), /status (what exists), /plan (ETVLR orchestrator),
  /scraper (write/test scrapers), /ingest (group + extract + publish),
  /map (value mapping), /parent-map (centralized parent company resolution),
  /dive (build a dive end-to-end),
  /preview (render a dive in chat), /verify (prove data correct),
  /dashboard-review (adversarial browser QA against dev.soriaanalytics.com),
  /diagnose (failure triage), /ticket (file structured tickets mid-session),
  /promote (warehouse_diff + warehouse_promote + PR + CI), /newsroom (news
  pipeline ops), /lessons (retrospective), /browse (persistent Chromium via
  the `agent-browser` CLI for verification, screenshots, and Soria-app
  login), plus engineering skills /dev-env, /dev-dives,
  /test, and /code-review for branch-local app work, dev HTTPS dive frontend
  repair, test evidence, and Soria-specific code review.
  Suggest the right skill by stage: starting a session → /tools;
  investigating what exists → /status; planning work → /plan; writing scraper
  code → /scraper; building a pipeline → /ingest; normalizing values → /map;
  resolving parent companies → /parent-map; building a dive or reviewing its
  SQL → /dive; proving data correct → /verify; testing live dive UI → /dashboard-review; something
  broke → /diagnose; filing a bug/feature ticket → /ticket; promoting to
  prod → /promote; news pipeline → /newsroom; reviewing recent work →
  /lessons.
allowed-tools:
  - Read
  - Bash
---

## Preamble (run first)

```bash
mkdir -p ~/.soria-stack/artifacts
echo "SoriaStack v6 loaded"
echo "---"
echo "Recent artifacts:"
ls -t ~/.soria-stack/artifacts/*.md 2>/dev/null | head -5 || echo "  (none)"
```

**Reversibility, not isolation.** There are no isolated dev environments.
Every MCP write lands on shared Postgres + `soria_duckdb_staging` — but
every write is soft-delete reversible via `deleted_at` + the
`PipelineEvent` audit trail. Promotion to `soria_duckdb_main` is PR-gated
through `.github/workflows/promote.yml` and `dbt-deploy.yml`.

Read `ETHOS.md` before any data pipeline work. See `MCP_TOOL_MAP.md` for
the tool surface.

# SoriaStack — Data Pipeline And Engineering Skills

SoriaStack contains data pipeline skills and engineering skills. Data pipeline
skills drive the platform through the `mcp__soria__*` MCP tool namespace.
Engineering skills operate inside app repo worktrees and follow that repo's
`AGENTS.md`, scripts, and local dev environment rules.

## Skill routing

| If the user is... | Suggest |
|-------------------|---------|
| Starting a new session | `/tools` |
| Sanity-checking the dev stack | `/env` |
| Asking "what do we have for X?" | `/status` |
| Saying "let's work on X" or "come up with a plan" | `/plan` |
| Writing or repairing source discovery code | `/scraper` |
| Ready to group, extract, or publish | `/ingest` |
| Normalizing values across eras | `/map` |
| Resolving company names to parent companies | `/parent-map` |
| Building a dive, writing dbt SQL, or reviewing a dive | `/dive` |
| Checking if data is correct, proving it | `/verify` |
| Testing a live dive in a browser | `/dashboard-review` |
| Wanting to see a dive rendered in chat | `/preview` |
| Something broke or isn't working | `/diagnose` |
| Hit a bug, need to file a ticket | `/ticket` |
| Promoting to production (`git push` + PR) | `/promote` |
| Working with the news pipeline | `/newsroom` |
| Reviewing recent work for lessons | `/lessons` |
| Needing a persistent browser (repro, recon, Soria-app login) | `/browse` |
| Entering or repairing a branch-local app dev environment | `/dev-env` |
| Repairing `dev.soriaanalytics.com` dive frontend/runtime alignment | `/dev-dives` |
| Testing Soria engineering changes or choosing E2E proof | `/test` |
| Reviewing a Soria code diff or PR | `/code-review` |

## The sequence

```
/tools (verify MCP reachable + local stack installed — always first)
   ↓
/status → /plan → /scraper → /ingest → /map → /dive → /verify → /promote
                    (skip /scraper if files already exist)
                          ↑              ↑
                   /parent-map      (verify rows live in
                   (parallel to /map) the shared seed,
                                     authored inside /dive)
   + /dashboard-review (browser QA — after dive is in git)
   + /preview (render dive output in chat — any time)
   + /diagnose (enters from any phase when something breaks)
   + /ticket (side-quest — file a bug/feature ticket from any phase)
   + /newsroom (separate domain)
   + /lessons (periodic)
```

Each skill produces an artifact the next skill consumes.
Don't skip steps — every pipeline that went poorly started with the AI
building before looking.

## ETVLR Framework

Every data concept follows this lifecycle:

```
E (Extract)    → /scraper + /ingest Gate 1: scrape    (mcp__soria__scraper_run)
T (Transform)  → /ingest Gates 2-4: group, schema,    (schema_manage /
                 parse/detect, extract, validate       schema_mappings /
                                                       parse_pdf / detection_run /
                                                       agent_extract or extraction_run)
V (Value Map)  → /map: normalize values to canonicals (mcp__soria__value_manage)
L (Load)       → /ingest Gate 5: publish to staging   (mcp__soria__warehouse_manage
                                                       action="publish" → soria_duckdb_staging)
R (Represent)  → /dive: dbt marts model + manifest +  (dbt run locally →
                 TSX component + DivesPage entry +     mcp__soria__warehouse_query to
                 verify seed rows + methodology        validate, then git push + PR)
```

`/plan` orchestrates the phases. `/verify` runs after each.

## Reversibility model

All write-path skills (`/scraper`, `/ingest`, `/map`, `/parent-map`, `/dive`,
`/promote`) write directly to shared state — there are no isolated envs
to "switch to." The safety net is:

1. **Soft-delete.** Every `Base` ORM model has `deleted_at` / `deleted_by`.
   The `do_orm_execute` listener filters soft-deleted rows from normal
   reads. `SOFT_DELETE_CASCADES` propagates the delete down required
   relationships. Undo via `mcp__soria__database_mutate` setting
   `deleted_at = NULL`.
2. **Audit trail.** `PipelineEvent` captures every create/update/delete
   with actor + timestamp. Read via `mcp__soria__pipeline_activity` /
   `pipeline_history` / `pipeline_cascade`.
3. **PR-gated warehouse promotion.** Prod MotherDuck
   (`soria_duckdb_main`) is written to only by CI on PR merge. Staging
   (`soria_duckdb_staging`) is the working surface.

Read-only skills (`/status`, `/verify`, `/plan`, `/newsroom`, `/lessons`,
`/preview`, `/ticket`) don't change state but should surface the current
shared-state position in their output.

## Quick reference

- **Principles** in `ETHOS.md` — the source of truth
- **Tool surface** in `MCP_TOOL_MAP.md` — what every `mcp__soria__*` call does
- **Artifacts** in `~/.soria-stack/artifacts/` — state passed between skills
- **Gates** in every skill — hard stops where the human must review
- **Completion status** — every skill ends with DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT
- **Local dev** — use `/dev-dives` for frontend-only dive work at `https://dev.soriaanalytics.com` against the prod DBOS API + Clerk. No local backend is needed for dive frontend iteration.
