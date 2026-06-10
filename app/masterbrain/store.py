"""Append-only JSONL memory store for the Shared External Agent Brain.

Everything durable lives under ``$MASTERBRAIN_DATA_DIR`` (default ``/data``):

    /data/graph-memory/claims.jsonl    # claim + review + link events (append-only)
    /data/graph-memory/edges.jsonl     # typed graph edges between nodes
    /data/graph-memory/sources.jsonl   # raw source references

Event-sourced & append-only: a claim's *current* state is derived by folding its
review and link events over the original claim record. Nothing is ever
overwritten, so provenance ("who said it, when, from what source, was it
approved, what does it supersede") is preserved.

Legacy records written by the pre-0.5 schema are accepted: they are normalized to
the canonical schema at read time (never rewritten on disk). Standard library
only.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .slugs import build_key_index, build_registry, quiet_resolve, resolve_subject

# --- Canonical vocabularies --------------------------------------------------

EVIDENCE_LEVELS = ("explicit", "inferred", "speculative")

APPROVAL_STATUSES = (
    "draft",
    "proposed",
    "reviewed",
    "approved",
    "contested",
    "rejected",
    "deprecated",
)

EDGE_TYPES = (
    "related_to",
    "supports",
    "contradicts",
    "derived_from",
    "mentions",
    "approved_by",
    "supersedes",
    "evidence_for",
    "source_of",
)

# Relationship list fields carried on a claim and mutable via append-only links.
CLAIM_REL_FIELDS = ("related_to", "supports", "contradicts", "supersedes", "superseded_by")

# Known agents -> visualization colors. Not embedded per-record; available for
# the future registry / graph viewer to color nodes by source agent.
AGENT_COLORS = {
    "hermes": "#4E79A7",
    "herbie": "#4E79A7",
    "claude": "#B07AA1",
    "codex": "#59A14F",
    "gpt": "#E15759",
    "openai": "#E15759",
    "gemini": "#F28E2B",
    "llama": "#BAB0AC",
    "arcane": "#BAB0AC",
    "mousa": "#76B7B2",
    "tarek": "#EDC948",
    "dareen": "#FF9DA7",
    "local-llama": "#BAB0AC",
}

# --- Agent registry mirror (Phase 1.7 write guards) ---------------------------
# Human source of truth: agents/agent-registry.md. This is the code mirror used
# to enforce writes; the linter (`python -m masterbrain lint`) flags drift
# between this constant and the registry file.

VALID_AGENTS = (
    "hermes",
    "claude",
    "codex",
    "gpt",
    "gemini",
    "local-llama",
    "mousa",
    "tarek",
    "dareen",
)

# Aliases normalize to canonical keys before validation/storage.
AGENT_ALIASES = {
    "herbie": "hermes",
    "openai": "gpt",
    "llama": "local-llama",
    "arcane": "local-llama",
}

# Intake-only identities: may register raw sources, but may never author
# structured claims, reviews, links, or edges (CONVENTIONS: phone is a raw
# intake lane, not an authoring agent).
INTAKE_ONLY_AGENTS = ("phone",)

# The only identity allowed to grant elevated approval statuses (PROCESS.md
# rule 10: agents cannot self-approve).
APPROVER = "clint"

# Review statuses that require by=clint (approved per Clint's D1 decision,
# 2026-06-09). Registered agents may submit `draft`, `proposed`, `contested`.
CLINT_ONLY_STATUSES = ("approved", "reviewed", "rejected", "deprecated")


class GuardError(ValueError):
    """A write was rejected by a provenance/approval guard (PROCESS.md)."""


def guards_enabled() -> bool:
    """Hard-reject guards are on unless MASTERBRAIN_GUARDS=off (Clint-supervised
    repair escape hatch). Bypassing is never silent."""
    return os.environ.get("MASTERBRAIN_GUARDS", "").strip().lower() != "off"


def _warn_guards_off(action: str) -> None:
    print(
        f"WARNING: MASTERBRAIN_GUARDS=off — write guard BYPASSED for {action}. "
        "This mode is for Clint-supervised repairs only (PROCESS.md).",
        file=sys.stderr,
    )


def normalize_agent(
    agent: str | None,
    *,
    action: str,
    allow_intake: bool = False,
    allow_approver: bool = False,
    allow_none: bool = False,
    label: str = "agent",
) -> str | None:
    """Normalize an agent identity (aliases → canonical key) and enforce the
    registry guard. Raises GuardError on unregistered/forbidden identities
    unless MASTERBRAIN_GUARDS=off."""
    key = (agent or "").lower().strip()
    if not key:
        if allow_none:
            return None
        if not guards_enabled():
            _warn_guards_off(action)
            return None
        raise GuardError(f"{label} is required for {action}")
    key = AGENT_ALIASES.get(key, key)
    if key in VALID_AGENTS:
        return key
    if key in INTAKE_ONLY_AGENTS:
        if allow_intake:
            return key
        if not guards_enabled():
            _warn_guards_off(action)
            return key
        raise GuardError(
            f"{label} '{key}' is intake-only (see agents/agent-registry.md) and "
            f"may not {action}. Intake items must be triaged into an authoring "
            "agent's lane first."
        )
    if key == APPROVER:
        if allow_approver:
            return key
        if not guards_enabled():
            _warn_guards_off(action)
            return key
        raise GuardError(
            f"'{APPROVER}' is the approver identity, not a registered authoring "
            f"agent, and may not {action}. Use MASTERBRAIN_GUARDS=off for a "
            "supervised repair if truly needed."
        )
    if not guards_enabled():
        _warn_guards_off(action)
        return key
    raise GuardError(
        f"{label} '{agent}' is not a registered agent "
        f"(valid: {', '.join(VALID_AGENTS)}; aliases: "
        f"{', '.join(sorted(AGENT_ALIASES))}). See agents/agent-registry.md "
        "and PROCESS.md."
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    # Short, time-ordered id: prefix_<epoch-millis-hex><random>. No deps.
    ms = int(time.time() * 1000)
    return f"{prefix}_{ms:x}{secrets.token_hex(3)}"


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _validate(value: str | None, allowed: tuple[str, ...], label: str) -> None:
    if value is not None and value not in allowed:
        raise ValueError(f"{label} must be one of {allowed}, got {value!r}")


# --- Normalization of legacy (pre-0.5) records -------------------------------

def normalize_claim(rec: dict[str, Any]) -> dict[str, Any]:
    """Map any claim record (legacy or current) to the canonical claim schema."""
    out = dict(rec)
    out["claim_id"] = rec.get("claim_id") or rec.get("id")
    out["canonical_subject"] = rec.get("canonical_subject") or rec.get("subject")
    out["claim"] = rec.get("claim") or rec.get("statement")
    out["source_agent"] = (rec.get("source_agent") or rec.get("agent") or "").lower() or None
    out["source_type"] = rec.get("source_type")
    refs = rec.get("source_refs")
    if refs is None and rec.get("source"):
        refs = [rec["source"]]
    out["source_refs"] = _as_list(refs)
    out["project"] = rec.get("project")
    out["confidence"] = rec.get("confidence")
    out["evidence_level"] = rec.get("evidence_level")
    out["approval_status"] = rec.get("approval_status") or rec.get("approval_state") or "draft"
    created = rec.get("created_at") or rec.get("created")
    out["created_at"] = created
    out["updated_at"] = rec.get("updated_at") or created
    out["related_to"] = _as_list(rec.get("related_to") or rec.get("links"))
    out["supports"] = _as_list(rec.get("supports"))
    out["contradicts"] = _as_list(rec.get("contradicts"))
    out["supersedes"] = _as_list(rec.get("supersedes"))
    out["superseded_by"] = _as_list(rec.get("superseded_by"))
    for k in ("id", "subject", "statement", "agent", "source", "links",
              "approval_state", "created", "agent_color", "reviews"):
        out.pop(k, None)
    return out


def normalize_review(rec: dict[str, Any]) -> dict[str, Any]:
    out = dict(rec)
    out["approval_status"] = rec.get("approval_status") or rec.get("approval_state")
    out["created_at"] = rec.get("created_at") or rec.get("created")
    out.pop("approval_state", None)
    out.pop("created", None)
    return out


def normalize_edge(rec: dict[str, Any]) -> dict[str, Any]:
    out = dict(rec)
    out["edge_id"] = rec.get("edge_id") or rec.get("id")
    out["from_id"] = rec.get("from_id") or rec.get("src")
    out["to_id"] = rec.get("to_id") or rec.get("dst")
    out["edge_type"] = rec.get("edge_type") or rec.get("rel")
    out["confidence"] = rec.get("confidence")
    out["evidence_level"] = rec.get("evidence_level")
    out["source_refs"] = _as_list(rec.get("source_refs"))
    out["created_at"] = rec.get("created_at") or rec.get("created")
    out["created_by_agent"] = (rec.get("created_by_agent") or rec.get("agent") or "").lower() or None
    for k in ("id", "src", "dst", "rel", "agent", "created"):
        out.pop(k, None)
    return out


def normalize_source(rec: dict[str, Any]) -> dict[str, Any]:
    out = dict(rec)
    out["source_id"] = rec.get("source_id") or rec.get("id")
    out["path"] = rec.get("path") or rec.get("ref")
    out["source_type"] = rec.get("source_type")
    out["source_agent"] = (rec.get("source_agent") or rec.get("agent") or "").lower() or None
    out["title"] = rec.get("title")
    out["project"] = rec.get("project")
    out["created_at"] = rec.get("created_at") or rec.get("created")
    out["checksum_or_stable_id"] = rec.get("checksum_or_stable_id")
    for k in ("id", "ref", "agent", "created"):
        out.pop(k, None)
    return out


@dataclass
class Store:
    """Filesystem-backed, append-only memory store."""

    data_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("MASTERBRAIN_DATA_DIR", "/data"))
    )

    @property
    def graph_dir(self) -> Path:
        return self.data_dir / "graph-memory"

    @property
    def claims_path(self) -> Path:
        return self.graph_dir / "claims.jsonl"

    @property
    def edges_path(self) -> Path:
        return self.graph_dir / "edges.jsonl"

    @property
    def sources_path(self) -> Path:
        return self.graph_dir / "sources.jsonl"

    # -- setup -------------------------------------------------------------
    def init(self) -> list[Path]:
        """Ensure the graph-memory dir + JSONL files exist (no wiki scaffolding)."""
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []
        for p in (self.claims_path, self.edges_path, self.sources_path):
            if not p.exists():
                p.touch()
                created.append(p)
        return created

    # -- low-level append/read --------------------------------------------
    def _append(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _read(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        out: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    # -- claims ------------------------------------------------------------
    def add_claim(
        self,
        canonical_subject: str,
        claim: str,
        source_agent: str,
        source_type: str | None = None,
        source_refs: Iterable[str] | None = None,
        project: str | None = None,
        confidence: float | None = None,
        evidence_level: str = "explicit",
        approval_status: str = "draft",
        related_to: Iterable[str] | None = None,
        supports: Iterable[str] | None = None,
        contradicts: Iterable[str] | None = None,
        supersedes: Iterable[str] | None = None,
        superseded_by: Iterable[str] | None = None,
        force_new_subject: bool = False,
    ) -> dict[str, Any]:
        _validate(evidence_level, EVIDENCE_LEVELS, "evidence_level")
        _validate(approval_status, APPROVAL_STATUSES, "approval_status")
        if confidence is not None and not (0.0 <= float(confidence) <= 1.0):
            raise ValueError("confidence must be between 0 and 1")
        # Guard (D1/PROCESS.md rule 10): new claims are draft-only; agents may
        # not create pre-elevated claims. Registered authoring agents only.
        agent_key = normalize_agent(source_agent, action="author a claim",
                                    label="source_agent")
        if approval_status != "draft" and guards_enabled():
            raise GuardError(
                f"new claims must have approval_status 'draft' (got "
                f"{approval_status!r}). Elevation happens via review events by "
                f"'{APPROVER}' (PROCESS.md rule 10 / CONVENTIONS rule 6)."
            )
        if approval_status != "draft":
            _warn_guards_off("create a non-draft claim")
        # Phase 1.8: resolve the subject to a durable path-based canonical_id
        # (raises AmbiguousSubjectError / NearMissError per D3/D4; unknown
        # subjects get a provisional id per D2 and are reported by lint).
        res = resolve_subject(self.data_dir, canonical_subject,
                              force_new=force_new_subject)
        now = _now_iso()
        record = {
            "claim_id": _new_id("clm"),
            "type": "claim",
            "canonical_subject": canonical_subject,
            "canonical_id": res["canonical_id"],
            "canonical_slug": res["canonical_slug"],
            "claim": claim,
            "source_agent": agent_key,
            "source_type": source_type,
            "source_refs": _as_list(source_refs),
            "project": project,
            "confidence": confidence,
            "evidence_level": evidence_level,
            "approval_status": approval_status,
            "created_at": now,
            "updated_at": now,
            "related_to": _as_list(related_to),
            "supports": _as_list(supports),
            "contradicts": _as_list(contradicts),
            "supersedes": _as_list(supersedes),
            "superseded_by": _as_list(superseded_by),
        }
        self._append(self.claims_path, record)
        return record

    def review_claim(
        self, claim_id: str, approval_status: str, by: str, note: str | None = None
    ) -> dict[str, Any]:
        _validate(approval_status, APPROVAL_STATUSES, "approval_status")
        # Guard (D1, 2026-06-09): approved/reviewed/rejected/deprecated require
        # by=clint. Registered agents may submit draft/proposed/contested.
        by_key = normalize_agent(by, action="review a claim",
                                 allow_approver=True, label="by")
        if (
            approval_status in CLINT_ONLY_STATUSES
            and by_key != APPROVER
            and guards_enabled()
        ):
            raise GuardError(
                f"approval_status '{approval_status}' requires by='{APPROVER}'. "
                f"Agents may not approve, review, reject, or deprecate claims "
                f"(PROCESS.md rule 10; agent '{by_key}' may submit 'proposed' "
                "or 'contested' instead)."
            )
        if approval_status in CLINT_ONLY_STATUSES and by_key != APPROVER:
            _warn_guards_off(f"set '{approval_status}' as '{by_key}'")
        record = {
            "event_id": _new_id("rev"),
            "type": "review",
            "claim_id": claim_id,
            "approval_status": approval_status,
            "by": by_key,
            "note": note,
            "created_at": _now_iso(),
        }
        self._append(self.claims_path, record)
        return record

    def link_claim(
        self, claim_id: str, field_name: str, value: str, by_agent: str
    ) -> dict[str, Any]:
        """Append a relationship to a claim (related_to/supports/contradicts/
        supersedes/superseded_by) without rewriting the original record."""
        if field_name not in CLAIM_REL_FIELDS:
            raise ValueError(f"field must be one of {CLAIM_REL_FIELDS}, got {field_name!r}")
        agent_key = normalize_agent(by_agent, action="link claims",
                                    allow_approver=True, label="by_agent")
        record = {
            "event_id": _new_id("lnk"),
            "type": "link",
            "claim_id": claim_id,
            "field": field_name,
            "value": value,
            "created_by_agent": agent_key,
            "created_at": _now_iso(),
        }
        self._append(self.claims_path, record)
        return record

    def supersede_claim(
        self, old_claim_id: str, new_claim_id: str, by_agent: str, deprecate: bool = True
    ) -> list[dict[str, Any]]:
        """B supersedes A: record on both sides; optionally deprecate A.

        Guard (D1): deprecation is a clint-only review, so ``deprecate=True``
        requires by_agent=clint. Agents must pass ``deprecate=False``
        (CLI: --no-deprecate) and let clint deprecate the old claim.
        """
        by_key = normalize_agent(by_agent, action="supersede claims",
                                 allow_approver=True, label="by_agent")
        if deprecate and by_key != APPROVER and guards_enabled():
            raise GuardError(
                f"supersede with auto-deprecate requires by_agent='{APPROVER}' "
                f"because 'deprecated' is a clint-only status (D1). Agent "
                f"'{by_key}': re-run with --no-deprecate and ask "
                f"'{APPROVER}' to deprecate the old claim."
            )
        events = [
            self.link_claim(new_claim_id, "supersedes", old_claim_id, by_agent),
            self.link_claim(old_claim_id, "superseded_by", new_claim_id, by_agent),
        ]
        if deprecate:
            events.append(
                self.review_claim(old_claim_id, "deprecated", by=by_agent,
                                  note=f"superseded by {new_claim_id}")
            )
        return events

    def claims(
        self,
        subject: str | None = None,
        status: str | None = None,
        project: str | None = None,
    ) -> list[dict]:
        """Return current-state claims: fold review + link events over claims."""
        events = self._read(self.claims_path)
        claims: dict[str, dict[str, Any]] = {}
        for ev in events:
            if ev.get("type", "claim") == "claim":
                norm = normalize_claim(ev)
                norm["reviews"] = []
                claims[norm["claim_id"]] = norm
        for ev in events:
            kind = ev.get("type")
            if kind == "review":
                rev = normalize_review(ev)
                base = claims.get(rev.get("claim_id"))
                if base is not None:
                    base["approval_status"] = rev["approval_status"]
                    base["updated_at"] = rev["created_at"] or base["updated_at"]
                    base["reviews"].append(rev)
            elif kind == "link":
                base = claims.get(ev.get("claim_id"))
                fld = ev.get("field")
                if base is not None and fld in CLAIM_REL_FIELDS:
                    if ev.get("value") not in base[fld]:
                        base[fld].append(ev.get("value"))
                    base["updated_at"] = ev.get("created_at") or base["updated_at"]
        # Phase 1.8: legacy records (and any record without a stored identity)
        # get canonical_id/canonical_slug computed at read time — never
        # rewritten on disk (D5). quiet_resolve never raises and never fuzzes.
        registry = build_registry(self.data_dir)
        idx = build_key_index(registry)
        for base in claims.values():
            if not base.get("canonical_id"):
                cid, slug, _kind = quiet_resolve(registry, idx,
                                                 base.get("canonical_subject"))
                base["canonical_id"] = cid
                base["canonical_slug"] = base.get("canonical_slug") or slug
        result = list(claims.values())
        if subject is not None:
            s = subject.lower()
            result = [c for c in result if (c.get("canonical_subject") or "").lower() == s]
        if status is not None:
            result = [c for c in result if c.get("approval_status") == status]
        if project is not None:
            result = [c for c in result if c.get("project") == project]
        return result

    def get_claim(self, claim_id: str) -> dict[str, Any] | None:
        for c in self.claims():
            if c["claim_id"] == claim_id:
                return c
        return None

    # -- edges -------------------------------------------------------------
    def add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: str,
        created_by_agent: str,
        confidence: float | None = None,
        evidence_level: str | None = None,
        source_refs: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        _validate(edge_type, EDGE_TYPES, "edge_type")
        _validate(evidence_level, EVIDENCE_LEVELS, "evidence_level")
        if confidence is not None and not (0.0 <= float(confidence) <= 1.0):
            raise ValueError("confidence must be between 0 and 1")
        agent_key = normalize_agent(created_by_agent, action="assert an edge",
                                    allow_approver=True, label="created_by_agent")
        record = {
            "edge_id": _new_id("edg"),
            "type": "edge",
            "from_id": from_id,
            "to_id": to_id,
            "edge_type": edge_type,
            "confidence": confidence,
            "evidence_level": evidence_level,
            "source_refs": _as_list(source_refs),
            "created_at": _now_iso(),
            "created_by_agent": agent_key,
        }
        self._append(self.edges_path, record)
        return record

    def edges(self) -> list[dict[str, Any]]:
        return [normalize_edge(e) for e in self._read(self.edges_path)]

    # -- sources -----------------------------------------------------------
    def add_source(
        self,
        path: str,
        source_type: str | None = None,
        source_agent: str | None = None,
        title: str | None = None,
        project: str | None = None,
        checksum_or_stable_id: str | None = None,
    ) -> dict[str, Any]:
        # Sources: registered agents, the intake-only 'phone' lane, and clint
        # may register raw sources; source_agent may also be omitted.
        agent_key = normalize_agent(source_agent, action="register a source",
                                    allow_intake=True, allow_approver=True,
                                    allow_none=True, label="source_agent")
        record = {
            "source_id": _new_id("src"),
            "type": "source",
            "path": path,
            "source_type": source_type,
            "source_agent": agent_key,
            "title": title,
            "project": project,
            "created_at": _now_iso(),
            "checksum_or_stable_id": checksum_or_stable_id,
        }
        self._append(self.sources_path, record)
        return record

    def sources(self) -> list[dict[str, Any]]:
        return [normalize_source(s) for s in self._read(self.sources_path)]

    # -- stats -------------------------------------------------------------
    def stats(self) -> dict[str, Any]:
        claims = self.claims()
        by_status: dict[str, int] = {}
        by_agent: dict[str, int] = {}
        by_evidence: dict[str, int] = {}
        for c in claims:
            st = c.get("approval_status") or "unknown"
            ag = c.get("source_agent") or "unknown"
            ev = c.get("evidence_level") or "unspecified"
            by_status[st] = by_status.get(st, 0) + 1
            by_agent[ag] = by_agent.get(ag, 0) + 1
            by_evidence[ev] = by_evidence.get(ev, 0) + 1
        return {
            "data_dir": str(self.data_dir),
            "claims": len(claims),
            "edges": len(self.edges()),
            "sources": len(self.sources()),
            "claims_by_status": by_status,
            "claims_by_agent": by_agent,
            "claims_by_evidence_level": by_evidence,
        }
