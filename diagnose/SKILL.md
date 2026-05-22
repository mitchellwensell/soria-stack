---
name: diagnose
version: 3.1.0
description: |
  Diagnose and fix broken pipelines, silent failures, missing data, dive
  load failures, and infrastructure issues. Triage-first — observe before
  hypothesizing. Five modes: Silent Failure, Data Trace, Schema Mismatch,
  Infrastructure, Quality. Investigates via `mcp__soria__*` tools
  (database_query, warehouse_query, file_query, pipeline_activity /
  pipeline_history / pipeline_cascade). Ends with either an inline fix or
  a Linear ticket for backend changes.
  Use when something "isn't working", "returned wrong data", "said success
  but nothing happened", "is slow", "is missing rows", or a dive "won't
  load" or "shows NaN". Proactively invoke this skill when the user
  reports a failure or unexpected behavior. (soria-stack)
benefits-from: [status, ingest, dive, verify]
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---

## Preamble (run first)

```bash
mkdir -p ~/.soria-stack/artifacts
echo "SKILL: diagnose"
echo "---"
echo "Git state (soria-2):"
git status --short 2>&1 | head -10 || echo "  (not in soria-2 checkout)"
echo "---"
echo "Recent debug artifacts:"
ls -t ~/.soria-stack/artifacts/diagnose-*.md 2>/dev/null | head -3 || echo "  (none)"
```

Also run `mcp__soria__pipeline_activity(limit=20)` — if the failure is
recent, the triggering write usually shows up in the last 20 events.

Read `ETHOS.md`.

## Skill routing (always active)

When the user's intent shifts away from debugging, invoke the matching skill:

- User wants to rebuild the pipeline → invoke `/ingest`
- User wants to re-map values → invoke `/map`
- User wants to verify data correctness → invoke `/verify`
- User wants to check what exists → invoke `/status`
- User wants to promote after fixing → invoke `/promote`

**After /diagnose completes with a fix**, suggest `/verify` to confirm the fix worked.

---

# /diagnose — "Why isn't this working?"

You are a diagnostic investigator. Your job is to find root causes, not guess.
**Observe first, hypothesize second.** The AI's #1 debugging mistake is jumping
to a hypothesis before looking at the actual data.

---

## Rule Zero: Schema Discovery Before Any Query

**NEVER query a column without first confirming it exists.** This is the single
most common AI debugging mistake — querying columns that exist in Pydantic models
or ORM classes but not in the actual database table.

Before ANY diagnostic query, run:

```
mcp__soria__database_query(sql="
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = '{table}' AND table_schema = 'public'
  ORDER BY ordinal_position
")
```

For warehouse tables:

```
mcp__soria__warehouse_query(sql="
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_schema = '{schema}' AND table_name = '{table}'
")
```

For dive manifests — read the file directly:

```bash
cat frontend/src/dives/manifests/{dive-id}.manifest.ts
```

If you skip this step and get a "column does not exist" error, that's on you.

---

## Rule Zero-and-a-Half: Confirm Your Branch Matches Prod

If you're debugging behavior observed in prod (or staging), confirm your
checkout's code matches what's running before reading any source files.
The user's branch may be days or weeks behind main, and you'll waste
time diagnosing dead code.

```bash
git fetch origin main
git log --oneline HEAD..origin/main -- {subsystem-path}/ | head
```

If main has commits to the relevant subsystem that your branch doesn't,
your file reads are diagnosing the wrong code. Read the prod version
instead:

```bash
git show origin/main:path/to/file.py
# or work from an existing worktree that's on main:
ls .claude/worktrees/
```

Skip this only when the user has explicitly said "I want to debug local
changes" — anything else, assume prod.

---

## Step 1: Triage — What kind of failure?

Ask one question: **What did you expect to happen, and what happened instead?**

Then classify into one of five modes:

| Symptom | Mode | The problem |
|---------|------|-------------|
| "It said success but nothing happened" | **Silent Failure** | MCP tool returned success but produced no output |
| "Wrong data / missing rows / NULLs" | **Data Trace** | Data exists somewhere but is wrong or incomplete |
| "Column/table doesn't exist" | **Schema Mismatch** | Migration not applied, wrong table name, stale schema |
| "Slow / timeout / connection error / dive won't load" | **Infrastructure** | MotherDuck cold start, DBOS Cloud, WASM cold start, event relay |
| "Extraction produced bad data" | **Quality** | LLM output wrong, truncated, or incomplete |

Pick the mode. Say it out loud: "This looks like a **silent failure** — let me trace it."

---

## Mode 1: Silent Failure

Operations that report success but produce nothing. The most dangerous failure
type because the AI will initially believe the "OK" response.

**Core rule: Never trust tool success alone. Verify independently.**

### Diagnostic steps

1. **What tool was called?** Note the exact invocation and params.

2. **Verify the output exists independently:**

   - `mcp__soria__scraper_run` said "started" → check for downloaded files:
     ```
     mcp__soria__database_query(sql="
       SELECT id, name, status, created_at FROM files
       WHERE scraper_id = '{scraper_id}' ORDER BY created_at DESC LIMIT 10
     ")
     ```

   - `mcp__soria__extraction_run` said "started for N files" → check for child files:
     ```
     mcp__soria__database_query(sql="
       SELECT id, name, status FROM files
       WHERE parent_file_id IN (SELECT id FROM files WHERE group_id = '{group_id}')
       ORDER BY created_at DESC LIMIT 20
     ")
     ```

   - `mcp__soria__warehouse_manage(action="publish")` said OK → check bronze:
     ```
     mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM soria_duckdb_staging.bronze.{table_name}")
     ```

   - `dbt run` said "1 of 1 OK" → query the materialized marts row:
     ```
     mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM soria_duckdb_staging.main_marts.{model}")
     ```

   - `dbt test` said pass → read run-results:
     ```bash
     cat frontend/src/dives/dbt/target/run_results.json | jq '.results[] | select(.status != "pass")'
     ```

3. **Check the audit trail:** `PipelineEvent` knows what actually committed.
   ```
   mcp__soria__pipeline_history(entity_type="{Group|File|Scraper}", entity_id="{id}")
   ```
   Compare against what you expected. If the event isn't there, the write
   never committed — retry or diagnose further.

4. **Known causes:**

   - **Soft-delete filter hiding rows:** The `do_orm_execute` listener hides
     rows with `deleted_at IS NOT NULL`. If a file was soft-deleted out of
     reach, it won't appear in `database_query`. Query with
     `deleted_at IS NOT NULL` to see them.
   - **Stale warehouse table:** `warehouse_manage(action="publish")` may have
     soft-deleted the old table record but bronze is still the old shape.
     Re-publish with `force=True`.
   - **Upstream event relay crash:** Cloudflare Durable Object event relay
     (`workers/event-relay`) may have dropped the notify event — the row
     landed but downstream subscribers never heard about it.

5. **Check prior sessions for this exact failure:**
   ```
   mcp__openclaw__mempalace_search(query="silent failure {tool_name}")
   ```

### Disposition
- Backend bug (error swallowing, race condition) → **Ticket**
- Stale artifact blocking → **Fix inline** (`force=True` re-publish, or unpublish + republish)
- Soft-delete hiding expected row → **Fix inline** (flip `deleted_at` back via `database_mutate`)
- Upstream event relay issue → **Ticket** + manual re-trigger

---

## Mode 2: Data Trace

Wrong data, missing rows, unexpected NULLs, or duplicate rows. Requires
multi-layer tracing.

### Diagnostic steps

1. **Identify the layer the user is seeing the problem at:**
   - Dive (browser) → user-facing
   - dbt marts → dive SQL layer
   - dbt intermediate / staging → transformation layers
   - Bronze (staging warehouse) → raw published data
   - Postgres state → pipeline state

2. **Trace backwards through every layer.** At each layer, get a row count
   and check for the specific problem:

   ```
   # Layer 5: Marts (what the dive queries)
   mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM soria_duckdb_staging.main_marts.{model}")

   # Layer 4: Intermediate (joins + logic)
   mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM soria_duckdb_staging.main_intermediate.{model}")

   # Layer 3: Staging (cleaned + typed)
   mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM soria_duckdb_staging.main_staging.{model}")

   # Layer 2: Bronze (raw published data)
   mcp__soria__warehouse_query(sql="SELECT COUNT(*) FROM soria_duckdb_staging.bronze.{table}")

   # Layer 1: Postgres pipeline state
   mcp__soria__database_query(sql="
     SELECT COUNT(*) FROM files
     WHERE group_id = '{group_id}' AND status = 'published'
   ")
   ```

3. **Find where the data disappears or goes wrong.** The layer where counts
   diverge or values change is where the bug lives.

4. **Common root causes by divergence point:**
   - Bronze has rows, staging doesn't → staging SQL filter too aggressive
   - Staging has rows, intermediate doesn't → join condition wrong
   - Intermediate has rows, marts don't → dbt model staleness (run `dbt run --select {model}`)
   - Marts has rows, dive shows nothing → manifest filter value drift —
     the manifest references a filter value that doesn't exist in the data:
     ```bash
     cat frontend/src/dives/manifests/{dive}.manifest.ts
     ```
     ```
     mcp__soria__warehouse_query(sql="
       SELECT DISTINCT {filter_column}
       FROM soria_duckdb_staging.main_marts.{model}
     ")
     ```
   - Data loaded 2-3x → repeated publish without dedup.
     Check `_source_file` column for duplicates.

### Disposition
- SQL bug in staging/intermediate/marts → **Fix inline** (edit the dbt model, `dbt run`)
- dbt model stale → **Fix inline** (`dbt run --select {model}`)
- Manifest filter drift → **Fix inline** (update manifest values list)
- Extraction produced bad data → Invoke `/ingest` to fix extractor
- Value mapping wrong → Invoke `/map`
- Duplicate publish → **Fix inline** (`warehouse_manage(action="unpublish")`, then republish)

---

## Mode 3: Schema Mismatch

Column doesn't exist, table not found, or queries return unexpected structure.

### Diagnostic steps

1. **Get the actual schema** (Rule Zero):
   ```
   mcp__soria__database_query(sql="
     SELECT column_name, data_type
     FROM information_schema.columns
     WHERE table_name = '{table}' AND table_schema = 'public'
     ORDER BY ordinal_position
   ")
   ```

2. **Compare against what was expected.** Common mismatches:
   - **Computed property, not a DB column:** e.g., something that exists as a
     Python `@property` but not in the database. Check the model code.
   - **Migration not applied:** Column exists in code but not in the database.
     Check Alembic migration status.
   - **Wrong table name:** dbt layers live at
     `soria_duckdb_staging.main_staging.{m}`,
     `soria_duckdb_staging.main_intermediate.{m}`, and
     `soria_duckdb_staging.main_marts.{m}` (prod counterparts under
     `soria_duckdb_main`). Bronze tables live at
     `soria_duckdb_staging.bronze.{table}`.
   - **Staging/prod badge mode:** the frontend routes queries to staging or
     prod via the amber/green `EnvironmentBadge` (default prod), backed by
     the `X-SQLMESH-ENV` header (legacy name). If the user reports "data
     looks wrong" on `dev.soriaanalytics.com`, check which badge mode is
     active before chasing it as a pipeline bug.

3. **For warehouse schema issues:**
   ```
   mcp__soria__warehouse_query(sql="
     SELECT table_schema, table_name
     FROM information_schema.tables
     WHERE table_name ILIKE '%{keyword}%'
   ")
   ```

### Disposition
- Missing migration → **Ticket** (need Alembic migration + deploy)
- Wrong table/column name → **Fix inline** (correct the query)

---

## Mode 4: Infrastructure

Timeouts, connection errors, slow queries, cold starts, dive load failures.

### Subsystem catalog

| System | Common failure | Fix |
|--------|---------------|-----|
| **Postgres (Neon-backed)** | Pool exhaustion, SSL drops | Transient — retry once; if persistent, ticket |
| **MotherDuck (DuckDB)** | Cold start 30-47s after idle | Architectural — not a bug unless causing gateway timeout |
| **GCS (file storage)** | Object 404, cross-region latency | Check object exists; if transient, retry |
| **DBOS Cloud** | Worker restart, PG wire timeout | Check DBOS dashboard; ticket if persistent |
| **Clerk JWT** | Stale token, admin/user role mismatch | Re-login at `https://dev.soriaanalytics.com`; if role issue, check user metadata |
| **Durable Object event relay** (`workers/event-relay`) | Event dropped, relay stuck | Check Cloudflare worker logs; re-trigger event |
| **WASM cold start** (dive) | First load takes ~20s to download/compile client | Normal — distinguish from "broken" (dual-mode loading) |
| **Postgres wire proxy** (dive fallback) | 30s statement timeout | Reduce query complexity or add marts aggregation |
| **Local vite** (`dev.soriaanalytics.com`) | "The frontend is down" / `curl https://dev.soriaanalytics.com/` returns 000 | `make dev-https` runs foreground and dies with its shell. Restart detached (see step 7). |
| **Staging/prod badge** | "Data looks wrong" | Check the badge mode first (amber staging / green prod). Toggling between them routes to different MotherDuck databases. Default is prod. |

### Diagnostic steps

1. **Identify the subsystem** from the error message, URL pattern, or stack trace.

2. **For slow dive queries:** Check marts table exists and dbt is fresh:
   ```
   mcp__soria__warehouse_query(sql="
     SELECT table_name FROM information_schema.tables
     WHERE table_schema = 'main_marts'
   ")
   ```
   ```bash
   cat frontend/src/dives/dbt/target/manifest.json | jq '.metadata.generated_at'
   ```

3. **For connection errors:** Almost always transient. Retry once. If
   persistent, likely Postgres pool exhaustion or DBOS Cloud worker issue.

4. **For MotherDuck cold start:** First query after idle takes 30-47s.
   Not a bug. If it causes gateway timeouts, ticket for timeout config.

5. **For dive "won't load" reports:** Distinguish the two load modes —
   ```
   Is it: (a) first paint blank/stuck for >5s?      → Postgres proxy failing
          (b) first paint OK but stale after?       → WASM upgrade failing
          (c) worked once, now broken on refresh?   → Session cache poison
   ```
   Check the browser console and the network tab. WASM cold start for the
   first ~20s is normal — the Postgres proxy must return data first.

6. **For Durable Object event relay issues:**
   ```bash
   cd workers/event-relay && wrangler tail
   ```

7. **For "frontend is down" / vite dead:** Probe, then restart detached.
   `make dev-https` runs vite in the foreground — it dies with the shell
   that launched it. Use `nohup + disown` to keep it alive past the
   current tool session.
   ```bash
   curl -sk -o /dev/null -w "%{http_code}\n" https://dev.soriaanalytics.com/
   lsof -ti:5189 >/dev/null && echo "vite up" || echo "vite down"

   # Restart (from soria-2 repo root):
   cd frontend && nohup npx vite --port 5189 > /tmp/soria-vite.log 2>&1 &
   disown
   # Stop later:  kill $(lsof -ti:5189)
   ```
   If this keeps happening, the real fix is patching the `dev-https`
   Makefile target to daemonize the way `run-dev` does (via
   `scripts/run-dev.sh`). Worth a `/ticket`.

### Disposition
- Transient → **Retry** (no action needed)
- Stale dbt marts → **Fix inline** (`dbt run --select {model}`)
- Manifest/data drift → **Fix inline** (update manifest filter values)
- Pool exhaustion → **Ticket** (container cleanup or pool config)
- Event relay stuck → **Ticket** + manual re-trigger
- WASM cold start confused for breakage → **Document** (not a bug)
- Vite died → **Fix inline** (nohup restart). If recurrent, **Ticket** the Makefile.
- "Data looks wrong" but badge is on prod (or staging) → **Check badge** before deeper investigation.

---

## Mode 5: Quality

Extraction produced wrong, incomplete, or truncated data.

### Diagnostic steps

1. **Get the source file and extraction output side by side:**
   ```
   mcp__soria__file_query(file_id="{file_id}")                  # source metadata
   mcp__soria__database_query(sql="
     SELECT id, name, storage_key, status
     FROM files WHERE parent_file_id = '{file_id}'
   ")
   ```

2. **Check for known extraction failure patterns:**
   - **Truncated JSON:** LLM output hit token limit on large PDFs. Look for
     incomplete rows or malformed CSV.
   - **Missing pages:** Detection may not have flagged all relevant pages.
     Check detection results:
     ```
     mcp__soria__database_query(sql="
       SELECT file_id, detected_pages
       FROM detection_results WHERE file_id = '{file_id}'
     ")
     ```
   - **Wrong schema applied:** Extractor used wrong column set. Compare
     extraction CSV headers against group schema columns.

3. **Spot-check 3 values** from the source against the extraction output.
   Don't check totals or obvious values — check middle-of-table specifics.

### Multi-stage LLM pipelines — trace every stage in Logfire

If the bad output came from an LLM pipeline with more than one agent
stage, the DB row shows ONLY the final state. An upstream agent may
have produced something good that a downstream agent silently overwrote.

Logfire is the source of truth here. Pull every `agent run` span in the
relevant trace window and inspect each agent's actual input + structured
output:

```sql
SELECT
  start_timestamp,
  attributes->>'gen_ai.agent.name' AS agent,
  attributes->'final_result' AS output,
  attributes->'pydantic_ai.all_messages' AS messages
FROM records
WHERE trace_id = '{trace_id}'
  AND span_name = 'agent run'
ORDER BY start_timestamp
```

Notes:
- Use `attributes->'pydantic_ai.all_messages'` for full prompt/response.
  The `events` field shows `<elided>` for content — that's an OTel
  exporter detail, not real redaction.
- Content matching scrub-list keywords (e.g. "Auth", "Secret") will
  appear as `[Scrubbed due to '<keyword>']`; note them and move past.
- Walk the agents in timestamp order. The bug lives at the stage where
  a clean upstream output became a bad downstream one. Always confirm
  *which* agent owns the bad output before editing any prompt.

### Disposition
- Extractor bug → Invoke `/ingest` (fix extractor, dry-run with `extraction_run(test=True, code=...)`)
- Detection missed pages → **Fix inline** (adjust detection prompt, re-run)
- LLM truncation → **Ticket** if systemic, or split extraction into smaller chunks
- Wrong agent stage edited → **Re-diagnose** via Logfire trace; only edit the prompt of the agent that actually produced the bad output

---

## Check for the Interactive Agent

Before filing a ticket or force-fixing something, check whether the Modal
sandbox interactive agent is already working on it. It listens for comments
on PRs and investigations on Linear issues and replies in real time.

Use signals you can observe without Linear MCP:

```bash
# auto-fix branches on origin matching the ENG-ticket you're debugging
git branch -r | grep -E "auto-fix/ENG-"

# Open PRs from the agent's service account
gh pr list --state open --json number,author,title,headRefName
```

Linear inspection is owned by `/ticket` — if you need a deeper check
(duplicate/regression/active agent run with `agent` label), **invoke
`/ticket`** and let it do the Linear query.

If an active agent run is investigating the same failure, **defer to it** —
report that the agent is on it and move on. Don't duplicate work or race
the agent.

---

## Filing a Ticket

When the disposition is **Ticket**, **invoke `/ticket`** — don't file directly.
`/ticket` owns all Linear writes, checks for duplicates, scans for active
interactive-agent runs, and classifies priority consistently. Pass it your
diagnostic findings so it can write a complete repro + root-cause ticket
without re-discovering the problem.

### When to ticket vs fix inline

| Situation | Action |
|-----------|--------|
| Backend code change needed (error swallowing, wrong logic) | invoke `/ticket` |
| Infrastructure config (pool size, timeout, container cleanup) | invoke `/ticket` |
| SQL model fix (wrong join, missing filter) | Fix inline (edit dbt model, `dbt run`) |
| Stale dbt marts | Fix inline (`dbt run --select {model}`) |
| Manifest filter value drift | Fix inline (update manifest) |
| Re-extraction with adjusted parameters | Fix inline via `/ingest` |
| Soft-deleted row hiding expected data | Fix inline (`database_mutate` flip `deleted_at`) |
| Systemic LLM extraction failure | invoke `/ticket` |
| Durable Object event relay stuck | invoke `/ticket` |
| Modal sandbox agent stuck PR | invoke `/ticket` (agent will pick it up) |
| MCP tool gap (needed action has no tool) | invoke `/ticket` (classify as "Missing feature") |

After `/ticket` files the issue, return to `/diagnose` if the user wants
to continue debugging, or close out with a report.

---

## Searching Prior Sessions

Before deep-diving, check if this exact issue has been debugged before:

```
mcp__openclaw__mempalace_search(query="{description of the problem}")
```

If a prior session found the root cause, skip straight to the fix or ticket.
Don't re-debug what's already been diagnosed.

---

## Artifact Output

```bash
cat > ~/.soria-stack/artifacts/diagnose-$(date +%Y%m%d-%H%M%S).md << 'ARTIFACT'
# Debug Report: [Short description]

## Symptom
[What the user reported]

## Triage
Mode: [Silent Failure | Data Trace | Schema Mismatch | Infrastructure | Quality]

## Investigation
[What you checked, what you found at each layer]

## Root Cause
[The actual problem — be specific]

## Disposition
[Fix inline | Ticket | Invoke /ingest | Invoke /map | Defer to interactive agent]

## Action Taken
[What was done — SQL fix, ticket created (ENG-XXX), dbt run, etc.]

## Outcome
Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
Lesson: [What was unexpected or worth remembering]
ARTIFACT
```

---

## Anti-Patterns

1. **Hypothesizing before observing.** Don't say "this is probably a schema issue"
   before running a single query. Look first.

2. **Querying columns without schema discovery.** Rule Zero exists because the AI
   gets this wrong in almost every debug session. `information_schema` first.

3. **Trusting MCP tool success.** A publish returning OK doesn't mean data
   landed. Verify independently at the destination AND check the
   `PipelineEvent` audit trail.

4. **Checking one layer and declaring success.** Data exists in Postgres but not
   MotherDuck? That's not "data exists." Trace all layers.

5. **Saying "this needs a ticket" without creating one.** If the disposition is
   Ticket, invoke `/ticket` right now. Don't defer.

6. **Re-debugging known issues.** Search prior sessions first. If it's been
   diagnosed, skip to the fix.

7. **Guessing the fix without confirming the cause.** "Let me try re-running dbt"
   is not debugging. Find the root cause, then fix it.

8. **Racing the interactive agent.** If the Modal sandbox agent has an active
   run on the same PR or ticket, defer to it. Don't comment, don't fix, don't
   ticket — report and move on.

9. **Calling WASM cold start a bug.** First dive load takes ~20s to warm the
   DuckDB-WASM client. The Postgres proxy fallback must return data in the
   meantime. If first paint is slow but data arrives, that's normal.

10. **Hard-deleting to "fix" broken state.** Everything is soft-delete
    reversible. Flip `deleted_at` via `database_mutate` or use a `force=True`
    republish — never `DELETE FROM` against shared Postgres.
```
