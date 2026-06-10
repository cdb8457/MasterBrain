---
title: raw/ — Preserved Sources
type: governance
status: active
canonical: true
created: 2026-05-30
updated: 2026-05-30
---

# raw/ — Preserved Sources

Original source material, kept verbatim. **Never edit `raw/` files for content.**
Synthesis, cleanup, and interpretation happen in attributed agent notes
(`inbox/`, `agents/`) or canonical pages (`concepts/`, etc.) — never by mutating
the source.

Subfolders:

- `articles/` — saved articles / web pages.
- `transcripts/` — meeting/call/voice transcripts.
- `youtube/` — video captures and their transcripts.
- `papers/` — PDFs / academic or technical papers.
- `assets/` — images, audio, attachments.

Each raw item should have a companion **source reference** (see
[`../templates/source-reference.md`](../templates/source-reference.md)) capturing
its `source_type`, origin, capture date, and a `checksum_or_stable_id`. Structured
source records live in `graph-memory/sources.jsonl`.

Adding material here does **not** authorize ingestion. Ingestion is governed by
[`../graph-memory/ingest-allowlist.md`](../graph-memory/ingest-allowlist.md)
(default-deny).
