---
title: MasterBrain — Activity Log
type: log
status: active
canonical: true
owner: Clint
created: 2026-05-30
updated: 2026-06-09
---

# Activity Log

Append-only, newest first. One line (or short block) per meaningful change.
Detailed phase decisions live in
[`projects/second-brain/shared-agent-brain-build-status.md`](projects/second-brain/shared-agent-brain-build-status.md).

## 2026-06-10

- **Phase 1.10 cleanup.** Converted the first-run runbook to pure ASCII (the
  em-dashes/arrows/ellipses were valid UTF-8 but rendered as mojibake in
  cp1252 editors); wikilinks now use the filename stem (resolution verified).
  Deployment logic unchanged. Lint: 0 errors / 4 known example warnings.
  Phase 2 still PAUSED.
- **Phase 1.10 prepared — Unraid/Arcane first hosted run.** Re-audited
  Dockerfile/compose/.env.example vs current code (no dep changes); added
  stdlib Dockerfile HEALTHCHECK + NO-AUTH/LAN-ONLY warnings + IP-binding
  docs; wrote canonical runbook `unraid-first-run-runbook.md` (11 steps,
  expected outputs, guard smoke vs /tmp/smoke, persistence proof,
  backup/restore test, troubleshooting, result log). Locally verified:
  compose parses, lint 0 errors / 4 known warnings, runbook = 4th canonical
  subject. No app-code changes. Awaiting Clint's hosted execution +
  pasted outputs. Phase 2 still PAUSED.
- **Spec proposed — Phase 1.10 Unraid/Arcane first hosted run.** Claude
  authored `inbox/claude/2026-06-10-spec-unraid-first-hosted-run.md`
  (status: proposed): read-only re-audit of Dockerfile/compose/.env against
  current code, optional container healthcheck (only code-adjacent change),
  and a runbook (`unraid-first-run-runbook.md`) with exact commands +
  expected outputs — seeding, first run, in-container smoke against a temp
  dir (vault untouched), rebuild-persistence proof, backup/restore test.
  Execution split: Claude prepares, Clint runs on Unraid and pastes outputs.
  Key flags: API has no auth → LAN-only; hosted share becomes the single
  source of truth (R6). Decisions D1–D5 await Clint. **No changes made.
  Awaiting approval. Phase 2 still PAUSED.**

## 2026-06-09

- **Phase 1.9 implemented — review queue.** CLI `review-queue`
  (--json / --group-by status|agent|project|canonical-id / --write).
  Aggregation only over store + linter; no new state, schema, or actions.
  `--write` alone emits the generated, gitignored `queries/review-queue.md`
  (type: generated-view, banner, timestamp; lint-exempt; no wikilinks).
  Two bugs fixed in verification (registry file mis-bucketed as orphan note;
  lint artifact message embedded literal mojibake). 19/19 new checks +
  1.7/1.8 regressions pass. Live queue: 0 pending, 4 claimless notes (info),
  0 actionable findings; live lint unchanged (0 errors / 4 known examples).
  Phase 1.9 complete; Phase 2 still PAUSED.
- **Spec proposed — Phase 1.9 review queue.** Claude authored
  `inbox/claude/2026-06-09-spec-review-queue.md` (status: proposed):
  aggregation-only queue over existing store + linter (no new state) —
  draft/proposed claims, contested claims, unregistered-subject page-creation
  queue, orphan notes, actionable lint findings; groupable by agent/project/
  status/canonical_id. CLI `review-queue` (+`--json`), optional `--write` of a
  single generated, gitignored `queries/review-queue.md`; plugin-free
  Markdown; no web UI. Five decisions (D1–D5) await Clint. **No code written.
  Awaiting approval. Phase 2 still PAUSED.**
- **Phase 1.8 implemented — canonical slug registry.** Durable path-based
  `canonical_id` (e.g. `concepts/team-forge`) + secondary `canonical_slug`,
  resolved from a derived registry (canonical pages' filename slug, title,
  Obsidian `aliases:`). Variants auto-resolve; `projects/arcane` and
  `entities/arcane` coexist but unqualified `Arcane` is an ambiguity error;
  fuzzy near-misses reject with suggestion (`--force-new-subject` overrides);
  unknown subjects get provisional ids queued by lint. Schema 0.6 (additive);
  legacy computed at read, never rewritten. New read-only CLI: `subjects`,
  `resolve`. Lint adds ambiguous/unregistered/orphaned-subject checks.
  Verified: 22/22 new + 32/32 regression; live lint 0 errors / 4 known
  example warnings. Phase 1.8 complete; Phase 2 still PAUSED.
- **Spec proposed — Phase 1.8 canonical slug registry.** Claude authored
  `inbox/claude/2026-06-09-spec-canonical-slug-registry.md` (status: proposed)
  per PROCESS.md: derived registry from canonical page filenames + Obsidian
  `aliases:` frontmatter, two-tier resolution (auto-normalize identical forms;
  reject fuzzy near-misses with suggestion + `--force-new-subject` override),
  accept+warn for genuinely new subjects pre-pilot, additive `canonical_slug`
  field (schema 0.6), `subjects`/`resolve` CLI commands, new lint checks.
  Five decisions (D1–D5) await Clint. **No code written. Awaiting approval.
  Phase 2 still PAUSED.**
- **Phase 1.7 cleanup.** Added `canonical: true` to
  `projects/second-brain/unraid-arcane-deployment-plan.md` (the one real lint
  finding). Live lint now: 0 errors, 5 warnings (4 = CONVENTIONS example
  wikilinks; 1 = README's own documentation of the mojibake check contained the
  literal example sequence — since reworded to a plain description, resolving
  that warning). No code changed; Phase 2 still PAUSED.
- **Phase 1.7 implemented — write guards + reconciler/linter.** Clint approved
  the spec (D1–D5). Store now enforces: registered agents only (aliases
  normalize; `local-llama` added; `phone` intake-only), draft-only claim
  creation, clint-only `approved`/`reviewed`/`rejected`/`deprecated`,
  clint-only supersede-with-deprecate, loud-warning `MASTERBRAIN_GUARDS=off`
  escape hatch. CLI exits 3 on guard rejection; API maps guards to 403. New
  read-only `python -m masterbrain lint [--json]` (exit 0/1/2) reports
  conventions violations, Markdown↔JSONL drift, mojibake, and registry↔code
  drift. Verified: 32/32 CLI/store + 7/7 API checks, fixture + live lint,
  checksums prove read-only. Phase 1.7 complete; Phase 2 still PAUSED.
- **Spec proposed — Phase 1.7 write guards + reconciler/linter.** Claude
  authored `inbox/claude/2026-06-09-spec-write-guards-reconciler.md`
  (status: proposed) per the PROCESS.md spec-first workflow: goal, decision,
  assumptions, 5 decisions needing Clint's verification (approval-guard
  semantics, agent-key source of truth, strictness/escape hatch, lint scope,
  invocation), scope, out-of-scope, 8 acceptance criteria, test plan, files,
  risks. **No code written. Awaiting Clint approval. Phase 2 still PAUSED.**
- **PROCESS.md rules 13–15 added.** (13) Fresh session read order: PROCESS.md →
  handoff → CONVENTIONS.md → ingest-allowlist → schema.md (if touching
  structured memory). (14) GitHub/privacy: repo carries code/templates/schema/
  scaffold/architecture docs only; real content, raw sources, inbox/agent
  notes, JSONL memory, and graph outputs stay on `/data`, gitignored.
  (15) Critic/reviewer: second-agent reviews and critiques are attributed agent
  notes at `draft` unless Clint promotes them. No features; Phase 2 still
  PAUSED.
- **Process codified — spec-first workflow.** Created `PROCESS.md` at the vault
  root (12 binding rules set by Clint): spec + acceptance criteria + Clint
  approval before any implementation; small checkpoints; human verification of
  major decisions; post-implementation self-critique/tests/report; default-deny
  ingestion; no Graphify/UI/MCP unless explicitly requested; no pilot unless
  allowlisted; container replaceable, vault sacred; no self-approval; automated
  write paths never touch canonical pages; every phase updates the handoff.
  Updated `README.md` and the handoff to point at it. No features implemented;
  Phase 2 remains PAUSED.
- **First attributed agent note.** Claude wrote an Obsidian-team-style
  architecture review at
  `inbox/claude/2026-06-09-obsidian-team-style-architecture-review.md`
  (agent: claude, status: draft, project: second-brain). Covers what's right,
  pushback, risks (JSONL invisible to Obsidian, dual-write drift, fragile
  `canonical_subject` strings, approval bottleneck, missing write guards), and
  a non-pilot roadmap (write guards → reconciler/linter → slug registry →
  review queue → Graphify/Cytoscape later). **No Phase 2, no pilot, no
  ingestion, no Graphify, no MCP/UI/API changes, no structured claims.**
  Phase 2 remains PAUSED.

## 2026-05-30

- **Phase 1.6 — GitHub readiness.** Hardened `.gitignore` to exclude `.env`,
  `raw/` sources, `inbox/`/agent notes, `graph-memory/*.jsonl`, `graphify-out/`,
  and caches, while keeping code, docs, templates, schema, deployment docs, the
  registry, and folder placeholders tracked. Validated in a temp git mirror: 51
  safe files would commit, 0 private files. Added a README version-control
  section. Nothing committed; repo not initialized in the live folder.
- **Phase 1.5 — Deployment readiness audit.** Confirmed the app + Docker
  scaffolding are ready to host on Unraid via Arcane later. Smoke tests passed
  (compile/import, `init` on empty `/data`, `stats`). Docker build not run
  (unavailable in audit env); Dockerfile verified by inspection. Fixed misleading
  `PUID`/`PGID` docs (MVP runs as root). No heavy services, auth, or cloud deps.
  Phase 2 still paused — no pilot selected.
- **Phase 1 audit.** Verified the 8 readiness checks (skeleton, templates,
  conventions, registry, canonical/agent model, index/log, allowlist, handoff).
  Two small fixes: refreshed stale "does not exist yet" notes in the ingest
  allowlist (those files now exist) and made the **Phase 2 = PAUSED until a pilot
  is selected** state explicit in the handoff and index. No pilot selected; no
  ingestion; system paused.
- **Phase 1 — Foundation structure & conventions.** Created the vault skeleton
  (`raw/`, `inbox/`, `agents/`, `concepts/`, `entities/`, `components/`,
  `projects/`, `comparisons/`, `queries/`, `templates/`, `graph-memory/`,
  `graphify-out/`). Wrote `index.md`, `log.md`, `CONVENTIONS.md`, the agent
  registry, and 8 templates. Seeded two architecture pages
  ([[Shared External Agent Memory Graph]], [[Graphify Second Brain Operating Plan]]).
  No ingestion, no structured claims from notes, no Graphify, no UI/MCP, no
  LooseIt pilot.
- **Phase 0.5 — Schema alignment.** Realigned the memory store/CLI/API to the
  canonical claim/edge/source schema; added append-only `link`/`supersede`;
  legacy-record normalization at read time. (`graph-memory/schema.md`.)
- **Deployment scaffolding.** Container-ready MVP for Unraid via Arcane: memory
  CLI + optional FastAPI over JSONL at `/data/graph-memory/`, Docker assets,
  deployment plan. Vault sacred, container replaceable.
- **Phase 0 — Discovery.** Found the vault empty; bootstrapped fresh in
  MasterBrain. Created the ingest allowlist (default-deny) and build-status
  handoff.
