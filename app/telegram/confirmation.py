from __future__ import annotations

from app.models.models import KomandusTask
from app.notifications.services import TelegramNotificationService


class TelegramConfirmationFlow:
    def __init__(self, notifications: TelegramNotificationService | None = None):
        self.notifications = notifications or TelegramNotificationService()

    async def send_task_confirmation(self, chat_id: int, task: KomandusTask) -> dict:
        text = (
            "Новая задача:\n\n"
            f"Название: {task.title}\n"
            f"Описание: {task.description or '—'}\n"
            f"Срок: {task.due_at.isoformat() if task.due_at else '—'}\n"
            f"Источник: Telegram {task.source_chat_id or '—'}/{task.source_message_id or '—'}"
        )
        markup = {"inline_keyboard": [[{"text": "Подтвердить", "callback_data": f"v2task_approve_{task.id}"}, {"text": "Отказаться", "callback_data": f"v2task_decline_{task.id}"}]]}
        return await self.notifications.send_message(chat_id, text, markup)
