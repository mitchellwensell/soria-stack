---
name: soria-dashboard-review
description: 'Soria Stack Hermes skill for dashboard-review. Ship-readiness browser QA for a Soria dive in Hermes. Use when the user wants a live dive reviewed, QA''d, critiqued, or checked before promotion, including headless screenshots, render checks, data correctness, interactivity, methodology, edge cases, performance evidence, and the Soria good-dive grammar: analytical contract, time columns, dense parent/sub-metric rows, Top N + Other + Total cohorts, chart/table pairing, information density, and domain vocabulary. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/dashboard-review/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Dashboard Review

Hermes adapter for upstream Soria-stack skill `dashboard-review`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-dashboard-review`
- Upstream source: `plugins/soria-stack/skills/dashboard-review/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Dashboard Review

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-dashboard-review` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting. Then read the canonical skill at
[../../../../dashboard-review/SKILL.md](../../../../dashboard-review/SKILL.md);
it contains the review gates and Soria good-dive grammar.

## Focus

- live dive QA against `https://dev.soriaanalytics.com` before merge or
  `https://soriaanalytics.com` for prod canary
- actual rendered screenshots first; code and data checks explain or verify
  what the screenshots show
- headless `/soria-browse` evidence (via the `agent-browser` CLI) for render,
  interactivity, correctness, and performance
- cross-check rendered values against the `verifications.csv` seed and the
  live warehouse via `warehouse_query`
- final gate before `/soria-promote`

## Hermes Runtime Rules

- Use `/soria-browse` (the `agent-browser` CLI) for all browser work. Do not fall
  back to Playwright MCP, `mcp__chrome-devtools__*`, or the legacy `$B`
  binary.
- Run headless. Do not open visible browser windows or panes.
- Use a named session (`AGENT_BROWSER_SESSION_NAME=soria-dev`) so cookies
  persist; the one-time Clerk login flow is in `/soria-browse`.
- Do not start, restart, or reconfigure frontend/backend unless the user
  explicitly asks. If the target is down, report `TARGET_DOWN`.
- Save screenshots and a compact JSON report under
  `.dev/browse/<review-name>/` when working in a repo.
- Keep live browser concurrency modest; parallelize screenshot analysis rather
  than opening many tabs at once.
- Separate tool/runtime failures from dashboard failures.
- Do not silently file tickets from here; hand off to `ticket` or `diagnose`.
