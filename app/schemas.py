from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

TaskStatus = Literal["backlog", "todo", "in_progress", "review", "done", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "critical"]
TaskSource = Literal["telegram_text", "telegram_voice", "meeting_audio"]
CandidateStatus = Literal["pending", "confirmed", "rejected", "created", "duplicate"]


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = "medium"


class TaskResponse(BaseModel):
    id: str
    team_id: str | None = None
    candidate_id: str | None = None
    external_kanban_id: str | None = None
    external_kanban_url: str | None = None
    title: str
    description: str | None = None
    assignee: str | None = None
    assignee_id: str | None = None
    deadline: datetime | None = None
    status: str
    priority: str
    source: str
    confidence: float | None = None
    created_by_ai: bool = False
    kanban_provider: str = "internal"
    source_message_excerpt: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    started_at: datetime | None = None
    last_status_change_at: datetime | None = None
    status_changed_count: int = 0


class TaskCandidateResponse(BaseModel):
    id: str
    team_id: str | None = None
    message_id: str | None = None
    meeting_id: str | None = None
    title: str
    description: str | None = None
    assignee_id: str | None = None
    assignee_raw: str | None = None
    deadline: datetime | None = None
    deadline_raw: str | None = None
    priority: str = "medium"
    confidence: float
    status: str
    source: str
    missing_fields: list[str] = Field(default_factory=list)
    reason: str | None = None
    source_excerpt: str | None = None
    source_message_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ConfirmCandidatePayload(BaseModel):
    confirmed_by: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)


class RejectCandidatePayload(BaseModel):
    rejected_by: str | None = None
    reason: str = "other"


class UpdateTaskStatusPayload(BaseModel):
    status: TaskStatus
    changed_by: str | None = None
    source: str = "dashboard"
    comment: str | None = None


class RescheduleTaskPayload(BaseModel):
    new_deadline: datetime | str
    changed_by: str | None = None
    reason: str | None = None


class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[dict[str, Any]] = None
    callback_query: Optional[dict[str, Any]] = None


class ExtractedTask(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    assignee_id: str | None = None
    assignee_raw: str | None = None
    deadline: str | None = None
    deadline_raw: str | None = None
    priority: TaskPriority = "medium"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: TaskSource = "telegram_text"
    missing_fields: list[str] = Field(default_factory=list)
    source_excerpt: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class TaskExtractionResult(BaseModel):
    has_task: bool = False
    tasks: list[ExtractedTask] = Field(default_factory=list)
    raw: Any = None
