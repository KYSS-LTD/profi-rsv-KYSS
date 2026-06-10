from pydantic import BaseModel, Field

from app.auth.schemas import TokenResponse


class SetupStatusResponse(BaseModel):
    initialized: bool = Field(examples=[False])


class SetupRequest(BaseModel):
    organization_name: str = Field(min_length=1, max_length=255, examples=["My Company"])
    full_name: str = Field(min_length=1, max_length=255, examples=["John Doe"])
    email: str = Field(examples=["admin@company.com"])
    password: str = Field(min_length=8, examples=["StrongPassword123"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "organization_name": "My Company",
                    "full_name": "John Doe",
                    "email": "admin@company.com",
                    "password": "StrongPassword123",
                }
            ]
        }
    }


class SetupTokenResponse(TokenResponse):
    pass
