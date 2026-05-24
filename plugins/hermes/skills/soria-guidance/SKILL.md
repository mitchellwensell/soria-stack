---
name: soria-guidance
description: 'Soria Stack Hermes skill for guidance. Build a normalized, chunk-cited CSV of a public company''s forward-looking financial guidance over a date window. Pulls from ir_<ticker>, sec_edgar_prime, and earnings_transcripts via chunk_search; cross-checks gaps against the IR scraper. Use for "show X''s guidance", "track guidance revisions", "when did they suspend / raise / lower", "build a guidance timeline", "compare initial vs current FY outlook". Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/guidance/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Guidance

Hermes adapter for upstream Soria-stack skill `guidance`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-guidance`
- Upstream source: `plugins/soria-stack/skills/guidance/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Guidance

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-guidance` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- one ticker per invocation; default window 8 quarters
- inventory the disclosure surface FIRST via `database_query`
  against `files` joined to `scrapers` (filter by `s.name = 'ir_<ticker>'`
  and `s.name = 'sec_edgar_prime'`); confirm the candidate event list with
  the user before extraction (Gate 1)
- **source preference per event**: 8-K Exhibit 99.1 (`sec_edgar_prime`) >
  IR press release PDF (`ir_<ticker>`) > prepared remarks PDF > earnings
  transcript. Use `as_of_date` = 8-K filing date or press release header
  date (NOT `date_iso`). For mid-quarter pre-announcements, `as_of_date` =
  pre-announcement date, not the subsequent earnings call date.
- per event, run THREE `chunk_search` shapes — segment outlook,
  EPS reconciliation, ratios/capital — never just one
- always set `ticker=<TICKER>` and `scraper_name=<source>`
- do NOT use `date_from`/`date_to` for IR docs (`date_iso` is fiscal year,
  not release date); date filters work only for `sec_edgar_prime`
- normalize to the locked schema:
  `as_of_date,period,metric_category,metric,value_range,value_units,chunk_id`
- categories are locked: `Total | Segment Revenue | Segment Operating Earnings | EPS | EPS Bridge | Ratios | Cash Flow | Capital | Members | Long-Term`
- **EBITDA / non-per-share profitability → `Total`, never `EPS`**. `EPS` is
  reserved for actual per-share metrics only. EBITDA-anchored issuers (ALHC,
  OSCR, CLOV) may have zero `EPS` rows — that is correct.
- value encoding: `low - high` | `>= X` | `~X` | `X` | `withdrawn` | `qualitative`
- **`value_units` vocab** (hard constraint): `$ billions` | `$ per share` | `%` | `millions` | `text`.
  NEVER use `$M`, `$B`, `USD_billions`, `percent`, `count`, `count_millions`,
  `days`, `clinics`, `states`, `members`, `note`, or any other freeform unit.
  If a metric needs an out-of-vocab unit, set `value_units=text` and embed
  the unit in `value_range` (e.g. `~44 days`).
- **`period` vocab**: `FY20XX`, `Long-Term`, or quarterly forms (`1Q25`,
  `2H25`). Monthly snapshots (e.g. `Jan-2025`) are not guidance periods — drop.
- **`value_range` format**: canonical only — no prose, no `(at low-end)`,
  no arrows, no parenthetical negatives. Use `-X` not `(X)`.
- vocab gate before Gate 2: walk every row and assert all three field
  constraints above; fix or drop any row that fails
- coverage check (Gate 2): for IC / Q4 / "re-establishes outlook" events,
  confirm segment + EPS + ratios + cash flow + capital + members are all
  attempted; for mid-cycle revisions, EPS-only is by design
- spot-check (Gate 3): re-read the cited chunk for the most recent event's
  Adjusted EPS (or EBITDA for EBITDA-anchored issuers) row before declaring DONE
- output sorted by `as_of_date` then `period` then category order

## Common anti-patterns

- citing a recap chunk instead of the primary event chunk
- one `chunk_search` call per event (will miss segment / ratios / capital tables)
- assuming the Investor Conference deck is in the chunk index — usually only
  the press release preview is. Say so explicitly when the deck is missing.
- inventing metric_categories or metric names; the taxonomy is the contract
- searching without a `ticker` filter — returns cross-issuer noise
- putting EBITDA or other non-per-share profitability metrics in `EPS` category
- using freeform `value_units` (`$M`, `$B`, `days`, `count`, etc.) instead of
  the five allowed vocab terms; use `text` + embed the unit in `value_range`
- trusting `date_iso` from `ir_<ticker>` for `as_of_date` — it's a fiscal-year
  stamp, not the press release date; read the press release header instead
- using the transcript number when the 8-K press release table has the same
  metric — transcripts have rounding artifacts and verbal imprecision

## Cross-issuer adaptation

Adapt query 1 segment names per ticker:
- managed care (UNH/HUM/CI/CVS/ELV/MOH): UnitedHealthcare/Optum/Aetna/Cigna Healthcare/Evernorth/Anthem
- hospitals (HCA/THC/UHS/CYH): same-facility admissions, EBITDA, capex
- standard insurers: combined ratio, NWP, BVPS

Schema and gates stay constant across issuers.
