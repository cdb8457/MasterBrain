# MasterBrain — Shared External Agent Brain

A local-first, **provenance-aware, multi-agent** memory substrate for Arcane /
PMAX. Different agents (Claude, Codex, Hermes/Herbie, GPT, Gemini, local
Llama/Arcane, PMAX Mousa/Tarek/Dareen) don't share hidden memory — they only
share what they explicitly write here. Every contribution becomes inspectable,
source-backed, attributable institutional memory.

This repository is **both** the Markdown vault and the small app that gives the
vault a structured, queryable memory layer.

> **Core principle: the container is replaceable, the mounted vault is sacred.**

## Layout

```
MasterBrain/                 # the vault root  (== /data in the container)
├── index.md, log.md         # (created in Phase 1)
├── projects/  concepts/  inbox/  entities/  sources/   # wiki (Phase 1)
├── graph-memory/
│   ├── ingest-allowlist.md  # default-deny ingestion policy
│   └── *.jsonl              # durable structured memory (runtime)
├── projects/second-brain/
│   ├── shared-agent-brain-build-status.md   # phase handoff — read this first
│   └── unraid-arcane-deployment-plan.md     # hosting plan
├── app/                     # application code  (== /app in the container)
│   ├── masterbrain/         # store + CLI + optional API
│   └── requirements.txt
├── Dockerfile  docker-compose.yml  .env.example
└── README.md
```

`app/` (code) and the vault content are separated in production: the image
carries only `/app`; the vault is bind-mounted at `/data`.

## Memory model

Memory is **append-only events** under `graph-memory/` (full field reference in
[`graph-memory/schema.md`](graph-memory/schema.md)):

- **claims** — an attributed statement about a `canonical_subject`, carrying
  `source_agent`, `source_type`, `source_refs`, `project`, `confidence`,
  `evidence_level` (`explicit`/`inferred`/`speculative`), `approval_status`
  (`draft`→`proposed`→`reviewed`→`approved`/`contested`/`rejected`/`deprecated`),
  and relationship lists (`related_to`, `supports`, `contradicts`, `supersedes`,
  `superseded_by`).
- **review** & **link events** — append-only changes to a claim's approval
  status or relationships. The current state is *folded* from these events at
  read time, so the original record and full history are never overwritten.
- **edges** — typed relationships (`edge_type` ∈ related_to, supports,
  contradicts, derived_from, mentions, approved_by, supersedes, evidence_for,
  source_of) with confidence/evidence/source refs.
- **sources** — preserved raw references (`path`, `source_type`, `title`,
  `project`, `checksum_or_stable_id`).

Legacy pre-0.5 records are normalized to this schema at read time (never
rewritten). The plain Markdown wiki stays fully usable in Obsidian / git / any
editor.

## Quick start (local dev)

The CLI uses only the Python standard library.

```bash
# point the store at this vault (instead of the container default /data)
export MASTERBRAIN_DATA_DIR="$(pwd)"

cd app
python -m masterbrain init
python -m masterbrain add-claim \
  --canonical-subject "Team Forge" \
  --claim "Onboarding uses a 3-step wizard flow" \
  --source-agent claude \
  --source-type ui-review \
  --source-ref "inbox/claude/2026-05-29-team-forge-ui-review.md" \
  --project team-forge --confidence 0.8 \
  --evidence-level inferred --approval-status draft

python -m masterbrain list-claims --canonical-subject "Team Forge"
python -m masterbrain review --claim-id clm_xxx --approval-status approved --by clint
python -m masterbrain link --claim-id clm_xxx --field supports --value clm_yyy --by-agent codex
python -m masterbrain supersede --old-claim-id clm_old --new-claim-id clm_new --by-agent hermes
python -m masterbrain stats
```

Durable data lands in `graph-memory/*.jsonl` (append-only; see
[`graph-memory/schema.md`](graph-memory/schema.md)).

## Write guards & lint (Phase 1.7)

The store enforces the provenance rules in code (CLI and API inherit them):

- **Registered agents only.** `source_agent` / `by` / `created_by_agent` must be
  a key from [`agents/agent-registry.md`](agents/agent-registry.md); aliases
  normalize (`herbie`→`hermes`, `llama`/`arcane`→`local-llama`,
  `openai`→`gpt`). `phone` is intake-only: it may register sources but never
  author claims, reviews, links, or edges.
- **Draft-only creation.** New claims must be `approval_status: draft`.
- **No self-approval.** `approved`, `reviewed`, `rejected`, and `deprecated`
  require `--by clint`. Agents may submit `proposed` or `contested`.
  `supersede` with auto-deprecate is clint-only; agents use `--no-deprecate`.
- **Escape hatch:** `MASTERBRAIN_GUARDS=off` bypasses guards for
  Clint-supervised repairs only — every bypass prints a loud warning; it is
  never silent. Guard rejections exit the CLI with code 3; the API returns 403
  (validation errors 400).

## Canonical subject identity (Phase 1.8)

Subjects resolve to a durable, path-based **canonical_id** (the canonical
page's relative path without `.md`, e.g. `concepts/team-forge`) via a registry
**derived** from canonical pages — filename slug, `title:`, and Obsidian-style
`aliases:` frontmatter. `Team Forge`, `team-forge`, `TeamForge`, and
`team_forge` all resolve to the same id; `projects/arcane` and
`entities/arcane` may coexist, but unqualified `Arcane` is then an ambiguity
error requiring a qualified id. Fuzzy near-misses are rejected with a
suggestion (`--force-new-subject` overrides); genuinely new subjects are
accepted with a provisional id and queued by `lint` for page creation.

```bash
python -m masterbrain subjects                  # list the derived registry
python -m masterbrain resolve --subject "X"     # dry-run resolution
```

New claims carry `canonical_id` + `canonical_slug` (schema v0.6, additive);
legacy records get theirs computed at read time, never rewritten.

## Authenticated agent writes (Phase 3a)

The API is **token-gated: every endpoint requires a per-agent bearer token
except `GET /health`.** Identity is derived from the token (conflicting
identity in a body is rejected). The network surface can only produce:
attributed draft notes in the agent's own `inbox/<agent>/` lane
(`POST /notes`), **draft-only** claims (`POST /claims`, unknown subjects →
409 with suggestions; `force_new_subject` is explicit + audited), sources,
and safe provenance edges (`approved_by`/`supersedes` rejected). **Review,
link, supersede, approval, and canonical writes do not exist over HTTP** —
Clint elevates via the local CLI only. Every write attempt and auth failure
lands in append-only `graph-memory/audit.jsonl` (payload digests only;
bodies size-capped before parsing).

```bash
# Clint, on the box:
docker exec masterbrain python -m masterbrain token issue --agent claude
docker exec masterbrain python -m masterbrain token list
docker exec masterbrain python -m masterbrain token revoke --agent claude
docker exec masterbrain python -m masterbrain audit --tail 50

# An agent, from the LAN:
curl -H "Authorization: Bearer $TOKEN" http://<host>:8077/stats
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"My note","body":"...","links":["[[Some Page]]"]}' \
  http://<host>:8077/notes
```

Token hashes (sha256 only — plaintext is shown once at issue) live in
`<vault>/.secrets/agent-tokens.json`, which is gitignored. Still LAN-only;
still never internet-exposed.

## MCP server (Phase 3b)

MCP-capable agents (Claude, Codex, Hermes harnesses) can use native tool
calls via the **agent-side** thin-client MCP server in [`mcp/`](mcp/README.md)
— it forwards everything to the authenticated API above, so all guards,
identity, and audit apply unchanged. Setup, contract, and token rules:
[`mcp/README.md`](mcp/README.md). The container image is unaffected.

## Review queue (Phase 1.9)

One view of everything waiting on Clint — draft/proposed claims, contested
claims, unregistered subjects (page-creation queue), orphan notes (unlinked;
linked-but-claimless is informational), and actionable lint findings:

```bash
python -m masterbrain review-queue                 # read-only terminal view
python -m masterbrain review-queue --json
python -m masterbrain review-queue --group-by agent   # status|agent|project|canonical-id
python -m masterbrain review-queue --write         # also emit the report below
```

`--write` (and only `--write`) creates/overwrites `queries/review-queue.md` —
a plain-Markdown, plugin-free generated view (`type: generated-view`, banner,
timestamp; never edit by hand). It embeds private claim text, so it is
**gitignored**. Approving still happens via `review --by clint`; the queue
only surfaces.

The read-only reconciler/linter reports Markdown↔JSONL drift and convention
violations — it never modifies anything:

```bash
python -m masterbrain lint          # human-readable
python -m masterbrain lint --json   # machine-readable
# exit codes: 0 clean, 1 warnings only, 2 errors
```

Checks include: canonical pages carrying an `agent:` field, attributed notes
missing/unregistered agents, inbox-folder vs `agent:` mismatches, unknown
statuses, unresolved wikilinks (warn), encoding artifacts (common mojibake
sequences caused by smart quotes, em-dashes, and arrows surviving a wrong
charset round-trip), dangling claim `source_refs`, phone-authored or
self-elevated claims, broken supersede pairs, and drift between
`VALID_AGENTS` in code and the agent registry (the registry file is the human
source of truth).

## Optional API

A thin FastAPI service (no auth, no database, no cloud) exposes the same store.

```bash
pip install -r app/requirements.txt
cd app && python -m masterbrain.api          # serves on 0.0.0.0:8077
# GET  /health  /stats  /claims  /claims/{id}  /edges  /sources
# POST /claims  /claims/{id}/review  /claims/{id}/link  /edges  /sources
```

## Deployment (Docker → Unraid via Arcane)

Target: Clint's Unraid server, hosted through Arcane. Build container-ready from
day one. Full detail in
[`projects/second-brain/unraid-arcane-deployment-plan.md`](projects/second-brain/unraid-arcane-deployment-plan.md).

### Path model

| Where | Path |
|-------|------|
| Local dev | `MasterBrain/` |
| In container | `/data` (vault) + `/app` (code) |
| Unraid persistent share | e.g. `/mnt/user/appdata/masterbrain` → `/data` |

### Run with Docker Compose

```bash
cp .env.example .env
# set MASTERBRAIN_VAULT_HOST_PATH to your persistent share (Unraid:
#   /mnt/user/appdata/masterbrain ; local: ./)
docker compose up -d --build

# verify
curl http://localhost:8077/health
docker exec masterbrain python -m masterbrain stats
```

### First hosted run

Follow the step-by-step runbook (commands, expected outputs, persistence
proof, backup/restore test, troubleshooting):
[`projects/second-brain/unraid-first-run-runbook.md`](projects/second-brain/unraid-first-run-runbook.md).
**The API has no auth — keep it LAN-only; never port-forward or reverse-proxy
it to the internet.**

### Hosting on Unraid / Arcane

- **Image / container name**: `masterbrain` (override via `MASTERBRAIN_IMAGE` /
  `MASTERBRAIN_CONTAINER_NAME`).
- **Required volume**: `<persistent share>:/data` — the only mount that matters.
  Never bind `/data` to an ephemeral/anonymous volume.
- **Port** (only if the API is used): container `8077` → host
  `MASTERBRAIN_API_PORT`.
- **Environment**: see `.env.example` (`MASTERBRAIN_VAULT_HOST_PATH`, `TZ`,
  optional `PUID`/`PGID`).
- Arcane may recreate/update the container freely **as long as the `/data` bind
  mount is preserved**.
- The MVP container runs as **root**, so files under `/data` are root-owned
  (fine on a typical Unraid appdata share). `PUID`/`PGID` are documented but not
  yet wired — a future hardening item.

### Backups

Back up the whole `/data` share — especially `graph-memory/*.jsonl`. The
container, image, and `graphify-out/` cache are disposable and regenerable. Use
the Unraid appdata backup plugin, a scheduled snapshot/rsync, and/or git history
of the vault. Test restores against a copy of the share.

### Updates / rebuilds

Rebuild the image and `docker compose up -d`; the `/data` mount is untouched, so
no memory is lost. The JSONL schema is additive and event-sourced — future code
reads older records without migration. **Durable memory must never live only
inside the image or an anonymous volume.**

## Version control (private GitHub repo)

**Use a PRIVATE GitHub repo.** The repo carries the *code and scaffolding*; the
actual knowledge and runtime memory live only on the Unraid `/data` volume and
are restored from backup — never committed.

**Committed to GitHub (safe):**
the `app/` code, `Dockerfile`, `docker-compose.yml`, `.env.example`, `README.md`,
`CONVENTIONS.md`, `PROCESS.md`, `index.md`, `log.md`, everything in `templates/`, the schema and
allowlist in `graph-memory/` (`schema.md`, `ingest-allowlist.md`), the
`projects/second-brain/` docs, the `concepts/` architecture seeds,
`agents/agent-registry.md`, and the folder placeholders (`.gitkeep`) + area
READMEs that preserve the structure.

**Stays ONLY on Unraid `/data` (never in git):**

- `.env` (secrets)
- `raw/` source material (private)
- `inbox/` and per-agent `agents/<agent>/` notes (attributed private content)
- `graph-memory/*.jsonl` (durable structured memory)
- `graphify-out/` (generated)
- caches / temp files

All of the above are enforced by [`.gitignore`](.gitignore). Folder structure is
kept via `.gitkeep` placeholders, so an empty clone still has the right skeleton.

### Clone / build / run

```bash
git clone <your-private-repo-url> masterbrain
cd masterbrain
cp .env.example .env
# set MASTERBRAIN_VAULT_HOST_PATH to your persistent share, e.g.
#   /mnt/user/appdata/masterbrain   (Unraid)   or   ./   (local dev)
docker compose up -d --build

# verify
curl http://localhost:8077/health
docker exec masterbrain python -m masterbrain stats
```

On a fresh host the `/data` share starts empty; the API initializes it on
startup (or run `docker exec masterbrain python -m masterbrain init`). **git
carries only code + scaffolding — bring memory with you by restoring `/data`
from backup, not from git.**

## Status & scope

- **Fresh agent sessions follow the read order in [`PROCESS.md`](PROCESS.md)
  rule 13** (PROCESS → handoff → CONVENTIONS → allowlist → schema).
- **All work follows the spec-first workflow in [`PROCESS.md`](PROCESS.md)**:
  spec + acceptance criteria + Clint's approval before implementation, small
  checkpoints, self-critique/tests after, handoff updated every time. Agents do
  not self-approve, do not write canonical pages via automated paths, and do
  not start Graphify/UI/MCP/pilot work unless Clint explicitly requests it.
- Read [`projects/second-brain/shared-agent-brain-build-status.md`](projects/second-brain/shared-agent-brain-build-status.md)
  for the current phase, decisions, and what must **not** be built yet.
- Ingestion is governed by
  [`graph-memory/ingest-allowlist.md`](graph-memory/ingest-allowlist.md)
  (default-deny). Old projects are excluded until Clint explicitly adds them.

Not built yet (by design): graph UI, MCP server, scheduled Graphify runner,
Neo4j, Kubernetes, external auth, any cloud dependency.
