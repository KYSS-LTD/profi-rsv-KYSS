from datetime import date, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_employee, get_db
from app.models.models import Employee, Task
from app.schemas import TaskCreate
from app.services.task_service import TASK_STATUSES, normalize_task_status, sync_task_status_to_yougile

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("")
async def get_tasks(
    assignee_id: str | None = None,
    status: str | None = None,
    source: str | None = None,
    current: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    query = db.query(Task).filter(Task.organization_id == current.organization_id)
    if current.role == "EMPLOYEE":
        query = query.filter(Task.assignee_employee_id == current.id)
    elif assignee_id:
        db_id = parse_employee_id(assignee_id)
        query = query.filter(Task.assignee_employee_id == db_id if db_id else Task.assignee_id == assignee_id)
    if status:
        query = query.filter(Task.status == normalize_task_status(status))
    if source:
        query = query.filter(Task.source == source)
    return [serialize_db_task(task) for task in query.order_by(Task.created_at.desc()).limit(200).all()]


@router.post("", status_code=201)
async def create_task(payload: TaskCreate, current: Employee = Depends(get_current_employee), db: Session = Depends(get_db)):
    assignee_id = getattr(payload, "assignee_id", None)
    assignee = db.query(Employee).filter(Employee.id == assignee_id, Employee.organization_id == current.organization_id).first() if assignee_id else None
    db_task = Task(
        organization_id=current.organization_id,
        title=payload.title,
        description=payload.description,
        status="OPEN",
        priority="medium",
        source="manual",
        created_by_ai=False,
        creator_id=current.id,
        assignee_employee_id=assignee.id if assignee else None,
        assignee_id=str(assignee.id) if assignee else None,
        assignee=assignee.full_name if assignee else None,
        due_date=getattr(payload, "due_date", None),
        deadline=getattr(payload, "due_date", None),
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return serialize_db_task(db_task)


@router.get("/my")
async def get_my_tasks(current: Employee = Depends(get_current_employee), db: Session = Depends(get_db)):
    return [serialize_db_task(task) for task in db.query(Task).filter(Task.organization_id == current.organization_id, Task.assignee_employee_id == current.id).all()]


@router.get("/dashboard")
async def get_dashboard(current: Employee = Depends(get_current_employee), db: Session = Depends(get_db)):
    query = db.query(Task).filter(Task.organization_id == current.organization_id)
    if current.role == "EMPLOYEE":
        query = query.filter(Task.assignee_employee_id == current.id)
    tasks = query.all()
    today = date.today().isoformat()
    return {
        "total": len(tasks),
        "open": sum(1 for task in tasks if task.status == "OPEN"),
        "in_progress": sum(1 for task in tasks if task.status == "IN_PROGRESS"),
        "done": sum(1 for task in tasks if task.status == "DONE"),
        "overdue": sum(1 for task in tasks if task.status not in {"DONE", "CANCELLED"} and task.due_date and task.due_date < today),
    }


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    payload: dict = Body(default_factory=dict),
    current: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    db_id = parse_db_task_id(task_id)
    task = db.query(Task).filter(Task.id == db_id, Task.organization_id == current.organization_id).first() if db_id is not None else None
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if current.role == "EMPLOYEE" and task.assignee_employee_id != current.id:
        raise HTTPException(status_code=403, detail="Employees can update only own tasks")

    new_status = normalize_task_status(payload.get("status"))
    if new_status not in TASK_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported task status")
    old_status = task.status
    task.status = new_status
    db.commit()
    db.refresh(task)
    sync_result = await sync_task_status_to_yougile(db, task)
    return {"task_id": f"db_{task.id}", "old_status": old_status, "new_status": new_status, "updated_at": task.updated_at.isoformat() if task.updated_at else datetime.utcnow().isoformat(), **sync_result}


@router.post("/{task_id}/reschedule")
async def reschedule_task(
    task_id: str,
    payload: dict = Body(default_factory=dict),
    current: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
):
    new_deadline = payload.get("new_deadline")
    if not new_deadline:
        raise HTTPException(status_code=422, detail="new_deadline is required")
    db_id = parse_db_task_id(task_id)
    task = db.query(Task).filter(Task.id == db_id, Task.organization_id == current.organization_id).first() if db_id is not None else None
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task.deadline = new_deadline
    task.due_date = new_deadline
    db.commit()
    db.refresh(task)
    return {"task_id": f"db_{task.id}", "deadline": new_deadline, "reminders_rebuilt": True}


def parse_db_task_id(task_id: str) -> int | None:
    raw_id = task_id.removeprefix("db_")
    return int(raw_id) if raw_id.isdigit() else None


def parse_employee_id(assignee_id: str) -> int | None:
    raw_id = assignee_id.removeprefix("employee_")
    return int(raw_id) if raw_id.isdigit() else None


def serialize_db_task(task: Task) -> dict:
    return {
        "id": f"db_{task.id}",
        "organization_id": task.organization_id,
        "candidate_id": str(task.candidate_id) if task.candidate_id else None,
        "title": task.title,
        "description": task.description,
        "assignee": task.assignee,
        "assignee_id": task.assignee_id,
        "assignee_employee_id": task.assignee_employee_id,
        "creator_id": task.creator_id,
        "deadline": task.deadline,
        "due_date": task.due_date,
        "status": task.status,
        "priority": task.priority,
        "source": task.source,
        "confidence": task.confidence,
        "created_by_ai": task.created_by_ai,
        "kanban_provider": "yougile" if task.yougile_task_id else "internal",
        "yougile_task_id": task.yougile_task_id,
        "yougile_url": task.yougile_url,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
