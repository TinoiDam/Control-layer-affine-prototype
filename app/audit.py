from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.models import RejectedDoc

_AUDIT_FILE = Path(__file__).parent.parent / "data" / "audit.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append(record: dict) -> str:
    """Append a record and return its audit_id."""
    _AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return record["audit_id"]


# ---------------------------------------------------------------------------
# Document audit events
# ---------------------------------------------------------------------------

def log_select_canonical(selected_id: str, rejected: list[RejectedDoc]) -> None:
    _append({
        "audit_id": f"aud-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
        "action": "select_canonical_document",
        "selected_document_id": selected_id,
        "rejected": [r.model_dump() for r in rejected],
    })


def log_create_draft(source_id: str, draft_id: str) -> None:
    _append({
        "audit_id": f"aud-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
        "action": "create_draft",
        "source_document_id": source_id,
        "draft_id": draft_id,
    })


def log_rejection(document_id: str, reason: str) -> None:
    _append({
        "audit_id": f"aud-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
        "action": "rejection",
        "document_id": document_id,
        "reason": reason,
    })


# ---------------------------------------------------------------------------
# Workflow audit event (governance-first MVP)
# ---------------------------------------------------------------------------

def log_workflow(
    project_id: str,
    action: str,
    sources_read: list[str],
    policy_decisions: list[dict],
    write_targets: list[str],
    result_status: str,
) -> str:
    """Log a full governance workflow event. Returns the audit_id."""
    return _append({
        "audit_id": f"aud-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
        "action": action,
        "project_id": project_id,
        "sources_read": sources_read,
        "policy_decisions": policy_decisions,
        "write_targets": write_targets,
        "result_status": result_status,
    })


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def read_audit_log() -> list[dict]:
    if not _AUDIT_FILE.exists():
        return []
    with _AUDIT_FILE.open() as f:
        return [json.loads(line) for line in f if line.strip()]
