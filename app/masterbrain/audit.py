"""Append-only audit log for agent-facing writes (Phase 3a). Stdlib only.

Every write ATTEMPT over the network — success, guard rejection, or auth
failure — appends exactly one event to ``graph-memory/audit.jsonl`` (covered
by the existing ``graph-memory/*.jsonl`` gitignore). Events carry a sha256
digest of the payload, never the payload itself (notes/claims can be private)
and never any token material. Payload-size caps are enforced upstream in the
API middleware BEFORE bodies are parsed or digested (Clint D5, 2026-06-11).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .store import _new_id, _now_iso

AUDIT_RELPATH = "graph-memory/audit.jsonl"

OUTCOMES = ("ok", "rejected", "auth-failed")


def _audit_path(data_dir: Path) -> Path:
    return Path(data_dir) / AUDIT_RELPATH


def payload_digest(payload: Any) -> str | None:
    if payload is None:
        return None
    canon = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def append_audit(
    data_dir: Path,
    *,
    endpoint: str,
    method: str,
    agent: str,
    outcome: str,
    status_code: int,
    reason: str | None = None,
    payload: Any = None,
    flags: list[str] | None = None,
    result_id: str | None = None,
) -> dict[str, Any]:
    """Append one audit event. Never raises into the request path."""
    event = {
        "event_id": _new_id("aud"),
        "type": "audit",
        "created_at": _now_iso(),
        "agent": agent,
        "endpoint": endpoint,
        "method": method,
        "outcome": outcome if outcome in OUTCOMES else "rejected",
        "status_code": status_code,
        "reason": reason,
        "payload_sha256": payload_digest(payload),
        "flags": flags or [],
        "result_id": result_id,
    }
    try:
        p = _audit_path(data_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass  # auditing must never take the API down; surfaced via lint later
    return event


def read_audit(data_dir: Path, tail: int | None = None) -> list[dict[str, Any]]:
    p = _audit_path(data_dir)
    if not p.exists():
        return []
    events = []
    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events[-tail:] if tail else events
