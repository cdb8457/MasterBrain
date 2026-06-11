"""MasterBrain MCP server (Phase 3b) - PURE THIN CLIENT.

Runs AGENT-SIDE (stdio) and forwards every tool call to the Phase 3a
authenticated HTTP API, which is the single enforcement point: per-agent
token identity, draft-only claims, strict subject resolution, safe edge
types, size caps, append-only audit. This file contains ZERO policy logic,
ZERO vault/filesystem access, and ZERO imports from the masterbrain app
package. If the API is unreachable, tools fail cleanly - there is no local
fallback by design.

Configuration (environment only; never commit these):
    MASTERBRAIN_API_URL   e.g. http://192.168.1.50:8077  (LAN-only)
    MASTERBRAIN_TOKEN     the agent's bearer token (shown once at issue;
                          revocable via `masterbrain token revoke`)

The token is redacted from every error message and never appears in tool
output or logs.

Contract (enforced by the API, restated for agents):
- Notes land ONLY in your own inbox/<agent>/ lane, as `draft`.
- Claims are ALWAYS `draft`. Only Clint elevates, via the local CLI.
- Unknown subjects are rejected with suggestions; pass
  force_new_subject=True only if the subject is genuinely new (audited).
- Edge types `approved_by` and `supersedes` are not available to agents.
- There is no review/approve/reject/link/supersede/canonical tool. Do not
  ask for one.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("masterbrain")

TIMEOUT_S = 20

# Edge types agents may assert (mirrors the API's SAFE_EDGE_TYPES for
# documentation; the API enforces - this list is advisory only).
SAFE_EDGE_TYPES = ("related_to", "supports", "contradicts", "derived_from",
                   "mentions", "evidence_for", "source_of")


def _cfg() -> tuple[str, str]:
    url = (os.environ.get("MASTERBRAIN_API_URL") or "").rstrip("/")
    token = os.environ.get("MASTERBRAIN_TOKEN") or ""
    if not url:
        raise RuntimeError("MASTERBRAIN_API_URL is not set in this MCP "
                           "server's environment")
    if not token:
        raise RuntimeError("MASTERBRAIN_TOKEN is not set in this MCP "
                           "server's environment")
    return url, token


def _redact(text: str) -> str:
    token = os.environ.get("MASTERBRAIN_TOKEN") or ""
    return text.replace(token, "[REDACTED-TOKEN]") if token else text


def _call(method: str, path: str, payload: dict | None = None,
          query: dict | None = None) -> object:
    url, token = _cfg()
    if query:
        q = {k: v for k, v in query.items() if v is not None}
        if q:
            path = f"{path}?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url + path, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if payload is not None:
        req.data = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("detail")
        except Exception:
            detail = str(exc.reason)
        raise RuntimeError(_redact(
            f"MasterBrain API {exc.code}: {detail}")) from None
    except urllib.error.URLError as exc:
        raise RuntimeError(_redact(
            f"MasterBrain API unreachable at {url}: {exc.reason}. "
            "No local fallback exists by design - nothing was written."
        )) from None


# --- Write tools (all guarded by the API; identity comes from the token) -----

@mcp.tool()
def masterbrain_add_note(title: str, body: str = "",
                         source_refs: list[str] | None = None,
                         links: list[str] | None = None,
                         tags: list[str] | None = None) -> dict:
    """Write an attributed DRAFT note into your own inbox/<agent>/ lane in
    the shared brain. Filename is server-generated from the title (no paths
    allowed). links are Obsidian wikilinks to canonical pages, e.g.
    "[[Team Forge]]". Only Clint can elevate a note beyond draft."""
    return _call("POST", "/notes", {
        "title": title, "body": body,
        "source_refs": source_refs or [], "links": links or [],
        "tags": tags or [],
    })


@mcp.tool()
def masterbrain_add_claim(canonical_subject: str, claim: str,
                          source_type: str | None = None,
                          source_refs: list[str] | None = None,
                          project: str | None = None,
                          confidence: float | None = None,
                          evidence_level: str = "explicit",
                          force_new_subject: bool = False,
                          related_to: list[str] | None = None,
                          supports: list[str] | None = None,
                          contradicts: list[str] | None = None) -> dict:
    """Add one atomic DRAFT claim about a canonical subject. Prefer a
    qualified canonical_id (e.g. 'projects/second-brain/...') or an exact
    page title. Unknown subjects are rejected with suggestions; set
    force_new_subject=True ONLY if the subject is genuinely new (audited).
    evidence_level: explicit | inferred | speculative. Claims are always
    draft; only Clint approves."""
    return _call("POST", "/claims", {
        "canonical_subject": canonical_subject, "claim": claim,
        "source_type": source_type, "source_refs": source_refs or [],
        "project": project, "confidence": confidence,
        "evidence_level": evidence_level,
        "force_new_subject": force_new_subject,
        "related_to": related_to or [], "supports": supports or [],
        "contradicts": contradicts or [],
    })


@mcp.tool()
def masterbrain_add_source(path: str, source_type: str | None = None,
                           title: str | None = None,
                           project: str | None = None,
                           checksum_or_stable_id: str | None = None) -> dict:
    """Register a raw source reference (vault path, URL, or stable id) so
    claims can cite it. Sources are preserved references, never rewritten."""
    return _call("POST", "/sources", {
        "path": path, "source_type": source_type, "title": title,
        "project": project, "checksum_or_stable_id": checksum_or_stable_id,
    })


@mcp.tool()
def masterbrain_add_edge(from_id: str, to_id: str, edge_type: str,
                         confidence: float | None = None,
                         evidence_level: str | None = None,
                         source_refs: list[str] | None = None) -> dict:
    """Assert a provenance edge between two nodes (claim ids, canonical ids,
    or source ids). Allowed edge_type values: related_to, supports,
    contradicts, derived_from, mentions, evidence_for, source_of.
    approved_by and supersedes are NOT available to agents."""
    return _call("POST", "/edges", {
        "from_id": from_id, "to_id": to_id, "edge_type": edge_type,
        "confidence": confidence, "evidence_level": evidence_level,
        "source_refs": source_refs or [],
    })


# --- Read tools ---------------------------------------------------------------

@mcp.tool()
def masterbrain_stats() -> dict:
    """Summary counts of the shared brain: claims by status/agent/evidence,
    edges, sources."""
    return _call("GET", "/stats")


@mcp.tool()
def masterbrain_list_claims(canonical_subject: str | None = None,
                            approval_status: str | None = None,
                            project: str | None = None) -> list:
    """List current-state claims, optionally filtered by subject, approval
    status (draft/proposed/reviewed/approved/contested/rejected/deprecated),
    or project."""
    return _call("GET", "/claims", query={
        "canonical_subject": canonical_subject,
        "approval_status": approval_status, "project": project,
    })


@mcp.tool()
def masterbrain_get_claim(claim_id: str) -> dict:
    """Fetch one claim by id with its folded state and review history."""
    return _call("GET", f"/claims/{urllib.parse.quote(claim_id)}")


@mcp.tool()
def masterbrain_list_sources() -> list:
    """List registered raw source references."""
    return _call("GET", "/sources")


@mcp.tool()
def masterbrain_list_edges() -> list:
    """List graph edges between nodes."""
    return _call("GET", "/edges")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
