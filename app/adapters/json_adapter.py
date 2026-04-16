from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.models import Document

_BASE = Path(__file__).parent.parent.parent / "data"
_DOCUMENTS_FILE = _BASE / "documents.json"
_DRAFTS_FILE = _BASE / "drafts.json"


class JsonAdapter:
    def load_documents(self) -> list[Document]:
        with _DOCUMENTS_FILE.open() as f:
            return [Document(**d) for d in json.load(f)]

    def load_drafts(self) -> list[Document]:
        with _DRAFTS_FILE.open() as f:
            return [Document(**d) for d in json.load(f)]

    def save_draft(self, doc: Document) -> None:
        drafts = self.load_drafts()
        drafts.append(doc)
        with _DRAFTS_FILE.open("w") as f:
            json.dump([d.model_dump() for d in drafts], f, indent=2)

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        for doc in self.load_documents() + self.load_drafts():
            if doc.id == doc_id:
                return doc
        return None
