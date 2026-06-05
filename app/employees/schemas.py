from pydantic import BaseModel, Field
from uuid import UUID

from app.common.enums import Role


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1, examples=["Ivan Petrov"])
    email: str | None = Field(default=None, examples=["ivan@example.com"])
    role: Role = Role.EMPLOYEE
    telegram_id: int | None = Field(default=None, examples=[123456789])


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    role: Role | None = None
    telegram_id: int | None = None
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: UUID
    organization_id: UUID
    full_name: str
    email: str | None
    role: str
    telegram_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}
