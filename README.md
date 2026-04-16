# Control Layer — Affine Prototype

A governance layer that sits between an LLM (Claude) and knowledge backends (AFFiNE, Google Drive, ASD MCP servers). It enforces deterministic canonical source selection, policy-compliant draft creation, and full auditability before any future MCP integration.

## Architecture

```
LLM Client (Claude)
        │
        ▼
Control Layer  ◄── this service
        │
        ▼
Knowledge Backend (mock JSON → AFFiNE / Google Drive)
```

## Features

- **Canonical source selection** — deterministically picks the highest approved version matching type and tags; fails closed on ambiguity
- **Draft-only creation** — drafts are only generated from approved templates; approved documents can never be overwritten
- **Audit logging** — every decision is appended to a structured JSONL log
- **Extensible adapter pattern** — backend connectors can be swapped without touching governance logic

## Quickstart

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/version` | Service version |
| GET | `/documents` | List all documents |
| POST | `/select-canonical` | Select canonical source document |
| POST | `/create-draft` | Generate a draft from an approved template |
| GET | `/audit-log` | Retrieve audit records |

### Example: select canonical

```bash
curl -X POST http://localhost:8000/select-canonical \
  -H "Content-Type: application/json" \
  -d '{"document_type": "template", "required_tags": ["decision"]}'
```

### Example: create draft

```bash
curl -X POST http://localhost:8000/create-draft \
  -H "Content-Type: application/json" \
  -d '{
    "source_document_id": "tpl-v2",
    "placeholders": {
      "decision": "Assign domain owners",
      "owner": "architecture-team",
      "date": "2026-04-16",
      "impact": "High",
      "context": "Domain ownership was undefined.",
      "outcome": "Each domain now has a designated owner."
    }
  }'
```

## Project Structure

```
├── app/
│   ├── main.py       # FastAPI routes
│   ├── models.py     # Pydantic models and enums
│   ├── policy.py     # Governance rules (pure functions)
│   ├── selector.py   # Canonical selection and draft creation
│   ├── store.py      # JSON file adapter
│   └── audit.py      # Append-only JSONL audit logger
├── data/
│   ├── documents.json  # Seed documents
│   ├── drafts.json     # Created drafts (runtime)
│   └── audit.jsonl     # Audit log (runtime)
└── requirements.txt
```

## Tech Stack

Python 3.11+ · FastAPI · Pydantic v2 · Uvicorn · Local JSON storage

## Out of Scope (MVP)

AFFiNE / Google Drive integration · ASD MCP servers · RBAC · Vector search · Human approval workflows
