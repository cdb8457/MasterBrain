---
title: "Graphify Second Brain Operating Plan"
type: project
canonical: true
status: draft
project: second-brain
created: 2026-05-30
updated: 2026-05-30
tags: [second-brain, plan, graphify, architecture]
links: ["[[Shared External Agent Memory Graph]]"]
---

# Graphify Second Brain Operating Plan

> **Canonical project page — shared truth, not owned by an agent.** Describes how
> the second brain is built and operated. It does **not** ingest old projects or
> create project claims.

## Summary

The second brain is the [[Shared External Agent Memory Graph]] made operational:
a plain-Markdown vault plus a small, container-ready memory app, built in
deliberate phases. The graph layer ("Graphify") is a *later* visualization over
durable Markdown + provenance-backed structured memory — not the first thing
built and not the source of truth.

## Operating principles

- **The graph reveals the truth; it is not the truth.** Durable truth lives in
  canonical Markdown and `graph-memory/*.jsonl`.
- **The container is replaceable; the mounted vault is sacred.** Memory survives
  any rebuild (see [`shared-agent-brain-build-status.md`](shared-agent-brain-build-status.md)
  and [`unraid-arcane-deployment-plan.md`](unraid-arcane-deployment-plan.md)).
- **Default-deny ingestion.** Nothing enters structured memory unless it is on
  the allowlist.
- **Provenance first.** Attribute every contribution; approve only with Clint's
  sign-off.

## Architecture at a glance

- Vault root (`MasterBrain/` locally, `/data` in the container): the Markdown
  wiki + `graph-memory/`.
- App (`app/`, `/app` in the container): the `masterbrain` memory CLI + optional
  thin API over append-only JSONL.
- Future siblings sharing `/data`: an MCP server, a Graphify runner, and a graph
  UI — none built yet.

## Phased build

| Phase | Scope | State |
|-------|-------|-------|
| 0 | Discovery; bootstrap empty vault; ingest allowlist | done |
| 0.5 | Canonical claim/edge/source schema; memory CLI/API | done |
| — | Container/Unraid deployment scaffolding | done |
| 1 | Foundation structure, conventions, templates, seed pages | done |
| 2 | Controlled pilot ingestion of ONE allowlisted project (likely LooseIt) into canonical pages + attributed claims, exercising templates + CLI | planned |
| 3+ | Graphify runner → `graphify-out/`; then MCP tools for agents; then graph UI | later |

Detailed status, decisions, and "what not to do yet" live in
[`shared-agent-brain-build-status.md`](shared-agent-brain-build-status.md).

## Explicitly out of scope (for now)

Whole-vault Graphify, the graph UI, MCP, Neo4j/heavy services, auto-
canonicalization, and any ingestion of old projects or the LooseIt pilot until
Clint adds it to the allowlist.

## Workflow (once ingestion begins, later phase)

1. Preserve the source in `raw/` + a source reference.
2. Agents write attributed notes in `inbox/<agent>/` linking to a canonical node.
3. Atomic claims recorded via the CLI (`draft`).
4. Clint reviews; approved claims fold into the canonical page.
5. Edges connect nodes; Graphify later renders the picture.

---
*Status `draft`. Plan of record, pending Clint's approval to advance phases.*
