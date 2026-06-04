from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Message, Task, TaskCandidate, TaskStatusHistory
from app.schemas import ExtractedTask, TaskExtractionResult
from app.services.kanban_adapter import KanbanAdapter
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)

AUTO_CONFIRM_THRESHOLD = 0.85
HUMAN_CONFIRM_THRESHOLD = 0.55


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalise_title(title: str) -> str:
    return " ".join(title.lower().strip().split())


class TaskDecisionEngine:
    def __init__(self, db: Session):
        self.db = db
        self.kanban = KanbanAdapter(db)

    async def process_text_message(self, message_id: int, source: str = "telegram_text") -> dict[str, Any]:
        message = self.db.get(Message, message_id)
        if not message or not message.text:
            return {"created": 0, "pending": 0, "discarded": 0}
        extraction = await llm_client.extract_tasks(message.text, source=source)
        return await self.route_extraction(extraction, message=message, source=source)

    async def process_transcript(self, transcript: str, source: str = "telegram_voice") -> dict[str, Any]:
        message = Message(text=transcript, raw_update={"source": source})
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return await self.process_text_message(message.id, source=source)

    async def route_extraction(
        self,
        extraction: TaskExtractionResult,
        *,
        message: Message | None = None,
        source: str = "telegram_text",
        meeting_id: int | None = None,
    ) -> dict[str, Any]:
        stats = {"created": 0, "pending": 0, "discarded": 0, "duplicates": 0}
        if not extraction.has_task:
            return stats

        for extracted in extraction.tasks:
            if self._is_duplicate(extracted.title):
                self._create_candidate(extracted, message=message, source=source, meeting_id=meeting_id, status="duplicate", reason="duplicate")
                stats["duplicates"] += 1
                continue

            if extracted.confidence >= AUTO_CONFIRM_THRESHOLD:
                candidate = self._create_candidate(extracted, message=message, source=source, meeting_id=meeting_id, status="confirmed")
                self._create_task_from_candidate(candidate, changed_by="ai:auto-confirm")
                stats["created"] += 1
            elif extracted.confidence >= HUMAN_CONFIRM_THRESHOLD:
                candidate = self._create_candidate(extracted, message=message, source=source, meeting_id=meeting_id, status="pending")
                if message and message.chat_id:
                    await self._send_confirmation_inline(message.chat_id, candidate)
                stats["pending"] += 1
            else:
                stats["discarded"] += 1
                if message and message.chat_id:
                    await self._send_clarification(message.chat_id, extracted)
        return stats

    async def process_update(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if payload.get("callback_query"):
            return await self.process_callback(payload["callback_query"])
        if payload.get("message_id"):
            return await self.process_text_message(int(payload["message_id"]))
        return None

    async def process_callback(self, callback: dict[str, Any]) -> dict[str, Any]:
        callback_id = callback.get("id")
        data = callback.get("data", "")
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        telegram_message_id = message.get("message_id")

        if not data.startswith("task_"):
            return {"status": "ignored"}

        _, action, candidate_id_raw = data.split("_", 2)
        candidate_id = int(candidate_id_raw)
        if action in {"approve", "confirm"}:
            task = self.confirm_candidate(candidate_id, confirmed_by="telegram")
            if chat_id and telegram_message_id:
                await self._edit_message_text(chat_id, telegram_message_id, f"✅ Задача создана: {task.title}")
            if callback_id:
                await self._answer_callback(callback_id, "Добавлено на доску")
            return {"status": "created", "task_id": task.id}
        if action == "reject":
            self.reject_candidate(candidate_id, reason="telegram_reject", rejected_by="telegram")
            if chat_id and telegram_message_id:
                await self._edit_message_text(chat_id, telegram_message_id, "❌ Предложение отклонено")
            if callback_id:
                await self._answer_callback(callback_id, "Отклонено")
            return {"status": "rejected", "candidate_id": candidate_id}
        return {"status": "ignored"}

    def confirm_candidate(self, candidate_id: int, overrides: dict[str, Any] | None = None, confirmed_by: str | None = None) -> Task:
        candidate = self.db.get(TaskCandidate, candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        if candidate.task:
            return candidate.task
        if candidate.status not in {"pending", "confirmed"}:
            raise ValueError(f"Candidate cannot be confirmed from status {candidate.status}")
        self._apply_candidate_overrides(candidate, overrides or {})
        candidate.status = "confirmed"
        return self._create_task_from_candidate(candidate, changed_by=confirmed_by or "dashboard")

    def reject_candidate(self, candidate_id: int, reason: str = "other", rejected_by: str | None = None) -> TaskCandidate:
        candidate = self.db.get(TaskCandidate, candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        candidate.status = "rejected"
        candidate.reason = reason
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def update_task_status(self, task_id: int, new_status: str, source: str = "dashboard", changed_by: str | None = None, comment: str | None = None) -> Task:
        task = self.db.get(Task, task_id)
        if not task:
            raise ValueError("Task not found")
        old_status = task.status
        task._previous_status = old_status
        task.status = new_status
        now = datetime.now(timezone.utc)
        task.updated_at = now
        task.last_status_change_at = now
        if old_status != new_status:
            task.status_changed_count = (task.status_changed_count or 0) + 1
        if new_status == "in_progress" and task.started_at is None:
            task.started_at = now
        if new_status == "done":
            task.closed_at = now
        self.db.add(TaskStatusHistory(task_id=task.id, old_status=old_status, new_status=new_status, source=source, changed_by=changed_by, comment=comment))
        self.kanban.create_card(task) if not task.kanban_provider else None
        self.db.commit()
        self.db.refresh(task)
        return task

    def _create_candidate(
        self,
        extracted: ExtractedTask,
        *,
        message: Message | None,
        source: str,
        meeting_id: int | None,
        status: str,
        reason: str | None = None,
    ) -> TaskCandidate:
        candidate = TaskCandidate(
            message_id=message.id if message else None,
            meeting_id=meeting_id,
            title=extracted.title,
            description=extracted.description,
            assignee_raw=extracted.assignee_raw,
            deadline=_parse_datetime(extracted.deadline),
            deadline_raw=extracted.deadline_raw,
            priority=extracted.priority,
            confidence=extracted.confidence,
            status=status,
            source=source,
            missing_fields=extracted.missing_fields,
            reason=reason,
            raw_llm_json=extracted.raw,
            source_excerpt=extracted.source_excerpt or (message.text[:500] if message and message.text else None),
        )
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def _create_task_from_candidate(self, candidate: TaskCandidate, changed_by: str) -> Task:
        task = Task(
            team_id=candidate.team_id,
            candidate_id=candidate.id,
            title=candidate.title,
            description=candidate.description,
            assignee_id=candidate.assignee_id,
            assignee_raw=candidate.assignee_raw,
            deadline=candidate.deadline,
            status="todo",
            priority=candidate.priority,
            source=candidate.source,
            confidence=candidate.confidence,
            created_by_ai=True,
            source_message_excerpt=candidate.source_excerpt,
        )
        self.db.add(task)
        self.db.flush()
        self.db.add(TaskStatusHistory(task_id=task.id, old_status=None, new_status="todo", source=changed_by, changed_by=changed_by))
        candidate.status = "confirmed"
        self.db.commit()
        self.db.refresh(task)
        self.kanban.create_card(task)
        return task

    def _is_duplicate(self, title: str) -> bool:
        normalized = _normalise_title(title)
        stmt = select(Task).where(func.lower(Task.title) == normalized, Task.status.notin_(["done", "cancelled"]))
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def _apply_candidate_overrides(self, candidate: TaskCandidate, overrides: dict[str, Any]) -> None:
        for field in ("title", "description", "assignee_raw", "priority"):
            if field in overrides:
                setattr(candidate, field, overrides[field])
        if "assignee_id" in overrides and overrides["assignee_id"]:
            candidate.assignee_id = int(overrides["assignee_id"])
        if "deadline_raw" in overrides:
            candidate.deadline_raw = overrides.get("deadline_raw")
        if "deadline" in overrides:
            candidate.deadline = _parse_datetime(overrides.get("deadline"))
            candidate.deadline_raw = overrides.get("deadline") or candidate.deadline_raw

    async def _send_confirmation_inline(self, chat_id: int, candidate: TaskCandidate) -> None:
        token = settings.BOT_TOKEN
        if not token:
            logger.info("[Mock Bot] candidate %s requires confirmation: %s", candidate.id, candidate.title)
            return
        payload = {
            "chat_id": chat_id,
            "text": f"🤖 Обнаружена задача:\n\n{candidate.title}\n\nУверенность AI: {int(candidate.confidence * 100)}%",
            "reply_markup": {"inline_keyboard": [[
                {"text": "✅ Confirm", "callback_data": f"task_confirm_{candidate.id}"},
                {"text": "✏️ Edit", "callback_data": f"task_edit_{candidate.id}"},
                {"text": "❌ Reject", "callback_data": f"task_reject_{candidate.id}"},
            ]]},
        }
        await self._telegram_post("sendMessage", payload)

    async def _send_clarification(self, chat_id: int, task: ExtractedTask) -> None:
        if settings.BOT_TOKEN:
            await self._telegram_post("sendMessage", {"chat_id": chat_id, "text": f"Не хватает данных для задачи: {task.title}"})

    async def _edit_message_text(self, chat_id: int, message_id: int, text: str) -> None:
        await self._telegram_post("editMessageText", {"chat_id": chat_id, "message_id": message_id, "text": text})

    async def _answer_callback(self, callback_id: str, text: str) -> None:
        await self._telegram_post("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})

    async def _telegram_post(self, method: str, payload: dict[str, Any]) -> None:
        if not settings.BOT_TOKEN:
            return
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(f"https://api.telegram.org/bot{settings.BOT_TOKEN}/{method}", json=payload)
                response.raise_for_status()
        except Exception as exc:
            logger.warning("Telegram API call %s failed: %s", method, exc)
