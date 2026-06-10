"""Optional, lightweight FastAPI service over the memory store (canonical schema).

Thin by design — read/add/review/link claims, edges, sources, stats. No auth, no
database, no cloud calls. NOT the future graph UI. The CLI alone is sufficient for
the MVP; run this only if you want an HTTP surface.

    python -m masterbrain.api            # serves on 0.0.0.0:8077

FastAPI/uvicorn are optional. If absent, importing this module raises a clear
error while the CLI keeps working.
"""

from __future__ import annotations

import os

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "FastAPI is not installed. Install with 'pip install fastapi uvicorn[standard]' "
        "or use the CLI ('python -m masterbrain ...') instead."
    ) from exc

from .store import APPROVAL_STATUSES, EDGE_TYPES, EVIDENCE_LEVELS, GuardError, Store

store = Store()
app = FastAPI(title="MasterBrain Memory API", version="0.1.0")


def _guarded(fn, *args, **kwargs):
    """Run a store write; map guard rejections to 403 and validation errors
    to 400 so the API inherits the Phase 1.7 write-guard behavior."""
    try:
        return fn(*args, **kwargs)
    except GuardError as exc:
        raise HTTPException(403, f"guard rejected: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


class ClaimIn(BaseModel):
    canonical_subject: str
    claim: str
    source_agent: str
    source_type: str | None = None
    source_refs: list[str] = Field(default_factory=list)
    project: str | None = None
    confidence: float | None = None
    evidence_level: str = "explicit"
    approval_status: str = "draft"
    related_to: list[str] = Field(default_factory=list)
    supports: list[str] = Field(default_factory=list)
    contradicts: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: list[str] = Field(default_factory=list)


class ReviewIn(BaseModel):
    approval_status: str
    by: str
    note: str | None = None


class LinkIn(BaseModel):
    field: str
    value: str
    by_agent: str


class EdgeIn(BaseModel):
    from_id: str
    to_id: str
    edge_type: str
    created_by_agent: str
    confidence: float | None = None
    evidence_level: str | None = None
    source_refs: list[str] = Field(default_factory=list)


class SourceIn(BaseModel):
    path: str
    source_type: str | None = None
    source_agent: str | None = None
    title: str | None = None
    project: str | None = None
    checksum_or_stable_id: str | None = None


@app.on_event("startup")
def _startup() -> None:
    store.init()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "data_dir": str(store.data_dir)}


@app.get("/stats")
def stats() -> dict:
    return store.stats()


@app.get("/claims")
def list_claims(canonical_subject: str | None = None,
                approval_status: str | None = None,
                project: str | None = None) -> list[dict]:
    return store.claims(subject=canonical_subject, status=approval_status, project=project)


@app.post("/claims")
def add_claim(body: ClaimIn) -> dict:
    if body.evidence_level not in EVIDENCE_LEVELS:
        raise HTTPException(400, f"evidence_level must be one of {EVIDENCE_LEVELS}")
    if body.approval_status not in APPROVAL_STATUSES:
        raise HTTPException(400, f"approval_status must be one of {APPROVAL_STATUSES}")
    return _guarded(store.add_claim, **body.model_dump())


@app.get("/claims/{claim_id}")
def get_claim(claim_id: str) -> dict:
    claim = store.get_claim(claim_id)
    if claim is None:
        raise HTTPException(404, "claim not found")
    return claim


@app.post("/claims/{claim_id}/review")
def review_claim(claim_id: str, body: ReviewIn) -> dict:
    if body.approval_status not in APPROVAL_STATUSES:
        raise HTTPException(400, f"approval_status must be one of {APPROVAL_STATUSES}")
    if store.get_claim(claim_id) is None:
        raise HTTPException(404, "claim not found")
    return _guarded(store.review_claim, claim_id, body.approval_status,
                    by=body.by, note=body.note)


@app.post("/claims/{claim_id}/link")
def link_claim(claim_id: str, body: LinkIn) -> dict:
    return _guarded(store.link_claim, claim_id, body.field, body.value,
                    by_agent=body.by_agent)


@app.get("/edges")
def list_edges() -> list[dict]:
    return store.edges()


@app.post("/edges")
def add_edge(body: EdgeIn) -> dict:
    if body.edge_type not in EDGE_TYPES:
        raise HTTPException(400, f"edge_type must be one of {EDGE_TYPES}")
    return _guarded(store.add_edge, **body.model_dump())


@app.get("/sources")
def list_sources() -> list[dict]:
    return store.sources()


@app.post("/sources")
def add_source(body: SourceIn) -> dict:
    return _guarded(store.add_source, **body.model_dump())


def main() -> None:
    import uvicorn

    host = os.environ.get("MASTERBRAIN_API_HOST", "0.0.0.0")
    port = int(os.environ.get("MASTERBRAIN_API_PORT", "8077"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
