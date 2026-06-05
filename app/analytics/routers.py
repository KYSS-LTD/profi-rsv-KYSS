from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.schemas import DashboardResponse, EmployeeAnalyticsResponse
from app.tasks.schemas import AIAssistantRequest, AIAssistantResponse
from app.analytics.services import AnalyticsService
from app.auth.dependencies import get_current_user
from app.dependencies import get_db

router = APIRouter(prefix="/api/v2/analytics", tags=["Analytics v2"])


@router.get("/dashboard", response_model=DashboardResponse, summary="Dashboard analytics", description="Return dashboard cards and chart datasets scoped to current organization.")
def dashboard(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return AnalyticsService(db).dashboard(current_user)


@router.get("/employee/{employee_id}", response_model=EmployeeAnalyticsResponse, summary="Employee analytics", description="Return per-employee acceptance, completion, overdue, response-time, and efficiency ranking metrics.")
def employee_analytics(employee_id: UUID, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return AnalyticsService(db).employee(employee_id, current_user)


@router.post("/assistant", response_model=AIAssistantResponse, summary="Ask AI assistant", description="Answer manager questions using real Komandus operational data.")
def ai_assistant(payload: AIAssistantRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return AnalyticsService(db).ai_assistant(current_user, payload.question)
