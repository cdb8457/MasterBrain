---
title: "{{title}}"
type: agent-note
canonical: false
agent: "{{hermes|claude|codex|gpt|gemini|local-llama}}"
status: draft
project: "{{project or ''}}"
source_refs: []
confidence: {{0.0-1.0 or null}}
evidence_level: "{{explicit|inferred|speculative}}"
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
tags: []
links: ["[[{{Canonical Node}}]]"]
---

# {{title}}

*Attributed perspective by **{{agent}}**. This is one viewpoint, not shared
truth. It links to the canonical node(s) below.*

## Canonical node(s)

- [[{{Canonical Node}}]]

## What I observed / built / inferred

{{the substance — keep claims atomic and sourced where possible}}

## Evidence

- {{source_ref or [[raw/...]] }}

## Open questions / disagreements

- {{anything that contradicts another agent or the canonical page — note it; do
  not overwrite the canonical page}}

---
*Default status is `draft`. Do not mark `approved` — only Clint approves.*
*Structured claim (optional, later phase):*
`python -m masterbrain add-claim --canonical-subject "{{Canonical Node}}" --claim "{{...}}" --source-agent {{agent}} --source-type agent-note --evidence-level {{level}} --approval-status draft`
