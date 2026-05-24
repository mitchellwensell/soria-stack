---
name: soria-browse
description: 'Soria Stack Hermes skill for browse. Fast persistent Chromium for AI agents via the `agent-browser` CLI. Open any URL, interact via @e refs from the accessibility snapshot, screenshot, inspect console/network, log into the Soria app. Named sessions persist cookies across Claude and Hermes. Use when asked to open a page, verify a dive, reproduce a UI bug, capture screenshots, inspect console or network, or test a user flow on localhost, dev, or prod. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/browse/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Browse

Hermes adapter for upstream Soria-stack skill `browse`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-browse`
- Upstream source: `plugins/soria-stack/skills/browse/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Browse

This is the unified browser path for both Claude and Hermes.

**Runtime:** `agent-browser` CLI (https://agent-browser.dev). Install with
`brew install agent-browser && agent-browser install` (or `npm i -g
agent-browser` if Homebrew is unavailable).

**Do not use:**
- `mcp__chrome-devtools__*` MCP tools — no shared session, non-reproducible.
- Playwright MCP — kept around as an emergency fallback only. Do not silently
  switch to it; say the runtime is missing and ask the user.
- The legacy `$B` / gstack binary from `browse/vendor/dist/browse` — superseded.

## Preamble

```bash
command -v agent-browser >/dev/null || { \
  echo "NEEDS_SETUP — run: brew install agent-browser && agent-browser install"; \
  exit 1; }

# Named sessions persist cookies/localStorage across calls AND across
# Claude/Hermes. Pick one per target:
#   soria-dev    → https://dev.soriaanalytics.com
#   soria-prod   → https://soriaanalytics.com
#   soria-local  → http://localhost:* for the Soria app
#   <vendor>     → a vendor site
export AGENT_BROWSER_SESSION_NAME="${AGENT_BROWSER_SESSION_NAME:-soria-dev}"
```

## Soria auth and URL rules

The Soria app sits behind Clerk. Sign in once per session name, then the
session keeps you logged in.

For Soria dive work on `https://dev.soriaanalytics.com`, use `dev-dives`
first if the page is down, a grid shows no rows, or the frontend may be
pointed at the wrong backend/MotherDuck catalog. `browse` owns browser auth
and evidence; `dev-dives` owns Vite/env/catalog alignment.

### Pick the right URL

- Authenticated Soria app pages: bare `https://dev.soriaanalytics.com/...`.
  Dives live at `https://dev.soriaanalytics.com/dives`.
- That host is local in dev: `/etc/hosts` maps it to `127.0.0.1`; macOS
  `pf` redirects port `443` to Vite on `5189`.
- `https://dev.soriaanalytics.com:5189/...` is a liveness diagnostic — do
  not use the explicit port for Clerk sign-in.
- Local non-Clerk pages: `http://localhost:<port>/...` directly.

### Liveness preflight

```bash
curl -skI --max-time 3 https://dev.soriaanalytics.com/ >/dev/null && echo BARE_OK || echo BARE_DOWN
curl -skI --max-time 3 https://dev.soriaanalytics.com:5189/ >/dev/null && echo VITE_OK || echo VITE_DOWN
```

- `BARE_OK`: proceed.
- `BARE_DOWN` + `VITE_OK`: pf redirect is broken. Tell the user to rerun
  `make dev-https-setup` (or `scripts/setup-local-https.sh`) with sudo.
- `VITE_DOWN`: for Soria dive work, switch to `dev-dives`.

### One-time login

Try `adam@soriaanalytics.com` first; if Clerk rejects, retry with
`adam@soriaresearch.com`. Password is `password` for both.

```bash
agent-browser open https://dev.soriaanalytics.com/
agent-browser wait body
agent-browser fill 'input[name="identifier"], input[type="email"], #email' 'adam@soriaresearch.com'
agent-browser fill 'input[name="password"], input[type="password"], #password' 'password'
agent-browser js "(() => { const b=[...document.querySelectorAll('button')].find(x => /sign in|continue|submit/i.test(x.textContent || '')); if (b) { b.disabled=false; b.click(); return 'clicked'; } return 'no submit button'; })()"
agent-browser wait --load networkidle || true
agent-browser snapshot -i
```

The snapshot should show the Soria sidebar and `AR Adam Ron` account button.
If it still shows the sign-in form, capture `agent-browser cookies`,
`agent-browser console`, last 80 network lines, and report the blocker —
do not loop.

### Soria environment badge

If the user expects staging and the badge says `prod`, click the badge,
wait, re-snapshot:

```bash
agent-browser snapshot -i
agent-browser click @e1   # the env badge ref from the snapshot
agent-browser wait --load networkidle
agent-browser snapshot -i
```

## Operating rules

1. Chain related actions in one shell so page state is preserved
   (`agent-browser open URL && agent-browser wait body && ...`).
2. `snapshot -i` first, then click/fill using its `@e` refs.
3. Re-snapshot after navigation or DOM changes — refs are short-lived.
4. If `click @e12` times out, snapshot again; the ref likely moved.
5. Soria renders duplicate controls in sticky header and main content. If a
   ref click is flaky, use `find role button --name "..."` or a JS click by
   exact button text.

## Common flows

### Open and inspect
```bash
agent-browser open https://dev.soriaanalytics.com/dives?dive=my-dive \
  && agent-browser wait --load networkidle \
  && agent-browser snapshot -c \
  && agent-browser console \
  && agent-browser network
```

### Capture evidence
```bash
agent-browser screenshot /tmp/dive.png
agent-browser screenshot --annotate /tmp/dive-annotated.png
```

### Reproduce an interaction
```bash
agent-browser open https://dev.soriaanalytics.com/dives?dive=my-dive
agent-browser wait --load networkidle
agent-browser snapshot -i
agent-browser click @e12
agent-browser snapshot -i
```

### Soria dive control patterns
```bash
agent-browser open 'https://dev.soriaanalytics.com/dives?dive=cost-reports-dashboard'
agent-browser wait --load networkidle
agent-browser snapshot -i
agent-browser text

# Click by exact text when duplicate refs are flaky:
agent-browser js "(() => { const b=[...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Operating Margin'); b?.click(); return location.href; })()"

# Dropdowns render options after the first click — re-snapshot before selecting:
agent-browser js "(() => { const b=[...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'HCA HEALTHCARE INC'); b?.click(); return 'opened'; })()"
agent-browser snapshot -i
agent-browser click @e83

# Numeric input:
agent-browser fill @e81 5
agent-browser press Enter

# Evidence:
agent-browser console
agent-browser network | tail -n 80
```

### Inspect a vendor site before writing a scraper
```bash
agent-browser open https://vendor.example.com
agent-browser text
agent-browser links
agent-browser forms
agent-browser html
```

## `$B` → `agent-browser` translation

| Legacy                              | New                                              |
|-------------------------------------|--------------------------------------------------|
| `$B goto URL`                       | `agent-browser open URL`                         |
| `$B wait --networkidle`             | `agent-browser wait --load networkidle`          |
| `$B snapshot -i/-c/-d N/-s sel`     | same flags                                       |
| `$B click @e1` / `fill` / `is` / `screenshot` | same verbs                             |
| `$B cookie-import-browser ...`      | one-time login flow above, then `--session-name` |
| `BROWSE_STATE_FILE=…`               | `AGENT_BROWSER_SESSION_NAME=…`                   |

`agent-browser --help` is authoritative for the full command surface.
