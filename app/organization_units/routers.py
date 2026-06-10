from uuid import UUID
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.common.enums import Role
from app.common.rbac import RoleChecker
from app.dependencies import get_db
from app.organization_units.schemas import (
    ConnectCodeCreate,
    ConnectCodeResponse,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    HierarchyWizardResponse,
    HierarchyWizardUpdate,
    OrganizationChatResponse,
    OrganizationModeResponse,
    TaskSourceResponse,
    TeamCreate,
    TeamResponse,
)
from app.organization_units.services import OrganizationUnitService

router = APIRouter(prefix="/api/v2/org", tags=["Organization"])


@router.get("/mode", response_model=OrganizationModeResponse)
def organization_mode(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).get_mode(current_user)


@router.post("/hierarchy-wizard/start", response_model=HierarchyWizardResponse)
def start_hierarchy_wizard(current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN)), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).start_hierarchy_wizard(current_user)


@router.patch("/hierarchy-wizard", response_model=HierarchyWizardResponse)
def update_hierarchy_wizard(payload: HierarchyWizardUpdate, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN)), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).update_hierarchy_wizard(payload, current_user)


@router.post("/hierarchy-wizard/confirm", response_model=HierarchyWizardResponse)
def confirm_hierarchy_mode(current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN)), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).confirm_hierarchy_mode(current_user)


@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).list_departments(current_user)


@router.post("/departments", response_model=DepartmentResponse, status_code=201)
def create_department(payload: DepartmentCreate, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN)), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).create_department(payload, current_user)


@router.patch("/departments/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: UUID, payload: DepartmentUpdate, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN)), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).update_department(department_id, payload, current_user)


@router.get("/teams", response_model=list[TeamResponse])
def list_teams(department_id: UUID | None = None, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).list_teams(current_user, department_id)


@router.post("/teams", response_model=TeamResponse, status_code=201)
def create_team(payload: TeamCreate, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN)), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).create_team(payload, current_user)


@router.get("/chats", response_model=list[OrganizationChatResponse])
def list_chats(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).list_chats(current_user)


@router.get("/task-sources", response_model=list[TaskSourceResponse])
def list_task_sources(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).list_task_sources(current_user)


@router.post("/telegram/connect-code", response_model=ConnectCodeResponse)
def create_telegram_connect_code(payload: ConnectCodeCreate, current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN, Role.MANAGER)), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).create_connect_code(payload, current_user)


@router.patch("/chats/{chat_id}", response_model=OrganizationChatResponse)
def update_chat(chat_id: UUID, ai_enabled: bool = Body(...), department_id: UUID | None = Body(default=None), current_user=Depends(RoleChecker(Role.OWNER, Role.ADMIN, Role.MANAGER)), db: Session = Depends(get_db)):
    return OrganizationUnitService(db).set_chat_ai(chat_id, ai_enabled, department_id, current_user)
