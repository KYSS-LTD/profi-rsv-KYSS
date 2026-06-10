from __future__ import annotations

from app.models.models import Employee, KomandusTask
from app.telegram.service import TelegramService


class TelegramConfirmationFlow:
    def __init__(self, telegram: TelegramService | None = None):
        self.telegram = telegram or TelegramService()

    async def send_task_confirmation(self, employee: Employee, task: KomandusTask) -> dict:
        return await self.telegram.send_task_confirmation(employee, task)
