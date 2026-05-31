---
name: scraper
version: 1.0.0
description: |
  Write, repair, and test Soria scrapers. Use when the task is primarily
  discovering source files, coding a `SimpleScraper`, handling dynamic sites,
  producing generated CSV/JSON bytes, fixing scraper drift, or deciding between
  direct HTTP, `browser_task`, Playwright `needs_browser`, manual upload, and
  pull-mode `create_file`. Use before /ingest when source discovery is the hard
  part; return to /ingest after files land. Drives scraper operations through
  `mcp__soria__scraper_run`, `scraper_manage`, `scraper_upload_urls`, and
  `scraper_confirm_uploads`; no `soria` CLI. (soria-stack)
benefits-from: [status, ingest]
allowed-tools:
  - Read
  - Bash
  - Write
  - AskUserQuestion
  - mcp__soria__*
---

## Preamble

```bash
mkdir -p ~/.soria-stack/artifacts
echo "SKILL: scraper"
echo "---"
git status --short 2>/dev/null | head -10 || true
```

Read `ETHOS.md`. For scraper work, the important rules are: inventory before
action, inspect the source before coding, dry-run with `test=True`, and show
file-count/date-range evidence before saying the scraper works.

## Contract

A Soria scraper is one `SimpleScraper` subclass. Runtime code is loaded through
the scraper DB row, and in the app repo the durable reviewed source lives at
`scrapers/{name}.py`.

Required:

```python
from soria.scrapers.core.base_scraper import (
    SimpleScraper,
    get_html,
    get_json,
    make_absolute_url,
    clean_filename,
)


class MySourceScraper(SimpleScraper):
    url = "https://example.com/data"

    def discover_files(self) -> list[dict]:
        soup = get_html(self.url)
        return [
            {
                "url": make_absolute_url(link["href"], self.url),
                "filename": clean_filename(link.get_text(strip=True)),
                "date": "2026-05",        # YYYY, YYYY-MM, YYYY-MM-DD, or YYYY-QN
                "page_url": self.url,      # provenance
            }
            for link in soup.select("a[href$='.pdf']")
        ]
```

Each discovered dict must include `url`, `filename`, `date`, and `page_url`.
Any extra keys become file metadata. `date` must parse as `YYYY`,
`YYYY-MM`, `YYYY-MM-DD`, or `YYYY-QN`; invalid dates fail during ingest.

Optional:

- `SCRAPER_HEADERS = {...}` for cookies, auth, or source-specific headers.
- `needs_browser = True` for deterministic Playwright interaction via
  `self.page`.
- `self.browser_task(...)` for dynamic pages where natural-language browser
  discovery is cheaper than reverse-engineering selectors.
- `produce(self, url, filename, context)` when discovered files are virtual and
  the scraper must generate bytes, such as a CSV assembled from an API.
- `custom_validators = [...]` for source-specific discovery checks.
- Pull mode with `self.create_file(...)` for scrapers that directly create
  files instead of returning file refs.

## Recon First

Before writing code:

1. Check existing scrapers/files:
   - `mcp__soria__database_query` over `scrapers`, `groups`, and `files`.
   - `mcp__soria__scraper_manage(scraper_name="...", read=True)` if a likely
     scraper exists.
2. Open or fetch the source page. Identify:
   - static links, API JSON, dashboard API, or generated files.
   - date range and update cadence.
   - filenames that will be stable and group-matchable.
   - whether files are PDFs, CSVs, Excel, ZIP, TXT, or JSON.
3. Pick the simplest access tier that works:
   - `get_html` / `get_json`: default.
   - `browser_task`: dynamic site discovery with flexible structure.
   - `needs_browser=True` + `self.page`: precise clicks/forms/session behavior.
   - manual upload: only when human confirms the source is not scrapable.

Never import `requests`, `httpx`, or `curl_cffi` in scraper code. Use
`get_html` / `get_json`; they route through Soria's fetch stack, including the
proxy/browser fallback that raw HTTP bypasses.

## Hard-To-Scrape Sites

Use the built-in escalation path deliberately:

1. **Start with `get_html` / `get_json`.** These wrap Soria's fetch service,
   default browser-like headers, timeout handling, proxy routing, and browser
   fallback. Most sites should stay here.
2. **Add `SCRAPER_HEADERS` only for source-specific requirements** like a
   required cookie, API token, or custom Accept header. Do not paste a full
   browser header dump unless the site actually requires it.
3. **Use `browser_task` for volatile dynamic pages.** It is an AI browser agent
   that can find links or structured data without writing selectors. It does
   not require `needs_browser=True`.
4. **Use `needs_browser=True` + `self.page` for deterministic browser work:**
   login-free clicks, dropdowns, tabs, form submissions, waiting on selectors,
   or executing JavaScript in the page context. Keep selectors minimal and wait
   for the network/DOM state you need.
5. **Use `produce()` for virtual files.** If the site exposes data only through
   API calls, `discover_files()` should return logical file refs and `produce()`
   should generate stable CSV/JSON bytes.
6. **Stop before manual upload.** Manual upload is allowed only after the human
   confirms the source is not scrapable or is intentionally an uploaded/manual
   source.

Common failure signatures:

- Tiny "PDF" or "CSV" downloads are often bot-protection/error HTML. Inspect
  size/content and fix access instead of accepting the file.
- Infinite scroll/API dashboards usually have JSON endpoints. Use browser
  network inspection or `browser_task` to identify them before falling back to
  manual browser scripting.
- Auth/MFA portals are usually not suitable for automated scraping. Escalate to
  manual upload or a first-party integration decision.

## Write Patterns

### Static HTML Links

Use `get_html`, CSS selectors, `make_absolute_url`, and deterministic date
parsing from nearby text, link text, table cells, or URL segments. Do not
hardcode a list of report URLs unless the source page truly has no index.

### JSON APIs

Use `get_json`. Keep pagination explicit and bounded. Include API parameters
that explain the date range in file metadata. If an API returns data rather
than downloadable files, use `produce()` to serialize a CSV/JSON file.

### Dynamic Sites

Use `browser_task` first when structure is volatile:

```python
result = self.browser_task(
    "Find all downloadable PDF reports. Return url, filename, date, page_url.",
    output_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "filename": {"type": "string"},
                "date": {"type": "string"},
                "page_url": {"type": "string"},
            },
            "required": ["url", "filename", "date", "page_url"],
        },
    },
)
```

Use `needs_browser=True` only when deterministic browser actions are required.
`self.page` starts on `self.url`; wait for selectors before reading content.

### Generated Files With `produce`

Use `discover_files()` to return one file ref per logical output. Put any
parameters needed by `produce()` in metadata.

```python
def discover_files(self):
    return [{
        "url": f"{self.url}/api/data?ticker=UNH",
        "filename": "source_UNH_2026-05-31.csv",
        "date": "2026-05-31",
        "page_url": self.url,
        "ticker": "UNH",
    }]

def produce(self, url, filename, context):
    rows = context["get_json"](url)
    return serialize_csv(rows)
```

`produce()` should return bytes or `None` to fall back to normal download.

## Test Loop

Always dry-run before saving or landing:

```text
mcp__soria__scraper_run(
  scraper_name="source_name",
  test=True,
  code=code,
  url="https://example.com/data",
)
```

Review:

- test passed without timeout.
- files found is plausible.
- sample filenames are stable and clean.
- dates are valid and cover expected history.
- URLs are absolute and real.
- file types are supported.
- no error pages are masquerading as tiny PDFs/CSVs.

Then save/run through MCP when operating directly on shared state:

```text
mcp__soria__scraper_manage(
  scraper_name="source_name",
  save={"code": code, "url": "https://example.com/data"},
)
mcp__soria__scraper_run(scraper_name="source_name", auto_pipeline=True)
```

When working in the app repo, edit `scrapers/{name}.py` instead of only saving
MCP code, run the repo's required tests, and land through git so CI deploys the
canonical scraper code.

## Verify After Real Run

Use `file_query` and/or Postgres state to show:

- files discovered vs downloaded.
- duplicates skipped by hash.
- grouped count and unmapped-header drift.
- sample files by oldest/newest.
- any auto-pipeline follow-up: column mapping, detection enqueued, parse needed.

If the real run times out, do not rerun blindly. Check file landing and
workflow status first; scraper runs can continue after the MCP call times out.

## Manual Upload

Use only after explicit human approval or when there is genuinely no scrapable
source URL.

```text
mcp__soria__scraper_upload_urls(
  scraper_name="manual_source",
  files=[{"filename": "...", "content_hash": "...", "size_bytes": 123}]
)
mcp__soria__scraper_confirm_uploads(
  scraper_name="manual_source",
  files=[{"filename": "...", "storage_key": "...", "content_hash": "..."}]
)
```

Confirm upload triggers the same grouping and downstream pipeline wiring.

## Artifact

```bash
cat > ~/.soria-stack/artifacts/scraper-$(date +%Y%m%d-%H%M%S).md << 'ARTIFACT'
# Scraper Report: [source]

## Source
- URL: [...]
- Access pattern: [HTML | JSON API | browser_task | needs_browser | produce | manual]
- Expected cadence/range: [...]

## Code
- Scraper name: [...]
- File path or MCP row: [...]
- Dry-run result: [files found, sample]

## Run Evidence
- Files downloaded: [...]
- Date range: [...]
- File types: [...]
- Grouping / pipeline follow-up: [...]

## Outcome
Status: [DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT]
Lesson: [...]
ARTIFACT
```

## Anti-Patterns

- Raw HTTP libraries instead of `get_html` / `get_json`.
- Hardcoded URL lists copied from today's page.
- Missing or non-ISO `date`.
- Omitting `page_url`.
- Saving code before `scraper_run(test=True)`.
- Manual upload to avoid fixing a scrapeable source.
- Scraper code that does extraction, value normalization, or warehouse writes.
- Module-level mutable state that can leak across imports/runs.
