# MVP Validation Run

## Setup

```bash
uvicorn app.main:app --reload
```

## Preconditions

- Run from the repository root
- Local JSON backend is active
- Existing single-project state may already contain `proj-001`

## Tests

### 1. Init existing project

```bash
curl -X POST http://localhost:8000/init-project \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-001"}'
```

Expected result:
- `409 Conflict`
- clear message that `PROJECT_STATE` already exists for `proj-001`

### 2. Summarize existing project

```bash
curl -X POST http://localhost:8000/summarize-project-status \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-001"}'
```

Expected result:
- `200 OK`
- stable summary content
- `sources_used` = `PROJECT_STATE`, `DECISIONS`, `ACTIONS`
- `write_targets` = `PROJECT_STATE`, `TRACKER`, `WORK_SUMMARY`

### 3. Audit verification

```bash
curl 'http://localhost:8000/audit-log?project_id=proj-001'
```

Expected result:
- append-only audit records
- `policy_decision` and `policy_reason` present
- `state_diff.before` and `state_diff.after` present for summarize events
- `version` increments across repeated summarize calls

### 4. Init different project under single-project constraint

```bash
curl -X POST http://localhost:8000/init-project \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-002"}'
```

Expected result:
- `409 Conflict`
- clear message that current storage model is single-project and reset is required before initializing another project

## Interpretation

This validation run proves:
- governed API bootstrap exists
- bootstrap is non-destructive
- summarize workflow is deterministic at content level
- audit logging is reconstructable
- current storage model is intentionally single-project
