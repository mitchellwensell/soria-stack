---
name: soria-lessons
description: 'Soria Stack Hermes skill for lessons. Retrospective for Hermes. Use when the user wants to review recent Soria work, extract patterns, capture failures, or update team skills from concrete evidence. Use for Soria data pipeline, dive, verification, promotion, or engineering workflow requests that match this topic.'
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: plugins/soria-stack/skills/lessons/SKILL.md
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# Soria Lessons

Hermes adapter for upstream Soria-stack skill `lessons`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `soria-lessons`
- Upstream source: `plugins/soria-stack/skills/lessons/SKILL.md`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

# Lessons

Hermes adaptation of the `Soria-Inc/soria-stack` `/soria-lessons` skill.

Read [../../references/hermes-adapter.md](../../references/hermes-adapter.md)
before acting.

## Focus

- review recent artifacts and session evidence
- use mempalace when available for prior comparable work
- identify repeat failures, successful patterns, and principle updates
- treat "capture this", "why did this take so long", and "make sure we
  remember this" as possible skill-update requests
- decide whether the lesson belongs in an existing skill or needs a new skill
- route engineering lessons deliberately: test decisions to `test`, review
  rules to `code-review`, dev environment procedure to `dev-env`, TP runtime
  helper usage to `test` or `dev-env`
- locate the target skill/new skill and compare any branch-local patch against
  canonical `Soria-Inc/soria-stack`
- propose a concrete target and reviewable diff before editing unless the user
  explicitly approved direct landing
- update the canonical skill repo, not a temporary `soria-2` checkout or
  backup copy
- on Adam's machine, edit skills in
  `/Users/adamron/.superset/projects/soria-stack`, not directly under
  `~/.codex/skills`, `~/.claude/skills`, or app-repo embedded copies
- update both surfaces when needed:
  `<skill>/SKILL.md` and `plugins/soria-stack/skills/<skill>/SKILL.md`
- remember Hermes reads plugin skills through symlinks: existing `SKILL.md`
  edits are live on disk, but after GitHub `main` changes run `git pull`; run
  `bash install-codex.sh` for new/removed skills, plugin metadata, or `/soria-browse`
  rebuilds, and use a fresh Hermes session if changes do not appear
- preserve `https://github.com/Soria-Inc/soria-stack` metadata when porting
  lessons from embedded copies
- surface MCP tool gaps (needed behavior with no `Soria MCP tools` tool)
- end with concrete lessons, not generic retrospection

## Canonical Skill Update Workflow

When an approved lesson changes skill behavior:

1. Verify the canonical repo with `git remote -v`; expected remote is
   `https://github.com/Soria-Inc/soria-stack`.
2. Decide whether an existing skill should absorb the lesson or whether a new
   skill is warranted. Prefer existing skills for gates, anti-patterns, and
   trigger clarifications; propose a new skill for repeatable workflows with a
   distinct entrypoint, tool surface, or domain.
3. Identify the target skill or new skill name.
4. Search for the lesson in likely stray locations: current worktree,
   `~/.claude/skills`, `~/.codex/skills`, plugin wrappers, and backups.
5. Present the target, rationale, evidence, and proposed diff. If creating a
   new skill, include frontmatter, first-pass body, and any references/scripts.
6. Port only the lesson into canonical `soria-stack`. Do not wholesale copy
   branch-local files whose metadata or repo assumptions point at `soria-2`.
7. Update both the Claude-facing skill and the Hermes-facing wrapper when both
   should change.
8. Show the diff or, if the user approved direct landing, commit and push.
