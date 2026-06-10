---
title: Shared External Agent Brain — Build Status & Handoff
type: handoff
project: second-brain / shared-external-agent-brain
current_phase: 1
phase_status: complete
owner: Clint
org: Arcane / PMAX
created: 2026-05-30
updated: 2026-06-09
---

# Shared External Agent Brain — Build Status & Handoff

> **Fresh-session agents: read this file first**, then [`PROCESS.md`](../../PROCESS.md)
> (binding spec-first workflow — no implementation without an approved spec).
> This file is the running record of what has been built, what was decided, and
> what must not be done yet.

## North star (do not lose this)

A local-first, **provenance-aware, multi-agent** memory substrate. Different
agents (Claude, Codex, Hermes/Herbie, GPT, Gemini, local Llama/Arcane, PMAX
Mousa/Tarek/Dareen) do **not** share hidden memory — they only share what they
explicitly write here. Every contribution should become **inspectable,
source-backed, attributable** institutional memory.

Core model: **one canonical shared node per real thing**, plus **separate
attributed agent notes/claims** that link back to it. Raw sources are preserved,
not silently rewritten. The graph reveals the truth; durable truth lives in
canonical Markdown + provenance-backed structured memory.

---

## Current phase: Phase 0 — Discovery & Planning ✅ COMPLETE

### Phase 0 discovery report

**1. What currently exists**

Nothing pre-existing. The connected workspace folder **MasterBrain was empty** —
no `index.md`, no `log.md`, no `projects/`, no `concepts/`, no `.md` files at
all. No `/config/wiki` is mounted to the agent session; the host/container vault
referenced in the spec is **not reachable** from here.

Per Clint's decision, the vault is being **bootstrapped fresh in MasterBrain**.

**2. What already matches the Shared External Agent Brain architecture**

Nothing pre-built to reconcile. Clean slate. The architecture spec (Clint's
kickoff prompt) is the design source of truth; there is no legacy structure that
already conforms or conflicts.

**3. What is missing (i.e. everything still to build)**

- Folder skeleton: `inbox/<agent>/`, `concepts/`, canonical `projects/`,
  `entities/`, `sources/`, and `graph-memory/` (`claims/`, `edges/`).
- `index.md` and `log.md` at the vault root.
- Frontmatter / schema conventions distinguishing **canonical nodes** from
  **attributed agent notes/claims**.
- Templates: canonical page, agent inbox note, claim, edge, source reference.
- Approval-state taxonomy (draft / proposed / approved / contested).
- Agent + color registry (encoded as data for later visualization).
- The `graphify-second-brain-operating-plan.md` page.
- The `shared-external-agent-memory-graph.md` concept page.

**4. What should be created in Phase 1** — see "Recommended Phase 1 action list"
below. Structure, conventions, templates, and a couple of seed pages only.

**5. What should remain out of scope** (Phase 0 and Phase 1)

- Any old/pre-existing project content (none exists now; policy holds for future
  imports — see `graph-memory/ingest-allowlist.md`).
- Whole-vault Graphify runs.
- MCP / API access for agents.
- The graph UI / visualization build.
- Auto-canonicalization of anything.
- The LooseIt pilot — not until Clint explicitly selects it.

**6. Risk of old-project contamination**

Currently **zero** — the vault is empty, so there is nothing old to contaminate.
The real risk has shifted: **(a)** if Clint later connects/merges his actual
existing wiki, the allowlist must be enforced *at that moment*; **(b)** scope
creep — an eager agent building Phase 1+ structure or running Graphify before
asked. Both are mitigated by the default-deny allowlist and phased delivery.

**7. Recommended Phase 1 action list** — see dedicated section below.

---

## Deployment architecture (added 2026-05-30, same session)

Clint clarified the target is **not** a local-only experiment: it deploys to his
**Unraid server via Arcane (Docker hoster)**, container-ready from day one.

**Path model** — same vault, three names:

| Context | Path |
|---------|------|
| Local development | `MasterBrain/` (connected workspace = vault root) |
| Inside the container | `/data` (vault) + `/app` (code, separate) |
| Unraid persistent share | e.g. `/mnt/user/appdata/masterbrain` → bind-mounted to `/data` |

Spec paths `/config/wiki/<x>` ≡ vault root `<x>` ≡ `MasterBrain/<x>` ≡ `/data/<x>`.

**Core deployment principle: the container is replaceable, the mounted vault is
sacred.** Durable memory (Markdown + `graph-memory/*.jsonl`) lives only on the
bind-mounted host share, never baked into the image. Rebuilds must not lose data.

**MVP shipped this session:** a stdlib Python memory CLI (`python -m masterbrain`)
with append-only, event-sourced JSONL storage (claims + reviews + edges +
sources), provenance (agent/source/approval-state), and a thin optional FastAPI
service. No cloud deps, no Neo4j, no UI, no MCP, no Graphify runner. Smoke-tested
end-to-end. Full plan: [[unraid-arcane-deployment-plan]].

## Files created (Phase 0 + deployment scaffolding)

Planning / governance (vault content):
- `graph-memory/ingest-allowlist.md` — default-deny ingestion policy.
- `projects/second-brain/shared-agent-brain-build-status.md` — this handoff.
- `projects/second-brain/unraid-arcane-deployment-plan.md` — hosting plan.

Container scaffolding (code, maps to `/app`; not vault truth):
- `Dockerfile`, `docker-compose.yml`, `.env.example`, `.dockerignore`,
  `.gitignore`, `README.md`.
- `app/masterbrain/` — `__init__.py`, `store.py`, `cli.py`, `__main__.py`,
  `api.py`; `app/requirements.txt`.

Directories created: `projects/second-brain/`, `graph-memory/`, `app/masterbrain/`.

## Files modified (Phase 0)

- None. No pre-existing files existed to modify.

## Commands run (Phase 0 + scaffolding)

- Filesystem inspection of the connected folder (`ls` / `find`) — confirmed
  MasterBrain, uploads, and outputs are empty; no `wiki`/`config` paths present.
- `mkdir -p` for `projects/second-brain/`, `graph-memory/`, `app/masterbrain/`.
- `py_compile` + an end-to-end CLI smoke test (init → add-claim → review →
  add-edge → stats) against a temp `MASTERBRAIN_DATA_DIR`. Passed.
- No Graphify run. No ingestion. No MCP. No deep crawl. No image push.

---

## Important decisions

- **Bootstrap fresh in MasterBrain.** The empty `MasterBrain` folder is the new
  vault root. (Chosen by Clint after discovery found no accessible `/config/wiki`.)
- **Path mapping:** every `/config/wiki/<path>` reference in the spec maps to
  `<MasterBrain>/<path>` in this deployment. A future agent should read spec
  paths through this mapping.
- **Default-deny ingestion** governs all current and future content
  (`graph-memory/ingest-allowlist.md`).
- **Phase discipline:** build only the phase requested; no UI, MCP, or Graphify
  yet.
- **Container-ready from day one:** Unraid + Arcane/Docker target; vault sacred,
  container replaceable; durable JSONL under the bind-mounted vault; no cloud
  services required for basic operation.
- **MVP app = Python CLI + optional thin FastAPI**, stdlib-only store. No Neo4j,
  no Kubernetes, no external auth.

## Known risks

- If Clint's real wiki is connected later, old-project content could be
  ingested by accident — enforce the allowlist before any merge.
- Scope creep into later phases (premature structure, Graphify, MCP).
- Path-mapping confusion between spec `/config/wiki/...` and MasterBrain root —
  documented above to prevent it.
- Canonical-vs-attributed model could collapse into "memory soup" if templates
  and frontmatter conventions aren't set before content lands — address early in
  Phase 1.

---

## Next recommended phase: Phase 1 — Foundation structure & conventions

**Goal:** stand up the empty skeleton, conventions, and templates so that when
real content arrives it lands in the right, attributable shape. No ingestion.

Recommended Phase 1 action list:

1. Create the vault skeleton (empty, with `.keep` / README stubs):
   `inbox/` with per-agent subfolders, `concepts/`, `projects/` (canonical),
   `entities/`, `sources/`, `graph-memory/claims/`, `graph-memory/edges/`.
2. Create root `index.md` (map of the vault) and `log.md` (append-only build log).
3. Define and document frontmatter conventions for: canonical node, agent note,
   claim, edge, source ref — including `node_type`, `agent`, `approval_state`,
   `source`, `links`.
4. Write the agent + color registry as structured data (table or YAML) — see
   reference palette below.
5. Add Markdown **templates** for each node type.
6. Seed two real pages as worked examples (not ingestion):
   `concepts/shared-external-agent-memory-graph.md` and
   `projects/second-brain/graphify-second-brain-operating-plan.md`.
7. Update this handoff: mark Phase 1 complete, list files, define Phase 2.

## What should NOT be done yet

- ❌ No Graphify run (not whole-vault, not partial).
- ❌ No MCP / API endpoints for agents.
- ❌ No graph UI / visualization.
- ❌ No ingesting, summarizing, or canonicalizing any old project.
- ❌ No LooseIt pilot until Clint explicitly selects it.
- ❌ No auto-generated claims from existing notes.
- ❌ No modifying content outside the Phase 0/Phase 1 allowlist.

---

## Reference: agent color palette (preserve for later visualization)

Encode as data now; render later. Node fill = topic cluster, node border = source
agent, edge color = relationship type, edge style = review/evidence state, node
shape = node type.

| Agent | Hex |
|-------|-----|
| Hermes / Herbie | `#4E79A7` |
| Claude | `#B07AA1` |
| Codex | `#59A14F` |
| GPT / OpenAI | `#E15759` |
| Gemini | `#F28E2B` |
| Local Llama / Arcane | `#BAB0AC` |
| PMAX Mousa | `#76B7B2` |
| PMAX Tarek | `#EDC948` |
| PMAX Dareen | `#FF9DA7` |

## Phase log

- **2026-05-30 — Phase 0 complete.** Discovery found empty vault; bootstrapped
  fresh in MasterBrain. Created ingest-allowlist and this handoff. No ingestion,
  no Graphify, no UI, no MCP. Next: Phase 1 foundation structure.
- **2026-05-30 — Deployment scaffolding added.** Clint set the target as Unraid
  via Arcane/Docker. Added container-ready MVP: Python memory CLI + optional thin
  FastAPI over append-only JSONL at `/data/graph-memory/`, plus `Dockerfile`,
  `docker-compose.yml`, `.env.example`, `.dockerignore`, `.gitignore`, `README`,
  and `unraid-arcane-deployment-plan.md`. Smoke-tested. Still no UI/MCP/Graphify/
  Neo4j; nothing ingested.
- **2026-05-30 — Phase 0.5 schema alignment.** Realigned the store/CLI/API to the
  canonical claim/edge/source model (see `graph-memory/schema.md`). Claims now
  use `claim_id`, `canonical_subject`, `claim`, `source_agent`, `source_type`,
  `source_refs`, `project`, `confidence`, `evidence_level`
  (explicit/inferred/speculative), `approval_status`
  (draft/proposed/reviewed/approved/contested/rejected/deprecated), `created_at`,
  `updated_at`, and relationship lists (`related_to`/`supports`/`contradicts`/
  `supersedes`/`superseded_by`). Edges use `edge_id`/`from_id`/`to_id`/`edge_type`
  (9-value enum)/`confidence`/`evidence_level`/`source_refs`/`created_at`/
  `created_by_agent`. Sources use `source_id`/`path`/`source_type`/`source_agent`/
  `title`/`project`/`created_at`/`checksum_or_stable_id`. Added append-only
  `link` + `supersede` operations. Legacy pre-0.5 records are normalized at read
  time (never rewritten). Full smoke test passed (legacy compat, review lifecycle,
  link, supersede/deprecate, edges, sources, stats, enum validation, append-only
  preservation). **Phase 1 is now safe to begin.**

  Files changed this phase: `app/masterbrain/store.py`, `app/masterbrain/cli.py`,
  `app/masterbrain/api.py` (rewritten to canonical schema);
  `graph-memory/schema.md` (new); `README.md`, this handoff (updated).

  Note: the Linux test-mount lagged behind the Windows file writes during this
  phase, so the smoke test ran against a verified faithful copy in the sandbox;
  the Windows-side source files were confirmed complete via direct read.
- **2026-05-30 — Phase 1 foundation structure & conventions.** Built the vault
  skeleton and authored conventions, templates, registry, and two architecture
  seed pages. **No ingestion, no claims from notes, no Graphify, no UI/MCP, no
  LooseIt pilot.** Phase 1 is complete. **Phase 2 is PAUSED — no pilot is
  selected.** Do not begin Phase 2 until Clint explicitly selects a pilot and
  adds it to `graph-memory/ingest-allowlist.md`.

  Directories created: `raw/{articles,transcripts,youtube,papers,assets}`,
  `inbox/{hermes,claude,codex,phone}`, `agents/{hermes,claude,codex,gpt,gemini,
  local-llama}`, `concepts`, `entities`, `components`, `comparisons`, `queries`,
  `templates`, `graphify-out` (`.gitkeep` in empty leaves).

  Files created: `index.md`, `log.md`, `CONVENTIONS.md`,
  `agents/agent-registry.md`, `raw/README.md`, `inbox/README.md`; templates
  `raw-source-note`, `agent-inbox-note`, `canonical-concept-page`, `project-page`,
  `decision-record`, `claim-review`, `source-reference`, `graph-edge-note`; seeds
  `concepts/shared-external-agent-memory-graph.md` and
  `projects/second-brain/graphify-second-brain-operating-plan.md`.

  Conventions established: node-type → folder map; canonical pages carry
  `canonical: true` and **no `agent`**; agent notes require `agent:` and default
  to `status: draft`; status lifecycle mirrors the structured `approval_status`
  with `approved` gated on Clint; raw sources preserved; one canonical node per
  real thing; many notes link to one node; default-deny ingestion.

  **Next recommended phase — Phase 2:** controlled pilot ingestion of ONE
  allowlisted project (likely LooseIt) into a canonical page plus attributed
  agent notes/claims, exercising the templates and the memory CLI end-to-end —
  **only after Clint adds the pilot to the ingest allowlist.** Still no Graphify,
  UI, or MCP.
- **2026-05-30 — Phase 1.5 deployment readiness audit.** Audited the 10
  deployment checks; the app + scaffolding are ready to be configured in Arcane
  later. Smoke tests passed: Python compile/import, `init` on an empty `/data`
  (creates `graph-memory/{claims,edges,sources}.jsonl`), and `stats` with
  `MASTERBRAIN_DATA_DIR=/data`. A live `docker build` was **not** run (Docker
  unavailable in the audit env); the Dockerfile was verified by inspection.
  One gap fixed: `PUID`/`PGID` were advertised but not wired, so `.env.example`,
  the deployment plan, and `README` now state the MVP runs as **root** (root-owned
  `/data`) with PUID/PGID a documented future hardening. No Neo4j, auth, or cloud
  deps added. `docker-compose.yml` needed no change (already mounts `/data` and
  matches `.env.example`). **Phase 2 remains PAUSED — no pilot selected.**
- **2026-05-30 — Phase 1.6 GitHub readiness.** Hardened `.gitignore` so the repo
  carries code + scaffolding only; private knowledge and runtime memory stay on
  `/data`. Now ignored: `.env`, `raw/` content, `inbox/` notes, per-agent
  `agents/<agent>/` notes, `graph-memory/*.jsonl`, `graphify-out/`, caches —
  while keeping structure (`.gitkeep`), area READMEs, and `agents/agent-registry.md`.
  Validated in a faithful temp git repo (with injected fake private files):
  **51 safe files would be committed; 0 private/runtime files tracked.** README
  gained a "Version control (private GitHub repo)" section (committed vs
  /data-only + clone/build/run). No repo was initialized and nothing was
  committed in the live folder (the audit ran in a temp mirror because the
  sandbox mount lagged the Windows writes). No sample data files added (schema.md
  + templates already document formats; live data stays on `/data`). **Phase 2
  still PAUSED — no pilot selected.**
- **2026-06-09 — First attributed agent note (Claude architecture review).**
  Clint asked Claude (Fable 5) to review the vault "like an Obsidian developer"
  and write it up as an attributed note. Created
  `inbox/claude/2026-06-09-obsidian-team-style-architecture-review.md`
  (`type: agent-note`, `node_type: agent_note`, `agent: claude`,
  `canonical: false`, `status: draft`, `project: second-brain`,
  `source_type: agent_architecture_review`; links to
  [[Shared External Agent Memory Graph]] and
  [[Graphify Second Brain Operating Plan]]). The note records: what is already
  right (Markdown-as-truth, hub/satellite topology, default-deny, event
  sourcing); pushback (Obsidian's native graph cannot render the intended
  encoding — Graphify must be custom; the JSONL layer is invisible to Obsidian;
  connectivity matters before visualization; conventions need code
  enforcement); five risks (JSONL invisibility, dual-write drift, fragile
  `canonical_subject` strings, approval bottleneck, missing API/MCP write
  guards); and a proposed non-pilot roadmap (write guards → reconciler/linter →
  canonical slug registry → review queue → Graphify/Cytoscape later).
  Also updated `log.md` and `index.md` (note listed; status line refreshed).
  **Boundaries honored: no Phase 2, no pilot, no ingestion, no Graphify run,
  no MCP/UI/API changes, no structured claims.** The note is `draft`; only
  Clint may approve. **Phase 2 remains PAUSED — no pilot selected.**
  Recommended next non-pilot phase: **Phase 1.7 — enforcement & hygiene
  tooling** (API/store write guards + reconciler/linter + canonical slug
  registry), which hardens the substrate without ingesting any content.
- **2026-06-09 — Process codified: spec-first workflow (`PROCESS.md`).** Clint
  set a binding operating process for all agents and all future MasterBrain
  work. Created **`PROCESS.md`** at the vault root with 12 rules: (1) spec-first
  workflow — goal in one sentence, the decision the work helps Clint make,
  assumptions, decisions requiring Clint's verification, scoped spec with
  acceptance criteria, test/verification steps, then **wait for Clint's
  approval** unless he explicitly says "implement now"; (2) small checkpoints,
  one piece at a time; (3) human verification before major decisions;
  (4) acceptance criteria before implementation; (5) post-implementation
  self-critique + tests + pass/fail/paused report; (6) default-deny ingestion;
  (7) no Graphify/UI/MCP unless explicitly requested; (8) no pilot/content
  ingestion unless allowlisted; (9) container replaceable, vault sacred;
  (10) agents cannot self-approve; (11) automated write paths confined to
  `inbox/<agent>/` + `agents/<agent>/` — never canonical pages; (12) all phase
  work updates this handoff. Also updated `README.md` (Status & scope +
  version-control list) and `log.md`. **No feature implemented, no Phase 2, no
  Graphify, no UI/MCP. Phase 2 remains PAUSED — no pilot selected.**
  Fresh-session agents: read `PROCESS.md` alongside this handoff before doing
  anything.
- **2026-06-09 — PROCESS.md patched with rules 13–15.** Three additions per
  Clint: **(13) fresh session read order** — PROCESS.md → this handoff →
  CONVENTIONS.md → ingest-allowlist → schema.md (if touching structured
  memory); **(14) GitHub/privacy rule** — the private repo carries code,
  templates, schema, scaffold, and architecture docs only; real vault content,
  `raw/`, `inbox/`, `agents/<agent>/` notes, `graph-memory/*.jsonl`, and
  `graphify-out/` stay on the mounted `/data` vault, gitignored by default;
  **(15) critic/reviewer rule** — second-agent reviews, critiques, and model
  opinions are saved as attributed agent notes at `status: draft` unless Clint
  explicitly promotes them; never canonical truth by default. README's status
  section now points at the read order. **No new feature, no Phase 2, no
  Graphify, no MCP/UI/API changes. Phase 2 remains PAUSED — no pilot selected.**
- **2026-06-09 — Phase 1.7 spec proposed (write guards + reconciler/linter).**
  Following PROCESS.md rule 1, Claude wrote a spec-only note:
  `inbox/claude/2026-06-09-spec-write-guards-reconciler.md` (`status:
  proposed`). Goal: mechanically enforce registered-agent / no-self-approval /
  draft-by-default rules in the store (CLI+API inherit) and add a **read-only**
  `lint` subcommand reporting Markdown↔JSONL drift. Five decisions await
  Clint's verification (D1 approval-guard semantics, D2 agent-key source of
  truth incl. the `local-llama` vs `llama` mismatch found in `store.py`,
  D3 strict-reject + `MASTERBRAIN_GUARDS=off` escape hatch, D4 lint check
  list, D5 CLI-only invocation). Out of scope: MCP/UI/new endpoints, slug
  registry, auto-fixing, Phase 2, ingestion, Graphify. **No implementation
  yet — waiting for Clint's approval per PROCESS.md. Phase 2 remains PAUSED.**
- **2026-06-09 — Phase 1.7 IMPLEMENTED: write guards + reconciler/linter.**
  Clint approved the spec with decisions D1–D5; implemented same session.
  **Guards (in `store.py`, inherited by CLI + API):** registered-agent
  enforcement via `VALID_AGENTS` (code mirror of `agents/agent-registry.md`;
  added `local-llama`; aliases `herbie`→`hermes`, `llama`/`arcane`→
  `local-llama`, `openai`→`gpt`); `phone` intake-only (sources yes, claims/
  reviews/links/edges no); new claims draft-only; `approved`/`reviewed`/
  `rejected`/`deprecated` require `by=clint` (D1; agents may submit `proposed`/
  `contested`); supersede-with-deprecate is clint-only (agents:
  `--no-deprecate`); `MASTERBRAIN_GUARDS=off` escape hatch warns loudly, never
  silent (D3). CLI exits 3 on guard rejection; API returns 403 (GuardError) /
  400 (validation) via a `_guarded` wrapper — no new endpoints. **Linter
  (`lint.py`, CLI `python -m masterbrain lint [--json]`, exit 0/1/2):**
  read-only checks for canonical-with-agent, missing/unregistered agent on
  attributed notes, inbox-folder mismatch, status vocabulary, unresolved
  wikilinks (warn), encoding artifacts/mojibake (D4 addition), dangling
  source_refs, phone-authored claims, elevated-status-not-clint, broken
  supersede pairs, edge/source agent checks, and registry↔code drift (D2).
  **Verification:** 32/32 store/CLI checks (AC1–AC4, AC7 incl. legacy compat +
  guards-off warning), 7/7 API checks via FastAPI TestClient (403/400/200),
  fixture vault fired all AC6 findings, live-vault lint = 0 errors /
  5 explainable warnings (CONVENTIONS example wikilinks; one real finding:
  `projects/second-brain/unraid-arcane-deployment-plan.md` lacks
  `canonical: true` — left for Clint, content untouched), exit codes 0/1/2
  verified, AC8 read-only proven by before/after checksums (fixture + live
  graph-memory). Note: the sandbox test-mount again lagged the Windows writes
  (as in Phase 0.5), so tests ran against verified faithful copies; the
  Windows-side files are confirmed complete. Files changed:
  `app/masterbrain/store.py`, `app/masterbrain/lint.py` (new),
  `app/masterbrain/cli.py`, `app/masterbrain/api.py`, `README.md`, this
  handoff, `log.md`. **Phase 1.7 COMPLETE. Still no Phase 2, no pilot, no
  ingestion, no Graphify, no MCP/UI, no structured claims from notes. Phase 2
  remains PAUSED — no pilot selected.** Next recommended non-pilot phase:
  canonical slug registry, then the Bases/Dataview review queue (separate
  specs, per PROCESS.md).
- **2026-06-09 — Phase 1.8 spec proposed (canonical slug registry).** Following
  PROCESS.md rule 1, Claude wrote a spec-only note:
  `inbox/claude/2026-06-09-spec-canonical-slug-registry.md` (`status:
  proposed`). Goal: `canonical_subject` resolves to one stable slug per
  canonical page so subject spellings can't fork the graph. Proposal: registry
  **derived** from canonical page filenames + `title:` + Obsidian-native
  `aliases:` frontmatter (no separate file to drift); slugify
  lowercase/hyphens; two-tier resolution — normalized-identical forms
  auto-resolve, fuzzy near-misses (difflib ≥ 0.85) reject with suggestion +
  `--force-new-subject` override; unknown subjects accept+warn pre-pilot (D2 —
  must be revisited/tightened before MCP opens); additive `canonical_slug`
  field on new records (schema 0.5 → 0.6, additive; legacy computed at read,
  never rewritten); read-only `subjects` / `resolve` CLI commands; lint adds
  unregistered-subject queue, duplicate-slug collision (error), and orphaned
  slug (rename) checks. Decisions D1–D5 await Clint's verification. Out of
  scope: Phase 2, ingestion, Graphify, MCP/UI, record rewriting,
  auto-creating canonical pages, rename automation. **No implementation —
  waiting for Clint's approval per PROCESS.md. Phase 2 remains PAUSED.**
- **2026-06-09 — Phase 1.8 IMPLEMENTED: canonical slug registry.** Clint
  approved with one correction: the durable identity is **path-based
  `canonical_id`** (relative canonical page path without `.md`, e.g.
  `concepts/team-forge`), with `canonical_slug` (slugified basename) as
  secondary display. **Implementation:** new `app/masterbrain/slugs.py` —
  derived registry scanning `canonical: true` pages under
  concepts/entities/components/projects; keys = filename slug + `title:` +
  Obsidian `aliases:`; resolution: qualified ids resolve directly;
  normalized-identical forms auto-resolve (`TeamForge` ≡ `Team Forge` ≡
  `team_forge`); unqualified multi-match (e.g. `Arcane` with both
  `projects/arcane` + `entities/arcane`) raises an ambiguity error requiring a
  qualified id — namespaced coexistence itself is allowed (D4); fuzzy
  near-miss (difflib ≥ 0.85) rejects with suggestions, `--force-new-subject`
  overrides (D3); unknown subjects accepted with provisional namespace-less id
  (D2 — **revisit before MCP**). `add_claim` stamps `canonical_id` +
  `canonical_slug` (schema 0.5 → 0.6, additive); legacy records computed at
  read time, never rewritten (D5). CLI: read-only `subjects` (+`--json`) and
  `resolve` commands; no new API endpoints (resolution errors surface as 400
  via the existing `_guarded` wrapper). Frontmatter parser moved to `slugs.py`
  (single shared parser; lint imports it). **Lint additions:**
  `shared-subject-key` (info; warn if an explicit alias is shared),
  `ambiguous-subject` on stored claims (error), `unregistered-subject`
  page-creation queue (warn), `orphaned-canonical-id` rename check (warn).
  **Verification:** 22/22 Phase 1.8 acceptance checks (after fixing one wrong
  test *expectation* — fixture has 3 canonical pages, not 4; code was
  correct), full Phase 1.7 regression 32/32, live vault: `subjects` lists the
  3 real canonical pages, lint = **0 errors / 4 known intentional CONVENTIONS
  example warnings**, `resolve` works, read-only verified (lint/subjects/
  resolve modified nothing; live `graph-memory/*.jsonl` don't exist yet —
  expected, nothing ever written there). Spec note checked for encoding
  artifacts: none (uses proper UTF-8). Sandbox mount lagged Windows writes
  again; tests ran against verified faithful copies patched with identical
  edits ( `slugs.py` synced fully and was used as-is). Files changed:
  `app/masterbrain/slugs.py` (new), `store.py`, `cli.py`, `lint.py`,
  `graph-memory/schema.md` (v0.6 additive + resolution rules), `README.md`,
  this handoff, `log.md`. **Phase 1.8 COMPLETE. Phase 2 remains PAUSED — no
  pilot selected. Still no ingestion, Graphify, MCP/UI, or pilot content.**
  Carried-forward flag: D2 accept+warn must be tightened before MCP/agent-
  facing writes open. Next recommended non-pilot phase: review queue
  (Bases/Dataview over draft/proposed items) — separate spec per PROCESS.md.
- **2026-06-09 — Phase 1.9 spec proposed (review queue).** Following
  PROCESS.md rule 1, Claude wrote a spec-only note:
  `inbox/claude/2026-06-09-spec-review-queue.md` (`status: proposed`). Goal:
  one cheap, current view of everything waiting on Clint. Design:
  **aggregation only** — reuses `Store.claims()` + the existing `Linter`, no
  new state, no schema change, no review *actions* (approval still happens via
  `review --by clint`). Surfaces: CLI `review-queue` with `--json` and
  `--group-by {status,agent,project,canonical-id}`; optional `--write`
  generating a single, clearly-banner-marked `queries/review-queue.md`
  (gitignored — claim text is private per PROCESS rule 14; lint exempts
  `type: generated-view`). Sections: draft/proposed claims, contested claims,
  unregistered-subject page-creation queue, orphan notes (D2: unlinked vs
  claimless, the latter informational pre-Phase-2), actionable lint findings
  (D5 include/exclude split; `wikilink-unresolved` excluded as
  CONVENTIONS-sanctioned). Plugin-free Markdown; Bases/Dataview deferred (D4).
  Decisions D1–D5 await Clint's verification. Out of scope: Phase 2,
  ingestion, Graphify, MCP, web UI, scheduler, queue-driven actions,
  auto-creating pages. **No implementation — waiting for Clint's approval per
  PROCESS.md. Phase 2 remains PAUSED.**
- **2026-06-09/10 — Phase 1.9 IMPLEMENTED: review queue.** Clint approved
  D1–D5 as proposed. **Implementation:** new `app/masterbrain/review_queue.py`
  (aggregation only — reuses `Store.claims()` + `Linter`; no new state, no
  schema change, no review actions); CLI `review-queue` with `--json`,
  `--group-by {status,agent,project,canonical-id}`, and `--write` which alone
  creates/overwrites `queries/review-queue.md` (plain Markdown, standard
  relative links — deliberately no wikilinks so the report can't create lint
  findings; frontmatter `type: generated-view`, `canonical: false`, banner,
  timestamp, regenerate command). Lint exempts `generated-view` via the
  governance allowlist. `.gitignore`: `queries/**` already ignored; added an
  explicit `queries/review-queue.md` line so intent survives any future
  un-ignoring (verified via temp git mirror: `git check-ignore` matches).
  Sections: pending (draft/proposed) claims with agent/project/canonical_id/
  age/source_refs; contested; unregistered subjects with claim counts;
  orphan notes in D2's two buckets; lint findings filtered per D5
  (errors + unregistered-subject, orphaned-canonical-id, dangling-source-ref,
  shared-subject-key, encoding-artifact; wikilink-unresolved excluded).
  **Bugs found & fixed during verification:** (1) note scan picked up
  `agents/agent-registry.md` as an "orphan note" — notes now require the
  `<top>/<agent>/...` depth; (2) the lint `encoding-artifact` message embedded
  the literal mojibake sequence, so the generated report that quotes lint
  findings flagged *itself* and broke idempotency — the message now shows the
  escaped form (`\\xe2\\u20ac…`), fixing both. **Verification:** 19/19 Phase
  1.9 checks (incl. checksum-proved read-only default, single-file `--write`,
  idempotency modulo timestamp, git-mirror ignore check), 1.7 regression
  32/32, 1.8 regression passes (the one listed "failure" is the known wrong
  test expectation from the 1.8 session — fixture has 3 pages, not 4;
  separately verified correct). **Live vault:** queue shows 0 pending /
  0 contested / 0 unregistered / 0 unlinked / 4 claimless notes (Claude's own
  review + 3 specs — correctly informational) / 0 actionable findings; report
  generated at `queries/review-queue.md`; lint stays 0 errors / 4 known
  CONVENTIONS-example warnings and does not flag the report. Files changed:
  `app/masterbrain/review_queue.py` (new), `cli.py`, `lint.py` (exemption +
  escaped artifact message), `.gitignore`, `README.md`, this handoff,
  `log.md`. **Phase 1.9 COMPLETE. Phase 2 remains PAUSED — no pilot
  selected. No ingestion, Graphify, MCP/UI, or pilot content.** Carried
  flags: D2 (slug accept+warn) still must tighten before MCP; revisit D5
  noise thresholds after the pilot. The non-pilot hardening track
  (1.7 guards → 1.8 identity → 1.9 queue) is now complete — the natural next
  step is Clint selecting a Phase 2 pilot, or a Graphify generator spec.
- **2026-06-10 — Phase 1.10 spec proposed (Unraid/Arcane first hosted run).**
  Following PROCESS.md rule 1, Claude wrote a spec-only note:
  `inbox/claude/2026-06-10-spec-unraid-first-hosted-run.md` (`status:
  proposed`). Goal: current foundation hosted as the `masterbrain` container
  on Unraid via Arcane, vault on a persistent share, rebuilds proven
  lossless. Scope: read-only re-audit of deployment files vs current code
  (new modules are stdlib-only — no dependency changes expected); optional
  Dockerfile/compose `HEALTHCHECK` (D3 — the only code-adjacent change); new
  canonical runbook `projects/second-brain/unraid-first-run-runbook.md` with
  exact commands + expected outputs (seed share per D5, compose up, /health,
  in-container `stats`/`lint`/`review-queue`, guard smoke against
  `MASTERBRAIN_DATA_DIR=/tmp/smoke` so `/data` is never written, rebuild
  persistence via checksums, backup/restore test, Arcane bind-mount warning).
  Execution split (D1): Claude prepares + verifies pasted outputs; Clint
  executes on the server (Claude has no access; Docker also unavailable in
  the sandbox — build has never run live, flagged as R1). Hard flags: the
  API has **no auth** → LAN-only, never internet-exposed (D2/R2); after
  seeding, the hosted share becomes the single source of truth (R6 — needs
  Clint's explicit acknowledgment). Decisions D1–D5 await Clint. Out of
  scope: Phase 2, ingestion, Graphify, MCP/UI, auth, PUID/PGID, extra
  services, app-code changes. **No changes made — waiting for Clint's
  approval per PROCESS.md. Phase 2 remains PAUSED.**
- **2026-06-10 — Phase 1.10 PREPARED: Unraid/Arcane first hosted run.** Clint
  approved D1–D5 + acknowledged R6 (after seeding, the Unraid share is the
  single source of truth; this machine becomes a working copy). **Claude-side
  work complete:** re-audited deployment files against current code — no
  dependency changes needed (all new modules stdlib); compose already carried
  a healthcheck; added the matching stdlib `HEALTHCHECK` to the Dockerfile
  (urllib → `/health`; no curl, no new deps) plus NO-AUTH/LAN-ONLY warnings
  in Dockerfile/compose/.env.example, and documented IP-prefixed port binding
  (`192.168.x.x:8077` / `127.0.0.1:8077`). New canonical runbook
  `projects/second-brain/unraid-first-run-runbook.md`: 11 steps with exact
  commands + expected outputs — share creation (default
  `/mnt/user/appdata/masterbrain:/data`), git clone (code/scaffold only, rule
  14), one-time vault seeding, `.env`, build/start, `/health`, in-container
  `stats`/`subjects`/`lint`/`review-queue` with the known-good expected
  values, guard smoke against `MASTERBRAIN_DATA_DIR=/tmp/smoke` (real vault
  untouched; checksum baseline), rebuild-persistence proof (`diff` of stats +
  jsonl checksums + `docker inspect` bind-mount check), backup/restore test
  with a disposable second container, Arcane invariants, troubleshooting
  table, and a result log to fill in. Deployment plan gained a Phase 1.10
  re-audit section; README points at the runbook. **Local verification:**
  compose YAML parses with the healthcheck; Dockerfile HEALTHCHECK present;
  live lint still 0 errors / 4 known example warnings; `subjects` now lists
  the runbook as the 4th canonical page (matching the runbook's own expected
  output). **No app-code changes; 1.7–1.9 behavior untouched. A live
  `docker build` still hasn't run anywhere — first build happens on Unraid.**
  **AWAITING CLINT:** run the runbook on Unraid/Arcane, paste outputs (esp.
  steps 5–10); Claude then verifies and records results in the runbook's
  result log. Remaining risks: R1 (build issues surface only on Unraid),
  R2 (no-auth API even LAN-only), R3 (root-owned files), R6 (acknowledged).
  **Phase 1.10 prepared, pending hosted execution. Phase 2 remains PAUSED —
  no pilot, no ingestion, no Graphify, no MCP/UI, no auth, no PUID/PGID.**
