from __future__ import annotations

from app.models import Document, DocumentStatus, DocumentType


class AmbiguityError(Exception):
    """Raised when multiple candidates share the same highest version."""


class NoCanonicalFoundError(Exception):
    """Raised when no valid canonical document exists."""


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
