from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.models import Document

_BASE = Path(__file__).parent.parent / "data"
_DOCUMENTS_FILE = _BASE / "documents.json"
_DRAFTS_FILE = _BASE / "drafts.json"


def load_documents() -> list[Document]:
    with _DOCUMENTS_FILE.open() as f:
        return [Document(**d) for d in json.load(f)]


def load_drafts() -> list[Document]:
    with _DRAFTS_FILE.open() as f:
        return [Document(**d) for d in json.load(f)]


def save_draft(doc: Document) -> None:
    drafts = load_drafts()
    drafts.append(doc)
    with _DRAFTS_FILE.open("w") as f:
        json.dump([d.model_dump() for d in drafts], f, indent=2)


def get_document_by_id(doc_id: str) -> Optional[Document]:
    for doc in load_documents() + load_drafts():
        if doc.id == doc_id:
            return doc
    return None
