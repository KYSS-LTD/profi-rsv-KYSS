from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.assistant import AIAssistantService
from app.audit.services import AuditService
from app.common.enums import TaskStatus
from app.models.models import Employee, KomandusTask, Notification, TelegramAccountLink
from app.telegram.notifications import TelegramNotificationService
from app.telegram.service import TelegramDeliveryError, TelegramService


class TelegramCommandRouter:
    COMMANDS = {"/start", "/help", "/mytasks", "/status"}

    def __init__(self, db: Session, telegram: TelegramService | None = None):
        self.db = db
        self.telegram = telegram or TelegramService()
        self.audit = AuditService(db)
        self.notifications = TelegramNotificationService(db, self.telegram)

    async def dispatch(self, msg: dict):
        text = (msg.get("text") or "").strip()
        if not text.startswith("/"):
            return None
        command, *args = text.split(maxsplit=1)
        command = command.split("@")[0].lower()
        if command not in self.COMMANDS:
            return None
        if command == "/start":
            return await self._start(msg)
        return await self._employee_command(msg, command)

    async def _start(self, msg: dict):
        sender = msg.get("from") or {}
        username = sender.get("username")
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat.get("type") != "private":
            await self._send_message(chat_id, "Для безопасного входа откройте личный чат с ботом и выполните /start.")
            return {"status": "not_linked", "reason": "not_private_chat"}
        if not username:
            await self._send_message(chat_id, "Не вижу ваш Telegram username. Добавьте username в Telegram и повторите /start.")
            return {"status": "not_linked", "reason": "missing_username"}
        normalized = f"@{username}"
        employee = self.db.query(Employee).filter(func.lower(Employee.telegram_username) == normalized.lower()).first()
        if not employee:
            await self._send_message(chat_id, "Ваш аккаунт ещё не создан.\nОбратитесь к руководителю.")
            return {"status": "not_linked", "reason": "employee_not_found"}
        employee.telegram_id = sender.get("id")
        employee.telegram_first_name = sender.get("first_name")
        employee.telegram_last_name = sender.get("last_name")
        employee.telegram_username = normalized
        employee.telegram_status = "CONNECTED"
        employee.telegram_connected_at = datetime.utcnow()
        link = self.db.query(TelegramAccountLink).filter(TelegramAccountLink.organization_id == employee.organization_id, TelegramAccountLink.employee_id == employee.id).first()
        if not link:
            self.db.add(TelegramAccountLink(organization_id=employee.organization_id, employee_id=employee.id, telegram_id=sender.get("id"), telegram_username=normalized, is_active=True))
        else:
            link.telegram_id = sender.get("id")
            link.telegram_username = normalized
            link.is_active = True
        self.db.add(Notification(organization_id=employee.organization_id, employee_id=employee.id, type="employee_connected", title="Сотрудник подключил Telegram", body=employee.full_name))
        self.db.commit()
        await self._send_message(chat_id, "Вы успешно подключены к Komandus")
        return {"status": "linked", "employee_id": str(employee.id)}

    async def _employee_command(self, msg: dict, command: str):
        chat_id = (msg.get("chat") or {}).get("id")
        sender = msg.get("from") or {}
        employee = self.db.query(Employee).filter(Employee.telegram_id == sender.get("id")).first()
        if command == "/help":
            text = "Команды Komandus:\n/start — подключить Telegram\n/mytasks — мои открытые задачи\n/status — количество задач по статусам\n/help — помощь"
        elif not employee:
            text = "Сначала подключите аккаунт командой /start."
        else:
            tasks = self.db.query(KomandusTask).filter(KomandusTask.employee_id == employee.id).all()
            if command == "/status":
                open_count = sum(1 for task in tasks if task.status == TaskStatus.OPEN.value)
                in_progress = sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS.value)
                done = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
                text = f"Статус задач:\nОткрыто: {open_count}\nВ работе: {in_progress}\nЗавершено: {done}"
            else:
                active = [task for task in tasks if task.status in {TaskStatus.OPEN.value, TaskStatus.IN_PROGRESS.value}]
                text = "Мои открытые задачи:\n" + "\n".join(f"• {task.title} — {task.status}" for task in active[:10]) if active else "Открытых задач нет."
        await self._send_message(chat_id, text)
        return {"status": "command", "command": command}

    def main_menu_keyboard(self):
        return {"inline_keyboard": [[{"text": "📋 Мои задачи", "callback_data": "menu:tasks"}, {"text": "📈 Статус", "callback_data": "menu:status"}], [{"text": "❓ Помощь", "callback_data": "menu:help"}]]}

    async def _send_message(self, chat_id: int | None, text: str, reply_markup: dict | None = None):
        if chat_id is None:
            raise TelegramDeliveryError("Cannot send Telegram message: chat_id is missing.")
        try:
            return await self.telegram.send_message(chat_id, text, reply_markup=reply_markup)
        except TelegramDeliveryError as exc:
            self.audit.log(action="Telegram Delivery Failed", entity_type="TelegramMessage", entity_id=str(chat_id), metadata={"error": str(exc)})
            raise
