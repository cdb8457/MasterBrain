---
title: Unraid / Arcane Deployment Plan — MasterBrain Shared External Agent Brain
type: deployment-plan
canonical: true
project: second-brain / shared-external-agent-brain
status: draft
phase: 0 (planning) → enables Phase 1+ container work
owner: Clint
host_target: Unraid server, hosted via Arcane (Docker hoster)
created: 2026-05-30
updated: 2026-06-09
---

# Unraid / Arcane Deployment Plan

## Core principle

**The container is replaceable. The mounted vault is sacred.**

Everything durable — the Markdown wiki, `graph-memory/*.jsonl`, any generated
graph output — lives on a persistent host path bind-mounted into the container.
The image carries only code. Rebuilding, updating, or destroying the container
must never lose memory.

## Path model (read this first)

The same vault is referred to by three paths depending on where you stand:

| Context | Path | Notes |
|---------|------|-------|
| Local development | `MasterBrain/` (the connected workspace folder) | The dev vault. |
| Inside the container | `/data` | The mounted vault. Code lives separately at `/app`. |
| Unraid persistent storage | a bind-mounted share, e.g. `/mnt/user/appdata/masterbrain` | The real durable home. Clint picks the exact share. |

Wherever the architecture spec says `/config/wiki/<x>`, read it as the vault root
`<x>` — i.e. `MasterBrain/<x>` locally and `/data/<x>` in the container.

```
Unraid / Arcane
└── masterbrain (container)
    ├── /app    = code (from the image; replaceable)
    └── /data   = persistent vault (bind mount; SACRED)
                  ├── index.md, log.md
                  ├── projects/   concepts/   inbox/   entities/   sources/
                  ├── graph-memory/*.jsonl      (durable structured memory)
                  └── graphify-out/             (generated graph artifacts; cache)
```

## MVP scope (what this deployment is, today)

A small, self-hostable memory service with no cloud dependencies:

- **Python memory CLI** (`python -m masterbrain ...`) — the required MVP.
  Append-only JSONL store with provenance (agent, source, approval state) and
  event-sourced review history. Standard library only.
- **Optional lightweight FastAPI service** (`masterbrain.api`) — a thin HTTP
  surface (health, stats, add/list/get/review claims, edges, sources). Enabled
  by default in the container so Arcane has a real long-running service with a
  port; can be disabled for CLI-only use.
- **Durable storage**: `/data/graph-memory/*.jsonl` under the bind-mounted vault.
- **Plain Markdown vault** at `/data` remains usable as normal files (Obsidian,
  git, editors) — the memory layer never locks the wiki away.

### Explicitly NOT in the MVP (do not build yet)

- ❌ The visual graph UI (`masterbrain-ui`).
- ❌ Neo4j or any heavy database/service.
- ❌ Kubernetes / orchestration beyond a single container.
- ❌ External auth, SSO, or user accounts.
- ❌ Any cloud API requirement for basic operation.
- ❌ MCP server (`masterbrain-mcp`) — future phase.
- ❌ Scheduled Graphify runner (`graphify-runner`) — future phase.

## Component roadmap (target, not all built now)

| Component | Purpose | Status |
|-----------|---------|--------|
| `masterbrain` (CLI + store) | append/query/review claims, edges, sources | **MVP — built** |
| `masterbrain-api` | HTTP query/add/review over the store | **MVP — thin version built (optional)** |
| `masterbrain-mcp` | tools exposing memory to Claude / Codex / Hermes | future |
| `masterbrain-ui` | graph viewer | future |
| `graphify-runner` | scheduled graph generation into `graphify-out/` | future |

The MVP container runs CLI + optional API only. Future components can be added as
separate services in the same compose file, all sharing the one `/data` mount.

## Container specification

- **Image name**: `masterbrain:latest` (configurable via `MASTERBRAIN_IMAGE`).
- **Container name**: `masterbrain` (configurable via `MASTERBRAIN_CONTAINER_NAME`).
- **Base**: `python:3.12-slim`.
- **Code location**: `/app` (built into image).
- **Data location**: `/data` (bind-mounted host path — required).
- **Port** (only if the API is used): container `8077`, published to a host port
  via `MASTERBRAIN_API_PORT` (default `8077`). No port is needed for CLI-only use.
- **Restart policy**: `unless-stopped`.
- **Default command**: `python -m masterbrain.api` (lightweight FastAPI). Override
  to `tail -f /dev/null` for an idle container you drive with `docker exec`.

### Required volume mount

```
<host vault share>:/data
# Unraid example:
/mnt/user/appdata/masterbrain:/data
```

This is the only mount that matters. It must point at persistent Unraid storage,
not at the container's writable layer.

### Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MASTERBRAIN_VAULT_HOST_PATH` | `./` | Host path bound to `/data`. Set to the Unraid share. |
| `MASTERBRAIN_DATA_DIR` | `/data` | Vault path inside the container. |
| `MASTERBRAIN_IMAGE` | `masterbrain:latest` | Image tag. |
| `MASTERBRAIN_CONTAINER_NAME` | `masterbrain` | Container name. |
| `MASTERBRAIN_API_PORT` | `8077` | Host port for the API. |
| `MASTERBRAIN_API_HOST` | `0.0.0.0` | API bind address inside the container. |
| `TZ` | `UTC` | Timezone. |
| `PUID` / `PGID` | unset | Documented for a future hardening pass; **not yet wired** — the MVP image runs as root and writes `/data` as root. |

## How Arcane / Unraid should host it

1. **Pick the persistent share.** Create or choose an Unraid share, e.g.
   `/mnt/user/appdata/masterbrain`. This holds the entire vault and survives
   container changes. Seed it with the existing `MasterBrain/` contents.
2. **Get the code.** Clone/copy this repo to the Unraid box (or have Arcane build
   from it). The repo contains `Dockerfile`, `docker-compose.yml`, `app/`.
3. **Configure.** `cp .env.example .env`, then set
   `MASTERBRAIN_VAULT_HOST_PATH=/mnt/user/appdata/masterbrain` and a free
   `MASTERBRAIN_API_PORT`.
4. **Build & run.** `docker compose up -d --build`. Arcane can manage this as a
   stack; the only required volume is the `/data` bind mount above.
5. **Verify.** `curl http://<unraid-ip>:<port>/health` → `{"status":"ok",...}`,
   or `docker exec masterbrain python -m masterbrain stats`.

> Arcane note: because the container is replaceable, Arcane may recreate or
> update it freely **as long as the `/data` bind mount is preserved**. Never map
> `/data` to an anonymous/ephemeral volume.

## Backup expectations

- **What to back up**: the entire `/data` share — especially
  `graph-memory/*.jsonl` (the durable structured memory) and the Markdown wiki.
- **What you can throw away**: the container, the image, and `graphify-out/`
  (regenerable cache). Losing these costs nothing.
- **How**: Unraid appdata backup plugin, a scheduled `rsync`/snapshot of the
  share, and/or `git` history of the vault. JSONL is append-only and diff/merge
  friendly, so versioning it is straightforward if desired.
- **Test restores** by pointing a fresh container at a copy of the share — the
  CLI/API should come up with all claims intact.

## Update / rebuild expectations

- Updating the app = rebuild the image and `docker compose up -d`. The `/data`
  bind mount is untouched, so **no memory is lost**.
- The JSONL schema is additive and event-sourced (claims + reviews folded at
  read time); future code can read older records without migration. If a
  breaking schema change ever lands, write a migration that appends, never one
  that rewrites history in place.
- Durable memory must **never** live only inside the image or an anonymous
  volume. If the only copy of a claim is in the container, that is a bug.

## Permissions (MVP)

The container runs as **root**; files it writes under `/data` are root-owned.
On a standard Unraid appdata share this is fine and remains editable. If you need
files owned by a specific Unraid user (e.g. for SMB editing), that is a future
hardening item (`PUID`/`PGID` via an entrypoint that drops privileges) — not
wired in the MVP.

## First-run runbook

Step-by-step first hosted run (commands + expected outputs + troubleshooting):
[[Unraid / Arcane First-Run Runbook]]. **The API has no auth — LAN-only,
never internet-exposed.** After seeding, the Unraid share is the single source
of truth for durable vault content (Clint, 2026-06-10).

## Re-audit (Phase 1.10 — 2026-06-10)

Deployment files re-audited against the current app (now incl. guards, slugs,
lint, review-queue — all stdlib, **no dependency changes**):

- `Dockerfile`: still copies only `app/`; added a stdlib `HEALTHCHECK`
  (urllib against `/health`) and a no-auth/LAN-only warning. CMD unchanged.
- `docker-compose.yml`: already had the equivalent healthcheck; added the
  LAN-only warning and documented IP-prefixed port binding
  (`MASTERBRAIN_API_PORT=192.168.x.x:8077` or `127.0.0.1:8077`).
- `.env.example`: same LAN-only/IP-binding documentation; PUID/PGID still
  documented as NOT wired (deferred by decision D4, 2026-06-10).
- `.dockerignore` / `app/requirements.txt`: unchanged, still correct.
- *A live `docker build` has still never been run* (no Docker in the audit
  environments); first build happens on Unraid per the runbook — results to
  be recorded in the runbook's result log.

## Deployment readiness audit (Phase 1.5 — 2026-05-30)

Verified ready to configure in Arcane later:

- Dockerfile is correct by inspection (slim Python base, copies only `/app`,
  declares `VOLUME /data`, `EXPOSE 8077`, runs the API). *A live `docker build`
  was not run — Docker was unavailable in the audit environment.*
- `docker-compose.yml` mounts the host vault to `/data` and sets
  `MASTERBRAIN_DATA_DIR=/data`; env vars referenced match `.env.example` exactly.
- Durable memory is never image-only: `.dockerignore` excludes the vault, only
  `app/` is copied, `/data` is a runtime mount.
- `python -m masterbrain init` creates `/data/graph-memory/{claims,edges,sources}.jsonl`
  on an empty volume; `stats` works with `MASTERBRAIN_DATA_DIR=/data`. (Smoke
  tests passed against a verified faithful copy; the audit sandbox mount lagged
  behind the Windows files, which were confirmed complete by direct read.)
- Optional API exposes `GET /health`; FastAPI/uvicorn are pinned in
  `app/requirements.txt`. No Neo4j, no auth, no cloud dependencies.

## Open decisions for Clint (later)

- Exact Unraid share path for `/data`.
- Whether to version `graph-memory/*.jsonl` in git (history vs. quiet diffs).
- Host port for the API if exposed beyond localhost.
- When to introduce `masterbrain-mcp`, `graphify-runner`, and `masterbrain-ui`
  (each a later phase, each a sibling service sharing the same `/data`).

## Related

- [[shared-agent-brain-build-status]] — phase handoff and decisions.
- [[ingest-allowlist]] — what may be ingested (default-deny).
