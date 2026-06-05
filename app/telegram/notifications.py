from __future__ import annotations

from app.auth.magic import MagicLoginService
from app.models.models import Employee, KomandusTask
from app.telegram.service import TelegramService


class TelegramNotificationService:
    def __init__(self, db, telegram: TelegramService | None = None):
        self.db = db
        self.telegram = telegram or TelegramService()

    async def send_employee_magic_login(self, employee: Employee):
        magic_url = None
        if employee.user_id:
            token = MagicLoginService(self.db).create_token(employee.user_id)
            magic_url = MagicLoginService(self.db).build_magic_login_url(token.token)
        return await self.telegram.send_magic_login(employee, magic_url)

    async def send_task_confirmation(self, employee: Employee, task: KomandusTask):
        return await self.telegram.send_task_confirmation(employee, task)
