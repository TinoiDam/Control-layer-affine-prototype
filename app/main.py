from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app import audit, store
from app.models import (
    CreateDraftRequest,
    CreateDraftResponse,
    SelectCanonicalRequest,
    SelectCanonicalResponse,
)
from app.policy import AmbiguityError, NoCanonicalFoundError
from app.selector import create_draft, select_canonical

app = FastAPI(title="Control Layer", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": "1.0.0", "service": "control-layer"}


@app.get("/documents")
def list_documents():
    return store.load_documents()


@app.post("/select-canonical", response_model=SelectCanonicalResponse)
def select_canonical_endpoint(request: SelectCanonicalRequest):
    try:
        return select_canonical(request)
    except NoCanonicalFoundError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except AmbiguityError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/create-draft", response_model=CreateDraftResponse)
def create_draft_endpoint(request: CreateDraftRequest):
    try:
        return create_draft(request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/audit-log")
def get_audit_log():
    return audit.read_audit_log()
