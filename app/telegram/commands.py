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
    COMMANDS = {"/start", "/help", "/login", "/tasks", "/mytasks", "/today", "/week", "/status", "/stats", "/settings", "/ask"}

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
        if command == "/login":
            return await self._login(msg)
        if command == "/ask":
            return await self._ask(msg, args[0] if args else "")
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
            await self._send_message(chat_id, "Аккаунт сотрудника не найден. Попросите менеджера добавить ваш @username в Командус.")
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
        await self.notifications.send_employee_magic_login(employee)
        await self._send_message(chat_id, "Главное меню:", reply_markup=self.main_menu_keyboard())
        return {"status": "linked", "employee_id": str(employee.id)}

    async def _login(self, msg: dict):
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat.get("type") != "private":
            await self._send_message(chat_id, "Для безопасного входа выполните /login в личном чате с ботом.")
            return {"status": "not_sent", "reason": "not_private_chat"}
        sender = msg.get("from") or {}
        employee = self.db.query(Employee).filter(Employee.telegram_id == sender.get("id")).first()
        if not employee:
            await self._send_message(chat_id, "Сначала подключите аккаунт командой /start.")
            return {"status": "not_linked"}
        await self.notifications.send_employee_magic_login(employee)
        return {"status": "magic_login_sent", "employee_id": str(employee.id)}

    async def _ask(self, msg: dict, question: str):
        chat_id = (msg.get("chat") or {}).get("id")
        sender = msg.get("from") or {}
        employee = self.db.query(Employee).filter(Employee.telegram_id == sender.get("id")).first()
        if not employee or not employee.user_id:
            await self._send_message(chat_id, "Сначала подключите аккаунт командой /start.")
            return {"status": "not_linked"}
        if not question:
            await self._send_message(chat_id, "Напишите вопрос после /ask. Например: /ask какие у меня дедлайны")
            return {"status": "ask_waiting"}
        from app.models.models import User
        user = self.db.query(User).filter(User.id == employee.user_id).first()
        answer = AIAssistantService(self.db).fallback_answer(user, question)
        await self._send_message(chat_id, answer["answer"])
        return {"status": "answered"}

    async def _employee_command(self, msg: dict, command: str):
        chat_id = (msg.get("chat") or {}).get("id")
        sender = msg.get("from") or {}
        employee = self.db.query(Employee).filter(Employee.telegram_id == sender.get("id")).first()
        if command == "/help":
            text = "Команды Командуса:\n/mytasks — все мои задачи\n/today — задачи и дедлайны на сегодня\n/week — дедлайны на 7 дней\n/status — статус задач и подключения\n/settings — настройки Telegram\n/login — ссылка активации/входа\n/ask <вопрос> — спросить AI или Rule Engine. Например: /ask что просрочено"
        elif not employee:
            text = "Сначала подключите аккаунт командой /start."
        else:
            tasks = self.db.query(KomandusTask).filter(KomandusTask.employee_id == employee.id).all()
            if command in {"/stats", "/status"}:
                done = sum(1 for task in tasks if task.status == TaskStatus.DONE.value)
                overdue = sum(1 for task in tasks if task.status == TaskStatus.OVERDUE.value)
                active = sum(1 for task in tasks if task.status not in {TaskStatus.DONE.value, TaskStatus.REJECTED.value})
                text = f"Статус: всего {len(tasks)}, активных {active}, завершено {done}, просрочено {overdue}. Telegram: {employee.telegram_status}."
            elif command == "/today":
                today = [task for task in tasks if task.due_at and task.due_at.date() == datetime.utcnow().date()]
                text = "Сегодня:\n" + "\n".join(f"• {task.title} — {task.status}" for task in today[:10]) if today else "На сегодня задач нет."
            elif command == "/week":
                today = datetime.utcnow().date()
                week = [task for task in tasks if task.due_at and 0 <= (task.due_at.date() - today).days <= 7]
                text = "На 7 дней:\n" + "\n".join(f"• {task.due_at.date().isoformat()} · {task.title} — {task.status}" for task in week[:10]) if week else "На ближайшие 7 дней дедлайнов нет."
            elif command == "/settings":
                text = "Настройки Telegram: используйте /login для новой ссылки входа, /help для списка команд. Изменение профиля выполняется в Командусе."
            else:
                active = [task for task in tasks if task.status not in {TaskStatus.DONE.value, TaskStatus.REJECTED.value}]
                text = "Ваши задачи:\n" + "\n".join(f"• {task.title} — {task.status}" for task in active[:10]) if active else "Активных задач нет."
        await self._send_message(chat_id, text, reply_markup=self.main_menu_keyboard())
        return {"status": "command", "command": command}

    def main_menu_keyboard(self):
        return {"inline_keyboard": [[{"text": "📋 Мои задачи", "callback_data": "menu:tasks"}, {"text": "⏰ Сегодня", "callback_data": "menu:today"}], [{"text": "📆 Неделя", "callback_data": "menu:week"}, {"text": "📈 Статус", "callback_data": "menu:status"}], [{"text": "⚙️ Настройки", "callback_data": "menu:settings"}, {"text": "❓ Помощь", "callback_data": "menu:help"}], [{"text": "🔗 Войти в Командус", "callback_data": "menu:login"}]]}

    async def _send_message(self, chat_id: int | None, text: str, reply_markup: dict | None = None):
        if chat_id is None:
            raise TelegramDeliveryError("Cannot send Telegram message: chat_id is missing.")
        try:
            return await self.telegram.send_message(chat_id, text, reply_markup=reply_markup)
        except TelegramDeliveryError as exc:
            self.audit.log(action="Telegram Delivery Failed", entity_type="TelegramMessage", entity_id=str(chat_id), metadata={"error": str(exc)})
            raise
