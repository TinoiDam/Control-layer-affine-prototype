from __future__ import annotations

from datetime import datetime, timezone

from app import audit, project_store
from app.models import (
    ObjectType,
    ProjectState,
    SummarizeRequest,
    SummarizeResponse,
    TrackerEntry,
    WorkSummary,
)
from app.policy import PolicyDeniedError, allowed_write_targets, can_read, can_write

_INTENT = "summarize_project_status"


def summarize_project_status(request: SummarizeRequest) -> SummarizeResponse:
    """
    Single MVP workflow: governed retrieval → deterministic summary →
    policy-checked write-back → audit.

    prompt → project scope → governed retrieval → policy check →
    generate → write-back → audit
    """
    project_id = request.project_id
    policy_log: list[dict] = []
    sources_read: list[str] = []

    # ------------------------------------------------------------------
    # 1. Resolve write targets for this intent (pre-approved, not model-driven)
    # ------------------------------------------------------------------
    write_targets = allowed_write_targets(_INTENT)
    if not write_targets:
        raise PolicyDeniedError(f"Unknown intent '{_INTENT}': no write targets defined.")

    # ------------------------------------------------------------------
    # 2. Governed retrieval — check every read before loading
    # ------------------------------------------------------------------
    read_types = [ObjectType.PROJECT_STATE, ObjectType.DECISIONS, ObjectType.ACTIONS]
    for obj_type in read_types:
        ok, reason = can_read(project_id, obj_type)
        policy_log.append({
            "check": "read",
            "object_type": obj_type.value,
            "decision": "allow" if ok else "deny",
            "reason": reason,
        })
        if not ok:
            _emit_audit(project_id, sources_read, policy_log, [], "denied")
            raise PolicyDeniedError(f"Read denied for {obj_type.value}: {reason}")
        sources_read.append(obj_type.value)

    # ------------------------------------------------------------------
    # 3. Load data from local store
    # ------------------------------------------------------------------
    state = project_store.load_project_state(project_id)
    decisions = project_store.load_decisions(project_id)
    actions = project_store.load_actions(project_id)

    # ------------------------------------------------------------------
    # 4. Generate deterministic status summary
    # ------------------------------------------------------------------
    open_actions = [a for a in actions if a.status == "open"]
    closed_actions = [a for a in actions if a.status == "closed"]
    open_decisions = [d for d in decisions if d.status == "open"]

    action_lines = "\n".join(f"  - [{a.status.upper()}] {a.title}" for a in actions)
    decision_lines = "\n".join(f"  - [{d.status.upper()}] {d.title}" for d in decisions)

    summary = (
        f"Project {project_id} — Status: {state.status}\n"
        f"Open actions: {len(open_actions)} | Closed: {len(closed_actions)}\n"
        f"Open decisions: {len(open_decisions)}\n\n"
        f"Actions:\n{action_lines}\n\n"
        f"Decisions:\n{decision_lines}"
    )

    write_target_values = [t.value for t in write_targets]

    # ------------------------------------------------------------------
    # 5. Policy-check all write targets before writing
    # ------------------------------------------------------------------
    for obj_type in write_targets:
        ok, reason = can_write(project_id, obj_type)
        policy_log.append({
            "check": "write",
            "object_type": obj_type.value,
            "decision": "allow" if ok else "deny",
            "reason": reason,
        })
        if not ok:
            _emit_audit(project_id, sources_read, policy_log, write_target_values, "denied")
            raise PolicyDeniedError(f"Write denied for {obj_type.value}: {reason}")

    # ------------------------------------------------------------------
    # 6. Write-back: update PROJECT_STATE (capture diff for audit)
    # ------------------------------------------------------------------
    state_diff = {
        "before": {
            "version": state.version,
            "open_actions": state.open_actions,
            "open_decisions": state.open_decisions,
            "last_updated": state.last_updated,
        },
        "after": {
            "version": state.version + 1,
            "open_actions": len(open_actions),
            "open_decisions": len(open_decisions),
            "last_updated": _now_iso(),
        },
    }
    updated_state = ProjectState(
        project_id=state.project_id,
        object_type=state.object_type,
        status=state.status,
        version=state_diff["after"]["version"],
        last_updated=state_diff["after"]["last_updated"],
        summary=summary,
        open_actions=state_diff["after"]["open_actions"],
        open_decisions=state_diff["after"]["open_decisions"],
    )
    project_store.save_project_state(updated_state)

    # ------------------------------------------------------------------
    # 7. Append TRACKER entry
    # ------------------------------------------------------------------
    project_store.append_tracker(TrackerEntry(
        project_id=project_id,
        object_type=ObjectType.TRACKER,
        status="completed",
        version=1,
        last_updated=_now_iso(),
        event=f"summarize_project_status executed — PROJECT_STATE v{updated_state.version}",
        triggered_by="control-layer",
    ))

    # ------------------------------------------------------------------
    # 8. Create WORK_SUMMARY
    # ------------------------------------------------------------------
    project_store.append_work_summary(WorkSummary(
        project_id=project_id,
        object_type=ObjectType.WORK_SUMMARY,
        status="final",
        version=1,
        last_updated=_now_iso(),
        summary=summary,
        sources_read=sources_read,
    ))

    # ------------------------------------------------------------------
    # 9. Audit all reads, writes, and policy decisions
    # ------------------------------------------------------------------
    audit_id = _emit_audit(
        project_id, sources_read, policy_log, write_target_values, "success",
        state_diff=state_diff,
    )

    return SummarizeResponse(
        project_id=project_id,
        summary=summary,
        sources_used=sources_read,
        write_targets=write_target_values,
        audit_id=audit_id,
    )


def _emit_audit(
    project_id: str,
    sources_read: list[str],
    policy_decisions: list[dict],
    write_targets: list[str],
    result_status: str,
    state_diff: dict | None = None,
) -> str:
    return audit.log_workflow(
        project_id=project_id,
        action=_INTENT,
        sources_read=sources_read,
        policy_decisions=policy_decisions,
        write_targets=write_targets,
        result_status=result_status,
        state_diff=state_diff,
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
