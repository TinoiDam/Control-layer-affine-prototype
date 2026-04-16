# MVP Workflow: summarize_project_status

## Purpose

The single end-to-end MVP workflow. Given a `project_id`, it:

1. Resolves project scope
2. Retrieves governed context (policy-checked reads)
3. Generates a deterministic status summary
4. Updates `PROJECT_STATE`
5. Appends a `TRACKER` entry
6. Creates a `WORK_SUMMARY`
7. Logs all reads, writes, and policy decisions to the audit trail

## Endpoint

```
POST /summarize-project-status
Content-Type: application/json

{ "project_id": "proj-001" }
```

## Response

```json
{
  "project_id": "proj-001",
  "summary": "Project proj-001 — Status: active\nOpen actions: 2 ...",
  "sources_used": ["PROJECT_STATE", "DECISIONS", "ACTIONS"],
  "write_targets": ["PROJECT_STATE", "TRACKER", "WORK_SUMMARY"],
  "audit_id": "aud-a1b2c3d4"
}
```

## Flow

```
POST /summarize-project-status
        │
        ▼
[1] Resolve write targets for intent "summarize_project_status"
        │  policy.allowed_write_targets()
        ▼
[2] For each read type: policy.can_read(project_id, object_type)
        │  → Deny if not in allowed reads
        │  → Log policy decision
        ▼
[3] Load from project_store:
        │  PROJECT_STATE, DECISIONS, ACTIONS
        ▼
[4] Generate deterministic summary
        │  Count open/closed actions and decisions
        │  Format structured text summary
        ▼
[5] For each write target: policy.can_write(project_id, object_type)
        │  → Deny if not in allowed writes
        │  → Log policy decision
        ▼
[6] Write-back:
        │  PROJECT_STATE — version++, summary updated
        │  TRACKER       — append event
        │  WORK_SUMMARY  — append new summary
        ▼
[7] audit.log_workflow() — append-only JSONL
        ▼
[8] Return SummarizeResponse
```

## Allowed reads

| Object | Reason |
|--------|--------|
| `PROJECT_STATE` | Required: current status baseline |
| `DECISIONS` | Required: count open decisions |
| `ACTIONS` | Required: count open/closed actions |

## Allowed writes

| Object | Reason |
|--------|--------|
| `PROJECT_STATE` | Updated with new summary and counts |
| `TRACKER` | Event appended for traceability |
| `WORK_SUMMARY` | Generated output stored |

## Forbidden operations

- Reading `TRACKER` (write-only target)
- Cross-project reads
- Writing to `DECISIONS` or `ACTIONS`
- Overwriting `final` or `approved` artifacts
- Model-driven retrieval scope selection
- Model-driven write target selection

## Audit requirements

Every execution emits one audit record containing:

```json
{
  "audit_id": "aud-xxxxxxxx",
  "timestamp": "2026-04-16T12:00:00Z",
  "action": "summarize_project_status",
  "project_id": "proj-001",
  "sources_read": ["PROJECT_STATE", "DECISIONS", "ACTIONS"],
  "policy_decisions": [
    {"check": "read",  "object_type": "PROJECT_STATE", "decision": "allow", "reason": "allowed"},
    {"check": "write", "object_type": "TRACKER",       "decision": "allow", "reason": "allowed"}
  ],
  "write_targets": ["PROJECT_STATE", "TRACKER", "WORK_SUMMARY"],
  "result_status": "success"
}
```

## Error handling

| Condition | HTTP status | Behaviour |
|-----------|-------------|-----------|
| Policy read denied | 403 | Audit record emitted with `result_status: denied` |
| Policy write denied | 403 | Audit record emitted with `result_status: denied` |
| Project not found | 404 | No state written |
| Unknown intent | 403 | No writes attempted |
