from pydantic import BaseModel
from uuid import UUID


class WorkloadSummary(BaseModel):
    active_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    completed_tasks: int
    workload_score: int


class OrganizationMapNode(BaseModel):
    id: UUID
    user_id: UUID | None = None
    full_name: str
    position: str | None = None
    role: str
    manager_id: UUID | None = None
    department_id: UUID | None = None
    team_id: UUID | None = None
    direct_reports: int
    indirect_reports: int
    responsibilities: list[str]
    active_delegations: int
    workload: WorkloadSummary
    requires_attention: bool
    children: list["OrganizationMapNode"] = []


class AttentionItem(BaseModel):
    type: str
    title: str
    count: int
    severity: str
    explanation: str


class HealthScore(BaseModel):
    score: int
    causes: list[str]


class OrganizationMapResponse(BaseModel):
    nodes: list[OrganizationMapNode]
    attention: list[AttentionItem]
    health: HealthScore
    role_model: list[str]
    permission_scopes: list[str]


class ProfileContextResponse(BaseModel):
    employee: OrganizationMapNode
    reports_to: str | None
    direct_reports: list[str]
    indirect_reports: int
    responsibilities: list[str]
    delegations: list[str]
    successors: list[str]
    recent_activity: list[str]
