---
title: Memory Schema — Shared External Agent Brain
type: schema
status: active
phase: 1.8
schema_version: 0.6
owner: Clint
created: 2026-05-30
updated: 2026-06-09
---

# Memory Schema (v0.6)

Durable structured memory is **append-only JSONL** under the vault's
`graph-memory/` directory. Three logs:

| File | Holds |
|------|-------|
| `graph-memory/claims.jsonl` | claim records + their `review` and `link` events |
| `graph-memory/edges.jsonl`  | typed graph edges between nodes |
| `graph-memory/sources.jsonl`| raw source references |

## Append-only & event-sourced

Records are only ever **appended**. Nothing is rewritten in place. A claim's
*current* state is computed by folding its `review` and `link` events over the
original `claim` record at read time. This preserves full provenance — who said
it, when, from what source, whether it was approved, and what it supersedes.

Every record carries a `type` discriminator: `claim`, `review`, `link`, `edge`,
or `source`.

## Claim

A single attributed statement about one canonical subject.

| Field | Type | Notes |
|-------|------|-------|
| `claim_id` | string | `clm_…`, assigned on creation. |
| `canonical_subject` | string | The subject as given by the writer (display string, e.g. `Team Forge`). |
| `canonical_id` | string \| null | **(v0.6, additive)** Durable identity: the canonical page's relative path without `.md` (e.g. `concepts/team-forge`). Namespace-less values (e.g. `team-forge`) are *provisional* — no canonical page existed at write time (reported by `lint`). Computed at read time for pre-0.6 records; never rewritten. |
| `canonical_slug` | string \| null | **(v0.6, additive)** Slugified basename for display (e.g. `team-forge`). Secondary to `canonical_id`. |
| `claim` | string | The statement itself. |
| `source_agent` | string | Contributing agent: `claude`, `codex`, `hermes`, `gpt`, `gemini`, `llama`/`arcane`, `mousa`, `tarek`, `dareen`. |
| `source_type` | string \| null | Kind of source (`ui-review`, `build-notes`, `chat`, `doc`, …). |
| `source_refs` | list[string] | Source references (paths/URLs/ids). |
| `project` | string \| null | Owning project, if any. |
| `confidence` | float \| null | 0.0–1.0. |
| `evidence_level` | enum \| null | `explicit` \| `inferred` \| `speculative`. |
| `approval_status` | enum | `draft` \| `proposed` \| `reviewed` \| `approved` \| `contested` \| `rejected` \| `deprecated`. Current value is folded from `review` events. |
| `created_at` | ISO-8601 UTC | Creation time. |
| `updated_at` | ISO-8601 UTC | Advances when a `review`/`link` event touches the claim. |
| `related_to` | list | Loose associations. |
| `supports` | list | Claims/nodes this claim supports. |
| `contradicts` | list | Claims/nodes this claim contradicts. |
| `supersedes` | list | Claims this one supersedes. |
| `superseded_by` | list | Claims that supersede this one. |

### Review event (in `claims.jsonl`)

Append-only state change. Folded to set the claim's `approval_status` /
`updated_at`.

`event_id` (`rev_…`), `type: review`, `claim_id`, `approval_status`, `by`,
`note`, `created_at`.

### Link event (in `claims.jsonl`)

Append-only relationship change — adds a value to one of the claim's
relationship lists without rewriting the original record.

`event_id` (`lnk_…`), `type: link`, `claim_id`, `field` (one of `related_to` /
`supports` / `contradicts` / `supersedes` / `superseded_by`), `value`,
`created_by_agent`, `created_at`.

`supersede` is a convenience that emits two link events (new→`supersedes`→old,
old→`superseded_by`→new) and, by default, a `review` deprecating the old claim.

## Edge

A typed relationship between two nodes (claims, subjects, or sources).

| Field | Type | Notes |
|-------|------|-------|
| `edge_id` | string | `edg_…`. |
| `from_id` | string | Source node id/subject. |
| `to_id` | string | Target node id/subject. |
| `edge_type` | enum | `related_to` \| `supports` \| `contradicts` \| `derived_from` \| `mentions` \| `approved_by` \| `supersedes` \| `evidence_for` \| `source_of`. |
| `confidence` | float \| null | 0.0–1.0. |
| `evidence_level` | enum \| null | `explicit` \| `inferred` \| `speculative`. |
| `source_refs` | list[string] | Supporting source references. |
| `created_at` | ISO-8601 UTC | |
| `created_by_agent` | string | Agent that asserted the edge. |

## Source

A preserved reference to raw material. Sources are not rewritten.

| Field | Type | Notes |
|-------|------|-------|
| `source_id` | string | `src_…`. |
| `path` | string | Path/URL/id of the source. |
| `source_type` | string \| null | Kind of source. |
| `source_agent` | string \| null | Agent that registered it. |
| `title` | string \| null | Human-readable title. |
| `project` | string \| null | Owning project. |
| `created_at` | ISO-8601 UTC | |
| `checksum_or_stable_id` | string \| null | Checksum or other stable identifier for integrity/dedup. |

## Subject resolution (v0.6)

`canonical_subject` is resolved against the **derived slug registry** — a
read-only scan of pages with `canonical: true` under `concepts/ entities/
components/ projects/` (their filename slug, `title:`, and Obsidian-style
`aliases:` all resolve to the page's `canonical_id`). Rules:

- Qualified subjects (containing `/`) resolve directly by canonical_id.
- Unqualified subjects that match exactly one page resolve to it; matching
  multiple pages (e.g. `Arcane` with both `projects/arcane` and
  `entities/arcane`) is an **ambiguity error** — pages may share a basename
  across namespaces; only unqualified use is rejected.
- Normalized-identical forms auto-resolve (`TeamForge` ≡ `Team Forge` ≡
  `team_forge` ≡ `team-forge`).
- Fuzzy near-misses (difflib ≥ 0.85) are rejected with a suggestion;
  `--force-new-subject` overrides.
- Unknown subjects are accepted with a provisional namespace-less id and
  reported by `lint` (**revisit before MCP/agent-facing writes open**).

See `python -m masterbrain subjects` / `resolve` (both read-only).

## Backwards compatibility (legacy → canonical)

Pre-0.5 sample records are accepted and **normalized at read time** (never
rewritten on disk). Field mapping:

| Legacy (pre-0.5) | Canonical (v0.5) |
|------------------|------------------|
| `id` | `claim_id` / `edge_id` / `source_id` |
| `subject` | `canonical_subject` |
| `statement` | `claim` |
| `agent` | `source_agent` / `created_by_agent` |
| `source` (string) | `source_refs` (list) |
| `links` | `related_to` |
| `approval_state` | `approval_status` |
| `created` | `created_at` |
| `src` / `dst` / `rel` (edge) | `from_id` / `to_id` / `edge_type` |
| `ref` (source) | `path` |

Missing canonical fields are filled with `null`/`[]`. Because normalization is
read-only, old and new records safely coexist in the same JSONL log.

## Vocabularies (authoritative lists)

- **evidence_level**: `explicit`, `inferred`, `speculative`
- **approval_status**: `draft`, `proposed`, `reviewed`, `approved`, `contested`,
  `rejected`, `deprecated`
- **edge_type**: `related_to`, `supports`, `contradicts`, `derived_from`,
  `mentions`, `approved_by`, `supersedes`, `evidence_for`, `source_of`

These are enforced by the store (`app/masterbrain/store.py`) and the CLI.

## Forward compatibility

Schema changes must be **additive** and event-sourced. Add new fields with
sensible defaults; add new event types rather than mutating existing records. If
a breaking change is ever unavoidable, write a migration that *appends*
corrected records — never one that rewrites history in place.
