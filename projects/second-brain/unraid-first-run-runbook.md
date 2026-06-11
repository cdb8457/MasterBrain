---
title: Unraid / Arcane First-Run Runbook
type: project
canonical: true
status: draft
project: second-brain
created: 2026-06-10
updated: 2026-06-10
tags: [deployment, unraid, arcane, runbook]
links: ["[[unraid-arcane-deployment-plan]]"]
---

# Unraid / Arcane First-Run Runbook

> Step-by-step first hosted run of the `masterbrain` container. Each step shows
> the command and the **expected output**. Run in order; paste outputs back to
> the session for verification. Companion to
> [[unraid-arcane-deployment-plan|the deployment plan]].

**Before you start - two rules:**

1. **The container is replaceable; the mounted vault is sacred.** The only
   thing that matters is the `/data` bind mount.
2. **The API has NO AUTH. LAN-only.** Never port-forward, reverse-proxy, or
   otherwise expose it to the internet. Anyone who can reach the port can
   write draft claims.

**After step 3 completes, the Unraid share is the single source of truth for
durable vault content** (acknowledged by Clint, 2026-06-10). The dev machine's
copy is a working copy unless explicitly synced.

---

## 1. Pick the persistent share

Default (used throughout): host `/mnt/user/appdata/masterbrain` -> container
`/data`.

```bash
mkdir -p /mnt/user/appdata/masterbrain
```

## 2. Get the code (private GitHub repo - code/scaffold only)

```bash
cd /mnt/user/appdata
git clone <your-private-repo-url> masterbrain-code
cd masterbrain-code
```

Expected: a working tree with `app/`, `Dockerfile`, `docker-compose.yml`,
`.env.example` - and *no* real vault content (git carries scaffold only,
PROCESS.md rule 14).

## 3. Seed the vault share (one-time)

Copy the **current dev vault** (the whole `MasterBrain/` folder contents from
the dev machine - Markdown, `graph-memory/`, inbox/agent notes, everything)
into `/mnt/user/appdata/masterbrain`, e.g. over SMB or rsync. Then verify:

```bash
ls /mnt/user/appdata/masterbrain
```

Expected: `index.md  log.md  CONVENTIONS.md  PROCESS.md  concepts/  projects/
inbox/  agents/  graph-memory/  templates/  ...`

> From this moment the share is the source of truth (rule above).

## 4. Configure

```bash
cd /mnt/user/appdata/masterbrain-code
cp .env.example .env
nano .env
#   MASTERBRAIN_VAULT_HOST_PATH=/mnt/user/appdata/masterbrain
#   MASTERBRAIN_API_PORT=8077          # or a free port; LAN-ONLY, no auth!
```

## 5. Build & start

```bash
docker compose up -d --build
```

Expected: image builds (first build downloads `python:3.12-slim`, installs
fastapi/uvicorn), then `Container masterbrain  Started`.

```bash
docker ps --filter name=masterbrain
```

Expected: STATUS shows `Up ... (healthy)` after ~10-30s (the healthcheck pings
`/health` every 30s).

## 6. Verify the API (from a LAN machine)

```bash
curl http://<unraid-ip>:8077/health
```

Expected: `{"status":"ok","data_dir":"/data"}`

## 7. Verify the brain sees the real vault

```bash
docker exec masterbrain python -m masterbrain stats
docker exec masterbrain python -m masterbrain subjects
docker exec masterbrain python -m masterbrain lint
docker exec masterbrain python -m masterbrain review-queue
```

Expected (as of seeding, 2026-06-10):

- `stats`: `"claims": 0, "edges": 0, "sources": 0` (no structured memory yet -
  jsonl files are created on first `init`/API startup).
- `subjects`: 3 canonical pages (`concepts/shared-external-agent-memory-graph`,
  `projects/second-brain/graphify-second-brain-operating-plan`,
  `projects/second-brain/unraid-arcane-deployment-plan`) plus this runbook
  (`projects/second-brain/unraid-first-run-runbook`).
- `lint`: `0 error(s), 4 warning(s)` - the 4 known `wikilink-unresolved`
  CONVENTIONS documentation examples. **Any error = stop and report.**
- `review-queue`: 0 pending / 0 contested / 0 unregistered / 0 unlinked;
  several "linked but claimless (informational)" notes - expected.

## 8. Guard smoke test (does NOT touch the real vault)

Runs against a temp dir inside the container; `/data` is never written.

```bash
docker exec -e MASTERBRAIN_DATA_DIR=/tmp/smoke masterbrain \
  python -m masterbrain init
docker exec -e MASTERBRAIN_DATA_DIR=/tmp/smoke masterbrain \
  python -m masterbrain add-claim --canonical-subject "Smoke" \
  --claim "guard test" --source-agent mallory ; echo "exit=$?"
```

Expected: `GUARD REJECTED: source_agent 'mallory' is not a registered agent...`
and `exit=3`.

```bash
docker exec -e MASTERBRAIN_DATA_DIR=/tmp/smoke masterbrain \
  python -m masterbrain add-claim --canonical-subject "Smoke" \
  --claim "guard test" --source-agent claude ; echo "exit=$?"
```

Expected: a JSON claim record (`"approval_status": "draft"`) and `exit=0`.
The temp dir vanishes with the container; confirm the real vault is untouched:

```bash
md5sum /mnt/user/appdata/masterbrain/graph-memory/*.jsonl
```

Record these checksums - they are also the baseline for step 9.

## 9. Persistence proof (rebuild loses nothing)

```bash
docker exec masterbrain python -m masterbrain stats > /tmp/stats_before.json
docker compose up -d --build --force-recreate
docker exec masterbrain python -m masterbrain stats > /tmp/stats_after.json
diff /tmp/stats_before.json /tmp/stats_after.json && echo PERSISTENCE_OK
md5sum /mnt/user/appdata/masterbrain/graph-memory/*.jsonl
```

Expected: `PERSISTENCE_OK`; checksums identical to step 8. Also confirm the
bind mount survived recreation:

```bash
docker inspect masterbrain --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```

Expected: `/mnt/user/appdata/masterbrain -> /data` (a **bind** to the share -
if you ever see an anonymous volume here, stop: the vault is not persistent).

## 10. Backup / restore test

```bash
cp -a /mnt/user/appdata/masterbrain /mnt/user/appdata/masterbrain-restore-test
MASTERBRAIN_VAULT_HOST_PATH=/mnt/user/appdata/masterbrain-restore-test \
MASTERBRAIN_CONTAINER_NAME=masterbrain-restoretest \
MASTERBRAIN_API_PORT=8078 \
  docker compose -p mb-restore up -d
docker exec masterbrain-restoretest python -m masterbrain stats
docker compose -p mb-restore down
rm -rf /mnt/user/appdata/masterbrain-restore-test
```

Expected: the restore-test container reports identical `stats`. Then set up
the *ongoing* backup: Unraid appdata backup plugin (or scheduled rsync) of
`/mnt/user/appdata/masterbrain` - `graph-memory/*.jsonl` plus the Markdown is
everything.

## 11. Hand to Arcane

Manage the stack in Arcane with these invariants:

- The `/data` bind mount (`/mnt/user/appdata/masterbrain:/data`) must survive
  every recreate/update. Container, image: disposable.
- Restart policy `unless-stopped`; healthcheck is built in (step 5).
- Port stays LAN-only. **No auth exists. Do not expose.**

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Build fails on `COPY app/` | Build context wrong - run compose from the repo root (`masterbrain-code/`). |
| `unhealthy` in `docker ps` | API didn't start: `docker logs masterbrain`. If fastapi import fails, the image built without requirements - rebuild with `--no-cache`. |
| `/health` works on the box but not from LAN | Unraid firewall, or you bound the port to `127.0.0.1` in `.env`. |
| `stats` shows 0 but you expected content | Wrong share mounted - check `docker inspect` mounts (step 9). |
| Files on the share owned by root | Known MVP behavior (PUID/PGID deferred). Fine for appdata; SMB editing may need a chown - see deployment plan "Permissions". |
| `lint` reports errors | Stop; paste output back to the session before continuing. |

## Addendum - Phase 3a rollout: authenticated agent writes

After rebuilding with the Phase 3a image, ALL endpoints except `GET /health`
require a bearer token. Rollout (one-agent pilot, claude only - D6):

```bash
cd /mnt/user/appdata/masterbrain-code && git pull
docker compose up -d --build

# 1. Confirm the lockdown: unauthenticated reads must fail now
curl -s -o /dev/null -w "%{http_code}\n" http://<unraid-ip>:8077/stats   # expect 401
curl -s http://<unraid-ip>:8077/health                                   # expect {"status":"ok",...}

# 2. Issue the claude token (shown ONCE - store it in your password manager)
docker exec masterbrain python -m masterbrain token issue --agent claude

# 3. Pilot writes from a LAN machine (replace $TOK)
curl -s -H "Authorization: Bearer $TOK" http://<unraid-ip>:8077/stats     # expect JSON
curl -s -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"title":"Phase 3a pilot note","body":"hello from the claude token"}' \
  http://<unraid-ip>:8077/notes                                           # expect {"path":"inbox/claude/..."}
curl -s -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"canonical_subject":"projects/second-brain/unraid-arcane-deployment-plan","claim":"Phase 3a pilot claim","source_type":"api-test"}' \
  http://<unraid-ip>:8077/claims                                          # expect draft claim JSON

# 4. Negative checks (all must fail)
curl -s -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"canonical_subject":"projects/second-brain/unraid-arcane-deployment-plan","claim":"x","approval_status":"approved"}' \
  http://<unraid-ip>:8077/claims          # expect 403 (draft-only)
curl -s -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"from_id":"a","to_id":"b","edge_type":"approved_by"}' \
  http://<unraid-ip>:8077/edges           # expect 403 (privileged edge type)

# 5. Audit + queue
docker exec masterbrain python -m masterbrain audit --tail 20
docker exec masterbrain python -m masterbrain review-queue
```

Do NOT issue codex/hermes/gpt/gemini tokens until the claude pilot output has
been reviewed (D6). Revoke any time:
`docker exec masterbrain python -m masterbrain token revoke --agent claude`.
Still LAN-only; never port-forward or reverse-proxy.

## Result log

| Date | Step reached | Notes |
|---|---|---|
| 2026-06-10 | 11 (complete) | First hosted run complete per Clint: health OK, /data mounted from /mnt/user/appdata/masterbrain, rebuild persistence passed, backup/restore sanity check passed. |
| _(fill in after Phase 3a rollout)_ | | |
