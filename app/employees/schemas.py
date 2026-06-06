from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.common.enums import Role


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1, examples=["Ivan Petrov"])
    email: str | None = Field(default=None, examples=["ivan@example.com"])
    role: Role = Role.EMPLOYEE
    manager_id: UUID | None = None
    department_id: UUID | None = None
    team_id: UUID | None = None
    position: str | None = None
    telegram_username: str | None = Field(default=None, examples=["@ivan_petrov"])


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    role: Role | None = None
    manager_id: UUID | None = None
    department_id: UUID | None = None
    team_id: UUID | None = None
    position: str | None = None
    telegram_username: str | None = None
    telegram_id: int | None = None
    active: bool | None = None
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID | None = None
    manager_id: UUID | None
    full_name: str
    email: str | None
    role: str
    department_id: UUID | None
    team_id: UUID | None
    position: str | None
    telegram_username: str | None
    telegram_first_name: str | None
    telegram_last_name: str | None
    avatar_url: str | None
    telegram_status: str
    telegram_connected_at: datetime | None
    telegram_id: int | None
    telegram_user_id: int | None = None
    telegram_connected: bool = False
    active: bool = True
    is_active: bool
    deactivated_at: datetime | None = None
    deactivated_by: UUID | None = None
    generated_password: str | None = None
    invitation_text: str | None = None

    model_config = {"from_attributes": True}
