---
title: Process — Spec-First Workflow & Operating Rules
type: governance
status: active
canonical: true
owner: Clint
created: 2026-06-09
updated: 2026-06-09
---

# Process — Spec-First Workflow & Operating Rules

**Binding on all agents working in this vault** (Claude, Codex, Hermes/Herbie,
GPT, Gemini, local Llama/Arcane, PMAX agents). Fresh sessions follow the read
order in rule 13: this file, then the
[handoff file](projects/second-brain/shared-agent-brain-build-status.md),
[[CONVENTIONS]], the
[ingest allowlist](graph-memory/ingest-allowlist.md), and — if touching
structured memory — the [schema](graph-memory/schema.md).

Set by Clint on 2026-06-09. These rules govern *how* work is done; CONVENTIONS
governs *what* notes look like.

## 1. Spec-first workflow

Do not build directly from a broad idea. Do not infer major decisions silently.
Do not jump ahead to later phases. Before implementing any new phase or
feature, present a spec containing:

1. The true goal, restated in one sentence.
2. The decision this work is supposed to help Clint make.
3. Assumptions.
4. Key decisions requiring Clint's verification.
5. A small scoped spec with acceptance criteria.
6. Test/verification steps.
7. **Then wait for Clint's approval.** Implement without waiting only if Clint
   explicitly says "implement now."

## 2. Small checkpoint rule

Work in small checkpoints. Deliver one piece at a time. Prefer the smallest
useful increment that can be reviewed and reversed.

## 3. Human verification before major decisions

Major decisions (architecture, schema changes, phase transitions, anything
touching canonical truth or the approval lifecycle) require Clint's explicit
verification before they take effect. Agents surface options; Clint decides.

## 4. Acceptance criteria before implementation

No implementation begins without written acceptance criteria (from the spec in
rule 1). If criteria are missing, write them and get them approved first.

## 5. Verification & self-critique after implementation

After implementing:

1. Self-critique against the acceptance criteria.
2. Run tests or smoke checks where possible.
3. Report what passed, what failed, and what remains paused.
4. Update the handoff file (rule 12).

## 6. Default-deny ingestion

Nothing enters the vault's structured memory or canonical pages unless it is on
[`graph-memory/ingest-allowlist.md`](graph-memory/ingest-allowlist.md). Old
projects are inventoried by name only until Clint explicitly allowlists them.

## 7. No Graphify / UI / MCP unless explicitly requested

No Graphify runs (whole-vault or partial), no graph UI work, and no MCP server
work unless Clint explicitly requests that specific work.

## 8. No pilot / content ingestion unless allowlisted

Phase 2 (pilot ingestion) stays PAUSED until Clint selects a pilot **and** adds
it to the ingest allowlist. No content ingestion of any project without both.

## 9. Container replaceable, vault sacred

Durable memory (Markdown + `graph-memory/*.jsonl`) lives only on the mounted
vault, never inside an image or anonymous volume. Any rebuild/update must
preserve the `/data` bind mount.

## 10. Agents cannot self-approve claims

`approved` status — on notes or structured claims — requires Clint's explicit
sign-off. New agent contributions default to `draft`. No agent may raise its
own (or another agent's) contribution to `approved`.

## 11. Agents cannot write canonical pages through automated write paths

Canonical pages (`concepts/`, `entities/`, `components/`, `projects/`) are
shared truth. Automated write paths (API, MCP, scripts, scheduled jobs) must be
confined to `inbox/<agent>/` and `agents/<agent>/`. Canonical pages change only
through Clint-supervised edits.

## 12. All phase work must update the handoff file

Every piece of phase work ends by updating
[`projects/second-brain/shared-agent-brain-build-status.md`](projects/second-brain/shared-agent-brain-build-status.md)
(and `log.md`) with what was done, what was decided, and what remains paused.

## 13. Fresh session read order

Every fresh agent session must read these first, in order:

1. `PROCESS.md` (this file)
2. [`projects/second-brain/shared-agent-brain-build-status.md`](projects/second-brain/shared-agent-brain-build-status.md)
3. [`CONVENTIONS.md`](CONVENTIONS.md)
4. [`graph-memory/ingest-allowlist.md`](graph-memory/ingest-allowlist.md)
5. [`graph-memory/schema.md`](graph-memory/schema.md) — if touching structured
   memory

## 14. GitHub / privacy rule

GitHub (private repo) is for **code, templates, schema, scaffold, and
architecture docs only**. Real vault content, raw sources (`raw/`), inbox notes
(`inbox/`), private agent notes (`agents/<agent>/`), JSONL structured memory
(`graph-memory/*.jsonl`), and graph outputs (`graphify-out/`) stay on the
mounted `/data` vault and are ignored by default (enforced via `.gitignore`).

## 15. Critic / reviewer rule

Second-agent reviews, architecture critiques, or model opinions must be saved
as **attributed agent notes** (per [[CONVENTIONS]]) with `status: draft` unless
Clint explicitly promotes them. They are perspectives, not canonical truth by
default — they never overwrite or directly edit canonical pages.
