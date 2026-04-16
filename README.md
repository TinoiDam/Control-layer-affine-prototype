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

## Quickstart

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Bootstrap (API-first)

```bash
curl -X POST http://localhost:8000/init-project \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-001"}'
```

## Alternative reset (CLI)

```bash
python scripts/seed.py
```

## MVP Workflow

```bash
curl -X POST http://localhost:8000/summarize-project-status \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-001"}'
```

## Verify audit logging

```bash
curl 'http://localhost:8000/audit-log?project_id=proj-001'
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/version` | Service version |
| POST | `/init-project` | Initialize project state (governed) |
| POST | `/summarize-project-status` | MVP workflow |
| GET | `/audit-log` | Retrieve audit trail |

## Notes

- `init-project` is non-destructive: it will fail if a project already exists
- `scripts/seed.py` remains for full reset during development
