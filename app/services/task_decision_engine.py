from __future__ import annotations

import logging

import httpx
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Message, TaskCandidate, TelegramChat
from app.services.kanban_adapter import KanbanAdapter
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class TaskDecisionEngine:
    def __init__(self, db: Session):
        self.db = db
        self.kanban = KanbanAdapter(db)

    async def process_update(self, payload: dict):
        if payload.get("message"):
            return await self._handle_message(payload["message"])
        if payload.get("callback_query"):
            return await self._handle_callback(payload["callback_query"])
        return {"status": "ignored", "reason": "unsupported_update"}

    async def process_chat_context(self, chat_id: int) -> list[TaskCandidate]:
        messages = self._get_recent_chat_messages(chat_id)
        if not messages:
            return []

        transcript = self._format_transcript(messages)
        extraction = await llm_service.extract_tasks(transcript)
        if not extraction.get("has_task"):
            return []

        last_message = messages[-1]
        candidates = self._save_candidates(last_message, extraction["tasks"])
        self._mark_chat_processed(chat_id, last_message.telegram_message_id)
        return candidates

    async def _handle_message(self, msg: dict):
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return {"status": "ignored", "reason": "missing_chat"}

        self._upsert_chat(chat)
        db_message = self._save_message(msg)
        candidates = await self.process_chat_context(chat_id)

        for candidate in candidates:
            await self._send_confirmation_inline(chat_id, candidate)

        return {
            "status": "processed",
            "message_id": db_message.id,
            "candidates_created": len(candidates),
        }

    async def _handle_callback(self, callback: dict):
        callback_id = callback["id"]
        data = callback.get("data", "")
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        msg_id = message.get("message_id")

        if not data.startswith("task_"):
            return {"status": "ignored", "reason": "unsupported_callback"}

        parts = data.split("_")
        action = parts[1]
        candidate_id = int(parts[2])

        candidate = self.db.query(TaskCandidate).filter(TaskCandidate.id == candidate_id).first()
        if not candidate or candidate.status != "pending":
            await self._answer_callback(callback_id, "Эта задача уже была обработана!")
            return {"status": "ignored", "reason": "candidate_already_processed"}

        if action == "approve":
            candidate.status = "approved"
            self.db.commit()

            task_status = "done" if candidate.action == "complete" else "todo"
            task = self.kanban.add_task(
                title=candidate.title,
                description=candidate.source_excerpt or "Извлечено из Telegram-чата.",
                assignee=candidate.assignee_raw,
                deadline=candidate.deadline_raw,
                candidate_id=candidate.id,
                confidence=candidate.confidence,
                status=task_status,
            )

            new_text = (
                "✅ **Задача утверждена и добавлена на доску**\n\n"
                f"📌 **Название:** {task.title}\n"
                f"👤 **Ответственный:** {candidate.assignee_raw or 'не назначен'}\n"
                f"📅 **Срок:** {candidate.deadline_raw or 'не указан'}\n"
                f"📊 **Статус:** {task.status.upper()}"
            )
            await self._edit_message_text(chat_id, msg_id, new_text)
            await self._answer_callback(callback_id, "Добавлено на доску!")
            return {"status": "approved", "task_id": task.id}

        if action == "reject":
            candidate.status = "rejected"
            self.db.commit()

            new_text = f"❌ **Кандидат на задачу отклонён.**\n\n🗑 ~~{candidate.title}~~"
            await self._edit_message_text(chat_id, msg_id, new_text)
            await self._answer_callback(callback_id, "Отклонено.")
            return {"status": "rejected", "candidate_id": candidate.id}

        return {"status": "ignored", "reason": "unknown_action"}

    def _upsert_chat(self, chat: dict) -> TelegramChat:
        telegram_chat_id = chat["id"]
        db_chat = self.db.query(TelegramChat).filter(TelegramChat.telegram_chat_id == telegram_chat_id).first()
        if db_chat is None:
            db_chat = TelegramChat(telegram_chat_id=telegram_chat_id)
            self.db.add(db_chat)

        db_chat.title = chat.get("title") or chat.get("username") or chat.get("first_name")
        db_chat.type = chat.get("type")
        self.db.commit()
        self.db.refresh(db_chat)
        return db_chat

    def _save_message(self, msg: dict) -> Message:
        existing = (
            self.db.query(Message)
            .filter(
                Message.chat_id == msg["chat"]["id"],
                Message.telegram_message_id == msg["message_id"],
            )
            .first()
        )
        if existing:
            return existing

        sender = msg.get("from") or {}
        text, source = self._extract_message_text(msg)
        db_message = Message(
            telegram_message_id=msg["message_id"],
            telegram_user_id=sender.get("id"),
            chat_id=msg["chat"]["id"],
            sender_name=self._format_sender_name(sender),
            username=sender.get("username"),
            text=text,
            source=source,
            raw_payload=msg,
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message

    def _save_candidates(self, message: Message, tasks: list[dict]) -> list[TaskCandidate]:
        candidates = []
        for task in tasks:
            title = task.get("title")
            if not title:
                continue

            duplicate = (
                self.db.query(TaskCandidate)
                .filter(
                    TaskCandidate.chat_id == message.chat_id,
                    TaskCandidate.message_id == message.id,
                    TaskCandidate.title == title,
                )
                .first()
            )
            if duplicate:
                continue

            candidate = TaskCandidate(
                message_id=message.id,
                chat_id=message.chat_id,
                title=title,
                assignee_raw=task.get("assignee_raw"),
                deadline_raw=task.get("deadline_raw"),
                confidence=task.get("confidence", 1.0),
                status="pending",
                action=task.get("action", "create"),
                source_excerpt=task.get("source_excerpt"),
                llm_block=task.get("llm_block"),
            )
            self.db.add(candidate)
            candidates.append(candidate)

        self.db.commit()
        for candidate in candidates:
            self.db.refresh(candidate)
        return candidates

    def _get_recent_chat_messages(self, chat_id: int) -> list[Message]:
        rows = (
            self.db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(desc(Message.telegram_message_id))
            .limit(settings.TELEGRAM_CONTEXT_LIMIT)
            .all()
        )
        return list(reversed(rows))

    def _mark_chat_processed(self, chat_id: int, telegram_message_id: int) -> None:
        db_chat = self.db.query(TelegramChat).filter(TelegramChat.telegram_chat_id == chat_id).first()
        if db_chat:
            db_chat.last_processed_message_id = telegram_message_id
            self.db.commit()

    def _format_transcript(self, messages: list[Message]) -> str:
        lines = []
        for message in messages:
            speaker = message.sender_name or message.username or str(message.telegram_user_id or "unknown")
            lines.append(f"{speaker}: {message.text}")
        return "\n".join(lines)

    def _extract_message_text(self, msg: dict) -> tuple[str, str]:
        if msg.get("text"):
            return msg["text"], "telegram_text"
        if msg.get("caption"):
            source = "telegram_voice" if msg.get("voice") or msg.get("audio") else "telegram_text"
            return msg["caption"], source
        if msg.get("voice"):
            file_id = msg["voice"].get("file_id", "unknown")
            return f"[voice:{file_id}] Голосовое сообщение ожидает транскрибации", "telegram_voice"
        return "[unsupported] Сообщение без текста", "telegram_text"

    def _format_sender_name(self, sender: dict) -> str | None:
        parts = [sender.get("first_name"), sender.get("last_name")]
        name = " ".join(part for part in parts if part)
        return name or sender.get("username")

    async def _send_confirmation_inline(self, chat_id: int, candidate: TaskCandidate):
        token = settings.BOT_TOKEN
        if not token:
            logger.warning("[Mock Bot] candidate %s: %s", candidate.id, candidate.title)
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = (
            "🤖 **Обнаружена задача!**\n\n"
            f"📝 **Что сделать:** {candidate.title}\n"
            f"👤 **Ответственный:** {candidate.assignee_raw or 'Не назначен'}\n"
            f"📅 **Дедлайн:** {candidate.deadline_raw or 'Не указан'}\n"
            f"🎯 **Уверенность AI:** {int(candidate.confidence * 100)}%\n\n"
            "Добавить задачу на Kanban-панель?"
        )
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "👍 Подтвердить", "callback_data": f"task_approve_{candidate.id}"},
                        {"text": "👎 Отклонить", "callback_data": f"task_reject_{candidate.id}"},
                    ]
                ]
            },
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload, timeout=5.0)
        except Exception as exc:
            logger.error("Telegram API Error (sendMessage): %s", exc)

    async def _edit_message_text(self, chat_id: int | None, message_id: int | None, text: str):
        token = settings.BOT_TOKEN
        if not token or chat_id is None or message_id is None:
            return
        url = f"https://api.telegram.org/bot{token}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload, timeout=5.0)
        except Exception as exc:
            logger.error("Telegram API Error (editMessage): %s", exc)

    async def _answer_callback(self, callback_id: str, text: str):
        token = settings.BOT_TOKEN
        if not token:
            return
        url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
        payload = {"callback_query_id": callback_id, "text": text}
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload, timeout=5.0)
        except Exception as exc:
            logger.error("Telegram API Error (answerCallback): %s", exc)
