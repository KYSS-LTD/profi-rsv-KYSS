import httpx
import logging
from sqlalchemy.orm import Session
from app.models.models import Message, TaskCandidate
from app.services.llm_service import llm_service
from app.services.kanban_adapter import KanbanAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskDecisionEngine:
    def __init__(self, db: Session):
        self.db = db
        self.kanban = KanbanAdapter(db)

    async def process_update(self, payload: dict):
        if payload.get("message"):
            await self._handle_message(payload["message"])
        elif payload.get("callback_query"):
            await self._handle_callback(payload["callback_query"])

    async def _handle_message(self, msg: dict):
        chat_id = msg["chat"]["id"]
        message_id = msg["message_id"]
        user_id = msg["from"]["id"]
        text = msg.get("text", "")

        if not text:
            return

        # 1. Сохраняем входящее сообщение
        db_message = Message(
            telegram_message_id=message_id,
            telegram_user_id=user_id,
            chat_id=chat_id,
            text=text
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)

        # 2. Извлекаем задачу с помощью сервиса Павла
        extraction = await llm_service.extract_tasks(text)

        if extraction.get("has_task") and extraction.get("tasks"):
            for t in extraction["tasks"]:
                # 3. Регистрируем кандидата в БД
                candidate = TaskCandidate(
                    message_id=db_message.id,
                    title=t["title"],
                    assignee_raw=t.get("assignee_raw"),
                    deadline_raw=t.get("deadline_raw"),
                    confidence=t.get("confidence", 1.0),
                    status="pending"
                )
                self.db.add(candidate)
                self.db.commit()
                self.db.refresh(candidate)

                # 4. Запускаем Confirmation Flow в групповом чате
                await self._send_confirmation_inline(chat_id, candidate)

    async def _handle_callback(self, callback: dict):
        callback_id = callback["id"]
        data = callback.get("data", "")
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        msg_id = message.get("message_id")

        if not data.startswith("task_"):
            return

        parts = data.split("_")
        action = parts[1]  # "approve" или "reject"
        candidate_id = int(parts[2])

        candidate = self.db.query(TaskCandidate).filter(TaskCandidate.id == candidate_id).first()
        if not candidate or candidate.status != "pending":
            await self._answer_callback(callback_id, "Эта задача уже была обработана!")
            return

        if action == "approve":
            candidate.status = "approved"
            self.db.commit()

            # Добавляем на доску через KanbanAdapter (P0.4)
            task = self.kanban.add_task(
                title=candidate.title,
                description=f"Извлечено из Telegram. Исполнитель: {candidate.assignee_raw}, Срок: {candidate.deadline_raw}",
                candidate_id=candidate.id
            )

            new_text = f"✅ **Задача успешно утверждена!**\n\n📌 **Название:** {task.title}\n📊 **Канбан статус:** {task.status.upper()}"
            await self._edit_message_text(chat_id, msg_id, new_text)
            await self._answer_callback(callback_id, "Добавлено на доску!")

        elif action == "reject":
            candidate.status = "rejected"
            self.db.commit()

            new_text = f"❌ **Кандидат на задачу отклонён.**\n\n🗑 ~~{candidate.title}~~"
            await self._edit_message_text(chat_id, msg_id, new_text)
            await self._answer_callback(callback_id, "Отклонено.")

    async def _send_confirmation_inline(self, chat_id: int, candidate: TaskCandidate):
        token = settings.BOT_TOKEN
        if not token:
            logger.warning(f"[Mock Bot] Отправка кнопок для кандидата {candidate.id}: {candidate.title}")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = (
            f"🤖 **Обнаружена задача!**\n\n"
            f"📝 **Что сделать:** {candidate.title}\n"
            f"👤 **Ответственный:** {candidate.assignee_raw or 'Не назначен'}\n"
            f"📅 **Дедлайн:** {candidate.deadline_raw or 'Не указан'}\n"
            f"🎯 **Уверенность AI:** {int(candidate.confidence * 100)}%\n\n"
            f"Интегрировать задачу на Kanban-панель?"
        )
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "👍 Подтвердить", "callback_data": f"task_approve_{candidate.id}"},
                        {"text": "👎 Отклонить", "callback_data": f"task_reject_{candidate.id}"}
                    ]
                ]
            }
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"Telegram API Error (sendMessage): {e}")

    async def _edit_message_text(self, chat_id: int, message_id: int, text: str):
        token = settings.BOT_TOKEN
        if not token:
            return
        url = f"https://api.telegram.org/bot{token}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"Telegram API Error (editMessage): {e}")

    async def _answer_callback(self, callback_id: str, text: str):
        token = settings.BOT_TOKEN
        if not token:
            return
        url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
        payload = {"callback_query_id": callback_id, "text": text}
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"Telegram API Error (answerCallback): {e}")