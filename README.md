# Control Layer — Governance-First Prototype

A policy-enforced control layer that governs all reads and writes for
AI-driven document and project workflows. The model never decides what
to read or where to write — the control layer does.

## Active MVP

One end-to-end governed workflow:

> **Summarize current project status and update tracker.**

```
prompt → project scope → governed retrieval → policy check →
generate → write-back → audit
```

## Architecture

```
LLM / API Client
      │
      ▼
Control Layer  ◄── this service (governance, policy, audit)
      │
      ▼
Local JSON Store  (active MVP backend)
      │
      ▼
(Future) AFFiNE / Google Drive / ASD MCP servers
```

**Architectural rules:**
- The Control Layer is the only gateway for all reads and writes
- Default deny — everything is denied unless explicitly allowed
- The model never decides retrieval scope or write targets
- All decisions are logged in an append-only audit trail
- Fail closed on ambiguity

## Quickstart

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No environment variables required. The service runs entirely on local JSON.

API docs: `http://localhost:8000/docs`

## Bootstrap a demo project

Reset all data files to a clean seed state:

```bash
python scripts/seed.py                        # seeds proj-001 (default)
python scripts/seed.py --project-id my-proj   # custom project ID
```

This resets `project_state.json`, `decisions.json`, `actions.json`,
`tracker.json`, `work_summaries.json`, and clears `audit.jsonl`.

## MVP Workflow

```bash
curl -X POST http://localhost:8000/summarize-project-status \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-001"}'
```

Returns:
```json
{
  "project_id": "proj-001",
  "summary": "Project proj-001 — Status: active\nOpen actions: 2 | Closed: 1\nOpen decisions: 1\n\nActions:\n  - [OPEN] Implement AFFiNE adapter stub\n  - [OPEN] Validate governance policy with compliance officer\n  - [CLOSED] Implement local JSON backend\n\nDecisions:\n  - [OPEN] Select canonical source mechanism",
  "sources_used": ["PROJECT_STATE", "DECISIONS", "ACTIONS"],
  "write_targets": ["PROJECT_STATE", "TRACKER", "WORK_SUMMARY"],
  "audit_id": "aud-a1b2c3d4"
}
```

## Verify audit logging

```bash
# All events
curl http://localhost:8000/audit-log

# Filtered by project
curl 'http://localhost:8000/audit-log?project_id=proj-001'
```

Each audit record includes:

```json
{
  "audit_id": "aud-c7973256",
  "timestamp": "2026-04-16T12:00:00Z",
  "action": "summarize_project_status",
  "project_id": "proj-001",
  "sources_used": ["PROJECT_STATE", "DECISIONS", "ACTIONS"],
  "write_targets": ["PROJECT_STATE", "TRACKER", "WORK_SUMMARY"],
  "policy_decisions": [
    {"check": "read",  "object_type": "PROJECT_STATE", "decision": "allow", "reason": "allowed"},
    {"check": "write", "object_type": "TRACKER",       "decision": "allow", "reason": "allowed"}
  ],
  "result_status": "success"
}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/version` | Service version |
| GET | `/documents` | List reference documents |
| POST | `/summarize-project-status` | **MVP workflow** — governed status summary |
| POST | `/select-canonical` | Select canonical source document |
| POST | `/create-draft` | Generate a draft from an approved template |
| GET | `/audit-log` | Retrieve full audit trail |

## Project Structure

```
├── app/
│   ├── main.py           # FastAPI routes
│   ├── models.py         # Pydantic domain models
│   ├── policy.py         # Governance rules (pure, default deny)
│   ├── workflow.py       # MVP workflow: summarize_project_status
│   ├── project_store.py  # Project object persistence
│   ├── store.py          # Document store (adapter factory)
│   ├── selector.py       # Canonical document selection
│   ├── audit.py          # Append-only JSONL audit logger
│   └── adapters/
│       ├── base.py           # BackendAdapter protocol
│       ├── json_adapter.py   # Active: local JSON backend
│       └── affine_adapter.py # Future stub: AFFiNE backend
├── data/
│   ├── project_state.json  # Canonical project state
│   ├── decisions.json
│   ├── actions.json
│   ├── tracker.json
│   ├── work_summaries.json
│   ├── documents.json      # Reference documents / templates
│   └── drafts.json
└── docs/
    ├── PROJECT_STATE.md
    └── MVP_WORKFLOW.md
```

## Governance policy

| Read allowed | Write allowed |
|-------------|--------------|
| PROJECT_STATE | PROJECT_STATE |
| DECISIONS | TRACKER |
| ACTIONS | WORK_SUMMARY |
| WORK_SUMMARY (recent) | — |

## Tech Stack

Python 3.11+ · FastAPI · Pydantic v2 · Uvicorn · Local JSON storage

## Future work (out of scope for active MVP)

| Area | Description |
|------|-------------|
| AFFiNE integration | `app/adapters/affine_adapter.py` — stub ready |
| MCP exposure | Expose control layer as MCP tools |
| Google Drive | Backend adapter |
| RBAC | Role-based access control |
| Human-in-the-loop | Approval workflows |
| Policy-as-code | External policy configuration |
