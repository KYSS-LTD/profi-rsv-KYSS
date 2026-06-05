from pydantic import BaseModel, Field
from uuid import UUID


class LoginRequest(BaseModel):
    email: str = Field(examples=["manager@example.com"])
    password: str = Field(min_length=8, examples=["correct horse battery staple"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: UUID
    organization_id: UUID
    email: str
    full_name: str | None
    role: str

    model_config = {"from_attributes": True}
