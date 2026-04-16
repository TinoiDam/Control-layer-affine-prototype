# Control Layer — Governance-First Prototype

A policy-enforced control layer that governs all reads and writes for
AI-driven document and project workflows. The model never decides what
to read or where to write — the control layer does.

## Active MVP

One end-to-end governed workflow:

> **Summarize current project status and update tracker.**

## Quickstart

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Optional: Enable LLM generation (controlled)

By default, the system uses deterministic summaries.

To enable LLM-assisted generation (step 4 only):

```bash
export CONTROL_LAYER_GENERATION_MODE=llm
export LLM_API_URL="https://your-llm-endpoint/v1/chat/completions"
export LLM_API_KEY="your-key"
export LLM_MODEL="your-model"
```

If configuration is missing or the call fails, the system automatically falls back to deterministic output.

## Bootstrap (API-first)

```bash
curl -X POST http://localhost:8000/init-project \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-001"}'
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

## Notes

- LLM is not allowed to change retrieval or write targets
- All governance checks remain unchanged
- LLM only affects text generation (step 4)
- Fallback guarantees deterministic behavior
- `init-project` is non-destructive
