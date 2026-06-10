---
title: "Shared External Agent Memory Graph"
type: concept
canonical: true
status: draft
project: second-brain
created: 2026-05-30
updated: 2026-05-30
tags: [architecture, memory, multi-agent, provenance]
links: ["[[Graphify Second Brain Operating Plan]]"]
---

# Shared External Agent Memory Graph

> **Canonical, shared truth — not owned by any agent.** This page describes the
> architecture of the brain itself. It does not ingest or summarize any old
> project.

## What it is

A local-first, provenance-aware, multi-agent memory substrate. Different agents
— Claude, Codex, Hermes/Herbie, GPT, Gemini, local Llama/Arcane, and the PMAX
agents — do **not** share hidden memory. They run in different systems, sessions,
and tools, and share only what they **explicitly write** into this external
layer. The brain turns those contributions into inspectable, source-backed,
attributable institutional memory.

## Core model

- **One canonical node per real thing.** A concept, entity, component, or project
  is represented by exactly one canonical page (`concepts/`, `entities/`,
  `components/`, `projects/`). Canonical pages are cleaned, durable, shared truth
  and are **not owned by any agent**.
- **Many attributed agent notes** orbit each canonical node. Each note records
  what *one* agent said, inferred, reviewed, built, or contradicted, and **links
  back** to the canonical node. Notes are perspectives, not truth.
- **Raw sources are preserved** under `raw/`, never silently rewritten. Synthesis
  happens in notes and canonical pages, not by mutating sources.
- **Structured memory** (`graph-memory/*.jsonl`) is the machine-readable layer:
  claims, reviews, links, edges, and sources, each carrying provenance.

The Markdown is the human-readable truth; the structured layer makes it
queryable; the graph (later) *reveals* relationships. The graph is not itself the
truth.

## Provenance & lifecycle

Every contribution can answer: *What do we know? Who said it? What source backs
it? Did Clint approve it? What is still draft? What contradicts it? What did each
agent contribute?* This is enforced by:

- **Attribution** — `source_agent` on claims, `agent:` on notes; canonical pages
  have neither (they are not owned).
- **Approval lifecycle** — `draft → proposed → reviewed → approved`, with
  `contested`, `rejected`, `deprecated` as off-ramps. **`approved` requires
  Clint's explicit sign-off**; agents may not self-approve. New contributions
  default to `draft`.
- **Append-only history** — reviews and links are appended, never overwritten, so
  a claim's evolution and supersession chain stay visible.
- **Evidence levels** — `explicit | inferred | speculative` — and optional
  `confidence`.

See [[CONVENTIONS]] and [`../graph-memory/schema.md`](../graph-memory/schema.md).

## Structure

Canonical hubs in `concepts/ entities/ components/ projects/`; attributed
satellites in `inbox/<agent>/` and `agents/<agent>/`; preserved material in
`raw/`; structured memory in `graph-memory/`. Agents and their colors are listed
in [`../agents/agent-registry.md`](../agents/agent-registry.md).

## Intended graph encoding (not built yet)

- Node **fill** = topic/community cluster.
- Node **border/ring** = source agent.
- **Edge color** = relationship type (`edge_type`).
- **Edge style** = review/evidence state.
- Node **shape** = node type.

One shared center (the canonical node) with colored, agent-specific satellites.

## Boundaries

- Default ingestion is **deny unless allowlisted**
  ([`../graph-memory/ingest-allowlist.md`](../graph-memory/ingest-allowlist.md)).
- Old projects are inventoried by name only — never summarized, canonicalized, or
  turned into claims — until Clint explicitly adds them.
- No whole-vault Graphify, no auto-canonicalization, no UI/MCP yet.

## Open questions

- How canonical pages get *promoted* from accumulated agent notes (the merge
  ritual) — to be defined in a later phase.
- Conflict resolution UX when agents contradict each other.

---
*Status `draft`. This is architecture, not approved doctrine, until Clint signs
off.*
