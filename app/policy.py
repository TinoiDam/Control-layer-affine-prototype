from __future__ import annotations

from app.models import Document, DocumentStatus, DocumentType, ObjectType


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AmbiguityError(Exception):
    """Raised when multiple candidates share the same highest version."""


class NoCanonicalFoundError(Exception):
    """Raised when no valid canonical document exists."""


class PolicyDeniedError(Exception):
    """Raised when a governance policy denies a read or write."""


# ---------------------------------------------------------------------------
# Document governance (canonical source selection)
# ---------------------------------------------------------------------------

def is_valid_canonical(
    doc: Document,
    required_type: DocumentType,
    required_tags: list[str],
) -> tuple[bool, str]:
    if doc.document_type != required_type:
        return False, f"document_type={doc.document_type.value} (expected {required_type.value})"
    if doc.status != DocumentStatus.approved:
        return False, f"status={doc.status.value}"
    missing = [t for t in required_tags if t not in doc.tags]
    if missing:
        return False, f"missing_tags={missing}"
    return True, ""


def select_highest_version(candidates: list[Document]) -> Document:
    if not candidates:
        raise NoCanonicalFoundError("No valid canonical candidates found.")
    sorted_docs = sorted(candidates, key=lambda d: d.version, reverse=True)
    if len(sorted_docs) >= 2 and sorted_docs[0].version == sorted_docs[1].version:
        raise AmbiguityError(
            f"Ambiguous canonical source: multiple documents at version {sorted_docs[0].version}."
        )
    return sorted_docs[0]


# ---------------------------------------------------------------------------
# Project governance — default deny, fail closed on ambiguity
# ---------------------------------------------------------------------------

_ALLOWED_READS: frozenset[ObjectType] = frozenset({
    ObjectType.PROJECT_STATE,
    ObjectType.DECISIONS,
    ObjectType.ACTIONS,
    ObjectType.WORK_SUMMARY,
})

_ALLOWED_WRITES: frozenset[ObjectType] = frozenset({
    ObjectType.PROJECT_STATE,
    ObjectType.TRACKER,
    ObjectType.WORK_SUMMARY,
})

_WORKFLOW_WRITE_TARGETS: dict[str, list[ObjectType]] = {
    "summarize_project_status": [
        ObjectType.PROJECT_STATE,
        ObjectType.TRACKER,
        ObjectType.WORK_SUMMARY,
    ],
}


def can_read(project_id: str, object_type: ObjectType) -> tuple[bool, str]:
    if object_type not in _ALLOWED_READS:
        return False, f"{object_type.value} is not an allowed read target"
    return True, "allowed"


def can_write(project_id: str, object_type: ObjectType) -> tuple[bool, str]:
    if object_type not in _ALLOWED_WRITES:
        return False, f"{object_type.value} is not an allowed write target"
    return True, "allowed"


def allowed_write_targets(intent: str) -> list[ObjectType]:
    """Return the pre-approved write targets for a named workflow intent.
    Returns an empty list (deny all) if the intent is unknown.
    """
    return list(_WORKFLOW_WRITE_TARGETS.get(intent, []))
