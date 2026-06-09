from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.audit.services import AuditService
from app.auth.magic import MagicLoginService
from app.common.enums import ConfirmationStatus, Role, TaskSourceType, TaskStatus
from app.common.rbac import normalize_role
from app.models.models import Employee, KomandusTask, Message, Notification, OrganizationChat, TaskCandidate, TaskConfirmation, TaskSource, TelegramAccountLink, TelegramChat, TelegramConnectCode
from app.services.kanban_adapter import KanbanAdapter
from app.services.llm_service import llm_service
from app.telegram.callbacks import TelegramCallbackRouter
from app.telegram.commands import TelegramCommandRouter
from app.telegram.service import TelegramDeliveryError, TelegramService


logger = logging.getLogger(__name__)


def _name_match_strength(full_name: str | None, needle: str) -> int:
    name = (full_name or "").strip().lower()
    if not name or not needle:
        return 0
    if name == needle:
        return 3
    if needle in name.split():
        return 2
    if needle in name:
        return 1
    return 0


def match_employee_by_name(assignee_raw: str | None, candidates, *, team_id=None, department_id=None):
    """Resolve a free-text assignee to a single employee, or None if absent/ambiguous.

    Pure helper (no DB) so the matching rules can be unit-tested. ``candidates``
    are objects exposing ``full_name``, ``team_id`` and ``department_id``. The
    same-source team/department is used to break ties; genuine ambiguity yields
    None so the task falls back to manager triage.
    """
    if not assignee_raw:
        return None
    needle = assignee_raw.strip().lower().lstrip("@")
    if not needle:
        return None

    def scope_rank(employee) -> int:
        if team_id and getattr(employee, "team_id", None) == team_id:
            return 2
        if department_id and getattr(employee, "department_id", None) == department_id:
            return 1
        return 0

    scored = [(employee, _name_match_strength(getattr(employee, "full_name", None), needle)) for employee in candidates]
    scored = [(employee, strength) for employee, strength in scored if strength > 0]
    if not scored:
        return None
    best_key = max((strength, scope_rank(employee)) for employee, strength in scored)
    winners = [employee for employee, strength in scored if (strength, scope_rank(employee)) == best_key]
    return winners[0] if len(winners) == 1 else None


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

    async def process_chat_context(self, chat_id: int, task_source: TaskSource | None = None, org_chat: OrganizationChat | None = None, topic_id: int | None = None) -> list[KomandusTask]:
        messages = self._get_unprocessed_chat_messages(chat_id)
        if not messages:
            return []

        transcript = self._format_transcript(messages)
        extraction = await llm_service.extract_tasks(transcript, context=self._build_llm_context(chat_id))
        last_message = messages[-1]
        if not extraction.get("has_task"):
            self._mark_chat_processed(chat_id, last_message.telegram_message_id)
            return []

        candidates = self._save_candidates(last_message, extraction["tasks"])
        self._mark_chat_processed(chat_id, last_message.telegram_message_id)

        # Resolve scoping context when invoked outside the webhook (e.g. /analyze).
        if task_source is None:
            task_source = self._task_source_for_message(chat_id, topic_id)
        if org_chat is None:
            org_chat = self.db.query(OrganizationChat).filter(OrganizationChat.telegram_chat_id == chat_id).first()

        created: list[KomandusTask] = []
        for candidate in candidates:
            task = await self._materialize_and_route(candidate, last_message, task_source, org_chat, chat_id, topic_id)
            if task:
                created.append(task)
        return created

    async def _handle_message(self, msg: dict):
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return {"status": "ignored", "reason": "missing_chat"}

        command_result = await self._handle_command(msg)
        if command_result:
            return command_result

        custom_reject = await self._maybe_custom_reject(msg)
        if custom_reject:
            return custom_reject

        self._upsert_chat(chat)
        db_message = self._save_message(msg)
        topic_id = msg.get("message_thread_id")
        task_source = self._task_source_for_message(chat_id, topic_id)
        org_chat = self.db.query(OrganizationChat).filter(OrganizationChat.telegram_chat_id == chat_id, OrganizationChat.ai_enabled.is_(True), OrganizationChat.is_active.is_(True)).first()
        if not task_source and org_chat:
            task_source = self._ensure_task_source(org_chat.organization_id, chat_id, chat.get("title") or "Рабочий чат", chat.get("type"), None, org_chat.department_id, org_chat.team_id)
        if (not task_source or not task_source.ai_enabled) and chat.get("type") in {"group", "supergroup", "channel"}:
            return {"status": "stored", "message_id": db_message.id, "ai_enabled": False}
        tasks = await self.process_chat_context(chat_id, task_source=task_source, org_chat=org_chat, topic_id=topic_id)

        return {
            "status": "processed",
            "message_id": db_message.id,
            "tasks_created": len(tasks),
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
        if data.startswith("trrc:"):
            return await self._ask_custom_reason(callback_id, data.split(":", 1)[1], chat_id, msg_id)
        if data.startswith("trr:"):
            _, task_id, reason_code = data.split(":", 2)
            return await self._handle_task_reject(callback_id, task_id, reason_code, chat_id, msg_id)
        if data.startswith("task_clarify:"):
            await self.telegram.answer_callback_query(callback_id, "Менеджеру отправлен запрос на уточнение.")
            return {"status": "clarification_requested", "task_id": data.split(":", 1)[1]}
        if data.startswith("mgr_approve:"):
            return await self._handle_manager_approve(callback_id, data.split(":", 1)[1], chat_id, msg_id)
        if data.startswith("mgr_reject_false:"):
            return await self._handle_manager_reject_false(callback_id, data.split(":", 1)[1], chat_id, msg_id)
        if data.startswith("mgr_reject:"):
            return await self._handle_manager_reject(callback_id, data.split(":", 1)[1], chat_id, msg_id)
        if data.startswith("mgr_reassign:"):
            return await self._handle_manager_reassign_prompt(callback_id, data.split(":", 1)[1], chat_id, msg_id)
        if data.startswith("mgr_assign:"):
            _, reassign_task_id, reassign_employee_id = data.split(":", 2)
            return await self._handle_manager_assign(callback_id, reassign_task_id, reassign_employee_id, chat_id, msg_id)
        if data.startswith("mgr_resend:"):
            return await self._handle_manager_resend(callback_id, data.split(":", 1)[1], chat_id, msg_id)

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
        topic_id = msg.get("message_thread_id")
        if chat.get("type") not in {"group", "supergroup", "channel"}:
            await self._send_message(chat.get("id"), "Команду /connect нужно выполнить в рабочем групповом чате.", message_thread_id=topic_id)
            return {"status": "ignored", "reason": "not_group_chat"}
        code_row = self.db.query(TelegramConnectCode).filter(TelegramConnectCode.code == code, TelegramConnectCode.status == "PENDING").first()
        if not code_row:
            await self._send_message(chat.get("id"), "Код подключения не найден или уже использован.", message_thread_id=topic_id)
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
        task_source = self._ensure_task_source(code_row.organization_id, chat.get("id"), chat.get("title") or "Рабочий чат", chat.get("type"), topic_id, code_row.department_id, code_row.team_id)
        code_row.status = "USED"
        from datetime import datetime
        code_row.used_at = datetime.utcnow()
        self.db.commit()
        if bot_is_admin:
            await self._send_message(chat.get("id"), f"✅ Источник задач подключен к Командусу: {task_source.title}. AI-анализ сообщений включен.", message_thread_id=topic_id)
        else:
            await self._send_message(chat.get("id"), "⚠️ Чат подключен, но бот не является администратором. Назначьте бота администратором, иначе часть функций Telegram будет недоступна.", message_thread_id=topic_id)
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

            relation = task.get("dedup_relation") or "none"
            existing_id = task.get("existing_task_id")
            if relation in ("duplicate", "update") and existing_id:
                self._apply_dedup(existing_id, relation, task)
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
                assignee_raw=self._engine_assignee_raw(task) or task.get("assignee_raw"),
                deadline_raw=task.get("deadline_raw"),
                deadline=task.get("deadline"),
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

    def _build_llm_context(self, chat_id: int) -> dict:
        org_chat = self.db.query(OrganizationChat).filter(OrganizationChat.telegram_chat_id == chat_id).first()
        if not org_chat:
            return {}
        org_id = org_chat.organization_id
        employees = self.db.query(Employee).filter(Employee.organization_id == org_id, Employee.is_active.is_(True)).all()
        open_tasks = self.db.query(KomandusTask).filter(KomandusTask.organization_id == org_id, KomandusTask.status.notin_(["DONE", "REJECTED", "CANCELLED"])).all()
        return {
            "team_members": [{"id": str(e.id), "display_name": e.full_name, "role": e.role} for e in employees],
            "open_tasks": [
                {"id": str(t.id), "title": t.title, "assignee_id": str(t.employee_id) if t.employee_id else None, "deadline": t.due_at.isoformat() if t.due_at else None, "status": t.status}
                for t in open_tasks
            ],
        }

    def _engine_assignee_raw(self, task: dict) -> str | None:
        raw_id = task.get("assignee_id")
        if not raw_id:
            return None
        try:
            UUID(str(raw_id))
        except (ValueError, TypeError):
            return None
        employee = self.db.query(Employee).filter(Employee.id == raw_id, Employee.is_active.is_(True)).first()
        if not employee:
            return None
        if employee.telegram_username:
            return "@" + employee.telegram_username.lstrip("@")
        return employee.full_name

    def _apply_dedup(self, existing_task_id: str, relation: str, task: dict) -> None:
        due = self._parse_deadline(task.get("deadline"))
        if relation != "update" or not due:
            return
        try:
            existing = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(str(existing_task_id))).first()
            if existing:
                existing.due_at = due
                self.db.commit()
        except (ValueError, TypeError):
            pass

    def _parse_deadline(self, iso: str | None) -> datetime | None:
        if not iso:
            return None
        try:
            return datetime.fromisoformat(iso).astimezone(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
        except (ValueError, TypeError):
            return None

    def _source_title(self, chat_id: int) -> str | None:
        if self.db is None:
            return None
        org_chat = self.db.query(OrganizationChat).filter(OrganizationChat.telegram_chat_id == chat_id).first()
        if org_chat and org_chat.title:
            return org_chat.title
        task_source = self.db.query(TaskSource).filter(TaskSource.telegram_chat_id == chat_id).first()
        return task_source.title if task_source else None

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
        lines = []
        for message in messages:
            speaker = self._speaker_name(message)
            lines.append(f"{speaker}: {message.text}")
        return "\n".join(lines)

    def _speaker_name(self, message: Message) -> str:
        employee = None
        if message.telegram_user_id:
            employee = self.db.query(Employee).filter(Employee.telegram_id == message.telegram_user_id, Employee.is_active.is_(True)).first()
        if not employee and message.username:
            uname = message.username.lstrip("@").lower()
            employee = self.db.query(Employee).filter(func.lower(Employee.telegram_username).in_((uname, "@" + uname)), Employee.is_active.is_(True)).first()
        if employee:
            return employee.full_name
        return message.sender_name or message.username or str(message.telegram_user_id or "unknown")

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


    async def _send_message(self, chat_id: int | None, text: str, reply_markup: dict | None = None, message_thread_id: int | None = None):
        if chat_id is None:
            raise TelegramDeliveryError("Cannot send Telegram message: chat_id is missing.")
        try:
            return await self.telegram.send_message(chat_id, text, reply_markup=reply_markup, message_thread_id=message_thread_id)
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

    async def _materialize_and_route(self, candidate: TaskCandidate, message: Message, task_source: TaskSource | None, org_chat: OrganizationChat | None, chat_id: int, topic_id: int | None) -> KomandusTask | None:
        organization_id = department_id = team_id = organization_chat_id = None
        if task_source:
            organization_id = task_source.organization_id
            department_id = task_source.department_id
            team_id = task_source.team_id
        if org_chat:
            organization_id = organization_id or org_chat.organization_id
            department_id = department_id or org_chat.department_id
            team_id = team_id or org_chat.team_id
            organization_chat_id = org_chat.id
        if organization_id is None:
            # Without an organization context the task cannot be scoped or made
            # visible on the kanban, so we skip creating an orphan record.
            return None

        employee = self._resolve_assignee(candidate.assignee_raw, organization_id, department_id, team_id)

        from app.tasks.services import V2TaskService

        task = V2TaskService(self.db).create_from_llm(
            organization_id=organization_id,
            employee_id=employee.id if employee else None,
            title=candidate.title,
            description=candidate.source_excerpt,
            source_chat_id=chat_id,
            source_message_id=message.telegram_message_id,
            confidence=candidate.confidence or 0.0,
            llm_model="telegram-detection",
            extraction_version="engine-v1",
            department_id=department_id,
            team_id=team_id,
            organization_chat_id=organization_chat_id,
            source_excerpt=candidate.source_excerpt,
            notify=False,
        )
        due = self._parse_deadline(candidate.deadline)
        if due:
            task.due_at = due
            self.db.commit()
        # Reply inside the originating topic; fall back to the topic the source
        # was bound to so a group reply never lands in General by accident.
        effective_topic = topic_id or (task_source.telegram_topic_id if task_source else None)
        await self._dispatch_detected_task(task, employee, organization_id, department_id, team_id, chat_id, effective_topic)
        return task

    async def _dispatch_detected_task(self, task: KomandusTask, employee: Employee | None, organization_id, department_id, team_id, chat_id: int, topic_id: int | None) -> dict:
        confidence = task.llm_confidence or 0.0
        source_title = self._source_title(chat_id)
        # 1) Resolved assignee, high confidence, reachable → straight to their DM.
        if employee and employee.telegram_id and confidence > 0.85:
            try:
                await self.telegram.send_task_confirmation(employee, task, source_title=source_title)
                return {"routed_to": "employee", "employee_id": str(employee.id)}
            except TelegramDeliveryError as exc:
                logger.warning("Task %s: DM to assignee %s failed, escalating to manager: %s", task.id, employee.id, exc)
        # 2) Low confidence or unresolved assignee → responsible manager for triage.
        manager = self._resolve_manager(organization_id, department_id, team_id, employee)
        if manager and manager.telegram_id:
            try:
                await self.telegram.send_manager_task_confirmation(manager, task, employee_hint=employee.full_name if employee else None, source_title=source_title)
                return {"routed_to": "manager", "manager_id": str(manager.id)}
            except TelegramDeliveryError as exc:
                logger.warning("Task %s: DM to manager %s failed, falling back to group %s: %s", task.id, manager.id, chat_id, exc)
        else:
            logger.warning("Task %s: no reachable manager (org=%s dept=%s team=%s); falling back to group %s", task.id, organization_id, department_id, team_id, chat_id)
        # 3) Fallback → the originating group, inside the correct topic.
        text, markup = self._task_card(task, employee)
        try:
            await self.telegram.send_group_message(chat_id, text, reply_markup=markup, message_thread_id=topic_id)
            return {"routed_to": "group", "chat_id": chat_id, "topic_id": topic_id}
        except TelegramDeliveryError as exc:
            logger.error("Task %s: group delivery to %s failed: %s", task.id, chat_id, exc)
            return {"routed_to": "none", "task_id": str(task.id)}

    def _resolve_assignee(self, assignee_raw: str | None, organization_id, department_id, team_id) -> Employee | None:
        if not assignee_raw or not assignee_raw.strip():
            return None
        raw = assignee_raw.strip()
        if raw.startswith("@"):
            return (
                self.db.query(Employee)
                .filter(Employee.organization_id == organization_id, Employee.is_active.is_(True), func.lower(Employee.telegram_username) == raw.lower())
                .first()
            )
        candidates = self.db.query(Employee).filter(Employee.organization_id == organization_id, Employee.is_active.is_(True)).all()
        return match_employee_by_name(raw, candidates, team_id=team_id, department_id=department_id)

    def _resolve_manager(self, organization_id, department_id, team_id, employee: Employee | None) -> Employee | None:
        # Only ever return a manager the bot can actually DM: an unreachable
        # manager (no telegram_id) would silently bounce the confirmation into
        # the originating group. Mirrors the reachability filter already used by
        # _reassignment_candidates.
        if employee and employee.manager_id:
            manager = self.db.query(Employee).filter(Employee.id == employee.manager_id, Employee.is_active.is_(True)).first()
            if manager and manager.telegram_id and normalize_role(manager.role) == Role.MANAGER:
                return manager
        base = self.db.query(Employee).filter(Employee.organization_id == organization_id, Employee.is_active.is_(True), Employee.role == Role.MANAGER.value, Employee.telegram_id.isnot(None))
        if team_id:
            manager = base.filter(Employee.team_id == team_id).first()
            if manager:
                return manager
        if department_id:
            manager = base.filter(Employee.department_id == department_id).first()
            if manager:
                return manager
        return base.first()

    def _task_card(self, task: KomandusTask, employee: Employee | None) -> tuple[str, dict]:
        assignee = employee.full_name if employee else "не назначен"
        text = (
            "🤖 Обнаружена задача!\n\n"
            f"📝 Что сделать: {task.title}\n"
            f"👤 Ответственный: {assignee}\n"
            f"📅 Дедлайн: {task.due_at.isoformat() if task.due_at else 'Не указан'}\n"
            f"🎯 Уверенность AI: {int((task.llm_confidence or 0) * 100)}%\n\n"
            "Подтвердите задачу:"
        )
        markup = {"inline_keyboard": [[{"text": "✅ Принять", "callback_data": f"task_accept:{task.id}"}, {"text": "❌ Отклонить", "callback_data": f"task_reject:{task.id}"}]]}
        return text, markup

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
        rows = [[{"text": label, "callback_data": f"trr:{task_id}:{code}"}] for code, label in reasons]
        rows.append([{"text": "✏️ Своя причина", "callback_data": f"trrc:{task_id}"}])
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, "Выберите причину отказа:", reply_markup={"inline_keyboard": rows})
        await self.telegram.answer_callback_query(callback_id, "Укажите причину отказа")
        return {"status": "reason_requested", "task_id": task_id}

    async def _ask_custom_reason(self, callback_id: str, task_id: str, chat_id: int | None, message_id: int | None):
        if chat_id:
            await self.telegram.send_html_message(chat_id, f"✏️ Напишите свою причину отказа ответом на это сообщение.\n<code>rej:{task_id}</code>", reply_markup={"force_reply": True, "input_field_placeholder": "Причина отказа"})
        await self.telegram.answer_callback_query(callback_id, "Напишите причину ответом на сообщение")
        return {"status": "custom_reason_requested", "task_id": task_id}

    async def _maybe_custom_reject(self, msg: dict):
        reply_text = (msg.get("reply_to_message") or {}).get("text") or ""
        if "rej:" not in reply_text:
            return None
        tail = reply_text.split("rej:")[-1].strip()
        task_id = tail.split()[0] if tail else ""
        try:
            UUID(task_id)
        except (ValueError, TypeError):
            return None
        reason = (msg.get("text") or "").strip()
        if not reason:
            return None
        chat_id = (msg.get("chat") or {}).get("id")
        return await self._handle_task_reject(None, task_id, None, chat_id, None, custom_reason=reason)

    async def _handle_task_reject(self, callback_id: str | None, task_id: str, reason_code: str | None, chat_id: int | None, message_id: int | None, custom_reason: str | None = None):
        reason_labels = {"no_time": "Нет времени", "not_mine": "Не моя зона ответственности", "no_access": "Нет доступа", "need_details": "Нужны уточнения", "other": "Другое"}
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            if callback_id:
                await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        confirmation = self.db.query(TaskConfirmation).filter(TaskConfirmation.task_id == task.id).first()
        if not confirmation:
            confirmation = TaskConfirmation(organization_id=task.organization_id, task_id=task.id, employee_id=task.employee_id)
            self.db.add(confirmation)
        task.status = TaskStatus.REJECTED.value
        task.rejected_at = datetime.utcnow()
        confirmation.status = ConfirmationStatus.DECLINED.value
        reason_text = (custom_reason or "").strip() or reason_labels.get(reason_code, reason_code)
        confirmation.decline_reason = reason_text
        confirmation.responded_at = datetime.utcnow()
        self.db.commit()
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, f"❌ Задача отклонена: {task.title}\nПричина: {reason_text}")
        elif chat_id:
            await self._send_message(chat_id, f"❌ Задача отклонена: {task.title}\nПричина: {reason_text}")
        if callback_id:
            await self.telegram.answer_callback_query(callback_id, "Отказ сохранен. Передано менеджеру.")
        await self._escalate_rejection_to_manager(task, reason_text)
        return {"status": "rejected", "task_id": task_id, "reason": reason_text}

    async def _handle_manager_approve(self, callback_id: str, task_id: str, chat_id: int | None, message_id: int | None):
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        task.status = TaskStatus.ACCEPTED.value
        task.accepted_at = datetime.utcnow()
        self.db.commit()
        # If an assignee is known, forward the task to them for personal acceptance.
        forwarded = False
        if task.employee_id:
            employee = self.db.query(Employee).filter(Employee.id == task.employee_id, Employee.is_active.is_(True)).first()
            if employee and employee.telegram_id:
                try:
                    await self.telegram.send_task_confirmation(employee, task)
                    forwarded = True
                except TelegramDeliveryError:
                    forwarded = False
        if chat_id and message_id:
            suffix = "\n\n➡️ Отправлено исполнителю." if forwarded else "\n\n✅ Добавлено на доску."
            await self.telegram.edit_message_text(chat_id, message_id, f"✅ Задача утверждена: {task.title}{suffix}")
        await self.telegram.answer_callback_query(callback_id, "Утверждено")
        return {"status": "approved", "task_id": task_id, "forwarded": forwarded}

    async def _handle_manager_reject(self, callback_id: str, task_id: str, chat_id: int | None, message_id: int | None):
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        task.status = TaskStatus.REJECTED.value
        task.rejected_at = datetime.utcnow()
        self.db.commit()
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, f"❌ Задача отклонена менеджером: {task.title}")
        await self.telegram.answer_callback_query(callback_id, "Отклонено")
        return {"status": "rejected", "task_id": task_id}

    async def _escalate_rejection_to_manager(self, task: KomandusTask, reason: str | None) -> None:
        """Notify the responsible manager that an employee rejected a task in Telegram,
        offering reassign / mark-as-false / resend actions."""
        employee = self.db.query(Employee).filter(Employee.id == task.employee_id).first() if task.employee_id else None
        manager = self._resolve_manager(task.organization_id, task.department_id, task.team_id, employee)
        if not manager or not manager.telegram_id:
            return
        name = employee.full_name if employee else "Сотрудник"
        text = (
            f"⚠️ <b>{self.telegram._escape(name)}</b> отклонил задачу: {self.telegram._escape(task.title)}\n"
            f"Причина: {self.telegram._escape(reason or 'не указана')}\n\n"
            "Что сделать с задачей?"
        )
        markup = {"inline_keyboard": [
            [{"text": "🔁 Переназначить", "callback_data": f"mgr_reassign:{task.id}"}],
            [{"text": "🗑 Ложная", "callback_data": f"mgr_reject_false:{task.id}"}, {"text": "📩 Снова тому же", "callback_data": f"mgr_resend:{task.id}"}],
        ]}
        try:
            await self.telegram.send_html_message(manager.telegram_id, text, reply_markup=markup)
        except TelegramDeliveryError:
            pass

    def _reassignment_candidates(self, task: KomandusTask, limit: int = 10) -> list[Employee]:
        query = self.db.query(Employee).filter(Employee.organization_id == task.organization_id, Employee.is_active.is_(True), Employee.telegram_id.isnot(None))
        if task.employee_id:
            query = query.filter(Employee.id != task.employee_id)
        scoped = []
        if task.team_id:
            scoped = query.filter(Employee.team_id == task.team_id).limit(limit).all()
        if not scoped and task.department_id:
            scoped = query.filter(Employee.department_id == task.department_id).limit(limit).all()
        if not scoped:
            scoped = query.limit(limit).all()
        return scoped

    async def _handle_manager_reassign_prompt(self, callback_id: str, task_id: str, chat_id: int | None, message_id: int | None):
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        candidates = self._reassignment_candidates(task)
        if not candidates:
            await self.telegram.answer_callback_query(callback_id, "Нет подключённых сотрудников для переназначения", show_alert=True)
            return {"status": "no_candidates", "task_id": task_id}
        rows = [[{"text": employee.full_name, "callback_data": f"mgr_assign:{task.id}:{employee.telegram_id}"}] for employee in candidates]
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, f"Кому переназначить задачу: {task.title}?", reply_markup={"inline_keyboard": rows})
        await self.telegram.answer_callback_query(callback_id, "Выберите исполнителя")
        return {"status": "reassign_prompt", "task_id": task_id, "candidates": len(candidates)}

    async def _handle_manager_assign(self, callback_id: str, task_id: str, employee_id: str, chat_id: int | None, message_id: int | None):
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        employee = self.db.query(Employee).filter(Employee.telegram_id == int(employee_id), Employee.organization_id == task.organization_id, Employee.is_active.is_(True)).first()
        if not employee:
            await self.telegram.answer_callback_query(callback_id, "Сотрудник не найден", show_alert=True)
            return {"status": "employee_not_found"}
        task.employee_id = employee.id
        task.status = TaskStatus.ACCEPTED.value
        task.rejected_at = None
        self._reset_confirmation(task, employee.id)
        self.db.commit()
        forwarded = False
        if employee.telegram_id:
            try:
                await self.telegram.send_task_confirmation(employee, task)
                forwarded = True
            except TelegramDeliveryError:
                forwarded = False
        if chat_id and message_id:
            suffix = "" if forwarded else " (нет Telegram у сотрудника)"
            await self.telegram.edit_message_text(chat_id, message_id, f"🔁 Переназначено на {employee.full_name}: {task.title}{suffix}")
        await self.telegram.answer_callback_query(callback_id, "Переназначено")
        return {"status": "reassigned", "task_id": task_id, "employee_id": employee_id, "forwarded": forwarded}

    async def _handle_manager_reject_false(self, callback_id: str, task_id: str, chat_id: int | None, message_id: int | None):
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        task.status = TaskStatus.REJECTED.value
        task.rejected_at = datetime.utcnow()
        self.db.commit()
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, f"🗑 Задача отклонена как ложная: {task.title}")
        await self.telegram.answer_callback_query(callback_id, "Отклонено как ложная")
        return {"status": "rejected_false", "task_id": task_id}

    async def _handle_manager_resend(self, callback_id: str, task_id: str, chat_id: int | None, message_id: int | None):
        task = self.db.query(KomandusTask).filter(KomandusTask.id == UUID(task_id)).first()
        if not task:
            await self.telegram.answer_callback_query(callback_id, "Задача не найдена", show_alert=True)
            return {"status": "not_found"}
        employee = self.db.query(Employee).filter(Employee.id == task.employee_id, Employee.is_active.is_(True)).first() if task.employee_id else None
        if not employee or not employee.telegram_id:
            await self.telegram.answer_callback_query(callback_id, "У сотрудника нет Telegram — переназначьте задачу", show_alert=True)
            return {"status": "no_telegram", "task_id": task_id}
        task.status = TaskStatus.ACCEPTED.value
        task.rejected_at = None
        self._reset_confirmation(task, employee.id)
        self.db.commit()
        try:
            await self.telegram.send_task_confirmation(employee, task)
        except TelegramDeliveryError:
            await self.telegram.answer_callback_query(callback_id, "Не удалось доставить сотруднику", show_alert=True)
            return {"status": "delivery_failed", "task_id": task_id}
        if chat_id and message_id:
            await self.telegram.edit_message_text(chat_id, message_id, f"📩 Задача снова отправлена {employee.full_name}: {task.title}")
        await self.telegram.answer_callback_query(callback_id, "Отправлено снова")
        return {"status": "resent", "task_id": task_id, "employee_id": str(employee.id)}

    def _reset_confirmation(self, task: KomandusTask, employee_id) -> None:
        confirmation = self.db.query(TaskConfirmation).filter(TaskConfirmation.task_id == task.id).first()
        if not confirmation:
            confirmation = TaskConfirmation(organization_id=task.organization_id, task_id=task.id, employee_id=employee_id)
            self.db.add(confirmation)
        confirmation.employee_id = employee_id
        confirmation.status = ConfirmationStatus.PENDING.value
        confirmation.decline_reason = None
        confirmation.responded_at = None

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
