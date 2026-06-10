from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.schemas import DashboardResponse, EmployeeAnalyticsResponse
from app.tasks.schemas import AIAssistantRequest, AIAssistantResponse
from app.analytics.services import AnalyticsService
from app.auth.dependencies import get_current_user
from app.common.enums import Permission
from app.common.rbac import PermissionChecker
from app.dependencies import get_db

router = APIRouter(prefix="/api/v2/analytics", tags=["Analytics v2"])


@router.get("/dashboard", response_model=DashboardResponse, summary="Dashboard analytics", description="Return dashboard cards and chart datasets scoped to current role and optional org/dept/team/employee filters.")
def dashboard(organization_id: UUID | None = None, department_id: UUID | None = None, team_id: UUID | None = None, employee_id: UUID | None = None, current_user=Depends(PermissionChecker(Permission.CAN_VIEW_ANALYTICS)), db: Session = Depends(get_db)):
    return AnalyticsService(db).dashboard(current_user, organization_id=organization_id, department_id=department_id, team_id=team_id, employee_id=employee_id)


@router.get("/employee/{employee_id}", response_model=EmployeeAnalyticsResponse, summary="Employee analytics", description="Return per-employee metrics if the employee is in the current access scope.")
def employee_analytics(employee_id: UUID, current_user=Depends(PermissionChecker(Permission.CAN_VIEW_ANALYTICS)), db: Session = Depends(get_db)):
    return AnalyticsService(db).employee(employee_id, current_user)


@router.post("/assistant", response_model=AIAssistantResponse, summary="Ask AI assistant", description="Answer questions using scoped Komandus operational data with local fallback.")
def ai_assistant(payload: AIAssistantRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return AnalyticsService(db).ai_assistant(current_user, payload.question)
