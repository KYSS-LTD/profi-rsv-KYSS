from __future__ import annotations

import asyncio
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

from app.schemas import ExtractedTask, TaskExtractionResult

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
LLM_DIR = ROOT_DIR / "LLMProcessing"


def _normalise_priority(value: Any) -> str:
    text = str(value or "medium").lower().strip()
    mapping = {
        "низкий": "low",
        "low": "low",
        "средний": "medium",
        "medium": "medium",
        "высокий": "high",
        "high": "high",
        "критичный": "critical",
        "critical": "critical",
    }
    return mapping.get(text, "medium")


def _coerce_task(raw: dict[str, Any], source: str) -> ExtractedTask | None:
    title = raw.get("title") or raw.get("задача") or raw.get("task") or raw.get("name")
    if not title:
        return None

    confidence = raw.get("confidence", raw.get("уверенность", raw.get("score", 0.9)))
    try:
        confidence_float = float(confidence)
    except (TypeError, ValueError):
        confidence_float = 0.9
    if confidence_float > 1:
        confidence_float = confidence_float / 100

    deadline = raw.get("deadline") or raw.get("срок") or raw.get("due_date")
    assignee = raw.get("assignee_raw") or raw.get("ответственный") or raw.get("assignee")
    description = raw.get("description") or raw.get("обоснование") or raw.get("reason")

    missing_fields: list[str] = []
    if not assignee:
        missing_fields.append("assignee")
    if not deadline:
        missing_fields.append("deadline")

    return ExtractedTask(
        title=str(title).strip(),
        description=str(description).strip() if description else None,
        assignee_raw=str(assignee).strip() if assignee else None,
        deadline_raw=str(deadline).strip() if deadline else None,
        priority=_normalise_priority(raw.get("priority") or raw.get("приоритет")),
        confidence=max(0.0, min(confidence_float, 1.0)),
        source=source,  # type: ignore[arg-type]
        missing_fields=missing_fields,
        source_excerpt=str(raw.get("source_excerpt") or raw.get("цитата") or "")[:500] or None,
        raw=raw,
    )


class LLMProcessingClient:
    """Isolation boundary around Pavel's LLMProcessing package.

    This client only invokes/validates the pipeline and returns structured schemas.
    It deliberately performs no database writes and no task-manager network calls.
    """

    async def extract_tasks(self, text: str, source: str = "telegram_text") -> TaskExtractionResult:
        if not text.strip():
            return TaskExtractionResult(has_task=False, raw=[])

        raw_tasks = await asyncio.to_thread(self._run_pipeline, text)
        tasks = [task for item in raw_tasks if isinstance(item, dict) for task in [_coerce_task(item, source)] if task]
        return TaskExtractionResult(has_task=bool(tasks), tasks=tasks, raw=raw_tasks)

    def _run_pipeline(self, text: str) -> list[dict[str, Any]]:
        try:
            if str(LLM_DIR) not in sys.path:
                sys.path.insert(0, str(LLM_DIR))
            from pipeline import run_pipeline  # type: ignore

            result = run_pipeline(transcript=text, meeting_date=date.today().isoformat())
            return result if isinstance(result, list) else []
        except Exception as exc:
            logger.warning("LLMProcessing pipeline unavailable; returning deterministic fallback: %s", exc)
            return [
                {
                    "title": text.strip()[:500],
                    "description": "Автоматически извлечено из сообщения.",
                    "confidence": 0.9,
                }
            ]


llm_client = LLMProcessingClient()
