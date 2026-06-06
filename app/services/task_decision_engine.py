from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.audit.services import AuditService
from app.auth.magic import MagicLoginService
from app.common.enums import ConfirmationStatus, TaskSourceType, TaskStatus
from app.models.models import Employee, KomandusTask, Message, Notification, OrganizationChat, TaskCandidate, TaskConfirmation, TaskSource, TelegramAccountLink, TelegramChat, TelegramConnectCode
from app.services.kanban_adapter import KanbanAdapter
from app.services.llm_service import llm_service
from app.telegram.callbacks import TelegramCallbackRouter
from app.telegram.commands import TelegramCommandRouter
from app.telegram.service import TelegramDeliveryError, TelegramService



class TaskDecisionEngine:
    def __init__(self, db: Session):
        self.db = db
        self.kanban = KanbanAdapter(db)
        self.telegram = TelegramService()
        self.audit = AuditService(db)

    async def process_update(self, payload: dict):
        if payload.get("message"):
            return await self._handle_message(payload["message"])
        if payload.get("edited_message"):
            return await self._handle_message(payload["edited_message"])
        if payload.get("callback_query"):
            return await TelegramCallbackRouter(self).dispatch(payload["callback_query"])
        if payload.get("chat_member"):
            return await self._handle_chat_member(payload["chat_member"])
        if payload.get("my_chat_member"):
            return await self._handle_my_chat_member(payload["my_chat_member"])
        return {"status": "ignored", "reason": "unsupported_update"}

    async def process_chat_context(self, chat_id: int, topic_id: int | None = None) -> list[TaskCandidate]:
        messages = self._get_unprocessed_chat_messages(chat_id, topic_id)
        if not messages:
            return []

        transcript = self._format_transcript(messages)
        extraction = await llm_service.extract_tasks(transcript)
        last_message = messages[-1]
        if not extraction.get("has_task"):
            self._mark_chat_processed(chat_id, last_message.telegram_message_id, topic_id)
            return []

        candidates = self._save_candidates(last_message, extraction["tasks"])
        self._mark_chat_processed(chat_id, last_message.telegram_message_id, topic_id)
        return candidates

    async def _handle_message(self, msg: dict):
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return {"status": "ignored", "reason": "missing_chat"}

        command_result = await self._handle_command(msg)
        if command_result:
            return command_result

        self._upsert_chat(chat)
        db_message = self._save_message(msg)
        topic_id = msg.get("message_thread_id")
        task_source = self._task_source_for_message(chat_id, topic_id)
        org_chat = self.db.query(OrganizationChat).filter(OrganizationChat.telegram_chat_id == chat_id, OrganizationChat.ai_enabled.is_(True), OrganizationChat.is_active.is_(True)).first()
        if not task_source and org_chat and topic_id is None:
            task_source = self._ensure_task_source(org_chat.organization_id, chat_id, chat.get("title") or "Рабочий чат", chat.get("type"), None, org_chat.department_id, org_chat.team_id)
        if (not task_source or not task_source.ai_enabled) and chat.get("type") in {"group", "supergroup", "channel"}:
            return {"status": "stored", "message_id": db_message.id, "ai_enabled": False, "reason": "source_not_mapped"}
        candidates = await self.process_chat_context(chat_id, topic_id)

        for candidate in candidates:
            await self._route_confirmation(candidate, task_source)

        return {
            "status": "processed",
            "message_id": db_message.id,
            "candidates_created": len(candidates),
        }

    async def _handle_task_callback(self, callback: dict):
        callback_id = callback["id"]
        data = callback.get("data", "")
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        msg_id = message.get("message_id")

        if data.startswith("task_accept:"):
            return await self._handle_task_accept(callback_id, data.split(":", 1)[1], chat_id, msg_id)
        if data.startswith("task_reject:"):
            return await self._ask_reject_reason(callback_id, data.split(":", 1)[1], chat_id, msg_id)
        if data.startswith("task_reject_reason:"):
            _, task_id, reason_code = data.split(":", 2)
            return await self._handle_task_reject(callback_id, task_id, reason_code, chat_id, msg_id)
        if data.startswith("task_clarify:"):
            await self.telegram.answer_callback_query(callback_id, "Менеджеру отправлен запрос на уточнение.")
            return {"status": "clarification_requested", "task_id": data.split(":", 1)[1]}

        if not data.startswith("task_"):
            return {"status": "ignored", "reason": "unsupported_callback"}

        parts = data.split("_")
        action = parts[1]
        candidate_id = int(parts[2])

        candidate = self.db.query(TaskCandidate).filter(TaskCandidate.id == candidate_id).first()
        if not candidate or candidate.status != "pending":
            await self.telegram.answer_callback_query(callback_id, "Эта задача уже была обработана!")
            return {"status": "ignored", "reason": "candidate_already_processed"}

        if action == "approve":
            candidate.status = "approved"
            self.db.commit()
            task_status = "done" if candidate.action == "complete" else "todo"
            task = self.kanban.add_task(title=candidate.title, description=candidate.source_excerpt or "Извлечено из Telegram-чата.", assignee=candidate.assignee_raw, deadline=candidate.deadline_raw, candidate_id=candidate.id, confidence=candidate.confidence, status=task_status)
            new_text = f"✅ Задача утверждена и добавлена на доску\n\n📌 Название: {task.title}\n👤 Ответственный: {candidate.assignee_raw or 'не назначен'}\n📅 Срок: {candidate.deadline_raw or 'не указан'}\n📊 Статус: {task.status.upper()}"
            if chat_id and msg_id:
                await self.telegram.edit_message_text(chat_id, msg_id, new_text)
            await self.telegram.answer_callback_query(callback_id, "Добавлено на доску!")
            return {"status": "approved", "task_id": task.id}

        if action == "reject":
            candidate.status = "rejected"
            self.db.commit()
            if chat_id and msg_id:
                await self.telegram.edit_message_text(chat_id, msg_id, f"❌ Кандидат на задачу отклонён.\n\n{candidate.title}")
            await self.telegram.answer_callback_query(callback_id, "Отклонено.")
            return {"status": "rejected", "candidate_id": candidate.id}

        return {"status": "ignored", "reason": "unknown_action"}


    async def _handle_command(self, msg: dict):
        text = (msg.get("text") or "").strip()
        if not text.startswith("/"):
            return None
        command = text.split(maxsplit=1)[0].split("@")[0].lower()
        if command == "/connect":
            args = text.split(maxsplit=1)[1:]
            return await self._connect_chat(msg, args[0].strip() if args else "")
        return await TelegramCommandRouter(self.db, self.telegram).dispatch(msg)

    async def _connect_chat(self, msg: dict, code: str):
        chat = msg.get("chat") or {}
        if chat.get("type") not in {"group", "supergroup", "channel"}:
            await self._send_message(chat.get("id"), "Команду /connect нужно выполнить в рабочем групповом чате.")
            return {"status": "ignored", "reason": "not_group_chat"}
        code_row = self.db.query(TelegramConnectCode).filter(TelegramConnectCode.code == code, TelegramConnectCode.status == "PENDING").first()
        if not code_row:
            await self._send_message(chat.get("id"), "Код подключения не найден или уже использован.")
            return {"status": "rejected", "reason": "invalid_code"}
        members_count = await self._get_chat_member_count(chat.get("id"))
        bot_is_admin = await self._bot_is_admin(chat.get("id"))
        org_chat = self.db.query(OrganizationChat).filter(OrganizationChat.organization_id == code_row.organization_id, OrganizationChat.telegram_chat_id == chat.get("id")).first()
        if not org_chat:
            org_chat = OrganizationChat(organization_id=code_row.organization_id, telegram_chat_id=chat.get("id"), title=chat.get("title") or "Рабочий чат")
            self.db.add(org_chat)
        org_chat.department_id = code_row.department_id
        org_chat.team_id = code_row.team_id
        org_chat.title = chat.get("title") or org_chat.title
        org_chat.chat_type = chat.get("type")
        org_chat.members_count = members_count
        org_chat.bot_is_admin = bot_is_admin
        org_chat.is_active = True
        org_chat.ai_enabled = True
        topic_id = msg.get("message_thread_id")
        task_source = self._ensure_task_source(code_row.organization_id, chat.get("id"), chat.get("title") or "Рабочий чат", chat.get("type"), topic_id, code_row.department_id, code_row.team_id)
        code_row.status = "USED"
        from datetime import datetime
        code_row.used_at = datetime.utcnow()
        self.db.commit()
        if bot_is_admin:
            await self._send_message(chat.get("id"), f"✅ Источник задач подключен к Командусу: {task_source.title}. AI-анализ сообщений включен.")
        else:
            await self._send_message(chat.get("id"), "⚠️ Чат подключен, но бот не является администратором. Назначьте бота администратором, иначе часть функций Telegram будет недоступна.")
        return {"status": "connected", "chat_id": chat.get("id"), "task_source_id": str(task_source.id), "members_count": members_count, "bot_is_admin": bot_is_admin}

    def _task_source_for_message(self, chat_id: int, topic_id: int | None) -> TaskSource | None:
        query = self.db.query(TaskSource).filter(TaskSource.telegram_chat_id == chat_id, TaskSource.is_active.is_(True))
        if topic_id:
            source = query.filter(TaskSource.source_type == TaskSourceType.TELEGRAM_TOPIC.value, TaskSource.telegram_topic_id == topic_id).first()
            if source:
                return source
        return query.filter(TaskSource.source_type == TaskSourceType.TELEGRAM_CHAT.value, TaskSource.telegram_topic_id.is_(None)).first()

    def _ensure_task_source(self, organization_id, chat_id: int, title: str, chat_type: str | None, topic_id: int | None, department_id, team_id) -> TaskSource:
        source_type = TaskSourceType.TELEGRAM_TOPIC.value if topic_id else TaskSourceType.TELEGRAM_CHAT.value
        source = self.db.query(TaskSource).filter(TaskSource.organization_id == organization_id, TaskSource.telegram_chat_id == chat_id, TaskSource.telegram_topic_id == topic_id, TaskSource.source_type == source_type).first()
        if not source:
            source = TaskSource(organization_id=organization_id, source_type=source_type, telegram_chat_id=chat_id, telegram_topic_id=topic_id, title=title, department_id=department_id, team_id=team_id, metadata_json={"chat_type": chat_type})
            self.db.add(source)
        source.title = title or source.title
        source.department_id = department_id
        source.team_id = team_id
        source.ai_enabled = True
        source.is_active = True
        self.db.commit(); self.db.refresh(source)
        return source

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
            message_thread_id=msg.get("message_thread_id"),
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
                    TaskCandidate.title == title,
                    TaskCandidate.status.in_(("pending", "approved", "confirmed")),
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

    def _get_unprocessed_chat_messages(self, chat_id: int, topic_id: int | None = None) -> list[Message]:
        db_chat = self.db.query(TelegramChat).filter(TelegramChat.telegram_chat_id == chat_id).first()
        query = self.db.query(Message).filter(Message.chat_id == chat_id)
        if topic_id is not None:
            query = query.filter(Message.message_thread_id == topic_id)
        else:
            query = query.filter(Message.message_thread_id.is_(None))
        if topic_id is None and db_chat and db_chat.last_processed_message_id is not None:
            query = query.filter(Message.telegram_message_id > db_chat.last_processed_message_id)

        rows = query.order_by(desc(Message.telegram_message_id)).limit(settings.TELEGRAM_CONTEXT_LIMIT).all()
        return list(reversed(rows))

    def _mark_chat_processed(self, chat_id: int, telegram_message_id: int, topic_id: int | None = None) -> None:
        if topic_id is not None:
            return
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


    async def _send_message(self, chat_id: int | None, text: str, reply_markup: dict | None = None):
        if chat_id is None:
            raise TelegramDeliveryError("Cannot send Telegram message: chat_id is missing.")
        try:
            return await self.telegram.send_message(chat_id, text, reply_markup=reply_markup)
        except TelegramDeliveryError as exc:
            self.audit.log(action="Telegram Delivery Failed", entity_type="TelegramMessage", entity_id=str(chat_id), metadata={"error": str(exc)})
            raise

    async def _get_chat_member_count(self, chat_id: int | None) -> int | None:
        if chat_id is None:
            return None
        return await self.telegram.get_chat_member_count(chat_id)

    async def _bot_is_admin(self, chat_id: int | None) -> bool:
        if chat_id is None:
            return False
        member = await self.telegram.get_chat_member(chat_id, "@self")
        status = member.get("result", {}).get("status")
        return status in {"administrator", "creator"}

    async def _route_confirmation(self, candidate: TaskCandidate, source: TaskSource | None):
        confidence = candidate.confidence or 0
        employee = self._employee_for_candidate(candidate, source)
        if confidence >= 0.8 and employee and employee.telegram_id:
            return await self._send_candidate_confirmation(employee.telegram_id, candidate, employee_flow=True)
        manager = self._manager_for_source(source, employee)
        if manager and manager.telegram_id:
            return await self._send_candidate_confirmation(manager.telegram_id, candidate, employee_flow=False)
        self.audit.log(
            action="Task Confirmation Routing Failed",
            organization_id=source.organization_id if source else None,
            entity_type="TaskCandidate",
            entity_id=candidate.id,
            metadata={"confidence": confidence, "assignee_raw": candidate.assignee_raw},
        )
        return {"status": "not_routed", "candidate_id": candidate.id}

    async def _send_candidate_confirmation(self, chat_id: int, candidate: TaskCandidate, *, employee_flow: bool):
        text = (
            "🤖 Обнаружена задача!\n\n"
            f"📝 Что сделать: {candidate.title}\n"
            f"👤 Ответственный: {candidate.assignee_raw or 'Не назначен'}\n"
            f"📅 Дедлайн: {candidate.deadline_raw or 'Не указан'}\n"
            f"🎯 Уверенность AI: {int((candidate.confidence or 0) * 100)}%"
        )
        if employee_flow:
            markup = {"inline_keyboard": [[{"text": "✅ Принять", "callback_data": f"task_approve_{candidate.id}"}, {"text": "❌ Отклонить", "callback_data": f"task_reject_{candidate.id}"}]]}
        else:
            markup = {"inline_keyboard": [[{"text": "✅ Подтвердить", "callback_data": f"task_approve_{candidate.id}"}, {"text": "❌ Отклонить", "callback_data": f"task_reject_{candidate.id}"}], [{"text": "✏️ Изменить", "callback_data": f"task_clarify:{candidate.id}"}]]}
        return await self.telegram.send_message(chat_id, text, reply_markup=markup)

    def _employee_for_candidate(self, candidate: TaskCandidate, source: TaskSource | None) -> Employee | None:
        if not candidate.assignee_raw:
            return None
        assignee = candidate.assignee_raw.strip().lower().lstrip("@")
        query = self.db.query(Employee).filter(Employee.is_active.is_(True))
        if source:
            query = query.filter(Employee.organization_id == source.organization_id)
        for employee in query.all():
            aliases = {
                (employee.full_name or "").lower(),
                (employee.email or "").lower(),
                (employee.telegram_username or "").lower().lstrip("@"),
            }
            if assignee in aliases:
                return employee
        return None

    def _manager_for_source(self, source: TaskSource | None, employee: Employee | None = None) -> Employee | None:
        if employee and employee.manager_id:
            manager = self.db.query(Employee).filter(Employee.id == employee.manager_id, Employee.is_active.is_(True)).first()
            if manager:
                return manager
        query = self.db.query(Employee).filter(Employee.is_active.is_(True), Employee.role == "MANAGER")
        if source:
            query = query.filter(Employee.organization_id == source.organization_id)
            if source.team_id:
                scoped = query.filter(Employee.team_id == source.team_id).first()
                if scoped:
                    return scoped
            if source.department_id:
                scoped = query.filter(Employee.department_id == source.department_id).first()
                if scoped:
                    return scoped
        return query.first()

    async def _handle_task_accept(self, callback_id: str, task_id: str, chat_id: int | None, message_id: int | None):
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        confirmation = self.db.query(TaskConfirmation).filter(TaskConfirmation.task_id == task.id).first()
        if not confirmation:
            confirmation = TaskConfirmation(organization_id=task.organization_id, task_id=task.id, employee_id=task.employee_id)
            self.db.add(confirmation)
        task.status = TaskStatus.ACCEPTED.value
        task.accepted_at = datetime.utcnow()
        confirmation.status = ConfirmationStatus.APPROVED.value
        confirmation.responded_at = datetime.utcnow()
        self.db.commit()
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, f"✅ Задача принята: {task.title}")
        await self.telegram.answer_callback_query(callback_id, "Задача принята")
        return {"status": "accepted", "task_id": task_id}

    async def _ask_reject_reason(self, callback_id: str, task_id: str, chat_id: int | None, message_id: int | None):
        reasons = [("no_time", "Нет времени"), ("not_mine", "Не моя зона"), ("no_access", "Нет доступа"), ("need_details", "Нужны уточнения"), ("other", "Другое")]
        markup = {"inline_keyboard": [[{"text": label, "callback_data": f"task_reject_reason:{task_id}:{code}"}] for code, label in reasons]}
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, "Выберите причину отказа:", reply_markup=markup)
        await self.telegram.answer_callback_query(callback_id, "Укажите причину отказа")
        return {"status": "reason_requested", "task_id": task_id}

    async def _handle_task_reject(self, callback_id: str, task_id: str, reason_code: str, chat_id: int | None, message_id: int | None):
        reason_labels = {"no_time": "Нет времени", "not_mine": "Не моя зона ответственности", "no_access": "Нет доступа", "need_details": "Нужны уточнения", "other": "Другое"}
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        confirmation = self.db.query(TaskConfirmation).filter(TaskConfirmation.task_id == task.id).first()
        if not confirmation:
            confirmation = TaskConfirmation(organization_id=task.organization_id, task_id=task.id, employee_id=task.employee_id)
            self.db.add(confirmation)
        task.status = TaskStatus.REJECTED.value
        task.rejected_at = datetime.utcnow()
        confirmation.status = ConfirmationStatus.DECLINED.value
        confirmation.decline_reason = reason_labels.get(reason_code, reason_code)
        confirmation.responded_at = datetime.utcnow()
        self.db.commit()
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, f"❌ Задача отклонена: {task.title}\nПричина: {confirmation.decline_reason}")
        await self.telegram.answer_callback_query(callback_id, "Отказ сохранен")
        return {"status": "rejected", "task_id": task_id, "reason": confirmation.decline_reason}

    async def _handle_chat_member(self, payload: dict):
        return await self._sync_chat_membership(payload)

    async def _handle_my_chat_member(self, payload: dict):
        return await self._sync_chat_membership(payload)

    async def _sync_chat_membership(self, payload: dict):
        chat = payload.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return {"status": "ignored", "reason": "missing_chat"}
        org_chat = self.db.query(OrganizationChat).filter(OrganizationChat.telegram_chat_id == chat_id).first()
        if not org_chat:
            return {"status": "ignored", "reason": "chat_not_connected"}
        new_status = (payload.get("new_chat_member") or {}).get("status")
        org_chat.is_active = new_status not in {"left", "kicked"}
        org_chat.bot_is_admin = new_status in {"administrator", "creator"}
        org_chat.chat_type = chat.get("type") or org_chat.chat_type
        org_chat.title = chat.get("title") or org_chat.title
        self.db.commit()
        return {"status": "updated", "chat_id": chat_id, "bot_status": new_status}
