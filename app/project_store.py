from __future__ import annotations

import json
from pathlib import Path

from app.models import Action, Decision, ProjectState, TrackerEntry, WorkSummary

_BASE = Path(__file__).parent.parent / "data"


def _read(file: Path) -> list[dict]:
    with file.open() as f:
        return json.load(f)


def _write(file: Path, data: list[dict] | dict) -> None:
    with file.open("w") as f:
        json.dump(data, f, indent=2)


def load_project_state(project_id: str) -> ProjectState:
    data = _read(_BASE / "project_state.json")
    if isinstance(data, list):
        for item in data:
            if item.get("project_id") == project_id:
                return ProjectState(**item)
        raise ValueError(f"No PROJECT_STATE found for project '{project_id}'.")
    if data.get("project_id") == project_id:
        return ProjectState(**data)
    raise ValueError(f"No PROJECT_STATE found for project '{project_id}'.")


def save_project_state(state: ProjectState) -> None:
    # Single-project file: overwrite in place.
    _write(_BASE / "project_state.json", state.model_dump())


def load_decisions(project_id: str) -> list[Decision]:
    return [
        Decision(**d)
        for d in _read(_BASE / "decisions.json")
        if d.get("project_id") == project_id
    ]


def load_actions(project_id: str) -> list[Action]:
    return [
        Action(**a)
        for a in _read(_BASE / "actions.json")
        if a.get("project_id") == project_id
    ]


def append_tracker(entry: TrackerEntry) -> None:
    file = _BASE / "tracker.json"
    entries = _read(file)
    entries.append(entry.model_dump())
    _write(file, entries)


def append_work_summary(summary: WorkSummary) -> None:
    file = _BASE / "work_summaries.json"
    summaries = _read(file)
    summaries.append(summary.model_dump())
    _write(file, summaries)
