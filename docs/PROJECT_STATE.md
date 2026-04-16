# PROJECT_STATE

`PROJECT_STATE` is the single canonical project state per project. It is the
authoritative record of a project's current status and is the primary write
target of the `summarize_project_status` workflow.

## Schema

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | string | Unique project identifier |
| `object_type` | `PROJECT_STATE` | Fixed discriminator |
| `status` | string | `active`, `paused`, `closed` |
| `version` | int | Increments on every governed update |
| `last_updated` | ISO-8601 | Timestamp of last update |
| `summary` | string | Human-readable status summary |
| `open_actions` | int | Count of open actions at last update |
| `open_decisions` | int | Count of open decisions at last update |

## Rules

- There is exactly **one** `PROJECT_STATE` per project.
- It may only be written by a governed workflow (not directly by a model).
- Every write increments `version` and updates `last_updated`.
- The previous state is not deleted — version history is maintained via the `TRACKER`.

## Storage

`data/project_state.json` — single-object JSON file for the active project.

## Relationships

```
PROJECT_STATE
    ↑ updated by: summarize_project_status workflow
    ↑ reads from: DECISIONS, ACTIONS
    ↓ logged in:  TRACKER, audit.jsonl
    ↓ produces:   WORK_SUMMARY
```
