---
name: news-debug
version: 0.1.0
description: |
  Explain what happened to a news article or event in the v2 news
  pipeline. Use when articles duped, failed to cluster, got the wrong
  label, when two events look like they should be one, or when you need
  to trace a Correspondent → Editor → Review → Publisher run end-to-end.
  Produces an ASCII pipeline flow + the exact decision point + the
  prompt/threshold that drove it + a fix recommendation.

  Read-only investigation across Postgres state (via `mcp__sumo__*`),
  Logfire traces (via `mcp__logfire__*`), and the v2 pipeline source in
  `soria/news/`. Knows the pipeline shape, span names, prompt files, and
  thresholds — so you can hand it an event ID or "these two should be
  one" and get a concrete answer instead of guessing.

  Use when:
    - two events that should be one event (cluster miss)
    - one event with two articles that should have been distinct (over-cluster)
    - an article didn't cluster at all (orphan)
    - an event has a weird label or summary
    - "what did this scan run do?" type questions
    - newsletter showed something unexpected — trace it backward

  Do NOT use for: building dives (/dive), general app debugging
  (/investigate), warehouse data quality (/diagnose). (soria-stack)
benefits-from: [diagnose, ticket]
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# News Debug

Trace a news pipeline outcome back to the decision that produced it. Read-only investigation across Postgres state + Logfire traces + the v2 pipeline source code in the `soria-2` repo. The skill knows the pipeline shape, the span names, the prompt files, and the thresholds — so you can hand it an event ID or "these two should be one" and get a concrete answer instead of guessing.

## Inputs

Accepted in order of precedence (if multiple, use the most specific):

1. **Event IDs** (UUIDs from `news_events.id`) — most common: "these two should be one"
2. **Article IDs** (UUIDs from `news_articles.id`) — "why didn't this cluster"
3. **Run ID** (UUID from `news_events.created_by_run_id`) — "what did this scan do"
4. **Free-text headlines / screenshots** — resolve to articles by `title ILIKE '%fragment%'` first, then proceed as Article IDs

## Pipeline shape (memorize this)

```
scheduled_news_scan
  └─ run_news_scan_v2
       ├─ fetch (EventRegistry trusted/core/policy + CMS scrapers)
       ├─ run_correspondent (per source, parallel)
       │    ├─ Correspondent-Extract  (Gemini-3.1-Pro) → Articles + relevance score
       │    ├─ Correspondent-Decide   (Gemini-3.1-Pro) → update existing event vs create
       │    └─ Correspondent-Verify   (GPT-5.5)        → confirm any "update" decision
       ├─ run_editor   (Gemini)  → group "create" articles into draft events within run
       ├─ run_review   (pgvector + GPT-5.5 verifier) → catch drafts that should have been updates
       └─ Publisher    (GPT-5.5) → write/revise event label + summary
```

## Source-of-truth files (in the `soria-2` repo)

| Concern | File |
|---|---|
| Top-level workflow | `soria/news/workflows/news_scan.py` (`run_news_scan_v2`) |
| Per-article extract + decide | `soria/news/news_correspondent.py` |
| Within-run grouping | `soria/news/news_editor.py` |
| Cross-run pgvector recheck | `soria/news/news_review.py` |
| Final summary writer | `soria/news/news_publisher.py` |
| **All decision prompts** | `soria/news/news_prompts.py` |
| ORM models | `soria/news/news_models.py` |

Key constants in `news_prompts.py`:
- `REVIEW_COSINE_MATCH = 0.85` (shortlist threshold; distance = 1 − this = 0.15)
- `REVIEW_DISTANCE = 0.15` (above this → never sent to verifier)
- `REVIEW_AUTO_MERGE_DISTANCE = 0.08` (below this → auto-merge, skip verifier)
- `MIN_RELEVANT_SCORE = 6`

## Logfire span names to grep

| Stage | Span name |
|---|---|
| Workflow root | `scheduled_news_scan` / `run_news_scan_v2` |
| Correspondent fan-out | `run_correspondent` |
| Per-article extract | `agent run` with `final_result.agent_name = "Correspondent-Extract"` |
| Per-article decide | `agent run` with `final_result.agent_name = "Correspondent-Decide"` |
| Per-update verify | `agent run` with `final_result.agent_name = "Correspondent-Verify"` |
| Editor batch | `run_editor`, `editor done: %d create-articles → %d draft events` |
| Review summary | `run_review`, `review: %d auto-merged, %d verifier hits (%d rejected), %d total redirects` |
| Review rejection (per draft) | `review verifier rejected redirect for draft %d → %s. Reason: %s` |
| Publisher | `agent run` with `final_result.agent_name = "Publisher"` |

All v2 traces share one `trace_id` per scan run. To find a run's trace_id from a `run_id`, query Logfire for the run's start time (from `news_events.created_at` of any event it produced) and grep for `scheduled_news_scan` near that time.

## Workflow

### 1. Resolve input

```sql
-- Event lookup
SELECT id, label, summary, event_date, created_at, created_by_run_id, source_url
FROM news_events
WHERE id IN ('<event_id>', ...);

-- Article lookup with source provenance
SELECT a.id, a.title, a.event_date, a.event_summary, a.event_id, a.created_at,
       s.source_domain, s.url, s.published_at, s.title AS source_title
FROM news_articles a LEFT JOIN news_sources s ON s.id = a.source_id
WHERE a.id IN ('<article_id>', ...);

-- Articles belonging to an event
SELECT a.id, a.title, a.created_at, s.source_domain
FROM news_articles a LEFT JOIN news_sources s ON s.id = a.source_id
WHERE a.event_id = '<event_id>'
ORDER BY a.created_at;
```

Use `mcp__sumo__database_query` (read-only, Postgres). Do NOT use `mcp__soria__database_query` unless you are explicitly investigating local dev state — sumo is prod.

Note: `mcp__sumo__database_query` rejects leading SQL comments (it parses `--` as DDL). Strip comments before sending.

### 2. Pull the Logfire trace

```sql
SELECT trace_id, start_timestamp, span_name, message
FROM records
WHERE service_name = 'soria'
  AND start_timestamp BETWEEN '<run_start - 1min>' AND '<run_start + 5min>'
  AND (span_name = 'scheduled_news_scan' OR span_name = 'run_news_scan_v2')
ORDER BY start_timestamp ASC LIMIT 5;
```

Use `mcp__logfire__query_run` with `project='soria-2'`. The trace_id is shared across the whole scan run.

### 3. Locate the decision points

For a cluster-miss case, the relevant spans are:

```sql
SELECT start_timestamp, span_name, message, substr(attributes::text, 1, 2000) AS attrs
FROM records
WHERE trace_id = '<trace_id>'
  AND service_name = 'soria'
  AND (
    (span_name = 'agent run' AND attributes::text LIKE '%Correspondent-Decide%'
       AND attributes::text LIKE '%<article-title-fragment>%')
    OR message LIKE 'editor done%'
    OR message LIKE 'review:%'
    OR message LIKE 'review verifier rejected%'
  )
ORDER BY start_timestamp ASC LIMIT 50;
```

`Correspondent-Decide` `final_result.observations` is the gold — it literally lists each pgvector neighbor the model saw, with the SAME BECAUSE / DIFFERENT BECAUSE reasoning and the final action.

### 4. Cross-reference the rule

When a decision was rule-driven, find the rule text in `soria/news/news_prompts.py` and cite the line. The most-referenced sections:

- `COMPARE_PROMPT` — the per-article decide rules (Step 2 PICK ACTION, RULES section)
- The "shared entity but different period → create" bullet around `news_prompts.py:320`, reinforced by the "Q4 vs Q1 earnings" example in the RULES section

Read the prompt at the cited line so the explanation quotes the actual text, not a paraphrase.

### 5. Render

Output format:

```
═══════════════════════════════════════════════════════════
NEWS-DEBUG REPORT — <short case summary>
═══════════════════════════════════════════════════════════

INPUT
  <article(s), event(s), or run(s) under investigation>

OUTCOME
  <what actually happened: split / merged / mislabeled / orphaned>

DECISION POINT
  Stage:       <Correspondent-Decide | Editor | Review | Publisher>
  Trace:       <logfire trace_id>
  Span:        <span name + timestamp>
  Rule fired:  soria/news/news_prompts.py:<line> — "<verbatim rule>"

EVIDENCE
  <log excerpt: Correspondent-Decide observations, Review counts, etc.>

ASCII FLOW
  <pipeline trace box diagram showing the relevant path>

VERDICT
  <one of: rule misapplied | embedding too far | context starvation |
   correct (data really is distinct) | retrieval miss | LLM judgment call>

RECOMMENDATION
  <prompt fix with target file:line | threshold tweak | file a ticket | nothing>
```

ASCII flow style: two parallel columns when comparing two runs, single column when explaining one outcome. Show the decision gate explicitly with a `← ✗ here` marker on the bad call.

### 6. Verdict guidance

| Symptom in logs | Likely verdict | Typical fix |
|---|---|---|
| Decide observation correctly named overlap but rule chose create | Rule misapplied | Prompt carve-out for the specific case class |
| Decide observations didn't mention the candidate at all | Retrieval miss (pgvector didn't return it) | Loosen `REVIEW_DISTANCE` or fix article-side embedding |
| Review log shows 0 auto-merged / few verifier hits when there should have been more | Embedding too far | Re-embed with richer text, or add structured cluster key |
| Decide observations are slim ("nothing concrete") | Context starvation | Extract more fields in Correspondent-Extract |
| Verifier rejection log explains why | Probably correct | Read the reason; if legitimate, no fix |

## Reference case — Kaufman Hall May 22 dupe

Use this as the canonical worked example.

**The bug:**
- Event `2b508bcc` (May 19, Fierce Healthcare: "Hospitals Lift March Margins to 2.9%…")
- Event `2f703c99` (May 21, Becker's Hospital Review: "Kaufman Hall…Revenue Up 5% in Q1…")
- Both are coverage of the same Kaufman Hall March 2026 National Hospital Flash Report

**Trace** `019e50335fec5284092dba92d08d0584` at `2026-05-22T15:00`. Correspondent-Decide span at `15:01:38` shows:

```
E[0] Hospitals Lift March Margins to 2.9% as Length of Stay Falls 2%
     SAME BECAUSE: Kaufman Hall national hospital data
     DIFFERENT BECAUSE: Q1 revenue 5% / outpatient 8%
                        vs March margins 2.9% / length of stay 2%
```

Decide chose `create` per the "shared entity but different period → create" rule in `COMPARE_PROMPT`. Review ran `0 auto-merged, 4 verifier hits (1 rejected), 3 total redirects` — the May 19 event wasn't in the 4 hits because the draft's (label, summary) embedding was ≥0.15 cosine distance from it.

**Fix shipped** in the soria-2 repo: added a "Bundled periodic releases are one event" bullet to `COMPARE_PROMPT` RULES section listing the known bundled periodic publications (Kaufman Hall NHFR, BLS monthly, CMS monthly, Strata, Premier).

## Hard rules for the agent running this skill

- **Read-only.** Never write to `news_articles`, `news_events`, or any prod table. No `database_mutate`.
- **Sumo, not soria.** Use `mcp__sumo__*` for prod investigation. `mcp__soria__*` is local dev.
- **14-day window.** Logfire retains 14 days. If the run is older, say so — don't fabricate.
- **Quote, don't paraphrase.** When you cite a prompt rule, paste the actual line. When you cite log evidence, paste the actual span attributes.
- **No fixes without confirmed root cause.** If the trace doesn't conclusively show why the outcome happened, report "inconclusive — need <X>" instead of guessing.
- **Sumo SQL hygiene.** `mcp__sumo__database_query` parses `--` at line start as DDL and rejects the whole query. Strip comments.
