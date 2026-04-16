"""
Bootstrap / seed script for the Control Layer MVP.

Resets all project data files to a clean demo state so the
summarize_project_status workflow can be verified from scratch.

Usage:
    python scripts/seed.py              # seed default project proj-001
    python scripts/seed.py --project-id my-project
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"


def seed(project_id: str) -> None:
    files = {
        "project_state.json": {
            "project_id": project_id,
            "object_type": "PROJECT_STATE",
            "status": "active",
            "version": 1,
            "last_updated": "2026-04-16T10:00:00Z",
            "summary": f"Initial project state for {project_id}.",
            "open_actions": 2,
            "open_decisions": 1,
        },
        "decisions.json": [
            {
                "project_id": project_id,
                "object_type": "DECISIONS",
                "status": "open",
                "version": 1,
                "last_updated": "2026-04-16T09:00:00Z",
                "title": "Select canonical source mechanism",
                "description": "Decide whether canonical source selection is rule-based or ML-assisted.",
            }
        ],
        "actions.json": [
            {
                "project_id": project_id,
                "object_type": "ACTIONS",
                "status": "open",
                "version": 1,
                "last_updated": "2026-04-16T09:00:00Z",
                "title": "Implement AFFiNE adapter stub",
                "assignee": "architecture-team",
                "due_date": "2026-05-01",
            },
            {
                "project_id": project_id,
                "object_type": "ACTIONS",
                "status": "open",
                "version": 1,
                "last_updated": "2026-04-16T09:30:00Z",
                "title": "Validate governance policy with compliance officer",
                "assignee": "architecture-team",
                "due_date": "2026-04-30",
            },
            {
                "project_id": project_id,
                "object_type": "ACTIONS",
                "status": "closed",
                "version": 1,
                "last_updated": "2026-04-16T10:00:00Z",
                "title": "Implement local JSON backend",
                "assignee": "architecture-team",
                "due_date": None,
            },
        ],
        "tracker.json": [],
        "work_summaries.json": [],
    }

    _DATA.mkdir(exist_ok=True)

    for filename, content in files.items():
        path = _DATA / filename
        with path.open("w") as f:
            json.dump(content, f, indent=2)
        print(f"  reset  {path.relative_to(Path.cwd())}")

    # Clear audit log for clean demo
    audit_path = _DATA / "audit.jsonl"
    audit_path.write_text("")
    print(f"  cleared {audit_path.relative_to(Path.cwd())}")

    print(f"\nSeed complete. Project '{project_id}' ready.")
    print("Run the workflow:")
    print(f'  curl -X POST http://localhost:8000/summarize-project-status \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"project_id": "{project_id}"}}\'')
    print("\nVerify audit:")
    print(f"  curl 'http://localhost:8000/audit-log?project_id={project_id}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo project data.")
    parser.add_argument("--project-id", default="proj-001", help="Project ID to seed")
    args = parser.parse_args()
    seed(args.project_id)
