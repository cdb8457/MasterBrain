---
title: "Edge: {{from}} —{{edge_type}}→ {{to}}"
type: edge-note
canonical: false
created_by_agent: "{{agent}}"
from_id: "{{claim_id or [[Node]]}}"
to_id: "{{claim_id or [[Node]]}}"
edge_type: "{{related_to|supports|contradicts|derived_from|mentions|approved_by|supersedes|evidence_for|source_of}}"
confidence: {{0.0-1.0 or null}}
evidence_level: "{{explicit|inferred|speculative}}"
source_refs: []
status: draft
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
links: []
---

# Edge: {{from}} —{{edge_type}}→ {{to}}

Human-readable companion to a structured graph edge. Use for edges worth
explaining; routine edges can live only in `graph-memory/edges.jsonl`.

- From: {{from_id}}
- To: {{to_id}}
- Type: `{{edge_type}}`
- Asserted by: {{agent}} — confidence {{x}}, evidence {{level}}

## Why this edge

{{rationale and supporting source_refs}}

---
*Structured form (append-only):*
`python -m masterbrain add-edge --from-id {{from}} --to-id {{to}} --edge-type {{edge_type}} --created-by-agent {{agent}} --confidence {{x}} --evidence-level {{level}}`
