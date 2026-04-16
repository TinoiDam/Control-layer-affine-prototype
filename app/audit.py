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
    _AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return record["audit_id"]


def log_workflow(
    project_id: str,
    action: str,
    sources_read: list[str],
    policy_decisions: list[dict],
    write_targets: list[str],
    result_status: str,
    state_diff: dict | None = None,
    generation: dict | None = None,
) -> str:
    deny = next((p for p in policy_decisions if p.get("decision") == "deny"), None)
    policy_decision = "deny" if deny else "allow"
    policy_reason = deny["reason"] if deny else "all_checks_passed"

    record: dict = {
        "audit_id": f"aud-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
        "action": action,
        "project_id": project_id,
        "sources_used": sources_read,
        "write_targets": write_targets,
        "policy_decision": policy_decision,
        "policy_reason": policy_reason,
        "policy_decisions": policy_decisions,
        "result_status": result_status,
    }

    if state_diff is not None:
        record["state_diff"] = state_diff

    if generation is not None:
        record["generation"] = generation

    return _append(record)


def read_audit_log() -> list[dict]:
    if not _AUDIT_FILE.exists():
        return []
    with _AUDIT_FILE.open() as f:
        return [json.loads(line) for line in f if line.strip()]
