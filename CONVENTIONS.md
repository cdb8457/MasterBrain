---
title: Vault Conventions — Frontmatter & Model Rules
type: governance
status: active
phase: 1
canonical: true
owner: Clint
created: 2026-05-30
updated: 2026-05-30
---

# Vault Conventions

How notes are typed, attributed, and linked in the Shared External Agent Brain.
Read alongside [`graph-memory/schema.md`](graph-memory/schema.md) (structured
memory) and [`graph-memory/ingest-allowlist.md`](graph-memory/ingest-allowlist.md)
(what may be ingested).

## The model in one paragraph

There is **one canonical node per real thing** (a concept, entity, component, or
project). Canonical pages are **shared truth — not owned by any agent**. Around
them sit **many attributed agent notes** (perspectives, syntheses, reviews) that
**link to** the canonical node. **Raw sources are preserved** verbatim and never
silently rewritten. Structured claims/edges in `graph-memory/*.jsonl` are the
machine-readable layer; the Markdown is the human-readable layer. The graph
reveals the truth; it is not itself the truth.

## Important model rules (authoritative)

1. **Canonical pages are shared truth, not owned by an agent.** They carry
   `canonical: true` and **no `agent` field**. Anyone may improve them; no single
   agent signs them.
2. **Agent notes are attributed perspectives.** They carry `canonical: false`
   and a required `agent:` field. They represent what *that* agent said,
   inferred, reviewed, built, or contradicted.
3. **Raw sources are preserved.** Files under `raw/` are never edited for
   content. Cleaning/synthesis happens in agent notes or canonical pages, never
   by mutating the source.
4. **One canonical node represents the real thing.** Do not create duplicate
   canonical nodes for the same subject.
5. **Many agent notes/claims link to one canonical node** via
   `links: ["[[Canonical Name]]"]`.
6. **No approved claims or canonical "approved" status unless Clint explicitly
   approved them.** Agents may not self-approve.
7. **Default status for new agent contributions is `draft`.**
8. **Default ingestion policy is deny unless allowlisted** (see the allowlist).

## Node types

| `type` | Lives in | Canonical? | `agent` field |
|--------|----------|------------|---------------|
| `raw-source` | `raw/{articles,transcripts,youtube,papers,assets}/` | no | preserved-as: who captured it |
| `agent-note` | `inbox/<agent>/`, `agents/<agent>/` | no | **required** |
| `concept` | `concepts/` | **yes** | none |
| `entity` | `entities/` | **yes** | none |
| `component` | `components/` | **yes** | none |
| `project` | `projects/<name>/` | **yes** | none |
| `decision` | within the relevant `projects/<name>/` | yes (shared record) | none (records who decided in body) |
| `claim-review` | `inbox/<agent>/` or beside the claim | no | **required** (the reviewer) |
| `source-ref` | beside the raw file, or `raw/.../` | no | who registered it |
| `edge-note` | `graph-memory/` or `comparisons/` | no | who asserted it |
| `query` | `queries/` | no | optional |
| `comparison` | `comparisons/` | no | optional |

## Frontmatter

Every note starts with YAML frontmatter. Common fields:

```yaml
---
title: Human readable title
type: concept            # see node types above
canonical: false         # true ONLY for concept/entity/component/project/decision
agent: claude            # REQUIRED for agent notes; OMIT on canonical pages
status: draft            # draft | proposed | reviewed | approved | contested | deprecated
project: second-brain    # owning project, if any
source_refs: []          # paths/URLs/ids backing this note
created: 2026-05-30
updated: 2026-05-30
tags: []
links: []                # wiki links to related nodes, e.g. ["[[Team Forge]]"]
---
```

### Status vocabulary

`draft → proposed → reviewed → approved` (with `contested`, `rejected`,
`deprecated` as off-ramps) — the same lifecycle as `approval_status` in the
structured schema. **`approved` requires Clint's explicit sign-off.** New agent
contributions default to `draft`.

### Attribution rules

- If `canonical: true`, there must be **no `agent`** field — canonical pages are
  not owned.
- If `type: agent-note` (or any attributed note), `agent:` is **required** and
  must be a known agent from the registry.
- Agent notes should link back to the canonical node(s) they discuss via `links`.

## Linking

Use Obsidian-style wiki links: `[[Canonical Name]]`. A `[[link]]` that has no
page yet is fine — it marks a node worth creating. Prefer linking agent notes →
canonical pages (not agent → agent) so the canonical node stays the hub.

## Structured vs. Markdown

- **Markdown** (this vault): human-readable canonical pages, attributed notes,
  preserved sources.
- **Structured** (`graph-memory/*.jsonl`): claims, reviews, links, edges,
  sources — written via the `masterbrain` CLI/API. See
  [`graph-memory/schema.md`](graph-memory/schema.md).

Phase 1 establishes conventions only. **No structured claims are generated from
notes yet** — that is a later, explicitly-scoped phase.

## Visualization encoding (preserved for later, not built yet)

- Node fill = topic/community cluster
- Node border/ring = source agent (see [`agents/agent-registry.md`](agents/agent-registry.md))
- Edge color = relationship type (`edge_type`)
- Edge style = review/evidence state
- Node shape = node type
