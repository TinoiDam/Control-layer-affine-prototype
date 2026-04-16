from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Document model (canonical source selection / draft creation)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Project domain objects (governance-first MVP)
# ---------------------------------------------------------------------------

class ObjectType(str, Enum):
    PROJECT_STATE = "PROJECT_STATE"
    TRACKER = "TRACKER"
    DECISIONS = "DECISIONS"
    ACTIONS = "ACTIONS"
    WORK_SUMMARY = "WORK_SUMMARY"


class ProjectObject(BaseModel):
    project_id: str
    object_type: ObjectType
    status: str
    version: int
    last_updated: str


class ProjectState(ProjectObject):
    object_type: ObjectType = ObjectType.PROJECT_STATE
    summary: str = ""
    open_actions: int = 0
    open_decisions: int = 0


class TrackerEntry(ProjectObject):
    object_type: ObjectType = ObjectType.TRACKER
    event: str
    triggered_by: str


class Decision(ProjectObject):
    object_type: ObjectType = ObjectType.DECISIONS
    title: str
    description: str


class Action(ProjectObject):
    object_type: ObjectType = ObjectType.ACTIONS
    title: str
    assignee: str
    due_date: Optional[str] = None


class WorkSummary(ProjectObject):
    object_type: ObjectType = ObjectType.WORK_SUMMARY
    summary: str
    sources_read: list[str]


# ---------------------------------------------------------------------------
# Workflow request / response
# ---------------------------------------------------------------------------

class SummarizeRequest(BaseModel):
    project_id: str


class SummarizeResponse(BaseModel):
    project_id: str
    summary: str
    sources_used: list[str]
    write_targets: list[str]
    audit_id: str


class InitProjectRequest(BaseModel):
    project_id: str
    status: str = "active"


class InitProjectResponse(BaseModel):
    project_id: str
    status: str
    write_targets: list[str]
    audit_id: str
