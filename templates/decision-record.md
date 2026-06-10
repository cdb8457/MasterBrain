---
title: "{{ADR-NNN: Decision title}}"
type: decision
canonical: true
status: proposed
project: "{{project}}"
decided_by: "{{clint or agent}}"
decided_on: "{{YYYY-MM-DD or '' if pending}}"
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
tags: [decision]
links: []
supersedes: []
superseded_by: []
---

# {{ADR-NNN: Decision title}}

> Lightweight decision record. Shared truth; records *who* decided in the body.
> Decisions that change earlier ones use `supersedes`/`superseded_by`.

## Status

{{proposed | accepted | rejected | superseded}} — decided by {{who}} on {{date}}.

## Context

{{the situation and forces at play}}

## Decision

{{what was decided}}

## Consequences

{{trade-offs, follow-ups, risks}}

## Alternatives considered

- {{option}} — {{why not}}

---
*Approval/acceptance reflects Clint's call unless explicitly delegated.*
