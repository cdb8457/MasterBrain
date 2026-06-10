---
title: "{{title}}"
type: raw-source
canonical: false
source_type: "{{article|transcript|youtube|paper|asset}}"
origin: "{{url or device or person}}"
captured_by: "{{agent or phone or clint}}"
project: "{{project or ''}}"
status: draft
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
checksum_or_stable_id: "{{sha256: or stable id}}"
tags: []
links: []
---

# {{title}}

> Preserved source — **do not edit the captured content below.** Interpretation
> belongs in agent notes or canonical pages, not here.

## Provenance

- Source type: {{article/transcript/youtube/paper/asset}}
- Origin: {{url / device / person}}
- Captured by: {{agent / phone / clint}} on {{date}}
- File(s): {{path under raw/...}}
- Stable id / checksum: {{...}}

## Captured content

{{paste or link the verbatim source. For binary assets, link the file in
raw/assets/ and describe it here.}}

---
*Register a structured source via:*
`python -m masterbrain add-source --path "raw/.../{{file}}" --source-type {{type}} --source-agent {{agent}} --project {{project}} --checksum {{id}}`
