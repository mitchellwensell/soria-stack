---
name: soria-scraper
description: 'Soria Stack Hermes skill for scraper. Write, repair, and test Soria scrapers in Hermes. Use when building a `SimpleScraper`, fixing scraper drift, handling dynamic sites, generated files, manual uploads, or deciding between `get_html` / `get_json`, `browser_task`, `needs_browser`, and `produce`. Use before ingest when source discovery is the hard part. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/scraper/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Scraper

Hermes adapter for upstream Soria-stack skill `scraper`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-scraper`
- Upstream source: `plugins/soria-stack/skills/scraper/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Scraper

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-scraper` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- inspect source before coding; inventory existing scrapers/files first
- write exactly one `SimpleScraper` subclass
- discovered files must include `url`, `filename`, `date`, and `page_url`
- prefer `get_html` / `get_json`; use `browser_task` for dynamic pages and
  `needs_browser=True` only for deterministic browser interactions
- use `produce()` when the scraper must generate bytes from an API
- dry-run with `scraper_run(test=True, code=..., url=...)` before
  saving or editing canonical app-repo code
- verify real runs with `file_query`, downloaded counts, date range, file types,
  grouping, and schema drift

## Core Contract

```python
from soria.scrapers.core.base_scraper import SimpleScraper, get_html, make_absolute_url, clean_filename


class MySourceScraper(SimpleScraper):
    url = "https://example.com/data"

    def discover_files(self) -> list[dict]:
        soup = get_html(self.url)
        return [{
            "url": make_absolute_url(a["href"], self.url),
            "filename": clean_filename(a.get_text(strip=True)),
            "date": "2026-05",
            "page_url": self.url,
        } for a in soup.select("a[href$='.pdf']")]
```

## Guardrails

- no raw `requests`, `httpx`, or `curl_cffi` in scraper code
- no hardcoded report URL lists when an index/API exists
- no non-ISO dates
- no scraper-side extraction, value mapping, or warehouse writes
- no manual upload unless the human approves or no scrapable source exists
- if a real run times out, check workflow/file state before retrying
