# SoriaStack - Agent Skills for Soria Work

SoriaStack is the canonical skill pack for Soria Analytics agent workflows.
It is not a generic prompt library. It captures how the team wants agents to
operate on Soria's data platform, dives, developer tooling, QA, promotion, and
retrospectives.

The pack supports Claude-style skills, Codex plugin skills, and generated
Hermes skills:

- Claude-facing skills live as top-level directories such as `status/`,
  `dive/`, and `lessons/`.
- Codex-facing wrappers live under `plugins/soria-stack/skills/`.
- Hermes-facing wrappers are generated under `plugins/hermes/skills/` with
  `soria-*` names to avoid collisions with bundled Hermes skills.
- Shared behavior should be kept in sync across both surfaces when both tools
  need the lesson.

## Operating Philosophy

1. **MCP first for platform data work.** Soria pipeline/product work runs
   through the `soria` MCP server (`mcp__soria__*`). There is no `soria` CLI
   fallback for pipeline operations. Engineering environment work is different:
   app repo workflows may use `soria env ...` and Makefile targets to create
   branch-local dev environments.
2. **Shared state, reversible writes.** MCP writes hit shared Postgres and
   `soria_duckdb_staging`. Prefer reversible operations with audit trails over
   fake local isolation. Postgres rows use soft deletes and `PipelineEvent`
   history.
3. **Git-native product work.** dbt SQL, manifests, React dive components,
   verify seeds, and skill text are authored locally in git, reviewed in diffs,
   and promoted through PR/CI.
4. **Evidence before claims.** Agents should show rows, counts, browser
   evidence, traces, or diffs before saying work is correct.
5. **Skills are executable team memory.** Add or update a skill when a workflow
   is repeatable and Soria-specific enough that the next agent should not
   rediscover it from scratch.
6. **Lessons close the loop.** `/lessons` turns concrete session evidence into
   durable skill updates in this repo.

## Architecture

```
                  +-------------------------------------------+
                  |  mcp__soria__* tools (one shared MCP)     |
                  |  scraper_run, detection_run, extraction   |
                  |  validation, schema_manage, value_manage  |
                  |  warehouse_manage, warehouse_query        |
                  +------------------+------------------------+
                                     |
                                     v
        +-----------------------+---------------------------+
        |  shared Postgres      |  soria_duckdb_staging     |
        |  scrapers/groups/     |  bronze + dbt staging/    |
        |  files/schemas        |  intermediate/marts       |
        +-----------------------+---------------------------+
                                     ^
                                     | local dbt run
                      +--------------+---------------+
                      |  frontend/src/dives/dbt/     |  <- git
                      |  staging -> intermediate ->  |
                      |  marts, verifications seed   |
                      +--------------+---------------+
                                     |
                                     v
                    https://dev.soriaanalytics.com
                    local vite -> prod DBOS API + Clerk
                    staging/prod badge -> X-SQLMESH-ENV
                                     |
                          git push -> PR -> CI
                                     |
                                     v
                          soria_duckdb_main (prod)
```

Classic backend-rendered dashboards are retired. Modern dives are file-based:
dbt models, manifests, React components, and verification rows live under the
Soria app repo. The browser switches between staging and prod through the
environment badge.

## Skill Types

SoriaStack can contain two kinds of skills:

- **Pipeline/product skills** for Soria data work: inventory, planning,
  ingestion, value mapping, dives, verification, browser review, promotion, and
  release workflows.
- **Developer skills** for Soria-specific engineering workflows: local setup,
  CI debugging, MCP debugging, frontend runtime checks, test protocol, release
  hygiene, or repo maintenance.

Developer-focused skills are welcome when they encode repeatable
Soria-specific behavior. Avoid adding generic engineering advice that would
apply equally to any codebase.

## Available Skills

Invoke skills by name, for example `/status` or `/dive`.

| Skill | What it does |
|-------|-------------|
| `/browse` | Fast persistent Chromium via the `agent-browser` CLI for dive verification, bug repro, scraper recon, screenshots, console, and network checks. Named sessions keep you signed in to the Soria app across calls and across Claude/Codex. |
| `/env` | Preflight the Soria dev stack: MCP reachable, dev cert present, recent shared-state activity visible. |
| `/tools` | Verify MCP tools and local dependencies such as `uv`, `node`, `dbt`, `make`, `git`, and `gh`. |
| `/status` | Read-only inventory for a concept, scraper, group, warehouse table, or dive. |
| `/plan` | ETVLR planning: Extract, Transform, Value-map, Load, Represent, with verification defined before implementation. |
| `/scraper` | Write, repair, and test Soria `SimpleScraper` sources before returning to ingestion. |
| `/ingest` | Group, schema, parse/detect, extract with agent extraction or SimpleExtractor, map, and publish bronze through MCP tools. |
| `/map` | Normalize raw values to canonical forms with evidence. |
| `/parent-map` | Maintain centralized parent-company mapping and ownership timelines. |
| `/dive` | Build or revise a dive: dbt marts SQL, manifest, TSX component, `DivesPage` registration, verification rows, and methodology. |
| `/preview` | Render a dive as markdown tables in chat by reading the manifest and querying MotherDuck. |
| `/verify` | Prove data correctness with warehouse checks, seed comparisons, and external benchmarks when available. |
| `/dashboard-review` | Ship-readiness browser QA for a dive via `/browse`. |
| `/diagnose` | Triage broken workflows before guessing: schema mismatches, missing data, silent failures, runtime issues. |
| `/ticket` | Capture a structured issue in Linear or as a GitHub-ready issue draft. |
| `/promote` | Safe production path: diff, verification, browser QA, PR, promotion manifest, CI. |
| `/lessons` | Retrospective and skill-maintenance loop. Turns evidence into durable updates in this repo. |

Developer-focused skills:

| Skill | What it does |
|-------|-------------|
| `/dev-env` | Start, inspect, or repair a branch-local Soria app environment for engineering work. |
| `/dev-dives` | Start or repair the canonical dev HTTPS dive frontend when browser QA or empty grids may be caused by wrong Vite/backend/catalog alignment. |
| `/test` | Choose and run the right proof layer: unit, integration, boundary, runtime, pipeline E2E, or deployed proof. |
| `/code-review` | Review Soria diffs against repo-specific engineering patterns and test-boundary expectations. |

Repo-local helper scripts, such as `soria-2/scripts/seed-dev-tp.py`, are not
standalone skills. `/dev-env` and `/test` should route to those scripts when a
specific proof needs them.

## Installation for Codex

Prerequisites:

- Codex is installed and can load local skills/plugins.
- The `soria` MCP server is configured in the Codex client, usually as an HTTP
  endpoint like `https://<your-dbos>.cloud.dbos.dev/mcp/`.
- This repo is cloned to a stable path. Use any stable path, but do not copy
  individual skills around by hand.

Recommended setup:

```bash
git clone https://github.com/Soria-Inc/soria-stack ~/soria-stack
cd ~/soria-stack
./install-codex.sh
```

`install-codex.sh` creates or updates:

```text
~/plugins/soria-stack -> <repo>/plugins/soria-stack
~/.agents/plugins/marketplace.json
```

Some Codex sessions also expect top-level skill directories under
`~/.codex/skills`. In that case, add direct symlinks from Codex's skill home to
the plugin skills:

```bash
mkdir -p ~/.codex/skills
for skill_dir in ~/plugins/soria-stack/skills/*; do
  [ -f "$skill_dir/SKILL.md" ] || continue
  ln -sfn "$skill_dir" "$HOME/.codex/skills/$(basename "$skill_dir")"
done
```

The important rule is that symlinks should point back into the git clone. Do
not copy skill folders into `~/.codex/skills`; copied skills go stale.

Restart Codex or start a fresh session after changing plugin or skill
symlinks.

## Installation for Claude Code

Claude Code reads flat top-level skill directories from `~/.claude/skills`.
Clone or symlink this repo into that directory, then run the installer:

```bash
git clone https://github.com/Soria-Inc/soria-stack ~/.claude/skills/soria-stack
cd ~/.claude/skills/soria-stack
./install.sh
```

The installer creates symlinks like:

```text
~/.claude/skills/ingest -> soria-stack/ingest
~/.claude/skills/dive -> soria-stack/dive
~/.claude/skills/lessons -> soria-stack/lessons
```

It is idempotent. Rerun it after `git pull` to pick up added, removed, or moved
skills.

## Installation for Hermes

Hermes reads extra skill directories from `~/.hermes/config.yaml`
`skills.external_dirs`. The Hermes surface is generated from the Codex-facing
wrappers and namespaced as `/soria-status`, `/soria-dive`, `/soria-plan`, etc.,
so it does not collide with bundled Hermes skills.

On the Hermes host:

```bash
git clone https://github.com/Soria-Inc/soria-stack ~/soria-stack
cd ~/soria-stack
./install-hermes.sh
```

`install-hermes.sh`:

- regenerates `plugins/hermes/skills/*/SKILL.md`
- adds `<repo>/plugins/hermes/skills` to Hermes `skills.external_dirs`
- installs a user systemd timer, when available, to fast-forward this checkout
  hourly and refresh Hermes when `origin/main` changes

Generated Hermes skills are not source files. Edit the canonical
`plugins/soria-stack/skills/<name>/SKILL.md` wrapper or the generator, then run:

```bash
python3 scripts/sync-hermes-skills.py
```

## How Symlinks Should Work

Use symlinks to expose canonical repo content to each agent runtime:

- `~/plugins/soria-stack` should point at `<repo>/plugins/soria-stack` for the
  Codex plugin.
- `~/.codex/skills/<name>` may point at
  `~/plugins/soria-stack/skills/<name>` for top-level Codex skill discovery.
- `~/.claude/skills/<name>` should point at `soria-stack/<name>` for
  Claude-style skills.
- Hermes should point `skills.external_dirs` at
  `<repo>/plugins/hermes/skills`; those generated files point back to the
  upstream wrappers in this repo.

This lets `git pull` update the skill text that every symlink resolves to.
Only rerun installers when skill directories are added, removed, renamed, or
when a symlink target has moved.

## Keeping the Pack Up To Date

Codex:

```bash
cd ~/soria-stack
git pull --ff-only
./install-codex.sh
mkdir -p ~/.codex/skills
for skill_dir in ~/plugins/soria-stack/skills/*; do
  [ -f "$skill_dir/SKILL.md" ] || continue
  ln -sfn "$skill_dir" "$HOME/.codex/skills/$(basename "$skill_dir")"
done
```

Claude Code:

```bash
cd ~/.claude/skills/soria-stack
git pull --ff-only
./install.sh
```

Hermes:

```bash
cd ~/soria-stack
git pull --ff-only
./install-hermes.sh
```

Then start a fresh agent session and run:

```text
/tools
/status
```

## Daily Workflow

Most work follows this path:

```text
/tools
  -> /status
  -> /plan
  -> /ingest or /dive
  -> /verify
  -> /dashboard-review when UI proof is needed
  -> /promote when ready to land
  -> /lessons when the session produced durable learning
```

Use `/preview` any time a dive should be inspected in chat. Use `/diagnose`
from any phase when reality does not match the expected workflow.

## Adding New Skills

New developer-focused skills are fine. Add one when the behavior is
Soria-specific, repeatable, and useful for future agents.

For each new skill:

1. Pick a short command-style name, such as `ci-fix`, `frontend-debug`, or
   `mcp-debug`.
2. Decide the surfaces:
   - Claude-facing: `<name>/SKILL.md`
   - Codex-facing: `plugins/soria-stack/skills/<name>/SKILL.md`
   - Hermes-facing: generated from the Codex wrapper by
     `scripts/sync-hermes-skills.py`
   - Both source surfaces, if both agent runtimes should use it
3. Include frontmatter with `name`, `description`, and relevant metadata.
4. Document:
   - when to use it
   - when not to use it
   - preferred tools and commands
   - safety rules
   - verification or exit criteria
   - what should be updated if the workflow changes
5. Update this README's skill table when the skill is durable.
6. Run the relevant installer or symlink refresh locally, then test in a fresh
   agent session.

Good developer-skill candidates include Soria-specific CI debugging, MCP tool
surface debugging, frontend runtime checks, local dev stack repair, release
checks, or test protocol. Generic code review advice or broad engineering
style guidance belongs somewhere else.

## `/lessons` Flow

Use `/lessons` when a session reveals something the next agent should know:

- a repeated failure mode
- a successful workflow pattern
- a confusing setup issue
- a missing MCP/tool capability
- a user preference that affects future Soria work
- a "remember this" instruction

The `/lessons` workflow:

1. Review concrete evidence from the session: diffs, commands, outputs, browser
   traces, MCP calls, tickets, or notes.
2. Decide whether the lesson belongs in an existing skill, a new skill, this
   README, `ETHOS.md`, or `MCP_TOOL_MAP.md`.
3. Search for stray copies in current worktrees, `~/.claude/skills`,
   `~/.codex/skills`, plugin wrappers, and backups before editing.
4. Update the canonical `Soria-Inc/soria-stack` repo. Do not patch temporary
   checkouts or copied skill folders as the source of truth.
5. If both Claude and Codex need the behavior, update both the root skill and
   `plugins/soria-stack/skills/<name>/SKILL.md`.
6. Keep the lesson specific and actionable. Prefer a concrete guardrail,
   command, or routing rule over generic retrospective text.
7. Commit and push the change so the symlinked installations can pick it up on
   the next `git pull`.

## Reference Docs

- `ETHOS.md` contains the broader operating principles.
- `MCP_TOOL_MAP.md` maps Soria workflows to `mcp__soria__*` tools.
- `plugins/soria-stack/references/codex-adapter.md` explains how the Codex
  wrappers translate the canonical Claude skill pack.
- `plugins/hermes/references/hermes-adapter.md` explains Hermes runtime naming
  and MCP tool differences.


## Auto-update

`install.sh` registers a Claude Code SessionStart hook that runs
`scripts/auto-update.sh` at most once per day. The hook:

- Pulls latest from `origin/main` with `--ff-only` (won't clobber local commits)
- If anything changed, re-runs `install.sh` to pick up new skills + rebuild
  `/browse` if its source changed
- Stamps `.last-auto-update` so it doesn't re-run on every session that day
- Stays quiet on success; only prints when there's a real update or an error

**Disable it:** remove the `auto-update.sh` entry from
`~/.claude/settings.json` under `hooks.SessionStart`. Or chmod -x the script.

**Force update now:** `~/.claude/skills/soria-stack/scripts/auto-update.sh`
(delete `.last-auto-update` first if you want to bypass the daily gate).

**On divergence** — if your local checkout has uncommitted changes or local
commits that aren't on `origin/main`, the ff-only pull fails silently and the
script writes the daily stamp anyway (so it doesn't retry every session).
Resolve manually via `git status` + `git pull` when ready.

`install-hermes.sh` also installs `soria-stack-hermes-sync.timer` on systemd
hosts. The timer runs `scripts/hermes-auto-update.sh`, refuses dirty checkouts,
pulls `origin/main` with `--ff-only`, regenerates Hermes skills, and restarts
the Hermes gateway only when the checkout actually moved.
