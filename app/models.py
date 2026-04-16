from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class DocumentStatus(str, Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    archived = "archived"
    obsolete = "obsolete"


class DocumentType(str, Enum):
    template = "template"
    report = "report"
    note = "note"
    policy = "policy"


class Document(BaseModel):
    id: str
    title: str
    document_type: DocumentType
    status: DocumentStatus
    version: int
    owner: str
    updated_at: str
    source: str
    tags: list[str]
    supersedes: Optional[str] = None
    content: str


class RejectedDoc(BaseModel):
    id: str
    reason: str


class SelectCanonicalRequest(BaseModel):
    document_type: DocumentType
    required_tags: list[str] = []


class SelectCanonicalResponse(BaseModel):
    selected: Document
    rejected: list[RejectedDoc]


class CreateDraftRequest(BaseModel):
    source_document_id: str
    placeholders: dict[str, str] = {}


class CreateDraftResponse(BaseModel):
    draft: Document
