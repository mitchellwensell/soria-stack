#!/usr/bin/env python3
"""Generate Hermes-facing Soria-stack skills from Codex skill wrappers.

Hermes uses a flat skill namespace. The Codex plugin intentionally exposes
short names like ``plan`` and ``test``, but those collide with Hermes bundled
skills. This generator creates namespaced Hermes adapters such as
``soria-plan`` and ``soria-test`` while preserving the upstream workflow text.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = REPO_ROOT / "plugins" / "soria-stack" / "skills"
TARGET_DIR = REPO_ROOT / "plugins" / "hermes" / "skills"

SOURCE_REPO = "https://github.com/Soria-Inc/soria-stack"


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    return text[4:end], text[end + 5 :]


def frontmatter_value(frontmatter: str, key: str) -> str:
    lines = frontmatter.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith(f"{key}:"):
            continue
        raw = line.split(":", 1)[1].strip()
        if raw == "|":
            collected: list[str] = []
            for follow in lines[i + 1 :]:
                if follow and not follow.startswith((" ", "\t")):
                    break
                stripped = follow.strip()
                if stripped:
                    collected.append(stripped)
            return " ".join(collected)
        return raw.strip('"').strip("'")
    return ""


def target_name(source_name: str) -> str:
    return source_name if source_name == "soria-stack" else f"soria-{source_name}"


def title_for(name: str) -> str:
    return name.replace("-", " ").title()


def transform_body(body: str, name_map: dict[str, str]) -> str:
    body = body.replace("Codex adaptation", "Hermes adaptation")
    body = body.replace("Codex-native", "Hermes-facing")
    body = body.replace("Codex", "Hermes")
    body = body.replace("codex-adapter.md", "hermes-adapter.md")
    body = body.replace("mcp__soria__*", "Soria MCP tools")
    body = re.sub(r"\bmcp__soria__([A-Za-z0-9_]+)\b", r"\1", body)

    for source, target in sorted(name_map.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(
            rf"(?<![A-Za-z0-9_.-])/{re.escape(source)}(?=$|[\s`),.;:])"
        )
        body = pattern.sub(f"/{target}", body)

    return body.strip() + "\n"


def transform_description(description: str, name_map: dict[str, str]) -> str:
    description = description.replace("Codex", "Hermes")
    description = description.replace("mcp__soria__*", "Soria MCP tools")
    description = re.sub(r"\bmcp__soria__([A-Za-z0-9_]+)\b", r"\1", description)
    description = description.replace("Soria MCP tools tools", "Soria MCP tools")
    description = description.replace("`Soria MCP tools` tools", "`Soria MCP tools`")
    for source, target in sorted(name_map.items(), key=lambda item: len(item[0]), reverse=True):
        pattern = re.compile(
            rf"(?<![A-Za-z0-9_.-])/{re.escape(source)}(?=$|[\s`),.;:])"
        )
        description = pattern.sub(f"/{target}", description)
    return description


def shell_quote_single(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def generate() -> list[Path]:
    if not SOURCE_DIR.is_dir():
        raise SystemExit(f"missing source skill dir: {SOURCE_DIR}")

    sources = sorted(SOURCE_DIR.glob("*/SKILL.md"))
    name_map: dict[str, str] = {}
    parsed: list[tuple[str, Path, str, str]] = []

    for skill_md in sources:
        text = skill_md.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        source_name = frontmatter_value(fm, "name") or skill_md.parent.name
        desc = frontmatter_value(fm, "description") or f"Soria-stack {source_name} workflow."
        name_map[source_name] = target_name(source_name)
        parsed.append((source_name, skill_md, desc, body))

    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True)

    written: list[Path] = []
    for source_name, skill_md, desc, body in parsed:
        hermes_name = name_map[source_name]
        target = TARGET_DIR / hermes_name
        target.mkdir(parents=True)
        upstream_rel = skill_md.relative_to(REPO_ROOT)
        generated_body = transform_body(body, name_map)
        desc = transform_description(desc, name_map)
        description = (
            f"Soria Stack Hermes skill for {source_name}. {desc} "
            "Use for Soria data pipeline, dive, verification, promotion, "
            "or engineering workflow requests that match this topic."
        )

        out = f"""---
name: {hermes_name}
description: {shell_quote_single(description)}
metadata:
  source_repo: {SOURCE_REPO}
  upstream_skill: {upstream_rel.as_posix()}
  variant: hermes
  generated_by: scripts/sync-hermes-skills.py
---

# {title_for(hermes_name)}

Hermes adapter for upstream Soria-stack skill `{source_name}`.

Read `../../references/hermes-adapter.md` before acting.

## Hermes Runtime Notes

- Hermes skill name: `{hermes_name}`
- Upstream source: `{upstream_rel.as_posix()}`
- Soria MCP tools are exposed by the configured `sumo` MCP server without the
  legacy `mcp__soria__` prefix.
- This file is generated. Update the upstream Soria-stack skill or generator,
  then rerun `python3 scripts/sync-hermes-skills.py`.

## Upstream Workflow

{generated_body}"""
        target_file = target / "SKILL.md"
        target_file.write_text(out, encoding="utf-8")
        written.append(target_file)

    return written


def main() -> None:
    written = generate()
    for path in written:
        print(path.relative_to(REPO_ROOT))
    print(f"generated {len(written)} Hermes skill(s)")


if __name__ == "__main__":
    main()
