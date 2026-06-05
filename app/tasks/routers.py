from uuid import UUID
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.common.enums import Permission
from app.common.rbac import PermissionChecker
from app.dependencies import get_db
from app.tasks.schemas import TaskStatusUpdate, V2TaskCreate, V2TaskResponse
from app.tasks.services import V2TaskService

router = APIRouter(prefix="/api/v2/tasks", tags=["Tasks v2"])


@router.get("", response_model=list[V2TaskResponse], summary="List tasks", description="List tasks scoped by organization, hierarchy, and role permissions.")
def list_tasks(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return V2TaskService(db).list(current_user)


@router.post("", response_model=V2TaskResponse, status_code=201, summary="Create task", description="Create a manual task in Komandus without directly calling external boards.")
def create_task(payload: V2TaskCreate, current_user=Depends(PermissionChecker(Permission.CAN_ASSIGN_TASKS)), db: Session = Depends(get_db)):
    return V2TaskService(db).create_manual(payload, current_user)


@router.patch("/{task_id}/status", response_model=V2TaskResponse, summary="Move task", description="Move a task through the validated lifecycle state machine.")
def move_task(task_id: UUID, payload: TaskStatusUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return V2TaskService(db).change_status(task_id, payload.status, current_user)


@router.post("/{task_id}/confirm", response_model=V2TaskResponse, summary="Confirm task", description="Approve or decline an extracted task and enqueue downstream board synchronization.")
def confirm_task(task_id: UUID, approved: bool = Body(...), reason: str | None = Body(default=None), current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return V2TaskService(db).confirm(task_id, approved, reason, current_user)
