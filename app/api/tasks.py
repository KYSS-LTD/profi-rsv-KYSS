from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.models import Task
from app.schemas import RescheduleTaskPayload, TaskCreate, UpdateTaskStatusPayload
from app.services.task_decision_engine import TaskDecisionEngine

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def serialize_task(task: Task) -> dict:
    return {
        "id": str(task.id),
        "team_id": task.team_id,
        "candidate_id": str(task.candidate_id) if task.candidate_id else None,
        "external_kanban_id": task.external_kanban_id,
        "external_kanban_url": task.external_kanban_url,
        "title": task.title,
        "description": task.description,
        "assignee": task.assignee.name if task.assignee else task.assignee_raw,
        "assignee_id": str(task.assignee_id) if task.assignee_id else None,
        "deadline": task.deadline,
        "status": task.status,
        "priority": task.priority,
        "source": task.source,
        "confidence": task.confidence,
        "created_by_ai": task.created_by_ai,
        "kanban_provider": task.kanban_provider,
        "source_message_excerpt": task.source_message_excerpt,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "closed_at": task.closed_at,
        "started_at": task.started_at,
        "last_status_change_at": task.last_status_change_at,
        "status_changed_count": task.status_changed_count,
    }


@router.get("")
def get_tasks(
    team_id: str | None = None,
    assignee_id: str | None = None,
    status: str | None = None,
    source: str | None = None,
    deadline_from: datetime | None = None,
    deadline_to: datetime | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Task).order_by(Task.created_at.desc())
    if team_id:
        stmt = stmt.where(Task.team_id == team_id)
    if assignee_id:
        if not assignee_id.isdigit():
            return []
        stmt = stmt.where(Task.assignee_id == int(assignee_id))
    if status:
        stmt = stmt.where(Task.status == status)
    if source:
        stmt = stmt.where(Task.source == source)
    if deadline_from:
        stmt = stmt.where(Task.deadline >= deadline_from)
    if deadline_to:
        stmt = stmt.where(Task.deadline <= deadline_to)
    return [serialize_task(task) for task in db.execute(stmt).scalars().all()]


@router.post("", status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(title=payload.title, description=payload.description, priority=payload.priority, source="telegram_text", created_by_ai=False)
    db.add(task)
    db.commit()
    db.refresh(task)
    return serialize_task(task)


@router.get("/my")
def get_my_tasks(user_id: str = Query(default="1"), db: Session = Depends(get_db)):
    if not user_id.isdigit():
        return []
    return [serialize_task(task) for task in db.execute(select(Task).where(Task.assignee_id == int(user_id))).scalars().all()]


@router.patch("/{task_id}/status")
def update_task_status(task_id: int, payload: UpdateTaskStatusPayload, db: Session = Depends(get_db)):
    engine = TaskDecisionEngine(db)
    try:
        task = engine.update_task_status(task_id, payload.status, source=payload.source, changed_by=payload.changed_by, comment=payload.comment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "task_id": str(task.id),
        "old_status": getattr(task, "_previous_status", None),
        "new_status": task.status,
        "external_synced": task.kanban_provider == "external",
        "updated_at": task.updated_at,
    }


@router.post("/{task_id}/reschedule")
def reschedule_task(task_id: int, payload: RescheduleTaskPayload, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.deadline = datetime.fromisoformat(str(payload.new_deadline).replace("Z", "+00:00"))
    db.commit()
    db.refresh(task)
    return {"task_id": str(task.id), "deadline": task.deadline, "reminders_rebuilt": True}


@router.post("/candidates/{candidate_id}/confirm")
def confirm_candidate(candidate_id: int, payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    engine = TaskDecisionEngine(db)
    try:
        task = engine.confirm_candidate(candidate_id, overrides=payload.get("overrides") or {}, confirmed_by=payload.get("confirmed_by") or "dashboard")
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 409
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return {
        "task_id": str(task.id),
        "external_kanban_id": task.external_kanban_id,
        "external_kanban_url": task.external_kanban_url,
        "status": "created",
    }


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate_from_tasks(candidate_id: int, payload: dict = Body(default_factory=dict), db: Session = Depends(get_db)):
    engine = TaskDecisionEngine(db)
    try:
        candidate = engine.reject_candidate(candidate_id, reason=payload.get("reason") or "other", rejected_by=payload.get("rejected_by"))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": candidate.status, "candidate_id": str(candidate.id)}
