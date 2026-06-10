---
title: MasterBrain — Index
type: index
status: active
phase: 1
canonical: true
owner: Clint
created: 2026-05-30
updated: 2026-06-09
---

# MasterBrain — Shared External Agent Brain

Local-first, provenance-aware, multi-agent memory. Agents share only what they
explicitly write here. One canonical node per real thing; many attributed agent
notes link to it; raw sources are preserved. See [[CONVENTIONS]] for the rules.

## Start here

- [[CONVENTIONS]] — frontmatter & model rules.
- [`graph-memory/schema.md`](graph-memory/schema.md) — structured memory schema.
- [`graph-memory/ingest-allowlist.md`](graph-memory/ingest-allowlist.md) — what may be ingested (default-deny).
- [`agents/agent-registry.md`](agents/agent-registry.md) — agents & colors.
- [`projects/second-brain/shared-agent-brain-build-status.md`](projects/second-brain/shared-agent-brain-build-status.md) — build status & phase handoff (read first if resuming).
- [`README.md`](README.md) — app/CLI & deployment.

## Vault map

| Folder | Purpose | Canonical? |
|--------|---------|------------|
| `raw/` | Preserved source material — `articles/`, `transcripts/`, `youtube/`, `papers/`, `assets/`. Never edited for content. | no |
| `inbox/` | Incoming attributed notes per lane — `hermes/`, `claude/`, `codex/`, `phone/`. | no |
| `agents/` | Per-agent attributed notes — `hermes/`, `claude/`, `codex/`, `gpt/`, `gemini/`, `local-llama/`. | no |
| `concepts/` | Canonical concept pages (shared truth). | **yes** |
| `entities/` | Canonical entities (people, orgs, tools). | **yes** |
| `components/` | Canonical components / building blocks. | **yes** |
| `projects/` | Canonical project pages, incl. `second-brain/`. | **yes** |
| `comparisons/` | Side-by-side analyses across nodes. | no |
| `queries/` | Saved questions / views over the brain. | no |
| `templates/` | Note templates for each node type. | n/a |
| `graph-memory/` | Structured memory: `*.jsonl`, `schema.md`, `ingest-allowlist.md`. | n/a |
| `graphify-out/` | Generated graph artifacts (cache; not built yet). | n/a |
| `app/` | The `masterbrain` memory CLI/API (maps to `/app` in the container). | n/a |

## Canonical concepts

- [[Shared External Agent Memory Graph]] — the architecture of this brain.

## Projects

- [[Graphify Second Brain Operating Plan]] — second-brain build plan.

## Notable agent notes (attributed, draft)

- [`inbox/claude/2026-06-09-obsidian-team-style-architecture-review.md`](inbox/claude/2026-06-09-obsidian-team-style-architecture-review.md)
  — Claude's Obsidian-team-style architecture review (first agent contribution).

## Status

Phase 1 (foundation structure & conventions) complete. **Phase 2 is paused —
no pilot is selected.** No old projects ingested; no structured claims generated
from notes yet; no Graphify/UI/MCP. First attributed agent note landed
2026-06-09 (Claude architecture review, draft). See the build-status handoff
for what is safe to do next.
