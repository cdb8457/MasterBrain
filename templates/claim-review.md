---
title: "Review of {{claim_id or claim summary}}"
type: claim-review
canonical: false
agent: "{{reviewer agent, or 'clint'}}"
status: draft
reviews_claim: "{{claim_id}}"
decision: "{{reviewed|approved|contested|rejected|deprecated}}"
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
links: ["[[{{Canonical Node}}]]"]
---

# Review of {{claim_id}}

*Human-readable companion to a structured review event. Attributed to the
reviewer.*

## Claim under review

> {{paste the claim text}} — by {{source_agent}}, evidence: {{evidence_level}},
> source: {{source_refs}}

## Assessment

{{does the evidence support it? is it consistent with the canonical node and
other agents' claims?}}

## Decision

`{{reviewed | approved | contested | rejected | deprecated}}` — rationale: {{...}}

> **`approved` is only valid if Clint approved it.** Agents may recommend, not
> self-approve.

---
*Apply the structured review (append-only):*
`python -m masterbrain review --claim-id {{claim_id}} --approval-status {{decision}} --by {{reviewer}} --note "{{rationale}}"`
