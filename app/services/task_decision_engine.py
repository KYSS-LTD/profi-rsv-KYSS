from __future__ import annotations

import logging

import httpx
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Employee, Message, Task, TaskCandidate, TelegramChat, TelegramSource
from app.services.llm_service import llm_service
from app.services.task_service import create_task_from_candidate

logger = logging.getLogger(__name__)
HIGH_CONFIDENCE_THRESHOLD = 80.0
MANAGER_ROLES = {"OWNER", "ADMIN", "MANAGER"}


class TaskDecisionEngine:
    def __init__(self, db: Session):
        self.db = db

    async def process_update(self, payload: dict):
        if payload.get("message"):
            return await self._handle_message(payload["message"])
        if payload.get("callback_query"):
            return await self._handle_callback(payload["callback_query"])
        return {"status": "ignored", "reason": "unsupported_update"}

    async def process_chat_context(self, chat_id: int) -> list[TaskCandidate]:
        source = self._get_active_source(chat_id)
        if source is None:
            return []
        messages = self._get_unprocessed_chat_messages(chat_id)
        if not messages:
            return []

        transcript = self._format_transcript(messages)
        extraction = await llm_service.extract_tasks(transcript, context=self._build_llm_context(source))
        last_message = messages[-1]
        if not extraction.get("has_task"):
            self._mark_chat_processed(chat_id, last_message.telegram_message_id)
            return []

        candidates = self._save_candidates(source, last_message, extraction["tasks"])
        self._mark_chat_processed(chat_id, last_message.telegram_message_id)
        return candidates

    async def _handle_message(self, msg: dict):
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return {"status": "ignored", "reason": "missing_chat"}

        text, _source = self._extract_message_text(msg)
        command = (text or "").split(maxsplit=1)[0].lower()
        if command == "/start":
            return await self._handle_start(msg)
        if command == "/help":
            await self._send_message(chat_id, "Команды Komandus: /start, /help, /mytasks, /status")
            return {"status": "command", "command": "help"}
        if command == "/mytasks":
            return await self._handle_mytasks(msg)
        if command == "/status":
            return await self._handle_status(msg)
        if command == "/register":
            return await self._handle_register(msg)

        sender_employee = self._employee_by_telegram_user((msg.get("from") or {}).get("id"))
        if sender_employee and sender_employee.pending_rejection_candidate_id and chat.get("type") == "private":
            return await self._finish_rejection(sender_employee, text)

        source = self._get_active_source(chat_id)
        if source is None:
            return {"status": "ignored", "reason": "unregistered_chat"}

        self._upsert_chat(chat, source.organization_id)
        db_message = self._save_message(msg, source.organization_id)
        candidates = await self.process_chat_context(chat_id)

        for candidate in candidates:
            await self._route_candidate_confirmation(candidate)

        return {"status": "processed", "message_id": db_message.id, "candidates_created": len(candidates)}

    async def _handle_start(self, msg: dict):
        sender = msg.get("from") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        username = self._normalize_username(sender.get("username"))
        if not username:
            await self._send_message(chat_id, "Ваш аккаунт ещё не создан. Обратитесь к руководителю.")
            return {"status": "not_connected", "reason": "missing_username"}

        employee = (
            self.db.query(Employee)
            .filter(Employee.telegram_username == username, Employee.is_active.is_(True))
            .first()
        )
        if employee is None:
            await self._send_message(chat_id, "Ваш аккаунт ещё не создан.\nОбратитесь к руководителю.")
            return {"status": "not_connected", "reason": "employee_not_found"}

        employee.telegram_user_id = sender.get("id")
        employee.telegram_connected = True
        self.db.commit()
        await self._send_message(chat_id, "Вы успешно подключены к Komandus")
        return {"status": "connected", "employee_id": employee.id}

    async def _handle_register(self, msg: dict):
        chat = msg.get("chat") or {}
        sender = msg.get("from") or {}
        chat_id = chat.get("id")
        manager = self._employee_by_telegram_user(sender.get("id"))
        if manager is None or manager.role not in MANAGER_ROLES:
            await self._send_message(chat_id, "Зарегистрировать чат может только подключённый менеджер Komandus.")
            return {"status": "ignored", "reason": "manager_not_connected"}
        if chat.get("type") == "private":
            await self._send_message(chat_id, "Добавьте бота в группу, сделайте администратором и отправьте /register в группе.")
            return {"status": "ignored", "reason": "private_chat"}

        source = self._get_active_source(chat_id, include_inactive=True)
        if source is None:
            source = TelegramSource(chat_id=chat_id, organization_id=manager.organization_id)
            self.db.add(source)
        source.organization_id = manager.organization_id
        source.chat_title = chat.get("title") or chat.get("username")
        source.is_active = True
        self.db.commit()
        self._upsert_chat(chat, manager.organization_id)
        await self._send_message(chat_id, "Telegram чат подключён к Komandus. Теперь сообщения будут анализироваться.")
        return {"status": "registered", "chat_id": chat_id, "organization_id": manager.organization_id}

    async def _handle_mytasks(self, msg: dict):
        sender = msg.get("from") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        employee = self._employee_by_telegram_user(sender.get("id"))
        if employee is None:
            await self._send_message(chat_id, "Сначала подключите аккаунт через /start")
            return {"status": "ignored", "reason": "employee_not_connected"}
        tasks = (
            self.db.query(Task)
            .filter(Task.organization_id == employee.organization_id, Task.assignee_employee_id == employee.id, Task.status.in_(("OPEN", "IN_PROGRESS")))
            .order_by(Task.created_at.desc())
            .limit(10)
            .all()
        )
        if not tasks:
            await self._send_message(chat_id, "У вас нет открытых задач.")
        else:
            lines = ["Ваши открытые задачи:"] + [f"• {task.title} — {task.status}" for task in tasks]
            await self._send_message(chat_id, "\n".join(lines))
        return {"status": "command", "command": "mytasks", "tasks": len(tasks)}

    async def _handle_status(self, msg: dict):
        sender = msg.get("from") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        employee = self._employee_by_telegram_user(sender.get("id"))
        if employee is None:
            await self._send_message(chat_id, "Сначала подключите аккаунт через /start")
            return {"status": "ignored", "reason": "employee_not_connected"}
        query = self.db.query(Task).filter(Task.organization_id == employee.organization_id)
        if employee.role == "EMPLOYEE":
            query = query.filter(Task.assignee_employee_id == employee.id)
        tasks = query.all()
        counts = {status: sum(1 for task in tasks if task.status == status) for status in ("OPEN", "IN_PROGRESS", "DONE")}
        await self._send_message(chat_id, f"Статус задач:\nОткрыто: {counts['OPEN']}\nВ работе: {counts['IN_PROGRESS']}\nЗавершено: {counts['DONE']}")
        return {"status": "command", "command": "status", "counts": counts}

    async def _handle_callback(self, callback: dict):
        callback_id = callback["id"]
        data = callback.get("data", "")
        actor = self._employee_by_telegram_user((callback.get("from") or {}).get("id"))
        normalized = self._parse_callback_data(data)
        if normalized is None:
            return {"status": "ignored", "reason": "unsupported_callback"}
        action, candidate_id = normalized

        candidate = self.db.query(TaskCandidate).filter(TaskCandidate.id == candidate_id).first()
        if not candidate or candidate.status not in {"PENDING", "pending"}:
            await self._answer_callback(callback_id, "Эта задача уже была обработана!")
            return {"status": "ignored", "reason": "candidate_already_processed"}
        if actor and actor.organization_id != candidate.organization_id:
            await self._answer_callback(callback_id, "Нет доступа к задаче другой организации.")
            return {"status": "ignored", "reason": "wrong_organization"}

        if action in {"accept", "approve"}:
            task = await create_task_from_candidate(self.db, candidate, actor)
            await self._answer_callback(callback_id, "Задача принята.")
            await self._notify_managers(candidate.organization_id, f"{actor.full_name if actor else 'Сотрудник'} принял задачу: {candidate.title}")
            return {"status": "accepted", "task_id": task.id, "yougile_task_id": task.yougile_task_id}

        if action == "reject":
            if actor:
                actor.pending_rejection_candidate_id = candidate.id
                self.db.commit()
            await self._answer_callback(callback_id, "Напишите причину отказа следующим сообщением.")
            await self._send_message((callback.get("message") or {}).get("chat", {}).get("id"), "Напишите причину отказа следующим сообщением.")
            return {"status": "awaiting_rejection_reason", "candidate_id": candidate.id}

        return {"status": "ignored", "reason": "unknown_action"}

    async def _finish_rejection(self, employee: Employee, reason: str):
        candidate = self.db.query(TaskCandidate).filter(TaskCandidate.id == employee.pending_rejection_candidate_id).first()
        if candidate is None:
            employee.pending_rejection_candidate_id = None
            self.db.commit()
            return {"status": "ignored", "reason": "candidate_missing"}
        candidate.status = "REJECTED"
        candidate.rejection_reason = reason
        employee.pending_rejection_candidate_id = None
        self.db.commit()
        await self._send_message(employee.telegram_user_id, "Отказ сохранён.")
        await self._notify_managers(candidate.organization_id, f"{employee.full_name} отклонил задачу: {candidate.title}\nПричина: {reason}")
        return {"status": "rejected", "candidate_id": candidate.id}

    def _upsert_chat(self, chat: dict, organization_id: int | None = None) -> TelegramChat:
        telegram_chat_id = chat["id"]
        db_chat = self.db.query(TelegramChat).filter(TelegramChat.telegram_chat_id == telegram_chat_id).first()
        if db_chat is None:
            db_chat = TelegramChat(telegram_chat_id=telegram_chat_id)
            self.db.add(db_chat)
        db_chat.organization_id = organization_id or db_chat.organization_id
        db_chat.title = chat.get("title") or chat.get("username") or chat.get("first_name")
        db_chat.type = chat.get("type")
        self.db.commit()
        self.db.refresh(db_chat)
        return db_chat

    def _save_message(self, msg: dict, organization_id: int | None = None) -> Message:
        existing = self.db.query(Message).filter(Message.chat_id == msg["chat"]["id"], Message.telegram_message_id == msg["message_id"]).first()
        if existing:
            return existing
        sender = msg.get("from") or {}
        text, source = self._extract_message_text(msg)
        db_message = Message(
            organization_id=organization_id,
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

    def _save_candidates(self, source: TelegramSource, message: Message, tasks: list[dict]) -> list[TaskCandidate]:
        candidates = []
        for task in tasks:
            title = task.get("title")
            if not title:
                continue
            relation = task.get("dedup_relation") or "none"
            existing_id = task.get("existing_task_id")
            if relation in ("duplicate", "update") and existing_id:
                self._attach_duplicate(source, message, task, int(existing_id))
                continue
            duplicate = self.db.query(TaskCandidate).filter(TaskCandidate.chat_id == message.chat_id, TaskCandidate.title == title, TaskCandidate.status.in_(("PENDING", "ACCEPTED", "pending", "approved", "confirmed"))).first()
            if duplicate:
                continue
            candidate = TaskCandidate(
                organization_id=source.organization_id,
                message_id=message.id,
                chat_id=message.chat_id,
                title=title,
                description=task.get("description") or task.get("source_excerpt"),
                assignee_raw=task.get("assignee_raw"),
                assignee_id=self._resolve_assignee_id(source, task),
                deadline_raw=task.get("deadline_raw"),
                deadline=task.get("deadline_raw"),
                confidence=self._confidence_percent(task.get("confidence", 100.0)),
                status="PENDING",
                action=task.get("action", "create"),
                source_message_id=message.telegram_message_id,
                source_chat_id=message.chat_id,
                source_excerpt=task.get("source_excerpt"),
                llm_block=task.get("llm_block"),
            )
            self.db.add(candidate)
            candidates.append(candidate)
        self.db.commit()
        for candidate in candidates:
            self.db.refresh(candidate)
        return candidates

    def _build_llm_context(self, source: TelegramSource) -> dict:
        employees = self.db.query(Employee).filter(Employee.organization_id == source.organization_id, Employee.is_active.is_(True)).all()
        open_tasks = self.db.query(Task).filter(Task.organization_id == source.organization_id, Task.status.in_(("OPEN", "IN_PROGRESS"))).all()
        return {
            "team_members": [{"id": str(e.id), "display_name": e.full_name, "role": e.role} for e in employees],
            "open_tasks": [
                {"id": str(t.id), "title": t.title, "assignee_id": str(t.assignee_employee_id) if t.assignee_employee_id else None, "deadline": t.deadline, "status": t.status}
                for t in open_tasks
            ],
        }

    def _resolve_assignee_id(self, source: TelegramSource, task: dict) -> int | None:
        raw_id = task.get("assignee_id")
        if raw_id:
            return int(raw_id)
        assignee = self._find_assignee(source.organization_id, task.get("assignee_raw"))
        return assignee.id if assignee else None

    def _attach_duplicate(self, source: TelegramSource, message: Message, task: dict, existing_task_id: int) -> None:
        candidate = TaskCandidate(
            organization_id=source.organization_id,
            message_id=message.id,
            chat_id=message.chat_id,
            title=task["title"],
            description=task.get("description") or task.get("source_excerpt"),
            assignee_raw=task.get("assignee_raw"),
            assignee_id=self._resolve_assignee_id(source, task),
            deadline_raw=task.get("deadline_raw"),
            deadline=task.get("deadline_raw"),
            confidence=self._confidence_percent(task.get("confidence", 1.0)),
            status="DUPLICATE",
            action=task.get("dedup_relation"),
            source_message_id=message.telegram_message_id,
            source_chat_id=message.chat_id,
            source_excerpt=task.get("source_excerpt"),
            llm_block=f"duplicate_of:{existing_task_id}",
        )
        self.db.add(candidate)

    async def _route_candidate_confirmation(self, candidate: TaskCandidate):
        assignee = self.db.query(Employee).filter(Employee.id == candidate.assignee_id).first() if candidate.assignee_id else None
        if candidate.confidence >= HIGH_CONFIDENCE_THRESHOLD and assignee and assignee.telegram_connected and assignee.telegram_user_id:
            await self._send_confirmation_inline(assignee.telegram_user_id, candidate)
            return
        await self._notify_managers(candidate.organization_id, self._candidate_text(candidate), candidate)

    def _get_unprocessed_chat_messages(self, chat_id: int) -> list[Message]:
        db_chat = self.db.query(TelegramChat).filter(TelegramChat.telegram_chat_id == chat_id).first()
        query = self.db.query(Message).filter(Message.chat_id == chat_id)
        if db_chat and db_chat.last_processed_message_id is not None:
            query = query.filter(Message.telegram_message_id > db_chat.last_processed_message_id)
        rows = query.order_by(desc(Message.telegram_message_id)).limit(settings.TELEGRAM_CONTEXT_LIMIT).all()
        return list(reversed(rows))

    def _mark_chat_processed(self, chat_id: int, telegram_message_id: int) -> None:
        db_chat = self.db.query(TelegramChat).filter(TelegramChat.telegram_chat_id == chat_id).first()
        if db_chat:
            db_chat.last_processed_message_id = telegram_message_id
            self.db.commit()

    def _format_transcript(self, messages: list[Message]) -> str:
        return "\n".join(f"{message.sender_name or message.username or message.telegram_user_id or 'unknown'}: {message.text}" for message in messages)

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
        name = " ".join(part for part in [sender.get("first_name"), sender.get("last_name")] if part)
        return name or sender.get("username")

    def _get_active_source(self, chat_id: int, include_inactive: bool = False) -> TelegramSource | None:
        query = self.db.query(TelegramSource).filter(TelegramSource.chat_id == chat_id)
        if not include_inactive:
            query = query.filter(TelegramSource.is_active.is_(True))
        return query.first()

    def _employee_by_telegram_user(self, telegram_user_id: int | None) -> Employee | None:
        if telegram_user_id is None:
            return None
        return self.db.query(Employee).filter(Employee.telegram_user_id == telegram_user_id, Employee.is_active.is_(True)).first()

    def _find_assignee(self, organization_id: int, assignee_raw: str | None) -> Employee | None:
        if not assignee_raw:
            return None
        raw = assignee_raw.strip().lstrip("@")
        return (
            self.db.query(Employee)
            .filter(
                Employee.organization_id == organization_id,
                Employee.is_active.is_(True),
                or_(Employee.telegram_username == raw, Employee.full_name.ilike(f"%{assignee_raw.strip()}%")),
            )
            .first()
        )

    def _normalize_username(self, username: str | None) -> str | None:
        return username.strip().lstrip("@") if username else None

    def _confidence_percent(self, value: float | int | str) -> float:
        confidence = float(value or 0)
        return confidence * 100 if confidence <= 1 else confidence

    def _parse_callback_data(self, data: str) -> tuple[str, int] | None:
        parts = data.split("_")
        if len(parts) == 3 and parts[0] == "task":
            return parts[1], int(parts[2])
        if len(parts) == 3 and parts[0] == "candidate":
            return parts[1], int(parts[2])
        return None

    def _candidate_text(self, candidate: TaskCandidate) -> str:
        return (
            "Найдена задача:\n\n"
            f"Название: {candidate.title}\n"
            f"Срок: {candidate.deadline or candidate.deadline_raw or 'не указан'}\n"
            f"Исполнитель: {candidate.assignee_raw or 'не назначен'}\n"
            f"Уверенность: {int(candidate.confidence)}%"
        )

    async def _send_confirmation_inline(self, chat_id: int, candidate: TaskCandidate):
        await self._send_message(chat_id, self._candidate_text(candidate), reply_markup={
            "inline_keyboard": [[
                {"text": "Принять", "callback_data": f"candidate_accept_{candidate.id}"},
                {"text": "Отклонить", "callback_data": f"candidate_reject_{candidate.id}"},
            ]]
        })

    async def _notify_managers(self, organization_id: int | None, text: str, candidate: TaskCandidate | None = None):
        if organization_id is None:
            return
        managers = self.db.query(Employee).filter(Employee.organization_id == organization_id, Employee.role.in_(MANAGER_ROLES), Employee.telegram_connected.is_(True), Employee.telegram_user_id.is_not(None)).all()
        for manager in managers:
            if candidate:
                await self._send_confirmation_inline(manager.telegram_user_id, candidate)
            else:
                await self._send_message(manager.telegram_user_id, text)

    async def _send_message(self, chat_id: int | None, text: str, reply_markup: dict | None = None):
        token = settings.BOT_TOKEN
        if not token or chat_id is None:
            logger.info("[Mock Bot] chat=%s text=%s", chat_id, text)
            return
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=5.0)
        except Exception as exc:
            logger.error("Telegram API Error (sendMessage): %s", exc)

    async def _answer_callback(self, callback_id: str, text: str):
        token = settings.BOT_TOKEN
        if not token:
            return
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery", json={"callback_query_id": callback_id, "text": text}, timeout=5.0)
        except Exception as exc:
            logger.error("Telegram API Error (answerCallback): %s", exc)
