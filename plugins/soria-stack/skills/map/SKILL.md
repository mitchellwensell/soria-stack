---
name: map
description: Value mapping in Codex. Use when raw values need to be normalized to canonical forms across eras and sources. Drive through `mcp__soria__value_manage` (index / map / unmap / rename / delete) with evidence, not string matching.
metadata:
  source_repo: https://github.com/Soria-Inc/soria-stack
  upstream_skill: map/SKILL.md
  variant: codex
---

# Map

Codex adaptation of the `Soria-Inc/soria-stack` `/map` skill.

Read [../../references/codex-adapter.md](../../references/codex-adapter.md)
before acting.

## Focus

- `mcp__soria__schema_mappings(group_id=..., read=True)` to find the
  `schema_mapping_id` for each mapped column
- `mcp__soria__value_manage(schema_mapping_id=..., index=True)` to index values
- `mcp__soria__value_manage(schema_mapping_id=..., auto_map=True, read=True)`
  for obvious formatting variants
- `mcp__soria__value_manage(schema_mapping_id=..., read=True)` to inspect
  canonicals, unmapped values, mapped values, and suggestions
- `mcp__soria__value_manage(schema_mapping_id=..., map={source_id: target_id},
  unmap=[...], rename={canonical_id: "..."}, delete_ids=[...])` for mutations
- semantic normalization decisions with concrete evidence (typo vs rebrand
  vs methodology change vs genuinely distinct)
- mempalace support when available for ticker, company, or domain grounding
- re-publish bronze with `mcp__soria__warehouse_manage(group_id=...,
  publish=True, force=True)` after mapping updates so mapped values propagate
- hand off to `verify` after substantial mapping changes
