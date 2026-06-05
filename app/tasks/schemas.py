from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.common.enums import TaskStatus


class V2TaskCreate(BaseModel):
    title: str = Field(min_length=1, examples=["Prepare launch report"])
    description: str | None = None
    employee_id: UUID | None = None
    due_at: datetime | None = None


class V2TaskResponse(BaseModel):
    id: UUID
    organization_id: UUID
    employee_id: UUID | None
    title: str
    description: str | None
    status: str
    due_at: datetime | None
    llm_confidence: float | None
    llm_model: str | None
    extraction_version: str | None
    source_chat_id: int | None
    source_message_id: int | None
    external_task_id: str | None

    model_config = {"from_attributes": True}


class TaskStatusUpdate(BaseModel):
    status: TaskStatus = Field(examples=["IN_PROGRESS"])
