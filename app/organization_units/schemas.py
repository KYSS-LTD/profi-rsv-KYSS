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
    team_id: UUID | None = None
    telegram_chat_id: int
    title: str
    chat_type: str | None
    members_count: int | None
    is_active: bool
    ai_enabled: bool
    bot_is_admin: bool
    connected_at: datetime

    model_config = {"from_attributes": True}


class TaskSourceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    source_type: str
    telegram_chat_id: int | None = None
    telegram_topic_id: int | None = None
    yougile_board_id: str | None = None
    yougile_column_id: str | None = None
    title: str
    department_id: UUID | None = None
    team_id: UUID | None = None
    board_mapping_id: UUID | None = None
    responsibility_area_id: UUID | None = None
    is_active: bool
    ai_enabled: bool
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectCodeCreate(BaseModel):
    department_id: UUID | None = None
    team_id: UUID | None = None


class ConnectCodeResponse(BaseModel):
    code: str
    command: str
    expires_at: datetime | None = None
    instruction: list[str]


class OrganizationModeResponse(BaseModel):
    mode: str
    hierarchy_setup_state: dict | None = None


class HierarchyWizardState(BaseModel):
    step: int = Field(ge=1, le=6)
    departments_ready: bool = False
    teams_ready: bool = False
    managers_ready: bool = False
    employees_distributed: bool = False
    telegram_sources_ready: bool = False


class HierarchyWizardUpdate(BaseModel):
    step: int | None = Field(default=None, ge=1, le=6)
    departments_ready: bool | None = None
    teams_ready: bool | None = None
    managers_ready: bool | None = None
    employees_distributed: bool | None = None
    telegram_sources_ready: bool | None = None


class HierarchyWizardResponse(BaseModel):
    mode: str
    hierarchy_setup_state: HierarchyWizardState
    can_confirm: bool
    checklist: list[str]
