from __future__ import annotations

import os
from typing import Any

import httpx

from app.models import Action, Decision, ProjectState

DEFAULT_GENERATION_MODE = "deterministic"
DEFAULT_TIMEOUT_SECONDS = 20.0


def generate_project_summary(
    project_id: str,
    state: ProjectState,
    decisions: list[Decision],
    actions: list[Action],
    deterministic_summary: str,
) -> tuple[str, dict[str, Any]]:
    mode = os.getenv("CONTROL_LAYER_GENERATION_MODE", DEFAULT_GENERATION_MODE).strip().lower()
    if mode != "llm":
        return deterministic_summary, {
            "mode": "deterministic",
            "provider": None,
            "model": None,
            "fallback_used": False,
            "fallback_reason": None,
        }

    api_url = os.getenv("LLM_API_URL", "").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if not api_url or not api_key or not model or api_key == "...":
        return deterministic_summary, {
            "mode": "deterministic_fallback",
            "provider": "llm",
            "model": model or None,
            "fallback_used": True,
            "fallback_reason": "missing_llm_configuration",
        }

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write concise project status summaries. "
                    "Use only the provided governed context. "
                    "Do not invent facts, tasks, or decisions."
                ),
            },
            {
                "role": "user",
                "content": _build_prompt(project_id, state, decisions, actions),
            },
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        summary = _extract_summary(data)
        if not summary:
            raise ValueError("empty_llm_response")
        return summary, {
            "mode": "llm",
            "provider": "openai_compatible",
            "model": model,
            "fallback_used": False,
            "fallback_reason": None,
        }
    except Exception as exc:
        return deterministic_summary, {
            "mode": "deterministic_fallback",
            "provider": "llm",
            "model": model,
            "fallback_used": True,
            "fallback_reason": str(exc),
        }


def _build_prompt(
    project_id: str,
    state: ProjectState,
    decisions: list[Decision],
    actions: list[Action],
) -> str:
    action_lines = "\n".join(
        f"- action | status={action.status} | title={action.title} | assignee={action.assignee}"
        for action in actions
    ) or "- none"
    decision_lines = "\n".join(
        f"- decision | status={decision.status} | title={decision.title}"
        for decision in decisions
    ) or "- none"

    return (
        f"Project ID: {project_id}\n"
        f"Current status: {state.status}\n"
        f"Current version: {state.version}\n\n"
        f"Actions:\n{action_lines}\n\n"
        f"Decisions:\n{decision_lines}\n\n"
        "Write a compact project status summary with: current status, open actions, open decisions, "
        "and the most relevant action and decision items."
    )


def _extract_summary(data: dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        return "\n".join(part for part in text_parts if part).strip()
    return str(content).strip()
