# ChatGPT Handoff — Control Layer MVP / Feature Branch

**Repo:** `Control-layer-affine-prototype`  
**Primary branch for continuation:** `feature/llm-generation`  
**Backend:** Local JSON  
**Current status:** Governance-first MVP is validated. Controlled LLM injection is implemented on the feature branch and currently falls back safely because the external provider returned `429 Too Many Requests`.

---

## 1. What changed on `feature/llm-generation`

| File | What changed | Status |
|------|-------------|--------|
| `app/main.py` | Added `POST /init-project` endpoint | Complete |
| `app/bootstrap.py` | Added governed project initialization workflow | Complete |
| `app/models.py` | Added `InitProjectRequest` and `InitProjectResponse` | Complete |
| `app/project_store.py` | Added `init_project()` and safe single-project bootstrap helpers | Complete |
| `app/policy.py` | Added `init_project` write target policy | Complete |
| `app/llm.py` | Added controlled LLM generation adapter with deterministic fallback | Complete |
| `app/workflow.py` | Wired step 4 to `generate_project_summary()` and passed generation metadata to audit | Complete |
| `app/audit.py` | Added `generation` metadata support to workflow audit records | Complete |
| `README.md` | Added controlled LLM configuration and API-first bootstrap notes | Complete |
| `TEST_RUN.md` | Added reproducible validation runbook | Complete |
| `.gitignore` | Ignores `.env`, credentials, and `data/audit.jsonl` | Complete |

---

## 2. Current runtime truth

### Active endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/version` | Service version |
| POST | `/init-project` | Governed, non-destructive bootstrap |
| POST | `/summarize-project-status` | Main governed workflow |
| GET | `/audit-log` | Audit trail, supports `?project_id=` |

### Current workflow behavior

`POST /summarize-project-status` executes:

1. Resolve write targets for intent `summarize_project_status`
2. Policy-check reads for `PROJECT_STATE`, `DECISIONS`, `ACTIONS`
3. Load governed context from local JSON
4. Generate summary:
   - if `CONTROL_LAYER_GENERATION_MODE != llm` → deterministic summary
   - if `CONTROL_LAYER_GENERATION_MODE == llm` → attempt external LLM call
   - on any LLM config/runtime/provider failure → deterministic fallback
5. Policy-check writes for `PROJECT_STATE`, `TRACKER`, `WORK_SUMMARY`
6. Update `PROJECT_STATE`
7. Append `TRACKER`
8. Append `WORK_SUMMARY`
9. Append audit record including generation metadata

### Current storage model

- Single-project only
- `project_state.json` is one canonical state object
- `proj-001` currently exists
- `proj-002` init correctly fails until reset because multi-project support is out of scope

---

## 3. What has been validated already

### Governance / storage
- `POST /init-project` exists and works
- `init-project` is non-destructive
- existing `proj-001` correctly returns `409 Conflict`
- different `project_id` also returns `409 Conflict` under current single-project design
- `summarize-project-status` increments `PROJECT_STATE.version`
- `TRACKER` and `WORK_SUMMARY` append correctly

### Audit
- Audit contains `policy_decision`, `policy_reason`, `policy_decisions`, `state_diff`
- Audit now also supports `generation`
- Latest validated feature-branch behavior produced:

```json
{
  "generation": {
    "mode": "deterministic_fallback",
    "provider": "llm",
    "model": "gpt-4o-mini",
    "fallback_used": true,
    "fallback_reason": "Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/chat/completions'"
  }
}
```

### LLM path
- LLM path is connected correctly
- External provider was reached successfully enough to return `429`
- Therefore code-path is valid; current blocker is external quota/rate-limit, not local integration

---

## 4. Open issues / current blocker

| Issue | Severity | Notes |
|-------|----------|-------|
| External LLM provider returned `429 Too Many Requests` | High | Prevents successful LLM generation, but fallback works correctly |
| Single-project storage model | Medium | Intentional constraint; blocks `proj-002` init while `proj-001` exists |
| No auth / RBAC | Medium | Still out of scope |
| No version history beyond audit diff | Low | Current design acceptable for MVP |

---

## 5. Exact continuation steps for a new chat

1. Continue from **branch `feature/llm-generation`**, not `main`
2. Treat current state as **working system with safe fallback**
3. First objective is **one successful LLM run**, not more features
4. Only if LLM still fails after provider/quota fix, inspect request/response shape
5. Do **not** change governance reads/writes or policy flow unless absolutely required

---

## 6. How to test from current state

### Start service

```bash
uvicorn app.main:app --reload
```

### Optional bootstrap reset

```bash
python3 scripts/seed.py
```

### Enable controlled LLM mode locally

```bash
export CONTROL_LAYER_GENERATION_MODE=llm
export LLM_API_URL="https://api.openai.com/v1/chat/completions"
export LLM_MODEL="gpt-4o-mini"
export LLM_API_KEY="<local-secret>"
```

### Run workflow

```bash
curl -X POST http://localhost:8000/summarize-project-status \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj-001"}'
```

### Inspect audit

```bash
curl 'http://localhost:8000/audit-log?project_id=proj-001'
```

### Success criteria

A successful LLM run should produce the latest audit entry with:

```json
{
  "generation": {
    "mode": "llm",
    "fallback_used": false
  }
}
```

---

## 7. Recommended next step

**Resolve provider quota/rate-limit and validate one successful LLM generation run.**

Why this is highest leverage:
- governance path is already proven
- fallback path is already proven
- a successful LLM run closes the last open validation gap on the feature branch

---

## 8. Files to inspect first tomorrow

1. `app/workflow.py` — orchestrates the full path and now calls `generate_project_summary()`
2. `app/llm.py` — external generation + fallback logic
3. `app/audit.py` — generation metadata is recorded here
4. `README.md` — env configuration and bootstrap usage
5. `TEST_RUN.md` — validation checklist

---

## 9. Important caution

- Secrets were discussed during development; treat all previously exposed keys as compromised and rotated
- Keep real keys local only via shell env vars or ignored local `.env`
- Do not paste keys into chat, code, or repo history
