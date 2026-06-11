"""Per-agent bearer-token authentication (Phase 3a). Stdlib only.

Identity model (approved by Clint, 2026-06-11):
- One active token per registered agent, issued by Clint ON THE BOX via
  ``python -m masterbrain token issue --agent <key>``. The plaintext token is
  shown exactly once at issue time and never stored or logged.
- At rest only sha256 hashes live in ``<vault>/.secrets/agent-tokens.json``
  (gitignored). Verification uses constant-time comparison.
- There is NO clint token: approval/elevation never happens over the network;
  Clint acts via the local CLI only.
- The server derives the acting agent from the token and ignores/rejects any
  conflicting identity asserted in a request body.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from pathlib import Path
from typing import Any

from .store import AGENT_ALIASES, APPROVER, VALID_AGENTS, _now_iso

SECRETS_RELPATH = ".secrets/agent-tokens.json"
TOKEN_PREFIX = "mbt_"


def _secrets_path(data_dir: Path) -> Path:
    return Path(data_dir) / SECRETS_RELPATH


def _load(data_dir: Path) -> dict[str, Any]:
    p = _secrets_path(data_dir)
    if not p.exists():
        return {"agents": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"agents": {}}


def _save(data_dir: Path, data: dict[str, Any]) -> None:
    p = _secrets_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _agent_key(agent: str) -> str:
    key = (agent or "").lower().strip()
    return AGENT_ALIASES.get(key, key)


def issue_token(data_dir: Path, agent: str) -> str:
    """Issue (or reissue, replacing) the token for a registered agent.
    Returns the plaintext token — show once, never persist."""
    key = _agent_key(agent)
    if key == APPROVER:
        raise ValueError(
            f"no token for '{APPROVER}': elevation never happens over the "
            "network; use the local CLI (Phase 3a D2)."
        )
    if key not in VALID_AGENTS:
        raise ValueError(
            f"'{agent}' is not a registered agent (valid: "
            f"{', '.join(VALID_AGENTS)}). See agents/agent-registry.md."
        )
    token = f"{TOKEN_PREFIX}{key}_{secrets.token_hex(24)}"
    data = _load(data_dir)
    data["agents"][key] = {
        "sha256": _hash(token),
        "issued_at": _now_iso(),
        "revoked": False,
    }
    _save(data_dir, data)
    return token


def revoke_token(data_dir: Path, agent: str) -> bool:
    key = _agent_key(agent)
    data = _load(data_dir)
    rec = data["agents"].get(key)
    if rec is None or rec.get("revoked"):
        return False
    rec["revoked"] = True
    rec["revoked_at"] = _now_iso()
    _save(data_dir, data)
    return True


def list_tokens(data_dir: Path) -> list[dict[str, Any]]:
    """Metadata only — hash prefix for identification, never full material."""
    data = _load(data_dir)
    return [
        {
            "agent": agent,
            "issued_at": rec.get("issued_at"),
            "revoked": bool(rec.get("revoked")),
            "sha256_prefix": (rec.get("sha256") or "")[:12],
        }
        for agent, rec in sorted(data["agents"].items())
    ]


def verify_token(data_dir: Path, token: str | None) -> str | None:
    """Return the agent key for a valid, unrevoked token; else None.
    Constant-time hash comparison; never logs token material."""
    if not token:
        return None
    h = _hash(token.strip())
    for agent, rec in _load(data_dir)["agents"].items():
        stored = rec.get("sha256") or ""
        if not rec.get("revoked") and hmac.compare_digest(stored, h):
            if agent in VALID_AGENTS:
                return agent
    return None
