---
title: Agent Registry
type: reference
status: active
phase: 1
canonical: true
owner: Clint
created: 2026-05-30
updated: 2026-05-30
---

# Agent Registry

The agents that may contribute attributed notes/claims to the brain, with the
colors used to encode **source agent** on graph node borders/rings. Canonical
pages are not owned by any agent; these colors apply to attributed contributions
only.

| Agent | Key | Inbox | Notes folder | Color |
|-------|-----|-------|--------------|-------|
| Hermes / Herbie | `hermes` | `inbox/hermes/` | `agents/hermes/` | `#4E79A7` |
| Claude | `claude` | `inbox/claude/` | `agents/claude/` | `#B07AA1` |
| Codex | `codex` | `inbox/codex/` | `agents/codex/` | `#59A14F` |
| GPT / OpenAI | `gpt` | — | `agents/gpt/` | `#E15759` |
| Gemini | `gemini` | — | `agents/gemini/` | `#F28E2B` |
| Local Llama / Arcane | `local-llama` | — | `agents/local-llama/` | `#BAB0AC` |
| PMAX Mousa | `mousa` | — | — | `#76B7B2` |
| PMAX Tarek | `tarek` | — | — | `#EDC948` |
| PMAX Dareen | `dareen` | — | — | `#FF9DA7` |
| Phone capture | `phone` | `inbox/phone/` | — | (raw intake, not an authoring agent) |

## Structured form

```yaml
agents:
  - key: hermes
    aliases: [herbie]
    color: "#4E79A7"
  - key: claude
    color: "#B07AA1"
  - key: codex
    color: "#59A14F"
  - key: gpt
    aliases: [openai]
    color: "#E15759"
  - key: gemini
    color: "#F28E2B"
  - key: local-llama
    aliases: [arcane, llama]
    color: "#BAB0AC"
  - key: mousa
    color: "#76B7B2"
  - key: tarek
    color: "#EDC948"
  - key: dareen
    color: "#FF9DA7"
```

These keys/colors mirror `AGENT_COLORS` in `app/masterbrain/store.py`. The
`source_agent` on a structured claim and the `agent:` in a note's frontmatter
must use one of these keys.

`inbox/phone/` is a raw-intake lane (captures from a phone), not an authoring
agent; items there are triaged into the right agent inbox or `raw/`.
