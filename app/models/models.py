from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base


# Telegram chat/user/message IDs are signed 64-bit values. Group and
# supergroup chat IDs are negative (often prefixed with -100) and do not
# fit into a 32-bit integer.
TELEGRAM_ID_TYPE = BigInteger


class TelegramChat(Base):
    __tablename__ = "telegram_chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, unique=True, index=True)
    title: Mapped[str | None]
    type: Mapped[str | None]
    last_processed_message_id: Mapped[int | None] = mapped_column(TELEGRAM_ID_TYPE)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
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
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    chat_id: Mapped[int] = mapped_column(TELEGRAM_ID_TYPE, index=True)
    title: Mapped[str]
    assignee_raw: Mapped[str | None]
    deadline_raw: Mapped[str | None]
    confidence: Mapped[float]
    status: Mapped[str] = mapped_column(default="pending")
    action: Mapped[str] = mapped_column(default="create")
    source_excerpt: Mapped[str | None]
    llm_block: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("task_candidates.id"))
    title: Mapped[str]
    description: Mapped[str | None]
    assignee_id: Mapped[str | None]
    assignee: Mapped[str | None]
    deadline: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="todo")
    priority: Mapped[str] = mapped_column(default="medium")
    source: Mapped[str] = mapped_column(default="telegram_text")
    created_by_ai: Mapped[bool] = mapped_column(default=False)
    confidence: Mapped[float | None]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
