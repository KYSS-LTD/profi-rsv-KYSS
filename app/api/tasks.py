from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.demo_data import TASKS, TASK_CANDIDATES, copy_data, now_iso
from app.dependencies import get_db
from app.models.models import Task
from app.schemas import TaskCreate

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


def _find_task(task_id: str) -> dict:
    task = next((item for item in TASKS if str(item["id"]) == str(task_id)), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("")
async def get_tasks(
    team_id: str | None = None,
    assignee_id: str | None = None,
    status: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
):
    db_query = db.query(Task)
    if assignee_id:
        db_query = db_query.filter(Task.assignee_id == assignee_id)
    if status:
        db_query = db_query.filter(Task.status == status)
    if source:
        db_query = db_query.filter(Task.source == source)
    return [serialize_db_task(task) for task in db_query.order_by(Task.created_at.desc()).limit(200).all()]


@router.post("", status_code=201)
async def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(
        title=payload.title,
        description=payload.description,
        status="todo",
        priority="medium",
        source="telegram_text",
        created_by_ai=False,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return serialize_db_task(db_task)


@router.get("/my")
async def get_my_tasks(user_id: str = Query(default="user_ivan"), db: Session = Depends(get_db)):
    return [serialize_db_task(task) for task in db.query(Task).filter(Task.assignee_id == user_id).all()]


@router.patch("/{task_id}/status")
async def update_task_status(task_id: str, payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    db_id = parse_db_task_id(task_id)
    db_task = db.query(Task).filter(Task.id == db_id).first() if db_id is not None else None
    if db_task is not None:
        old_status = db_task.status
        new_status = payload.get("status")
        if not new_status:
            raise HTTPException(status_code=422, detail="status is required")
        db_task.status = new_status
        db.commit()
        db.refresh(db_task)
        return {"task_id": task_id, "old_status": old_status, "new_status": new_status, "external_synced": False, "updated_at": db_task.updated_at.isoformat() if db_task.updated_at else now_iso()}

    task = _find_task(task_id)
    old_status = task["status"]
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=422, detail="status is required")

    task["status"] = new_status
    task["updated_at"] = now_iso()
    task["last_status_change_at"] = task["updated_at"]
    task["status_changed_count"] = int(task.get("status_changed_count") or 0) + 1
    if new_status == "done":
        task["closed_at"] = task["updated_at"]

    return {
        "task_id": task_id,
        "old_status": old_status,
        "new_status": new_status,
        "external_synced": task.get("kanban_provider") == "external",
        "updated_at": task["updated_at"],
    }


@router.post("/{task_id}/reschedule")
async def reschedule_task(task_id: str, payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    new_deadline = payload.get("new_deadline")
    if not new_deadline:
        raise HTTPException(status_code=422, detail="new_deadline is required")

    db_id = parse_db_task_id(task_id)
    db_task = db.query(Task).filter(Task.id == db_id).first() if db_id is not None else None
    if db_task is not None:
        db_task.deadline = new_deadline
        db.commit()
        db.refresh(db_task)
        return {"task_id": task_id, "deadline": new_deadline, "reminders_rebuilt": True}

    task = _find_task(task_id)
    task["deadline"] = new_deadline
    task["updated_at"] = now_iso()
    return {"task_id": task_id, "deadline": new_deadline, "reminders_rebuilt": True}


@router.post("/candidates/{candidate_id}/confirm")
async def confirm_candidate(candidate_id: str, payload: dict = Body(default_factory=dict)):
    candidate = next((item for item in TASK_CANDIDATES if item["id"] == candidate_id), None)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    overrides = payload.get("overrides") or {}
    candidate["status"] = "confirmed"
    task = {
        "id": f"task_from_{candidate_id}",
        "team_id": candidate.get("team_id", "team_1"),
        "candidate_id": candidate_id,
        "title": overrides.get("title") or candidate["title"],
        "description": overrides.get("description") or candidate.get("description"),
        "assignee": overrides.get("assignee_raw") or candidate.get("assignee_raw"),
        "assignee_id": overrides.get("assignee_id") or candidate.get("assignee_id"),
        "deadline": overrides.get("deadline") or candidate.get("deadline"),
        "status": "todo",
        "priority": overrides.get("priority") or candidate.get("priority", "medium"),
        "source": candidate.get("source", "telegram_text"),
        "confidence": candidate.get("confidence"),
        "created_by_ai": True,
        "kanban_provider": "internal",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    TASKS.append(task)
    return {"task_id": task["id"], "external_kanban_id": None, "external_kanban_url": None, "status": "created"}


@router.post("/candidates/{candidate_id}/reject")
async def reject_candidate_from_tasks(candidate_id: str, payload: dict = Body(default_factory=dict)):
    candidate = next((item for item in TASK_CANDIDATES if item["id"] == candidate_id), None)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate["status"] = "rejected"
    candidate["reason"] = payload.get("reason") or "other"
    return {"status": "rejected", "candidate_id": candidate_id}


def parse_db_task_id(task_id: str) -> int | None:
    raw_id = task_id.removeprefix("db_")
    return int(raw_id) if raw_id.isdigit() else None


def serialize_db_task(task: Task) -> dict:
    return {
        "id": f"db_{task.id}",
        "team_id": "team_1",
        "candidate_id": str(task.candidate_id) if task.candidate_id else None,
        "title": task.title,
        "description": task.description,
        "assignee": task.assignee,
        "assignee_id": task.assignee_id,
        "deadline": task.deadline,
        "status": task.status,
        "priority": task.priority,
        "source": task.source,
        "confidence": task.confidence,
        "created_by_ai": task.created_by_ai,
        "kanban_provider": "internal",
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
