from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base

JsonColumn = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(64), default="member", server_default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tasks: Mapped[list[Task]] = relationship(back_populates="assignee")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_update_id: Mapped[int | None] = mapped_column(Integer, index=True)
    telegram_message_id: Mapped[int | None] = mapped_column(Integer, index=True)
    telegram_user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    chat_id: Mapped[int | None] = mapped_column(Integer, index=True)
    text: Mapped[str | None] = mapped_column(Text)
    voice_file_id: Mapped[str | None] = mapped_column(String(255))
    raw_update: Mapped[dict[str, Any] | None] = mapped_column(JsonColumn)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidates: Mapped[list[TaskCandidate]] = relationship(back_populates="message")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Встреча команды", server_default="Встреча команды")
    summary: Mapped[str | None] = mapped_column(Text)
    decisions: Mapped[list[Any]] = mapped_column(JsonColumn, default=list, server_default="[]")
    action_items: Mapped[list[Any]] = mapped_column(JsonColumn, default=list, server_default="[]")
    transcript: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), default="meeting_audio", server_default="meeting_audio")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    candidates: Mapped[list[TaskCandidate]] = relationship(back_populates="meeting")


class TaskCandidate(Base):
    __tablename__ = "task_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[str | None] = mapped_column(String(64), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), index=True)
    meeting_id: Mapped[int | None] = mapped_column(ForeignKey("meetings.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    assignee_raw: Mapped[str | None] = mapped_column(String(255))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_raw: Mapped[str | None] = mapped_column(String(255))
    priority: Mapped[str] = mapped_column(String(32), default="medium", server_default="medium")
    confidence: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), default="pending", server_default="pending", index=True)
    source: Mapped[str] = mapped_column(String(64), default="telegram_text", server_default="telegram_text", index=True)
    missing_fields: Mapped[list[str]] = mapped_column(JsonColumn, default=list, server_default="[]")
    reason: Mapped[str | None] = mapped_column(String(255))
    raw_llm_json: Mapped[dict[str, Any] | None] = mapped_column(JsonColumn)
    source_excerpt: Mapped[str | None] = mapped_column(Text)
    source_message_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    message: Mapped[Message | None] = relationship(back_populates="candidates")
    meeting: Mapped[Meeting | None] = relationship(back_populates="candidates")
    task: Mapped[Task | None] = relationship(back_populates="candidate")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[str | None] = mapped_column(String(64), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("task_candidates.id"), unique=True, index=True)
    external_kanban_id: Mapped[str | None] = mapped_column(String(255), index=True)
    external_kanban_url: Mapped[str | None] = mapped_column(String(500))
    kanban_provider: Mapped[str] = mapped_column(String(32), default="internal", server_default="internal")
    title: Mapped[str] = mapped_column(String(500), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    assignee_raw: Mapped[str | None] = mapped_column(String(255))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), default="todo", server_default="todo", index=True)
    priority: Mapped[str] = mapped_column(String(32), default="medium", server_default="medium")
    source: Mapped[str] = mapped_column(String(64), default="telegram_text", server_default="telegram_text", index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_by_ai: Mapped[bool] = mapped_column(default=False, server_default="false")
    source_message_excerpt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status_change_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status_changed_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    assignee: Mapped[User | None] = relationship(back_populates="tasks")
    candidate: Mapped[TaskCandidate | None] = relationship(back_populates="task")
    status_history: Mapped[list[TaskStatusHistory]] = relationship(back_populates="task", cascade="all, delete-orphan")


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    old_status: Mapped[str | None] = mapped_column(String(32))
    new_status: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(64), default="dashboard", server_default="dashboard", index=True)
    changed_by: Mapped[str | None] = mapped_column(String(255))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped[Task] = relationship(back_populates="status_history")


Index("ix_tasks_team_status", Task.team_id, Task.status)
Index("ix_task_candidates_team_status", TaskCandidate.team_id, TaskCandidate.status)
