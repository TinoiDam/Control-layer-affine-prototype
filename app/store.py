from __future__ import annotations

import os
from typing import Optional

from app.adapters.base import BackendAdapter
from app.models import Document


def _get_adapter() -> BackendAdapter:
    backend = os.getenv("BACKEND", "json").lower()
    if backend == "affine":
        from app.adapters.affine_adapter import AffineAdapter
        return AffineAdapter()
    from app.adapters.json_adapter import JsonAdapter
    return JsonAdapter()


def load_documents() -> list[Document]:
    return _get_adapter().load_documents()


def load_drafts() -> list[Document]:
    return _get_adapter().load_drafts()


def save_draft(doc: Document) -> None:
    _get_adapter().save_draft(doc)


def get_document_by_id(doc_id: str) -> Optional[Document]:
    return _get_adapter().get_document_by_id(doc_id)
