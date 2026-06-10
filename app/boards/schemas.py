from pydantic import BaseModel, Field
from uuid import UUID


class VerifyYouGileRequest(BaseModel):
    api_token: str = Field(min_length=8, examples=["yg_xxx"])
    department_id: UUID | None = None
    team_id: UUID | None = None


class BoardIntegrationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    provider: str
    name: str
    external_project_id: str | None
    external_board_id: str | None
    department_id: UUID | None = None
    team_id: UUID | None = None
    is_active: bool
    metadata_json: dict | None

    model_config = {"from_attributes": True}


class ColumnMappingCreate(BaseModel):
    task_status: str
    external_column_id: str
    external_column_name: str | None = None


class EmployeeBoardMappingCreate(BaseModel):
    employee_id: UUID
    external_user_id: str
    external_email: str | None = None
