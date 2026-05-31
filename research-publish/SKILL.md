---
name: research-publish
version: 1.0.0
description: |
  Compose and publish Soria research — a research note (a story in the Research
  feed) or a research newsletter (an intro + ordered notes emailed to the
  internal team). Interviews the author for the story, its citations (news
  events, articles, dives, files, Datawrapper charts), their order, and an
  optional intro, then drives the `mcp__soria__research_*` MCP tools to
  create → preview → publish/send. A note reaches customers only when its
  visibility is `public`; newsletter send goes to the internal team audience
  only. Use when asked to "write a research note", "publish research", "build
  the research newsletter", "cite this event/dive/file in a note", or "send the
  research digest".
---

# /research-publish

You drive the tools; the author makes the decisions. This skill walks an author
through building research content and pushing it live, using tools that already
exist on the Soria MCP — you never touch the database or write SQL.

## The two units (establish this first)

- **Research note** — one story in the Research feed. Title + markdown body +
  ordered citations (references). **A note is invisible to customers until its
  `visibility` is `public`.** `internal` = saved but hidden from every feed —
  use it as a draft you can preview before publishing.
- **Research newsletter** — a subject + optional intro paragraph + an *ordered
  list of existing notes*, broadcast to the **internal team audience only**
  (`RESEND_RESEARCH_INTERNAL_AUDIENCE_ID`). No external/customer send path
  for now.

Ask the author which they're doing. Usual arc: author one or more notes →
publish the good ones → optionally bundle some into a newsletter for the team.

## Environment — know where you're writing

These tools write to whatever your Soria MCP currently points at:

- **Drafting / testing** → your local dev stack (writes to the dev DB).
- **Live publishing** → production (the real customer Research feed + the real
  team audience).

Confirm the intended environment with the author **before** any `create`,
`update`, or `send`. Publishing a note or sending a newsletter against prod is
real and immediately customer- or team-visible.

## Tools you drive (`mcp__soria__research_*`)

| Tool | Purpose |
|---|---|
| `research_note_query` | find/list notes — by `note_id`, text `query`, or `visibility` |
| `research_note_manage` | `action`: `create` / `update` / `archive` |
| `research_chart_manage` | generate a Datawrapper chart and attach it to a note |
| `research_newsletter_query` | find/list newsletters |
| `research_newsletter_manage` | `action`: `create` / `update` / `preview` / `send` |

---

## Workflow A — compose a research note

Interview one decision at a time. Don't dump the whole questionnaire at once.

### 1 · The story
Ask for the **title** and the **body** (markdown). These headings are the
convention — they become labelled blocks when the note is rendered into a
newsletter:

```
## The news
<what happened>

### Why it matters
<the so-what for Soria's customers>
```

### 2 · The citations — the heart of it
Ask: *"What are we linking — which event(s), articles, a dive, a file, an
external page?"* For each, you need its **id (or URL)** — help the author find
it (see **Finding reference IDs**). In the body, cite each one inline with a ref
token: `[the phrase to link](ref:<type>)` (or `(ref:<uuid>)`).

Each reference is a dict in the `references` list. Exact shapes:

| type | required | shape |
|---|---|---|
| `event` (one or many) | `ref_id` = news_event uuid | `{"ref_type":"event","ref_id":"<news_event uuid>","label":"…"}` |
| `news_article` | `ref_id` = news_article uuid | `{"ref_type":"news_article","ref_id":"<news_article uuid>","label":"…"}` |
| `dive` | `dive_id` in metadata | `{"ref_type":"dive","label":"…","metadata_json":{"dive_id":"<slug>","dive_filters":{"state":"CA"}}}` |
| `file` | `ref_id` = file uuid | `{"ref_type":"file","ref_id":"<file uuid>","label":"…"}` |
| `chunk` | `ref_id` = file_chunk uuid | `{"ref_type":"chunk","ref_id":"<file_chunk uuid>","label":"…"}` |
| `external_url` | `url` | `{"ref_type":"external_url","url":"https://…","label":"…"}` (opens in a new tab) |
| `datawrapper_chart` | — | don't hand-build; step 3 produces it |

A note can carry **multiple events** — just add one `event` reference per event.

### 3 · A chart? (optional)
If the story wants a Datawrapper chart:

```
research_chart_manage(
  chart_config={"title":"…","data":[…]},   # or a Datawrapper config dict
  title="…",
  note_id="<the note's id>",                # attaches automatically when given
  generate=true,                            # creates + publishes via Datawrapper
)
```

It returns `chart_id`, `public_url`, `png_url`, and a ready-made
`reference_payload`. With `note_id` given, it adds the `datawrapper_chart`
reference and bumps the note to a new version for you. If `status="failed"`,
read `error_json` and fix `chart_config`.

### 4 · The order
`position` (0, 1, 2, …) sets citation order — confirm which one leads. If you
omit `position`, the order you pass the list in is used.

### 5 · Create + publish
```
research_note_manage(
  action="create",
  title="…",
  body_markdown="…",
  visibility="public",       # show it in the feed now
  references=[ … ],
)
```
Returns `note_id` + an app link — open it to read the note in context.

**Want to draft privately first?** Create with `visibility="internal"` (hidden
from the feed), preview via the app link, then publish when ready:
```
research_note_manage(action="update", note_id="<id>", visibility="public")
```
Internal notes never show in the feed — that's the *"No Research notes are
published yet"* state. To unpublish later, update back to `internal`.

---

## Workflow B — assemble + send a newsletter

### 1 · Pick the notes, in order
Decide which existing notes go in and their order — the `note_ids` order *is*
the newsletter order. Use `research_note_query` to find ids.

### 2 · Optional intro
A short markdown intro that renders above the stories.

### 3 · Create
```
research_newsletter_manage(
  action="create",
  subject="…",
  intro_markdown="…",          # optional
  note_ids=["…","…","…"],      # ordered
)
```
Creating **freezes the exact version** of each note as it is right now — later
edits to a note won't change a newsletter you've already built or sent.

### 4 · Preview (sends nothing)
```
research_newsletter_manage(action="preview", newsletter_id="<id>")
```
Renders the email HTML so you can inspect it before sending.

### 5 · Send (internal team only)
```
research_newsletter_manage(action="send", newsletter_id="<id>")
```
Broadcasts the current version to the internal audience. To change something
first: `action="update"` (reorder via `note_ids`, edit `subject` /
`intro_markdown`; pass `intro_markdown=""` to clear the intro) — that makes a
fresh version; preview, then send.

---

## Finding reference IDs

You need the target's id/URL before you can cite it. Fastest paths:

- **Events / articles** — visible in the app's **Events** and **Analyst** tabs;
  grab the id there, or ask the author which event and look it up. (Events live
  in `news_events`, articles in `news_articles`.)
- **Dives** — `dive_id` is the slug in the dives URL (`/dives?dive=<dive_id>`),
  e.g. `aco-intelligence`. Add `dive_filters` to deep-link a specific view
  (e.g. `{"state":"CA","program":"mssp"}`).
- **Files / chunks** — the **Library** / file-viewer URLs carry the file id
  (`/file/<uuid>`); a chunk also needs its parent `file_id`.
- **External pages** — just the URL, no lookup needed.

When unsure, ask the author to paste the link from the app; pull the id/slug out
of it.

## Gotchas

- **"No Research notes are published yet"** → the note is `internal`. Set
  `visibility="public"`.
- **Newsletter only reaches the team** — no customer/external send for now.
- **Editing a note makes a new version**; a newsletter keeps the note version
  frozen at the moment the note was added.
- **Charts can fail** — check `status` / `error_json` on the
  `research_chart_manage` result before relying on the chart.
