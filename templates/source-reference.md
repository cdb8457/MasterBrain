---
title: "Source: {{title}}"
type: source-ref
canonical: false
source_type: "{{article|transcript|youtube|paper|asset|chat|doc}}"
source_agent: "{{who registered it}}"
project: "{{project or ''}}"
path: "raw/{{...}}"
url: "{{original url, if any}}"
checksum_or_stable_id: "{{sha256: or stable id}}"
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
links: []
---

# Source: {{title}}

Pointer to a preserved source. The raw material itself lives under `raw/`; this
note carries its metadata and stable identity.

- Path: `raw/{{...}}`
- Original: {{url / origin}}
- Type: {{source_type}}
- Registered by: {{agent}} on {{date}}
- Stable id / checksum: {{...}}

## What it is

{{one or two lines — enough to decide whether to open it}}

## Used by

- [[{{Canonical Node or agent note}}]]

---
*Structured form:*
`python -m masterbrain add-source --path "raw/{{...}}" --source-type {{type}} --source-agent {{agent}} --title "{{title}}" --project {{project}} --checksum {{id}}`
