# MVP Control Layer Requirements

## 1. Purpose

This document defines the requirements for a **Minimum Viable Product (MVP)** of a **Control Layer** that governs AI-driven document workflows. The Control Layer sits between an LLM (e.g., Claude) and knowledge systems (e.g., AFFiNE, Google Drive), ensuring deterministic, auditable, and policy-compliant behavior.

The MVP focuses on validating governance logic before integration with existing ASD MCP servers or other enterprise systems.

---

## 2. Architectural Positioning

### 2.1 High-Level Architecture

```

LLM Client (Claude / ChatGPT)
|
v
Control Layer (MVP)
|
v
Knowledge Backend (Mock JSON)
|
v
(Future) AFFiNE / Google Drive / ASD MCP Servers

```

### 2.2 Responsibilities

| Layer | Responsibility |
|------|----------------|
| LLM | Reasoning and generation |
| Control Layer | Governance, policies, and decision-making |
| Knowledge Backend | Storage and retrieval of documents |
| MCP Servers (Future) | Execution of external tool actions |

---

## 3. Objectives of the MVP

The MVP must demonstrate the following capabilities:

1. **Deterministic Canonical Source Selection**
   - Select the correct document based on explicit policies.
   - Reject invalid sources such as drafts or obsolete versions.

2. **Policy Enforcement**
   - Apply governance rules using metadata.
   - Ensure reproducible and explainable decisions.

3. **Draft-Only Output Creation**
   - Generate new documents only as drafts.
   - Prevent overwriting or publishing approved documents.

4. **Auditability**
   - Log all decisions and actions.
   - Provide explainability for compliance and trust.

5. **Extensibility**
   - Enable future integration with AFFiNE and ASD MCP servers.
   - Maintain clear separation between governance and execution layers.

---

## 4. Functional Requirements

### 4.1 Document Model

Each document must include the following metadata:

| Field | Description |
|------|-------------|
| `id` | Unique identifier |
| `title` | Document title |
| `document_type` | Type (e.g., template, report, note, policy) |
| `status` | Lifecycle status (draft, review, approved, archived, obsolete) |
| `version` | Version number |
| `owner` | Responsible person |
| `updated_at` | Last modification timestamp |
| `source` | Origin of the document |
| `tags` | List of classification tags |
| `supersedes` | Reference to previous version |
| `content` | Document body |

---

### 4.2 Canonical Source Selection

#### 4.2.1 Selection Rules

A document is considered a valid canonical source if:

1. `document_type` matches the requested type.
2. `status` is `approved`.
3. All required `tags` are present.
4. The document has the **highest version** among valid candidates.
5. If ambiguity remains, the system must **fail explicitly**.

#### 4.2.2 Expected Behavior

| Scenario | Expected Outcome |
|---------|-----------------|
| Approved template vs. draft | Approved template is selected |
| Multiple approved versions | Highest version is selected |
| Missing required tags | Document is rejected |
| No valid candidate | Explicit error returned |

---

## 5. Draft Creation

### 5.1 Rules

- Source document **must** be:
  - `status = approved`
  - `document_type = template`
- Output document **must always**:
  - Have `status = draft`
  - Receive a new unique `id`
  - Not overwrite existing approved documents
- Placeholder values in the template must be replaced.

### 5.2 Example

```

Template: "Decision: {{decision}}"
Output:   "Decision: Assign domain owners"

````

---

## 6. Audit Logging

All actions must be logged in a structured and append-only format (e.g., JSONL).

### 6.1 Logged Events

| Event | Description |
|------|-------------|
| `select_canonical_document` | Source selection decision |
| `create_draft` | Draft generation |
| `rejection` | Reasons for excluded documents |

### 6.2 Example Audit Record

```json
{
  "timestamp": "2026-04-16T12:00:00Z",
  "action": "select_canonical_document",
  "selected_document_id": "tpl-v2",
  "rejected": [
    {"id": "tpl-v3", "reason": "status=draft"}
  ]
}
````

---

## 7. Non-Functional Requirements

### 7.1 Determinism

* Identical inputs must always yield identical outputs.
* The system must fail closed when ambiguity exists.

### 7.2 Modularity

* Governance logic must be independent of backend integrations.
* Adapters for AFFiNE or MCP servers can be added later without modifying core logic.

### 7.3 Security (MVP Level)

* Optional Bearer token authentication for API access.
* No enterprise IAM required at this stage.

### 7.4 Observability

* Health and version endpoints must be available.
* Audit logs must be accessible via API.

### 7.5 Extensibility

* Design must be compatible with future MCP exposure.
* Backend connectors should follow an adapter pattern.

---

## 8. Technical Stack

| Component               | Technology                       |
| ----------------------- | -------------------------------- |
| Language                | Python 3.11+                     |
| Web Framework           | FastAPI                          |
| Data Validation         | Pydantic                         |
| Storage (MVP)           | Local JSON files                 |
| Logging                 | JSONL audit log                  |
| API Server              | Uvicorn                          |
| Development Environment | Visual Studio Code + Claude Code |

---

## 9. API Endpoints

| Endpoint            | Method | Description                  |
| ------------------- | ------ | ---------------------------- |
| `/health`           | GET    | Service health check         |
| `/version`          | GET    | Service version information  |
| `/documents`        | GET    | List available documents     |
| `/select-canonical` | POST   | Determine canonical document |
| `/create-draft`     | POST   | Generate draft from template |
| `/audit-log`        | GET    | Retrieve audit records       |

---

## 10. Project Structure

```
control-layer-prototype/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── policy.py
│   ├── selector.py
│   ├── store.py
│   └── audit.py
│
├── data/
│   ├── documents.json
│   └── drafts.json
│
├── requirements.txt
└── MVP_CONTROL_LAYER_REQUIREMENTS.md
```

---

## 11. Mock Data Requirements

The mock dataset must include:

* At least **two approved template versions**
* At least **one draft template** (to validate rejection)
* At least **one non-template document** (e.g., note or policy)

---

## 12. Acceptance Criteria

| ID  | Criterion                                                |
| --- | -------------------------------------------------------- |
| AC1 | Correct canonical document is selected deterministically |
| AC2 | Draft or obsolete documents are rejected                 |
| AC3 | Draft creation only uses approved templates              |
| AC4 | All decisions are logged in the audit trail              |
| AC5 | API endpoints are accessible and functional              |
| AC6 | Service is easily extensible for future integrations     |

---

## 13. Out of Scope for MVP

The following capabilities are intentionally excluded from the MVP:

* Integration with AFFiNE or Google Drive
* Integration with ASD MCP servers
* Vector databases or semantic search
* Role-based access control (RBAC)
* Human approval workflows
* User interfaces
* Multi-agent orchestration
* Enterprise security frameworks

---

## 14. Future Enhancements

| Area                 | Description                                |
| -------------------- | ------------------------------------------ |
| MCP Integration      | Expose control layer as MCP tools          |
| Knowledge Connectors | AFFiNE and Google Drive adapters           |
| Policy Engine        | Policy-as-code with external configuration |
| Human-in-the-Loop    | Approval workflows                         |
| Observability        | Metrics and distributed tracing            |
| Security             | RBAC and enterprise IAM                    |

---

## 15. Summary

The MVP Control Layer provides a **governance-first foundation** for AI-driven document workflows. By enforcing deterministic source selection, policy compliance, and auditability, it enables safe and scalable integration with LLMs and future MCP-based ecosystems.

---

## 16. Author & Version

| Field             | Value                                     |
| ----------------- | ----------------------------------------- |
| Document          | MVP Control Layer Requirements            |
| Version           | 1.0                                       |
| Status            | Draft                                     |
| Intended Audience | AI Engineers, Architects, ASD Engineering |
| Last Updated      | 2026                                      |

````

---

### ✅ Hoe te gebruiken

1. Maak het bestand aan in je projectmap:
   ```bash
   touch MVP_CONTROL_LAYER_REQUIREMENTS.md
````

2. Plak het volledige tekstblok hierboven in het bestand.

3. Gebruik dit document als:

   * Instructie voor **Claude Code**
   * Architectuurdocument voor ASD Engineering
   * Basis voor toekomstige integratie met AFFiNE en ASD MCP-servers

**Conclusie:** Je hebt nu een volledig en direct bruikbaar `.md`-bestand voor de MVP control layer.
**Confidence Level:** High (98%)
