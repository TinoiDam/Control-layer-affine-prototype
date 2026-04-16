from __future__ import annotations

import re
import uuid

from app import audit, store
from app.models import (
    CreateDraftRequest,
    CreateDraftResponse,
    Document,
    DocumentStatus,
    DocumentType,
    RejectedDoc,
    SelectCanonicalRequest,
    SelectCanonicalResponse,
)
from app.policy import (
    AmbiguityError,
    NoCanonicalFoundError,
    is_valid_canonical,
    select_highest_version,
)


def select_canonical(request: SelectCanonicalRequest) -> SelectCanonicalResponse:
    all_docs = store.load_documents()
    valid: list[Document] = []
    rejected: list[RejectedDoc] = []

    for doc in all_docs:
        ok, reason = is_valid_canonical(doc, request.document_type, request.required_tags)
        if ok:
            valid.append(doc)
        else:
            rejected.append(RejectedDoc(id=doc.id, reason=reason))

    selected = select_highest_version(valid)  # raises NoCanonicalFoundError or AmbiguityError

    # Docs that were valid but not selected (lower version) → add to rejected list
    for doc in valid:
        if doc.id != selected.id:
            rejected.append(RejectedDoc(id=doc.id, reason=f"lower_version={doc.version}"))

    audit.log_select_canonical(selected.id, rejected)
    return SelectCanonicalResponse(selected=selected, rejected=rejected)


def create_draft(request: CreateDraftRequest) -> CreateDraftResponse:
    source = store.get_document_by_id(request.source_document_id)
    if source is None:
        raise ValueError(f"Document '{request.source_document_id}' not found.")
    if source.status != DocumentStatus.approved:
        raise ValueError(
            f"Source document '{source.id}' has status='{source.status.value}'. "
            "Only approved documents may be used as draft sources."
        )
    if source.document_type != DocumentType.template:
        raise ValueError(
            f"Source document '{source.id}' has type='{source.document_type.value}'. "
            "Only templates may be used as draft sources."
        )

    content = source.content
    for key, value in request.placeholders.items():
        content = re.sub(r"\{\{" + re.escape(key) + r"\}\}", value, content)

    draft = Document(
        id=f"draft-{uuid.uuid4().hex[:8]}",
        title=f"[Draft] {source.title}",
        document_type=source.document_type,
        status=DocumentStatus.draft,
        version=source.version,
        owner=source.owner,
        updated_at=_now_iso(),
        source=source.id,
        tags=list(source.tags),
        supersedes=None,
        content=content,
    )

    store.save_draft(draft)
    audit.log_create_draft(source.id, draft.id)
    return CreateDraftResponse(draft=draft)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
