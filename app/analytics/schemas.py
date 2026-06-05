from pydantic import BaseModel
from uuid import UUID


class DashboardResponse(BaseModel):
    total_tasks: int
    completed: int
    overdue: int
    average_completion_time: float
    average_response_time: float
    acceptance_percent: float
    rejection_percent: float
    pie_statuses: dict[str, int]
    top_employees: list[dict]
    closed_by_day: list[dict]
    burnup: list[dict]


class EmployeeAnalyticsResponse(BaseModel):
    employee_id: UUID
    accepted_tasks: int
    rejected_tasks: int
    completed_tasks: int
    overdue_tasks: int
    average_completion_time: float
    average_response_time: float
    efficiency_score: float
    organization_rank: int
