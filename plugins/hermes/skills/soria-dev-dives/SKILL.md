---
name: soria-dev-dives
description: 'Soria Stack Hermes skill for dev-dives. Use when setting up, repairing, or verifying the Soria dev HTTPS dive frontend at https://dev.soriaanalytics.com in Hermes, especially frontend-only dive iteration against the remote prod API, Vite/MotherDuck env alignment, or empty dashboard grids caused by wrong runtime/catalogs. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/dev-dives/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Dev Dives

Hermes adapter for upstream Soria-stack skill `dev-dives`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-dev-dives`
- Upstream source: `plugins/soria-stack/skills/dev-dives/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Dev Dives

Hermes adaptation of `Soria-Inc/soria-stack` `/soria-dev-dives`.

Read `../../references/hermes-adapter.md`, then read the target repo's
`AGENTS.md` and `CLAUDE.md`.

Use this for the local dev HTTPS mode used to iterate on Soria dive frontends:
`https://dev.soriaanalytics.com` served by local Vite, with API calls proxied
to the remote prod backend. This is different from `dev-env`, which starts a
full local backend/frontend stack, and from `browse`, which handles browser
auth, screenshots, console, and network evidence after the runtime is sane.

## Runtime Contract

- Use bare `https://dev.soriaanalytics.com/...` for Soria Clerk auth and final
  dive QA. The explicit `:5189` URL is diagnostic only.
- Vite must run from the intended app worktree's `frontend/` directory.
- Frontend-only dive iteration proxies `/api` to
  `https://cameron-soria.cloud.dbos.dev`.
- Set the MotherDuck catalogs explicitly:
  `VITE_MOTHERDUCK_STAGING=soria_duckdb_staging` and
  `VITE_MOTHERDUCK_PROD=soria`.
- Do not treat an empty grid as deleted dbt tables until the served Vite env
  and warehouse row counts have been checked.

## Preflight

From the app worktree root:

```bash
pwd
git status --short --branch
lsof -nP -iTCP:5189 -sTCP:LISTEN || true

for pid in $(lsof -tiTCP:5189 -sTCP:LISTEN 2>/dev/null || true); do
  ps -p "$pid" -o pid,ppid,lstart,command
  lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n/cwd: /p'
done

curl -skI --max-time 3 https://dev.soriaanalytics.com/ | head -n 12 || true
curl -skI --max-time 3 https://dev.soriaanalytics.com:5189/ | head -n 12 || true
curl -sk https://dev.soriaanalytics.com/src/api/dashboardClient.ts \
  | rg -o 'VITE_API_PROXY_TARGET[^,]+|VITE_MOTHERDUCK_STAGING[^,]+|VITE_MOTHERDUCK_PROD[^,]+' || true
```

Expected:

```text
VITE_API_PROXY_TARGET": "https://cameron-soria.cloud.dbos.dev"
VITE_MOTHERDUCK_PROD": "soria"
VITE_MOTHERDUCK_STAGING": "soria_duckdb_staging"
```

## Start Or Repair

Stop only the Vite listener on `5189`. Do not kill Python backends unless the
user asked for full local dev stack repair.

```bash
set -e
for pid in $(lsof -tiTCP:5189 -sTCP:LISTEN 2>/dev/null || true); do
  echo "stopping vite pid $pid"
  ps -p "$pid" -o pid,ppid,command || true
  kill "$pid" || true
done
sleep 1

mkdir -p .dev
(
  cd frontend
  VITE_API_PROXY_TARGET=https://cameron-soria.cloud.dbos.dev \
  VITE_MOTHERDUCK_STAGING=soria_duckdb_staging \
  VITE_MOTHERDUCK_PROD=soria \
  nohup python3 -c 'import os,sys; os.setsid(); os.execvpe(sys.argv[1], sys.argv[1:], os.environ)' \
    ./node_modules/.bin/vite --port 5189 \
    > ../.dev/dev-dives-vite.log 2>&1 < /dev/null &
  echo $! > ../.dev/dev-dives-vite.pid
)

sleep 2
lsof -nP -iTCP:5189 -sTCP:LISTEN
tail -n 60 .dev/dev-dives-vite.log
```

Then rerun the preflight. The served Vite module is the source of truth; `ps`
alone is not enough.

If the repo has a maintained `make dev-https-prod` target that sets the same
three env vars, use it. If that target omits the MotherDuck vars, prefer the
explicit command above and consider fixing the Makefile separately.

## Empty Grid Triage

1. Confirm the left-sidebar data badge is on the expected environment.
2. Confirm `dashboardClient.ts` was served with the expected env vars.
3. Query the mart directly with the available Soria warehouse tool:

```sql
SELECT COUNT(*) AS rows
FROM soria_duckdb_staging.main_marts.<mart_name>;
```

Only call it missing data after the selected catalog is proven absent or empty.

## Hand Off To Browse

After setup, hard-refresh existing browser tabs. Use `browse` (the
`agent-browser` CLI) for Clerk login, screenshots, console/network capture,
and interaction testing — named sessions keep you signed in. If
`agent-browser` shows the sign-in form, run the one-time login flow in
`browse` rather than restarting Vite again.

## Failure Modes

- Bare host connection refused: Vite is down or `pf` is not redirecting `443`
  to `5189`.
- Bare host down, explicit `:5189` works: rerun local HTTPS setup
  (`make dev-https-setup` or `scripts/setup-local-https.sh`) with sudo.
- `No Rows To Show`: suspect wrong catalog/env first, especially
  `VITE_MOTHERDUCK_STAGING=my_db` or a local API proxy to an older checkout.
- `/api/runtime` 404: not always fatal in remote-prod API mode.
- API 401: auth/session problem; run the one-time `browse` login flow to
  refresh the session cookies.
