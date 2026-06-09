from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ---------- enums ----------
class MessageType(str, Enum):
    task_assignment = "task_assignment"
    task_proposal = "task_proposal"
    status_update = "status_update"
    question = "question"
    discussion = "discussion"
    noise = "noise"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class SourceType(str, Enum):
    telegram_text = "telegram_text"
    telegram_voice = "telegram_voice"
    meeting_audio = "meeting_audio"


class ActionRecommendation(str, Enum):
    skip = "skip"
    clarify = "clarify"
    confirm = "confirm"
    auto_create = "auto_create"
    update_existing = "update_existing"


class DedupRelation(str, Enum):
    none = "none"            # новая задача, не дубль
    duplicate = "duplicate"  # та же задача без новых деталей -> прикрепить, не создавать
    update = "update"        # та же задача, но новые детали (срок и т.п.) -> применение в P1


# ---------- LLM outputs ----------
class IntentResult(BaseModel):
    """Выход ноды 1. Заполняется LLM."""

    has_action_item: bool = Field(
        description="True только если message_type равен task_assignment или task_proposal."
    )
    message_type: MessageType = Field(description="Доминирующий тип сообщения, один лейбл.")
    confidence: float = Field(ge=0, le=1, description="Уверенность классификации.")


class RawExtractedTask(BaseModel):
    """Одна задача как её вернула LLM в ноде 2. Сырые поля + дата уже в ISO."""

    title: str = Field(description="Краткое действие в инфинитиве.")
    description: str | None = Field(default=None, description="Уточняющее предложение или null.")
    assignee_raw: str | None = Field(default=None, description="Имя/роль из текста дословно или null.")
    deadline_raw: str | None = Field(default=None, description="Формулировка срока из текста или null.")
    deadline: datetime | None = Field(
        default=None, description="ISO 8601 от 'сейчас'; null если срока нет или не уверен."
    )
    priority: Priority = Field(default=Priority.medium, description="Приоритет по словам срочности.")
    extraction_confidence: float = Field(
        default=0.8, ge=0, le=1, description="Уверенность, что это реальная задача."
    )


class ExtractedTaskList(BaseModel):
    """Структурный ответ ноды 2: 0..N задач из одного сообщения."""

    tasks: list[RawExtractedTask] = Field(default_factory=list)


# ---------- модель состояния (обогащается нодами 3-7) ----------
class ExtractedTask(RawExtractedTask):
    assignee_id: str | None = None
    assignee_confidence: float = 0.0
    is_duplicate: bool = False
    existing_task_id: str | None = None
    duplicate_confidence: float = 0.0
    dedup_relation: DedupRelation = DedupRelation.none
    confidence: float = 0.0
    action: ActionRecommendation | None = None
    needs_confirmation: bool = False


# ---------- контекст от бэкенда ----------
class TeamMember(BaseModel):
    id: str
    display_name: str
    role: str | None = None


class OpenTask(BaseModel):
    id: str
    title: str
    assignee_id: str | None = None
    deadline: str | None = None
    status: str | None = None


class ExtractionContext(BaseModel):
    now: datetime
    timezone: str = "Europe/Moscow"
    sender: str | None = None
    source_type: SourceType = SourceType.telegram_text
    source_quality: float = 1.0
    chat_context: list[str] = Field(default_factory=list)  # предыдущие реплики (для контекста)
    team_members: list[TeamMember] = Field(default_factory=list)
    open_tasks: list[OpenTask] = Field(default_factory=list)


# ---------- общее состояние графа ----------
class GraphState(BaseModel):
    text: str
    context: ExtractionContext
    intent: IntentResult | None = None
    tasks: list[ExtractedTask] = Field(default_factory=list)


# ---------- финальный выход пайплайна (контракт §16.1) ----------
class TaskExtractionResult(BaseModel):
    has_task: bool
    source_type: SourceType
    tasks: list[ExtractedTask] = Field(default_factory=list)
    raw_reasoning_summary: str | None = None
