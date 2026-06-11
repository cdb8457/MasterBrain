"""Authenticated agent-facing API (Phase 3a).

Security model (approved by Clint, 2026-06-11):
- LAN-only deployment; NEVER internet-exposed; no TLS/OAuth in v1.
- Every endpoint requires a per-agent bearer token EXCEPT ``GET /health``.
- The acting agent is derived from the token; identity asserted in request
  bodies is rejected on mismatch. There is no clint token.
- Network writes can only produce: attributed inbox notes (``POST /notes``,
  confined to ``inbox/<token-agent>/``), DRAFT claims, sources, and safe
  provenance edges. Privileged edge types (``approved_by``, ``supersedes``)
  are rejected over HTTP.
- review / link / supersede / approval / canonical writes DO NOT EXIST over
  HTTP — Clint elevates via the local CLI only.
- Unknown subjects are rejected with 409 + suggestions (strict mode);
  ``force_new_subject`` is allowed but audited and still draft-only.
- Every write attempt and every auth failure appends to the append-only
  audit log (payload digests only; request bodies are size-capped BEFORE
  parsing/digesting).
"""

from __future__ import annotations

import os

try:
    from fastapi import Depends, FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "FastAPI is not installed. Install with 'pip install fastapi uvicorn[standard]' "
        "or use the CLI ('python -m masterbrain ...') instead."
    ) from exc

from .audit import append_audit
from .auth import verify_token
from .notes import write_agent_note
from .slugs import AmbiguousSubjectError, NearMissError, resolve_subject
from .store import (AGENT_ALIASES, APPROVAL_STATUSES, EDGE_TYPES,
                    EVIDENCE_LEVELS, GuardError, Store)

store = Store()
app = FastAPI(title="MasterBrain Memory API", version="0.3.0")

# Size cap enforced BEFORE bodies are parsed or digested (D5).
MAX_BODY_BYTES = int(os.environ.get("MASTERBRAIN_MAX_BODY_BYTES", "262144"))

# Edge types an agent token may assert over HTTP: provenance only. Types that
# imply approval, review, or canonical authority are CLI/clint territory.
BLOCKED_EDGE_TYPES = ("approved_by", "supersedes")
SAFE_EDGE_TYPES = tuple(t for t in EDGE_TYPES if t not in BLOCKED_EDGE_TYPES)


# --- Request size middleware (runs before body parsing) ----------------------

@app.middleware("http")
async def _size_cap(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        cl = request.headers.get("content-length")
        if cl is None:
            return JSONResponse({"detail": "Content-Length required"}, 411)
        try:
            if int(cl) > MAX_BODY_BYTES:
                return JSONResponse(
                    {"detail": f"payload exceeds {MAX_BODY_BYTES} bytes"}, 413)
        except ValueError:
            return JSONResponse({"detail": "invalid Content-Length"}, 400)
    return await call_next(request)


# --- Auth dependency ----------------------------------------------------------

def require_agent(request: Request) -> str:
    auth = request.headers.get("authorization") or ""
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else None
    agent = verify_token(store.data_dir, token)
    if agent is None:
        append_audit(store.data_dir, endpoint=request.url.path,
                     method=request.method, agent="unauthenticated",
                     outcome="auth-failed", status_code=401,
                     reason="missing/invalid/revoked bearer token")
        raise HTTPException(401, "valid agent bearer token required")
    return agent


def _norm(agent_field: str | None) -> str | None:
    key = (agent_field or "").lower().strip()
    return AGENT_ALIASES.get(key, key) or None


def _reject(request: Request, agent: str, code: int, reason: str,
            payload=None, flags=None):
    append_audit(store.data_dir, endpoint=request.url.path,
                 method=request.method, agent=agent, outcome="rejected",
                 status_code=code, reason=reason, payload=payload, flags=flags)
    raise HTTPException(code, reason)


def _ok(request: Request, agent: str, payload=None, flags=None,
        result_id: str | None = None):
    append_audit(store.data_dir, endpoint=request.url.path,
                 method=request.method, agent=agent, outcome="ok",
                 status_code=200, payload=payload, flags=flags,
                 result_id=result_id)


# --- Models -------------------------------------------------------------------

class NoteIn(BaseModel):
    title: str
    body: str = ""
    source_refs: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ClaimIn(BaseModel):
    canonical_subject: str
    claim: str
    source_agent: str | None = None  # derived from token; mismatch rejected
    source_type: str | None = None
    source_refs: list[str] = Field(default_factory=list)
    project: str | None = None
    confidence: float | None = None
    evidence_level: str = "explicit"
    approval_status: str = "draft"
    force_new_subject: bool = False
    related_to: list[str] = Field(default_factory=list)
    supports: list[str] = Field(default_factory=list)
    contradicts: list[str] = Field(default_factory=list)


class EdgeIn(BaseModel):
    from_id: str
    to_id: str
    edge_type: str
    created_by_agent: str | None = None  # derived from token
    confidence: float | None = None
    evidence_level: str | None = None
    source_refs: list[str] = Field(default_factory=list)


class SourceIn(BaseModel):
    path: str
    source_type: str | None = None
    source_agent: str | None = None  # derived from token
    title: str | None = None
    project: str | None = None
    checksum_or_stable_id: str | None = None


# --- Open endpoint (the ONLY one) ----------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "data_dir": str(store.data_dir)}


@app.on_event("startup")
def _startup() -> None:
    store.init()


# --- Token-gated reads ----------------------------------------------------------

@app.get("/stats")
def stats(agent: str = Depends(require_agent)) -> dict:
    return store.stats()


@app.get("/claims")
def list_claims(canonical_subject: str | None = None,
                approval_status: str | None = None,
                project: str | None = None,
                agent: str = Depends(require_agent)) -> list[dict]:
    return store.claims(subject=canonical_subject, status=approval_status,
                        project=project)


@app.get("/claims/{claim_id}")
def get_claim(claim_id: str, agent: str = Depends(require_agent)) -> dict:
    claim = store.get_claim(claim_id)
    if claim is None:
        raise HTTPException(404, "claim not found")
    return claim


@app.get("/edges")
def list_edges(agent: str = Depends(require_agent)) -> list[dict]:
    return store.edges()


@app.get("/sources")
def list_sources(agent: str = Depends(require_agent)) -> list[dict]:
    return store.sources()


# --- Token-gated writes ----------------------------------------------------------

@app.post("/notes")
def add_note(body: NoteIn, request: Request,
             agent: str = Depends(require_agent)) -> dict:
    payload = body.model_dump()
    try:
        rel = write_agent_note(store.data_dir, agent, body.title, body.body,
                               source_refs=body.source_refs, links=body.links,
                               tags=body.tags)
    except ValueError as exc:
        _reject(request, agent, 400, str(exc), payload=payload)
    _ok(request, agent, payload=payload, result_id=rel)
    return {"path": rel, "agent": agent, "status": "draft"}


@app.post("/claims")
def add_claim(body: ClaimIn, request: Request,
              agent: str = Depends(require_agent)) -> dict:
    payload = body.model_dump()
    asserted = _norm(body.source_agent)
    if asserted and asserted != agent:
        _reject(request, agent, 403,
                f"source_agent '{body.source_agent}' conflicts with token "
                f"identity '{agent}'", payload=payload)
    if body.approval_status != "draft":
        _reject(request, agent, 403,
                "network claims are draft-only; elevation is clint-only via "
                "the local CLI (PROCESS.md rule 10)", payload=payload)
    if body.evidence_level not in EVIDENCE_LEVELS:
        _reject(request, agent, 400,
                f"evidence_level must be one of {EVIDENCE_LEVELS}",
                payload=payload)
    # Strict subject resolution for agent writes (D4).
    try:
        res = resolve_subject(store.data_dir, body.canonical_subject,
                              force_new=body.force_new_subject)
    except (AmbiguousSubjectError, NearMissError) as exc:
        _reject(request, agent, 409, str(exc), payload=payload)
    if res["kind"] in ("new", "new-qualified") and not body.force_new_subject:
        _reject(request, agent, 409,
                f"unknown subject {body.canonical_subject!r}: no canonical "
                "page matches. Create the canonical page first, or set "
                "force_new_subject=true (audited, draft-only).",
                payload=payload)
    flags = ["force_new_subject"] if body.force_new_subject else []
    try:
        rec = store.add_claim(
            canonical_subject=body.canonical_subject,
            claim=body.claim,
            source_agent=agent,
            source_type=body.source_type,
            source_refs=body.source_refs,
            project=body.project,
            confidence=body.confidence,
            evidence_level=body.evidence_level,
            approval_status="draft",
            related_to=body.related_to,
            supports=body.supports,
            contradicts=body.contradicts,
            force_new_subject=body.force_new_subject,
        )
    except GuardError as exc:
        _reject(request, agent, 403, f"guard rejected: {exc}", payload=payload,
                flags=flags)
    except ValueError as exc:
        _reject(request, agent, 400, str(exc), payload=payload, flags=flags)
    _ok(request, agent, payload=payload, flags=flags,
        result_id=rec["claim_id"])
    return rec


@app.post("/edges")
def add_edge(body: EdgeIn, request: Request,
             agent: str = Depends(require_agent)) -> dict:
    payload = body.model_dump()
    asserted = _norm(body.created_by_agent)
    if asserted and asserted != agent:
        _reject(request, agent, 403,
                f"created_by_agent '{body.created_by_agent}' conflicts with "
                f"token identity '{agent}'", payload=payload)
    if body.edge_type in BLOCKED_EDGE_TYPES:
        _reject(request, agent, 403,
                f"edge_type '{body.edge_type}' implies approval/canonical "
                f"authority and is not allowed over HTTP; allowed: "
                f"{SAFE_EDGE_TYPES}", payload=payload)
    if body.edge_type not in EDGE_TYPES:
        _reject(request, agent, 400,
                f"edge_type must be one of {SAFE_EDGE_TYPES}", payload=payload)
    try:
        rec = store.add_edge(body.from_id, body.to_id, body.edge_type,
                             created_by_agent=agent,
                             confidence=body.confidence,
                             evidence_level=body.evidence_level,
                             source_refs=body.source_refs)
    except GuardError as exc:
        _reject(request, agent, 403, f"guard rejected: {exc}", payload=payload)
    except ValueError as exc:
        _reject(request, agent, 400, str(exc), payload=payload)
    _ok(request, agent, payload=payload, result_id=rec["edge_id"])
    return rec


@app.post("/sources")
def add_source(body: SourceIn, request: Request,
               agent: str = Depends(require_agent)) -> dict:
    payload = body.model_dump()
    asserted = _norm(body.source_agent)
    if asserted and asserted != agent:
        _reject(request, agent, 403,
                f"source_agent '{body.source_agent}' conflicts with token "
                f"identity '{agent}'", payload=payload)
    try:
        rec = store.add_source(body.path, source_type=body.source_type,
                               source_agent=agent, title=body.title,
                               project=body.project,
                               checksum_or_stable_id=body.checksum_or_stable_id)
    except GuardError as exc:
        _reject(request, agent, 403, f"guard rejected: {exc}", payload=payload)
    except ValueError as exc:
        _reject(request, agent, 400, str(exc), payload=payload)
    _ok(request, agent, payload=payload, result_id=rec["source_id"])
    return rec


# NOTE: there are deliberately NO /claims/{id}/review, /claims/{id}/link, or
# supersede endpoints. Approval, review, linking, supersession, and canonical
# page writes are not reachable over the network (Phase 3a D3).


def main() -> None:
    import uvicorn

    host = os.environ.get("MASTERBRAIN_API_HOST", "0.0.0.0")
    port = int(os.environ.get("MASTERBRAIN_API_PORT", "8077"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
