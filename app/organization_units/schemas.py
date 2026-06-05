from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, examples=["Разработка"])
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DepartmentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    employee_count: int = 0
    task_count: int = 0
    overdue_count: int = 0
    efficiency: float = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamCreate(BaseModel):
    department_id: UUID
    name: str = Field(min_length=1, examples=["Backend"])
    description: str | None = None


class TeamResponse(BaseModel):
    id: UUID
    organization_id: UUID
    department_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationChatResponse(BaseModel):
    id: UUID
    organization_id: UUID
    department_id: UUID | None
    telegram_chat_id: int
    title: str
    chat_type: str | None
    members_count: int | None
    is_active: bool
    ai_enabled: bool
    bot_is_admin: bool
    connected_at: datetime

    model_config = {"from_attributes": True}


class ConnectCodeCreate(BaseModel):
    department_id: UUID | None = None


class ConnectCodeResponse(BaseModel):
    code: str
    command: str
    expires_at: datetime | None = None
    instruction: list[str]
