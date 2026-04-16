# CLAUDE.md — Control Layer Prototype

## Current direction

This repository is **not** following an AFFiNE-first or MCP-first MVP path.

The active MVP is a **governance-first local control layer** with one workflow:

> **Summarize current project status and update tracker.**

---

## Active MVP workflow

```
prompt → project scope → governed retrieval → policy check →
generate → write-back → audit
```

Implemented as `POST /summarize-project-status`.

---

## Allowed reads (governance policy)

| Object type | Allowed |
|-------------|---------|
| PROJECT_STATE | Yes |
| DECISIONS | Yes |
| ACTIONS | Yes |
| WORK_SUMMARY | Yes (recent) |
| TRACKER | No (write-only) |

Cross-project reads are forbidden. The model never decides retrieval scope.

---

## Allowed writes (governance policy)

| Object type | Allowed |
|-------------|---------|
| PROJECT_STATE | Yes |
| TRACKER | Yes (append-only) |
| WORK_SUMMARY | Yes |
| DECISIONS | No |
| ACTIONS | No |

Overwriting `final` or `approved` artifacts is forbidden. The model never
chooses write targets — they are pre-approved per workflow intent.

---

## Architectural constraints

1. The Control Layer is the only gateway for all reads and writes.
2. Default deny — everything is denied unless explicitly allowed.
3. The model must never decide retrieval scope.
4. The model must never choose write targets.
5. All decisions are logged in an append-only audit trail.
6. Backend integrations must remain replaceable (adapter pattern).
7. Fail closed on policy ambiguity.

---

## Deprecated direction

Any startup path or architecture that depends on:
- `BACKEND=affine`
- `AFFINE_MCP_URL`
- `AFFINE_WORKSPACE_ID`
- `AFFINE_API_TOKEN`

is **deprecated for the current iteration**. The `AffineAdapter` in
`app/adapters/affine_adapter.py` is preserved as a future stub only.

Do not make real backend integrations the active path for this MVP.
Use local JSON/mock storage (`BACKEND=json`) as the default.

---

## Out of scope for this MVP

- RBAC / enterprise IAM
- Human approval workflow execution
- Vector databases / semantic search
- Real MCP integration
- Real AFFiNE or Google Drive integration
- Multi-project or multi-agent support
- Production infrastructure

---

## Project structure

```
app/
├── main.py           # FastAPI routes
├── models.py         # Pydantic domain models
├── policy.py         # Governance rules (pure functions, default deny)
├── workflow.py       # MVP workflow: summarize_project_status
├── project_store.py  # Project object persistence (JSON)
├── store.py          # Document store (adapter factory)
├── selector.py       # Canonical document selection
├── audit.py          # Append-only JSONL audit logger
└── adapters/
    ├── base.py           # BackendAdapter protocol
    ├── json_adapter.py   # Active: local JSON backend
    └── affine_adapter.py # Future stub: AFFiNE backend

data/
├── project_state.json  # Canonical project state (single source of truth)
├── decisions.json      # Project decisions
├── actions.json        # Project actions
├── tracker.json        # Append-only workflow tracker
├── work_summaries.json # Generated work summaries
├── documents.json      # Reference documents / templates
└── drafts.json         # Created drafts
```
