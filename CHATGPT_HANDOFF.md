# ChatGPT Handoff — Control Layer MVP

**Repo:** `Control-layer-affine-prototype`
**Backend:** Local JSON (no external dependencies)
**Status:** MVP hardening complete. Single governed workflow runs end-to-end.

---

## 1. What I changed

| File | What changed | Status |
|------|-------------|--------|
| `app/models.py` | Added domain objects: `ProjectState`, `TrackerEntry`, `Decision`, `Action`, `WorkSummary`, `ObjectType`; added `SummarizeRequest/Response` | Complete |
| `app/policy.py` | Added `can_read`, `can_write`, `allowed_write_targets` (default deny, fail closed); kept original document governance functions | Complete |
| `app/audit.py` | Added `log_workflow` with full governance fields; added top-level `policy_decision`, `policy_reason`, `state_diff`; standardised all events to include `sources_used`, `write_targets`, `result_status` | Complete |
| `app/workflow.py` | Implemented 9-step `summarize_project_status` flow; removed dead `work_summary_id` variable; passes `state_diff` to audit | Complete |
| `app/project_store.py` | New — CRUD for `PROJECT_STATE`, `DECISIONS`, `ACTIONS`, `TRACKER`, `WORK_SUMMARY` on JSON files | Complete |
| `app/main.py` | Added `POST /summarize-project-status`; added `?project_id` filter to `GET /audit-log` | Complete |
| `app/store.py` | Refactored to adapter factory; `BACKEND=json` is default; `BACKEND=affine` path preserved but disabled | Complete |
| `app/adapters/affine_adapter.py` | Marked as future stub — not active | Complete (stub only) |
| `scripts/seed.py` | Resets all data files and clears `audit.jsonl` to clean demo state | Complete |
| `data/project_state.json` | Seed: project `proj-001`, version 1, active | Seed only |
| `data/decisions.json` | Seed: 1 open decision | Seed only |
| `data/actions.json` | Seed: 2 open + 1 closed action | Seed only |
| `data/tracker.json` | Empty — populated at runtime | Seed only |
| `data/work_summaries.json` | Empty — populated at runtime | Seed only |
| `CLAUDE.md` | Repo context, architectural rules, allowed reads/writes, deprecated direction | Complete |
| `docs/MVP_WORKFLOW.md` | Full flow diagram, policy tables, audit spec, error handling | Complete |
| `docs/PROJECT_STATE.md` | Schema, rules, relationships | Complete |
| `README.md` | Bootstrap instructions, exact curl commands, real audit output example | Complete |

---

## 2. Current runtime truth

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status": "ok"}` |
| GET | `/version` | Returns `{"version": "1.0.0", "service": "control-layer"}` |
| GET | `/documents` | Lists reference documents from `data/documents.json` |
| POST | `/select-canonical` | Selects canonical document by type + tags |
| POST | `/create-draft` | Creates draft from approved template |
| **POST** | **`/summarize-project-status`** | **Active MVP workflow** |
| GET | `/audit-log` | Full audit trail; supports `?project_id=` filter |

### Active MVP workflow

`POST /summarize-project-status` with `{"project_id": "proj-001"}` executes:

1. Resolve write targets for intent `summarize_project_status`
2. Policy-check each read: `PROJECT_STATE`, `DECISIONS`, `ACTIONS`
3. Load objects from `data/`
4. Generate deterministic text summary
5. Policy-check each write: `PROJECT_STATE`, `TRACKER`, `WORK_SUMMARY`
6. Update `PROJECT_STATE` (version++)
7. Append `TRACKER` entry
8. Append `WORK_SUMMARY`
9. Write audit record to `data/audit.jsonl`
10. Return `SummarizeResponse`

### Bootstrap method

```bash
python3 scripts/seed.py                        # resets to proj-001
python3 scripts/seed.py --project-id my-proj   # custom project ID
```

Resets: `project_state.json`, `decisions.json`, `actions.json`, `tracker.json`,
`work_summaries.json`, `audit.jsonl`.

### Audit structure (complete example)

```json
{
  "audit_id": "aud-6a426dec",
  "timestamp": "2026-04-16T18:19:53Z",
  "action": "summarize_project_status",
  "project_id": "proj-001",
  "sources_used": ["PROJECT_STATE", "DECISIONS", "ACTIONS"],
  "write_targets": ["PROJECT_STATE", "TRACKER", "WORK_SUMMARY"],
  "policy_decision": "allow",
  "policy_reason": "all_checks_passed",
  "policy_decisions": [
    {"check": "read",  "object_type": "PROJECT_STATE", "decision": "allow", "reason": "allowed"},
    {"check": "read",  "object_type": "DECISIONS",     "decision": "allow", "reason": "allowed"},
    {"check": "read",  "object_type": "ACTIONS",       "decision": "allow", "reason": "allowed"},
    {"check": "write", "object_type": "PROJECT_STATE", "decision": "allow", "reason": "allowed"},
    {"check": "write", "object_type": "TRACKER",       "decision": "allow", "reason": "allowed"},
    {"check": "write", "object_type": "WORK_SUMMARY",  "decision": "allow", "reason": "allowed"}
  ],
  "result_status": "success",
  "state_diff": {
    "before": {"version": 1, "open_actions": 2, "open_decisions": 1, "last_updated": "2026-04-16T10:00:00Z"},
    "after":  {"version": 2, "open_actions": 2, "open_decisions": 1, "last_updated": "2026-04-16T18:19:53Z"}
  }
}
```

### What is NOT implemented

- AFFiNE / MCP / Google Drive integration (stub exists, not active)
- RBAC or authentication
- Human approval workflow
- Multi-project support (single `project_state.json` only)
- LLM-generated summary (summary is deterministic template, no model call)
- `POST /init-project` API endpoint (bootstrap is CLI-only via `scripts/seed.py`)
- Soft-delete or version history for PROJECT_STATE (current version overwrites in place)

---

## 3. Decisions made

| Decision | Rationale |
|----------|-----------|
| Single `project_state.json` file | Simplest for MVP; multi-project support deferred |
| Deterministic summary (no LLM call) | Governance layer validated independently of model behaviour |
| `sources_used` ordering is hardcoded `[PROJECT_STATE, DECISIONS, ACTIONS]` | Deterministic by design; ordering not data-driven |
| `audit.jsonl` append-only, never modified | Audit integrity; `seed.py` truncates it only for demo reset |
| `AffineAdapter` kept as stub | Preserves adapter pattern without adding runtime dependency |
| Bootstrap via script, not endpoint | Avoids unauthenticated destructive API in MVP |
| `state_diff` only on PROJECT_STATE | Only write target that mutates structured state; TRACKER/WORK_SUMMARY are append-only |

---

## 4. Open issues / risks

| Issue | Severity | Notes |
|-------|----------|-------|
| No `id` field on `WorkSummary` or `TrackerEntry` | Low | Objects are identified by position in array; no random-access lookup |
| `project_state.json` is overwritten in place | Low | No version history; old state only recoverable from `state_diff` in audit |
| `data/audit.jsonl` not in `.gitignore` | Low | Stale test entries may appear in repo if not seeded before commit |
| Summary text includes `last_updated` timestamp | None | Content of summary is stable; `last_updated` field in PROJECT_STATE changes each run (expected) |
| No error if `decisions.json` or `actions.json` is missing | Medium | `project_store.load_decisions` will raise `FileNotFoundError`; not caught gracefully |
| Single-project assumption in `load_project_state` | Medium | Will raise `ValueError` if `project_state.json` contains a different `project_id` |

---

## 5. How to test

### Start the service

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Bootstrap

```bash
python3 scripts/seed.py
```

### Run the MVP workflow

```bash
curl -X POST http://localhost:8000/summarize-project-status \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-001"}'
```

### Verify audit

```bash
curl 'http://localhost:8000/audit-log?project_id=proj-001'
```

### Verify write-back

```bash
# PROJECT_STATE version should have incremented
cat data/project_state.json | python3 -m json.tool

# TRACKER should have one entry
cat data/tracker.json | python3 -m json.tool

# WORK_SUMMARY should have one entry
cat data/work_summaries.json | python3 -m json.tool
```

### Test policy denial (manual)

```bash
# Edit data/actions.json to remove project_id field, then:
curl -X POST http://localhost:8000/summarize-project-status \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-999"}'
# Expect 404: No PROJECT_STATE found for project 'proj-999'
```

---

## 6. Determinism status

| Element | Deterministic? | Notes |
|---------|---------------|-------|
| `sources_used` | Yes | Always `["PROJECT_STATE", "DECISIONS", "ACTIONS"]` |
| Summary text content | Yes | Same `actions.json` + `decisions.json` → identical summary |
| `PROJECT_STATE.version` | Yes | Increments by 1 each call |
| `PROJECT_STATE.open_actions` | Yes | Counted from `actions.json` |
| `audit_id` | No (by design) | UUID-based; unique per event |
| `timestamp` / `last_updated` | No (by design) | Live UTC timestamp; changes each call |
| `WORK_SUMMARY` ordering | Yes | Append-only; order reflects call sequence |

**Conclusion:** The workflow is deterministic for all content. Non-determinism is intentional and isolated to identifiers and timestamps only.

---

## 7. Recommended next step for ChatGPT

**Add `POST /init-project` API endpoint.**

Currently bootstrap requires CLI access (`scripts/seed.py`). Adding a governed API endpoint means the control layer can be initialised programmatically — useful for testing, for future LLM-driven orchestration, and for demonstrating that the control layer governs its own initialisation.

Why it matters: it closes the last manual step in the MVP loop. After this, the entire lifecycle (init → workflow → audit → inspect) is API-driven with no file editing required.

Scope: small. Create project state + empty tracker/work_summaries. Apply `can_write(project_id, PROJECT_STATE)` policy check. Log init event to audit.

---

## 8. Diff summary for ChatGPT

**Inspect these files first:**

1. `app/workflow.py` — the full MVP flow; 9 steps, all governance logic in one place
2. `app/policy.py` — governance rules; `can_read`, `can_write`, `allowed_write_targets`
3. `app/audit.py` — audit schema; `log_workflow` is the primary audit function
4. `app/project_store.py` — all persistence; simple JSON read/write
5. `scripts/seed.py` — bootstrap; understand data shape before modifying

**Most important structural fact:** `app/store.py` (document adapter factory) and `app/project_store.py` (project object store) are separate. Document governance and project governance are independent subsystems that share only `app/models.py` and `app/audit.py`.
