from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.models import Action, Decision, ProjectState, TrackerEntry, WorkSummary

_BASE = Path(__file__).parent.parent / "data"


def _read(file: Path) -> list[dict] | dict:
    with file.open() as f:
        return json.load(f)


def _write(file: Path, data: list[dict] | dict) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("w") as f:
        json.dump(data, f, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_list_file(file: Path) -> None:
    if not file.exists():
        _write(file, [])


def _state_snapshot(state: ProjectState) -> dict:
    return {
        "version": state.version,
        "open_actions": state.open_actions,
        "open_decisions": state.open_decisions,
        "last_updated": state.last_updated,
    }


def load_any_project_state() -> ProjectState | None:
    file = _BASE / "project_state.json"
    if not file.exists():
        return None
    data = _read(file)
    if isinstance(data, list):
        if not data:
            return None
        return ProjectState(**data[0])
    if not data:
        return None
    return ProjectState(**data)


def project_exists(project_id: str) -> bool:
    state = load_any_project_state()
    return state is not None and state.project_id == project_id


def init_project(project_id: str, status: str = "active") -> tuple[ProjectState, dict]:
    _BASE.mkdir(parents=True, exist_ok=True)

    existing = load_any_project_state()
    if existing:
        if existing.project_id == project_id:
            raise ValueError(f"PROJECT_STATE already exists for project '{project_id}'.")
        raise ValueError(
            f"PROJECT_STATE already exists for project '{existing.project_id}'. Reset before initializing '{project_id}'."
        )

    for name in [
        "decisions.json",
        "actions.json",
        "tracker.json",
        "work_summaries.json",
    ]:
        _ensure_list_file(_BASE / name)

    state = ProjectState(
        project_id=project_id,
        status=status,
        version=1,
        last_updated=_now_iso(),
        summary="",
        open_actions=0,
        open_decisions=0,
    )

    save_project_state(state)

    return state, {"before": None, "after": _state_snapshot(state)}


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
