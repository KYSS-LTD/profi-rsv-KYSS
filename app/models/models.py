from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


# Telegram chat/user/message IDs are signed 64-bit values. Group and
# supergroup chat IDs are negative (often prefixed with -100) and do not
# fit into a 32-bit integer.
TELEGRAM_ID_TYPE = BigInteger


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    yougile_project_id: Mapped[str | None]
    yougile_default_column_id: Mapped[str | None]
    yougile_in_progress_column_id: Mapped[str | None]
    yougile_done_column_id: Mapped[str | None]
    yougile_cancelled_column_id: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str]
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    full_name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, index=True)
    role: Mapped[str] = mapped_column(default="EMPLOYEE")
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), index=True)
    telegram_username: Mapped[str | None] = mapped_column(index=True)
    telegram_user_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    pending_rejection_candidate_id: Mapped[int | None] = mapped_column(ForeignKey("task_candidates.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class TelegramSource(Base):
    __tablename__ = "telegram_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, unique=True, index=True)
    chat_title: Mapped[str | None]
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class TelegramChat(Base):
    __tablename__ = "telegram_chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, unique=True, index=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    title: Mapped[str | None]
    type: Mapped[str | None]
    last_processed_message_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    telegram_message_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, index=True)
    telegram_user_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, index=True)
    sender_name: Mapped[str | None]
    username: Mapped[str | None]
    text: Mapped[str]
    source: Mapped[str] = mapped_column(default="telegram_text")
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class TaskCandidate(Base):
    __tablename__ = "task_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, index=True)
    title: Mapped[str]
    description: Mapped[str | None]
    assignee_raw: Mapped[str | None]
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), index=True)
    deadline_raw: Mapped[str | None]
    deadline: Mapped[str | None]
    confidence: Mapped[float]
    status: Mapped[str] = mapped_column(default="PENDING")
    action: Mapped[str] = mapped_column(default="create")
    source_message_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    source_chat_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    rejection_reason: Mapped[str | None]
    source_excerpt: Mapped[str | None]
    llm_block: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("task_candidates.id"))
    title: Mapped[str]
    description: Mapped[str | None]
    assignee_id: Mapped[str | None]
    assignee_employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), index=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), index=True)
    assignee: Mapped[str | None]
    deadline: Mapped[str | None]
    due_date: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="OPEN")
    priority: Mapped[str] = mapped_column(default="medium")
    source: Mapped[str] = mapped_column(default="telegram_text")
    created_by_ai: Mapped[bool] = mapped_column(default=False)
    confidence: Mapped[float | None]
    yougile_task_id: Mapped[str | None] = mapped_column(String, index=True)
    yougile_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
