---
title: Ingest Allowlist
type: governance
status: active
phase: 0
owner: Clint
maintained_by: shared-external-agent-brain
created: 2026-05-30
updated: 2026-05-30
---

# Ingest Allowlist — Shared External Agent Brain

This file is the **single source of truth for what may be ingested** into the
Shared External Agent Brain (structured memory, claims, edges, canonical nodes,
or any Graphify run).

## Governing rule: default-deny

**Nothing is in scope unless it is explicitly listed in the "Allowed scope"
section below.** If a path is not on the list, it is **excluded**. Silence means
no. Absence means excluded. There is no implicit inheritance from parent folders.

No agent (Claude, Codex, Hermes/Herbie, GPT, Gemini, local Llama/Arcane, PMAX
agents) may ingest, summarize, extract, canonicalize, or graph anything outside
this allowlist. Only **Clint** may add entries.

## Deployment note (read this first)

This vault was **bootstrapped fresh** on 2026-05-30. The connected workspace
folder `MasterBrain` was **empty** — there is no pre-existing `/config/wiki`
content mounted to the agent session.

- The vault root `/config/wiki/` referenced throughout the architecture spec maps
  to the **MasterBrain folder root** locally, and to **`/data`** inside the
  container (Unraid bind mount, e.g. `/mnt/user/appdata/masterbrain` → `/data`).
  Spec paths `/config/wiki/<x>` ≡ `MasterBrain/<x>` ≡ `/data/<x>`.
- Because the vault is empty, there are currently **no old projects** to exclude.
  The default-deny policy below still governs **any future import** of Clint's
  real existing wiki, should it be connected later.
- This allowlist governs ingestion regardless of host. Moving the vault into a
  container or onto Unraid does **not** widen scope.

## Allowed scope (Phase 0 / early MVP)

These are the only paths the brain may read and reason over for the MVP:

- `/config/wiki/index.md` — *(created in Phase 1)*
- `/config/wiki/log.md` — *(created in Phase 1)*
- `/config/wiki/projects/second-brain/graphify-second-brain-operating-plan.md` — *(created in Phase 1; architecture only)*
- `/config/wiki/concepts/shared-external-agent-memory-graph.md` — *(created in Phase 1; architecture only)*
- **New files and folders created specifically for this MVP**, including:
  - `/config/wiki/graph-memory/**` (this file lives here)
  - `/config/wiki/projects/second-brain/shared-agent-brain-build-status.md`
  - any `inbox/`, `concepts/`, `entities/`, `sources/`, `claims/`, `edges/`
    structures created by an explicit build phase
- **One explicitly selected pilot project — LooseIt** — *only after Clint
  confirms it.* Not yet active. Do not ingest LooseIt until it is moved from
  "pending" to "active" below.

## Explicitly excluded (until Clint adds them)

- **All old / pre-existing projects** anywhere in the wiki.
- Deep-crawling any existing project folder.
- Running Graphify across the whole wiki.
- Converting any old project into claims, edges, or canonical truth nodes.
- Treating any existing note as approved truth.
- Modifying old project pages.
- Creating duplicate canonical nodes for old projects.

### Inventory-by-name exception

Old projects **may be listed by name only** (a bare folder/title inventory) for
orientation. They may **not** be summarized, extracted, rewritten,
canonicalized, embedded, or added to structured memory. A name in an inventory
is not an ingestion grant.

## Pending (awaiting Clint's explicit approval)

| Candidate | Type | Status | Notes |
|-----------|------|--------|-------|
| LooseIt | pilot project | pending | First real pilot. Do not ingest until set to `active`. |

## How to add something to the allowlist

1. Clint adds the exact path (or pilot name) to **Allowed scope** above, or
   flips a Pending row to `active`.
2. Record the date and a one-line reason.
3. Only then may an agent ingest it.

Any agent that wants something added must **request it** here as a Pending row —
it must not ingest first and ask later.

## Change log

- 2026-05-30 — Created during Phase 0. Default-deny policy established. Vault
  bootstrapped fresh in MasterBrain (empty); no old projects present. LooseIt
  recorded as pending pilot.
