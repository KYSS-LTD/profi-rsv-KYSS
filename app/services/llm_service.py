from __future__ import annotations

import importlib
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from app.core.config import settings


TASK_STATUS_BY_BLOCK = {
    "новые": "pending",
    "невыполненные": "pending",
    "выполненные": "done",
}

TASK_ACTION_BY_BLOCK = {
    "новые": "create",
    "невыполненные": "update",
    "выполненные": "complete",
}


class LLMService:
    """Adapter between the backend and the LLMProcessing pipeline.

    The backend can work in two modes:
    - in-process LLMProcessing pipeline when ``LLM_PROCESSING_ENABLED=true`` and
      its optional dependencies are installed;
    - deterministic heuristic extraction for local development and tests.
    """

    async def extract_tasks(self, transcript: str, meeting_date: str | None = None) -> dict[str, Any]:
        if not transcript.strip():
            return {"has_task": False, "tasks": []}

        if settings.LLM_PROCESSING_ENABLED:
            raw_tasks = self._run_llm_processing(transcript, meeting_date)
        else:
            raw_tasks = self._extract_tasks_heuristically(transcript)

        tasks = [self._normalize_task(item) for item in raw_tasks]
        tasks = [task for task in tasks if task["title"]]
        return {"has_task": bool(tasks), "tasks": tasks}

    def _run_llm_processing(self, transcript: str, meeting_date: str | None) -> list[dict[str, Any]]:
        processing_dir = Path(settings.LLM_PROCESSING_PATH).resolve()
        if str(processing_dir) not in sys.path:
            sys.path.insert(0, str(processing_dir))

        pipeline = importlib.import_module("pipeline")
        config = importlib.import_module("config")

        llm_kwargs = config.LLM_KWARGS if config.PROVIDER_MODE == "local" else {"api_key": settings.OPENAI_API_KEY}
        return pipeline.run_pipeline(
            transcript,
            meeting_date=meeting_date or date.today().isoformat(),
            provider_mode=config.PROVIDER_MODE,
            model=config.MODEL_NAME,
            chunk_size=config.CHUNK_SIZE,
            overlap=config.CHUNK_OVERLAP,
            llm_kwargs=llm_kwargs,
        )

    def _normalize_task(self, item: dict[str, Any]) -> dict[str, Any]:
        block = str(item.get("блок") or item.get("block") or item.get("status") or "Новые")
        block_key = block.lower()
        title = item.get("задача") or item.get("task") or item.get("title") or ""
        assignee = item.get("ответственный") or item.get("assignee") or item.get("assignee_raw")
        deadline = item.get("срок") or item.get("deadline") or item.get("deadline_raw")
        evidence = item.get("обоснование") or item.get("evidence") or item.get("description")

        return {
            "title": str(title).strip(),
            "assignee_raw": str(assignee).strip() if assignee else None,
            "deadline_raw": str(deadline).strip() if deadline else None,
            "confidence": float(item.get("confidence") or 0.75),
            "status_hint": TASK_STATUS_BY_BLOCK.get(block_key, "pending"),
            "action": TASK_ACTION_BY_BLOCK.get(block_key, "create"),
            "source_excerpt": str(evidence).strip() if evidence else None,
            "llm_block": block,
        }

    def _extract_tasks_heuristically(self, transcript: str) -> list[dict[str, Any]]:
        """Small fallback for development when LLMProcessing is unavailable.

        It intentionally returns only explicit task-like phrases so that the
        Telegram flow can be tested without installing the heavy LLM stack.
        """
        direct_assignee_pattern = re.compile(
            r"(?P<assignee>[А-ЯЁA-Z][а-яёa-z]+)[,:]?\s+"
            r"(?P<title>(?i:сделай|сделать|подготовь|подготовить|проверь|проверить|"
            r"доделай|доделать|создай|создать|исправь|исправить|перенеси|перенести)\b[^.!?\n]*)"
        )
        task_phrase_pattern = re.compile(
            r"(?P<prefix>.*?\b)?"
            r"(?P<title>(?i:сделай|сделать|подготовь|подготовить|проверь|проверить|"
            r"доделай|доделать|создай|создать|исправь|исправить|перенеси|перенести)\b[^.!?\n]*)"
        )
        request_pattern = re.compile(
            r"(?i:нужно|надо|задача|поручение)[:\s]+(?P<title>[^.!?\n]+)"
            r"(?:\s+ответственный[:\s]+(?P<assignee>[А-ЯЁA-Z][а-яёa-z]+))?"
        )
        speaker_pattern = re.compile(r"^(?P<speaker>[^:]{1,60}):\s*(?P<text>.+)$")
        deadline_pattern = re.compile(r"\b(сегодня|завтра|до\s+\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|до\s+\w+)\b", re.IGNORECASE)
        tasks: list[dict[str, Any]] = []
        seen: set[tuple[str, str | None]] = set()

        for line in transcript.splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue

            speaker = None
            text = clean_line
            speaker_match = speaker_pattern.match(clean_line)
            if speaker_match:
                speaker = speaker_match.group("speaker").strip() or None
                text = speaker_match.group("text").strip()

            match = direct_assignee_pattern.search(text)
            assignee = match.group("assignee") if match else None
            if not match:
                match = request_pattern.search(text)
                assignee = match.groupdict().get("assignee") if match else None
            if not match:
                match = task_phrase_pattern.search(text)
                assignee = speaker if match else None

            if not match:
                continue

            title = self._clean_heuristic_title(match.group("title"))
            if not title:
                continue

            deadline_match = deadline_pattern.search(clean_line)
            deadline = deadline_match.group(0) if deadline_match else None
            key = (title.lower(), assignee.lower() if assignee else None)
            if key in seen:
                continue
            seen.add(key)

            tasks.append(
                {
                    "блок": "Новые",
                    "задача": title,
                    "ответственный": assignee,
                    "срок": deadline,
                    "обоснование": clean_line,
                    "confidence": 0.55,
                }
            )

        return tasks

    def _clean_heuristic_title(self, title: str) -> str:
        title = re.sub(r"\s+", " ", title).strip(" -—:")
        return re.sub(
            r"\s+\b(?:сегодня|завтра|до\s+\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|до\s+\w+)\b$",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip(" -—:")


llm_service = LLMService()
