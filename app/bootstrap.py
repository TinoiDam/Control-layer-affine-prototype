from __future__ import annotations

from app import audit, project_store
from app.models import InitProjectRequest, InitProjectResponse, ObjectType
from app.policy import PolicyDeniedError, allowed_write_targets, can_write

_INTENT = "init_project"


def init_project(request: InitProjectRequest) -> InitProjectResponse:
    project_id = request.project_id
    policy_log: list[dict] = []

    write_targets = allowed_write_targets(_INTENT)
    if not write_targets:
        raise PolicyDeniedError(f"Unknown intent '{_INTENT}': no write targets defined.")

    write_target_values = [target.value for target in write_targets]

    for obj_type in write_targets:
        ok, reason = can_write(project_id, obj_type)
        policy_log.append({
            "check": "write",
            "object_type": obj_type.value,
            "decision": "allow" if ok else "deny",
            "reason": reason,
        })
        if not ok:
            audit_id = _emit_audit(
                project_id=project_id,
                policy_decisions=policy_log,
                write_targets=write_target_values,
                result_status="denied",
            )
            raise PolicyDeniedError(
                f"Write denied for {obj_type.value}: {reason} (audit_id={audit_id})"
            )

    state, state_diff = project_store.init_project(
        project_id=project_id,
        status=request.status,
    )

    audit_id = _emit_audit(
        project_id=project_id,
        policy_decisions=policy_log,
        write_targets=write_target_values,
        result_status="success",
        state_diff=state_diff,
    )

    return InitProjectResponse(
        project_id=state.project_id,
        status=state.status,
        write_targets=write_target_values,
        audit_id=audit_id,
    )


def _emit_audit(
    project_id: str,
    policy_decisions: list[dict],
    write_targets: list[str],
    result_status: str,
    state_diff: dict | None = None,
) -> str:
    return audit.log_workflow(
        project_id=project_id,
        action=_INTENT,
        sources_read=[],
        policy_decisions=policy_decisions,
        write_targets=write_targets,
        result_status=result_status,
        state_diff=state_diff,
    )
