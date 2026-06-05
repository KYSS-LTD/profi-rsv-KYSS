from pydantic import BaseModel, Field
from uuid import UUID


class LoginRequest(BaseModel):
    email: str = Field(examples=["manager@example.com"])
    password: str = Field(min_length=8, examples=["correct horse battery staple"])


class MagicLoginRequest(BaseModel):
    token: str = Field(min_length=16, max_length=128)


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class ImpersonateRequest(BaseModel):
    user_id: UUID


class MeResponse(BaseModel):
    id: UUID
    organization_id: UUID
    email: str
    full_name: str | None
    role: str
    department_id: UUID | None = None
    team_id: UUID | None = None
    must_change_password: bool = False
    permissions: list[str] = []
    impersonated_by_user_id: UUID | None = None

    model_config = {"from_attributes": True}
