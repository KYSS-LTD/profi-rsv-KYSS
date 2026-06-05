from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.common.enums import Role


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1, examples=["Ivan Petrov"])
    email: str | None = Field(default=None, examples=["ivan@example.com"])
    role: Role = Role.EMPLOYEE
    department_id: UUID | None = None
    team_id: UUID | None = None
    position: str | None = None
    telegram_username: str | None = Field(default=None, examples=["@ivan_petrov"])


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    role: Role | None = None
    department_id: UUID | None = None
    team_id: UUID | None = None
    position: str | None = None
    telegram_username: str | None = None
    telegram_id: int | None = None
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: UUID
    organization_id: UUID
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
    generated_password: str | None = None
    invitation_text: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}
