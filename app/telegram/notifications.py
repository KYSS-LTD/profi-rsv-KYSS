from __future__ import annotations

from app.auth.magic import MagicLoginService
from app.models.models import Employee, KomandusTask
from app.telegram.service import TelegramService


class TelegramNotificationService:
    def __init__(self, db, telegram: TelegramService | None = None):
        self.db = db
        self.telegram = telegram or TelegramService()

    async def send_employee_activation_link(self, employee: Employee):
        activation_url = None
        if employee.user_id:
            token = MagicLoginService(self.db).create_token(employee.user_id)
            activation_url = MagicLoginService(self.db).build_activation_url(token.token)
        return await self.telegram.send_activation_link(employee, activation_url)

    async def send_employee_magic_login(self, employee: Employee):
        return await self.send_employee_activation_link(employee)

    async def send_task_confirmation(self, employee: Employee, task: KomandusTask):
        return await self.telegram.send_task_confirmation(employee, task)
