---
title: inbox/ — Agent Intake Lanes
type: governance
status: active
canonical: true
created: 2026-05-30
updated: 2026-05-30
---

# inbox/ — Agent Intake Lanes

Where new **attributed** contributions land before they are folded into canonical
pages. Every note here is a perspective owned by one agent — it carries an
`agent:` field and `canonical: false`, and links back to the canonical node(s)
it discusses.

Lanes:

- `hermes/`, `claude/`, `codex/` — notes authored by those agents.
- `phone/` — raw phone captures (quick thoughts, photos, voice). This is an
  intake lane, **not** an authoring agent; items are triaged into the right
  agent inbox or into `raw/`.

Rules (see [`../CONVENTIONS.md`](../CONVENTIONS.md)):

- Default `status: draft`. Nothing is `approved` without Clint's explicit
  sign-off.
- Canonical truth is **not** written here — inbox notes link to canonical pages
  in `concepts/`, `entities/`, `components/`, `projects/`.
- Use [`../templates/agent-inbox-note.md`](../templates/agent-inbox-note.md).

Longer-lived per-agent notes can graduate to `agents/<agent>/`.
