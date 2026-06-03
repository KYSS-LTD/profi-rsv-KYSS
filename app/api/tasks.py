from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas import TaskCreate
from app.services.task_service import TaskService

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)

@router.get("")
async def get_tasks(
    db: Session = Depends(get_db),
):
    return TaskService.get_all(db)

@router.post("")
async def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
):
    return TaskService.create(
        db,
        payload.title,
        payload.description,
    )